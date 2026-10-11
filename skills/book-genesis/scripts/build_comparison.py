"""Build four frozen comparison packets without exposing revision identity.

No model call, prose edit or grade is performed here. The private manifest
must stay with the orchestrator; only an individual packet and its response
schema go to a reader. Schema validation never replaces exact-quote checks.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import secrets
from typing import Any

from validate_blind_reader import CONFIDENCE, FLAGS, TURN_PAGES, MAX_EMOTION_LENGTH
from prepare_rubric import catalog_digest
from evidence_passages import evidence_passages


READERS = {
    "primary": ("Lena", "a primary reader looking for an engaging book for its intended audience"),
    "hostile": ("Mark", "a skeptical reader who notices shortcuts and weak causality"),
    "adjacent": ("Priya", "an interested reader outside the story's core audience"),
    "casual": ("Airport reader", "an impatient reader deciding whether to keep reading"),
}


class ComparisonPacketError(ValueError):
    """A comparison cannot be frozen safely."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reader_schema(reader: str, *, catalog: dict | None = None) -> dict[str, Any]:
    def obj(properties: dict[str, Any]) -> dict[str, Any]:
        return {"type": "object", "properties": properties,
                "required": list(properties), "additionalProperties": False}

    string = {"type": "string"}
    key = "passage_id" if catalog is not None else "quote"
    comparison = catalog is not None and catalog.get("kind") == "anonymous_comparison"
    groups = (catalog["sources"] if comparison else catalog["chapters"]) if catalog is not None else []
    citation = ({"type": "string", "enum": [p["id"] for c in groups for p in c["passages"]]}
                if catalog is not None else string)
    citation_definition = citation
    if catalog is not None:
        # Long chapters and comparisons send the ID enum once, not per field.
        citation = {"$ref": "#/$defs/passageId"}
    quote = obj({key: citation})
    reason = obj({key: citation, "reason": string})
    properties = {
        "reader": {"type": "string", "enum": [reader]},
        "turn_page": {"type": "string", "enum": sorted(TURN_PAGES)},
        "stopped_at": {"anyOf": [quote, {"type": "null"}]},
        "why_stopped": {"anyOf": [obj({"reason": string}), {"type": "null"}]},
        "remember_tomorrow": {"type": "array", "items": reason},
        "confused_by": {"type": "array", "items": reason},
        "flags": {"type": "array", "items": obj({
            "flag": {"type": "string", "enum": sorted(FLAGS)}, key: citation})},
        "strongest_passage": reason, "weakest_passage": reason,
        "machine_tells": {"type": "array", "items": obj({"tell": string, key: citation})},
        "felt": obj({"emotion": {"type": "string", "minLength": 1, "maxLength": MAX_EMOTION_LENGTH,
            "description": f"A short emotion label such as tension and relief, at most {MAX_EMOTION_LENGTH} characters. Put explanations in felt.reason; do not copy story prose here."},
            "reason": string}),
        "confidence": {"type": "string", "enum": sorted(CONFIDENCE)},
    }
    if catalog is None or comparison:
        properties["compare"] = {"type": "string", "enum": ["A", "B", "same"]}
    if catalog is not None:
        properties.update(schema_version={"type": "integer", "enum": [3 if comparison else 2]},
                          catalog_sha256={"type": "string", "enum": [catalog_digest(catalog)]})
    schema = obj(properties)
    if catalog is not None:
        schema["$defs"] = {"passageId": citation_definition}
    return schema


def _source(path: Path) -> tuple[dict[str, Any], str]:
    path = path.resolve()
    if path.suffix.lower() != ".md" or not path.is_file():
        raise ComparisonPacketError("Comparison inputs must be Markdown chapter files")
    data = path.read_bytes()
    text = data.decode("utf-8-sig")
    if text.count("<!--") != text.count("-->"):
        raise ComparisonPacketError("Unbalanced manuscript comment")
    visible = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    lines = visible.splitlines()
    if not lines or not lines[0].startswith("# ") or not lines[0][2:].strip():
        raise ComparisonPacketError("A chapter must start with one nonempty H1")
    if any(re.match(r"^#\s+", line) for line in lines[1:]):
        raise ComparisonPacketError("A comparison input must contain exactly one H1")
    # Input headings can contain 'accepted', 'revision' or a filename. These
    # are excluded from this prose comparison, never changed in the source.
    body = "\n".join(lines[1:]).strip()
    if not body:
        raise ComparisonPacketError("A comparison needs visible chapter prose")
    return {"path": str(path), "sha256": digest(data), "bytes": len(data),
            "reader_body_sha256": digest(body.encode("utf-8")), "h1_omitted": True}, body


def comparison_catalog(entries: list[tuple[str, dict, str]]) -> dict:
    """Complete anonymous prose only: no filenames, titles or revision identity."""
    sources = []
    for label, record, body in entries:
        paragraphs = evidence_passages(body)
        sources.append({"label": label, "sha256": record["sha256"],
                        "passages": [{"id": f"{label}:p{i:04d}", "text": paragraph}
                                     for i, paragraph in enumerate(paragraphs, 1)]})
    return {"schema_version": 3, "kind": "anonymous_comparison", "sources": sources}


def verify_comparison_catalog(catalog: dict, chapter_paths: list[Path]) -> dict:
    """Rebuild every assigned paragraph, including shared context, before reuse."""
    from prepare_rubric import canonical_json
    if not isinstance(catalog, dict) or catalog.get("schema_version") != 3 or catalog.get("kind") != "anonymous_comparison":
        raise ValueError("not an anonymous comparison catalog")
    rows = catalog.get("sources")
    if not isinstance(rows, list) or len(rows) < 2 or not all(isinstance(row, dict) for row in rows):
        raise ValueError("comparison catalog needs both complete versions")
    labels = [row.get("label") for row in rows]
    if labels != ["A", "B"] + [f"context-{i}" for i in range(1, len(rows) - 1)]:
        raise ValueError("invalid comparison source labels")
    sources = [_source(path) for path in chapter_paths]
    if sorted(row.get("sha256", "") for row in rows) != sorted(record["sha256"] for record, _ in sources):
        raise ValueError("comparison catalog differs from the assigned source files")
    by_hash = {record["sha256"]: (record, body) for record, body in sources}
    rebuilt = comparison_catalog([(row["label"], *by_hash[row["sha256"]]) for row in rows])
    if canonical_json(catalog) != canonical_json(rebuilt):
        raise ValueError("comparison catalog differs from the complete assigned prose")
    return rebuilt


def build_comparison(accepted: Path, candidate: Path, output_dir: Path,
                     context: list[Path] | None = None, *, role_path: Path | None = None) -> dict[str, Any]:
    accepted_record, accepted_body = _source(accepted)
    candidate_record, candidate_body = _source(candidate)
    if accepted_record["path"] == candidate_record["path"]:
        raise ComparisonPacketError("The two inputs must be different files")
    context_data = [_source(path) for path in (context or [])]
    source_records = [accepted_record, candidate_record] + [row[0] for row in context_data]
    if len({row["path"] for row in source_records}) != len(source_records):
        raise ComparisonPacketError("Do not repeat an input as context")
    role_path = role_path or Path(__file__).resolve().parents[1] / "references/roles/blind-reader.md"
    role = role_path.read_text(encoding="utf-8")
    output_dir = output_dir.resolve()
    # Exclusive creation preserves every earlier packet, including failed
    # partial builds. Retry into a fresh directory, never overwrite evidence.
    output_dir.mkdir(parents=True, exist_ok=False)
    order = list(READERS)
    secrets.SystemRandom().shuffle(order)
    candidate_first = set(order[:2])
    rows = []
    for persona, (reader, lens) in READERS.items():
        mapping = {"A": "candidate", "B": "accepted"} if persona in candidate_first else {"A": "accepted", "B": "candidate"}
        bodies = {"accepted": accepted_body, "candidate": candidate_body}
        records = {"accepted": accepted_record, "candidate": candidate_record}
        catalog = comparison_catalog(
            [(label, records[mapping[label]], bodies[mapping[label]]) for label in ("A", "B")]
            + [(f"context-{i}", record, body) for i, (record, body) in enumerate(context_data, 1)])
        rendered = {row["label"]: "\n\n".join(f"[{p['id']}]\n{p['text']}" for p in row["passages"])
                    for row in catalog["sources"]}
        prose_context = "".join(f"\n\n## Prose context {i}\n\n{rendered[f'context-{i}']}"
                                for i in range(1, len(context_data) + 1))
        packet = (
            f"# Chapter comparison\n\nYou are {reader}, {lens}. Your JSON reader field must be exactly {json.dumps(reader)}.\n"
            "Compare two anonymous prose versions, A and B. Their order carries no information about when they were written. "
            "Use only the supplied prose and reader role. Do not look for project files or earlier evaluations. "
            "Choose A, B or same from your real reading experience; an unfavorable vote is valid. Do not score the text.\n\n"
            "Use schema_version 3 and the supplied catalog_sha256. Cite the bracketed paragraph IDs in passage_id, "
            "not copied quotations. Use the role's catalog format with version 3 and add compare. "
            "When you did not stop, stopped_at and why_stopped must both be null. Otherwise stopped_at contains only passage_id, "
            "and why_stopped contains only reason. Passage and memory objects contain only passage_id and reason. "
            f"catalog_sha256: {catalog_digest(catalog)}\n\n"
            + role + prose_context + "\n\n## Draft A\n\n" + rendered["A"]
            + "\n\n## Draft B\n\n" + rendered["B"] + "\n"
        ).encode("utf-8")
        packet_name, schema_name = f"{persona}.packet.md", f"{persona}.schema.json"
        (output_dir / packet_name).write_bytes(packet)
        schema_data = (json.dumps(reader_schema(reader, catalog=catalog), indent=2) + "\n").encode("utf-8")
        (output_dir / schema_name).write_bytes(schema_data)
        catalog_name = f"{persona}.catalog.json"
        (output_dir / catalog_name).write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        rows.append({"persona": persona, "reader": reader, "packet": packet_name,
                     "packet_sha256": digest(packet), "response_schema": schema_name,
                     "response_schema_sha256": digest(schema_data), "mapping": mapping,
                     "catalog": catalog_name, "catalog_sha256": catalog_digest(catalog)})
    for row in source_records:
        if digest(Path(row["path"]).read_bytes()) != row["sha256"]:
            raise ComparisonPacketError("An input changed during packet creation; preserve this failed bundle")
    manifest = {"schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
                "accepted": accepted_record, "candidate": candidate_record,
                "context": [row[0] for row in context_data], "readers": rows,
                "private_mapping": True, "order": "randomized, two candidate-A and two candidate-B"}
    (output_dir / "manifest.private.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accepted", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--context-chapter", action="append", type=Path, default=[])
    args = parser.parse_args()
    try:
        manifest = build_comparison(args.accepted, args.candidate, args.output_dir, args.context_chapter)
    except (OSError, UnicodeError, ComparisonPacketError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}))
        return 1
    print(json.dumps({"status": "frozen", "output_dir": str(args.output_dir.resolve()),
                      "readers": len(manifest["readers"]), "private_manifest": "manifest.private.json"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
