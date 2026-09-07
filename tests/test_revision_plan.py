import json
import pytest
from runner.adapters import FakeAdapter
from runner.filesystem import scaffold_project
from runner.revision import ensure_revision_plan, revision_context


def project(tmp_path):
    root = tmp_path / "book"
    scaffold_project(root, idea="A complete record mystery", language="en", adapter="fake", model_name="fake")
    (root / "work/editorial-revision.md").write_text("Resolve the contradictory removal dates.", encoding="utf-8")
    for number, text in ((1, "Removed in 2005."), (2, "Removed in 2006.")):
        (root / f"manuscript/chapters/chapter-{number:02d}.md").write_text(text, encoding="utf-8")
    return root


def response(year="2006"):
    return json.dumps({"canonical_facts": [f"The removal date is 17 October {year}."],
                       "chapter_actions": {"1": [f"Change 2005 to {year}."], "2": ["Keep the removal date consistent."]}})


def test_shared_plan_reads_all_chapters_and_survives_resume(tmp_path):
    root = project(tmp_path)
    adapter = FakeAdapter([response()])
    path = ensure_revision_plan(root, adapter)
    assert "Removed in 2005." in adapter.calls[0].prompt
    assert "Removed in 2006." in adapter.calls[0].prompt
    assert "17 October 2006" in revision_context(root, 1)
    assert "17 October 2006" in revision_context(root, 2)
    assert "Change 2005" not in revision_context(root, 2)
    # Accepted chapter edits must not cause a different plan on resume.
    (root / "manuscript/chapters/chapter-01.md").write_text("Now revised.", encoding="utf-8")
    assert ensure_revision_plan(root, adapter) == path
    assert len(adapter.calls) == 1


def test_new_audit_or_author_notes_get_a_new_plan_without_overwriting_history(tmp_path):
    root = project(tmp_path)
    adapter = FakeAdapter([response(), response("2007")])
    first = ensure_revision_plan(root, adapter)
    original = first.read_bytes()
    (root / "work/author-notes.md").write_text("Use 2007 as the story year.", encoding="utf-8")
    assert revision_context(root, 1) == ""
    second = ensure_revision_plan(root, adapter)
    assert first != second and first.read_bytes() == original
    assert "2007" in revision_context(root, 1)


def test_book_uses_one_plan_in_each_editor_without_leaking_it_to_readers(tmp_path):
    from runner.book import run_book
    root = project(tmp_path)
    (root / "artifacts/05-outline.md").write_text("## Chapter 1: First\n\n## Chapter 2: Last\n", encoding="utf-8")
    for number in (1, 2):
        (root / f"work/rewrite-chapter-{number:02d}.pending").write_text("audit repair", encoding="utf-8")
    plan = json.dumps({"canonical_facts": ["SHARED-FACT-SENTINEL"],
                       "chapter_actions": {"1": ["CH1-ONLY-ACTION"], "2": ["CH2-ONLY-ACTION"]}})
    editor = FakeAdapter([plan, "# Chapter 1: First\n\nThe first scene.", "# Chapter 2: Last\n\nThe ending."])
    yes = "```yaml\nturn_page: yes\nstopped_at: none\nremember: []\nflags: []\n```"
    judge = FakeAdapter([yes, yes])
    result = run_book(root, {"editor": editor, "judge": judge}, {})
    assert result.status == "completed"
    assert len(editor.calls) == 3
    for call in editor.calls[1:]:
        assert "SHARED-FACT-SENTINEL" in call.prompt
    assert "CH2-ONLY-ACTION" not in editor.calls[1].prompt
    assert "CH1-ONLY-ACTION" not in editor.calls[2].prompt
    assert all("SHARED-FACT-SENTINEL" not in call.prompt for call in judge.calls)


@pytest.mark.parametrize("raw", ["not JSON", '{"canonical_facts": [], "chapter_actions": {}}',
    '{"canonical_facts": ["2006"], "chapter_actions": {"1": ["Fix date"]}}'])
def test_invalid_plan_preserves_chapters_and_does_not_cache(tmp_path, raw):
    root = project(tmp_path)
    original = (root / "manuscript/chapters/chapter-01.md").read_bytes()
    with pytest.raises(ValueError):
        ensure_revision_plan(root, FakeAdapter([raw]))
    assert (root / "manuscript/chapters/chapter-01.md").read_bytes() == original
    assert not list((root / "work/revision-plans").glob("*.json"))
