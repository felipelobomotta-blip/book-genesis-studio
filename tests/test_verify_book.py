"""Regression checks for stale reader evidence and truthful technical delivery.

The reports here are synthetic fixtures, not literary acceptance evidence.
"""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/book-genesis/scripts"
sys.path.insert(0, str(SCRIPTS))

from export_book import export_book  # noqa: E402
from validate_blind_reader import validate_blind_reader_report  # noqa: E402
from verify_book import verify_book  # noqa: E402
from prepare_rubric import build_catalog, catalog_digest


class VerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="bg-current-evidence-")
        self.book = Path(self.temp.name)
        self.chapters = self.book / "manuscript/chapters"
        self.chapters.mkdir(parents=True)
        self.chapter = self.chapters / "chapter-01.md"
        self.chapter.write_text("# First\n\nMara checked the desk.\n\nThe room held its breath.\n", encoding="utf-8")
        self.readers = self.book / "evaluations/readers"
        self.readers.mkdir(parents=True)
        self.index_path = self.book / "evaluations/review-index.json"
        self.index = {"schema_version": 1, "scopes": [{"scope": "opening", "chapters": ["chapter-01.md"], "readers": []}]}
        for identity in ("primary", "hostile", "adjacent", "casual"):
            report = {
                "reader": identity, "turn_page": "yes", "stopped_at": None, "why_stopped": None,
                "remember_tomorrow": [{"quote": "Mara checked the desk.", "reason": "A concrete action."}],
                "confused_by": [], "flags": [], "machine_tells": [],
                "strongest_passage": {"quote": "Mara checked the desk.", "reason": "The action."},
                "weakest_passage": {"quote": "The room held its breath.", "reason": "A familiar image."},
                "felt": {"emotion": "uneasy", "reason": "The empty room."}, "confidence": "medium",
            }
            report_path = self.readers / f"{identity}.json"
            receipt_path = self.readers / f"{identity}-validation.json"
            self.write_json(report_path, report)
            receipt = validate_blind_reader_report([self.chapter], report_path)
            self.assertTrue(receipt["valid"], receipt)
            self.write_json(receipt_path, receipt)
            self.index["scopes"][0]["readers"].append({
                "reader": identity,
                "report": report_path.relative_to(self.book).as_posix(),
                "validation": receipt_path.relative_to(self.book).as_posix(),
            })
        self.save_index()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_json(self, path: Path, value: object) -> None:
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def save_index(self) -> None:
        self.write_json(self.index_path, self.index)

    def verify(self) -> dict:
        return verify_book(self.book, self.index_path)

    def export(self) -> dict:
        return export_book(self.book, self.book / "delivery", title="Test", author="Author", language="en")

    def test_original_current_receipts_cover_four_distinct_readers(self) -> None:
        result = self.verify()
        self.assertEqual("current", result["reviews"]["status"])
        self.assertTrue(result["reviews"]["scopes"][0]["majority_turn_page"])
        self.assertEqual("pending", result["delivery"]["status"])
        self.assertEqual("not_assessed", result["publication_approval"])

    def use_passage_reports(self):
        catalog_path = self.readers / "catalog.json"
        catalog = build_catalog([self.chapter])
        self.write_json(catalog_path, catalog)
        for row in self.index["scopes"][0]["readers"]:
            path = self.book / row["report"]
            report = json.loads(path.read_text())
            report.update(schema_version=2, catalog_sha256=catalog_digest(catalog))
            for item in report["remember_tomorrow"] + [report["strongest_passage"], report["weakest_passage"]]:
                quote = item.pop("quote")
                item["passage_id"] = "c01p0001" if quote.startswith("Mara") else "c01p0002"
            self.write_json(path, report)
            self.write_json(self.book / row["validation"], validate_blind_reader_report([self.chapter], path, catalog_path=catalog_path))
            row["catalog"] = catalog_path.relative_to(self.book).as_posix()
        self.save_index()

    def test_passage_receipts_cover_current_draft_and_detect_modified_resolutions(self):
        self.use_passage_reports()
        self.assertEqual("current", self.verify()["reviews"]["status"])
        path = self.book / self.index["scopes"][0]["readers"][0]["validation"]
        receipt = json.loads(path.read_text())
        receipt["resolved_evidence"][0]["quote"] = "A fabricated passage."
        self.write_json(path, receipt)
        self.assertEqual("incomplete", self.verify()["reviews"]["status"])

    def test_passage_review_index_requires_saved_catalog_and_original_digest(self):
        self.use_passage_reports()
        row = self.index["scopes"][0]["readers"][0]
        catalog_path = row.pop("catalog")
        self.save_index()
        self.assertEqual("incomplete", self.verify()["reviews"]["status"])
        row["catalog"] = catalog_path
        self.save_index()
        path = self.book / row["validation"]
        receipt = json.loads(path.read_text())
        receipt["catalog_sha256"] = "0" * 64
        self.write_json(path, receipt)
        self.assertEqual("incomplete", self.verify()["reviews"]["status"])

    def test_edit_invalidates_old_read_even_when_every_quote_still_matches(self) -> None:
        self.chapter.write_text(self.chapter.read_text(encoding="utf-8") + "\nShe left before the news arrived.\n", encoding="utf-8")
        result = self.verify()
        scope = result["reviews"]["scopes"][0]
        self.assertEqual("incomplete", result["reviews"]["status"])
        self.assertEqual([], scope["valid_readers"])
        self.assertFalse(scope["majority_turn_page"])
        self.assertTrue(all("stale" in issue for issue in scope["errors"]))

    def test_modified_raw_report_cannot_keep_its_original_receipt(self) -> None:
        path = self.readers / "primary.json"
        report = json.loads(path.read_text(encoding="utf-8"))
        report["turn_page"] = "no"
        self.write_json(path, report)
        result = self.verify()
        self.assertEqual("incomplete", result["reviews"]["status"])
        self.assertTrue(any("report hash differs" in issue for issue in result["reviews"]["scopes"][0]["errors"]))

    def test_failed_original_validation_is_not_resurrected_by_fresh_validation(self) -> None:
        path = self.readers / "primary-validation.json"
        receipt = json.loads(path.read_text(encoding="utf-8"))
        receipt.update(valid=False, status="invalid")
        self.write_json(path, receipt)
        self.assertEqual("incomplete", self.verify()["reviews"]["status"])

    def test_duplicate_identity_does_not_complete_a_panel(self) -> None:
        self.index["scopes"][0]["readers"][1] = self.index["scopes"][0]["readers"][0].copy()
        self.save_index()
        self.assertEqual("incomplete", self.verify()["reviews"]["status"])

    def test_missing_persona_does_not_complete_a_panel(self) -> None:
        self.index["scopes"][0]["readers"].pop()
        self.save_index()
        self.assertEqual("invalid", self.verify()["reviews"]["status"])

    def test_missing_raw_file_does_not_complete_a_panel(self) -> None:
        (self.readers / "hostile.json").unlink()
        self.assertEqual("incomplete", self.verify()["reviews"]["status"])

    def test_comparison_vote_does_not_replace_a_final_draft_read(self) -> None:
        path = self.readers / "primary.json"
        report = json.loads(path.read_text(encoding="utf-8"))
        report["compare"] = "A"
        self.write_json(path, report)
        self.write_json(self.readers / "primary-validation.json", validate_blind_reader_report([self.chapter], path))
        self.assertEqual("incomplete", self.verify()["reviews"]["status"])

    def test_delivered_formats_are_independent_of_stale_pending_yaml(self) -> None:
        (self.book / "PROJECT_STATE.yaml").write_text("delivery:\n  status: pending\n", encoding="utf-8")
        result = self.export()
        status = json.loads(Path(result["status_file"]).read_text(encoding="utf-8"))
        self.assertEqual("delivered", status["status"])
        self.assertEqual("draft", status["scope"])
        self.assertEqual("delivered", self.verify()["delivery"]["status"])
        self.assertEqual({"md", "epub"}, set(self.verify()["delivery"]["formats"]))
        self.assertEqual("not_assessed", status["publication_approval"])

    def test_changed_prose_makes_delivery_stale(self) -> None:
        self.export()
        self.chapter.write_text(self.chapter.read_text(encoding="utf-8") + "\nA new ending.\n", encoding="utf-8")
        self.assertEqual("stale", self.verify()["delivery"]["status"])

    def test_legacy_count_receipt_remains_valid_when_visible_counts_agree(self) -> None:
        result = self.export()
        path = Path(result["receipt"])
        receipt = json.loads(path.read_text(encoding="utf-8"))
        receipt["word_count"]["method"] = "whitespace_split_prose_v1"
        receipt["word_count"]["excludes"].remove("standalone HTML comments")
        self.write_json(path, receipt)
        self.assertEqual("delivered", self.verify()["delivery"]["status"])

    def test_changed_export_bytes_are_detected(self) -> None:
        result = self.export()
        Path(result["manuscript"]).write_text("a truncated manuscript", encoding="utf-8")
        self.assertEqual("stale", self.verify()["delivery"]["status"])

    def test_rehashing_a_truncated_manuscript_does_not_hide_missing_text(self) -> None:
        result = self.export()
        manuscript = Path(result["manuscript"])
        manuscript.write_text("a truncated manuscript", encoding="utf-8")
        receipt_path = Path(result["receipt"])
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["outputs"]["manuscript.md"]["sha256"] = hashlib.sha256(manuscript.read_bytes()).hexdigest()
        self.write_json(receipt_path, receipt)
        self.assertEqual("stale", self.verify()["delivery"]["status"])

    def test_changed_chapter_set_during_verification_is_stale(self) -> None:
        from verify_book import verify_delivery as real_verify_delivery

        def mutate(root, chapters):
            result = real_verify_delivery(root, chapters)
            self.chapter.write_text(self.chapter.read_text(encoding="utf-8") + "\nConcurrent edit.\n", encoding="utf-8")
            return result

        with patch("verify_book.verify_delivery", side_effect=mutate):
            result = self.verify()
        self.assertEqual("stale", result["delivery"]["status"])
        self.assertEqual("stale", result["reviews"]["status"])

    def test_verification_does_not_mutate_receipts_or_prose(self) -> None:
        self.export()
        before = {path.relative_to(self.book): path.read_bytes() for path in self.book.rglob("*") if path.is_file()}
        self.verify()
        after = {path.relative_to(self.book): path.read_bytes() for path in self.book.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_cli_delivery_check_does_not_silently_claim_reader_coverage(self) -> None:
        self.export()
        delivery = subprocess.run([sys.executable, str(SCRIPTS / "verify_book.py"), "--book-dir", str(self.book), "--check", "delivery"], capture_output=True, text=True)
        all_checks = subprocess.run([sys.executable, str(SCRIPTS / "verify_book.py"), "--book-dir", str(self.book)], capture_output=True, text=True)
        self.assertEqual(0, delivery.returncode, delivery.stderr)
        self.assertEqual("not_run", json.loads(delivery.stdout)["reviews"]["status"])
        self.assertEqual(1, all_checks.returncode)


if __name__ == "__main__":
    unittest.main()
