"""Vote identity comes from frozen evidence, never from hand-written tallies."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from build_comparison import build_comparison
from decide_comparison import decide, main
from promote_chapter import promote_chapter
from validate_blind_reader import validate_blind_reader_report


class ComparisonDecisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.accepted, self.candidate = self.root / "chapter-01.md", self.root / "candidate.md"
        self.accepted.write_text("# One\n\nMara closed the door.\n\nThe key waited.\n", encoding="utf-8")
        self.candidate.write_text("# One\n\nMara opened the door.\n\nThe key fell.\n", encoding="utf-8")
        self.bundle = self.root / "bundle"
        self.manifest = build_comparison(self.accepted, self.candidate, self.bundle)
        self.manifest_path = self.bundle / "manifest.private.json"
        self.index_path = self.root / "index.json"

    def reports(self, preferences):
        index = {}
        for row, preference in zip(self.manifest["readers"], preferences):
            choice = preference if preference in {"A", "B", "same"} else next(k for k, v in row["mapping"].items() if v == preference)
            raw = {"schema_version": 3, "catalog_sha256": row["catalog_sha256"], "reader": row["reader"],
                   "turn_page": "yes", "stopped_at": None, "why_stopped": None,
                   "remember_tomorrow": [], "confused_by": [], "flags": [], "machine_tells": [],
                   "strongest_passage": {"passage_id": "A:p0001", "reason": "A concrete action."},
                   "weakest_passage": {"passage_id": "B:p0002", "reason": "Low stakes."},
                   "felt": {"emotion": "curious", "reason": "A choice to follow."},
                   "confidence": "medium", "compare": choice}
            report = self.root / (row["persona"] + ".json")
            validation = self.root / (row["persona"] + ".validation.json")
            report.write_text(json.dumps(raw), encoding="utf-8")
            checked = validate_blind_reader_report([self.accepted, self.candidate], report,
                                                   expected_reader=row["reader"], catalog_path=self.bundle / row["catalog"])
            self.assertTrue(checked["valid"], checked)
            validation.write_text(json.dumps(checked), encoding="utf-8")
            index[row["persona"]] = {"report": report.name, "validation": validation.name}
        self.index_path.write_text(json.dumps(index), encoding="utf-8")

    def decide(self):
        return decide(self.manifest_path, self.index_path, 1)

    def test_actual_promotion_follows_three_valid_mapped_votes_and_preserves_original(self):
        self.reports(["candidate"] * 3 + ["accepted"])
        original = self.accepted.read_bytes()
        decision = self.decide()
        self.assertEqual("promote", decision["decision"])
        self.assertEqual((3, 1, 0), (decision["revision_votes"], decision["accepted_votes"], decision["neutral_votes"]))
        path = self.root / "decision.json"
        path.write_text(json.dumps(decision))
        receipt = promote_chapter(self.accepted, self.candidate, path, self.root / "promotion.json")
        self.assertEqual(original, Path(receipt["backup_path"]).read_bytes())
        self.assertEqual(self.accepted.read_bytes(), self.candidate.read_bytes())

    def test_all_a_votes_are_a_counterbalanced_tie_not_four_votes_for_revision(self):
        self.reports(["A"] * 4)
        decision = self.decide()
        self.assertEqual((2, 2), (decision["revision_votes"], decision["accepted_votes"]))
        self.assertEqual("reject", decision["decision"])
        self.assertIn("separate_per_version_defect_evidence", decision["reason"])
        self.assertNotIn("accepted_concrete_defects", decision)
        self.assertNotIn("candidate_concrete_defects", decision)

    def test_same_remains_neutral_and_never_becomes_an_invented_preference(self):
        self.reports(["candidate"] * 3 + ["same"])
        decision = self.decide()
        self.assertEqual("same", decision["votes"][3]["prefers"])
        self.assertEqual((3, 0, 1), (decision["revision_votes"], decision["accepted_votes"], decision["neutral_votes"]))
        self.assertEqual("reject", decision["decision"])
        self.assertEqual("nondecisive_panel", decision["reason"])

    def test_new_candidate_cannot_reuse_old_reads_even_when_cited_paragraphs_survive(self):
        self.reports(["candidate"] * 4)
        # All quoted/identified original passages remain present. The new
        # uncited paragraph still changes the draft those readers must judge.
        self.candidate.write_text(self.candidate.read_text(encoding="utf-8") + "\nShe burned the letter.\n", encoding="utf-8")
        new_bundle = self.root / "new-comparison"
        build_comparison(self.accepted, self.candidate, new_bundle)
        with self.assertRaisesRegex(ValueError, "validations must pass"):
            decide(new_bundle / "manifest.private.json", self.index_path, 1)

    def test_original_report_receipt_or_source_changes_reject_the_decision(self):
        self.reports(["candidate"] * 4)
        for path in (self.root / "primary.json", self.root / "primary.validation.json", self.accepted):
            with self.subTest(path=path):
                original = path.read_bytes()
                if path.name.endswith("validation.json"):
                    record = json.loads(original)
                    record["report_sha256"] = "0" * 64
                    path.write_text(json.dumps(record))
                else:
                    path.write_bytes(original + b" ")
                with self.assertRaises(ValueError):
                    self.decide()
                path.write_bytes(original)

    def test_mapping_swap_and_reused_report_cannot_change_votes(self):
        self.reports(["candidate"] * 4)
        saved = self.manifest_path.read_bytes()
        altered = json.loads(saved)
        for row in altered["readers"]:
            row["mapping"] = {k: "candidate" if v == "accepted" else "accepted" for k, v in row["mapping"].items()}
        self.manifest_path.write_text(json.dumps(altered))
        with self.assertRaisesRegex(ValueError, "private mapping"):
            self.decide()
        self.manifest_path.write_bytes(saved)
        index = json.loads(self.index_path.read_text())
        index["hostile"] = index["primary"]
        self.index_path.write_text(json.dumps(index))
        with self.assertRaisesRegex(ValueError, "two readers"):
            self.decide()

    def test_cli_preserves_existing_decision_instead_of_overwriting_it(self):
        self.reports(["candidate"] * 4)
        output = self.root / "decision.json"
        output.write_text("prior evidence", encoding="utf-8")
        from contextlib import redirect_stdout
        from unittest.mock import patch
        import io
        args = ["decide_comparison.py", "--manifest", str(self.manifest_path), "--index", str(self.index_path),
                "--chapter", "1", "--output", str(output)]
        with patch.object(sys, "argv", args), redirect_stdout(io.StringIO()):
            self.assertEqual(1, main())
        self.assertEqual("prior evidence", output.read_text())


if __name__ == "__main__":
    unittest.main()
