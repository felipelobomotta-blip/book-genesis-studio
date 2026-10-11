"""A preferred revision must first resolve its assigned repair coherently."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from autonomous_book import BookWorkflow
from run_host_call import HostCallError
from workflow_state import WorkflowError, encoded, freeze, read_json, verify_execution
from test_autonomous_workflow import COMMAND, fixture_response, receipt_transport


class CreativeViabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        freeze(self.root / ".book-genesis/project.json", encoded({
            "host": "codex", "collaboration": "autonomous", "author_name": "QA",
            "model": "exact-test-model", "effort": "high", "idea": "A letter returns.", "language": "English",
            "autonomous_contract": {"chapters": 2, "min_words": 240, "max_words": 600, "quality_target": 8.5}}))
        freeze(self.root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
        self.calls = []
        self.mode = "pass"
        self.kwargs = dict(chapters=2, min_words=240, max_words=600,
                           transport=receipt_transport(self.generate))

    def workflow(self):
        return BookWorkflow(self.root, COMMAND, **self.kwargs)

    def generate(self, call_id, packet, schema, book):
        self.calls.append(call_id)
        result = fixture_response(call_id, packet, schema, book)
        if "-viability-" in call_id:
            catalog = json.loads(packet.split("Complete sources:\n", 1)[1])
            self.assertEqual(["accepted-chapter.md", "candidate-chapter.md", "current/chapter-02.md"],
                             [row["source"] for row in catalog["sources"][:3]])
            original = book / "work/snapshots/revision-1-c01-source-book/chapter-02.md"
            self.assertEqual(original.read_bytes().decode("utf-8").strip(),
                             "\n\n".join(row["text"] for row in catalog["sources"][2]["passages"]))
            self.assertNotIn("quality_target", packet)
            self.assertNotIn("calibrated", packet)
            if self.mode == "block":
                result["verdict"] = "block"
                result["checks"][0]["result"] = "block"
                result["findings"] = ["The revised scene still gives the courier information she has not learned."]
            elif self.mode == "invalid":
                # A supposedly positive report omits source evidence for the
                # old text. The host must not fill in those citations.
                for check in result["checks"]:
                    check["evidence_ids"] = check["evidence_ids"][1:]
        if "compare" in schema["properties"] and self.mode in {"tamper_report", "tamper_result"}:
            if self.mode == "tamper_report":
                target = book / "work/host-calls/wf-revision-1-c01-viability-1/response"
            else:
                target = book / "evaluations/decisions/revision-1-c01-viability.json"
            target.write_text("altered original repair check", encoding="utf-8")
        return result

    def test_unresolved_repair_never_reaches_preference_votes_or_replaces_accepted_prose(self):
        self.mode = "block"
        with redirect_stdout(io.StringIO()):
            workflow = self.workflow()
            self.assertEqual(0, workflow.run())
        self.assertEqual(3, len(workflow.journal.data["passes"]))
        self.assertFalse(any("-c01-primary" in key and "revision-" in key for key in self.calls))
        self.assertFalse(list((self.root / "evaluations/promotions").glob("*.json")))
        for number in (1, 2, 3):
            key = f"revision-{number}-c01-viability"
            self.assertEqual(1, len(workflow.journal.data["steps"][key]["attempts"]))
            report = read_json(self.root / f"evaluations/decisions/{key}.json")
            self.assertFalse(report["passed"])
            self.assertIn("has not learned", report["reason"])
        for chapter in (self.root / "manuscript/chapters").glob("*.md"):
            self.assertEqual(chapter.read_bytes(), (self.root / "work/snapshots/original-draft" / chapter.name).read_bytes())
        self.assertEqual(0, read_json(self.root / "evaluations/final-measurement.json")["number"])
        self.assertTrue(list((self.root / "delivery").glob("*.epub")))
        self.assertEqual("verified", verify_execution(self.root)["status"])

    def test_valid_repair_precedes_blind_comparison_and_completed_resume_makes_no_calls(self):
        with redirect_stdout(io.StringIO()):
            workflow = self.workflow()
            self.assertEqual(0, workflow.run())
        self.assertLess(self.calls.index("wf-revision-1-c01-viability-1"),
                        self.calls.index("wf-revision-1-c01-primary-1"))
        outcome = read_json(self.root / "evaluations/decisions/revision-1-c01-outcome.json")
        self.assertEqual("promote", outcome["decision"])
        self.assertIn("viability", outcome)
        before = list(self.calls)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, self.workflow().run())
        self.assertEqual(before, self.calls)
        self.assertEqual("verified", verify_execution(self.root)["status"])

    def test_missing_original_evidence_exhausts_bounded_checks_and_retains_the_draft(self):
        self.mode = "invalid"
        with redirect_stdout(io.StringIO()):
            workflow = self.workflow()
            self.assertEqual(0, workflow.run())
        for number in (1, 2, 3):
            step = workflow.journal.data["steps"][f"revision-{number}-c01-viability"]
            self.assertEqual("failed", step["status"])
            self.assertEqual(2, len(step["attempts"]))
            self.assertTrue(step["rejected_evidence"])
        self.assertFalse(list((self.root / "evaluations/promotions").glob("*.json")))
        self.assertEqual("verified", verify_execution(self.root)["status"])

    def test_authentication_failure_still_blocks_delivery(self):
        original = self.kwargs["transport"]
        def transport(root, call_id, packet, command):
            if "-viability-" in call_id:
                raise HostCallError("Native authentication unavailable", receipt={})
            return original(root, call_id, packet, command)
        self.kwargs["transport"] = transport
        with redirect_stdout(io.StringIO()), self.assertRaisesRegex(WorkflowError, "exhausted 2"):
            self.workflow().run()
        self.assertFalse(list((self.root / "delivery").glob("*.epub")))

    def test_changed_raw_report_or_decision_during_comparison_cannot_authorize_promotion(self):
        for mode in ("tamper_report", "tamper_result"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                original_root = self.root
                self.root = Path(temp)
                for relative in (".book-genesis/project.json", ".book-genesis/skills/.book-genesis-install.json"):
                    freeze(self.root / relative, (original_root / relative).read_bytes())
                self.mode = mode
                with redirect_stdout(io.StringIO()), self.assertRaisesRegex(WorkflowError, "Saved evidence is missing or changed"):
                    self.workflow().run()
                self.assertFalse(list((self.root / "evaluations/promotions").glob("*.json")))
                self.root = original_root

    def test_interruption_after_repair_check_resumes_without_repeating_its_review(self):
        with redirect_stdout(io.StringIO()):
            workflow = self.workflow()
            with patch.object(workflow, "compare_revision", side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
                workflow.run()
            before = self.calls.count("wf-revision-1-c01-viability-1")
            self.assertEqual(0, self.workflow().run())
        self.assertEqual(1, before)
        self.assertEqual(before, self.calls.count("wf-revision-1-c01-viability-1"))
        self.assertEqual("verified", verify_execution(self.root)["status"])

    def test_equivalent_reloaded_task_key_order_does_not_change_the_review_request(self):
        with redirect_stdout(io.StringIO()):
            workflow = self.workflow()
            with patch.object(workflow, "compare_revision", side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
                workflow.run()
            task = workflow.journal.data["strategies"][0]["tasks"][0]
            reloaded_task = {name: task[name] for name in reversed(tuple(task))}
            key = "revision-1-c01"
            before = list(self.calls)
            result = workflow.check_creative_viability(key, reloaded_task,
                self.root / f"work/revisions/{key}/chapter-01.md",
                self.root / f"work/attempts/{key}/stage/chapter.md",
                workflow.snapshot(key + "-source-book"))
        self.assertTrue(result["passed"])
        self.assertEqual(before, self.calls)


if __name__ == "__main__":
    unittest.main()
