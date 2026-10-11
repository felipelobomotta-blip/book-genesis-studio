"""Source-bound causal traces for whole-manuscript audits.

The host verifies locations and report consistency. A source hash or a valid
shape does not prove the critic's literary interpretation. Planned events,
reader disclosure and character acquisition are deliberately separate.
"""
import re


INSTRUCTIONS = """Causal evidence records:
Return causal_traces for at least one important knowledge-dependent action and
the central reader promise. Trace actual chapter prose, not plans as events.
Each trace names the fact or promise, its recipient, story time (or a bounded
unknown), acquisition/setup passages, later use/payoff passages, and passages
that disclose it to the reader. Include every disputed knowledge path and
central missing payoff you flag. IDs come only from chapter prose in this
catalog; quotations in guides or the planned canon are not observed events.
Use basis observed for directly shown events, derived for a stated inference
from quoted facts, and inferred for a plausible unshown route. An inferred
route remains status unknown; it is not proof of a contradiction or resolution.
A late reveal to the reader does not mean a character learned the fact late.
Distinguish story time from chapter order, including memories and flashbacks.
For a contradiction, cite the use and the earlier facts that rule out timely
acquisition; state the causal test. For an unknown route, state what is missing
and what would establish it. Do not manufacture a scene merely to remove an
unknown. Every contradicted trace needs a matching supported finding; a passing
audit cannot contain a proved contradiction. The reason is a short evidence
explanation, not private reasoning. These are craft checks, not a sales model.
"""


def chapter_passages(catalog):
    return {passage["id"]: source["source"]
            for source in catalog["sources"]
            if re.fullmatch(r"chapter-\d+\.md", source["source"])
            for passage in source["passages"]
            if not re.fullmatch(r"#{1,6}\s+[^\n]+", passage["text"].strip())}


def trace_schema(catalog):
    text = {"type": "string"}
    evidence = {"type": "array", "items": {"type": "string", "enum": list(chapter_passages(catalog))}}
    fields = {"id": text, "kind": {"type": "string", "enum": ["knowledge", "promise_payoff"]},
              "subject": text, "recipient": text, "story_time": text,
              "acquisition_or_setup_evidence_ids": evidence,
              "use_or_payoff_evidence_ids": {**evidence, "minItems": 1},
              "reader_disclosure_evidence_ids": evidence,
              "basis": {"type": "string", "enum": ["observed", "derived", "inferred"]},
              "status": {"type": "string", "enum": ["supported", "contradicted", "unknown"]},
              "reason": text, "limitations": text}
    return {"type": "array", "minItems": 2, "maxItems": 24,
            "items": {"type": "object", "properties": fields, "required": list(fields), "additionalProperties": False}}


def validate_traces(data, catalog):
    """No automatic inference about story chronology or prose quality."""
    errors, seen = [], set()
    kinds = {trace["kind"] for trace in data["causal_traces"]}
    if kinds != {"knowledge", "promise_payoff"}:
        errors.append("Causal traces must cover an important knowledge use and the central promise")
    allowed = chapter_passages(catalog)
    for trace in data["causal_traces"]:
        identifier = trace["id"]
        if identifier in seen:
            errors.append("Causal trace IDs must be unique")
        seen.add(identifier)
        for field in ("acquisition_or_setup_evidence_ids", "use_or_payoff_evidence_ids", "reader_disclosure_evidence_ids"):
            ids = trace[field]
            if len(ids) != len(set(ids)) or any(identifier not in allowed for identifier in ids):
                errors.append(f"Causal trace {identifier}: {field} needs unique chapter prose IDs")
        if trace["basis"] == "inferred" and trace["status"] != "unknown":
            errors.append(f"Causal trace {identifier}: an unshown inferred route must remain unknown")
        if trace["status"] == "supported" and not trace["acquisition_or_setup_evidence_ids"]:
            errors.append(f"Causal trace {identifier}: supported acquisition/setup needs chapter evidence")
        if trace["status"] == "contradicted":
            if data["verdict"] == "pass":
                errors.append(f"Causal trace {identifier}: a proved contradiction cannot accompany a passing audit")
            ids = set(trace["acquisition_or_setup_evidence_ids"] + trace["use_or_payoff_evidence_ids"])
            if not any(finding["kind"] in {"continuity", "structural"}
                       and ids.intersection(finding["evidence_ids"]) for finding in data["findings"]):
                errors.append(f"Causal trace {identifier}: a contradiction needs a matching continuity or structural finding")
    return errors
