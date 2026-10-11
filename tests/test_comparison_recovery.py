"""An optional invalid comparison must reject the candidate, not strand a book."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from autonomous_book import BookWorkflow
from run_host_call import HostCallError
from workflow_state import WorkflowError, encoded, freeze, read_json, verify_execution
from test_autonomous_workflow import COMMAND, fixture_response, receipt_transport


class ComparisonRecoveryTests(unittest.TestCase):
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
        result = fixture_response(call_id, packet, schema, book)
        if "compare" in schema["properties"]:
            key = call_id.removeprefix("wf-").rsplit("-", 2)[0]
            manifest = read_json(book / "work/comparisons" / key / "manifest.private.json")
            row = next(r for r in manifest["readers"] if r["reader"] == result["reader"])
            result["compare"] = next(label for label, identity in row["mapping"].items() if identity == "candidate")
            if result["reader"] == "Airport reader":
                # Actual native failure: valid IDs and a vote, but no binding
                # metadata. Even three valid positive votes cannot fill this in.
                result.pop("schema_version")
                result.pop("catalog_sha256")
        return result

    def workflow(self):
        return BookWorkflow(self.root, COMMAND, **self.kwargs)

    def test_two_invalid_comparisons_preserve_book_and_deliver_without_inventing_fourth_vote(self):
        with redirect_stdout(io.StringIO()):
            workflow = self.workflow()
            self.assertEqual(0, workflow.run())
        self.assertEqual(3, len(workflow.journal.data["passes"]))
        for number in (1, 2, 3):
            key = f"revision-{number}-c01-casual"
            step = workflow.journal.data["steps"][key]
            self.assertEqual("failed", step["status"])
            self.assertEqual(2, len(step["attempts"]))
            self.assertTrue(step["rejected_evidence"])
            decision = read_json(self.root / f"evaluations/decisions/revision-{number}-c01.json")
            self.assertEqual("reject", decision["decision"])
            self.assertNotIn("revision_votes", decision)
            self.assertEqual("Airport reader", decision["unverified_reader"])
        self.assertFalse(list((self.root / "evaluations/promotions").glob("*.json")))
        for path in (self.root / "manuscript/chapters").glob("*.md"):
            self.assertEqual(path.read_bytes(), (self.root / "work/snapshots/original-draft" / path.name).read_bytes())
        self.assertTrue(list((self.root / "delivery").glob("*.epub")))
        final = read_json(self.root / "evaluations/final-measurement.json")
        self.assertEqual(0, final["number"])
        self.assertFalse(final["passed"])
        self.assertFalse(any("measure-1" in call for call in self.calls))
        self.assertEqual("verified", verify_execution(self.root)["status"])
        before = list(self.calls)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, self.workflow().run())
        self.assertEqual(before, self.calls)
        original = self.root / "work/host-calls/wf-revision-1-c01-casual-1/response"
        self.assertNotIn("schema_version", read_json(original))
        original.write_text("changed")
        with self.assertRaises(WorkflowError):
            verify_execution(self.root)

    def test_native_authentication_failure_is_not_an_optional_comparison_rejection(self):
        original_transport = self.kwargs["transport"]
        def transport(root, call_id, packet, command):
            if "revision-1-c01-casual" in call_id:
                raise HostCallError("Native authentication unavailable", receipt={})
            return original_transport(root, call_id, packet, command)
        self.kwargs["transport"] = transport
        with redirect_stdout(io.StringIO()), self.assertRaisesRegex(WorkflowError, "exhausted 2"):
            self.workflow().run()
        self.assertFalse(list((self.root / "delivery").glob("*.epub")))
        self.assertFalse((self.root / "evaluations/decisions/revision-1-c01.json").exists())

    def test_tampered_first_failed_response_blocks_recovery(self):
        def generate(call_id, packet, schema, book):
            result = self.generate(call_id, packet, schema, book)
            if call_id == "wf-revision-1-c01-casual-2":
                (book / "work/host-calls/wf-revision-1-c01-casual-1/response").write_text("changed")
            return result
        self.kwargs["transport"] = receipt_transport(generate)
        with redirect_stdout(io.StringIO()), self.assertRaisesRegex(WorkflowError, "Rejected revision evidence changed"):
            self.workflow().run()
        self.assertFalse(list((self.root / "delivery").glob("*.epub")))


if __name__ == "__main__":
    unittest.main()
