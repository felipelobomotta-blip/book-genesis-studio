"""Focused tests for the read-only schema-6 progress reconciler."""

from pathlib import Path
import json
import shutil
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "skills" / "book-genesis" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from check_progress import parse_project_state, reconcile_book  # noqa: E402
from export_book import count_prose_words, discover_chapters  # noqa: E402


def _state(
    *,
    phase: str = "Phase 3: Drafting",
    completed: str = "[1]",
    words: int = 3,
    planned: int = 1,
    pipeline_status: str = "in_progress",
    manuscript_status: str = "in_progress",
    gates: str | None = None,
) -> str:
    gates = gates or """  intake: "passed"
  foundation: "passed"
  architecture: "passed"
  drafting: "in_progress"
  adversarial_audit: "pending"
  revision_loop: "pending"
  final_score: "pending"
  editorial_package: pending"""
    return f'''schema_version: 6

pipeline:
  current_phase: "{phase}"
  status: "{pipeline_status}"

manuscript:
  chapter_count_planned: {planned}
  completed_chapters: {completed}
  word_count_actual: {words}
  status: "{manuscript_status}"

gates:
{gates}
'''


class ProgressTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="book-genesis-progress-"))
        self.chapters = self.root / "manuscript" / "chapters"
        self.chapters.mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def write_chapter(self, number: int = 1, body: str = "One two three.") -> None:
        (self.chapters / f"chapter-{number:02d}.md").write_text(
            f"# Chapter {number}\n\n{body}\n", encoding="utf-8"
        )

    def write_state(self, text: str) -> None:
        (self.root / "PROJECT_STATE.yaml").write_text(text, encoding="utf-8")

    def test_empty_book_is_a_truthful_resume_state(self) -> None:
        report = reconcile_book(self.root)
        self.assertTrue(report["ok"])
        self.assertEqual("empty", report["status"])
        self.assertEqual([], report["canonical"]["chapter_numbers"])

    def test_stale_chapters_and_words_are_reported_with_recovery(self) -> None:
        self.write_chapter()
        self.write_state(_state(phase="Phase 1: Foundation", completed="[]", words=0))
        report = reconcile_book(self.root)
        self.assertFalse(report["ok"])
        fields = {item["field"] for item in report["mismatches"]}
        self.assertIn("manuscript.completed_chapters", fields)
        self.assertIn("manuscript.word_count_actual", fields)
        self.assertEqual("whitespace_split_prose_v1", report["canonical"]["word_count_method"])
        self.assertTrue(report["recovery_steps"])

    def test_block_list_chapters_are_supported(self) -> None:
        self.write_chapter()
        text = _state().replace("completed_chapters: [1]", "completed_chapters:\n    - 1")
        self.write_state(text)
        parsed = parse_project_state(self.root / "PROJECT_STATE.yaml")
        self.assertEqual([1], parsed["manuscript"]["completed_chapters"])
        self.assertTrue(reconcile_book(self.root)["ok"])

    def test_documented_decision_and_question_lists_do_not_break_reconciliation(self) -> None:
        self.write_chapter()
        self.write_state(_state() + """
decisions:
  - id: D-01
    phase: "Phase 0: Intake"
    decision: "keep the premise"
open_questions:
  - id: Q-01
    question: "none"
    status: "open"
""")
        report = reconcile_book(self.root)
        self.assertTrue(report["ok"], report)

    def test_unrelated_multiline_metadata_is_ignored(self) -> None:
        self.write_chapter()
        self.write_state(_state() + """
project:
  idea: |
    This is prose with no mapping syntax.
    It may contain a colon: safely ignored by the reconciler.
  notes:
    - a note
    - another note
""")
        report = reconcile_book(self.root)
        self.assertTrue(report["ok"], report)

    def test_multidocument_state_fails_closed(self) -> None:
        self.write_chapter()
        self.write_state(_state() + "---\nschema_version: 6\n")
        report = reconcile_book(self.root)
        self.assertFalse(report["ok"])
        self.assertEqual("invalid", report["status"])
        self.assertIn("multiple", report["mismatches"][0]["message"])

    def test_word_count_matches_exporter_for_frontmatter_and_scene_separators(self) -> None:
        self.write_chapter(body="First prose.\n\n* * *\n\nSecond  prose.\n---\nFormatting note\nFinal word.")
        chapters = discover_chapters(self.chapters)
        expected = sum(count_prose_words(chapter) for chapter in chapters)
        self.write_state(_state(words=expected))
        report = reconcile_book(self.root)
        self.assertTrue(report["ok"], report)
        self.assertEqual(expected, report["canonical"]["word_count"])

    def test_json_state_is_supported(self) -> None:
        self.write_chapter()
        state = {
            "schema_version": 6,
            "pipeline": {"current_phase": "Phase 3: Drafting", "status": "in_progress"},
            "manuscript": {"chapter_count_planned": 1, "completed_chapters": [1], "word_count_actual": 3, "status": "in_progress"},
            "gates": {name: "passed" for name in ("intake", "foundation", "architecture", "drafting", "adversarial_audit", "revision_loop", "final_score", "editorial_package")},
        }
        (self.root / "PROJECT_STATE.yaml").write_text(json.dumps(state), encoding="utf-8")
        self.assertTrue(reconcile_book(self.root)["ok"])

    def test_garbage_state_fails_closed(self) -> None:
        self.write_chapter()
        self.write_state("this is not a supported state document\n")
        report = reconcile_book(self.root)
        self.assertFalse(report["ok"])
        self.assertEqual("invalid", report["status"])
        self.assertIn("PROJECT_STATE.yaml", report["mismatches"][0]["field"])

    def test_duplicate_and_ambiguous_required_keys_fail_closed(self) -> None:
        self.write_chapter()
        self.write_state(_state() + "schema_version: 6\n")
        duplicate = reconcile_book(self.root)
        self.assertFalse(duplicate["ok"])
        self.assertIn("duplicate", duplicate["mismatches"][0]["message"])

        self.write_state(_state(completed="[1,]"))
        ambiguous = reconcile_book(self.root)
        self.assertFalse(ambiguous["ok"])
        self.assertEqual("invalid", ambiguous["status"])

    def test_complete_mode_rejects_early_phase_and_unfinished_gate(self) -> None:
        self.write_chapter()
        self.write_state(_state(phase="Phase 6: Final Score", gates="""  intake: "passed"
  foundation: "passed"
  architecture: "passed"
  drafting: "passed"
  adversarial_audit: "pending"
  revision_loop: "passed"
  final_score: "failed"
  editorial_package: pending"""))
        report = reconcile_book(self.root, complete=True, expected_chapters=1, min_words=1, max_words=10)
        fields = {item["field"] for item in report["mismatches"]}
        self.assertIn("pipeline.current_phase", fields)
        self.assertIn("gates.adversarial_audit", fields)

    def test_complete_mode_rejects_empty_canonical_set(self) -> None:
        self.write_state(_state(phase="Phase 7: Editorial Package", completed="[]", words=0, planned=0, manuscript_status="complete", gates="""  intake: "passed"
  foundation: "passed"
  architecture: "passed"
  drafting: "passed"
  adversarial_audit: "failed"
  revision_loop: "failed"
  final_score: "failed"
  editorial_package: in_progress"""))
        report = reconcile_book(self.root, complete=True)
        self.assertFalse(report["ok"])
        self.assertIn("manuscript/chapters", {item["field"] for item in report["mismatches"]})

    def test_complete_mode_allows_honest_failed_literary_gates(self) -> None:
        self.write_chapter()
        failed_gates = """  intake: "passed"
  foundation: "passed"
  architecture: "passed"
  drafting: "passed"
  adversarial_audit: "failed"
  revision_loop: "major_rewrite"
  final_score: "failed"
  editorial_package: in_progress"""
        self.write_state(_state(phase="Phase 7: Editorial Package", manuscript_status="complete", gates=failed_gates))
        report = reconcile_book(self.root, complete=True, expected_chapters=1, min_words=3, max_words=3)
        self.assertTrue(report["ok"], report)

    def test_complete_mode_requires_editorial_package_to_be_started_or_finished(self) -> None:
        self.write_chapter()
        gates = """  intake: "passed"
  foundation: "passed"
  architecture: "passed"
  drafting: "passed"
  adversarial_audit: "failed"
  revision_loop: "failed"
  final_score: "failed"
  editorial_package: pending"""
        self.write_state(_state(phase="Phase 7: Editorial Package", manuscript_status="complete", gates=gates))
        pending = reconcile_book(self.root, complete=True, expected_chapters=1)
        self.assertFalse(pending["ok"])
        self.assertIn("gates.editorial_package", {item["field"] for item in pending["mismatches"]})

        self.write_state(_state(phase="Phase 7: Editorial Package", manuscript_status="complete", gates=gates.replace("editorial_package: pending", "editorial_package: skipped")))
        skipped = reconcile_book(self.root, complete=True, expected_chapters=1)
        self.assertFalse(skipped["ok"])
        self.assertIn("gates.editorial_package", {item["field"] for item in skipped["mismatches"]})

        self.write_state(_state(phase="Phase 7: Editorial Package", manuscript_status="complete", gates=gates.replace("editorial_package: pending", "editorial_package: in_progress")))
        self.assertTrue(reconcile_book(self.root, complete=True, expected_chapters=1)["ok"])


if __name__ == "__main__":
    unittest.main()
