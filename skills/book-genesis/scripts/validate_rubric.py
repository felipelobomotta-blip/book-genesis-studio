"""Validate rubric structure and exact source evidence, never literary merit."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

from export_book import _visible_body
from prepare_rubric import build_catalog, canonical_json, catalog_digest
from validate_blind_reader import _normalise_quote, _strip_one_markdown_fence


DIMENSIONS = ("Originality", "Theme", "Characters", "Prose", "Pacing", "Emotion", "Coherence", "Market", "Voice", "Opening")


def rubric_schema(catalog: dict | None = None) -> dict[str, Any]:
    def obj(properties):
        return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}
    string = {"type": "string"}
    evidence = (obj({"passage_id": string, "reason": string}) if catalog is not None else
                obj({"chapter": {"type": "integer", "minimum": 1}, "quote": string, "reason": string}))
    properties = {
        "schema_version": {"type": "integer", "enum": [2 if catalog is not None else 1]},
        "coverage": obj({"scope": {"type": "string", "enum": ["full_manuscript", "sample"]},
                         "chapters": {"type": "array", "items": {"type": "integer", "minimum": 1}}}),
        "dimensions": {"type": "array", "items": obj({
            "name": {"type": "string", "enum": list(DIMENSIONS)},
            "score": {"anyOf": [{"type": "number", "minimum": 0, "maximum": 10}, {"type": "null"}]},
            "evidence": {"type": "array", "items": evidence}, "reason": string,
        })},
        "strongest_passage": evidence, "weakest_passage": evidence,
        "confidence": obj({"level": {"type": "string", "enum": ["low", "medium", "high"]}, "reason": string}),
        "limitations": string,
    }
    if catalog is not None:
        properties["catalog_sha256"] = {"type": "string", "enum": [catalog_digest(catalog)]}
    return obj(properties)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value):
    raise ValueError(f"non-finite JSON number: {value}")


def validate_rubric(chapter_paths: list[Path], report_path: Path, *, expected_chapters: int | None = None,
                    original_receipt: Path | None = None, catalog_path: Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    records = []
    sources = {}
    raw_report = b""
    unassessed = []
    full = False
    catalog = None
    passages = {}
    resolved = []
    version = 1

    def obj(value, fields, label):
        if not isinstance(value, dict) or set(value) != set(fields):
            errors.append(f"{label}: expected exactly {', '.join(fields)}")
            return {}
        return value

    def text(value, label):
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{label}: expected nonempty text")
            return ""
        return value

    def evidence(value, label):
        if version == 2:
            item = obj(value, ("passage_id", "reason"), label)
            reference = text(item.get("passage_id"), label + ".passage_id")
            reason = text(item.get("reason"), label + ".reason")
            passage = passages.get(reference)
            if passage is None:
                errors.append(f"{label}: unknown passage_id in the frozen manuscript")
                return ""
            resolved.append({"location": label, "passage_id": reference, **passage, "reason": reason})
            return _normalise_quote(passage["quote"])
        item = obj(value, ("chapter", "quote", "reason"), label)
        number = item.get("chapter")
        quote = text(item.get("quote"), label + ".quote")
        text(item.get("reason"), label + ".reason")
        if type(number) is not int or number not in sources:
            errors.append(f"{label}: chapter is not in the assigned scope")
        elif quote and _normalise_quote(quote) not in sources[number]:
            errors.append(f"{label}: quote is not an exact contiguous excerpt from chapter {number}")
        return _normalise_quote(quote)

    for path in chapter_paths:
        try:
            match = re.fullmatch(r"chapter-(\d+)\.md", path.name, re.I)
            if not match or int(match[1]) < 1:
                raise ValueError("source must be a canonical chapter-NN.md file")
            number = int(match[1])
            if number in sources:
                raise ValueError(f"duplicate source chapter {number}")
            data = path.read_bytes()
            lines = data.decode("utf-8-sig").splitlines()
            if not lines or not lines[0].startswith("# ") or not lines[0][2:].strip() or any(line.startswith("# ") for line in lines[1:]):
                raise ValueError("source must have one leading H1")
            body = _visible_body("\n".join(lines[1:]))
            if not body:
                raise ValueError("source has no visible prose")
            sources[number] = _normalise_quote(body)
            records.append({"chapter": number, "path": str(path), "sha256": hashlib.sha256(data).hexdigest()})
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"source {path}: {exc}")
    if not sources:
        errors.append("no readable source chapters")
    if catalog_path is not None:
        try:
            catalog = json.loads(catalog_path.read_text(encoding="utf-8-sig"),
                                 object_pairs_hook=_unique_object, parse_constant=_constant)
            current = build_catalog(chapter_paths)
            if canonical_json(catalog) != canonical_json(current):
                raise ValueError("catalog differs from the complete current manuscript; rebuild and obtain a fresh review")
            for chapter in catalog["chapters"]:
                for passage in chapter["passages"]:
                    passages[passage["id"]] = {"chapter": chapter["chapter"], "quote": passage["text"]}
        except (OSError, UnicodeError, ValueError, TypeError) as exc:
            catalog = None
            errors.append(f"evidence catalog: {exc}")
    try:
        raw_report = report_path.read_bytes()
        report = json.loads(_strip_one_markdown_fence(raw_report.decode("utf-8-sig")),
                            object_pairs_hook=_unique_object, parse_constant=_constant)
    except (OSError, UnicodeError, ValueError) as exc:
        errors.append(f"report: {exc}")
        report = None
    if report is None:
        errors.append("report must be a JSON object")
    else:
        version = report.get("schema_version") if isinstance(report, dict) else None
        fields = rubric_schema()["required"] + (["catalog_sha256"] if version == 2 else [])
        report = obj(report, fields, "report")
        if type(version) is not int or version not in (1, 2):
            errors.append("unsupported report schema")
        if version == 2:
            if catalog is None:
                errors.append("schema 2 requires a valid frozen --catalog")
            elif report.get("catalog_sha256") != catalog_digest(catalog):
                errors.append("report is bound to a different evidence catalog")
        elif catalog_path is not None:
            errors.append("a catalog requires a schema 2 passage-reference report")
        coverage = obj(report.get("coverage"), ("scope", "chapters"), "coverage")
        supplied = coverage.get("chapters")
        if not isinstance(supplied, list) or any(type(n) is not int for n in supplied) or sorted(supplied) != sorted(sources):
            errors.append("coverage must name every assigned chapter exactly once")
        scope = coverage.get("scope")
        if not isinstance(scope, str) or scope not in {"full_manuscript", "sample"}:
            errors.append("unknown coverage scope")
        if scope == "full_manuscript":
            full = (type(expected_chapters) is int and expected_chapters > 0
                    and sorted(sources) == list(range(1, expected_chapters + 1)))
            if not full:
                errors.append("full coverage requires the approved --expected-chapters count and its complete chapter set")
        rows = report.get("dimensions")
        if not isinstance(rows, list):
            errors.append("dimensions must be a list")
            rows = []
        names = []
        for i, value in enumerate(rows):
            row = obj(value, ("name", "score", "evidence", "reason"), f"dimensions[{i}]")
            names.append(row.get("name"))
            text(row.get("reason"), f"dimensions[{i}].reason")
            score = row.get("score")
            if score is None:
                unassessed.append(row.get("name"))
            elif type(score) not in (int, float) or not 0 <= score <= 10 or not math.isfinite(score):
                errors.append(f"dimensions[{i}]: score must be null or a finite number from 0 to 10")
                score = None
            entries = row.get("evidence")
            if not isinstance(entries, list):
                errors.append(f"dimensions[{i}].evidence must be a list")
                entries = []
            quotations = [evidence(v, f"dimensions[{i}].evidence[{j}]") for j, v in enumerate(entries)]
            if score is not None and len(set(q for q in quotations if q)) < (2 if score > 9 else 1):
                errors.append(f"dimensions[{i}]: insufficient distinct source excerpts for an assessed score")
        if len(names) != len(DIMENSIONS) or any(names.count(n) != 1 for n in DIMENSIONS):
            errors.append("each of the ten rubric dimensions must occur exactly once")
        for field in ("strongest_passage", "weakest_passage"):
            evidence(report.get(field), field)
        confidence = obj(report.get("confidence"), ("level", "reason"), "confidence")
        if not isinstance(confidence.get("level"), str) or confidence.get("level") not in {"low", "medium", "high"}:
            errors.append("unknown confidence level")
        text(confidence.get("reason"), "confidence.reason")
        text(report.get("limitations"), "limitations")
    for record in records:
        try:
            if hashlib.sha256(Path(record["path"]).read_bytes()).hexdigest() != record["sha256"]:
                errors.append(f"chapter {record['chapter']} changed during validation")
        except OSError as exc:
            errors.append(f"source changed or became unreadable: {exc}")
    report_hash = hashlib.sha256(raw_report).hexdigest()
    if original_receipt is not None:
        try:
            original = json.loads(original_receipt.read_text(encoding="utf-8-sig"), object_pairs_hook=_unique_object)
            if not isinstance(original, dict) or original.get("schema_version") != 1 or original.get("status") != "passed" or original.get("complete") is not True:
                raise ValueError("original validation was not complete and passed")
            if original.get("report_sha256") != report_hash:
                raise ValueError("raw report differs from its original validation")
            if original.get("catalog_sha256") != (catalog_digest(catalog) if catalog is not None else None):
                raise ValueError("evidence catalog differs from the original validation")
            if catalog is not None and original.get("resolved_evidence") != resolved:
                raise ValueError("resolved passage evidence differs from the original validation")
            old = original.get("source_chapters")
            if not isinstance(old, list) or sorted((r["chapter"], r["sha256"]) for r in old) != sorted((r["chapter"], r["sha256"]) for r in records):
                raise ValueError("source chapters differ from the original validation")
        except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"original receipt: {exc}")
    complete = not errors and full and not unassessed
    return {"schema_version": 1, "status": "invalid" if errors else "passed" if complete else "incomplete",
            "valid": not errors, "complete": complete, "source_chapters": records,
            "report_sha256": report_hash, "unassessed": unassessed,
            "catalog_sha256": catalog_digest(catalog) if catalog is not None else None,
            "resolved_evidence": resolved,
            "errors": errors, "literary_quality": "not_assessed_by_this_tool"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapter", action="append", default=[])
    parser.add_argument("--report", type=Path)
    parser.add_argument("--expected-chapters", type=int)
    parser.add_argument("--original-receipt", type=Path, help="Reject changed report or prose when reusing an earlier passed validation")
    parser.add_argument("--catalog", type=Path, help="Frozen manuscript from prepare_rubric.py, for schema 2 passage references")
    parser.add_argument("--schema", action="store_true", help="Print the critic's structured-output schema; no file access")
    args = parser.parse_args()
    if args.schema:
        try:
            catalog = (json.loads(args.catalog.read_text(encoding="utf-8-sig"), object_pairs_hook=_unique_object,
                                  parse_constant=_constant) if args.catalog is not None else None)
            print(json.dumps(rubric_schema(catalog), indent=2))
        except (OSError, UnicodeError, ValueError, TypeError) as exc:
            parser.error(f"cannot read evidence catalog: {exc}")
        return 0
    if not args.chapter or args.report is None:
        parser.error("--chapter and --report are required unless --schema is used")
    result = validate_rubric([Path(p) for p in args.chapter], args.report, expected_chapters=args.expected_chapters,
                             original_receipt=args.original_receipt, catalog_path=args.catalog)
    # Receipts are often piped through a Windows shell before being saved.
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
