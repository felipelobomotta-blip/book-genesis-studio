"""A malformed optional plan must not strand a complete reviewed manuscript."""
from contextlib import redirect_stdout
import io
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


class RevisionPlanRecoveryTests(unittest.TestCase):
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
        self.kwargs = dict(chapters=2, min_words=240, max_words=600,
                           transport=receipt_transport(self.generate))

    def generate(self, call_id, packet, schema, book):
        self.calls.append(call_id)
        response = fixture_response(call_id, packet, schema, book)
        if "strategy" in schema["properties"]:
            # Real failure class: well-formed JSON silently omits mandatory
            # historical findings, so it cannot authorize a revision.
            response["tasks"] = []
        return response

    def workflow(self):
        return BookWorkflow(self.root, COMMAND, **self.kwargs)

    def test_invalid_plans_export_current_draft_without_rerating_or_hiding_failure(self):
        with redirect_stdout(io.StringIO()):
            workflow = self.workflow()
            self.assertEqual(0, workflow.run())
        step = workflow.journal.data["steps"]["revision-plan-1"]
        self.assertEqual("failed", step["status"])
        self.assertEqual(2, len(step["attempts"]))
        self.assertEqual(1, len(workflow.journal.data["passes"]))
        self.assertIn("omits unresolved required issues", step["attempts"][1]["error"])
        self.assertTrue(step["rejected_evidence"])
        final = read_json(self.root / "evaluations/final-measurement.json")
        self.assertEqual(0, final["number"])
        self.assertFalse(final["passed"])
        self.assertTrue(final["issue_ledger"]["open"])
        self.assertFalse(any("measure-1" in call or "revision-1-c" in call for call in self.calls))
        self.assertTrue(list((self.root / "delivery").glob("*.epub")))
        for path in (self.root / "manuscript/chapters").glob("*.md"):
            self.assertEqual(path.read_bytes(), (self.root / "work/snapshots/original-draft" / path.name).read_bytes())
        self.assertIn("unapproved draft", (self.root / "artifacts/11-genesis-score.md").read_text(encoding="utf-8"))
        verify_execution(self.root)
        before = list(self.calls)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, self.workflow().run())
        self.assertEqual(before, self.calls)
        (self.root / "work/host-calls/wf-revision-plan-1-1/response").write_text("changed")
        with self.assertRaises(WorkflowError):
            verify_execution(self.root)

    def test_interrupted_draft_delivery_resumes_without_a_new_plan_or_measurement(self):
        workflow = self.workflow()
        finish = workflow.finish
        def interrupt(phase, *args, **kwargs):
            if phase == 5:
                raise KeyboardInterrupt()
            return finish(phase, *args, **kwargs)
        with patch.object(workflow, "finish", side_effect=interrupt), redirect_stdout(io.StringIO()):
            with self.assertRaises(KeyboardInterrupt):
                workflow.run()
        old_calls = list(self.calls)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, self.workflow().run())
        new_calls = self.calls[len(old_calls):]
        self.assertTrue(new_calls)  # The unfinished editorial package still runs.
        self.assertFalse(any("revision" in call or "measure" in call for call in new_calls))
        self.assertEqual(1, len(read_json(self.root / ".book-genesis/workflow.json")["passes"]))
        verify_execution(self.root)

    def test_transport_failure_is_not_relabelled_an_invalid_plan(self):
        original_transport = self.kwargs["transport"]
        def transport(root, call_id, packet, command):
            if "revision-plan" in call_id:
                raise HostCallError("Native authentication unavailable", receipt={})
            return original_transport(root, call_id, packet, command)
        self.kwargs["transport"] = transport
        with redirect_stdout(io.StringIO()), self.assertRaisesRegex(WorkflowError, "exhausted 2"):
            self.workflow().run()
        journal = read_json(self.root / ".book-genesis/workflow.json")
        self.assertEqual("blocked", journal["status"])
        self.assertNotIn("rejected_evidence", journal["steps"]["revision-plan-1"])
        self.assertFalse(list((self.root / "delivery").glob("*.epub")))

    def test_valid_revision_report_survives_interrupted_phase_finish(self):
        def generate(call_id, packet, schema, book):
            self.calls.append(call_id)
            return fixture_response(call_id, packet, schema, book)
        self.kwargs["transport"] = receipt_transport(generate)
        workflow = self.workflow()
        finish = workflow.finish
        def interrupt(phase, *args, **kwargs):
            if phase == 5:
                raise KeyboardInterrupt()
            return finish(phase, *args, **kwargs)
        with patch.object(workflow, "finish", side_effect=interrupt), redirect_stdout(io.StringIO()):
            with self.assertRaises(KeyboardInterrupt):
                workflow.run()
        reports = {name: (self.root / "evaluations" / name).read_bytes()
                   for name in ("revision-loop.md", "revision-plan.md", "proofread.md")}
        before = list(self.calls)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, self.workflow().run())
        self.assertFalse(any("revision" in call or "measure" in call for call in self.calls[len(before):]))
        for name, data in reports.items():
            self.assertEqual(data, (self.root / "evaluations" / name).read_bytes())
        verify_execution(self.root)

    def test_changed_original_failure_blocks_the_fallback(self):
        def generate(call_id, packet, schema, book):
            result = self.generate(call_id, packet, schema, book)
            if call_id == "wf-revision-plan-1-2":
                (book / "work/host-calls/wf-revision-plan-1-1/response").write_text("changed")
            return result
        self.kwargs["transport"] = receipt_transport(generate)
        with redirect_stdout(io.StringIO()), self.assertRaisesRegex(WorkflowError, "Rejected revision evidence changed"):
            self.workflow().run()
        self.assertFalse(list((self.root / "delivery").glob("*.epub")))


if __name__ == "__main__":
    unittest.main()
