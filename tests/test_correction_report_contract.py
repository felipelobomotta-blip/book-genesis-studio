"""Real controller decisions for ambiguous and negative correction reports."""
from contextlib import redirect_stdout
import copy
import io
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from autonomous_book import BookWorkflow
from workflow_state import Journal, WorkflowError, freeze, read_json
from test_autonomous_workflow import COMMAND, receipt_transport


class CorrectionReportContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        journal = Journal(self.root, {"model": "exact-test-model", "effort": "high"})
        self.accepted = self.root / "original/chapter-01.md"
        self.candidate = self.root / "candidate/chapter-01.md"
        freeze(self.accepted, b"# The key\n\nJonah Vale kept the key.\n")
        freeze(self.candidate, b"# The key\n\nJonah Mercer kept the key.\n")
        self.target = self.root / "manuscript/chapters/chapter-01.md"
        journal.publish(self.accepted, self.target)
        for name in ("00-brief.md", "03-characters.md", "07-outline.md", "09-continuity-ledger.md"):
            freeze(self.root / "artifacts" / name, b"Jonah Mercer is Elise's brother.\n")
        self.workflow = BookWorkflow.__new__(BookWorkflow)
        self.workflow.root = self.root
        self.workflow.command = COMMAND
        self.workflow.journal = journal
        self.report = {"verdict": "pass", "canon_supported": True, "factual_only": True,
            "dependencies_safe": True, "findings": [], "evidence": [
                {"passage_id": "accepted-p0002", "reason": "Wrong surname."},
                {"passage_id": "candidate-p0002", "reason": "Correct surname."},
                {"passage_id": "canon-1-p0001", "reason": "Established name."}]}
        self.decision = self.root / "decision.json"
        self.packets = []

    def configure(self, reports):
        def respond(_id, packet, _schema, _root):
            self.packets.append(packet)
            return reports[min(len(self.packets) - 1, len(reports) - 1)]
        self.workflow.transport = receipt_transport(respond)

    def run_check(self):
        with redirect_stdout(io.StringIO()):
            return self.workflow.check_factual_revision("revision-1-c01-facts",
                {"chapter": 1, "ticket": "Correct Jonah's surname against existing canon."},
                self.accepted, self.candidate, [], self.decision)

    def test_ambiguous_positive_summary_is_retained_and_fresh_valid_report_decides(self):
        ambiguous = copy.deepcopy(self.report)
        ambiguous["findings"] = ["Only quotation punctuation changed; no unresolved dependency remains."]
        self.configure([ambiguous, self.report])
        self.assertEqual("promote", self.run_check()["decision"])
        self.assertEqual(2, len(self.packets))
        self.assertEqual(self.packets[0], self.packets[1])  # No previous verdict sent to a critic.
        original = self.root / "work/host-calls/wf-revision-1-c01-facts-check-1/response"
        self.assertEqual(ambiguous, read_json(original))
        self.assertEqual("promote", self.run_check()["decision"])
        self.assertEqual(2, len(self.packets))  # Resume never resets the attempt budget.

    def test_coherent_block_is_final_without_rerating(self):
        report = copy.deepcopy(self.report)
        report.update(verdict="block", dependencies_safe=False, findings=["The key changes hands without a transfer."])
        self.configure([report, self.report])
        self.assertEqual("reject", self.run_check()["decision"])
        self.assertEqual(1, len(self.packets))
        self.assertEqual(self.accepted.read_bytes(), self.target.read_bytes())

    def test_two_malformed_reports_reject_candidate_without_destroying_accepted_chapter(self):
        report = copy.deepcopy(self.report)
        report["canon_supported"] = False  # A pass cannot contradict a failed check.
        self.configure([report])
        decision = self.run_check()
        self.assertEqual("reject", decision["decision"])
        self.assertIn("output-validation", decision["reason"])
        self.assertEqual(2, len(self.packets))
        self.assertEqual(self.accepted.read_bytes(), self.target.read_bytes())
        self.assertEqual(decision, self.run_check())
        self.assertEqual(2, len(self.packets))
        original = self.root / "work/host-calls/wf-revision-1-c01-facts-check-1/response"
        original.write_bytes(b"tampered")
        with self.assertRaisesRegex(WorkflowError, "evidence changed"):
            self.run_check()

    def test_missing_source_evidence_cannot_promote_a_correct_shaped_approval(self):
        report = copy.deepcopy(self.report)
        report["evidence"] = report["evidence"][:2]
        self.configure([report])
        self.assertEqual("reject", self.run_check()["decision"])
        self.assertEqual(2, len(self.packets))
        self.assertEqual(self.accepted.read_bytes(), self.target.read_bytes())

    def test_transport_failure_is_not_disguised_as_optional_rejection(self):
        def failed(*args):
            raise OSError("native transport unavailable")
        self.workflow.transport = failed
        with self.assertRaisesRegex(WorkflowError, "exhausted 2"):
            self.run_check()
        self.assertFalse(self.decision.exists())


if __name__ == "__main__":
    unittest.main()
