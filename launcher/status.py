"""Readable, read-only status built from this checkout's core verifiers."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any
from launcher.activity import collect_activity


def _check(argv: list[str], kind: str) -> dict[str, Any]:
    try:
        result = subprocess.run(argv, shell=False, check=False, capture_output=True,
                                text=True, encoding="utf-8", timeout=60)
    except (OSError, UnicodeError, subprocess.SubprocessError) as exc:
        return {"returncode": None, "report": None, "error": f"{kind} check could not finish: {exc}"}
    try:
        report = json.loads(result.stdout)
        if not isinstance(report, dict) or report.get("schema_version") != 1:
            raise ValueError("unsupported report schema")
        if kind == "progress":
            if not isinstance(report.get("ok"), bool) or not isinstance(report.get("canonical"), dict):
                raise ValueError("missing progress result")
            if report["ok"] and not isinstance(report.get("state"), dict):
                raise ValueError("missing saved state")
            passed = report["ok"]
        else:
            if any(not isinstance(report.get(key), dict) or not isinstance(report[key].get("status"), str)
                   for key in ("delivery", "reviews")):
                raise ValueError("missing delivery or reader result")
            passed = report["delivery"]["status"] == "delivered" and report["reviews"]["status"] == "current"
        if result.returncode == 0 and not passed:
            raise ValueError("successful exit conflicts with failed report")
    except (TypeError, ValueError) as exc:
        return {"returncode": result.returncode, "report": None,
                "error": f"{kind} returned an invalid report: {exc}",
                "stdout": result.stdout, "stderr": result.stderr}
    return {"returncode": result.returncode, "report": report,
            "error": None, "stderr": result.stderr}


def collect_status(root: Path, scripts: Path) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": 1, "book_dir": str(root),
        "technical_checks_passed": False,
        "literary_quality": "not_assessed_by_this_tool",
        "publication_approval": "not_assessed",
        "activity": collect_activity(root),
    }
    if not (root / "PROJECT_STATE.yaml").is_file():
        report.update(status="prepared", checks={}, reported_quality_gates="not_verified", status_exit_code=1)
        return report
    prefix = [sys.executable, "-X", "utf8"]
    verification = prefix + [str(scripts / "verify_book.py"), "--book-dir", str(root)]
    for name in ("final-reader-index.json", "review-index.json"):
        index = root / "evaluations" / name
        if index.is_file():
            verification.extend(["--review-index", str(index)])
            break
    checks = {
        "progress": _check(prefix + [str(scripts / "check_progress.py"), "--book-dir", str(root)], "progress"),
        "verification": _check(verification, "verification"),
    }
    report["checks"] = checks
    passed = all(c["error"] is None and c["returncode"] == 0 for c in checks.values())
    progress = checks["progress"]["report"] or {}
    state = progress.get("state", {})
    gates = state.get("gates", {}) if isinstance(state, dict) else {}
    gates = gates if isinstance(gates, dict) else {}
    audit, revision = gates.get("adversarial_audit"), gates.get("revision_loop")
    failures = {"revise", "major_rewrite", "not_passed", "gates_not_met", "failed", "blocked", "stopped"}
    quality = ("needs_revision" if audit in failures or revision in failures else
               "reported_pass" if audit in {"pass", "passed"} and revision in {"pass", "passed"} else "not_verified")
    verification_report = checks["verification"]["report"] or {}
    # An unfinished book naturally has no final export/index. Do not claim it is
    # delivered, or confuse expected pending work with a failed verification.
    pending = (progress.get("ok") is True and checks["progress"]["error"] is None
               and checks["progress"]["returncode"] == 0
               and state.get("pipeline_status") in {"in_progress", "running"}
               and checks["verification"]["error"] is None
               and checks["verification"]["returncode"] == 1
               and verification_report.get("delivery", {}).get("status") == "pending"
               and verification_report.get("reviews", {}).get("status") == "not_run")
    report.update(status="in_progress" if pending else "checked", completion_pending=pending,
                  status_exit_code=0 if passed or pending else 1,
                  technical_checks_passed=passed, reported_quality_gates=quality)
    return report


def print_status(report: dict[str, Any]) -> None:
    activity = report.get('activity', {})
    for row in activity.get('requests', []):
        elapsed = row.get('seconds_since_reserved')
        suffix = f" | {elapsed}s since request reservation" if elapsed is not None else ''
        print(f"Recorded operation: {row['label']} | {row['status']}{suffix}")
        if row.get('detail'):
            print(f"Saved diagnostic: {row['detail']}")
    if activity.get('requests'):
        print('These are saved journal observations; process liveness is not established by this command.')
    if activity.get('diagnostic'):
        print(f"Activity unavailable: {activity['diagnostic']}")
    if report["status"] == "prepared":
        print("Project prepared. No pipeline state has been saved by the native agent yet.")
        print("Next: resume this project to start writing.")
        return
    checks = report["checks"]
    progress = checks["progress"]["report"] or {}
    verification = checks["verification"]["report"] or {}
    state = progress.get("state") or {}
    canonical = progress.get("canonical") or {}
    print(f"Saved phase: {state.get('current_phase', 'unavailable')}")
    print(f"Manuscript: {canonical.get('chapter_count', '?')}/{state.get('chapter_count_planned', '?')} chapters | {canonical.get('word_count', '?')} words")
    delivery = verification.get("delivery", {})
    reviews = verification.get("reviews", {})
    print(f"Exported files: {delivery.get('status', 'not verified')} | Reader evidence: {reviews.get('status', 'not verified')}")
    gates = state.get("gates") or {}
    print(f"Saved quality gates: audit = {gates.get('adversarial_audit', 'unknown')} | revision = {gates.get('revision_loop', 'unknown')}")
    if report["reported_quality_gates"] == "needs_revision":
        print("Editorial work remains. Delivered files do not mean the quality gates passed.")
    elif report["reported_quality_gates"] == "reported_pass":
        print("The saved state reports passed quality gates. This command does not grade the writing.")
    else:
        print("Literary quality has not been verified by this command.")
    for name, check in checks.items():
        if check["error"]:
            print(f"Check error: {check['error']}")
        if check.get("stderr", "").strip():
            print(f"{name} diagnostic: {check['stderr'].strip()}")
        if check["returncode"] not in (None, 0) and not (name == "verification" and report.get("completion_pending")):
            print(f"{name} check exit code: {check['returncode']}")
    for item in progress.get("mismatches", []):
        print(f"Needs attention: {item.get('field', 'progress')}: {item.get('message', 'unknown mismatch')}")
    for section in (delivery, reviews):
        for error in section.get("errors", []):
            if not report.get("completion_pending"):
                print(f"Needs attention: {error}")
        for scope in section.get("scopes", []):
            for issue in scope.get("issues", []):
                print(f"Needs attention ({scope.get('scope', 'reader')}): {issue}")
    if report.get("completion_pending"):
        print("The saved workflow is in progress. Final export and full-book reader verification are still pending.")
        print("Next: follow the writing session. This status check does not establish that its process is still running.")
    elif not report["technical_checks_passed"]:
        print("Next: resolve the reported checks, then run status again. Use --json for full evidence.")
    elif report.get("resume_snapshot", {}).get("status") == "blocked":
        print("Next: keep this saved book and use its matching checkout before resuming.")
    elif report["reported_quality_gates"] == "needs_revision":
        print("Next: read the draft and its remaining findings. A completed bounded run will not restart its revision budget.")
    else:
        print("Next: read the exported manuscript before making a publication decision.")
