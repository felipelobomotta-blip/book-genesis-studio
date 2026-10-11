"""Launch the verified skill's controlled workflow, retaining native sign-in."""
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from launcher.native import codex_scoped_command, find_native, run_attached


def controlled_command(executable, *, model, effort, host="codex", bridge=None, context_window=None):
    """Capability-check the installed CLI; auth and execpolicy remain native."""
    if not model or not effort:
        raise ValueError("Unattended isolation requires an explicit --model and --effort; no silent native-default substitution")
    if host not in {"codex", "claude"}:
        raise ValueError("Unsupported controlled native host")
    if context_window is not None and (host != "codex" or type(context_window) is not int
            or not 8192 <= context_window <= 1050000):
        raise ValueError("An explicit native context window requires Codex and 8192--1050000 tokens")
    help_result = subprocess.run(list(executable) + (["exec", "--help"] if host == "codex" else ["--help"]), capture_output=True,
                                 text=True, encoding="utf-8", timeout=15, shell=False)
    if host == "claude":
        import json
        flags = ("--restricted", "--tools", "--strict-mcp-config", "--disable-slash-commands",
                 "--no-session-persistence", "--setting-sources", "--model", "--effort", "--output-format", "--json-schema", "--print")
        if help_result.returncode or any(flag not in help_result.stdout for flag in flags):
            raise ValueError("Unattended isolation requires native Claude restricted mode and subscription-preserving scoped flags")
        if not bridge or not Path(bridge).is_file():
            raise ValueError("Verified native Claude transport is missing from this book's installed skill")
        if model.lower() in {"opus", "sonnet", "haiku", "fable", "default"}:
            raise ValueError("Unattended Claude requires an exact model ID, not a changing native alias")
        return {"argv": [sys.executable, "-u", str(bridge), "--native-command-json", json.dumps(list(executable)),
                         "--model", model, "--effort", effort, "-o", "{output}", "-"], "timeout_seconds": 900}
    if help_result.returncode or any(flag not in help_result.stdout for flag in ("--ignore-user-config", "--ephemeral")):
        raise ValueError("Unattended isolation requires a native Codex exec with --ignore-user-config and --ephemeral support; no automatic CLI replacement")
    command = codex_scoped_command(executable, model=model, effort=effort)
    index = command["argv"].index("exec") + 1
    command["argv"][index:index] = ["--ignore-user-config", "--ephemeral"]
    if context_window is not None:
        # Per-book overrides only. This declares the requested native capacity;
        # successful native calls, not this flag, establish account support.
        command["argv"][index:index] = ["-c", f"model_context_window={context_window}",
            "-c", f"model_auto_compact_token_limit={int(context_window * .95)}"]
    return command


def launch_controlled(root: Path, config: dict, *, model, effort, author_name):
    # Import here to keep cli -> autonomous -> cli out of module initialization.
    from launcher.cli import _ownership, _write_json, _now, LOCK

    host = config["host"]
    if host not in {"codex", "claude"}:
        raise ValueError("Controlled unattended execution needs a supported native host")
    if model != config.get("model") or effort != config.get("effort") or author_name not in (None, config.get("author_name")):
        raise ValueError("An unattended run freezes model, effort and author; start a new project to change them")
    if not config.get("author_name"):
        raise ValueError("Unattended execution needs --author when preparing the new project")
    command = controlled_command(find_native(host), model=model, effort=effort, host=host,
        bridge=root / ".book-genesis/skills/book-genesis/scripts/native_claude.py",
        context_window=config["autonomous_contract"].get("native_context_window"))
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
    if contract.get("weighted_quality_target") is not None:
        argv += ["--weighted-quality-target", str(contract["weighted_quality_target"])]
    with _ownership(root):
        folder = root / ".book-genesis/launches"
        folder.mkdir(exist_ok=True)
        path = folder / (uuid4().hex + ".json")
        record = {"schema_version": 1, "host": host, "mode": "controlled_native", "model": model, "effort": effort,
                  "scoped_command": command, "status": "launching", "started_at": _now(), "book_completion": "not_assessed"}
        _write_json(path, record, exclusive=True)
        def started(pid):
            record.update(native_pid=pid, status="workflow_running")
            _write_json(path, record)
            _write_json(root / LOCK, {"launcher_pid": __import__("os").getpid(), "native_pid": pid, "host": host})
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
