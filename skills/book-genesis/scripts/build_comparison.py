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

from validate_blind_reader import CONFIDENCE, FLAGS, TURN_PAGES


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


def reader_schema(reader: str) -> dict[str, Any]:
    def obj(properties: dict[str, Any]) -> dict[str, Any]:
        return {"type": "object", "properties": properties,
                "required": list(properties), "additionalProperties": False}

    string = {"type": "string"}
    quote = obj({"quote": string})
    reason = obj({"quote": string, "reason": string})
    return obj({
        "reader": {"type": "string", "enum": [reader]},
        "turn_page": {"type": "string", "enum": sorted(TURN_PAGES)},
        "stopped_at": {"anyOf": [quote, {"type": "null"}]},
        "why_stopped": {"anyOf": [obj({"reason": string}), {"type": "null"}]},
        "remember_tomorrow": {"type": "array", "items": reason},
        "confused_by": {"type": "array", "items": reason},
        "flags": {"type": "array", "items": obj({
            "flag": {"type": "string", "enum": sorted(FLAGS)}, "quote": string})},
        "strongest_passage": reason, "weakest_passage": reason,
        "machine_tells": {"type": "array", "items": obj({"tell": string, "quote": string})},
        "felt": obj({"emotion": string, "reason": string}),
        "confidence": {"type": "string", "enum": sorted(CONFIDENCE)},
        "compare": {"type": "string", "enum": ["A", "B", "same"]},
    })


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
    prose_context = "".join(f"\n\n## Prose context {i}\n\n{body}"
                            for i, (_, body) in enumerate(context_data, 1))
    for persona, (reader, lens) in READERS.items():
        mapping = {"A": "candidate", "B": "accepted"} if persona in candidate_first else {"A": "accepted", "B": "candidate"}
        bodies = {"accepted": accepted_body, "candidate": candidate_body}
        packet = (
            f"# Chapter comparison\n\nYou are {reader}, {lens}. Your JSON reader field must be exactly {json.dumps(reader)}.\n"
            "Compare two anonymous prose versions, A and B. Their order carries no information about when they were written. "
            "Use only the supplied prose and reader role. Do not look for project files or earlier evaluations. "
            "Choose A, B or same from your real reading experience; an unfavorable vote is valid. Do not score the text.\n\n"
            "When you did not stop, stopped_at and why_stopped must both be null. Otherwise stopped_at contains only quote, "
            "and why_stopped contains only reason. Passage and memory objects contain only quote and reason, with no chapter key. "
            "Copy short exact contiguous quotes. Do not alter a quote to improve grammar.\n\n"
            + role + prose_context + "\n\n## Draft A\n\n" + bodies[mapping["A"]]
            + "\n\n## Draft B\n\n" + bodies[mapping["B"]] + "\n"
        ).encode("utf-8")
        packet_name, schema_name = f"{persona}.packet.md", f"{persona}.schema.json"
        (output_dir / packet_name).write_bytes(packet)
        schema_data = (json.dumps(reader_schema(reader), indent=2) + "\n").encode("utf-8")
        (output_dir / schema_name).write_bytes(schema_data)
        rows.append({"persona": persona, "reader": reader, "packet": packet_name,
                     "packet_sha256": digest(packet), "response_schema": schema_name,
                     "response_schema_sha256": digest(schema_data), "mapping": mapping})
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
