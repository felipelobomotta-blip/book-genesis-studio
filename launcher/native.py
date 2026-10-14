"""Discover and invoke official CLIs without a shell or credential-store access."""

from __future__ import annotations

from contextlib import contextmanager
import json
import importlib.util
import os
from pathlib import Path
import shutil
import signal
import subprocess
import threading
import time
from typing import Callable

from runner.filesystem import SKILL_ROOT


HOSTS = ("codex", "claude")
HOST_NAMES = {"codex": "Codex", "claude": "Claude Code"}
INSTALL_URLS = {
    "codex": "https://learn.chatgpt.com/docs/cli",
    "claude": "https://code.claude.com/docs/en/setup",
}


def find_native(host: str) -> list[str]:
    """Resolve an executable; translate only known npm shims on Windows.

    Popen must never receive a .cmd/.bat file: Windows can implicitly run those
    through cmd.exe even with shell=False. User text never enters a shell.
    No provider binary, auth setting or environment credential is modified.
    """
    if host not in HOSTS:
        raise ValueError(f"Unsupported native host: {host}")
    found = shutil.which(host)
    if found is None:
        raise ValueError(f"{HOST_NAMES[host]} is not on PATH. Install it yourself: {INSTALL_URLS[host]}")
    path = Path(found).resolve()
    if os.name != "nt" or path.suffix.lower() not in {".cmd", ".bat", ".ps1"}:
        return [str(path)]

    package = "@openai/codex" if host == "codex" else "@anthropic-ai/claude-code"
    package_root = path.parent / "node_modules" / package
    if host == "claude":
        binary = package_root / "bin" / "claude.exe"
        if binary.is_file():
            return [str(binary)]
    script = package_root / ("bin/codex.js" if host == "codex" else "cli.js")
    node = shutil.which("node")
    if script.is_file() and node:
        return [str(Path(node).resolve()), str(script)]
    raise ValueError(f"Cannot resolve the official executable behind {path}. Repair the native CLI installation; no shell fallback is used.")


def inspect_native(host: str) -> dict[str, object]:
    """Use native status commands. Return no email, organization or token data."""
    result: dict[str, object] = {"host": host, "name": HOST_NAMES[host], "status": "unknown"}
    try:
        executable = find_native(host)
    except ValueError as exc:
        result.update(status="unavailable", error=str(exc))
        return result
    result["executable"] = executable
    try:
        version = subprocess.run(executable + ["--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15, shell=False)
        if version.returncode != 0:
            result.update(status="error", error=f"Native version command failed (exit {version.returncode}). Run {host} --version for its diagnostic.")
            return result
        result["version"] = version.stdout.strip()
        status_args = ["login", "status"] if host == "codex" else ["auth", "status"]
        status = subprocess.run(executable + status_args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15, shell=False)
        if host == "codex":
            # Exact native status lines, not an inference from any error text.
            lines = (status.stdout + "\n" + status.stderr).splitlines()
            if status.returncode == 0 and "Logged in using ChatGPT" in lines:
                result.update(status="signed_in", account="ChatGPT plan")
            elif status.returncode == 0 and any(line.startswith("Logged in using an API key") for line in lines):
                result.update(status="signed_in", account="API billing")
            elif status.returncode != 0 and "Not logged in" in lines:
                result.update(status="signed_out", account="not signed in")
            elif status.returncode != 0:
                result.update(status="error", error=f"Native authentication command failed (exit {status.returncode}). Run codex login status.")
            else:
                result.update(status="unknown", error="Native authentication status was not recognized. Run codex login status.")
        else:
            data = json.loads(status.stdout)
            if not isinstance(data, dict) or not isinstance(data.get("loggedIn"), bool):
                raise ValueError("unsupported native status response")
            if data["loggedIn"] and status.returncode == 0:
                method = data.get("authMethod")
                result.update(status="signed_in", account="Claude plan" if method == "claude.ai" else "native provider / API billing")
            elif not data["loggedIn"]:
                result.update(status="signed_out", account="not signed in")
            else:
                result.update(status="error", error=f"Native authentication command failed (exit {status.returncode}). Run claude auth status.")
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        # Keep failure and signed-out states distinct. Do not retain raw native
        # status: it may include personal account information or an API key.
        result.update(status="error", error=f"Native status could not be checked ({type(exc).__name__}). Run {host} {'login' if host == 'codex' else 'auth'} status for its diagnostic.")
    return result


def login_argv(host: str) -> list[str]:
    return find_native(host) + (["login"] if host == "codex" else ["auth", "login"])


class NativeShutdownUnverified(RuntimeError):
    """The owned native process tree may still run; its owner must stay locked."""


def _load_guard():
    spec = importlib.util.spec_from_file_location("_book_genesis_owned_process", SKILL_ROOT / "scripts/run_host_call.py")
    if spec is None or spec.loader is None:
        raise ValueError("Cannot load the core's native process guard")
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    return guard


def _raise_interrupt(_signum, _frame):
    raise KeyboardInterrupt


@contextmanager
def _parent_signals(process: subprocess.Popen):
    """Turn termination requests into the normal owned-shutdown path.

    POSIX children run in their own session so the core can stop their whole
    tree; forward terminal resizes there so the native UI keeps its layout.
    """
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    handlers = {name: _raise_interrupt for name in ("SIGTERM", "SIGHUP", "SIGBREAK")}
    if os.name != "nt":
        handlers["SIGWINCH"] = lambda _signum, _frame: _forward_resize(process)
    previous = {}
    try:
        for name, handler in handlers.items():
            number = getattr(signal, name, None)
            if number is not None:
                previous[number] = signal.signal(number, handler)
        yield
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)


def _forward_resize(process: subprocess.Popen) -> None:
    try:
        os.killpg(process.pid, signal.SIGWINCH)
    except OSError:
        pass


def _group_alive(pid: int) -> bool:
    try:
        os.killpg(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    return True


def run_attached(argv: list[str], *, cwd: Path | None = None, on_start: Callable[[int], None] | None = None, env: dict[str, str] | None = None) -> int:
    """Inherit the terminal, with bounded shutdown of only our owned process.

    Reuse the core's existing process-tree shutdown rather than creating a
    second lifecycle implementation. Raise NativeShutdownUnverified when the
    owned tree may still be running; the caller must then retain its lock.
    """
    guard = _load_guard()
    job = None
    flags = 0
    if os.name == "nt":
        from launcher.windows_job import CREATE_SUSPENDED, WindowsJob
        job = WindowsJob()
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | CREATE_SUSPENDED
    try:
        process = subprocess.Popen(
            argv, cwd=cwd, shell=False, start_new_session=os.name != "nt",
            creationflags=flags, env=env,
        )
    except BaseException:
        if job is not None:
            job.close()
        raise
    try:
        with _parent_signals(process):
            if job is not None:
                process._book_genesis_job = job
                job.assign(process.pid)
            if on_start is not None:
                on_start(process.pid)
            if job is not None:
                job.resume(process.pid)
            # An untimed wait cannot be interrupted on Windows. A short timed
            # wait lets Ctrl+C or a termination request reach the cleanup path
            # while the native process is still alive to be stopped.
            while True:
                try:
                    code = process.wait(timeout=0.2)
                    break
                except subprocess.TimeoutExpired:
                    continue
    except BaseException:
        with _uninterruptible():
            stopped = guard._terminate_and_reap_owned(process)
            if job is not None:
                stopped = job.stop() and stopped
                job.close()
        if not stopped:
            raise NativeShutdownUnverified("Native process shutdown could not be verified. The launcher lock was kept; check that the recorded native process has stopped before removing it.")
        raise
    if job is not None:
        with _uninterruptible():
            stopped = job.stop()
            job.close()
        if not stopped:
            raise NativeShutdownUnverified("Native process shutdown could not be verified. The launcher lock was kept; check that the recorded native process has stopped before removing it.")
    # A POSIX session can outlive its leader. Do not report it as stopped while
    # owned descendants may still write to the book.
    if os.name != "nt" and _group_alive(process.pid):
        with _uninterruptible():
            guard._terminate_owned_tree(process)
            deadline = time.monotonic() + 3
            while _group_alive(process.pid) and time.monotonic() < deadline:
                time.sleep(0.05)
        if _group_alive(process.pid):
            raise NativeShutdownUnverified("The native CLI exited but processes it started could not be stopped. The launcher lock was kept.")
    return code


@contextmanager
def _uninterruptible():
    """A second Ctrl+C must not abandon a bounded shutdown halfway."""
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, previous)


def codex_scoped_command(executable: list[str], *, model: str | None, effort: str | None) -> dict:
    """A headless Codex role, separate from the parent's interactive argv."""
    argv = list(executable) + ["--no-daemon", "-a", "on-request", "exec",
                               "--skip-git-repo-check", "--sandbox", "read-only"]
    if model:
        argv += ["-m", model]
    if effort:
        argv += ["-c", "model_reasoning_effort=" + json.dumps(effort)]
    return {"argv": argv + ["-o", "{output}", "-"], "timeout_seconds": 900}


def session_argv(host: str, project: Path, prompt: str, *, model: str | None, effort: str | None) -> list[str]:
    argv = list(find_native(host))
    if host == "codex":
        argv += ["-C", str(project), "-s", "workspace-write", "-a", "on-request", "--no-alt-screen", "--no-daemon"]
        if model:
            argv += ["-m", model]
        if effort:
            argv += ["-c", "model_reasoning_effort=" + json.dumps(effort)]
    else:
        # Preserve native authentication, trust prompts, tools, permissions and
        # live UI. --bare disables subscription login and must not be used here.
        if model:
            argv += ["--model", model]
        if effort:
            argv += ["--effort", effort]
            # Native settings can reapply an env effort after process startup.
            # CLI-scoped settings merge this one key above user/project env;
            # they do not write settings, auth, permissions or provider config.
            argv += ["--settings", json.dumps({"env": {"CLAUDE_CODE_EFFORT_LEVEL": effort}})]
    # Avoid interpreting an author-controlled leading dash as a native flag.
    return argv + ["--", prompt]
