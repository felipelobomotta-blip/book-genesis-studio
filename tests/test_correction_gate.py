"""Factual correctness evidence stays distinct from literary preference votes."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
import check_correction as correction
from promote_chapter import promote_chapter, PromotionError


class CorrectionGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.accepted = self.root / "chapter-01.md"
        self.candidate = self.root / "candidate.md"
        self.canon = self.root / "canon.md"
        self.context = self.root / "chapter-02.md"
        self.accepted.write_text("# A name\n\nJonah Vale kept the key.\n", encoding="utf-8")
        self.candidate.write_text("# A name\n\nJonah Mercer kept the key.\n", encoding="utf-8")
        self.canon.write_text("Jonah Mercer is Elise's brother.\n", encoding="utf-8")
        self.context.write_text("# The door\n\nJonah's key opened it.\n", encoding="utf-8")
        self.bundle = self.root / "bundle"
        correction.prepare(self.accepted, self.candidate, [self.canon], [self.context], "Correct Jonah's surname against canon.", self.bundle)
        self.manifest = self.bundle / "manifest.private.json"
        self.call = self.root / "call"
        self.call.mkdir()
        self.report = {"verdict": "pass", "canon_supported": True, "factual_only": True,
                       "dependencies_safe": True, "evidence": [
                           {"passage_id": "accepted-p0002", "reason": "Wrong surname."},
                           {"passage_id": "candidate-p0002", "reason": "Correct surname."},
                           {"passage_id": "canon-1-p0001", "reason": "Established name."}],
                       "findings": []}
        self.write_call()
        self.decision = self.root / "decision.json"
        self.receipt = self.root / "promotion.json"

    def write_call(self):
        (self.call / "packet").write_bytes((self.bundle / "review.packet.md").read_bytes())
        (self.call / "response").write_text(json.dumps(self.report), encoding="utf-8")
        (self.call / "stdout").write_text("fixture stdout", encoding="utf-8")
        (self.call / "stderr").write_text("fixture stderr", encoding="utf-8")
        receipt = {"status": "completed", "exit_code": 0, "error": None}
        receipt.update({name + "_sha256": correction.digest(self.call / name) for name in ("packet", "response", "stdout", "stderr")})
        (self.call / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")

    def freeze(self):
        return correction.decision(self.manifest, self.call, self.decision)

    def promote(self, **kwargs):
        return promote_chapter(self.accepted, self.candidate, self.decision, self.receipt, **kwargs)

    def test_verified_factual_promotion_preserves_original_without_inventing_panel_votes(self):
        original = self.accepted.read_bytes()
        before = (self.call / "response").read_bytes()
        decision = self.freeze()
        self.assertNotIn("votes", decision)
        receipt = self.promote()
        self.assertIsNone(receipt["panel"])
        self.assertEqual("fresh_verified_factual_correction", receipt["correction"]["rule"])
        self.assertEqual(original, Path(receipt["backup_path"]).read_bytes())
        self.assertEqual(self.candidate.read_bytes(), self.accepted.read_bytes())
        self.assertEqual(before, (self.call / "response").read_bytes())

    def test_negative_verdict_or_any_failed_check_keeps_original(self):
        valid = copy.deepcopy(self.report)
        for field in ("verdict", "canon_supported", "factual_only", "dependencies_safe", "findings"):
            with self.subTest(field=field):
                self.report = copy.deepcopy(valid)
                self.report[field] = "block" if field == "verdict" else ["Unresolved dependency"] if field == "findings" else False
                self.write_call()
                with self.assertRaisesRegex(correction.CorrectionError, "blocked"):
                    self.freeze()
                self.assertIn("Jonah Vale", self.accepted.read_text())
                self.assertFalse(self.decision.exists())

    def test_invented_or_missing_canon_evidence_and_malformed_reports_fail(self):
        valid = copy.deepcopy(self.report)
        bad = []
        item = copy.deepcopy(valid)
        item["evidence"][0]["passage_id"] = "accepted-p9999"
        bad.append(item)
        item = copy.deepcopy(valid)
        item["evidence"] = item["evidence"][:2]
        bad.append(item)
        item = copy.deepcopy(valid)
        item["canon_supported"] = "true"
        bad.append(item)
        bad.append([])
        for report in bad:
            with self.subTest(report=report):
                self.report = report
                self.write_call()
                with self.assertRaises(correction.CorrectionError):
                    self.freeze()

    def test_stale_canon_cannot_be_rehashed_to_reuse_a_review(self):
        self.canon.write_text("Jonah Vale is Elise's brother.\n", encoding="utf-8")
        with self.assertRaisesRegex(correction.CorrectionError, "source changed"):
            self.freeze()
        manifest = correction.read_json(self.manifest)
        manifest["sources"][2]["sha256"] = correction.digest(self.canon)
        self.manifest.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(correction.CorrectionError, "complete sources"):
            self.freeze()

    def test_pending_failed_wrong_packet_or_modified_native_evidence_cannot_authorize(self):
        receipt_path = self.call / "receipt.json"
        for failure in ("pending", "failed", "packet", "response", "stdout", "stderr"):
            with self.subTest(failure=failure):
                self.write_call()
                pending = self.call / "response.pending"
                pending.unlink(missing_ok=True)
                if failure == "pending":
                    pending.write_text("still writing")
                elif failure == "failed":
                    record = correction.read_json(receipt_path)
                    record["status"] = "failed"
                    receipt_path.write_text(json.dumps(record))
                else:
                    (self.call / failure).write_text("changed", encoding="utf-8")
                with self.assertRaises(correction.CorrectionError):
                    self.freeze()

    def test_source_report_and_decision_changes_before_promotion_are_rejected(self):
        self.freeze()
        paths = [self.canon, self.context, self.manifest, self.call / "response", self.call / "receipt.json"]
        for path in paths:
            with self.subTest(path=path):
                original = path.read_bytes()
                path.write_bytes(original + b" ")
                with self.assertRaises(PromotionError):
                    self.promote()
                path.write_bytes(original)
                self.assertIn("Jonah Vale", self.accepted.read_text())
                self.assertFalse(self.receipt.exists())

    def test_evidence_change_during_atomic_promotion_keeps_original(self):
        self.freeze()
        original = self.accepted.read_bytes()
        with self.assertRaisesRegex(PromotionError, "evidence changed"):
            self.promote(_before_replace=lambda: self.context.write_text("New dependent action", encoding="utf-8"))
        self.assertEqual(original, self.accepted.read_bytes())
        self.assertFalse(self.receipt.exists())

    def test_preparation_requires_existing_canon_distinct_inputs_and_unchanged_heading(self):
        cases = [([], self.candidate), ([self.accepted], self.candidate), ([self.canon], self.accepted)]
        for canon, candidate in cases:
            with self.assertRaises(correction.CorrectionError):
                correction.prepare(self.accepted, candidate, canon, [], "Correction", self.root / "bad")
        self.candidate.write_text("# New title\n\nJonah Mercer kept the key.\n", encoding="utf-8")
        with self.assertRaisesRegex(correction.CorrectionError, "heading"):
            correction.prepare(self.accepted, self.candidate, [self.canon], [], "Correction", self.root / "bad")

    def test_decisions_and_bundles_are_never_overwritten(self):
        self.freeze()
        with self.assertRaises(FileExistsError):
            self.freeze()
        with self.assertRaises(FileExistsError):
            correction.prepare(self.accepted, self.candidate, [self.canon], [], "Correction", self.bundle)

    def test_malformed_and_duplicate_json_cannot_be_treated_as_approval(self):
        for path, invalid in [(self.manifest, "[]"), (self.manifest, '{"schema_version":1,"schema_version":2}'),
                              (self.call / "receipt.json", "null")]:
            with self.subTest(path=path, invalid=invalid):
                original = path.read_bytes()
                path.write_text(invalid, encoding="utf-8")
                with self.assertRaises(correction.CorrectionError):
                    self.freeze()
                path.write_bytes(original)
                self.assertFalse(self.decision.exists())
                self.assertIn("Jonah Vale", self.accepted.read_text())


if __name__ == "__main__":
    unittest.main()
