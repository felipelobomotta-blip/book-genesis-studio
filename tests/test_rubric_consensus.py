"""Three fresh rubric judgments, genuine medians and retained negative evidence."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from autonomous_book import BookWorkflow
from workflow_state import encoded, freeze
from test_autonomous_workflow import COMMAND, fixture_response, receipt_transport


class RubricConsensusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        freeze(self.root / ".book-genesis/project.json", encoded({
            "host": "codex", "collaboration": "autonomous", "author_name": "QA",
            "model": "exact-test-model", "effort": "high", "idea": "A letter returns.",
            "language": "English"}))
        freeze(self.root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
        freeze(self.root / "artifacts/01-market-map.md", b"Unverified positioning.")
        self.snapshot = [self.root / f"snapshot/chapter-{n:02d}.md" for n in (1, 2)]
        for path in self.snapshot:
            freeze(path, b"# A letter\n\nAda chose to confess.\n\nJo opened the door.\n")

    def workflow(self, scores, *, unassessed_third=False):
        calls = []

        def generate(call_id, packet, schema, book):
            calls.append((call_id, packet))
            report = fixture_response(call_id, packet, schema, book)
            for dimension in report["dimensions"]:
                dimension["score"] = scores[len(calls) - 1]
            if unassessed_third and len(calls) == 3:
                report["dimensions"][0].update(score=None, evidence=[],
                    reason="The supplied prose does not support this assessment.")
            return report

        with redirect_stdout(io.StringIO()):
            workflow = BookWorkflow(self.root, COMMAND, chapters=2, min_words=240,
                max_words=600, weighted_quality_target=9.0,
                transport=receipt_transport(generate))
        return workflow, calls

    def read(self, workflow):
        with redirect_stdout(io.StringIO()):
            return workflow.rubric("consensus-rubric", self.snapshot)

    def test_three_original_judgments_use_median_and_retain_strict_reading(self):
        workflow, calls = self.workflow([9.8, 9.4, 6.0])
        report = self.read(workflow)
        self.assertEqual(3, len(calls))
        self.assertEqual(3, len({call_id for call_id, _ in calls}))
        self.assertEqual(1, len({packet for _, packet in calls}))
        self.assertEqual([9.8, 9.4, 6.0], [r["data"]["dimensions"][0]["score"]
                                        for r in report["readings"]])
        self.assertEqual(3, len({r["report"] for r in report["readings"]}))
        self.assertTrue(all(r["validation"]["valid"] for r in report["readings"]))
        self.assertTrue(all(d["raw_median"] == 9.4 for d in report["dimensions"]))
        self.assertEqual(8.6, report["floor"])
        self.assertEqual(8.6, report["weighted"])
        self.assertEqual("low", report["confidence"])
        self.assertFalse(report["passed"])
        for _, packet in calls:
            self.assertNotIn("quality_target", packet)
            self.assertNotIn("consensus-rubric", packet)
            self.assertNotIn("earlier scores", packet.lower())

    def test_exact_90_is_not_above_90(self):
        workflow, _ = self.workflow([9.8, 9.8, 9.8])
        report = self.read(workflow)
        self.assertEqual(9.0, report["weighted"])
        self.assertFalse(report["passed"])

    def test_one_unassessed_replica_cannot_be_hidden_by_two_high_scores(self):
        workflow, calls = self.workflow([9.9, 9.9, 9.9], unassessed_third=True)
        report = self.read(workflow)
        self.assertEqual(3, len(calls))
        self.assertIsNone(report["floor"])
        self.assertIsNone(report["weighted"])
        self.assertIn("Originality", report["unassessed"])
        self.assertFalse(report["passed"])
        self.assertIsNone(report["readings"][2]["data"]["dimensions"][0]["score"])

    def test_replay_preserves_each_original_replica_without_new_calls(self):
        workflow, calls = self.workflow([9.8, 9.4, 6.0])
        original = self.read(workflow)
        raw = {r["report"]: (self.root / r["report"]).read_bytes()
               for r in original["readings"]}
        replay = self.read(workflow)
        self.assertEqual(3, len(calls))
        self.assertEqual(original, replay)
        self.assertEqual(raw, {name: (self.root / name).read_bytes() for name in raw})


if __name__ == "__main__":
    unittest.main()
