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
            self.assertEqual(8, workflow.journal.data["phase"])
            self.assertTrue((root / "delivery/export-receipt.json").is_file())


if __name__ == "__main__":
    unittest.main()
