"""Packet/evidence regressions, not evidence of literary quality."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from prepare_readers import prepare_readers
from prepare_rubric import build_catalog, catalog_digest
from validate_blind_reader import validate_blind_reader_report


class ReaderPassageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.chapter = self.root / "chapter-02.md"
        self.chapter.write_text("# Chapter two\n\nMara kept the key.\n\nShe left alone.\n", encoding="utf-8")
        self.catalog = build_catalog([self.chapter])
        self.catalog_path = self.root / "catalog.json"
        self.save_catalog()
        self.report_path = self.root / "raw.json"
        self.report = {
            "schema_version": 2, "catalog_sha256": catalog_digest(self.catalog),
            "reader": "Lena", "turn_page": "no", "confidence": "low",
            "stopped_at": {"passage_id": "c02p0002"}, "why_stopped": {"reason": "An abrupt departure."},
            "remember_tomorrow": [{"passage_id": "c02p0001", "reason": "The retained key."}],
            "confused_by": [{"passage_id": "c02p0002", "reason": "Her destination is unclear."}],
            "flags": [{"flag": "confusing", "passage_id": "c02p0002"}],
            "strongest_passage": {"passage_id": "c02p0001", "reason": "A physical choice."},
            "weakest_passage": {"passage_id": "c02p0002", "reason": "No consequence."},
            "machine_tells": [{"tell": "abrupt summary", "passage_id": "c02p0002"}],
            "felt": {"emotion": "nothing", "reason": "The departure has no setup."},
        }

    def save_catalog(self):
        self.catalog_path.write_text(json.dumps(self.catalog), encoding="utf-8")

    def validate(self, **kwargs):
        self.report_path.write_text(json.dumps(self.report), encoding="utf-8")
        return validate_blind_reader_report([self.chapter], self.report_path,
                                            expected_reader="Lena", catalog_path=self.catalog_path, **kwargs)

    def test_unfavorable_report_resolves_every_evidence_field_without_repair(self):
        receipt = self.validate()
        self.assertTrue(receipt["valid"], receipt)
        self.assertEqual(7, len(receipt["resolved_evidence"]))
        self.assertEqual("She left alone.", receipt["resolved_evidence"][0]["quote"])
        self.assertEqual(catalog_digest(self.catalog), receipt["catalog_sha256"])
        self.assertEqual(self.report, json.loads(self.report_path.read_text(encoding="utf-8")))
        self.assertEqual(hashlib.sha256(self.report_path.read_bytes()).hexdigest(), receipt["report_sha256"])

    def test_unknown_id_wrong_digest_and_mixed_quote_shapes_fail(self):
        original = copy.deepcopy(self.report)
        for change in (lambda r: r["strongest_passage"].update(passage_id="c02p9999"),
                       lambda r: r.update(catalog_sha256="f" * 64),
                       lambda r: r["strongest_passage"].update(quote="Mara kept the key."),
                       lambda r: r.update(schema_version=True),
                       lambda r: r.update(compare="A"),
                       lambda r: r.update(reader="Priya")):
            with self.subTest(change=change):
                self.report = copy.deepcopy(original)
                change(self.report)
                self.assertFalse(self.validate()["valid"])

    def test_changed_current_prose_and_old_report_with_new_catalog_fail(self):
        self.chapter.write_text(self.chapter.read_text(encoding="utf-8") + "\nThe door opened.\n", encoding="utf-8")
        self.assertFalse(self.validate()["valid"])
        self.catalog = build_catalog([self.chapter])
        self.save_catalog()
        self.assertFalse(self.validate()["valid"])

    def test_omitted_or_reordered_catalog_paragraphs_fail_even_with_recomputed_digest(self):
        original = copy.deepcopy(self.catalog)
        for kind in ("omit", "reverse", "invent"):
            with self.subTest(kind=kind):
                self.catalog = copy.deepcopy(original)
                passages = self.catalog["chapters"][0]["passages"]
                if kind == "omit":
                    passages.pop()
                elif kind == "reverse":
                    passages.reverse()
                else:
                    passages[0]["text"] = "This never happened."
                self.save_catalog()
                self.report["catalog_sha256"] = catalog_digest(self.catalog)
                self.assertFalse(self.validate()["valid"])

    def test_missing_catalog_and_nonstandard_json_fail(self):
        self.validate()
        self.assertFalse(validate_blind_reader_report([self.chapter], self.report_path)["valid"])
        for extra in ('"reader":"Lena",', '"other":NaN,'):
            self.report_path.write_text("{" + extra + json.dumps(self.report)[1:], encoding="utf-8")
            receipt = validate_blind_reader_report([self.chapter], self.report_path, catalog_path=self.catalog_path)
            self.assertFalse(receipt["valid"], receipt)

    def test_existing_structure_and_enum_rules_remain_enforced(self):
        original = copy.deepcopy(self.report)
        for field, value in (("turn_page", "absolutely"), ("flags", [{"flag": "made_up", "passage_id": "c02p0001"}]),
                             ("why_stopped", None), ("felt", {"emotion": "fine"}), ("confused_by", {})):
            with self.subTest(field=field):
                self.report = copy.deepcopy(original)
                self.report[field] = value
                self.assertFalse(self.validate()["valid"])

    def test_packets_include_complete_prose_and_structured_ids_with_no_private_paths(self):
        previous = self.root / "chapter-01.md"
        previous.write_text("# Earlier\n\nShe found the key.\n", encoding="utf-8")
        before = self.chapter.read_bytes()
        out = self.root / "packets"
        manifest = prepare_readers([self.chapter], out, audience="Literary fiction for adult readers", context_chapter=previous)
        self.assertEqual({"primary", "hostile", "adjacent", "casual"}, {r["persona"] for r in manifest["readers"]})
        for row in manifest["readers"]:
            packet = (out / row["packet"]).read_text(encoding="utf-8")
            schema = json.loads((out / row["response_schema"]).read_text())
            self.assertIn("Mara kept the key.", packet)
            self.assertIn("She left alone.", packet)
            self.assertIn("She found the key.", packet)
            self.assertNotIn(str(self.root), packet)
            self.assertNotIn("compare", schema["properties"])
            self.assertEqual([2], schema["properties"]["schema_version"]["enum"])
            citation = schema["properties"]["strongest_passage"]["properties"]["passage_id"]
            self.assertEqual(["c02p0001", "c02p0002"], citation["enum"])
        self.assertEqual(before, self.chapter.read_bytes())
        with self.assertRaises(FileExistsError):
            prepare_readers([self.chapter], out, audience="Adult fiction")

    def test_cli_returns_passed_receipt_for_unfavorable_reader(self):
        self.validate()
        run = subprocess.run([sys.executable, str(ROOT / "skills/book-genesis/scripts/validate_blind_reader.py"),
                              "--chapter", str(self.chapter), "--report", str(self.report_path),
                              "--catalog", str(self.catalog_path), "--expected-reader", "Lena"],
                             capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(0, run.returncode, run.stderr)
        self.assertTrue(json.loads(run.stdout)["valid"])
