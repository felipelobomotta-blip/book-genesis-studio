"""Background execution manager for Book Genesis Studio (pure Python stdlib).

Runs the official `book_genesis.py resume <book_dir>` controller in an owned
process tree (`WindowsJob` on Windows, process group on POSIX), streams stdout
and stderr to `.book-genesis/studio-console.log`, tracks live status, and lets
a non-technical user start, pause, recover proven-dead crash locks, and resume
any autonomous book end-to-end from the browser without touching a terminal.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/book-genesis/scripts"
for _p in (ROOT, SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from launcher.cli import LOCK, SKILLS, _install_path, _write_json, read_project
from runner.distribution import install_suite, verify_install
from run_host_call import _pid_state, _terminate_and_reap_owned


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json_optional(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def _tail_lines(path: Path, limit: int = 80) -> list[str]:
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-limit:]
    except OSError:
        return []


def check_locks(book_dir: Path) -> dict:
    """Check `launcher.lock` and `work/host-calls/.active.lock` using OS PID state."""
    launcher_lock = book_dir / LOCK
    host_lock = book_dir / "work/host-calls/.active.lock"
    active_pids: list[int] = []
    dead_locks: list[str] = []
    unknown_locks: list[str] = []

    for label, path, keys in (
        ("launcher.lock", launcher_lock, ("launcher_pid", "native_pid")),
        ("host-call.lock", host_lock, ("helper_pid", "child_pid")),
    ):
        if not path.is_file():
            continue
        data = _read_json_optional(path)
        if data is None:
            unknown_locks.append(label)
            continue
        states = []
        for k in keys:
            pid = data.get(k)
            if isinstance(pid, int) and pid > 0:
                st = _pid_state(pid)
                states.append((pid, st))
        if any(st is True for _, st in states):
            active_pids.extend(pid for pid, st in states if st is True)
        elif states and all(st is False for _, st in states):
            dead_locks.append(label)
        else:
            unknown_locks.append(label)

    return {
        "external_running": bool(active_pids),
        "active_pids": active_pids,
        "stale_lock": bool(dead_locks) and not active_pids and not unknown_locks,
        "dead_locks": dead_locks,
        "unknown_locks": unknown_locks,
    }


def clear_proven_dead_locks(book_dir: Path) -> list[str]:
    info = check_locks(book_dir)
    if info["external_running"] or info["unknown_locks"]:
        raise ValueError("An active or indeterminate process owns this book; refusing to clear its lock.")
    removed = []
    for rel in (LOCK, Path("work/host-calls/.active.lock")):
        target = book_dir / rel
        if target.is_file():
            target.unlink(missing_ok=True)
            removed.append(rel.as_posix())
    return removed


def ensure_ready_for_studio_run(book_dir: Path, *, default_contract: dict, default_models: dict[str, str]) -> dict:
    """Prepare or refresh an unstarted book if needed; never alter a started workflow."""
    config_path = _install_path(book_dir / ".book-genesis/project.json")
    if not config_path.is_file():
        raise ValueError("Folder is not a valid Book Genesis project.")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    workflow_started = (book_dir / ".book-genesis/workflow.json").is_file() or (book_dir / "PROJECT_STATE.yaml").is_file()

    # Upgrade check-in -> autonomous ONLY when zero workflow/state files exist yet.
    if not config.get("autonomous_contract") or config.get("collaboration") != "autonomous":
        if workflow_started:
            raise ValueError(
                "This book was already started in interactive terminal mode (no autonomous contract). "
                "Resume it in a terminal with `python book_genesis.py resume` or start a new book in Studio."
            )
        host = str(config.get("host") or "codex")
        config["collaboration"] = "autonomous"
        config["model"] = config.get("model") or default_models.get(host, "gpt-5.6-luna")
        config["effort"] = config.get("effort") or "high"
        config["author_name"] = config.get("author_name") or "Anonymous"
        config["autonomous_contract"] = dict(default_contract)
        _write_json(config_path, config)

    # Refresh installed skill snapshot ONLY if no workflow journal exists yet.
    if not (book_dir / ".book-genesis/workflow.json").is_file():
        host = str(config["host"])
        dest = _install_path(book_dir / SKILLS)
        verified = verify_install(host, destination=dest)
        if not verified["ok"]:
            agents = _install_path(book_dir / ".claude/agents") if host == "claude" else None
            refreshed = install_suite(host, destination=dest, agents_destination=agents, force=True)
            if not refreshed["ok"]:
                raise ValueError("Could not refresh local skill snapshot: " + "; ".join(refreshed["errors"]))

    return read_project(book_dir)


@dataclass
class ManagedRun:
    slug: str
    book_dir: Path
    process: subprocess.Popen
    job: object | None
    started_at: str
    log_path: Path
    state_path: Path
    finished_at: str | None = None
    exit_code: int | None = None
    stopped_by_user: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)


class StudioRunnerManager:
    """Owns background `book_genesis.py resume` processes spawned from the Studio UI."""

    def __init__(self, books_root: Path, *, command_builder: Callable[[Path], list[str]] | None = None):
        self.books_root = books_root
        self._runs: dict[str, ManagedRun] = {}
        self._guard = threading.RLock()
        self._command_builder = command_builder or self._default_command

    @staticmethod
    def _default_command(book_dir: Path) -> list[str]:
        return [sys.executable, "-u", str(ROOT / "book_genesis.py"), "resume", str(book_dir.resolve())]

    def _persist_state(self, run: ManagedRun, status: str, extra: dict | None = None) -> None:
        payload = {
            "schema_version": 1,
            "slug": run.slug,
            "status": status,
            "pid": run.process.pid,
            "started_at": run.started_at,
            "finished_at": run.finished_at,
            "exit_code": run.exit_code,
            "stopped_by_user": run.stopped_by_user,
        }
        if extra:
            payload.update(extra)
        try:
            _write_json(run.state_path, payload)
        except OSError:
            pass

    def start_or_resume(
        self,
        slug: str,
        book_dir: Path,
        *,
        default_contract: dict,
        default_models: dict[str, str],
        recover_stale_lock: bool = False,
    ) -> dict:
        with self._guard:
            existing = self._runs.get(slug)
            if existing is not None and existing.process.poll() is None:
                return self.inspect(slug, book_dir)

            journal = _read_json_optional(book_dir / ".book-genesis/workflow.json") or {}
            if journal.get("status") == "completed" and (book_dir / "delivery/export-receipt.json").is_file():
                return self.inspect(slug, book_dir)

            lock_info = check_locks(book_dir)
            if lock_info["external_running"]:
                raise ValueError(f"This book is already running in another process (PID {lock_info['active_pids']}).")
            if lock_info["stale_lock"]:
                if not recover_stale_lock:
                    raise ValueError("STALE_LOCK: A previous run was interrupted and left a dead lock. Click 'Unlock & Resume'.")
                clear_proven_dead_locks(book_dir)
            elif lock_info["unknown_locks"]:
                raise ValueError("An indeterminate lock file exists under .book-genesis; verify before resuming.")

            ensure_ready_for_studio_run(book_dir, default_contract=default_contract, default_models=default_models)

            meta_dir = book_dir / ".book-genesis"
            meta_dir.mkdir(parents=True, exist_ok=True)
            log_path = meta_dir / "studio-console.log"
            state_path = meta_dir / "studio-run.json"
            argv = self._command_builder(book_dir)

            job = None
            flags = 0
            if os.name == "nt":
                from launcher.windows_job import CREATE_SUSPENDED, WindowsJob
                job = WindowsJob()
                flags = subprocess.CREATE_NEW_PROCESS_GROUP | CREATE_SUSPENDED

            started_at = _now()
            with log_path.open("a", encoding="utf-8") as log_init:
                log_init.write(f"\n=== [{started_at}] Studio iniciou geração/retomada: {' '.join(argv)} ===\n")

            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"

            try:
                proc = subprocess.Popen(
                    argv,
                    cwd=str(book_dir),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=False,
                    start_new_session=os.name != "nt",
                    creationflags=flags,
                    env=env,
                )
                if job is not None:
                    proc._book_genesis_job = job
                    job.assign(proc.pid)
                    job.resume(proc.pid)
            except BaseException:
                if job is not None:
                    job.close()
                raise

            managed = ManagedRun(
                slug=slug,
                book_dir=book_dir,
                process=proc,
                job=job,
                started_at=started_at,
                log_path=log_path,
                state_path=state_path,
            )
            self._runs[slug] = managed
            self._persist_state(managed, "running")

            watcher = threading.Thread(target=self._watch_process, args=(managed,), daemon=True)
            watcher.start()
            return self.inspect(slug, book_dir)

    def _watch_process(self, run: ManagedRun) -> None:
        try:
            assert run.process.stdout is not None
            with run.log_path.open("a", encoding="utf-8", errors="replace") as log_handle:
                for raw_line in iter(run.process.stdout.readline, b""):
                    text = raw_line.decode("utf-8", errors="replace")
                    log_handle.write(text)
                    log_handle.flush()
        except OSError:
            pass
        finally:
            if run.process.stdout is not None:
                try:
                    run.process.stdout.close()
                except OSError:
                    pass
            code = run.process.wait()
            if run.job is not None:
                try:
                    run.job.stop()
                    run.job.close()
                except OSError:
                    pass
            with run.lock:
                run.exit_code = code
                run.finished_at = _now()
                if run.stopped_by_user:
                    final_status = "paused"
                    try:
                        clear_proven_dead_locks(run.book_dir)
                    except ValueError:
                        pass
                elif code == 0:
                    final_status = "completed"
                else:
                    final_status = "blocked"
                self._persist_state(run, final_status)
                try:
                    with run.log_path.open("a", encoding="utf-8") as log_end:
                        log_end.write(f"=== [{run.finished_at}] Processo finalizado ({final_status}, código {code}) ===\n")
                except OSError:
                    pass

    def stop(self, slug: str, book_dir: Path) -> dict:
        with self._guard:
            run = self._runs.get(slug)
        if run is None or run.process.poll() is not None:
            return self.inspect(slug, book_dir)
        with run.lock:
            run.stopped_by_user = True
        verified = _terminate_and_reap_owned(run.process)
        if run.job is not None:
            try:
                verified = run.job.stop() and verified
            except OSError:
                verified = False
        deadline = time.monotonic() + 3.0
        while run.finished_at is None and time.monotonic() < deadline:
            time.sleep(0.05)
        if verified:
            try:
                clear_proven_dead_locks(book_dir)
            except ValueError:
                pass
        return self.inspect(slug, book_dir)

    def shutdown_all(self) -> None:
        with self._guard:
            active = list(self._runs.values())
        for run in active:
            if run.process.poll() is None:
                try:
                    self.stop(run.slug, run.book_dir)
                except Exception:
                    pass

    def inspect(self, slug: str, book_dir: Path) -> dict:
        with self._guard:
            run = self._runs.get(slug)
        meta_dir = book_dir / ".book-genesis"
        log_path = meta_dir / "studio-console.log"
        saved_state = _read_json_optional(meta_dir / "studio-run.json") or {}
        journal = _read_json_optional(meta_dir / "workflow.json") or {}
        lock_info = check_locks(book_dir)

        studio_running = bool(run is not None and run.process.poll() is None)
        running = studio_running or lock_info["external_running"]

        if running:
            state = "running"
        elif journal.get("status") == "completed":
            state = "completed"
        elif saved_state.get("status") == "paused":
            state = "paused"
        elif journal.get("status") in {"blocked", "waiting_for_provider"} or saved_state.get("status") == "blocked":
            state = "blocked"
        else:
            state = "idle"

        delivery_status = None
        if (book_dir / "DELIVERY_STATUS.md").is_file():
            try:
                delivery_status = (book_dir / "DELIVERY_STATUS.md").read_text(encoding="utf-8")
            except OSError:
                pass

        return {
            "running": running,
            "studio_owned": studio_running,
            "state": state,
            "pid": (run.process.pid if studio_running and run else (lock_info["active_pids"][0] if lock_info["active_pids"] else saved_state.get("pid"))),
            "started_at": run.started_at if run else saved_state.get("started_at"),
            "finished_at": run.finished_at if run else saved_state.get("finished_at"),
            "exit_code": run.exit_code if run else saved_state.get("exit_code"),
            "stale_lock": False if running else lock_info["stale_lock"],
            "journal_error": journal.get("error"),
            "delivery_status": delivery_status,
            "log_tail": _tail_lines(log_path, 80),
            "run_report_tail": _tail_lines(book_dir / "RUN_REPORT.md", 30),
        }
