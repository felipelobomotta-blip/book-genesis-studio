"""Structured artifact contracts; no provider calls and no editorial gate targets."""
from __future__ import annotations

import re
from pathlib import Path

from export_book import Chapter, count_prose_words
from workflow_state import digest, encoded, freeze, read_json


TEXT = {"type": "string"}
INTEGER = {"type": "integer"}


def obj(fields):
    return {"type": "object", "properties": fields, "required": list(fields), "additionalProperties": False}


def array(items):
    return {"type": "array", "items": items}


def enum(values):
    return {"type": "string", "enum": list(values)}


def validate_shape(value, schema, where="response"):
    """Validate the small schema subset used here; the provider is not trusted."""
    errors = []
    kind = schema.get("type")
    valid_type = {"object": isinstance(value, dict), "array": isinstance(value, list),
                  "string": isinstance(value, str), "integer": type(value) is int,
                  "boolean": type(value) is bool, "number": type(value) in (int, float)}.get(kind, False)
    if not valid_type:
        return [f"{where}: expected {kind}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{where}: invalid enum value")
    if kind == "string" and not value.strip():
        errors.append(f"{where}: empty text")
    if kind == "object":
        if set(value) != set(schema["properties"]):
            errors.append(f"{where}: missing or unexpected fields")
        for key in set(value) & set(schema["properties"]):
            errors += validate_shape(value[key], schema["properties"][key], where + "." + key)
    elif kind == "array":
        for i, item in enumerate(value):
            errors += validate_shape(item, schema["items"], f"{where}[{i}]")
    return errors


def validate_json(path: Path, schema: dict):
    try:
        errors = validate_shape(read_json(path), schema)
    except (OSError, ValueError) as exc:
        errors = [str(exc)]
    return {"valid": not errors, "errors": errors, "response_sha256": digest(path.read_bytes())}


def artifact_schema(paths, *, metadata=False, chapters=False):
    fields = {"files": obj({path: TEXT for path in paths})}
    if metadata:
        fields["book"] = obj({"title": TEXT, "genre": TEXT, "audience": TEXT})
    if chapters:
        fields["chapters"] = array(obj({"number": INTEGER, "title": TEXT, "purpose": TEXT,
            "scene_pressure": TEXT, "events": TEXT, "characters": TEXT, "continuity": TEXT,
            "opening": TEXT, "ending": TEXT}))
    return obj(fields)


PROSE_SCHEMA = obj({"prose": TEXT, "continuity_delta": TEXT})


def validate_prose(path: Path, *, low: int, high: int):
    report = validate_json(path, PROSE_SCHEMA)
    if not report["valid"]:
        return report
    prose = read_json(path)["prose"]
    lines = prose.splitlines()
    if not lines or not re.match(r"^#{1,6} \S", lines[0]):
        report["errors"].append("Prose needs a leading Markdown chapter heading")
    if any(line.startswith("# ") for line in lines[1:]):
        report["errors"].append("Prose contains multiple chapters")
    # Match the existing export counter, rather than a model's length estimate.
    body = "\n".join(lines[1:])
    words = count_prose_words(Chapter(1, path, "chapter", body, digest(prose.encode("utf-8"))))
    if not low <= words <= high:
        report["errors"].append(f"Chapter has {words} prose words; production allowance is {low}..{high}")
    if re.search(r"\[(?:TODO|TBD|insert|scene missing)\b", prose, re.I):
        report["errors"].append("Unfinished prose placeholder")
    report.update(valid=not report["errors"], words=words, extracted_sha256=digest(prose.encode("utf-8")))
    return report


def text_catalog(files: dict[str, str]):
    return {"sources": [{"source": name, "sha256": digest(text.encode("utf-8")),
                         "passages": [{"id": f"s{i:02d}p{j:04d}", "text": para}
                                      for j, para in enumerate(re.split(r"\n\s*\n", text.strip()), 1) if para.strip()]}
                        for i, (name, text) in enumerate(files.items(), 1)]}


def review_schema(catalog: dict, *, passes: list[str]):
    ids = [p["id"] for source in catalog["sources"] for p in source["passages"]]
    return obj({"verdict": enum(("pass", "revise", "major_rewrite")),
        "coverage": array(TEXT), "checks": array(obj({"name": enum(passes), "result": enum(("pass", "finding")), "reason": TEXT})),
        "findings": array(obj({"severity": enum(("high", "medium", "low")),
            "kind": enum(("continuity", "structural", "character", "voice", "prose", "proofread")),
            "chapters": array(INTEGER), "evidence_ids": array(enum(ids)), "problem": TEXT, "fix": TEXT, "preserve": TEXT})),
        "ending_resolved": {"type": "boolean"}, "limitations": TEXT})


def validate_review(path: Path, schema: dict, catalog: dict, passes: list[str], *, max_chapter: int):
    report = validate_json(path, schema)
    if report["valid"]:
        data = read_json(path)
        expected = [source["source"] for source in catalog["sources"]]
        if sorted(data["coverage"]) != sorted(expected):
            report["errors"].append("Review did not cover every assigned source exactly once")
        if sorted(row["name"] for row in data["checks"]) != sorted(passes):
            report["errors"].append("Review omitted or duplicated a required check")
        if data["verdict"] == "pass" and any(f["severity"] == "high" for f in data["findings"]):
            report["errors"].append("A high-severity finding cannot accompany a passing audit")
        for finding in data["findings"]:
            if not finding["evidence_ids"] or not finding["chapters"]:
                report["errors"].append("Every finding needs source evidence and affected chapters")
            if any(not 1 <= n <= max_chapter for n in finding["chapters"]):
                report["errors"].append("Finding references an unplanned chapter")
        report["catalog_sha256"] = digest(encoded(catalog))
    report["valid"] = not report["errors"]
    return report


AUDIT_PASSES = ["Brief contract", "Existence", "Voice", "Over-explanation", "Human mess", "Failure",
                "Repetition", "Structure", "Continuity", "Machine prose", "Pitch and payoff"]
PLAN_PASSES = ["Premise", "Reader promise", "Time window", "Point of view", "Chapter dependencies", "Ledger facts"]
PROOF_PASSES = ["Spelling and grammar", "Names and typography", "Formatting and completeness"]
