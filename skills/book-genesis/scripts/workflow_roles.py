"""Structured artifact contracts; no provider calls and no editorial gate targets."""
from __future__ import annotations

import re
from pathlib import Path

from export_book import Chapter, count_prose_words, _XML_INVALID_RE, discover_chapters, word_count_receipt
from workflow_state import digest, encoded, freeze, read_json
from correction_edits import retains_title
from narrative_evidence import trace_schema, validate_traces


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
    counts = word_count_receipt(chapters)
    if counts["total"] <= 0:
        raise ValueError("Production positions require visible prose")
    before, positions = 0, []
    for row in counts["chapters"]:
        through = before + row["words"]
        positions.append({"chapter": row["number"], "words_before": before, "words_through": through,
            "percentage_before": round(100 * before / counts["total"], 3),
            "percentage_through": round(100 * through / counts["total"], 3)})
        before = through
    return {"fixed_contract": {key: contract[key] for key in ("chapters", "min_words", "max_words")},
        "observed_chapters": len(chapters), "prose_word_count": counts, "chapter_positions": positions,
        "interpretation": "These are deterministic counts and chapter positions in the complete supplied manuscript. "
            "Any event in a chapter lies within its measured whole-book word and percentage interval; do not guess "
            "a position from chapter numbering or confuse a local chapter percentage with a whole-book percentage. "
            "The fixed contract gives the hard chapter and whole-book length requirements. Per-chapter estimates "
            "and beat positions in planning prose are guides, not additional hard limits. Assess pacing through "
            "the actual action and consequences; a percentage difference alone does not establish a defect. "
            "Do not infer a whole-book length violation from an outline estimate."}


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


def hook_schema(reader):
    return obj({"reader": enum((reader,)), "options": {**array(obj({
        "id": {"type": "integer", "enum": [1, 2, 3]}, "click": {"type": "boolean"},
        "buy": {"type": "boolean"}, "keep_reading": {"type": "boolean"}, "reason": TEXT})),
        "minItems": 3, "maxItems": 3}})


def validate_hook(path, reader):
    report = validate_json(path, hook_schema(reader))
    if report["valid"] and sorted(row["id"] for row in read_json(path)["options"]) != [1, 2, 3]:
        report.update(valid=False, errors=["Hook options must cover IDs 1, 2, 3 exactly once"])
    return report


def enum(values):
    return {"type": "string", "enum": list(values)}


def validate_shape(value, schema, where="response"):
    """Validate the small schema subset used here; the provider is not trusted."""
    if "anyOf" in schema:
        return ([] if any(not validate_shape(value, option, where) for option in schema["anyOf"])
                else [f"{where}: does not match any permitted type or value"])
    errors = []
    kind = schema.get("type")
    valid_type = {"object": isinstance(value, dict), "array": isinstance(value, list),
                  "string": isinstance(value, str), "integer": type(value) is int,
                  "boolean": type(value) is bool, "number": type(value) in (int, float),
                  "null": value is None}.get(kind, False)
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
    # Every editable field has exactly one slot. Null retains the original.
    # A native structured-output decoder can enforce unique object properties;
    # an array of {path, after} cannot prevent two conflicting values for a path.
    return obj({"edits": obj({path: {"anyOf": [TEXT, {"type": "null"}]}
                               for path in sorted(plan_text_fields(data))})})


def plan_repair_targets(data, catalog, findings):
    """Bind cited review passages to literal editable fields, without judging them."""
    fields = plan_text_fields(data)
    addresses = [{"chapter": row["number"], "title": row["title"], "prefix": f"/chapters/{index}"}
                 for index, row in enumerate(data["chapters"])]
    rendered = render_plan(data)
    texts = {"outline": rendered["artifacts/07-outline.md"], "ledger": rendered["artifacts/09-continuity-ledger.md"]}
    spans = {name: [] for name in texts}
    positions = {name: 0 for name in texts}

    def bind(source, fragment, path):
        start = texts[source].find(fragment, positions[source])
        if start < 0:
            raise ValueError("Plan repair field differs from rendered source: " + path)
        end = start + len(fragment)
        spans[source].append((start, end, path))
        positions[source] = end

    # Record literal rendered spans in their actual order. Continuations and
    # compacted bullet groups can then cite all overlapping fields without
    # guessing a chapter/index from the passage ID or matching repeated words.
    for index, chapter in enumerate(data["chapters"]):
        prefix = f"/chapters/{index}"
        bind("outline", f"## Chapter {chapter['number']}: {chapter['title']}", prefix + "/title")
        for key, value in chapter.items():
            if key not in ("number", "title"):
                bind("outline", f"**{key.replace('_', ' ').capitalize()}:** {value}", prefix + "/" + key)
    for index, promise in enumerate(data["promises"]):
        prefix = f"/promises/{index}"
        bind("outline", f"**Promise:** {promise['promise']}", prefix + "/promise")
        bind("outline", f"**Setup, chapters {promise['setup_chapters']}:** {promise['setup_action']}", prefix + "/setup_action")
        bind("outline", f"**Resolution, chapters {promise['payoff_chapters']}:** {promise['on_page_resolution']}", prefix + "/on_page_resolution")
    for section in ("writer_facts", "canon"):
        for category, facts in data[section].items():
            for index, fact in enumerate(facts):
                bind("ledger", "- " + fact, f"/{section}/{category}/{index}")
    wanted = {identifier for finding in findings for identifier in finding["evidence_ids"]}
    evidence = []
    seen = set()
    for source in catalog["sources"]:
        name = source["source"]
        cursor = 0
        if name in texts and source["sha256"] != digest(texts[name].encode("utf-8")):
            raise ValueError("Plan repair catalog differs from the current rendered " + name)
        for passage in source["passages"]:
            paths = []
            if name in texts:
                start = texts[name].find(passage["text"], cursor)
                if start < 0:
                    raise ValueError("Plan repair passage differs from rendered source: " + passage["id"])
                cursor = start + len(passage["text"])
                paths = [path for begin, end, path in spans[name] if begin < cursor and end > start]
            if passage["id"] in wanted:
                evidence.append({"passage_id": passage["id"], "source": source["source"],
                                 "text": passage["text"], "editable_paths": paths})
                seen.add(passage["id"])
    if wanted != seen:
        raise ValueError("Unknown plan repair evidence: " + ", ".join(sorted(wanted - seen)))
    return {"chapter_addresses": addresses, "editable_fields": fields, "cited_evidence": evidence}


def plan_edit_items(edits):
    """Literal map application; never select between conflicting alternatives.

    The list form is retained for explicit historical/helper callers. The new
    native response schema permits only the fixed nullable map.
    """
    if isinstance(edits, dict):
        return [{"path": path, "after": after} for path, after in sorted(edits.items()) if after is not None]
    return edits


def apply_plan_edits(data, edits):
    """Change named text fields only; preserve every other approved plan value."""
    import copy
    from collections import Counter
    edits = plan_edit_items(edits)
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
    from evidence_passages import evidence_passages
    return {"sources": [{"source": name, "sha256": digest(text.encode("utf-8")),
                         "passages": [{"id": f"s{i:02d}p{j:04d}", "text": para}
                                      for j, para in enumerate(evidence_passages(text, separator=r"\n\s*\n"), 1)]}
                        for i, (name, text) in enumerate(files.items(), 1)]}


def review_schema(catalog: dict, *, passes: list[str]):
    ids = [p["id"] for source in catalog["sources"] for p in source["passages"]]
    fields = {"verdict": enum(("pass", "revise", "major_rewrite")),
        "coverage": {**array(enum(source["source"] for source in catalog["sources"])),
                     "minItems": len(catalog["sources"]), "maxItems": len(catalog["sources"])},
        "checks": {**array(obj({"name": enum(passes), "result": enum(("pass", "finding")), "reason": TEXT})),
                   "minItems": len(passes), "maxItems": len(passes)},
        "findings": array(obj({"severity": enum(("high", "medium", "low")),
            "kind": enum(("continuity", "structural", "character", "voice", "prose", "proofread")),
            "chapters": array(INTEGER), "evidence_ids": array(enum(ids)), "problem": TEXT, "fix": TEXT, "preserve": TEXT})),
        "ending_resolved": {"type": "boolean"}, "limitations": TEXT}
    if passes == AUDIT_PASSES:
        fields["causal_traces"] = trace_schema(catalog)
    if passes == PLAN_PASSES:
        from plan_verification import chapter_check_schema
        fields["chapter_checks"] = chapter_check_schema(catalog)
    return obj(fields)


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
        if "causal_traces" in schema["properties"]:
            report["errors"] += validate_traces(data, catalog)
        if "chapter_checks" in schema["properties"]:
            from plan_verification import validate_chapter_checks
            report["errors"] += validate_chapter_checks(data, catalog)
        report["catalog_sha256"] = digest(encoded(catalog))
    report["valid"] = not report["errors"]
    return report


AUDIT_PASSES = ["Brief contract", "Existence", "Voice", "Over-explanation", "Human mess", "Failure",
                "Repetition", "Structure", "Continuity", "Machine prose", "Pitch and payoff"]
PLAN_PASSES = ["Premise", "Reader promise", "Time window", "Point of view", "Chapter dependencies", "Ledger facts"]
PROOF_PASSES = ["Spelling and grammar", "Names and typography", "Formatting and completeness"]
