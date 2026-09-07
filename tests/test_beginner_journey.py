"""Customer-visible regressions: activity, language, recovery, and delivered files."""
import io
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch
import zipfile

from runner.activity import activity_events, complete_with_activity
from runner.adapters import AdapterError, FakeAdapter, codex_login_status
from runner.brief import build_chapter_brief
from runner.filesystem import scaffold_project, load_state_summary
from runner.phases import run_phase
from runner.session import run_session, _drafting
from runner.roles import build_role_adapters
from runner.ui import RichView
from test_session import INTAKE, FOUNDATION, ARCHITECTURE, CHAPTER_ONE, CHAPTER_TWO, AUDIT, SCORE, PACKAGE, RecordingView, OUTLINE, NO


class BeginnerJourneyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name) / "book"
        scaffold_project(self.project, idea="A complete mystery", language="en", adapter="fake", model_name="fake")

    def test_model_cannot_override_the_selected_language(self):
        response = INTAKE.replace("language: en", "language: pt-BR")
        self.assertTrue(run_phase(self.project, {"architect": FakeAdapter([response])}, {}).ok)
        self.assertEqual("en", load_state_summary(self.project)["language"])
        (self.project / "artifacts/05-outline.md").write_text(OUTLINE, encoding="utf-8")
        self.assertIn("Book language: en", build_chapter_brief(self.project, 1))

    def test_writer_has_one_length_target_when_author_overrides_genre(self):
        from runner.chapter import writer_prompt
        from runner.constants import load_genre_profile
        from runner.filesystem import update_state_value
        update_state_value(self.project / "PROJECT_STATE.yaml", "idea", "1500 to 1800 words each")
        (self.project / "artifacts/05-outline.md").write_text(OUTLINE, encoding="utf-8")
        brief = build_chapter_brief(self.project, 1)
        self.assertIn("Target length: 1500-1800 words", brief)
        profile = load_genre_profile("mystery")
        prompt = writer_prompt(brief, 1, "mystery", profile)
        self.assertNotIn(f"({profile.words_per_chapter_min}-{profile.words_per_chapter_max} words unless", prompt)

    def test_slow_provider_emits_activity_before_it_returns(self):
        pulse = threading.Event()
        lines = []
        def say(line):
            lines.append(line)
            if "waiting for provider" in line:
                pulse.set()
        class Slow:
            name = "fixture"
            def complete(self, prompt, *, model=""):
                if not pulse.wait(1):
                    raise AssertionError("No live activity while the provider was busy")
                return "A finished chapter."
        with patch("runner.activity.HEARTBEAT_SECONDS", 0.01), activity_events(say):
            self.assertEqual("A finished chapter.", complete_with_activity(Slow(), "private prompt"))
        self.assertIn("received 3 words", lines[-1])
        self.assertFalse(any("private prompt" in line for line in lines))

    def test_full_run_delivers_reader_markdown_and_epub(self):
        path = Path(self.tmp.name) / "responses.txt"
        second = [text.replace("Chapter 1: The Watch Room", "Chapter 2: The Drive") for text in CHAPTER_TWO]
        path.write_text("\n=== NEXT ===\n".join([INTAKE, FOUNDATION, ARCHITECTURE, *CHAPTER_ONE, *second, AUDIT, SCORE, PACKAGE]), encoding="utf-8")
        setup = build_role_adapters(fake_responses_path=path)
        self.assertEqual("completed", run_session(self.project, setup, RecordingView(), yes=True).status)
        self.assertIn("Chapter 2", (self.project / "exports/manuscript.md").read_text(encoding="utf-8"))
        self.assertTrue((self.project / "review/index.html").is_file())
        with zipfile.ZipFile(self.project / "exports/manuscript.epub") as book:
            self.assertIsNone(book.testzip())
            self.assertEqual(b"application/epub+zip", book.read("mimetype"))

    def test_retry_plan_uses_blocked_feedback_and_reaches_only_that_chapter(self):
        from runner.book import BookResult
        from types import SimpleNamespace
        (self.project / "artifacts/05-outline.md").write_text(OUTLINE, encoding="utf-8")
        report = self.project / "evaluations/chapter-01-judge-attempt-000002-1.md"
        report.write_text(NO, encoding="utf-8")
        manifest = self.project / "manuscript/chapters/history/chapter-01/manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({"attempts": [{"status": "blocked", "verdict_path": "evaluations/" + report.name}]}), encoding="utf-8")
        view = RecordingView(["perhaps", "ok", "no"])
        with patch("runner.session.run_book", return_value=BookResult("blocked", [], 1, "saved")) as run:
            result = _drafting(self.project, SimpleNamespace(adapters={}, models={}), view, ask=True, human=False, cap=1)
        self.assertEqual("blocked", result.status)
        self.assertEqual(2, run.call_count)
        self.assertIn("replace long explanations", build_chapter_brief(self.project, 1))
        self.assertNotIn("replace long explanations", build_chapter_brief(self.project, 2))

    def test_doctor_unknown_output_is_not_reported_as_logged_in(self):
        with patch("runner.adapters._resolve", return_value=["codex"]), patch("runner.adapters._run", return_value=subprocess.CompletedProcess([], 0, "unexpected output", "")):
            self.assertIsNone(codex_login_status())

    def test_rich_log_shows_activity_without_live_terminal(self):
        from rich.console import Console
        buffer = io.StringIO()
        view = RichView(interactive=False, live=False, console=Console(file=buffer))
        view.event("Writer: waiting for provider response | 5s elapsed")
        self.assertIn("waiting for provider response", buffer.getvalue())

    def test_outline_summary_is_not_a_duplicate_chapter_or_writer_brief(self):
        from runner.book import outline_chapters
        from runner.brief import extract_chapter_section
        from runner.filesystem import _outline_chapter_numbers
        outline = "# Outline\n\n**Chapter 1:** Summary\n\n**Chapter 2:** Summary\n\n" + OUTLINE
        self.assertEqual([1, 2], outline_chapters(outline))
        self.assertEqual([1, 2], _outline_chapter_numbers(outline))
        self.assertIn("OUTLINE-SENTINEL-CH1", extract_chapter_section(outline, 1))
        self.assertNotIn("Summary", extract_chapter_section(outline, 1))
        self.assertEqual([1, 2], outline_chapters("## Chapter 1: First\n\nBody\n\n**Chapter 2: Second**\n\nBody"))
        with self.assertRaises(ValueError):
            outline_chapters(OUTLINE + "\n## Chapter 2: Duplicate\n")

    def test_failed_step_offers_retry_with_feedback_without_restart(self):
        from runner.session import SessionResult
        from runner.phases import build_phase_prompt
        from runner.filesystem import current_phase
        view = RecordingView(["ok"])
        with patch("runner.session._run_session", side_effect=[SessionResult("failed", "missing outline"), SessionResult("completed")]) as run:
            self.assertEqual("completed", run_session(self.project, None, view).status)
        self.assertEqual(2, run.call_count)
        self.assertIn("missing outline", build_phase_prompt(self.project, current_phase(self.project)))

    def test_audit_repair_is_offered_and_preserves_previous_chapters(self):
        from runner.session import SessionResult, DRAFTING_LABEL
        from runner.filesystem import update_state_value
        (self.project / "artifacts/05-outline.md").write_text(OUTLINE, encoding="utf-8")
        (self.project / "artifacts/08-adversarial-audit.md").write_text("Repair the impossible timeline.\naudit_status: revise", encoding="utf-8")
        original = self.project / "manuscript/chapters/chapter-01.md"
        original.parent.mkdir(parents=True, exist_ok=True)
        original.write_text("Keep this existing version.", encoding="utf-8")
        update_state_value(self.project / "PROJECT_STATE.yaml", "status", "awaiting_revision")
        with patch("runner.session._run_session", side_effect=[SessionResult("blocked"), SessionResult("stopped")]):
            run_session(self.project, None, RecordingView(["yes"]))
        self.assertEqual("Keep this existing version.", original.read_text(encoding="utf-8"))
        self.assertTrue((self.project / "work/rewrite-chapter-02.pending").exists())
        self.assertEqual(DRAFTING_LABEL, load_state_summary(self.project)["current_phase"])
        self.assertIn("impossible timeline", build_chapter_brief(self.project, 2))

    def test_noninteractive_failure_does_not_retry_or_prompt(self):
        from runner.session import SessionResult
        view = RecordingView()
        with patch("runner.session._run_session", return_value=SessionResult("failed")) as run:
            run_session(self.project, None, view, yes=True)
        self.assertEqual(1, run.call_count)
        self.assertEqual([], view.questions)

    def test_existing_book_can_resume_with_a_simple_answer(self):
        from runner.app import session_main
        from runner.session import SessionResult
        view = RecordingView(["ok"])
        with patch("runner.app.build_setup", return_value=None), patch("runner.app.run_session", return_value=SessionResult("stopped")) as run:
            result = session_main(["new", "--idea", "A complete mystery", "--language", "en", "--path", str(self.project)], view)
        self.assertEqual(0, result)
        self.assertEqual(self.project, run.call_args.args[0])
        self.assertIn("Continue it?", view.questions[0][0])

    def test_cancelled_cli_call_terminates_its_process_tree(self):
        from runner.adapters import _run
        from unittest.mock import Mock
        process = Mock()
        process.communicate.side_effect = [KeyboardInterrupt(), ("", "")]
        with patch("runner.adapters.subprocess.Popen", return_value=process), patch("runner.adapters._terminate_timed_out_process") as terminate:
            with self.assertRaises(KeyboardInterrupt):
                _run(["fixture"], "prompt", timeout_seconds=10)
        terminate.assert_called_once_with(process)

    def test_explicit_length_is_measured_and_repaired_before_acceptance(self):
        from runner.chapter import _fit_requested_length
        from runner.brief import chapter_word_limits
        from runner.filesystem import update_state_value
        from runner.history import reserve_attempt
        update_state_value(self.project / "PROJECT_STATE.yaml", "idea", "Exactly two chapters, 10 to 20 words each.")
        self.assertEqual((10, 20), chapter_word_limits(self.project))
        attempt, _ = reserve_attempt(self.project, 1)
        corrected = "# Chapter 1\n\n" + "word " * 10
        adapter = FakeAdapter([corrected])
        result = _fit_requested_length(self.project, 1, "word " * 40, {"editor": adapter}, {}, attempt, lambda _: None)
        self.assertTrue(10 <= len(result.split()) <= 20)
        self.assertTrue(list((self.project / "manuscript/drafts/chapter-01").glob("*-length-*.md")))
        update_state_value(self.project / "PROJECT_STATE.yaml", "idea", "A book of 1000 to 2000 words total.")
        self.assertIsNone(chapter_word_limits(self.project))

    def test_length_repairs_are_bounded_and_never_silently_accept_oversize(self):
        from runner.chapter import _fit_requested_length
        from runner.filesystem import update_state_value
        from runner.history import reserve_attempt
        update_state_value(self.project / "PROJECT_STATE.yaml", "idea", "10-20 words each")
        attempt, _ = reserve_attempt(self.project, 1)
        oversize = "# Chapter 1\n\n" + "word " * 40
        adapter = FakeAdapter([oversize, oversize])
        with self.assertRaisesRegex(AdapterError, "stopped after two attempts"):
            _fit_requested_length(self.project, 1, oversize, {"editor": adapter}, {}, attempt, lambda _: None)
        self.assertFalse((self.project / "manuscript/chapters/chapter-01.md").exists())

    def test_saved_audit_prompts_before_any_new_model_call(self):
        from runner.filesystem import update_state_value
        from types import SimpleNamespace
        update_state_value(self.project / "PROJECT_STATE.yaml", "status", "awaiting_revision")
        with patch("runner.session.run_phase") as run:
            result = run_session(self.project, SimpleNamespace(adapters={}, models={}), RecordingView(["no"]))
        self.assertEqual("blocked", result.status)
        run.assert_not_called()

    def test_saved_length_repair_resumes_only_verified_draft(self):
        from runner.chapter import _resumable_length_draft
        from runner.history import reserve_attempt, record_draft
        attempt, _ = reserve_attempt(self.project, 1)
        path = self.project / "manuscript/drafts/chapter-01" / f"{attempt}-length-1.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Saved draft.", encoding="utf-8")
        record_draft(self.project, 1, attempt, path)
        self.assertEqual("Saved draft.", _resumable_length_draft(self.project, 1))
        path.write_text("Tampered draft.", encoding="utf-8")
        self.assertIsNone(_resumable_length_draft(self.project, 1))

    def test_declining_audit_revision_still_delivers_a_labelled_draft(self):
        from runner.filesystem import update_state_value
        from types import SimpleNamespace
        update_state_value(self.project / "PROJECT_STATE.yaml", "status", "awaiting_revision")
        (self.project / "artifacts/05-outline.md").write_text(OUTLINE, encoding="utf-8")
        chapter = self.project / "manuscript/chapters/chapter-01.md"
        chapter.parent.mkdir(parents=True, exist_ok=True)
        chapter.write_text("# Chapter 1\n\nA saved chapter.", encoding="utf-8")
        result = run_session(self.project, SimpleNamespace(adapters={}, models={}), RecordingView(["no"]))
        self.assertEqual("blocked", result.status)
        self.assertIn("Partial export", (self.project / "exports/draft.md").read_text(encoding="utf-8"))
        self.assertTrue((self.project / "exports/draft.epub").exists())
        self.assertTrue((self.project / "review/index.html").exists())

    def test_audit_repair_edits_existing_prose_without_creative_rewrite(self):
        from runner.chapter import run_chapter
        from test_session import DRAFT, YES
        chapter = self.project / "manuscript/chapters/chapter-01.md"
        chapter.parent.mkdir(parents=True, exist_ok=True)
        chapter.write_text(DRAFT, encoding="utf-8")
        (self.project / "work/editorial-revision.md").write_text("Make the librarian less formal.", encoding="utf-8")
        (self.project / "work/rewrite-chapter-01.pending").write_text("rewrite", encoding="utf-8")
        writer = FakeAdapter([])
        plan = json.dumps({"canonical_facts": ["Keep the existing facts and ending."], "chapter_actions": {"1": ["Make the librarian less formal."]}})
        result = run_chapter(self.project, 1, {"writer": writer, "disruptor": writer, "editor": FakeAdapter([plan, DRAFT]), "judge": FakeAdapter([YES])})
        self.assertTrue(result.accepted)

    def test_rewritten_chapter_is_not_counted_as_first_draft_acceptance(self):
        from runner.chapter import run_chapter
        from runner.score import genesis_score
        from test_session import DRAFT, YES
        (self.project / "artifacts/05-outline.md").write_text(OUTLINE, encoding="utf-8")
        adapter = FakeAdapter([DRAFT, DRAFT, YES, DRAFT, DRAFT, YES])
        adapters = {role: adapter for role in ("writer", "disruptor", "judge", "editor")}
        self.assertTrue(run_chapter(self.project, 1, adapters).accepted)
        self.assertEqual(1.0, next(c.value for c in genesis_score(self.project).components if c.key == "first_pass"))
        self.assertTrue(run_chapter(self.project, 1, adapters).accepted)
        self.assertEqual(0.0, next(c.value for c in genesis_score(self.project).components if c.key == "first_pass"))


if __name__ == "__main__":
    unittest.main()
