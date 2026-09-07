"""A failed continuity repair must not discard the chapter it was repairing.

Found in a real three-chapter run on 2026-09-07 (writer Luna high, judge Opus
medium). Chapter 3 was written, the blind reader said ``turn_page: yes``, and the
chapter still ended up blocked with no canonical text. The repair pass assigned
its own verdict back to ``accepted``:

    accepted = _accepted(check) and not remaining

so declining an *improvement* threw away the accepted prose it was improving.
The run scored 8.0 instead of 10.0, and the whole gap was that one chapter.

"Never publish an unchecked repair" is the right rule. Publishing nothing is not
the way to keep it: chapters 1 and 2 of the same run shipped with a recorded
``continuity`` flag, and a chapter with a visible finding beats no chapter.
"""

from pathlib import Path

from runner.chapter import ChapterResult, _append_run_report
from runner.score import chapter_rows


def _accepted_line(project: Path, chapter: int, unresolved: int = 0) -> str:
    result = ChapterResult(
        chapter=chapter,
        accepted=True,
        status="accepted",
        cycles=0,
        draft_path=project / "manuscript" / "chapters" / f"chapter-{chapter:02d}.md",
        verdicts=[],
        unresolved_continuity=[{"finding": "the ward has 18 beds in ch1 and 21 here"}] * unresolved,
    )
    _append_run_report(project, result, "single judge (claude claude-opus-5)")
    return (project / "RUN_REPORT.md").read_text(encoding="utf-8")


def test_unresolved_findings_appear_in_the_report(tmp_path: Path):
    text = _accepted_line(tmp_path, 3, unresolved=2)
    assert "unresolved continuity findings: 2" in text


def test_a_clean_chapter_says_nothing_about_continuity(tmp_path: Path):
    assert "unresolved continuity" not in _accepted_line(tmp_path, 1, unresolved=0)


def test_status_stays_exactly_accepted(tmp_path: Path):
    """score.py, acceptance.py and review.py compare this string by equality."""
    result = ChapterResult(3, True, "accepted", 0, Path("x.md"), [], [{"finding": "x"}])
    assert result.status == "accepted"


def test_the_report_line_still_parses_with_findings_attached(tmp_path: Path):
    """The score reads RUN_REPORT.md; a chapter carrying findings must still count."""
    report = tmp_path / "RUN_REPORT.md"
    report.write_text(
        "- chapter 3: accepted after 0 revision cycle(s); judge: single judge (claude claude-opus-5); "
        "last verdict: turn_page=yes, flags=[continuity], stopped_at=I take the portable monitor.; "
        "unresolved continuity findings: 2; file: books/x/manuscript/chapters/chapter-03.md\n",
        encoding="utf-8",
    )
    rows = chapter_rows(report)
    assert rows[3].status == "accepted"
    assert rows[3].turn_page is True
    assert rows[3].flags == ["continuity"]


def test_chapter_result_defaults_to_no_findings():
    assert ChapterResult(1, True, "accepted", 0, Path("x.md")).unresolved_continuity == []


def test_a_new_chapter_survives_a_failed_repair(tmp_path, monkeypatch):
    """No canonical text yet: blocking would preserve nothing. This is chapter 3."""
    root = _project(tmp_path)
    result = _run_with_failing_repair(root, monkeypatch)
    assert result.accepted
    assert result.unresolved_continuity
    assert (root / "manuscript/chapters/chapter-01.md").is_file()


def test_a_rewrite_that_contradicts_the_book_still_blocks(tmp_path, monkeypatch):
    """Canonical text exists: preserving it is exactly what the rule is for.

    The two cases share one code path and opposite answers, so they are asserted
    together — collapsing them again should turn one of these red.
    """
    root = _project(tmp_path)
    canonical = root / "manuscript/chapters/chapter-01.md"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text("# Chapter 1: The key\n\nThe key is brass.\n", encoding="utf-8")
    original = canonical.read_bytes()
    result = _run_with_failing_repair(root, monkeypatch)
    assert not result.accepted
    assert canonical.read_bytes() == original


def _project(tmp_path: Path) -> Path:
    from test_continuity_memory import book

    from runner.filesystem import update_state_value

    root = book(tmp_path)
    update_state_value(root / "PROJECT_STATE.yaml", "genre", "nonfiction")
    (root / "artifacts/05-outline.md").write_text("## Chapter 1: The key", encoding="utf-8")
    return root


def _run_with_failing_repair(root: Path, monkeypatch):
    from runner.adapters import FakeAdapter
    from runner.chapter import run_chapter

    monkeypatch.setattr("runner.continuity.memory_before", lambda *a: [])
    monkeypatch.setattr(
        "runner.continuity.verify_candidate",
        lambda *a: [{"previous_id": "evidence", "quote": "The key is silver.", "reason": "Metal changed"}],
    )
    yes = "```yaml\nturn_page: yes\nstopped_at: none\nremember: [a key]\nflags: []\nvs_previous: better\n```"
    prose = "# Chapter 1: The key\n\nThe key is silver."
    return run_chapter(
        root,
        1,
        {
            "writer": FakeAdapter([prose]),
            "editor": FakeAdapter([prose]),
            "judge": FakeAdapter([yes, yes]),
            "continuity": FakeAdapter([]),
        },
    )
