"""Reproducible mechanical release evidence; human and platform gates stay explicit."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics
import zipfile
import xml.etree.ElementTree as ET

from runner.audit import audit_status
from runner.book import outline_chapters
from runner.filesystem import load_state_summary
from runner.history import load_manifest, sha256


def source_fingerprint(root: Path) -> str:
    files = []
    for folder, pattern in (("runner", "*.py"), ("runner/config", "*.yaml"), ("runner/web", "*"), ("agents", "*.md"), ("skills/book-genesis-codex/references", "*")):
        for path in sorted((root / folder).rglob(pattern)):
            if path.is_file() and "__pycache__" not in path.parts:
                files.append((path.relative_to(root).as_posix(), sha256(path)))
    for name in ("pyproject.toml", "setup.py"):
        if (root / name).is_file():
            files.append((name, sha256(root / name)))
    return hashlib.sha256(json.dumps(sorted(set(files))).encode()).hexdigest()


def performance(project: Path) -> dict:
    path = project / "work/metrics.jsonl"
    records, invalid = [], 0
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
                if not isinstance(record, dict) or not isinstance(record.get("elapsed_seconds"), (int, float)):
                    raise ValueError()
                records.append(record)
            except ValueError:
                invalid += 1
    elapsed = [r["elapsed_seconds"] for r in records]
    streamed = [r["first_text_seconds"] for r in records if isinstance(r.get("first_text_seconds"), (int, float))]
    return {"calls": len(records), "failed_calls": sum(r.get("outcome") == "error" for r in records),
            "provider_seconds_sum": round(sum(elapsed), 3), "median_call_seconds": statistics.median(elapsed) if elapsed else None,
            "median_first_text_seconds": statistics.median(streamed) if streamed else None,
            "max_prompt_chars": max((r.get("prompt_chars", 0) for r in records), default=0),
            "invalid_metric_records": invalid,
            "notice": "Includes retries and resumed sessions. Provider seconds are not end-to-end book time."}


def inspect(project: Path, minimum_words=0) -> dict:
    project = project.resolve()
    checks = []
    def check(name, passed, detail=""):
        checks.append({"check": name, "passed": bool(passed), "detail": detail})
    state = load_state_summary(project)
    paths = sorted((project / "manuscript/chapters").glob("chapter-*.md"))
    try:
        expected = outline_chapters((project / "artifacts/05-outline.md").read_text(encoding="utf-8"))
        actual = [int(p.stem.split("-")[-1]) for p in paths]
        check("chapter_coverage", bool(expected) and actual == expected, str(actual))
    except (OSError, ValueError) as exc:
        check("chapter_coverage", False, str(exc))
    texts = [p.read_text(encoding="utf-8") for p in paths]
    words = sum(len(text.split()) for text in texts)
    check("requested_scale", bool(paths) and words >= minimum_words, f"{words} words; minimum {minimum_words}")
    check("pipeline_complete", state.get("status") == "completed", state.get("status", "missing"))
    check("no_pending_rewrites", not list((project / "work").glob("rewrite-chapter-*.pending")))
    for path, prose in zip(paths, texts):
        accepted = load_manifest(project, int(path.stem.split("-")[-1])).get("accepted") or {}
        check(path.stem + "_accepted_source", accepted.get("sha256") == sha256(path) and accepted.get("status") == "accepted")
        check(path.stem + "_text_integrity", prose.lstrip().startswith("# ") and "\ufffd" not in prose and bool(prose.strip()))
    try:
        check("whole_book_audit", audit_status((project / "artifacts/08-adversarial-audit.md").read_text(encoding="utf-8")) == "pass")
    except (OSError, ValueError) as exc:
        check("whole_book_audit", False, str(exc))
    markdown = sorted((project / "exports").glob("*.md"), key=lambda p: p.stat().st_mtime_ns)
    check("markdown_contains_all_chapters", bool(markdown) and bool(texts) and all(t.strip() in markdown[-1].read_text(encoding="utf-8") for t in texts))
    epubs = sorted((project / "exports").glob("*.epub"), key=lambda p: p.stat().st_mtime_ns)
    try:
        if not epubs:
            raise ValueError("No EPUB export")
        with zipfile.ZipFile(epubs[-1]) as archive:
            if archive.testzip() is not None or archive.read("mimetype") != b"application/epub+zip":
                raise ValueError("Invalid EPUB archive")
            for name in archive.namelist():
                if name.endswith((".xml", ".opf", ".xhtml")):
                    ET.fromstring(archive.read(name))
            package_name = next(name for name in archive.namelist() if name.endswith(".opf"))
            package = ET.fromstring(archive.read(package_name))
            ns = {"o": "http://www.idpf.org/2007/opf"}
            manifest = {item.attrib["id"]: item.attrib["href"] for item in package.findall("o:manifest/o:item", ns)}
            spine = [manifest[item.attrib["idref"]] for item in package.findall("o:spine/o:itemref", ns)]
            chapter_names = [p.stem + ".xhtml" for p in paths]
            check("epub_chapter_order", [name for name in spine if name.startswith("chapter-")] == chapter_names and bool(chapter_names))
            parent = Path(package_name).parent.as_posix()
            check("epub_manifest_targets", all((parent + "/" + name if parent != "." else name) in archive.namelist() for name in manifest.values()))
            check("epub_xml_integrity", True)
        check("epub_not_stale", bool(paths) and epubs[-1].stat().st_mtime_ns >= max(p.stat().st_mtime_ns for p in paths))
    except (OSError, ValueError, KeyError, StopIteration, zipfile.BadZipFile, ET.ParseError) as exc:
        check("epub_integrity", False, str(exc))
    return {"mechanical_acceptance": bool(checks) and all(c["passed"] for c in checks), "project": str(project),
            "source_fingerprint": source_fingerprint(Path(__file__).resolve().parents[1]),
            "chapters": len(paths), "words": words, "checks": checks, "performance": performance(project),
            "release_ready": False, "external_gates": {
                "human_literary_review": "not established by this command",
                "novice_usability": "requires observed novice sessions",
                "platform_matrix": "requires live platform evidence",
                "full_length_repetition": "requires repeated full-length real-provider cases"}}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="book-genesis acceptance")
    parser.add_argument("project", type=Path)
    parser.add_argument("--minimum-words", type=int, default=50000)
    args = parser.parse_args(argv)
    if args.minimum_words < 0:
        parser.error("--minimum-words must be nonnegative")
    result = inspect(args.project, args.minimum_words)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["mechanical_acceptance"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
