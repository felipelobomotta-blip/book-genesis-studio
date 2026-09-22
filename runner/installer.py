"""Install or verify the Book Genesis skills for a native agent host.

Book Genesis has no book-writing command line. The writing happens inside the
author's agent (Claude Code, Codex, OpenCode, Hermes, OpenClaw and others).
This command only copies the skill folders, checks them, and keeps the
generated Claude Code subagents in sync with their role files.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runner.agents import generate_agents
from runner.distribution import install_suite, supported_targets, validate_suite, verify_install


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="book-genesis-installer",
        description="Install or verify the Book Genesis skills. Never runs a model or writes a book.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    install = subparsers.add_parser("install", help="Copy the skills into an agent's skills folder")
    install.add_argument("target", choices=supported_targets(), help="The agent to install for")
    install.add_argument("--dest", default=None, help="Install into this skills folder instead of the agent default")
    install.add_argument(
        "--agents-dest",
        default=None,
        help="Claude Code only: install the subagents into this folder (needed with --dest)",
    )
    install.add_argument("--force", action="store_true", help="Back up and replace files you changed")
    install.add_argument("--dry-run", action="store_true", help="Show what would change and write nothing")

    subparsers.add_parser("verify-suite", help="Check this checkout's skills before installing")

    verify = subparsers.add_parser("verify-install", help="Check an installed copy against this checkout")
    verify.add_argument("target", choices=supported_targets(), help="The agent that was installed for")
    verify.add_argument("--dest", default=None, help="The skills folder used with install --dest")

    subparsers.add_parser("targets", help="List the agents this installer supports")
    subparsers.add_parser("generate-agents", help="Rebuild agents/ from the core skill's role files")
    return parser


def main(argv: list[str] | None = None) -> int:
    command = "installer"
    try:
        args = build_parser().parse_args(argv)
        command = args.command
        return _run(args)
    except (OSError, ValueError, KeyError) as exc:
        print(f"{command} failed: {exc}", file=sys.stderr)
        return 1


def _fail(title: str, lines: list[str]) -> int:
    print(title, file=sys.stderr)
    for line in lines:
        print(f"  {line}", file=sys.stderr)
    return 1


def _run(args: argparse.Namespace) -> int:
    if args.command == "targets":
        for target in supported_targets():
            print(target)
        return 0

    if args.command == "generate-agents":
        for path in generate_agents():
            print(f"generated: {path.relative_to(path.parents[1]).as_posix()}")
        return 0

    if args.command == "verify-suite":
        result = validate_suite()
        if not result["ok"]:
            return _fail("Suite check failed", list(result["errors"]))
        print("Suite check ok")
        return 0

    if args.command == "verify-install":
        result = verify_install(args.target, destination=args.dest)
        print(f"Checking installed skills: {result['destination']}")
        if not result["ok"]:
            return _fail("Installed files differ", list(result["errors"]))
        print("Installed files verified. Confirm the skill appears in your agent; no model was run.")
        return 0

    result = install_suite(
        args.target,
        destination=args.dest,
        agents_destination=args.agents_dest,
        force=args.force,
        dry_run=args.dry_run,
    )
    done = result["ok"] and not result["dry_run"]
    for item in result["actions"]:
        print(f"{item['action']}: {item['skill']}")
    for item in result["agent_actions"]:
        print(f"{item['action']}: agents/{item['agent']}")
    for item in result["retirements"]:
        if done:
            print(f"retired: {item['name']} (earlier Book Genesis version, moved to backup)")
        else:
            print(f"would retire: {item['name']} (earlier Book Genesis version)")
    for warning in result["warnings"]:
        print(f"warning: {warning}")
    for note in result["notes"]:
        print(f"note: {note}")
    if not result["ok"]:
        return _fail("Installation failed", list(result["errors"]))
    print(f"{'Installed' if done else 'Dry run'} for {args.target}: {result['destination']}")
    if result["agents_root"]:
        print(f"Claude Code subagents: {result['agents_root']}")
    for backup in result["backups"]:
        print(f"Backup: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
