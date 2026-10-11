"""Explicit chapter coverage for plan reviews, without judging story semantics."""
import re


CHECK_FIELDS = {
    "Point of view and purpose": ("point of view", "purpose"),
    "Time window and deadline": ("time window", "opening", "ending"),
    "Knowledge and object custody": ("continuity", "events", "characters"),
    "Setup and consequences": ("scene pressure", "events", "opening", "ending"),
}

INSTRUCTIONS = """Verify each chapter against the approved brief and complete ledger.
Return chapter_checks for every chapter exactly once. Each has all four named
checks exactly once, a pass/finding result, relevant evidence_ids and a short
source explanation. The supplied chapter coverage map lists the exact fields
that must be cited for each check; additional brief, ledger or other chapter IDs
may be needed to demonstrate a dependency. Read those fields, not just headings.
For each finding, flag the affected chapter's corresponding check and give a
matching ordinary finding with that chapter and shared evidence. A flagged
chapter check cannot coexist with a passing verdict. Keep an ordinary pass when
an approximate duration or valid delayed reader disclosure is consistent; do
not invent an exact deadline, strict viewpoint cycle or unseen knowledge route.
This grid records source coverage, not automatic proof of literary correctness.
"""


def chapter_requirements(catalog):
    sources = [s for s in catalog["sources"] if s["source"] == "outline"]
    if len(sources) != 1:
        raise ValueError("Plan review requires one controller-rendered outline")
    chapters, current = [], None
    for passage in sources[0]["passages"]:
        text = passage["text"].strip()
        heading = re.match(r"^## Chapter (\d+):", text)
        if heading:
            current = {"chapter": int(heading[1]), "fields": {}}
            chapters.append(current)
            continue
        if text == "## Story promises and causal payoffs":
            current = None
        field = re.match(r"^\*\*([^*]+):\*\*", text)
        if current is not None and field:
            name = field[1].strip().casefold()
            if name in current["fields"]:
                raise ValueError("Repeated controller-rendered plan field")
            current["fields"][name] = passage["id"]
    if not chapters or [row["chapter"] for row in chapters] != list(range(1, len(chapters) + 1)):
        raise ValueError("Plan coverage requires every chapter in order")
    requirements = []
    for row in chapters:
        try:
            checks = [{"name": name, "required_evidence_ids": [row["fields"][field] for field in fields]}
                      for name, fields in CHECK_FIELDS.items()]
        except KeyError as exc:
            raise ValueError("Controller-rendered plan is missing a required chapter field") from exc
        requirements.append({"chapter": row["chapter"], "checks": checks})
    return requirements


def chapter_check_schema(catalog):
    requirements = chapter_requirements(catalog)
    ids = [p["id"] for source in catalog["sources"] for p in source["passages"]]
    check = {"name": {"type": "string", "enum": list(CHECK_FIELDS)},
             "result": {"type": "string", "enum": ["pass", "finding"]},
             "evidence_ids": {"type": "array", "items": {"type": "string", "enum": ids}, "minItems": 2},
             "reason": {"type": "string"}}
    row = {"chapter": {"type": "integer", "enum": [r["chapter"] for r in requirements]},
           "checks": {"type": "array", "minItems": len(CHECK_FIELDS), "maxItems": len(CHECK_FIELDS),
                      "items": {"type": "object", "properties": check, "required": list(check), "additionalProperties": False}}}
    return {"type": "array", "minItems": len(requirements), "maxItems": len(requirements),
            "items": {"type": "object", "properties": row, "required": list(row), "additionalProperties": False}}


def validate_chapter_checks(data, catalog):
    requirements = chapter_requirements(catalog)
    errors = []
    expected = {r["chapter"]: r for r in requirements}
    rows = data["chapter_checks"]
    if sorted(r["chapter"] for r in rows) != sorted(expected):
        errors.append("Plan review must cover every chapter exactly once")
    flagged = {}
    for row in rows:
        chapter = row["chapter"]
        if sorted(c["name"] for c in row["checks"]) != sorted(CHECK_FIELDS):
            errors.append(f"Plan chapter {chapter}: omitted or duplicated a required check")
        required = {c["name"]: set(c["required_evidence_ids"]) for c in expected[chapter]["checks"]}
        for check in row["checks"]:
            ids = set(check["evidence_ids"])
            if len(ids) != len(check["evidence_ids"]) or not required[check["name"]].issubset(ids):
                errors.append(f"Plan chapter {chapter}, {check['name']}: cite the required exact chapter fields once")
            if check["result"] == "finding":
                flagged.setdefault(chapter, set()).update(ids)
                if not any(chapter in f["chapters"] and ids.intersection(f["evidence_ids"]) for f in data["findings"]):
                    errors.append(f"Plan chapter {chapter}: a flagged check needs a matching source-bound finding")
    for finding in data["findings"]:
        if any(not set(finding["evidence_ids"]).intersection(flagged.get(n, set())) for n in finding["chapters"]):
            errors.append("Plan finding must match the affected chapter checks and their evidence")
    if flagged and data["verdict"] == "pass":
        errors.append("A flagged plan chapter cannot accompany a passing verdict")
    return errors
