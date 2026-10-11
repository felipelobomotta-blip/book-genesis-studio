"""Repair claims require their own real quotes and a changed mechanism."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from creative_groups import schema_for, validate_report
from repair_findings import finding_schema, validate_findings
from workflow_roles import text_catalog, validate_shape
from workflow_state import encoded
from test_creative_groups import group_report


class RepairFindingTests(unittest.TestCase):
    def setUp(self):
        self.catalog = text_catalog({
            "original/chapter-01.md": "# One\n\nAda gave the brass fork to Cal.\n\nThe school door remained open.",
            "proposed/chapter-01.md": "# One\n\nAda gave the brass fork to Cal.\n\nThe school door was locked by Ada.",
            "original/chapter-02.md": "# Two\n\nCal held the fork until the medic arrived.",
            "proposed/chapter-02.md": "# Two\n\nCal held the fork until the medic arrived.",
            "contract/00-brief.md": "# Brief\n\nAda and Cal meet the medic at school.",
        })
        self.originals = {n: f"original/chapter-{n:02d}.md" for n in (1, 2)}
        self.proposals = {n: f"proposed/chapter-{n:02d}.md" for n in (1, 2)}
        self.sources = {s["source"]: s for s in self.catalog["sources"]}

    def quote(self, source, text):
        return {"passage_id": next(p["id"] for p in self.sources[source]["passages"] if text in p["text"]),
                "quote": text}

    def finding(self):
        return {"kind": "introduced_regression", "chapters": [1],
                "problem": "The proposed locked door removes the existing access.",
                "causal_test": "The original door is open, while the proposal locks it.",
                "limitations": "The controller checks quotes; interpretation still needs a reading.",
                "original_evidence": [self.quote(self.originals[1], "The school door remained open.")],
                "proposed_evidence": [self.quote(self.proposals[1], "The school door was locked by Ada.")],
                "supporting_evidence": []}

    def errors(self, finding):
        schema = finding_schema(self.catalog, self.originals, self.proposals)
        shape = validate_shape([finding], schema)
        return shape or validate_findings([finding], self.catalog, self.originals, self.proposals)

    def test_changed_mechanism_can_support_a_negative_repair_check_without_approving_its_meaning(self):
        self.assertEqual([], self.errors(self.finding()))
        schema = schema_for(self.catalog, [1, 2])
        from catalog_wire import render_catalog
        packet = "\nCatalog wire:\n" + render_catalog(self.catalog)
        report = group_report(packet, schema, blocked=True)
        report["findings"] = [self.finding()]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "response"
            path.write_bytes(encoded(report))
            validated = validate_report(path, schema, self.catalog, [1, 2])
            self.assertTrue(validated["valid"], validated["errors"])
            self.assertEqual("block", report["verdict"])

    def test_misquoted_event_and_swapped_source_cannot_authorize_a_block(self):
        finding = self.finding()
        finding["proposed_evidence"][0]["quote"] = "Cal gave the fork to the medics."
        self.assertIn("quote is absent", "; ".join(self.errors(finding)))
        finding = self.finding()
        finding["original_evidence"] = finding["proposed_evidence"]
        self.assertTrue(self.errors(finding))

    def test_unchanged_custody_cannot_be_claimed_as_an_introduced_regression(self):
        finding = self.finding()
        finding["original_evidence"] = [self.quote(self.originals[1], "Ada gave the brass fork to Cal.")]
        finding["proposed_evidence"] = [self.quote(self.proposals[1], "Ada gave the brass fork to Cal.")]
        self.assertIn("these quotes are unchanged", "; ".join(self.errors(finding)))
        finding["kind"] = "unresolved_ticket"
        self.assertEqual([], self.errors(finding))

    def test_every_affected_chapter_needs_its_own_original_and_proposed_quotes(self):
        finding = self.finding(); finding["chapters"] = [1, 2]
        self.assertEqual(2, len(self.errors(finding)))
        finding["original_evidence"].append(self.quote(self.originals[2], "Cal held the fork until the medic arrived."))
        finding["proposed_evidence"].append(self.quote(self.proposals[2], "Cal held the fork until the medic arrived."))
        self.assertEqual([], self.errors(finding))
        finding["chapters"] = [1, 1]
        self.assertIn("duplicates", "; ".join(self.errors(finding)))

    def test_headings_empty_quotes_and_inferred_events_are_not_prose_evidence(self):
        for quote in ("", " "):
            finding = self.finding(); finding["original_evidence"][0]["quote"] = quote
            self.assertTrue(self.errors(finding))
        finding = self.finding()
        finding["original_evidence"][0] = self.quote(self.originals[1], "# One")
        self.assertTrue(self.errors(finding))
        finding = self.finding(); finding["kind"] = "inferred_regression"
        self.assertTrue(self.errors(finding))
        for source in self.catalog["sources"]:
            self.assertEqual(source, self.sources[source["source"]])


if __name__ == "__main__":
    unittest.main()
