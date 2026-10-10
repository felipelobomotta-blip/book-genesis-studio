"""Freeze the complete visible manuscript as numbered evidence passages for a critic."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from export_book import _visible_body


def canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def catalog_digest(catalog: dict) -> str:
    return hashlib.sha256(canonical_json(catalog).encode("utf-8")).hexdigest()


def build_catalog(chapter_paths: list[Path]) -> dict:
    """No selection or summary: every visible body paragraph is included, in order."""
    chapters = {}
    for path in chapter_paths:
        match = re.fullmatch(r"chapter-(\d+)\.md", path.name, re.I)
        if not match or int(match[1]) < 1:
            raise ValueError(f"source must be a canonical chapter-NN.md file: {path}")
        number = int(match[1])
        if number in chapters:
            raise ValueError(f"duplicate source chapter {number}")
        raw = path.read_bytes()
        lines = raw.decode("utf-8-sig").splitlines()
        if not lines or not lines[0].startswith("# ") or not lines[0][2:].strip() or any(line.startswith("# ") for line in lines[1:]):
            raise ValueError(f"chapter {number} must have one leading H1")
        body = _visible_body("\n".join(lines[1:]))
        if not body:
            raise ValueError(f"chapter {number} has no visible prose")
        paragraphs = re.split(r"\n[ \t]*\n", body)
        passages = [{"id": f"c{number:02d}p{i:04d}", "text": text}
                    for i, text in enumerate((p for p in paragraphs if p.strip()), 1)]
        chapters[number] = {"chapter": number, "sha256": hashlib.sha256(raw).hexdigest(),
                            "title": lines[0][2:].strip(), "passages": passages}
    if not chapters:
        raise ValueError("no source chapters")
    # Refuse a snapshot assembled while its source files were changing.
    for path in chapter_paths:
        number = int(re.fullmatch(r"chapter-(\d+)\.md", path.name, re.I)[1])
        if hashlib.sha256(path.read_bytes()).hexdigest() != chapters[number]["sha256"]:
            raise ValueError(f"chapter {number} changed while preparing evidence")
    return {"schema_version": 1, "chapters": [chapters[n] for n in sorted(chapters)]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapter", action="append", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="A new JSON file; existing catalogs are never overwritten")
    args = parser.parse_args()
    try:
        catalog = build_catalog(args.chapter)
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": "prepared", "catalog": str(args.output),
                      "catalog_sha256": catalog_digest(catalog),
                      "chapters": [c["chapter"] for c in catalog["chapters"]]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
