"""The file named PROJECT_STATE.yaml has to agree with the manuscript beside it.

Found on 2026-09-07 by a first-time user reading books/prova-2, a finished run with
three accepted chapters on disk:

    manuscript:
      chapter_count: 0
      completed_chapters: []
      status: "not_started"

The block is written once by scaffold_project and never touched again — grep found
no writer and no reader. Dead fields would be harmless; these are dead fields that
say nothing happened. Someone coming back to a project tomorrow reads them.

The state is derived from the chapters on disk rather than incremented, so a project
that has been wrong since it was created corrects itself the next time it is written.
"""

from pathlib import Path

from runner.filesystem import refresh_manuscript_state, scaffold_project


def _book(tmp_path: Path, chapters=()) -> Path:
    root = tmp_path / "book"
    scaffold_project(root, idea="a haunted ward", adapter="fake", model_name="fake", language="en")
    folder = root / "manuscript" / "chapters"
    folder.mkdir(parents=True, exist_ok=True)
    for number in chapters:
        (folder / f"chapter-{number:02d}.md").write_text(f"# Chapter {number}\n\nProse.\n", encoding="utf-8")
    return root


def test_the_state_counts_the_chapters_that_exist(tmp_path: Path):
    root = _book(tmp_path, chapters=(1, 2, 3))
    refresh_manuscript_state(root)
    state = (root / "PROJECT_STATE.yaml").read_text(encoding="utf-8")
    assert "chapter_count: 3" in state
    assert "completed_chapters: [1, 2, 3]" in state


def test_a_book_with_chapters_is_not_described_as_not_started(tmp_path: Path):
    root = _book(tmp_path, chapters=(1,))
    refresh_manuscript_state(root)
    assert 'status: "in_progress"' in (root / "PROJECT_STATE.yaml").read_text(encoding="utf-8")


def test_an_empty_manuscript_still_reads_as_not_started(tmp_path: Path):
    root = _book(tmp_path)
    refresh_manuscript_state(root)
    state = (root / "PROJECT_STATE.yaml").read_text(encoding="utf-8")
    assert "chapter_count: 0" in state
    assert 'status: "not_started"' in state


def test_the_pipeline_status_above_it_is_left_alone(tmp_path: Path):
    """`status:` appears twice in the file. Writing the first one found would set the
    pipeline's status to the manuscript's and quietly reroute the whole run."""
    root = _book(tmp_path, chapters=(1, 2))
    before = (root / "PROJECT_STATE.yaml").read_text(encoding="utf-8")
    pipeline_status = before.split("pipeline:")[1].split("manuscript:")[0]
    refresh_manuscript_state(root)
    after = (root / "PROJECT_STATE.yaml").read_text(encoding="utf-8")
    assert after.split("pipeline:")[1].split("manuscript:")[0] == pipeline_status


def test_an_accepted_chapter_updates_the_state_without_being_told_the_number(tmp_path: Path):
    """Deriving from disk means a project that was wrong before is right afterwards."""
    root = _book(tmp_path, chapters=(1, 2, 3))
    refresh_manuscript_state(root)
    (root / "manuscript" / "chapters" / "chapter-04.md").write_text("# Chapter 4\n\nMore.\n", encoding="utf-8")
    refresh_manuscript_state(root)
    assert "completed_chapters: [1, 2, 3, 4]" in (root / "PROJECT_STATE.yaml").read_text(encoding="utf-8")


def test_accepting_a_chapter_writes_the_state(tmp_path: Path, monkeypatch):
    """The seam that matters: nobody calls refresh_manuscript_state by hand."""
    from runner.adapters import FakeAdapter
    from runner.chapter import run_chapter
    from runner.filesystem import update_state_value

    root = _book(tmp_path)
    update_state_value(root / "PROJECT_STATE.yaml", "genre", "nonfiction")
    (root / "artifacts/05-outline.md").write_text("## Chapter 1: The night", encoding="utf-8")
    monkeypatch.setattr("runner.continuity.memory_before", lambda *a: [])
    monkeypatch.setattr("runner.continuity.verify_candidate", lambda *a: [])
    yes = "```yaml\nturn_page: yes\nstopped_at: none\nremember: [a key]\nflags: []\nvs_previous: better\n```"
    prose = "# Chapter 1: The night\n\nShe took the night shift and the corridor was empty.\n"
    run_chapter(root, 1, {"writer": FakeAdapter([prose]), "editor": FakeAdapter([prose]),
                          "judge": FakeAdapter([yes, yes]), "continuity": FakeAdapter([])})
    state = (root / "PROJECT_STATE.yaml").read_text(encoding="utf-8")
    assert "chapter_count: 1" in state
    assert "completed_chapters: [1]" in state
