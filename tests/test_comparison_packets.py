"""Regression checks for anonymous order and assigned reader identity."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "skills/book-genesis/scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from build_comparison import ComparisonPacketError, READERS, build_comparison  # noqa: E402
from validate_blind_reader import validate_blind_reader_report  # noqa: E402


class ComparisonPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix=".test-comparison-", dir=REPO_ROOT))
        self.accepted = self.root / "accepted-chapter.md"
        self.candidate = self.root / "revision-r2.md"
        self.accepted.write_text(
            "# Accepted chapter\n\n<!-- quality target 8.5 -->\nMara checked the desk.\n\nThe room held its breath.\n",
            encoding="utf-8",
        )
        self.candidate.write_text(
            "# Candidate revision\n\n<!-- calibrated score 9 -->\nMara opened the drawer.\n\nA key struck the floor.\n",
            encoding="utf-8",
        )
        self.bundle = self.root / "bundle"

    def tearDown(self) -> None:
        if self.root.parent != REPO_ROOT or not self.root.name.startswith(".test-comparison-"):
            raise RuntimeError("Refusing cleanup outside the owned comparison fixture")
        shutil.rmtree(self.root)

    def report(self, reader: str) -> Path:
        path = self.root / "raw.json"
        path.write_text(json.dumps({
            "reader": reader, "turn_page": "no", "stopped_at": None,
            "why_stopped": None, "remember_tomorrow": [], "confused_by": [],
            "flags": [],
            "strongest_passage": {"quote": "Mara checked the desk.", "reason": "A physical action."},
            "weakest_passage": {"quote": "The room held its breath.", "reason": "A familiar image."},
            "machine_tells": [], "felt": {"emotion": "unmoved", "reason": "Little pressure."},
            "confidence": "medium", "compare": "same",
        }), encoding="utf-8")
        return path

    def test_readers_get_full_anonymous_prose_in_balanced_order_without_metadata(self) -> None:
        before = {p: p.read_bytes() for p in (self.accepted, self.candidate)}
        manifest = build_comparison(self.accepted, self.candidate, self.bundle)
        self.assertEqual({"Lena", "Mark", "Priya", "Airport reader"}, {r["reader"] for r in manifest["readers"]})
        self.assertEqual(2, sum(r["mapping"]["A"] == "candidate" for r in manifest["readers"]))
        self.assertEqual(4, len({r["persona"] for r in manifest["readers"]}))
        for row in manifest["readers"]:
            packet = (self.bundle / row["packet"]).read_text(encoding="utf-8")
            for forbidden in (str(self.accepted), str(self.candidate), "# Accepted chapter", "# Candidate revision", "quality target 8.5", "calibrated score 9", "A is the currently accepted", "B is a candidate"):
                self.assertNotIn(forbidden, packet)
            self.assertIn("Mara checked the desk.", packet)
            self.assertIn("A key struck the floor.", packet)
            self.assertEqual(row["packet_sha256"], hashlib.sha256((self.bundle / row["packet"]).read_bytes()).hexdigest())
            a_body = packet.split("## Draft A\n\n", 1)[1].split("## Draft B\n\n", 1)[0]
            expected = "Mara opened the drawer." if row["mapping"]["A"] == "candidate" else "Mara checked the desk."
            self.assertIn(expected, a_body)
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertTrue((self.bundle / "manifest.private.json").is_file())

    def test_schema_binds_each_identity_and_keeps_exact_quote_field_shapes(self) -> None:
        manifest = build_comparison(self.accepted, self.candidate, self.bundle)
        for row in manifest["readers"]:
            schema = json.loads((self.bundle / row["response_schema"]).read_text())
            fields = schema["properties"]
            self.assertEqual([row["reader"]], fields["reader"]["enum"])
            self.assertEqual({"quote"}, set(fields["stopped_at"]["anyOf"][0]["properties"]))
            self.assertEqual({"reason"}, set(fields["why_stopped"]["anyOf"][0]["properties"]))
            self.assertEqual({"quote", "reason"}, set(fields["strongest_passage"]["properties"]))
            self.assertEqual({"quote", "reason"}, set(fields["remember_tomorrow"]["items"]["properties"]))
            self.assertEqual(set(fields), set(schema["required"]))
            self.assertFalse(schema["additionalProperties"])

    def test_a_second_build_never_overwrites_a_frozen_bundle(self) -> None:
        build_comparison(self.accepted, self.candidate, self.bundle)
        before = {p: p.read_bytes() for p in self.bundle.iterdir()}
        with self.assertRaises(FileExistsError):
            build_comparison(self.accepted, self.candidate, self.bundle)
        self.assertEqual(before, {p: p.read_bytes() for p in self.bundle.iterdir()})

    def test_invalid_inputs_fail_before_creating_any_reader_packet(self) -> None:
        for index, data in enumerate((b"### Chapter\n\nProse.", b"# Heading\n\n<!-- empty -->", b"# Heading\n\n<!-- unclosed", b"# Heading\n\n\xff", b"# One\n\nText.\n\n# Two\n\nText.")):
            with self.subTest(index=index):
                invalid = self.root / f"invalid-{index}.md"
                invalid.write_bytes(data)
                output = self.root / f"bundle-{index}"
                with self.assertRaises((ComparisonPacketError, UnicodeError)):
                    build_comparison(self.accepted, invalid, output)
                self.assertFalse(output.exists())

    def test_repeated_source_or_context_is_not_a_comparison(self) -> None:
        with self.assertRaises(ComparisonPacketError):
            build_comparison(self.accepted, self.accepted, self.bundle)
        with self.assertRaises(ComparisonPacketError):
            build_comparison(self.accepted, self.candidate, self.bundle, [self.accepted])
        self.assertFalse(self.bundle.exists())

    def test_wrong_reader_is_invalid_without_renaming_or_mutating_raw_json(self) -> None:
        report = self.report("Lena")
        before = report.read_bytes()
        receipt = validate_blind_reader_report([self.accepted], report, expected_reader="Priya")
        self.assertFalse(receipt["valid"])
        self.assertTrue(any("assigned reader" in error for error in receipt["errors"]))
        self.assertEqual(before, report.read_bytes())

    def test_negative_vote_from_the_assigned_reader_is_valid(self) -> None:
        report = self.report("Priya")
        receipt = validate_blind_reader_report([self.accepted], report, expected_reader="Priya")
        self.assertTrue(receipt["valid"], receipt)
        self.assertEqual("Priya", receipt["expected_reader"])
        self.assertEqual("no", json.loads(report.read_text())["turn_page"])

    def test_expected_identity_does_not_waive_fabricated_quote_or_bad_assignment(self) -> None:
        report = self.report("Priya")
        payload = json.loads(report.read_text())
        payload["strongest_passage"]["quote"] = "A sentence that does not exist."
        report.write_text(json.dumps(payload), encoding="utf-8")
        self.assertFalse(validate_blind_reader_report([self.accepted], report, expected_reader="Priya")["valid"])
        self.assertFalse(validate_blind_reader_report([self.accepted], report, expected_reader=" ")["valid"])


if __name__ == "__main__":
    unittest.main()
