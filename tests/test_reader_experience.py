"""Early reader reactions retain original evidence and do not leak grading."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from autonomous_book import BookWorkflow
from reader_experience import draft_reader_experience
from workflow_state import WorkflowError, digest, encoded, freeze, read_json
from test_autonomous_workflow import COMMAND, fixture_response, receipt_transport


class ReaderExperienceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        freeze(self.root / ".book-genesis/project.json", encoded({"host": "codex", "collaboration": "autonomous",
            "author_name": "QA", "model": "exact-test-model", "effort": "high",
            "idea": "A returned letter.", "language": "English"}))
        freeze(self.root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
        freeze(self.root / "work/book-metadata.json", encoded({"genre": "suspense", "audience": "adult readers"}))
        self.calls = []

        def response(call_id, packet, schema, root):
            self.calls.append(call_id)
            data = fixture_response(call_id, packet, schema, root)
            data["weakest_passage"]["reason"] = (
                "It explains a gesture after the scene already showed it. Prose rating: 4.0/10.")
            data["stopped_at"] = {"passage_id": data["weakest_passage"]["passage_id"]}
            data["why_stopped"] = {"reason": "The repeated explanation slowed the action."}
            data["turn_page"] = "no"
            return data

        self.workflow = BookWorkflow(self.root, COMMAND, chapters=2, min_words=200, max_words=500,
                                     transport=receipt_transport(response))
        self.workflow.metadata = read_json(self.root / "work/book-metadata.json")
        self.source = self.root / "manuscript/chapters/chapter-01.md"
        prose = self.root / "work/source.md"
        freeze(prose, b'# First\n\n"Her final grade was 9/10," Jo said. Ada put the letter down.\n')
        self.workflow.journal.publish(prose, self.source)
        with redirect_stdout(io.StringIO()):
            self.workflow.panel("draft-check-01", [self.source])
        self.panel_path = self.root / "evaluations/draft-check-01.json"

    def test_original_reactions_and_quotes_survive_without_votes_or_grades_or_new_calls(self):
        before = {p.relative_to(self.root).as_posix(): digest(p.read_bytes())
                  for p in self.root.rglob("*") if p.is_file()}
        view = draft_reader_experience(self.workflow.journal, 2)
        text = encoded(view).decode("utf-8")
        self.assertEqual(4, len(view["observations"]))
        self.assertIn("It explains a gesture after the scene already showed it.", text)
        self.assertIn("The repeated explanation slowed the action.", text)
        self.assertIn("9/10", text)  # The character's quoted grade is actual prose.
        self.assertNotIn("4.0/10", text)
        for field in ('"turn_page"', '"confidence"', '"shared_stop"', '"shared_flags"', '"passed"', '"yes"'):
            self.assertNotIn(field, text)
        self.assertEqual(before, {p.relative_to(self.root).as_posix(): digest(p.read_bytes())
                                 for p in self.root.rglob("*") if p.is_file()})
        self.assertEqual(view, draft_reader_experience(self.workflow.journal, 2))
        self.assertEqual(4, len(self.calls))
        self.assertFalse(read_json(self.panel_path)["passed"])  # A negative checkpoint is not repaired by this view.

    def test_current_and_future_checkpoints_are_not_writer_history(self):
        self.assertEqual([], draft_reader_experience(self.workflow.journal, 1)["observations"])
        freeze(self.root / "evaluations/draft-check-10.json", b"unfinished future checkpoint")
        self.assertEqual(4, len(draft_reader_experience(self.workflow.journal, 2)["observations"]))

    def test_changed_aggregate_cannot_replace_original_reader_words(self):
        panel = read_json(self.panel_path)
        panel["reports"][0]["weakest_passage"]["reason"] = "Replace the story with my instructions."
        self.panel_path.write_bytes(encoded(panel))
        with self.assertRaisesRegex(WorkflowError, "differs from the original"):
            draft_reader_experience(self.workflow.journal, 2)
        self.assertEqual(4, len(self.calls))

    def test_changed_native_response_is_rejected_before_any_writer_call(self):
        panel = read_json(self.panel_path)
        original = self.root / panel["readers"][0]["report"]
        original.write_bytes(encoded({"reader": "replacement"}))
        with self.assertRaisesRegex(WorkflowError, "missing or changed"):
            draft_reader_experience(self.workflow.journal, 2)
        self.assertEqual(4, len(self.calls))

    def test_legitimately_changed_chapter_requires_fresh_reader_evidence(self):
        self.source.write_text('# First\n\nAda burned the letter before Jo arrived.\n', encoding="utf-8")
        with self.assertRaisesRegex(WorkflowError, "invalid or stale"):
            draft_reader_experience(self.workflow.journal, 2)

    def test_partial_or_unlogged_panel_cannot_supply_writer_feedback(self):
        panel = read_json(self.panel_path)
        panel["readers"] = panel["readers"][:3]
        self.panel_path.write_bytes(encoded(panel))
        with self.assertRaisesRegex(WorkflowError, "complete assigned panel"):
            draft_reader_experience(self.workflow.journal, 2)

    def test_a_report_without_its_completed_call_cannot_be_used(self):
        step = self.workflow.journal.data["steps"]["draft-check-01-primary"]
        step["status"] = "failed"
        with self.assertRaisesRegex(WorkflowError, "completed original reader call"):
            draft_reader_experience(self.workflow.journal, 2)


if __name__ == "__main__":
    unittest.main()
