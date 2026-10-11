"""Check the sources of repair accusations without deciding literary meaning."""
import re

from workflow_roles import TEXT, INTEGER, array, enum, obj


def _prose(catalog):
    return {p["id"]: (source["source"], p["text"])
            for source in catalog["sources"] for p in source["passages"]
            if not re.fullmatch(r"#{1,6}\s+[^\n]+", p["text"].strip())}


def finding_schema(catalog, originals, proposals):
    prose = _prose(catalog)
    quote = lambda names: obj({"passage_id": enum([pid for pid, (name, _) in prose.items() if name in names]),
                               "quote": TEXT})
    return array(obj({
        "kind": enum(("unresolved_ticket", "introduced_regression")),
        "chapters": {**array({**INTEGER, "enum": list(originals)}), "minItems": 1},
        "problem": TEXT, "causal_test": TEXT, "limitations": TEXT,
        "original_evidence": {**array(quote(set(originals.values()))), "minItems": 1},
        "proposed_evidence": {**array(quote(set(proposals.values()))), "minItems": 1},
        "supporting_evidence": array(obj({"passage_id": enum(list(prose)), "quote": TEXT})),
    }))


def validate_findings(findings, catalog, originals, proposals):
    prose = _prose(catalog)
    by_name = {source["source"]: "\n\n".join(p["text"] for p in source["passages"])
               for source in catalog["sources"]}
    errors = []
    for number, finding in enumerate(findings, 1):
        label = f"Repair finding {number}"
        chapters = finding["chapters"]
        if len(chapters) != len(set(chapters)):
            errors.append(label + " duplicates an affected chapter")
        for field, expected in (("original_evidence", originals), ("proposed_evidence", proposals)):
            cited = {prose[row["passage_id"]][0] for row in finding[field]}
            needed = {expected[n] for n in chapters}
            if not needed.issubset(cited):
                errors.append(label + " needs " + field + " from every affected chapter")
        for field in ("original_evidence", "proposed_evidence", "supporting_evidence"):
            for row in finding[field]:
                quote = row["quote"]
                if not quote.strip() or quote not in prose[row["passage_id"]][1]:
                    errors.append(label + ": " + field + " quote is absent from its assigned prose passage")
        if finding["kind"] == "introduced_regression":
            # An accusation about a new regression must point to a changed
            # on-page mechanism. An unchanged quoted mechanism does not prove
            # that the proposed edit introduced it. Interpretation stays human
            # or model work; this check never automatically approves prose.
            changed = any(row["quote"] not in by_name[proposals[n]]
                          for n in chapters for row in finding["original_evidence"]
                          if prose[row["passage_id"]][0] == originals[n])
            changed |= any(row["quote"] not in by_name[originals[n]]
                           for n in chapters for row in finding["proposed_evidence"]
                           if prose[row["passage_id"]][0] == proposals[n])
            if not changed:
                errors.append(label + ": introduced_regression must cite a changed mechanism; these quotes are unchanged")
    return errors


INSTRUCTIONS = """Every blocking finding must name unresolved_ticket or introduced_regression,
the affected chapters and exact quotes from their original AND proposed prose.
Quote the actual passage assigned to its ID; never attach an inferred statement
to an unrelated passage or swap original and proposed versions. A new regression
needs a quoted change that introduced its mechanism. An unchanged defect outside
the assigned ticket does not become a new regression because it was noticed now.
State the short source test and its limits. Follow object custody, acquisition,
story time, use and reader disclosure separately. A later disclosure can reveal
an earlier event. An ordinary unshown transfer or acquisition remains unknown
unless on-page facts rule it out; absence alone does not prove impossibility.
Distinguish that uncertainty from a ticketed missing setup or an unearned rescue
that fails the actual repair. Do not invent quoted events. This is an evidence
explanation, not a score or private reasoning. Valid citations cannot prove your
interpretation; you must still assess the complete proposed book.
"""
