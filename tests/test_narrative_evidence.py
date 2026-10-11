"""Causal evidence and hook contracts preserve uncertainty and real votes."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from workflow_roles import AUDIT_PASSES, review_schema, text_catalog, validate_review, validate_hook, hook_schema


class NarrativeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "report.json"
        self.catalog = text_catalog({"outline": "She is planned to learn about the red key.",
            "chapter-01.md": "# One\n\nMara found a red key.\n\nShe locked the door with it.",
            "chapter-02.md": "# Two\n\nA memory showed Jo telling her where it was.\n\nShe gave the key back."})
        self.schema = review_schema(self.catalog, passes=AUDIT_PASSES)
        ids = [p["id"] for source in self.catalog["sources"][1:] for p in source["passages"][1:]]
        self.ids = ids
        self.data = {"verdict": "pass", "coverage": [s["source"] for s in self.catalog["sources"]],
            "checks": [{"name": name, "result": "pass", "reason": "Synthetic location contract."} for name in AUDIT_PASSES],
            "findings": [], "ending_resolved": True, "limitations": "Synthetic fixture, no literary assessment.",
            "causal_traces": [{"id": f"t{n}", "kind": kind, "subject": "Where the red key is kept.", "recipient": "Mara",
                "story_time": "The memory is earlier than chapter one.", "acquisition_or_setup_evidence_ids": [ids[2]],
                "use_or_payoff_evidence_ids": [ids[1]], "reader_disclosure_evidence_ids": [ids[2]],
                "basis": "observed", "status": "supported", "reason": "Later disclosure depicts earlier acquisition.",
                "limitations": "Chronology needs a human reading; the host verifies locations."}
                for n, kind in enumerate(("knowledge", "promise_payoff"), 1)]}

    def validate(self):
        self.path.write_text(json.dumps(self.data), encoding="utf-8")
        return validate_review(self.path, self.schema, self.catalog, AUDIT_PASSES, max_chapter=2)

    def test_later_reader_disclosure_does_not_force_an_earlier_knowledge_violation(self):
        self.assertTrue(self.validate()["valid"])

    def test_plausible_off_page_route_remains_unknown_and_can_accompany_a_clean_audit(self):
        trace = self.data["causal_traces"][0]
        trace.update(basis="inferred", status="unknown", acquisition_or_setup_evidence_ids=[],
                     reason="A conversation is plausible but not shown.")
        self.assertTrue(self.validate()["valid"])
        trace["status"] = "contradicted"
        self.assertFalse(self.validate()["valid"])

    def test_plan_and_heading_are_not_observed_prose_evidence(self):
        for identifier in (self.catalog["sources"][0]["passages"][0]["id"], self.catalog["sources"][1]["passages"][0]["id"], "invented"):
            with self.subTest(identifier=identifier):
                self.data["causal_traces"][0]["acquisition_or_setup_evidence_ids"] = [identifier]
                self.assertFalse(self.validate()["valid"])

    def test_proved_contradiction_needs_a_negative_audit_and_linked_finding(self):
        trace = self.data["causal_traces"][0]
        trace["status"] = "contradicted"
        self.assertFalse(self.validate()["valid"])
        self.data["verdict"] = "revise"
        self.assertFalse(self.validate()["valid"])
        self.data["findings"] = [{"severity": "high", "kind": "continuity", "chapters": [1, 2],
            "evidence_ids": [self.ids[1]], "problem": "The supplied earlier event excludes timely acquisition.",
            "fix": "Repair the named knowledge path.", "preserve": "The red key and the return."}]
        self.assertTrue(self.validate()["valid"])

    def test_missing_or_duplicate_traces_and_unsupported_acquisition_are_rejected(self):
        original = copy.deepcopy(self.data)
        for change in ("duplicate", "no_setup", "no_knowledge", "no_use"):
            self.data = copy.deepcopy(original)
            if change == "duplicate":
                self.data["causal_traces"][1]["id"] = "t1"
            elif change == "no_setup":
                self.data["causal_traces"][0]["acquisition_or_setup_evidence_ids"] = []
            elif change == "no_knowledge":
                self.data["causal_traces"][0]["kind"] = "promise_payoff"
            else:
                self.data["causal_traces"][0]["use_or_payoff_evidence_ids"] = []
            with self.subTest(change=change):
                self.assertFalse(self.validate()["valid"])


class HookContractTests(unittest.TestCase):
    def test_exact_identity_and_negative_preferences_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "response"
            data = {"reader": "Lena", "options": [{"id": n, "click": False, "buy": False, "keep_reading": False,
                "reason": "The blurb does not interest me."} for n in (1, 2, 3)]}
            raw = json.dumps(data).encode()
            path.write_bytes(raw)
            self.assertTrue(validate_hook(path, "Lena")["valid"])
            self.assertEqual(raw, path.read_bytes())
            self.assertEqual(["Lena"], hook_schema("Lena")["properties"]["reader"]["enum"])
            for identity, identifiers in (("As Lena, package 1 is my favorite", [1, 2, 3]), ("Lena", [1, 1, 3]),
                                          ("Lena", [1, 2]), ("Lena", [1, 2, 4])):
                changed = copy.deepcopy(data)
                changed["reader"] = identity
                changed["options"] = [{**data["options"][0], "id": n} for n in identifiers]
                path.write_text(json.dumps(changed), encoding="utf-8")
                with self.subTest(identity=identity, identifiers=identifiers):
                    self.assertFalse(validate_hook(path, "Lena")["valid"])


if __name__ == "__main__":
    unittest.main()
