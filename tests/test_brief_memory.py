"""The writer is told what the book has already used, before it writes.

Writing chapter 3 of books/prova-2, the writer received the outline section for
chapter 3, the foundation artifacts, and the last 300 words of chapter 2. It had
never seen chapter 1. So it reprised chapter 1 beat for beat and wrote "The coffee
was bad and she drank all of it" for the third time, in a scene with no coffee.

The continuity memory that could have told it already existed in runner/continuity.py
and was only ever used to police the finished draft. This is the other direction:
the memory reaches the writer before the draft exists.
"""

from pathlib import Path

import pytest

from runner.brief import build_chapter_brief
from runner.filesystem import scaffold_project

COFFEE = "The coffee was bad and she drank all of it."
OUTLINE = """# Outline

## Chapter 1: The Watch Room

She takes the night shift.

## Chapter 2: The Records Office

She searches for the room.

## Chapter 3: The Ward

She is called back to the ward.
"""


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "book"
    scaffold_project(root, idea="a haunted ward", adapter="fake", model_name="fake", language="en")
    state = root / "PROJECT_STATE.yaml"
    state.write_text(state.read_text(encoding="utf-8").replace('genre: ""', 'genre: "thriller"'), encoding="utf-8")
    (root / "artifacts" / "05-outline.md").write_text(OUTLINE, encoding="utf-8")
    chapters = root / "manuscript" / "chapters"
    # The repeat sits at the top of each chapter, far outside the 300-word tail the
    # brief already carried — otherwise this test would pass without the new section.
    for number in (1, 2):
        body = f"# Chapter {number}\n\nSENTINEL-{number} She checked the monitor. {COFFEE}\n\n" + ("filler word " * 400)
        (chapters / f"chapter-{number:02d}.md").write_text(body + "\nThe corridor was empty.\n", encoding="utf-8")
    return root


def test_the_brief_names_the_sentence_the_book_keeps_reusing(project: Path):
    assert COFFEE in build_chapter_brief(project, 3)


def test_the_brief_says_where_it_was_used_and_how_often(project: Path):
    """A bare list of banned strings reads as arbitrary. The count is the argument."""
    brief = build_chapter_brief(project, 3)
    section = brief.split("## Already used in this book")[1]
    assert "chapter 1" in section and "2 times" in section


def test_a_book_that_repeats_nothing_gets_no_such_section(project: Path):
    """An always-present empty section trains the writer to skip the heading."""
    chapters = project / "manuscript" / "chapters"
    (chapters / "chapter-02.md").write_text("# Chapter 2\n\nThe vein rolled and she tried again.\n", encoding="utf-8")
    assert "## Already used in this book" not in build_chapter_brief(project, 3)


def test_the_brief_still_refuses_to_hand_over_whole_earlier_chapters(project: Path):
    """The fix is a list of repeats, not the manuscript. Pasting chapters 1..N-1 into
    every brief would blow the context and bury the outline the writer must follow.
    Chapter 2's tail is allowed in — it always was; chapter 1's opening is not."""
    brief = build_chapter_brief(project, 3)
    assert "SENTINEL-1" not in brief
    assert "SENTINEL-2" not in brief


def test_the_brief_shows_the_ground_the_book_has_already_covered(project: Path):
    """The reader's worst structural finding on books/prova-2: chapter 3 repeats
    chapter 1 beat for beat — page arrives, authority disbelieves, an elderly man
    desaturates, suction fails, the number climbs back, fatigue is blamed.

    The writer could not have known. The outline was read only to cut out this
    chapter's own section, so nothing ever told it what the book had already done.
    """
    brief = build_chapter_brief(project, 3)
    section = brief.split("## What the book has already covered")[1]
    assert "Chapter 1: The Watch Room" in section
    assert "Chapter 2: The Records Office" in section


def test_the_ground_covered_is_headings_and_not_the_outline_body(project: Path):
    """Whole sections would put chapters 1..39 in front of a chapter-40 writer and
    bury the one section it must follow. test_brief.py pins this from the other side."""
    brief = build_chapter_brief(project, 3)
    assert "She takes the night shift" not in brief
    assert "She is called back to the ward" in brief


def test_the_first_chapter_has_no_ground_behind_it(project: Path):
    assert "## What the book has already covered" not in build_chapter_brief(project, 1)
