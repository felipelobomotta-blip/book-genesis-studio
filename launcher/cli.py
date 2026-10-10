"""A small, local entry point for the same Book Genesis skill and native UI.

It prepares and verifies a project, then hands the terminal to an official
agent. It does not create another editorial engine, OAuth client or API proxy.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from hashlib import sha256
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from uuid import uuid4

from launcher.native import HOST_NAMES, HOSTS, NativeShutdownUnverified, codex_scoped_command, find_native, inspect_native, login_argv, run_attached, session_argv
from runner.distribution import INSTALL_RECORD, install_suite, verify_install
from runner.filesystem import load_manifest


CONFIG = Path(".book-genesis/project.json")
SKILLS = Path(".book-genesis/skills")
LOCK = Path(".book-genesis/launcher.lock")
EFFORTS = ("minimal", "low", "medium", "high", "xhigh", "max")


def _install_path(path: Path) -> Path:
    """Keep deep Windows paths usable without changing system settings.

    The book folder and native working directory keep their ordinary path.
    Installer staging, verification and launcher metadata use Windows'
    documented extended absolute form, so a folder near MAX_PATH still works.
    """
    absolute = str(path.resolve())
    if os.name != "nt" or absolute.startswith("\\\\?\\"):
        return Path(absolute)
    if absolute.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + absolute[2:])
    return Path("\\\\?\\" + absolute)


def _same_path(left: str | Path, right: str | Path) -> bool:
    def plain(value: str | Path) -> str:
        text = str(value)
        if text.startswith("\\\\?\\UNC\\"):
            text = "\\\\" + text[8:]
        elif text.startswith("\\\\?\\"):
            text = text[4:]
        return os.path.normcase(os.path.normpath(text))
    return plain(left) == plain(right)


def _has_terminal() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, value: object, *, exclusive: bool = False) -> None:
    data = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if exclusive:
        with path.open("xb") as handle:
            handle.write(data)
        return
    temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    try:
        temporary.write_bytes(data)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _profile(host: str, model: str | None, effort: str | None) -> None:
    if host not in HOSTS:
        raise ValueError("Choose codex or claude")
    if model is not None and (not model.strip() or model.startswith("-") or any(char in model for char in "\r\n\0")):
        raise ValueError("Model must be a nonempty native model name")
    if effort is not None and (effort not in EFFORTS or host == "claude" and effort == "minimal"):
        raise ValueError(f"Unsupported effort for {host}: {effort}")


def _author_name(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip() or any(char in value for char in "\r\n\0"):
        raise ValueError("Author must be a nonempty, single-line title-page name")
    return value.strip()


def _resume_command(root: Path, *, model: str | None = None, effort: str | None = None, author_name: str | None = None) -> str:
    # Display a copyable PowerShell command on Windows and a POSIX command
    # elsewhere. User text must not become shell expansion in this guidance.
    quote = (lambda value: "'" + str(value).replace("'", "''") + "'") if os.name == "nt" else shlex.quote
    command = "python book_genesis.py resume " + quote(str(root))
    for flag, value in (("--model", model), ("--effort", effort), ("--author", author_name)):
        if value is not None:
            command += " " + flag + " " + quote(value)
    return command


def prepare_project(project: Path, *, host: str, idea: str, language: str = "English", model: str | None = None, effort: str | None = None, autonomous: bool = False, author_name: str | None = None, autonomous_contract: dict | None = None) -> dict[str, object]:
    _profile(host, model, effort)
    author_name = _author_name(author_name)
    if not idea.strip() or not language.strip():
        raise ValueError("The idea and book language must not be empty")
    project = project.expanduser().absolute()
    if project.is_symlink():
        raise ValueError("Project is a link; choose the real folder")
    if project.exists() and (not project.is_dir() or any(project.iterdir())):
        raise ValueError("New project folder must be empty. Use resume for an existing launcher project.")
    created = not project.exists()
    project.mkdir(parents=True, exist_ok=True)
    project = project.resolve()
    metadata = project / ".book-genesis"
    try:
        metadata.mkdir()  # Atomically claim preparation before any installer output.
    except FileExistsError as exc:
        raise ValueError("Another preparation already owns this folder. Use resume after it finishes.") from exc
    owned = [metadata]
    try:
        if host == "claude":
            agents_folder = project / ".claude"
            agents_folder.mkdir()
            owned.append(agents_folder)
        agents = _install_path(project / ".claude/agents") if host == "claude" else None
        installed = install_suite(host, destination=_install_path(project / SKILLS), agents_destination=agents)
        if not installed["ok"]:
            raise ValueError("Local skill installation failed: " + "; ".join(str(item) for item in installed["errors"]))
        verified = verify_install(host, destination=_install_path(project / SKILLS))
        if not verified["ok"]:
            raise ValueError("Local skill verification failed: " + "; ".join(str(item) for item in verified["errors"]))
        config: dict[str, object] = {
            "schema_version": 1, "host": host, "model": model, "effort": effort,
            "idea": idea.strip(), "language": language.strip(),
            "author_name": author_name,
            "collaboration": "autonomous" if autonomous else "check-in",
            "created_at": _now(), "execution": "native_interactive",
        }
        if autonomous_contract is not None:
            config["autonomous_contract"] = autonomous_contract
        _write_json(_install_path(project / CONFIG), config, exclusive=True)
    except BaseException:
        # Delete only directories this attempt claimed. Recheck resolved
        # targets before recursive removal; a replaced link must not redirect
        # cleanup outside the book. Preserve files created by another writer.
        for folder in reversed(owned):
            try:
                target = folder.resolve()
                if target.parent != project or target != folder:
                    print(f"Partial preparation kept: {folder} now points outside its original location.", file=sys.stderr)
                    continue
                shutil.rmtree(_install_path(target))
            except (OSError, RuntimeError) as exc:
                print(f"Partial preparation kept at {folder}: {exc}", file=sys.stderr)
        if created:
            try:
                project.rmdir()
            except OSError:
                pass
        raise
    return config


def read_project(project: Path, *, verify_snapshot: bool = True) -> dict[str, object]:
    root = project.expanduser().resolve()
    try:
        data = json.loads(_install_path(root / CONFIG).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"{root} is not a Book Genesis launcher project ({CONFIG.as_posix()} is missing). Use new with an empty folder.") from None
    if not isinstance(data, dict) or data.get("schema_version") != 1 or data.get("execution") != "native_interactive":
        raise ValueError("Unsupported launcher project record")
    host, model, effort = data.get("host"), data.get("model"), data.get("effort")
    if not isinstance(host, str) or model is not None and not isinstance(model, str) or effort is not None and not isinstance(effort, str):
        raise ValueError("Invalid native host selection in project record")
    _profile(host, model, effort)
    _author_name(data.get("author_name"))  # Older records may omit this field.
    if data.get("collaboration") not in {"check-in", "autonomous"}:
        raise ValueError("Invalid collaboration mode in project record")
    if any(not isinstance(data.get(field), str) or not str(data[field]).strip() for field in ("idea", "language")):
        raise ValueError("Invalid idea or language in project record")
    if not verify_snapshot:
        return data
    result = verify_install(host, destination=_install_path(root / SKILLS))
    if not result["ok"]:
        raise ValueError("Skill snapshot differs from this checkout or its install record. Resume using the original checkout; no automatic upgrade: " + "; ".join(str(item) for item in result["errors"]))
    if host == "claude":
        # The install record names an absolute agents folder. A moved or copied
        # book would otherwise be checked against the original location.
        record = json.loads(_install_path(root / SKILLS / INSTALL_RECORD).read_text(encoding="utf-8"))
        if not _same_path(str(record.get("agents_root", "")), root / ".claude/agents"):
            raise ValueError("This book's Claude agents were verified in another folder (the project was moved or copied). Prepare a new project with new; no automatic upgrade.")
    return data


def start_prompt(config: dict[str, object], *, resumed: bool, model: str | None = None, effort: str | None = None, author_name: str | None = None) -> str:
    mode = "Resume the saved book from its actual files" if resumed else "Start the author's new book"
    author_name = _author_name(author_name)
    if author_name is not None:
        author_note = "The exact title-page author for this invocation is " + json.dumps(author_name) + "; use it in the book and export metadata, overriding the original default. "
    else:
        author_note = "The original project's title-page author is " + json.dumps(_author_name(config.get("author_name"))) + ". Retain a newer explicit author credit already saved with this book; use the project default only if no newer credit exists. "
    native_role_settings = ""
    if config["host"] == "codex":
        native_role_settings = (
            "For scoped Codex roles, use run_host_call.py --book-dir . --call-id <fresh-id> --packet <packet-file> "
            "--launch-receipt <the-matching-launch-receipt>. The launcher supplies its tested headless exec command. "
            "For a structured role, add --output-schema <absolute-schema-path>; for a canary add --timeout-seconds 60. "
            "Do not rebuild the argv, reuse the interactive native_command, omit exec, or invent CLI flags. "
        )
    if config["host"] == "claude" and effort is not None:
        native_role_settings = (
            "For scoped fresh Claude CLI roles, pass the selected --effort and CLI-scoped --settings "
            + json.dumps({"env": {"CLAUDE_CODE_EFFORT_LEVEL": effort}})
            + "; saved native env settings can otherwise override the role's effort. "
        )
    return (
        "Book Genesis writing session. You are already running inside the native CLI; the launcher has completed project setup. " + mode + ". "
        "The book and author-facing language is " + json.dumps(config["language"]) + "; use it from your first public message. "
        "Read .book-genesis/project.json for the author's idea, language and collaboration mode. "
        + author_note +
        "If no author credit is saved or supplied, ask at the first author checkpoint before drafting, not at export. "
        "Never infer a publishing name from account credentials or the computer's username. "
        "Read .book-genesis/skills/book-genesis/SKILL.md and apply that exact project-local build. "
        "Resolve its references from .book-genesis/skills/book-genesis, not a global installation. "
        "Read its references/pipeline/host-contract.md and references/prompts/orchestrator.md first. "
        "You are the single owning orchestrator; this launcher has no second book-writing agent. "
        "Treat .book-genesis/launcher.lock as the parent launcher's ownership record; never kill or clear it. "
        "Use the existing run_host_call.py only for scoped independent roles, never for another whole-book orchestrator. "
        "The launch receipt whose native_pid matches launcher.lock names the resolved native executable. "
        "Reuse that executable prefix for scoped native roles instead of resolving a different CLI version from a tool's PATH. "
        "Use this folder for the book. The launcher verified the installed snapshot before starting you. "
        "Read .book-genesis/skills/.book-genesis-install.json and reference that existing verification record in RUN_REPORT.md. "
        "Any additional hashes must be computed and saved by a program, never manually transcribed. "
        "Honor saved pending author checkpoints on resume; do not auto-accept them. "
        "Write public phase, role, chapter and saved-file progress as ordinary commentary; the native terminal renders it automatically. "
        "Use your file and command tools to create the book. Do not inspect or drive your own terminal window, reopen the launcher, or build another UI. "
        "Use the selected native model and effort; verify and propagate explicit selections to scoped calls. "
        "The explicit selections for this invocation are " + json.dumps({"model": model, "effort": effort}) + "; null means the native configured default. "
        "These invocation selections override the original model and effort in project.json when resuming. " + native_role_settings +
        "Scoped fresh role sessions in the selected host " + str(config["host"]) + " are part of this book workflow, subject to native permissions; use the core's actual isolation check and grade. "
        "Ask before spending another host's quota. Never silently switch to another provider or paid API. "
        "Do not claim current reviews or complete delivery without the core's evidence checks. "
        "Keep the original manuscript and failed attempts. "
        "The author originally requested " + str(config["collaboration"]) + " collaboration; "
        "an existing PROJECT_STATE.yaml remains authoritative for subsequent author decisions. "
        "When this is a new autonomous project, go to the end subject to the core's real blockers. "
        "Write the book and author-facing messages in the requested book language."
    )


@contextmanager
def _ownership(project: Path):
    lock = _install_path(project / LOCK)
    try:
        _write_json(lock, {"launcher_pid": os.getpid(), "started_at": _now()}, exclusive=True)
    except FileExistsError as exc:
        raise ValueError(f"A launcher already owns this project ({project / LOCK}). Do not start another one. If a session crashed, check that the recorded launcher and native PIDs have stopped before removing a stale lock.") from exc
    try:
        yield
    except NativeShutdownUnverified:
        # The owned native process tree may still be running.
        raise
    except BaseException:
        lock.unlink(missing_ok=True)
        raise
    else:
        lock.unlink(missing_ok=True)


def launch_project(project: Path, config: dict[str, object], *, host: str, model: str | None, effort: str | None, resumed: bool, author_name: str | None = None) -> int:
    _profile(host, model, effort)
    root = project.expanduser().resolve()
    if not _has_terminal():
        raise ValueError("The native agent needs an interactive terminal. Open a terminal and run: " + _resume_command(root, model=model, effort=effort, author_name=author_name))
    prompt = start_prompt(config, resumed=resumed, model=model, effort=effort, author_name=author_name)
    argv = session_argv(host, root, prompt, model=model, effort=effort)
    # Scope the explicit effort to the child too. session_argv also overrides
    # the native saved env setting; it can be reapplied after process startup.
    native_environment = None
    if host == "claude" and effort is not None:
        native_environment = os.environ.copy()
        native_environment["CLAUDE_CODE_EFFORT_LEVEL"] = effort
    with _ownership(root):
        launches = _install_path(root / ".book-genesis/launches")
        launches.mkdir(exist_ok=True)
        receipt = launches / (uuid4().hex + ".json")
        record = {
            "schema_version": 1, "status": "launching", "resumed": resumed, "host": host, "model": model, "effort": effort,
            # The exact native command, minus the long prompt it ends with.
            "native_command": argv[:-1], "prompt_sha256": sha256(prompt.encode("utf-8")).hexdigest(),
            "started_at": _now(), "native_exit_code": None, "book_completion": "not_assessed",
        }
        if host == "codex" and "-C" in argv:
            # session_argv owns this layout: the resolved executable prefix is
            # followed by -C. Reuse those exact paths, never resolve PATH again.
            record["scoped_command"] = codex_scoped_command(argv[:argv.index("-C")], model=model, effort=effort)
        _write_json(receipt, record, exclusive=True)
        print(f"Opening {HOST_NAMES[host]}. The native UI owns sign-in, permissions and live activity.", flush=True)
        print(f"Book folder: {root}", flush=True)
        # Inherit terminal and account environment, with only the explicit
        # Claude effort scoped above. No buffering, hidden daemon,
        # subprocess prompt rewriting, key extraction or credential redirection.
        def record_native_pid(pid: int) -> None:
            _write_json(_install_path(root / LOCK), {"launcher_pid": os.getpid(), "native_pid": pid, "host": host, "started_at": record["started_at"]})
            record.update(status="native_session_running", native_pid=pid)
            _write_json(receipt, record)

        try:
            exit_code = run_attached(argv, cwd=root, on_start=record_native_pid, env=native_environment)
        except BaseException as exc:
            status = "shutdown_unverified" if isinstance(exc, NativeShutdownUnverified) else "interrupted" if isinstance(exc, KeyboardInterrupt) else "launch_failed"
            record.update(status=status, error=str(exc) or type(exc).__name__, finished_at=_now())
            try:
                _write_json(receipt, record)
            except OSError:
                pass  # Never let a receipt error replace the original outcome or lock decision.
            raise
        record.update(status="native_session_exited", native_exit_code=exit_code, finished_at=_now())
        _write_json(receipt, record)
        print(f"Native session exited ({exit_code}). A session exit is not proof of a complete book.")
        print("Saved work stays in this folder. Use resume to continue, or status to run the read-only core checks.")
        return exit_code


def _choose_host(selected: str | None) -> str:
    if selected:
        find_native(selected)
        return selected
    available: list[str] = []
    for host in HOSTS:
        try:
            find_native(host)
            available.append(host)
        except ValueError:
            pass
    if not available:
        raise ValueError("Install Codex or Claude Code first. Run doctor for official installation links.")
    if len(available) == 1:
        return available[0]
    if not sys.stdin.isatty():
        raise ValueError("Both native hosts are available. Select one with --host codex or --host claude.")
    for number, host in enumerate(available, 1):
        print(f"{number}. {HOST_NAMES[host]}")
    answer = input("Use which agent? [1]: ").strip() or "1"
    if not answer.isdigit() or not 1 <= int(answer) <= len(available):
        raise ValueError("Choose one of the numbered native agents")
    return available[int(answer) - 1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="book-genesis", description="Use the same Book Genesis skill in your existing native agent. Local launcher prototype; no provider API backend.")
    commands = parser.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor", help="Check native CLI versions and sign-in; no model call")
    doctor.add_argument("--json", action="store_true")
    connect = commands.add_parser("connect", help="Open the official CLI's own sign-in flow")
    connect.add_argument("host", choices=HOSTS)
    for name in ("new", "resume"):
        command = commands.add_parser(name, help="Prepare and open a new book" if name == "new" else "Resume a launcher project from its saved files")
        command.add_argument("project", type=Path)
        command.add_argument("--host", choices=HOSTS)
        command.add_argument("--model", default=None, help="Exact native model; omitted means the native configured default")
        command.add_argument("--effort", choices=EFFORTS, default=None)
        command.add_argument("--author", default=None, help="Exact title-page author or pen name; overrides the original name for this invocation")
        command.add_argument("--prepare-only", action="store_true", help="Verify the project and print the launch plan without calling a model")
        if name == "new":
            ideas = command.add_mutually_exclusive_group()
            ideas.add_argument("--idea")
            ideas.add_argument("--idea-file", type=Path)
            command.add_argument("--language", default="English")
            command.add_argument("--autonomous", action="store_true", help="Request the existing core's go-to-the-end mode")
            command.add_argument("--chapters", type=int, default=12, help="Unattended Codex production contract (default 12)")
            command.add_argument("--min-words", type=int, default=40000)
            command.add_argument("--max-words", type=int, default=48000)
            command.add_argument("--quality-target", type=float, default=8.5, help="Private calibrated craft floor; never sent to writers or critics")
    status = commands.add_parser("status", help="Run the existing core's read-only progress and delivery checks")
    status.add_argument("project", type=Path)
    status.add_argument("--json", action="store_true", help="Print the full read-only evidence as one JSON object")
    return parser


def _run(args: argparse.Namespace) -> int:
    if args.command == "doctor":
        checks = [inspect_native(host) for host in HOSTS]
        if args.json:
            print(json.dumps({"hosts": checks, "model_calls": 0}, indent=2))
        else:
            for item in checks:
                print(f"{item['name']}: {item['status']} | {item.get('version', 'version unavailable')} | {item.get('account', 'account unknown')}")
                if item.get("error"):
                    print(f"  {item['error']}")
            print("Sign-in is owned by each official CLI. Plan limits and any enabled extra usage still apply.")
        return 0 if any(item["status"] == "signed_in" for item in checks) else 1
    if args.command == "connect":
        if not _has_terminal():
            raise ValueError("Open connect in your terminal to complete the official sign-in flow")
        return run_attached(login_argv(args.host))
    root = args.project.expanduser().absolute()
    if args.command == "status":
        from launcher.status import collect_status, print_status

        config = read_project(root, verify_snapshot=False)
        # Status inspects saved work using this checkout's trusted read-only
        # helpers. An old or changed project skill must block resume, not hide
        # the manuscript or execute a modified installed verifier.
        scripts = Path(__file__).resolve().parents[1] / "skills/book-genesis/scripts"
        report = collect_status(root, scripts)
        report["verification_engine"] = "current_checkout"
        try:
            read_project(root)
            report["resume_snapshot"] = {"status": "verified"}
        except (OSError, ValueError) as exc:
            report["resume_snapshot"] = {"status": "blocked", "error": str(exc)}
        report["project"] = {key: config[key] for key in ("host", "language", "collaboration")}
        report["launcher"] = _launcher_state(root)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"Book Genesis project | {HOST_NAMES[str(config['host'])]} | language: {config['language']} | collaboration: {config['collaboration']}")
            _print_launcher_state(report["launcher"])
            print_status(report)
            if report["resume_snapshot"]["status"] == "blocked":
                print(f"Resume is blocked: {report['resume_snapshot']['error']}")
        return 0 if report["technical_checks_passed"] else 1
    saved = read_project(root) if args.command == "resume" else None
    controlled = bool(saved and saved.get("autonomous_contract")) or bool(args.command == "new" and args.autonomous and args.host == "codex")
    if not args.prepare_only and not _has_terminal() and not controlled:
        raise ValueError("The native agent needs an interactive terminal. " + ("Add --prepare-only to prepare the book without a model call, then run resume from a terminal." if args.command == "new" else "Run resume from your terminal, or add --prepare-only to only verify the project."))
    author_name = _author_name(args.author)
    if args.command == "new":
        host = _choose_host(args.host)
        idea = args.idea_file.read_text(encoding="utf-8-sig") if args.idea_file else args.idea
        if idea is None:
            if not sys.stdin.isatty():
                raise ValueError("Pass --idea or --idea-file, or start from an interactive terminal")
            idea = input("What is your book idea? ").strip()
        if author_name is None and not args.prepare_only:
            if not _has_terminal():
                raise ValueError("Pass --author for unattended execution; no publishing name is inferred")
            # This visible Enter choice is an explicit author credit, never an
            # account-derived identity or a placeholder deferred until export.
            author_name = _author_name(input("Name on the title page [Anonymous]: ").strip() or "Anonymous")
        contract = None
        if args.autonomous and host == "codex":
            if not args.model or not args.effort:
                raise ValueError("Pass --model and --effort for the controlled unattended run; no model is silently substituted")
            if not 1 <= args.chapters <= 100 or args.min_words < 100 * args.chapters or args.max_words < args.min_words or not 0 <= args.quality_target <= 9.2:
                raise ValueError("Invalid unattended chapter, length or quality contract")
            contract = {"chapters": args.chapters, "min_words": args.min_words, "max_words": args.max_words, "quality_target": args.quality_target}
        config = prepare_project(root, host=host, idea=idea, language=args.language, model=args.model, effort=args.effort, autonomous=args.autonomous, author_name=author_name, autonomous_contract=contract)
    else:
        config = saved
        host = str(config["host"])
        if args.host is not None and args.host != host:
            raise ValueError(f"This book was prepared and verified for {HOST_NAMES[host]}. Resume it with --host {host}, or prepare a new project for {HOST_NAMES[args.host]}.")
        find_native(host)
    model = args.model if args.model is not None else config["model"]
    effort = args.effort if args.effort is not None else config["effort"]
    _profile(host, model, effort)
    print(f"Book Genesis | {HOST_NAMES[host]} | model: {model or 'native configured default'} | effort: {effort or 'native configured default'}")
    if author_name is not None or config.get("author_name") is not None:
        print(f"Title-page author: {author_name or config['author_name']}")
    print(" -> ".join(phase.label for phase in load_manifest()))
    if args.prepare_only:
        command = _resume_command(root, model=model, effort=effort, author_name=author_name)
        print(f"Prepared and verified: {root}\nNo model was called. When ready, run in {'PowerShell' if os.name == 'nt' else 'a terminal'}: {command}")
        return 0
    if config.get("autonomous_contract"):
        from launcher.autonomous import launch_controlled
        return launch_controlled(root.resolve(), config, model=model, effort=effort, author_name=author_name)
    return launch_project(root, config, host=host, model=model, effort=effort, resumed=args.command == "resume", author_name=author_name)


def _launcher_state(root: Path) -> dict[str, object]:
    """Report launcher records only; book progress comes from the core checks."""
    lock = _install_path(root / LOCK)
    lock_record = lock.read_text(encoding="utf-8").strip() if lock.is_file() else None
    receipts = []
    errors = []
    for path in _install_path(root / ".book-genesis/launches").glob("*.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(record, dict):
                raise ValueError("receipt is not an object")
            receipts.append(record)
        except (OSError, ValueError):
            errors.append(f"Unreadable launch receipt: {path.name}")
    last = max(receipts, key=lambda item: str(item.get("started_at", ""))) if receipts else None
    return {"lock_record": lock_record, "launch_count": len(receipts), "last": last, "errors": errors}


def _print_launcher_state(state: dict[str, object]) -> None:
    if state["lock_record"] is not None:
        print(f"Launcher lock present: {state['lock_record']}")
        print("  Another launcher may own this book. Remove the lock only after both recorded PIDs have stopped.")
    for error in state["errors"]:
        print(error)
    last = state["last"]
    if last:
        print(f"Launches: {state['launch_count']} | last: {last.get('status')} | native exit: {last.get('native_exit_code')} | book completion: {last.get('book_completion')}")
    else:
        print("Launches: none yet")


def main(argv: list[str] | None = None) -> int:
    try:
        return _run(build_parser().parse_args(argv))
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"Book Genesis: {exc}", file=sys.stderr)
        return 2
    except (KeyboardInterrupt, EOFError):
        print("\nSession interrupted. Keep saved files and resume from this project.", file=sys.stderr)
        return 130
