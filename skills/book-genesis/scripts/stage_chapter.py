"""Stage extracted prose; optionally normalize only its initial Markdown heading level.

Never edits the source or a canonical chapter. The only allowed transformation
removes extra leading '#' characters from a nonempty initial H2-H6. Body bytes,
title words, encoding and line endings remain unchanged, with separate hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from export_book import _visible_body, _XML_INVALID_RE


def stage_chapter(source: Path, output_dir: Path) -> dict:
    raw = source.read_bytes()
    bom = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
    content = raw[len(bom):]
    text = content.decode("utf-8")
    if _XML_INVALID_RE.search(text):
        raise ValueError("source contains XML-invalid control characters")
    heading = re.match(rb"(#{1,6}) ([^\r\n]+)(\r\n|\n|\r)", content)
    if not heading or not heading[2].strip():
        raise ValueError("source needs a nonempty initial Markdown H1-H6 followed by prose")
    body = content[heading.end():]
    if any(line.startswith("# ") for line in body.decode("utf-8").splitlines()):
        raise ValueError("source contains another level-1 heading")
    visible = _visible_body(body.decode("utf-8"))
    if not visible:
        raise ValueError("source has no visible prose")
    level = len(heading[1])
    staged = bom + content[level - 1:]
    # This assertion guards the transformation, including CRLF and BOM cases.
    staged_body = staged[len(bom) + heading.end() - (level - 1):]
    if staged_body != body:
        raise ValueError("heading normalization changed body bytes")
    digest = lambda data: hashlib.sha256(data).hexdigest()
    receipt = {
        "schema_version": 1, "status": "staged", "scope": "format_only_not_editorial_acceptance",
        "source_sha256": digest(raw), "staged_sha256": digest(staged),
        "body_sha256": digest(body), "body_unchanged": True,
        "transform": "none" if level == 1 else "initial_markdown_heading_to_h1",
        "original_heading_level": level, "heading_level": 1,
        "title": heading[2].decode("utf-8"), "visible_prose_words": len(visible.split()),
        "source_file": "source.md", "staged_file": "chapter.md",
    }
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "source.md").write_bytes(raw)
    (output_dir / "chapter.md").write_bytes(staged)
    if source.read_bytes() != raw:
        raise ValueError("source changed during staging; preserve this failed bundle")
    if (output_dir / "source.md").read_bytes() != raw or (output_dir / "chapter.md").read_bytes() != staged:
        raise ValueError("staged read-back differs; preserve this failed bundle")
    (output_dir / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Already extracted prose, not a raw JSON envelope")
    parser.add_argument("--output-dir", required=True, type=Path, help="New staging bundle; never a canonical chapter directory")
    args = parser.parse_args()
    try:
        receipt = stage_chapter(args.source, args.output_dir)
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}))
        return 1
    print(json.dumps(receipt, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
