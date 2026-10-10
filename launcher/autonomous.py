"""Launch the verified skill's controlled workflow, retaining native sign-in."""
from pathlib import Path
import sys
from uuid import uuid4

from launcher.native import codex_scoped_command, find_native, run_attached


def launch_controlled(root: Path, config: dict, *, model, effort, author_name):
    # Import here to keep cli -> autonomous -> cli out of module initialization.
    from launcher.cli import _ownership, _write_json, _now, LOCK

    if config["host"] != "codex":
        raise ValueError("Controlled unattended execution is currently verified only for the native Codex command")
    if model != config.get("model") or effort != config.get("effort") or author_name not in (None, config.get("author_name")):
        raise ValueError("An unattended run freezes model, effort and author; start a new project to change them")
    if not config.get("author_name"):
        raise ValueError("Unattended execution needs --author when preparing the new project")
    command = codex_scoped_command(find_native("codex"), model=model, effort=effort)
    command_file = root / ".book-genesis/native-command.json"
    if command_file.exists():
        import json
        if json.loads(command_file.read_text(encoding="utf-8")) != command:
            raise ValueError("The native executable selection changed; preserve the frozen run instead of silently switching")
    else:
        _write_json(command_file, command, exclusive=True)
    contract = config["autonomous_contract"]
    argv = [sys.executable, "-u", str(root / ".book-genesis/skills/book-genesis/scripts/autonomous_book.py"),
            "--book-dir", str(root), "--command-file", str(command_file)]
    for name in ("chapters", "min_words", "max_words", "quality_target"):
        argv += ["--" + name.replace("_", "-"), str(contract[name])]
    with _ownership(root):
        folder = root / ".book-genesis/launches"
        folder.mkdir(exist_ok=True)
        path = folder / (uuid4().hex + ".json")
        record = {"schema_version": 1, "host": "codex", "mode": "controlled_native", "model": model, "effort": effort,
                  "scoped_command": command, "status": "launching", "started_at": _now(), "book_completion": "not_assessed"}
        _write_json(path, record, exclusive=True)
        def started(pid):
            record.update(native_pid=pid, status="workflow_running")
            _write_json(path, record)
            _write_json(root / LOCK, {"launcher_pid": __import__("os").getpid(), "native_pid": pid, "host": "codex"})
        try:
            code = run_attached(argv, cwd=root, on_start=started)
        except BaseException:
            record.update(status="interrupted", finished_at=_now())
            _write_json(path, record)
            raise
        record.update(status="completed" if code == 0 else "blocked", native_exit_code=code, finished_at=_now(),
                      book_completion="verified_by_controlled_workflow" if code == 0 else "incomplete")
        _write_json(path, record)
        return code
