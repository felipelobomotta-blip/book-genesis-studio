import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "skills/book-genesis/scripts"))
from validate_rubric import DIMENSIONS, rubric_schema, validate_rubric


def valid_report():
    evidence = {"chapter": 1, "quote": "Mara kept the key.", "reason": "A concrete character choice."}
    return {"schema_version": 1, "coverage": {"scope": "full_manuscript", "chapters": [1, 2]},
            "dimensions": [{"name": name, "score": 6.0, "evidence": [dict(evidence)], "reason": "Competent but limited."} for name in DIMENSIONS],
            "strongest_passage": dict(evidence),
            "weakest_passage": {"chapter": 2, "quote": "The door stayed shut.", "reason": "A familiar ending."},
            "confidence": {"level": "low", "reason": "A short synthetic fixture."},
            "limitations": "No human or market validation."}


class RubricTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.chapters = [self.root / "chapter-01.md", self.root / "chapter-02.md"]
        self.chapters[0].write_text('# One\n\nMara kept the key. She said, “No.”\n\n<!-- Hidden secret. -->\n', encoding="utf-8")
        self.chapters[1].write_text("# Two\n\nThe door stayed shut.\n", encoding="utf-8")
        self.path = self.root / "report.json"

    def check(self, report, **kwargs):
        self.path.write_text(json.dumps(report), encoding="utf-8")
        return validate_rubric(self.chapters, self.path, expected_chapters=2, **kwargs)

    def test_valid_complete_receipt_preserves_inputs_and_does_not_grade(self):
        original = [p.read_bytes() for p in self.chapters]
        result = self.check(valid_report())
        self.assertTrue(result["complete"], result["errors"])
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), result["report_sha256"])
        self.assertEqual(original, [p.read_bytes() for p in self.chapters])
        self.assertEqual("not_assessed_by_this_tool", result["literary_quality"])

    def test_fabricated_paraphrased_wrong_chapter_and_hidden_quotes_fail(self):
        for quote, chapter in (("Mara held the key.", 1), ("She opened the door.", 1), ("Mara kept the key.", 2), ("Hidden secret.", 1)):
            with self.subTest(quote=quote, chapter=chapter):
                report = valid_report()
                report["dimensions"][0]["evidence"][0].update(quote=quote, chapter=chapter)
                self.assertFalse(self.check(report)["valid"])

    def test_typography_normalization_is_allowed_without_changing_words(self):
        report = valid_report()
        report["dimensions"][0]["evidence"][0]["quote"] = 'She said, "No."'
        self.assertTrue(self.check(report)["complete"])

    def test_high_score_needs_two_distinct_source_excerpts(self):
        report = valid_report()
        row = report["dimensions"][0]
        row["score"] = 9.2
        row["evidence"].append(copy.deepcopy(row["evidence"][0]))
        self.assertFalse(self.check(report)["complete"])
        row["evidence"][1] = {"chapter": 2, "quote": "The door stayed shut.", "reason": "A separate observation."}
        self.assertTrue(self.check(report)["complete"])

    def test_missing_duplicate_or_unknown_dimensions_fail(self):
        for change in (lambda rows: rows.pop(), lambda rows: rows.append(copy.deepcopy(rows[0])), lambda rows: rows[0].update(name="Invented")):
            report = valid_report()
            change(report["dimensions"])
            self.assertFalse(self.check(report)["valid"])

    def test_unassessed_dimension_is_honest_but_cannot_pass(self):
        report = valid_report()
        report["dimensions"][0].update(score=None, evidence=[], reason="Missing context.")
        result = self.check(report)
        self.assertTrue(result["valid"])
        self.assertEqual("incomplete", result["status"])
        self.assertEqual(["Originality"], result["unassessed"])

    def test_samples_omissions_duplicates_and_unknown_full_length_do_not_pass(self):
        for coverage in ({"scope":"sample", "chapters":[1,2]}, {"scope":"full_manuscript", "chapters":[1]}, {"scope":"full_manuscript", "chapters":[1,1,2]}, {"scope":[], "chapters":[1,2]}):
            report = valid_report()
            report["coverage"] = coverage
            self.assertFalse(self.check(report)["complete"])
        self.check(valid_report())
        self.assertFalse(validate_rubric(self.chapters, self.path)["complete"])

    def test_bool_nonfinite_out_of_range_and_huge_scores_fail(self):
        for value in (True, float("nan"), float("inf"), -1, 11, 10**500):
            with self.subTest(value=str(value)[:20]):
                report = valid_report()
                report["dimensions"][0]["score"] = value
                self.assertFalse(self.check(report)["valid"])

    def test_malformed_nested_values_and_json_null_fail_without_crashing(self):
        for value in (None, [], "text", {"schema_version":1}):
            self.assertFalse(self.check(value)["valid"])
        report = valid_report()
        report["confidence"]["level"] = []
        self.assertFalse(self.check(report)["valid"])

    def test_duplicate_json_keys_fail(self):
        self.path.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
        self.assertFalse(validate_rubric(self.chapters, self.path, expected_chapters=2)["valid"])

    def test_original_receipt_rejects_changed_prose_even_if_all_quotes_survive(self):
        result = self.check(valid_report())
        receipt = self.root / "receipt.json"
        receipt.write_text(json.dumps(result), encoding="utf-8")
        self.assertTrue(validate_rubric(self.chapters, self.path, expected_chapters=2, original_receipt=receipt)["complete"])
        self.chapters[1].write_text(self.chapters[1].read_text(encoding="utf-8") + "A new scene.\n", encoding="utf-8")
        check = validate_rubric(self.chapters, self.path, expected_chapters=2, original_receipt=receipt)
        self.assertFalse(check["complete"])
        self.assertIn("source chapters differ", " ".join(check["errors"]))

    def test_original_receipt_rejects_changed_scores_and_failed_original(self):
        report = valid_report()
        original = self.check(report)
        receipt = self.root / "receipt.json"
        receipt.write_text(json.dumps(original), encoding="utf-8")
        report["dimensions"][0]["score"] = 8.9
        self.assertFalse(self.check(report, original_receipt=receipt)["complete"])
        original.update(status="invalid", complete=False)
        receipt.write_text(json.dumps(original), encoding="utf-8")
        self.assertFalse(self.check(valid_report(), original_receipt=receipt)["complete"])

    def test_dimension_contract_matches_shipped_criteria(self):
        criteria = (REPO / "skills/book-genesis/references/scoring/rubric-criteria.md").read_text(encoding="utf-8")
        names = re.findall(r"^\| \d+ \| (\w+) \|", criteria, re.M)
        self.assertEqual(list(DIMENSIONS), names)
        self.assertEqual(list(valid_report()), rubric_schema()["required"])


if __name__ == "__main__":
    unittest.main()
