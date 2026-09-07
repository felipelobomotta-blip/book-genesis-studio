"""A chapter that repeats an earlier chapter does not pass in silence.

books/prova-2 scored 10.0/10 with "The coffee was bad and she drank all of it" in
all three chapters. Every gate passed it because no gate ever compared two chapters:
the judge is blind by design (ADR 0001) and reads one chapter at a time.

The rule here follows the one already established for continuity repair — try the
rewrite, and if the rewrite does not hold, keep the chapter and carry the finding
into RUN_REPORT.md rather than publishing nothing. A visible finding beats a missing
chapter, and a 40-chapter run must not stall on a repeated sentence.
"""

from pathlib import Path

from runner.chapter import ChapterResult, _append_run_report, run_chapter

COFFEE = "The coffee was bad and she drank all of it."
YES = "```yaml\nturn_page: yes\nstopped_at: none\nremember: [a key]\nflags: []\nvs_previous: better\n```"


def _project(tmp_path: Path) -> Path:
    from test_continuity_memory import book

    from runner.filesystem import update_state_value

    root = book(tmp_path)
    update_state_value(root / "PROJECT_STATE.yaml", "genre", "nonfiction")
    (root / "artifacts/05-outline.md").write_text("## Chapter 2: The night", encoding="utf-8")
    chapters = root / "manuscript/chapters"
    chapters.mkdir(parents=True, exist_ok=True)
    (chapters / "chapter-01.md").write_text(f"# Chapter 1\n\nShe checked the monitor. {COFFEE}\n", encoding="utf-8")
    return root


def _run(root: Path, monkeypatch, drafts):
    from runner.adapters import FakeAdapter

    monkeypatch.setattr("runner.continuity.memory_before", lambda *a: [])
    monkeypatch.setattr("runner.continuity.verify_candidate", lambda *a: [])
    return run_chapter(
        root,
        2,
        {
            "writer": FakeAdapter([drafts[0]]),
            "editor": FakeAdapter(drafts[1:] or [drafts[0]]),
            "judge": FakeAdapter([YES, YES, YES, YES]),
            "continuity": FakeAdapter([]),
        },
    )


def test_a_chapter_that_reuses_an_earlier_sentence_is_caught(tmp_path, monkeypatch):
    repeats = f"# Chapter 2\n\nThe tape stuck to her glove. {COFFEE}\n"
    result = _run(tmp_path := _project(tmp_path), monkeypatch, [repeats, repeats])
    assert [item["text"] for item in result.repeated_lines] == [COFFEE]
    assert result.repeated_lines[0]["first_used_in"] == 1


def test_a_rewrite_that_drops_the_repeat_clears_the_finding(tmp_path, monkeypatch):
    """The gate exists to get the sentence out of the book, not to label it."""
    repeats = f"# Chapter 2\n\nThe tape stuck to her glove. {COFFEE}\n"
    clean = "# Chapter 2\n\nThe tape stuck to her glove. She left the cup where it was.\n"
    result = _run(_project(tmp_path), monkeypatch, [repeats, clean])
    assert result.repeated_lines == []
    assert COFFEE not in result.draft_path.read_text(encoding="utf-8")


def test_a_clean_chapter_is_never_sent_for_a_rewrite(tmp_path, monkeypatch):
    """The rewrite costs a provider call. It must fire only on a real repeat."""
    clean = "# Chapter 2\n\nThe vein rolled and she tried again.\n"
    result = _run(_project(tmp_path), monkeypatch, [clean])
    assert result.repeated_lines == []
    assert result.accepted


def test_status_stays_exactly_accepted(tmp_path):
    """score.py:86, acceptance.py:72 and review.py:137 compare this string by equality."""
    result = ChapterResult(2, True, "accepted", 0, Path("x.md"), [], [], [{"text": COFFEE}])
    assert result.status == "accepted"


def test_the_report_records_a_repeat_that_survived_the_rewrite(tmp_path: Path):
    result = ChapterResult(2, True, "accepted", 0, tmp_path / "chapter-02.md", [], [],
                           [{"text": COFFEE, "first_used_in": 1, "times": 2}])
    _append_run_report(tmp_path, result, "single judge (fake)")
    assert "reused lines: 1" in (tmp_path / "RUN_REPORT.md").read_text(encoding="utf-8")


def test_a_clean_chapter_says_nothing_about_reuse(tmp_path: Path):
    result = ChapterResult(2, True, "accepted", 0, tmp_path / "chapter-02.md", [])
    _append_run_report(tmp_path, result, "single judge (fake)")
    assert "reused lines" not in (tmp_path / "RUN_REPORT.md").read_text(encoding="utf-8")
