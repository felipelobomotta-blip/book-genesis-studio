"""Do not let model word-count guesses replace the measured production contract."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from autonomous_book import BookWorkflow
from workflow_roles import production_facts
from workflow_state import encoded, freeze, read_json
from test_autonomous_workflow import COMMAND, fixture_response, receipt_transport


class ProductionFactsTests(unittest.TestCase):
    def test_counts_use_export_rules_and_omit_private_quality_model_and_history_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            chapter = Path(tmp) / "chapter-01.md"
            chapter.write_text("# A long heading does not count\n\nOne two three.\n\n***\n\n<!-- hidden -->\n\nFour five.\n", encoding="utf-8")
            contract = {"chapters": 1, "min_words": 3, "max_words": 8,
                        "quality_target": 8.5, "weighted_quality_target": 9.0, "model": "private", "prior_score": 7}
            facts = production_facts([chapter], contract)
            self.assertEqual(5, facts["prose_word_count"]["total"])
            self.assertEqual([{"number": 1, "words": 5}], facts["prose_word_count"]["chapters"])
            self.assertEqual({"chapters": 1, "min_words": 3, "max_words": 8}, facts["fixed_contract"])
            self.assertNotIn("quality_target", json.dumps(facts))
            self.assertNotIn("prior_score", json.dumps(facts))
            self.assertNotIn("private", json.dumps(facts))
            chapter.write_text("# One\n\nNow only three.\n", encoding="utf-8")
            self.assertEqual(3, production_facts([chapter], contract)["prose_word_count"]["total"])

    def test_unequal_chapters_use_cumulative_export_counts_instead_of_chapter_fractions(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for number, words in enumerate((90, 7, 3), 1):
                path = Path(tmp) / f"chapter-{number:02d}.md"
                path.write_text(f"# Heading {number}\n\n" + "word " * words + "\n\n***\n\n<!-- invisible -->\n", encoding="utf-8")
                paths.append(path)
            contract = {"chapters": 3, "min_words": 90, "max_words": 110}
            facts = production_facts(list(reversed(paths)), contract)
            self.assertEqual([
                {"chapter": 1, "words_before": 0, "words_through": 90, "percentage_before": 0.0, "percentage_through": 90.0},
                {"chapter": 2, "words_before": 90, "words_through": 97, "percentage_before": 90.0, "percentage_through": 97.0},
                {"chapter": 3, "words_before": 97, "words_through": 100, "percentage_before": 97.0, "percentage_through": 100.0},
            ], facts["chapter_positions"])

    def test_observed_chapter_ten_cannot_contain_a_whole_book_position_of_96_percent(self):
        # Reproduce the measured native chapter-10 boundaries, with a synthetic
        # partition of the earlier total. This is arithmetic, not native prose.
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for number, words in enumerate([3726] + [3722] * 8 + [4049, 3530, 2659], 1):
                path = Path(tmp) / f"chapter-{number:02d}.md"
                path.write_text(f"# Chapter {number}\n\n" + "word " * words + "\n", encoding="utf-8")
                paths.append(path)
            facts = production_facts(paths, {"chapters": 12, "min_words": 40000, "max_words": 48000})
            tenth = facts["chapter_positions"][9]
            self.assertEqual(43740, facts["prose_word_count"]["total"])
            self.assertEqual((33502, 37551), (tenth["words_before"], tenth["words_through"]))
            self.assertEqual((76.594, 85.85), (tenth["percentage_before"], tenth["percentage_through"]))
            self.assertFalse(tenth["percentage_before"] <= 96 <= tenth["percentage_through"])

    def test_legitimate_edits_recompute_positions_without_mutating_source_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = [Path(tmp) / f"chapter-{n:02d}.md" for n in (1, 2)]
            paths[0].write_text("# One\n\nOne two three.\n", encoding="utf-8")
            paths[1].write_text("# Two\n\nFour five six.\n", encoding="utf-8")
            contract = {"chapters": 2, "min_words": 5, "max_words": 10}
            self.assertEqual(50.0, production_facts(paths, contract)["chapter_positions"][1]["percentage_before"])
            paths[0].write_text("# One\n\nOne two three four five six.\n", encoding="utf-8")
            before = [p.read_bytes() for p in paths]
            self.assertEqual(66.667, production_facts(paths, contract)["chapter_positions"][1]["percentage_before"])
            self.assertEqual(before, [p.read_bytes() for p in paths])

    def test_omitted_duplicate_or_unrelated_snapshot_files_cannot_supply_partial_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = [Path(tmp) / f"chapter-{n:02d}.md" for n in (1, 2)]
            for path in paths:
                path.write_text("# One\n\nA scene.\n", encoding="utf-8")
            contract = {"chapters": 2, "min_words": 3, "max_words": 8}
            for wrong in ([], paths[:1], paths + paths[:1]):
                with self.assertRaises(ValueError):
                    production_facts(wrong, contract)

    def test_audit_issue_followup_and_revision_plan_receive_current_counts_through_full_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze(root / ".book-genesis/project.json", encoded({"host": "codex", "collaboration": "autonomous",
                "author_name": "QA", "model": "exact-test-model", "effort": "high", "idea": "A letter returns.", "language": "English",
                "autonomous_contract": {"chapters": 2, "min_words": 240, "max_words": 600, "quality_target": 8.5}}))
            freeze(root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
            workflow = BookWorkflow(root, COMMAND, chapters=2, min_words=240, max_words=600,
                transport=receipt_transport(fixture_response))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, workflow.run())
            for key, marker in (("measure-0-audit", "Complete sources:\n"), ("issue-check-0", "Current complete sources:\n")):
                packet = (root / f"work/workflow/{key}/packet.md").read_text(encoding="utf-8")
                catalog = json.loads(packet.rsplit(marker, 1)[1])
                source = next(s for s in catalog["sources"] if s["source"] == "controller/production-counts.json")
                facts = json.loads("\n\n".join(p["text"] for p in source["passages"]))
                self.assertEqual({"chapters": 2, "min_words": 240, "max_words": 600}, facts["fixed_contract"])
                measured = production_facts(list((root / "work/snapshots/measure-0").glob("chapter-*.md")), workflow.contract)
                self.assertEqual(measured, facts)
                self.assertNotIn("quality_target", packet)
            revision = (root / "work/workflow/revision-plan-1/packet.md").read_text(encoding="utf-8")
            self.assertIn("controller/production-counts.json", revision)
            rubric = (root / "work/workflow/measure-0-rubric-1/packet.md").read_text(encoding="utf-8")
            locations = json.loads(rubric.split("Measured chapter locations:\n", 1)[1].split("\nAn event lies", 1)[0])
            self.assertEqual(measured["prose_word_count"]["total"], locations["whole_book_prose_words"])
            self.assertEqual(measured["chapter_positions"], locations["chapter_positions"])
            self.assertNotIn("fixed_contract", locations)
            self.assertNotIn("quality_target", rubric)
            self.assertEqual(8, workflow.journal.data["phase"])
            self.assertTrue((root / "delivery/export-receipt.json").is_file())


if __name__ == "__main__":
    unittest.main()
