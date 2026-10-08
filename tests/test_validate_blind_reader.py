from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills/book-genesis/scripts/validate_blind_reader.py"
sys.path.insert(0, str(REPO_ROOT / "skills/book-genesis/scripts"))

from validate_blind_reader import validate_blind_reader_report  # noqa: E402


def valid_report() -> dict:
    return {
        "reader": "Priya",
        "turn_page": "yes",
        "stopped_at": None,
        "why_stopped": None,
        "remember_tomorrow": [
            {"quote": "Mara checked the desk.", "reason": "The physical detail stayed with me."}
        ],
        "confused_by": [],
        "flags": [],
        "strongest_passage": {
            "quote": "Mara checked the desk.",
            "reason": "It gives the scene a concrete start.",
        },
        "weakest_passage": {
            "quote": "The room held its breath.",
            "reason": "The image felt familiar.",
        },
        "machine_tells": [],
        "felt": {"emotion": "uneasy", "reason": "The missing key made me uneasy."},
        "confidence": "medium",
    }


class BlindReaderValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="bg-reader-validator-")
        self.root = Path(self.temp.name)
        self.chapter = self.root / "chapter-01.md"
        self.chapter.write_text(
            "# Chapter One\n\nMara checked the desk.\n\nThe room held its breath.\n",
            encoding="utf-8",
        )
        self.report = self.root / "report.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_report(self, value: object, *, fenced: bool = False) -> None:
        payload = json.dumps(value, ensure_ascii=False, indent=2)
        if fenced:
            payload = f"```json\n{payload}\n```\n"
        self.report.write_text(payload, encoding="utf-8")

    def test_valid_report_produces_passed_receipt_and_preserves_raw_report(self) -> None:
        report = valid_report()
        self.write_report(report)
        before = self.report.read_bytes()

        receipt = validate_blind_reader_report([self.chapter], self.report)

        self.assertTrue(receipt["valid"], receipt)
        self.assertEqual("passed", receipt["status"])
        self.assertEqual([], receipt["errors"])
        self.assertEqual(before, self.report.read_bytes())
        self.assertEqual(1, receipt["schema_version"])

    def test_single_json_fence_and_typographic_quote_normalization_are_allowed(self) -> None:
        report = valid_report()
        quote_chapter = self.root / "chapter-quote.md"
        quote_chapter.write_text(
            "# Quoted\n\nMara checked the desk’s drawer.\n",
            encoding="utf-8",
        )
        report["strongest_passage"]["quote"] = "Mara checked the desk's drawer."
        self.write_report(report, fenced=True)

        receipt = validate_blind_reader_report([self.chapter, quote_chapter], self.report)

        self.assertTrue(receipt["valid"], receipt)

    def test_balanced_inline_emphasis_can_be_omitted_without_changing_quote_words(self) -> None:
        for marker in ("*", "**", "_", "__"):
            with self.subTest(marker=marker):
                report = valid_report()
                quote_chapter = self.root / f"chapter-emphasis-{len(marker)}.md"
                quote_chapter.write_text(
                    f"# Quoted\n\nMara checked the {marker}Mercy Bell{marker} before dawn.\n",
                    encoding="utf-8",
                )
                report["strongest_passage"]["quote"] = "Mara checked the Mercy Bell before dawn."
                self.write_report(report)

                receipt = validate_blind_reader_report([self.chapter, quote_chapter], self.report)

                self.assertTrue(receipt["valid"], receipt)

    def test_emphasis_normalization_does_not_allow_word_substitution_or_cross_boundary_quotes(self) -> None:
        report = valid_report()
        quote_chapter = self.root / "chapter-emphasis.md"
        quote_chapter.write_text(
            "# Quoted\n\nMara checked the *Mercy Bell* before dawn.\n",
            encoding="utf-8",
        )

        report["strongest_passage"]["quote"] = "She checked the Mercy Bell before dawn."
        self.write_report(report)
        receipt = validate_blind_reader_report([self.chapter, quote_chapter], self.report)
        self.assertFalse(receipt["valid"])

        report = valid_report()
        report["strongest_passage"]["quote"] = "before dawn. The room held its breath."
        second_chapter = self.root / "chapter-emphasis-02.md"
        second_chapter.write_text(
            "# Second chapter\n\nThe room held its breath.\n",
            encoding="utf-8",
        )
        self.write_report(report)
        receipt = validate_blind_reader_report(
            [self.chapter, quote_chapter, second_chapter], self.report
        )
        self.assertFalse(receipt["valid"])

    def test_unbalanced_emphasis_markers_remain_strict(self) -> None:
        report = valid_report()
        quote_chapter = self.root / "chapter-emphasis.md"
        quote_chapter.write_text(
            "# Quoted\n\nMara checked the *Mercy Bell before dawn.\n",
            encoding="utf-8",
        )
        report["strongest_passage"]["quote"] = "Mara checked the Mercy Bell before dawn."
        self.write_report(report)

        receipt = validate_blind_reader_report([self.chapter, quote_chapter], self.report)

        self.assertFalse(receipt["valid"])

    def test_invented_quote_fails_closed_without_rewriting_report(self) -> None:
        report = valid_report()
        report["strongest_passage"]["quote"] = "She checked the desk."
        self.write_report(report)
        before = self.report.read_bytes()

        receipt = validate_blind_reader_report([self.chapter], self.report)

        self.assertFalse(receipt["valid"])
        self.assertTrue(any("exact contiguous quote" in error for error in receipt["errors"]))
        self.assertEqual(before, self.report.read_bytes())

    def test_invalid_flag_and_copied_felt_are_rejected(self) -> None:
        report = valid_report()
        report["flags"] = [{"flag": "made_up", "quote": "Mara checked the desk."}]
        report["felt"] = {
            "emotion": "Mara checked the desk. The room held its breath.",
            "reason": "This is copied instead of naming an emotion.",
        }
        self.write_report(report)

        receipt = validate_blind_reader_report([self.chapter], self.report)

        self.assertFalse(receipt["valid"])
        self.assertTrue(any("allowed flag" in error for error in receipt["errors"]))
        self.assertTrue(any("copied prose" in error for error in receipt["errors"]))

    def test_required_fields_and_enums_are_strict(self) -> None:
        report = valid_report()
        report.pop("reader")
        report["turn_page"] = "maybe"
        report["confidence"] = "certain"
        report["compare"] = "newer"
        self.write_report(report)

        receipt = validate_blind_reader_report([self.chapter], self.report)

        self.assertFalse(receipt["valid"])
        self.assertTrue(any("missing required fields" in error for error in receipt["errors"]))
        self.assertTrue(any("turn_page" in error for error in receipt["errors"]))
        self.assertTrue(any("confidence" in error for error in receipt["errors"]))
        self.assertTrue(any("compare" in error for error in receipt["errors"]))

    def test_malformed_json_is_invalid_with_a_receipt(self) -> None:
        self.report.write_text('{"reader": ', encoding="utf-8")

        receipt = validate_blind_reader_report([self.chapter], self.report)

        self.assertFalse(receipt["valid"])
        self.assertEqual("invalid", receipt["status"])
        self.assertTrue(any("malformed JSON" in error for error in receipt["errors"]))

    def test_json_null_is_invalid_with_a_receipt(self) -> None:
        self.report.write_text("null\n", encoding="utf-8")

        receipt = validate_blind_reader_report([self.chapter], self.report)

        self.assertFalse(receipt["valid"])
        self.assertTrue(any("JSON object" in error for error in receipt["errors"]))

    def test_unhashable_enum_values_fail_as_json_errors_without_traceback(self) -> None:
        cases = {
            "turn_page": {},
            "confidence": [],
            "compare": {},
            "flags": [{"flag": [], "quote": "Mara checked the desk."}],
        }
        for field, value in cases.items():
            with self.subTest(field=field):
                report = valid_report()
                if field == "compare":
                    report["compare"] = value
                else:
                    report[field] = value
                self.write_report(report)
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "--chapter", str(self.chapter), "--report", str(self.report)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertNotEqual(0, result.returncode)
                self.assertEqual("", result.stderr)
                receipt = json.loads(result.stdout)
                self.assertFalse(receipt["valid"])

    def test_utf8_bom_is_accepted_but_report_hash_covers_raw_bytes(self) -> None:
        payload = json.dumps(valid_report(), ensure_ascii=False).encode("utf-8")
        self.report.write_bytes(b"\xef\xbb\xbf" + payload)

        receipt = validate_blind_reader_report([self.chapter], self.report)

        self.assertTrue(receipt["valid"], receipt)
        self.assertEqual(
            hashlib.sha256(b"\xef\xbb\xbf" + payload).hexdigest(),
            receipt["report_sha256"],
        )

    def test_stop_fields_use_quote_and_reason_objects(self) -> None:
        report = valid_report()
        report["stopped_at"] = {"quote": "Mara checked the desk."}
        report["why_stopped"] = {"reason": "The opening did not make me curious."}
        self.write_report(report)

        receipt = validate_blind_reader_report([self.chapter], self.report)

        self.assertTrue(receipt["valid"], receipt)

    def test_cli_returns_json_receipt_and_nonzero_for_invalid_report(self) -> None:
        report = valid_report()
        report["flags"] = [{"flag": "wrong", "quote": "Mara checked the desk."}]
        self.write_report(report)

        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--chapter", str(self.chapter), "--report", str(self.report)],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertNotEqual(0, result.returncode)
        receipt = json.loads(result.stdout)
        self.assertFalse(receipt["valid"])
        self.assertEqual("invalid", receipt["status"])

    def test_multiple_assigned_chapters_are_checked_without_cross_boundary_quotes(self) -> None:
        second = self.root / "chapter-02.md"
        second.write_text("# Chapter Two\n\nLena found the key.\n", encoding="utf-8")
        report = valid_report()
        report["weakest_passage"]["quote"] = "Lena found the key."
        self.write_report(report)

        receipt = validate_blind_reader_report([self.chapter, second], self.report)

        self.assertTrue(receipt["valid"], receipt)


if __name__ == "__main__":
    unittest.main()
