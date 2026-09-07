import json
import threading
import time
from types import SimpleNamespace

import pytest

from runner.activity import activity_events, complete_with_activity, public_text_observer, WorkflowPaused
from runner.adapters import AdapterError, FakeAdapter
from runner.recovery import classify_error, capabilities
from runner.studio import StudioView
from runner.workspace_lock import project_lock


@pytest.mark.parametrize("message,category,retryable", [
    ("HTTP 401: unauthorized", "authentication", False), ("HTTP 403", "authentication", False),
    ("You've hit your session limit · resets 1:40pm", "quota", False),
    ("HTTP 429: quota exhausted", "quota", False), ("HTTP 429 rate limit", "rate_limit", True),
    ("headless permission denied", "permission", False), ("unknown model", "configuration", False),
    ("model not found", "configuration", False), ("provider timed out", "temporary", True),
    ("HTTP 503", "temporary", True), ("empty response", "output", True)])
def test_actionable_recovery(message, category, retryable):
    advice = classify_error(message)
    assert (advice.category, advice.retryable) == (category, retryable)


def test_metrics_record_success_and_failure_without_content_or_secrets(tmp_path):
    class Failing:
        name = "test"
        def complete(self, *a, **kw):
            raise AdapterError("HTTP 401 SECRET-KEY")
    with activity_events(lambda _: None, project=tmp_path):
        assert complete_with_activity(FakeAdapter(["private manuscript"]), "secret prompt") == "private manuscript"
        with pytest.raises(AdapterError):
            complete_with_activity(Failing(), "secret prompt")
    raw = (tmp_path / "work/metrics.jsonl").read_text(encoding="utf-8")
    assert all(secret not in raw for secret in ["private manuscript", "secret prompt", "SECRET-KEY"])
    records = [json.loads(line) for line in raw.splitlines()]
    assert [r["outcome"] for r in records] == ["success", "error"]
    assert records[1]["error_category"] == "authentication"


def test_public_prose_stream_has_no_duplicate_final_text_or_judge_leak(tmp_path):
    class Streaming:
        name = "stream"
        def complete(self, *a, **kw):
            observer = public_text_observer()
            if observer:
                observer("Hello ")
                observer("reader.")
            return "Hello reader."
    chunks = []
    with activity_events(lambda _: None, project=tmp_path, prose_listener=lambda task, text: chunks.append(text)):
        complete_with_activity(Streaming(), "write", task="Chapter 1 writer")
        complete_with_activity(Streaming(), "judge", task="Blind reader")
    assert chunks == ["Hello ", "reader."]


def test_pause_prevents_next_provider_call_and_releases_context():
    cancel = threading.Event()
    cancel.set()
    adapter = FakeAdapter(["saved"])
    with activity_events(lambda _: None, cancel=cancel):
        with pytest.raises(WorkflowPaused):
            complete_with_activity(adapter, "do not call")
    assert not adapter.calls
    assert complete_with_activity(adapter, "now call") == "saved"


def test_studio_checkpoint_waits_for_one_answer_and_pause_unblocks():
    view = StudioView()
    results = []
    worker = threading.Thread(target=lambda: results.append(view.checkpoint("Brief", "Text", "Continue")))
    worker.start()
    assert view.waiting.wait(2)
    assert view.answer("yes")
    worker.join(2)
    assert results == ["yes"] and not worker.is_alive()
    assert not view.answer("unsolicited")
    worker = threading.Thread(target=lambda: results.append(view.ask("Retry?")))
    worker.start()
    assert view.waiting.wait(2)
    view.cancel.set()
    worker.join(2)
    assert results[-1] == "q" and not worker.is_alive()


def test_project_lock_rejects_concurrent_writer_and_releases_after_error(tmp_path):
    with pytest.raises(RuntimeError):
        with project_lock(tmp_path):
            with pytest.raises(ValueError, match="already open"):
                with project_lock(tmp_path):
                    pass
            raise RuntimeError("crash")
    with project_lock(tmp_path):
        pass


def test_targeted_audit_preserves_unaffected_chapter_and_blocks_unchanged_repeat(tmp_path):
    from runner.filesystem import scaffold_project
    from runner.session import _prepare_audit_revision
    project = tmp_path / "book"
    scaffold_project(project, idea="A record mystery", language="en", adapter="fake", model_name="")
    (project / "artifacts/05-outline.md").write_text("## Chapter 1: Start\n\n## Chapter 2: End", encoding="utf-8")
    for n in (1, 2):
        (project / f"manuscript/chapters/chapter-{n:02d}.md").write_text(f"# Chapter {n}\n\nSaved prose.", encoding="utf-8")
    plan = {"canonical_facts": ["Preserve 2006."], "chapter_actions": {"1": ["Preserve"], "2": ["Fix date"]}, "affected_chapters": [2]}
    setup = SimpleNamespace(adapters={"editor": FakeAdapter([json.dumps(plan)])}, models={})
    original = (project / "manuscript/chapters/chapter-01.md").read_bytes()
    _prepare_audit_revision(project, setup)
    assert not (project / "work/rewrite-chapter-01.pending").exists()
    assert (project / "work/rewrite-chapter-02.pending").exists()
    assert (project / "manuscript/chapters/chapter-01.md").read_bytes() == original
    (project / "work/rewrite-chapter-02.pending").unlink()
    with pytest.raises(ValueError, match="no manuscript progress"):
        _prepare_audit_revision(project, setup)
