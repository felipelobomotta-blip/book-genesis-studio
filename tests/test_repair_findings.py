"""Repair claims require their own real quotes and a changed mechanism."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from creative_groups import schema_for, validate_report
from repair_findings import finding_schema, validate_findings, locate_quote
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

    def test_missing_quote_feedback_locates_field_row_and_exact_same_source_matches(self):
        finding = self.finding()
        correct = finding["proposed_evidence"][0]["passage_id"]
        wrong = self.quote(self.proposals[1], "Ada gave the brass fork to Cal.")["passage_id"]
        finding["proposed_evidence"][0]["passage_id"] = wrong
        before = encoded(finding)
        errors = self.errors(finding)
        self.assertEqual(1, len(errors))
        self.assertIn("proposed_evidence[1]", errors[0])
        self.assertIn(f"passage_id={wrong}", errors[0])
        self.assertIn("proposed/chapter-01.md", errors[0])
        self.assertIn(f"Exact quote matches within this same source: {correct}", errors[0])
        self.assertIn("The school door was locked by Ada.", errors[0])
        self.assertEqual(before, encoded(finding))
        self.assertNotIn("verdict", errors[0])

    def test_quote_feedback_never_suggests_another_version_or_invented_text(self):
        finding = self.finding()
        finding["proposed_evidence"][0]["quote"] = "The school door remained open."
        errors = self.errors(finding)
        self.assertTrue(any("No exact quote match exists in this source" in e for e in errors))
        self.assertFalse(any("Exact quote matches within this same source:" in e for e in errors))
        finding["proposed_evidence"][0]["quote"] = "The school door had been locked by Ada."
        self.assertTrue(any("No exact quote match exists in this source" in e for e in self.errors(finding)))

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


    def test_wrapped_native_control_quotes_resolve_only_inside_the_assigned_passage(self):
        original = ("At eight, Ada handed Cal the only brass fork. He closed his fist around it.\n"
                    "The medic would arrive at nine. Cal stayed at the school table. Ada worked at\n"
                    "the adjacent piano; neither left the room. They did not exchange the fork again\n"
                    "before nine.")
        proposed = original.replace("The medic would arrive at nine.",
            "At eight ten Cal gave the fork to a departing medic, who carried it outside and did not return before nine.")
        catalog = text_catalog({self.originals[1]: original, self.proposals[1]: proposed})
        evidence = []
        finding = self.finding()
        for field, source, text in (("original_evidence", self.originals[1], original),
                                    ("proposed_evidence", self.proposals[1], proposed)):
            passage = next(s["passages"][0] for s in catalog["sources"] if s["source"] == source)
            finding[field] = [{"passage_id": passage["id"], "quote": " ".join(text.split())}]
        before = encoded(finding)
        self.assertEqual([], validate_findings([finding], catalog, self.originals, self.proposals,
                                             located_quotes=evidence))
        self.assertEqual(before, encoded(finding))
        self.assertEqual([original, proposed], [row["source_quote"] for row in evidence])
        self.assertEqual(["whitespace_only", "whitespace_only"], [row["match"] for row in evidence])

    def test_whitespace_equivalent_unchanged_mechanism_cannot_authorize_a_regression(self):
        original = "Ada gave the brass fork\nto Cal."
        proposed = "Ada gave the brass fork\tto Cal."
        catalog = text_catalog({self.originals[1]: original, self.proposals[1]: proposed})
        finding = self.finding()
        for field, source in (("original_evidence", self.originals[1]),
                              ("proposed_evidence", self.proposals[1])):
            passage = next(s["passages"][0] for s in catalog["sources"] if s["source"] == source)
            finding[field] = [{"passage_id": passage["id"], "quote": "Ada gave the brass fork to Cal."}]
        self.assertIn("these quotes are unchanged", "; ".join(
            validate_findings([finding], catalog, self.originals, self.proposals)))

    def test_validated_source_quotes_are_metadata_and_never_rewrite_the_report(self):
        from catalog_wire import render_catalog
        finding = self.finding()
        schema = schema_for(self.catalog, [1, 2])
        report = group_report("\nCatalog wire:\n" + render_catalog(self.catalog), schema, blocked=True)
        report["findings"] = [finding]
        raw = encoded(report)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "response"
            path.write_bytes(raw)
            validated = validate_report(path, schema, self.catalog, [1, 2])
            self.assertTrue(validated["valid"], validated["errors"])
            self.assertEqual(raw, path.read_bytes())
            self.assertEqual("block", report["verdict"])
            self.assertEqual(2, len(validated["quote_evidence"]))
            for row in validated["quote_evidence"]:
                passage = next(p["text"] for p in self.sources[row["source"]]["passages"]
                               if p["id"] == row["passage_id"])
                self.assertEqual(passage[row["start"]:row["end"]], row["source_quote"])


class QuoteLocationTests(unittest.TestCase):
    def test_exact_matching_preserves_existing_behavior(self):
        self.assertEqual({"start": 0, "end": 3, "source_quote": "Cal", "match": "exact"},
                         locate_quote("Cal met Cal.", "Cal"))

    def test_line_wraps_tabs_and_unicode_whitespace_preserve_source_characters(self):
        source = "Before. Ada\r\ngave\tthe\u00a0fork\u2003to Cal. After."
        result = locate_quote(source, "Ada gave the fork to Cal.")
        self.assertEqual("whitespace_only", result["match"])
        self.assertEqual("Ada\r\ngave\tthe\u00a0fork\u2003to Cal.", result["source_quote"])
        self.assertEqual(source[result["start"]:result["end"]], result["source_quote"])

    def test_changed_words_punctuation_case_and_omissions_are_not_whitespace(self):
        source = "At eight, Ada gave\nthe brass fork to Cal."
        for quote in ("At nine, Ada gave the brass fork to Cal.",
                      "At eight Ada gave the brass fork to Cal.",
                      "At eight, ada gave the brass fork to Cal.",
                      "Ada gave the fork to Cal.", "Ada gave ... to Cal.",
                      "Ada gave the brass fork to Cal!", "Adagave the brass fork to Cal."):
            with self.subTest(quote=quote):
                self.assertIsNone(locate_quote(source, quote))

    def test_empty_and_wrong_passage_quotes_are_rejected(self):
        for quote in ("", " \t\n", "Cal gave the fork to Ada."):
            self.assertIsNone(locate_quote("Ada gave\nthe fork to Cal.", quote))

    def test_ambiguous_whitespace_matches_are_rejected_including_overlaps(self):
        self.assertIsNone(locate_quote("Ada\ngave. Ada\tgave.", "Ada gave."))
        self.assertIsNone(locate_quote("a\na\na", "a a"))


if __name__ == "__main__":
    unittest.main()
