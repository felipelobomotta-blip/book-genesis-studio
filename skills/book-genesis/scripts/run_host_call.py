"""Run one caller-selected native host command under a per-book single-call guard.

This wrapper launches the caller-selected existing native CLI and records its
outputs. It does not author prompts, select a provider or model, install a
provider, invoke an SDK or run a separate writing application. It runs the
supplied argv with ``shell=False``, feeds the immutable packet on stdin, and
records the result under ``work/host-calls/<call-id>``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BUSY_EXIT = 75
DEFAULT_TIMEOUT_SECONDS = 900.0
MAX_TIMEOUT_SECONDS = 24 * 60 * 60
CALL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,96}$")


class HostCallError(RuntimeError):
    def __init__(self, message: str, *, receipt: dict[str, Any], exit_code: int = 1) -> None:
        super().__init__(message)
        self.receipt = receipt
        self.exit_code = exit_code


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_hash(path: Path) -> str | None:
    try:
        return _sha256(path.read_bytes())
    except OSError:
        return None


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _safe_call_id(call_id: str) -> str:
    if not CALL_ID_RE.fullmatch(call_id) or call_id in {".", ".."}:
        raise ValueError("call-id must be a simple filename component")
    return call_id


def _parse_command(command_json: str) -> tuple[list[str], float]:
    try:
        value = json.loads(command_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"command-json is malformed JSON: line {exc.lineno} column {exc.colno}") from exc
    timeout = DEFAULT_TIMEOUT_SECONDS
    if isinstance(value, list):
        argv = value
    elif isinstance(value, dict):
        if set(value) - {"argv", "timeout_seconds"}:
            raise ValueError("command-json object may contain only argv and timeout_seconds")
        argv = value.get("argv")
        if "timeout_seconds" in value:
            timeout = value["timeout_seconds"]
    else:
        raise ValueError("command-json must be an argv JSON array or an object with argv")
    if not isinstance(argv, list) or not argv or any(not isinstance(item, str) or not item for item in argv):
        raise ValueError("command-json argv must be a non-empty array of non-empty strings")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= MAX_TIMEOUT_SECONDS:
        raise ValueError(f"timeout_seconds must be greater than zero and at most {MAX_TIMEOUT_SECONDS}")
    return list(argv), float(timeout)


def _replace_placeholders(argv: list[str], *, output: Path, cwd: Path) -> list[str]:
    return [item.replace("{output}", str(output)).replace("{cwd}", str(cwd)) for item in argv]


def _fresh_child_cwd(book_root: Path) -> tuple[Path, Path]:
    base = Path(tempfile.gettempdir()).resolve()
    if base.is_relative_to(book_root):
        raise ValueError("system temp directory must not be inside the book's tree")
    child = Path(tempfile.mkdtemp(prefix="book-genesis-host-call-", dir=base)).resolve()
    if child.is_relative_to(book_root) or book_root.is_relative_to(child) or child.parent != base:
        shutil.rmtree(child, ignore_errors=True)
        raise ValueError("fresh child cwd is not safely outside the book's ancestor tree")
    return base, child


def _cleanup_child_cwd(base: Path | None, child: Path | None) -> None:
    if base is None or child is None:
        return
    try:
        if child.parent == base and child.name.startswith("book-genesis-host-call-"):
            shutil.rmtree(child)
    except OSError:
        # The persisted call receipt remains the evidence if cleanup is denied.
        pass


def _pid_state(pid: Any) -> bool | None:
    """Return alive/dead, or None when the platform cannot prove either."""

    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return None
    if os.name == "nt":
        # Windows does not provide a harmless signal-0 probe: CPython maps
        # os.kill to TerminateProcess for non-CTRL signals. Query the process
        # with read-only rights instead, and distinguish a missing PID from an
        # access-denied/unknown state.
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False if ctypes.get_last_error() == 87 else None  # ERROR_INVALID_PARAMETER
        try:
            exit_code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return None
            return exit_code.value == 259  # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return None
    except OSError:
        return None
    return True


def _read_lock(lock_path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _write_lock(lock_path: Path, value: dict[str, Any]) -> None:
    data = _json_bytes(value) + b"\n"
    if os.name == "nt":
        # Some Windows workspace/temp providers reject replacing an existing
        # file even when no handle is open. The owner already holds the
        # O_EXCL-created lock; update that inode in place. Readers treat a
        # transiently incomplete JSON document as busy and fail closed.
        with lock_path.open("r+b") as handle:
            handle.seek(0)
            handle.truncate()
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        return
    temporary = lock_path.with_name(lock_path.name + ".tmp")
    temporary.write_bytes(data)
    os.replace(temporary, lock_path)


def _acquire_book_lock(lock_path: Path, *, call_id: str) -> dict[str, Any]:
    metadata = {"call_id": call_id, "helper_pid": os.getpid(), "child_pid": None, "started_at": _now()}
    created = False
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        created = True
        try:
            # Keep the O_EXCL-created inode and write its first metadata in
            # place. Replacing that inode immediately is rejected by Windows
            # in some environments even after the creator closes its handle.
            os.write(descriptor, _json_bytes(metadata) + b"\n")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return metadata
    except FileExistsError as exc:
        active = _read_lock(lock_path)
        if active is None:
            receipt = {"schema_version": 1, "status": "busy", "active_call_id": None, "message": "active lock is unreadable; fail closed"}
            raise HostCallError(receipt["message"], receipt=receipt, exit_code=BUSY_EXIT) from exc
        helper_state = _pid_state(active.get("helper_pid"))
        # A missing child PID can mean the owner died in the launch/update
        # gap. It is unknown whether a child was already spawned, so fail
        # closed instead of reclaiming that lock.
        child_state = _pid_state(active.get("child_pid")) if active.get("child_pid") is not None else None
        if helper_state is not False or child_state is True or child_state is None:
            receipt = {
                "schema_version": 1,
                "status": "busy",
                "active_call_id": active.get("call_id"),
                "message": "another host call is active; wait for its receipt before retrying",
            }
            raise HostCallError(receipt["message"], receipt=receipt, exit_code=BUSY_EXIT) from exc
        # Even a dead owner is not enough to prove that another process did
        # not acquire the same path between our read and a possible unlink.
        # Leave stale recovery to an explicit operator action and fail closed.
        receipt = {
            "schema_version": 1,
            "status": "busy",
            "active_call_id": active.get("call_id"),
            "message": "stale lock is not auto-recovered; inspect the recorded owner and child before retrying",
        }
        raise HostCallError(receipt["message"], receipt=receipt, exit_code=BUSY_EXIT) from exc
    except OSError:
        if created:
            try:
                lock_path.unlink()
            except OSError:
                pass
        raise


def _terminate_owned_tree(process: subprocess.Popen[bytes]) -> bool:
    if os.name == "nt":
        try:
            result = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False,
                timeout=3,
            )
            # A dead direct parent is not proof that a launcher's descendants
            # are gone. Only taskkill's successful tree operation proves the
            # tree boundary; the caller separately reaps the direct handle.
            return result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False
    def group_is_dead() -> bool:
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            return True
        except OSError:
            return False
        return False

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return process.poll() is not None
    except OSError:
        return False
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return process.poll() is not None
        except OSError:
            return False
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            return False
    if not group_is_dead():
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return process.poll() is not None
        except OSError:
            return False
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            return False
    return process.poll() is not None and group_is_dead()


def _terminate_and_reap_owned(process: subprocess.Popen[bytes]) -> bool:
    """Stop and reap our child, returning false when ownership is unverified."""

    tree_shutdown_verified = False
    try:
        tree_shutdown_verified = _terminate_owned_tree(process)
    except (OSError, subprocess.SubprocessError):
        pass
    if tree_shutdown_verified and process.poll() is not None:
        return True
    # taskkill/group termination can fail or time out. These operations target
    # only the Popen handle we own; every wait remains bounded.
    try:
        process.terminate()
    except OSError:
        pass
    try:
        process.wait(timeout=2)
        return tree_shutdown_verified
    except subprocess.TimeoutExpired:
        pass
    try:
        process.kill()
    except OSError:
        pass
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        return False
    return tree_shutdown_verified and process.poll() is not None


def _write_exclusive(path: Path, data: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(data)


def _paths(call_dir: Path) -> dict[str, Path]:
    return {
        "packet": call_dir / "packet",
        "stdout": call_dir / "stdout",
        "stderr": call_dir / "stderr",
        "response_pending": call_dir / "response.pending",
        "response": call_dir / "response",
        "receipt": call_dir / "receipt.json",
    }


def _receipt_paths(book_root: Path, paths: dict[str, Path]) -> dict[str, str]:
    return {name: str(path.relative_to(book_root)) for name, path in paths.items()}


def _existing_call(
    call_dir: Path,
    *,
    packet_hash: str,
    argv_hash: str,
) -> dict[str, Any] | None:
    if not call_dir.exists():
        return None
    receipt_path = call_dir / "receipt.json"
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"call-id directory exists without a readable receipt; use a new call-id: {exc}") from exc
    if not isinstance(receipt, dict) or receipt.get("status") != "completed":
        raise ValueError("call-id was already used by a non-completed call; retries require a new call-id")
    if receipt.get("packet_sha256") != packet_hash or receipt.get("argv_sha256") != argv_hash:
        raise ValueError("completed call-id request hashes differ; use a new call-id")
    expected_files = {
        "packet_sha256": call_dir / "packet",
        "stdout_sha256": call_dir / "stdout",
        "stderr_sha256": call_dir / "stderr",
        "response_sha256": call_dir / "response",
    }
    for field, path in expected_files.items():
        saved_hash = receipt.get(field)
        actual_hash = _file_hash(path)
        if not isinstance(saved_hash, str) or actual_hash != saved_hash:
            raise ValueError(f"completed call evidence hash mismatch for {path.name}; use a new call-id")
    if (call_dir / "response.pending").exists():
        raise ValueError("completed call retains a pending response; use a new call-id")
    result = dict(receipt)
    result["idempotent"] = True
    return result


def run_host_call(
    book_dir: str | Path,
    call_id: str,
    packet_path: str | Path,
    command_json: str,
) -> dict[str, Any]:
    """Run one native argv and return its completed receipt or raise structured error."""

    call_id = _safe_call_id(call_id)
    argv, timeout = _parse_command(command_json)
    book_root = Path(book_dir).resolve()
    packet_source = Path(packet_path)
    packet_bytes = packet_source.read_bytes()
    packet_hash = _sha256(packet_bytes)
    argv_hash = _sha256(_json_bytes(argv))
    calls_root = book_root / "work" / "host-calls"
    calls_root.mkdir(parents=True, exist_ok=True)
    call_dir = calls_root / call_id
    paths = _paths(call_dir)
    existing = _existing_call(call_dir, packet_hash=packet_hash, argv_hash=argv_hash)
    if existing is not None:
        return existing

    lock_path = calls_root / ".active.lock"
    lock_metadata = _acquire_book_lock(lock_path, call_id=call_id)
    child_temp_base: Path | None = None
    child_cwd: Path | None = None
    release_lock = True
    preserve_child_cwd = False
    try:
        if call_dir.exists():
            raise ValueError("call-id directory appeared while acquiring the book lock; use a new call-id")
        call_dir.mkdir()
        _write_exclusive(paths["packet"], packet_bytes)
        output_path = paths["response"]
        requires_output_file = any("{output}" in item for item in argv)
        started = _now()
        child_pid: int | None = None
        timed_out = False
        process_returncode: int | None = None
        process: subprocess.Popen[bytes] | None = None
        shutdown_unverified = False
        try:
            child_temp_base, child_cwd = _fresh_child_cwd(book_root)
            argv = _replace_placeholders(argv, output=paths["response_pending"], cwd=child_cwd)
            with paths["packet"].open("rb") as packet_handle, paths["stdout"].open("xb") as stdout_handle, paths["stderr"].open("xb") as stderr_handle:
                creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
                process = subprocess.Popen(
                    argv,
                    stdin=packet_handle,
                    stdout=stdout_handle,
                    stderr=stderr_handle,
                    cwd=child_cwd,
                    shell=False,
                    start_new_session=os.name != "nt",
                    creationflags=creationflags,
                )
                child_pid = process.pid
                lock_metadata["child_pid"] = child_pid
                _write_lock(lock_path, lock_metadata)
                try:
                    process_returncode = process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    if _terminate_and_reap_owned(process):
                        process_returncode = process.returncode
                    else:
                        shutdown_unverified = True
                        release_lock = False
                        preserve_child_cwd = True
                        process_returncode = process.poll()
        except Exception as exc:
            termination_error: str | None = None
            if process is not None and process.poll() is None:
                if not _terminate_and_reap_owned(process):
                    release_lock = False
                    preserve_child_cwd = True
                    termination_error = "owned child could not be terminated and reaped; active lock retained"
            error = f"native host call failed to start or complete: {exc}"
            if termination_error:
                error = f"{error}; {termination_error}"
            receipt = {
                "schema_version": 1,
                "status": "failed",
                "call_id": call_id,
                "packet_sha256": packet_hash,
                "argv_sha256": argv_hash,
                "stdout_sha256": _file_hash(paths["stdout"]),
                "stderr_sha256": _file_hash(paths["stderr"]),
                "response_sha256": _file_hash(paths["response"]),
                "pending_response_sha256": _file_hash(paths["response_pending"]),
                "exit_code": None,
                "error": error,
                "paths": _receipt_paths(book_root, paths),
                "started_at": started,
                "finished_at": _now(),
            }
            _write_exclusive(paths["receipt"], _json_bytes(receipt) + b"\n")
            raise HostCallError(error, receipt=receipt) from exc

        response_read_error: str | None = None
        response_bytes = b""
        try:
            pending_path = paths["response_pending"]
            if not pending_path.exists() and not requires_output_file and process_returncode == 0 and not shutdown_unverified:
                stdout_bytes = paths["stdout"].read_bytes()
                if stdout_bytes.strip():
                    _write_exclusive(pending_path, stdout_bytes)
            response_bytes = pending_path.read_bytes() if pending_path.is_file() else b""
        except OSError as exc:
            response_bytes = b""
            response_read_error = f"could not persist or read the response: {exc}"
        failed_reason = response_read_error
        if shutdown_unverified:
            failed_reason = "native host call exceeded timeout and owned child shutdown was not verified; active lock retained"
        elif timed_out:
            failed_reason = f"native host call exceeded timeout_seconds={timeout:g}; owned child tree was terminated"
        elif process_returncode != 0:
            failed_reason = f"native host call exited with code {process_returncode}"
        elif not response_bytes.strip() and failed_reason is None:
            failed_reason = "native host call exited 0 but produced an empty response"
        elif failed_reason is None:
            try:
                os.replace(paths["response_pending"], output_path)
                response_bytes = output_path.read_bytes()
            except OSError as exc:
                failed_reason = f"could not atomically publish the response: {exc}"
        receipt = {
            "schema_version": 1,
            "status": "failed" if failed_reason else "completed",
            "call_id": call_id,
            "packet_sha256": packet_hash,
            "argv_sha256": argv_hash,
            "stdout_sha256": _file_hash(paths["stdout"]),
            "stderr_sha256": _file_hash(paths["stderr"]),
            "response_sha256": _sha256(response_bytes),
            "pending_response_sha256": _file_hash(paths["response_pending"]),
            "exit_code": process_returncode,
            "error": failed_reason,
            "paths": _receipt_paths(book_root, paths),
            "started_at": started,
            "finished_at": _now(),
        }
        _write_exclusive(paths["receipt"], _json_bytes(receipt) + b"\n")
        if failed_reason:
            raise HostCallError(failed_reason, receipt=receipt)
        return receipt
    finally:
        if not preserve_child_cwd:
            _cleanup_child_cwd(child_temp_base, child_cwd)
        if release_lock:
            lock_path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--book-dir", required=True)
    parser.add_argument("--call-id", required=True)
    parser.add_argument("--packet", required=True)
    parser.add_argument("--command-json", required=True, help='argv JSON array or {"argv":[...],"timeout_seconds":...}')
    args = parser.parse_args(argv)
    try:
        receipt = run_host_call(args.book_dir, args.call_id, args.packet, args.command_json)
    except (HostCallError, OSError, ValueError) as exc:
        if isinstance(exc, HostCallError):
            receipt = exc.receipt
            exit_code = exc.exit_code
        else:
            receipt = {"schema_version": 1, "status": "rejected", "error": str(exc)}
            exit_code = 2
        json.dump(receipt, sys.stdout, ensure_ascii=True, indent=2)
        sys.stdout.write("\n")
        return exit_code
    json.dump(receipt, sys.stdout, ensure_ascii=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
