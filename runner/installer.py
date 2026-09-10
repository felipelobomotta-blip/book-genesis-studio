"""Maintainer-only package installer and integrity verifier.

Book Genesis 5.0 intentionally does not ship an interactive book-generation
CLI. Creative work happens in the user's native agent. This command is limited
to copying the portable skill bundle and checking its files.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runner.distribution import install_suite, supported_targets, validate_suite, verify_install


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="book-genesis-installer",
        description="Install or verify Book Genesis 5.0 skills; never runs a model.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="Install portable skills for an agent")
    install_parser.add_argument("target", choices=supported_targets())
    install_parser.add_argument("--dest", default=None, help="Override the runtime skills directory")
    install_parser.add_argument("--include-legacy", action="store_true")
    install_parser.add_argument("--force", action="store_true", help="Back up and replace conflicts")
    install_parser.add_argument("--dry-run", action="store_true")

    subparsers.add_parser("verify-suite", help="Validate skills and pipeline contracts")
    verify_parser = subparsers.add_parser("verify-install", help="Check installed skills and references")
    verify_parser.add_argument("target", choices=supported_targets())
    verify_parser.add_argument("--dest", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "verify-suite":
        result = validate_suite()
        for warning in result["warnings"]:
            print(f"warning: {warning}")
        if not result["ok"]:
            print("Portable suite validation failed")
            for error in result["errors"]:
                print(error)
            return 1
        print("Portable suite validation ok")
        return 0

    if args.command == "verify-install":
        result = verify_install(args.target, destination=args.dest)
        print(f"Checking installed skills: {result['destination']}")
        for error in result["errors"]:
            print(error)
        if result["ok"]:
            print("Installed files verified. Confirm discovery in the native host; no model was tested.")
        return 0 if result["ok"] else 1

    result = install_suite(
        args.target,
        destination=args.dest,
        include_legacy=args.include_legacy,
        force=args.force,
        dry_run=args.dry_run,
    )
    for action in result["actions"]:
        print(f"{action['action']}: {action['skill']}")
    for action in result.get("legacy_actions", []):
        print(f"{action['action']}: {action['component']}/{action['name']}")
    if not result["ok"]:
        print("Installation failed")
        for error in result["errors"]:
            print(error)
        return 1
    mode = "Dry run" if result.get("dry_run") else "Installed"
    print(f"{mode} for {args.target}: {result['destination']}")
    if result.get("backup"):
        print(f"Backup: {result['backup']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
