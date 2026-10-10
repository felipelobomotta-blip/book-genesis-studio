"""Prepare four current-draft reader packets with complete, frozen passage evidence.

This makes no model call and selects no favorable excerpts. Only an individual
packet and schema go to a reader. Keep the manifest with the orchestrator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build_comparison import READERS, _source, reader_schema
from prepare_rubric import build_catalog, catalog_digest


def prepare_readers(chapter_paths: list[Path], output_dir: Path, *, audience: str,
                    language: str = "en", context_chapter: Path | None = None) -> dict:
    if not audience.strip() or "\n" in audience or "\r" in audience:
        raise ValueError("audience must be one line naming the genre and intended reader")
    if language not in {"en", "pt-br"}:
        raise ValueError("machine-tell language must be en or pt-br")
    catalog = build_catalog(chapter_paths)
    root = Path(__file__).resolve().parents[1]
    role = (root / "references/roles/blind-reader.md").read_text(encoding="utf-8")
    tells = (root / f"references/patterns/ai-tells-{language}.md").read_text(encoding="utf-8")
    context_record = None
    context = ""
    if context_chapter is not None:
        context_record, body = _source(context_chapter)
        if context_chapter.resolve() in [p.resolve() for p in chapter_paths]:
            raise ValueError("a chapter under test cannot also be previous-chapter context")
        context = "\n\n## Previous chapter context (not under review)\n\n" + " ".join(body.split()[-300:])
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = []
    for persona, (reader, lens) in READERS.items():
        packet = (
            f"# Current-draft reading\n\nYou are {reader}, {lens}.\nAudience: {audience.strip()}\n\n"
            "Read the complete supplied prose once and report your actual reading experience. "
            "Use only this packet. Do not inspect project files, use tools, or score the book. "
            "A negative verdict is valid. Follow response schema version 2: use passage_id instead of quote "
            "in every evidence object. Cite only IDs from the frozen catalog. Do not copy prose into evidence fields. "
            "The validator resolves IDs to the unchanged paragraph in a separate receipt. "
            "stopped_at identifies the paragraph where attention first dropped; explain the precise issue in why_stopped. "
            "Return one JSON object, no compare field, no extra text.\n\n"
            + role + "\n\n## Machine-prose tells\n\n" + tells + context
            + "\n\n## Complete prose under review, in reading order\n\n"
            + json.dumps(catalog, ensure_ascii=False, indent=2)
            + f"\n\nReport schema_version: 2. catalog_sha256: {catalog_digest(catalog)}. "
            + f"Your reader field must be exactly {json.dumps(reader)}.\n"
        ).encode("utf-8")
        schema = (json.dumps(reader_schema(reader, catalog=catalog), indent=2) + "\n").encode("utf-8")
        packet_name, schema_name = f"{persona}.packet.md", f"{persona}.schema.json"
        (output_dir / packet_name).write_bytes(packet)
        (output_dir / schema_name).write_bytes(schema)
        rows.append({"persona": persona, "reader": reader, "packet": packet_name,
                     "packet_sha256": hashlib.sha256(packet).hexdigest(), "response_schema": schema_name,
                     "response_schema_sha256": hashlib.sha256(schema).hexdigest()})
    if build_catalog(chapter_paths) != catalog:
        raise ValueError("assigned prose changed during preparation; preserve this failed bundle")
    if context_record and hashlib.sha256(context_chapter.read_bytes()).hexdigest() != context_record["sha256"]:
        raise ValueError("previous chapter context changed during preparation")
    manifest = {"schema_version": 1, "catalog": "catalog.json", "catalog_sha256": catalog_digest(catalog),
                "chapters": [{"path": str(p.resolve()), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                             for p in chapter_paths], "context": context_record, "readers": rows}
    (output_dir / "manifest.private.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapter", action="append", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--audience", required=True)
    parser.add_argument("--language", choices=("en", "pt-br"), default="en")
    parser.add_argument("--context-chapter", type=Path)
    args = parser.parse_args()
    try:
        result = prepare_readers(args.chapter, args.output_dir, audience=args.audience,
                                 language=args.language, context_chapter=args.context_chapter)
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}))
        return 1
    print(json.dumps({"status": "prepared", "catalog_sha256": result["catalog_sha256"],
                      "output_dir": str(args.output_dir.resolve()), "readers": result["readers"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
