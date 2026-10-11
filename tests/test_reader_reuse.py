"""Unchanged text keeps its first reader evidence, including negative readings."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from autonomous_book import BookWorkflow
from workflow_state import WorkflowError, encoded, freeze, read_json
from test_autonomous_workflow import COMMAND, fixture_response, receipt_transport


class ReaderReuseTests(unittest.TestCase):
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

        def generate(call_id, packet, schema, book):
            self.calls.append(call_id)
            data = fixture_response(call_id, packet, schema, book)
            if "turn_page" in data and "draft-check" in call_id:
                passage = schema["$defs"]["passageId"]["enum"][0]
                data.update(turn_page="no", stopped_at={"passage_id": passage},
                            why_stopped={"reason": "The opening does not create enough pressure."})
            return data

        self.kwargs = dict(chapters=2, min_words=240, max_words=600, transport=receipt_transport(generate))
        self.workflow = BookWorkflow(self.root, COMMAND, **self.kwargs)
        with redirect_stdout(io.StringIO()):
            self.workflow.planning()
            self.workflow.draft()
            self.workflow.initial_audit()

    def test_negative_reading_survives_new_snapshot_and_resume_without_another_vote(self):
        snapshot = self.workflow.snapshot("after-audit")
        before = len(self.calls)
        with redirect_stdout(io.StringIO()):
            panel = self.workflow.panel("new-scope", [snapshot[0]])
        self.assertEqual(before, len(self.calls))
        self.assertFalse(panel["passed"])
        self.assertEqual(0, panel["yes"])
        self.assertEqual(4, panel["reused_readings"])
        with redirect_stdout(io.StringIO()):
            resumed = BookWorkflow(self.root, COMMAND, **self.kwargs)
            resumed.planning()
            again = resumed.panel("new-scope", [snapshot[0]])
        self.assertEqual(panel, again)
        self.assertEqual(before, len(self.calls))

    def test_changed_prose_gets_new_reads_and_tampered_original_evidence_cannot_be_reused(self):
        snapshot = self.workflow.snapshot("after-audit")
        changed = self.root / "work/changed/chapter-01.md"
        freeze(changed, snapshot[0].read_bytes() + b"\n\nJo chose to keep the letter.\n")
        before = len(self.calls)
        with redirect_stdout(io.StringIO()):
            panel = self.workflow.panel("changed", [changed])
        self.assertEqual(before + 4, len(self.calls))
        self.assertTrue(panel["passed"])
        self.assertEqual(0, panel["reused_readings"])
        original_step = self.workflow.journal.data["steps"]["draft-check-01-primary"]
        (self.root / original_step["response"]).write_text('{"turn_page":"yes"}', encoding="utf-8")
        before = len(self.calls)
        with redirect_stdout(io.StringIO()), self.assertRaisesRegex(WorkflowError, "Saved evidence"):
            self.workflow.panel("original-again", [snapshot[0]])
        self.assertEqual(before, len(self.calls))

    def test_rubric_replicates_still_run_in_two_distinct_contexts(self):
        before = len(self.calls)
        with redirect_stdout(io.StringIO()):
            result = self.workflow.rubric("replicate-check", self.workflow.snapshot("rubric-copy"))
        self.assertEqual(before + 2, len(self.calls))
        self.assertEqual(2, len(result["readings"]))
        self.assertNotEqual(result["readings"][0]["report"], result["readings"][1]["report"])

    def test_reader_receives_only_previous_300_words_and_changed_context_gets_new_reads(self):
        snapshot = self.workflow.snapshot("context-original")
        previous = self.root / "work/context-original-copy/chapter-01.md"
        target = previous.with_name("chapter-02.md")
        body = "HIDDEN_EARLY_CONTEXT " + "ordinary word " * 200 + "The courier still holds the key."
        freeze(previous, ("# Previous\n\n" + body + "\n").encode())
        freeze(target, snapshot[1].read_bytes())
        before = len(self.calls)
        with redirect_stdout(io.StringIO()):
            first = self.workflow.panel("draft-check-context-c02", [target])
            same = self.workflow.panel("same-context-c02", [target])
        self.assertEqual(before + 4, len(self.calls))
        self.assertEqual(0, first["yes"])
        self.assertEqual(0, same["yes"])
        self.assertEqual(4, same["reused_readings"])
        packet = (self.root / "work/panels/draft-check-context-c02/primary.packet.md").read_text(encoding="utf-8")
        excerpt = packet.split("## Previous chapter context (not under review)\n\n", 1)[1].split("\n\n## Complete prose", 1)[0]
        self.assertEqual(" ".join(body.split()[-300:]), excerpt)
        self.assertEqual(300, len(excerpt.split()))
        self.assertNotIn("HIDDEN_EARLY_CONTEXT", packet)
        self.assertNotIn("FUTURE_ONLY_RESOLUTION", packet)
        self.assertNotIn("quality_target", packet)
        manifest = read_json(self.root / "work/panels/draft-check-context-c02/manifest.private.json")
        frozen_context = Path(manifest["context"]["path"])
        original_context = frozen_context.read_bytes()
        previous.write_text("# Previous\n\nThe courier gave the key to Jo.\n", encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            changed = self.workflow.panel("changed-context-c02", [target])
        self.assertEqual(before + 8, len(self.calls))
        self.assertEqual(0, changed["reused_readings"])
        self.assertEqual(original_context, frozen_context.read_bytes())
        self.workflow.journal.verify_files(first["evidence"])
        with self.assertRaisesRegex(WorkflowError, "Immutable evidence changed"):
            self.workflow.panel("draft-check-context-c02", [target])
        self.assertEqual(before + 8, len(self.calls))

    def test_missing_preceding_context_blocks_before_any_reader_dispatch(self):
        source = self.workflow.snapshot("for-missing-context")[1]
        target = self.root / "work/only-second/chapter-02.md"
        freeze(target, source.read_bytes())
        before = len(self.calls)
        with self.assertRaisesRegex(WorkflowError, "missing the preceding"):
            self.workflow.panel("missing-context", [target])
        self.assertEqual(before, len(self.calls))


if __name__ == "__main__":
    unittest.main()
