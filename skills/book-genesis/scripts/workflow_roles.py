"""Structured artifact contracts; no provider calls and no editorial gate targets."""
from __future__ import annotations

import re
from pathlib import Path

from export_book import Chapter, count_prose_words, _XML_INVALID_RE, discover_chapters, word_count_receipt
from workflow_state import digest, encoded, freeze, read_json
from correction_edits import retains_title


TEXT = {"type": "string"}
INTEGER = {"type": "integer"}


def production_facts(chapter_paths, contract):
    """Count the exact supplied snapshot with the exporter's prose counter.

    This is measured source data, not a model verdict or a quality target.
    Enumerate public production fields rather than exposing the private contract.
    """
    paths = [Path(path).resolve() for path in chapter_paths]
    if not paths:
        raise ValueError("Production facts require a complete chapter snapshot")
    chapters = discover_chapters(paths[0].parent)
    if {chapter.path.resolve() for chapter in chapters} != set(paths) or len(paths) != len(chapters):
        raise ValueError("Production facts must count exactly the supplied chapter snapshot")
    return {"fixed_contract": {key: contract[key] for key in ("chapters", "min_words", "max_words")},
        "observed_chapters": len(chapters), "prose_word_count": word_count_receipt(chapters),
        "interpretation": "These are deterministic counts of the complete supplied manuscript. The fixed contract gives the hard chapter and whole-book length requirements. Per-chapter estimates in planning prose are guides, not additional hard word limits. Assess pacing on its own merits; do not infer a whole-book length violation from an outline estimate."}


def character_context(markdown, participants):
    """Select approved cards without asking a model to resummarize their facts.

    Named H2 cards are the foundation's usual format. If an older foundation
    uses another format, retain its approved text rather than silently give a
    writer no character context. The outline and POV constrain who is on stage.
    """
    headings = list(re.finditer(r"^##[ \t]+(.+)$", markdown, re.M))
    selected = []
    for index, heading in enumerate(headings):
        title = re.sub(r"[*_`]", "", heading[1]).strip()
        title = re.sub(r"^\d+[.)]\s*", "", title)
        name = re.split(r",|\s+[—–]\s+|\s*\(", title, maxsplit=1)[0].strip()
        if not name:
            continue
        exact = re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", participants,
                          re.I if len(name.split()) > 1 else 0)
        # A card headed 'Mara Vale, daughter' also applies when a local outline
        # calls her 'Mara'. Keep this fallback case-sensitive to avoid a name
        # such as Will matching the ordinary auxiliary 'will'.
        first = name.split()[0]
        short = (len(first) >= 2 and first[0].isupper()
                 and re.search(r"(?<!\w)" + re.escape(first) + r"(?!\w)", participants))
        if exact or short:
            end = headings[index + 1].start() if index + 1 < len(headings) else len(markdown)
            selected.append(markdown[heading.start():end].strip())
    return "\n\n".join(selected) if selected else markdown


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
    if kind == "string" and (_XML_INVALID_RE.search(value) or re.search(r"[\ud800-\udfff]", value)):
        errors.append(f"{where}: text contains XML-invalid control characters or unpaired Unicode surrogates; return valid readable Unicode")
    if kind == "object":
        if set(value) != set(schema["properties"]):
            errors.append(f"{where}: missing or unexpected fields")
        for key in set(value) & set(schema["properties"]):
            errors += validate_shape(value[key], schema["properties"][key], where + "." + key)
    elif kind == "array":
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", float("inf")):
            errors.append(f"{where}: wrong number of items")
        for i, item in enumerate(value):
            errors += validate_shape(item, schema["items"], f"{where}[{i}]")
    return errors


# These are process assertions, not story facts. Do not forward them to fresh
# critics even if a planning model puts them inside an otherwise valid string.
PROCESS_CLAIMS = re.compile(r"(?i)brief contract check|verification\s*:|independent verification|"
    r"(?:prior|previous|earlier|supplied) (?:finding|review|verdict)|repair history|"
    r"(?:gate|audit|rubric)[ _-](?:status|score|passed|failed)|\bphase [0-7]\b")


def neutral_contract_schema():
    return obj({name: TEXT for name in ("premise", "reader_promise", "point_of_view", "time_window", "tone")})


def plan_schema(chapters):
    chapter = obj({"number": INTEGER, **{name: TEXT for name in ("title", "point_of_view", "time_window", "purpose",
        "scene_pressure", "events", "characters", "continuity", "opening", "ending")}})
    return obj({"opening_strategy": TEXT,
        "writer_facts": obj({name: array(TEXT) for name in ("identities", "calendar", "setting")}),
        "promises": {**array(obj({"promise": TEXT, "setup_action": TEXT, "on_page_resolution": TEXT,
            "setup_chapters": {**array(INTEGER), "minItems": 1}, "payoff_chapters": {**array(INTEGER), "minItems": 1}})), "minItems": 1},
        "chapters": {**array(chapter), "minItems": chapters, "maxItems": chapters},
        "canon": obj({name: array(TEXT) for name in ("characters", "timeline", "world_rules", "objects", "knowledge")})})


def validate_neutral(data):
    text = encoded(data).decode("utf-8")
    return ["Story facts contain process verdicts or repair history; return only current declarative story facts"] if PROCESS_CLAIMS.search(text) else []


def render_plan(data):
    """Render the same neutral fact structure used by writers and verifiers."""
    outline = ["# Chapter outline", ""]
    for chapter in data["chapters"]:
        outline += [f"## Chapter {chapter['number']}: {chapter['title']}", ""]
        outline += [f"**{key.replace('_', ' ').capitalize()}:** {value}\n" for key, value in chapter.items() if key not in ("number", "title")]
    outline += ["## Story promises and causal payoffs", ""]
    for promise in data["promises"]:
        outline += [f"**Promise:** {promise['promise']}",
            f"**Setup, chapters {promise['setup_chapters']}:** {promise['setup_action']}",
            f"**Resolution, chapters {promise['payoff_chapters']}:** {promise['on_page_resolution']}", ""]
    ledger = ["# Planned continuity canon", "", "These are planned facts; chapter drafts separately record demonstrated events.", ""]
    for category, facts in data["writer_facts"].items():
        ledger += ["## Baseline " + category.title(), ""] + [f"- {fact}" for fact in facts] + [""]
    for category, facts in data["canon"].items():
        ledger += ["## " + category.replace("_", " ").title(), ""] + [f"- {fact}" for fact in facts] + [""]
    return {"artifacts/07-outline.md": "\n".join(outline), "artifacts/08-opening-strategy.md": data["opening_strategy"],
            "artifacts/09-continuity-ledger.md": "\n".join(ledger)}


def plan_text_fields(data, prefix=""):
    fields = {}
    if isinstance(data, str):
        return {prefix: data}
    for key, value in (enumerate(data) if isinstance(data, list) else data.items()):
        if isinstance(value, (str, dict, list)):
            fields.update(plan_text_fields(value, prefix + "/" + str(key)))
    return fields


def plan_repair_schema(data):
    # The journal binds this response to the exact input plan. The controller
    # already owns the original value; asking the model to retype it adds no
    # concurrency protection and makes valid edits fail on typographic drift.
    return obj({"edits": {**array(obj({"path": enum(plan_text_fields(data)), "after": TEXT})), "minItems": 1}})


def apply_plan_edits(data, edits):
    """Change named text fields only; preserve every other approved plan value."""
    import copy
    from collections import Counter
    fields = plan_text_fields(data)
    result = copy.deepcopy(data)
    duplicates = sorted(path for path, count in Counter(e["path"] for e in edits).items() if count > 1)
    if duplicates:
        raise ValueError("Duplicate plan edit paths: " + ", ".join(duplicates)
                         + ". Consolidate each into one complete after value; do not choose a value by list order.")
    for edit in edits:
        path = edit["path"]
        if path not in fields:
            raise ValueError(f"Plan edit does not name an existing text field: {path}")
        if "before" in edit and edit["before"] != fields[path]:
            raise ValueError(f"Plan edit before value differs from the frozen original at {path}")
        if edit["after"] == fields[path]:
            continue  # Harmless repeated context is not a substantive repair.
        parts = path.strip("/").split("/")
        target = result
        for part in parts[:-1]:
            target = target[int(part)] if isinstance(target, list) else target[part]
        target[int(parts[-1]) if isinstance(target, list) else parts[-1]] = edit["after"]
    if result == data:
        raise ValueError("No substantive plan edit; an unchanged plan cannot be rerated")
    return result


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
    return validate_prose_text(read_json(path)["prose"], path, low=low, high=high, report=report)


def validate_prose_text(prose: str, path: Path, *, low: int, high: int, report=None):
    report = report or {"valid": True, "errors": []}
    report["errors"] += validate_shape(prose, TEXT, "prose")
    if report["errors"]:
        report["valid"] = False
        return report
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


CORRECTION_SCHEMA = obj({"replacements": {**array(obj({"before": TEXT, "after": TEXT})), "minItems": 1, "maxItems": 64}})


def apply_corrections(original: str, replacements: list[dict]) -> str:
    """Apply disjoint, unambiguous literal edits; no fuzzy matching or rewriting."""
    spans = []
    for row in replacements:
        before, after = row["before"], row["after"]
        if not before or original.count(before) != 1:
            raise ValueError("Each correction must name one unique exact passage from the original chapter")
        start = original.index(before)
        spans.append((start, start + len(before), after))
    spans.sort()
    if any(left[1] > right[0] for left, right in zip(spans, spans[1:])):
        raise ValueError("Correction passages overlap")
    candidate = original
    for start, end, after in reversed(spans):
        candidate = candidate[:start] + after + candidate[end:]
    if candidate == original or not retains_title(original.splitlines()[0][2:], candidate.splitlines()[0][2:]):
        raise ValueError("Factual corrections must retain the heading and change the body")
    return candidate


def validate_corrections(path: Path, original: str, *, low: int, high: int):
    report = validate_json(path, CORRECTION_SCHEMA)
    if report["valid"]:
        try:
            candidate = apply_corrections(original, read_json(path)["replacements"])
            report = validate_prose_text(candidate, path, low=low, high=high, report=report)
        except ValueError as exc:
            report.update(valid=False, errors=[str(exc)])
    return report


def text_catalog(files: dict[str, str]):
    return {"sources": [{"source": name, "sha256": digest(text.encode("utf-8")),
                         "passages": [{"id": f"s{i:02d}p{j:04d}", "text": para}
                                      for j, para in enumerate(re.split(r"\n\s*\n", text.strip()), 1) if para.strip()]}
                        for i, (name, text) in enumerate(files.items(), 1)]}


def review_schema(catalog: dict, *, passes: list[str]):
    ids = [p["id"] for source in catalog["sources"] for p in source["passages"]]
    return obj({"verdict": enum(("pass", "revise", "major_rewrite")),
        "coverage": {**array(enum(source["source"] for source in catalog["sources"])),
                     "minItems": len(catalog["sources"]), "maxItems": len(catalog["sources"])},
        "checks": {**array(obj({"name": enum(passes), "result": enum(("pass", "finding")), "reason": TEXT})),
                   "minItems": len(passes), "maxItems": len(passes)},
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
