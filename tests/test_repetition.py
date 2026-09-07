"""What the book has already used, found without asking a model.

Found by reading books/prova-2 straight through on 2026-09-07. The product scored
that run 10.0/10 and the sentence "The coffee was bad and she drank all of it"
appears verbatim in chapter 1, chapter 2 and chapter 3 — twice in scenes with no
coffee in them. Nothing in the pipeline could see it: the judge is blind by design
(ADR 0001) and the writer only ever receives the previous chapter's last 300 words,
so three different calls wrote the same sentence without knowing the other two had.

This is the cheap half of the fix. Repetition across chapters is a fact about
strings, so it costs no provider call and cannot be talked out of its finding.
"""

from pathlib import Path

import pytest

from runner.repetition import reuse_against

COFFEE = "The coffee was bad and she drank all of it."
CORPUS = Path(__file__).resolve().parent.parent / "books" / "prova-2" / "manuscript" / "chapters"


def test_a_sentence_the_book_already_used_is_found():
    earlier = {1: f"She checked the monitor again. {COFFEE} The corridor was empty."}
    candidate = f"The tape stuck to her glove. {COFFEE} She wrote the time down."
    assert [found.text for found in reuse_against(candidate, earlier)] == [COFFEE]


def test_the_finding_says_which_chapter_used_it_first():
    """The writer needs somewhere to look, and 'chapter 1' is that somewhere."""
    earlier = {1: "Nothing repeats here.", 4: f"{COFFEE} She went back to the desk."}
    assert reuse_against(f"{COFFEE}", earlier)[0].first_used_in == 4


def test_a_chapter_that_repeats_nothing_is_clean():
    earlier = {1: "She checked the monitor again. The corridor was empty."}
    assert reuse_against("The vein rolled. She withdrew and tried again.", earlier) == []


def test_a_novel_is_allowed_to_say_yes_twice():
    """The finding has to be worth acting on. Ordinary short dialogue is not a defect,
    and a detector that reports it is one nobody will read twice."""
    earlier = {1: "“Yes.” “No.” “I know.” “Her pressure?” Nora looked at him."}
    candidate = "“Yes.” “No.” “I know.” “Her pressure?” Nora looked at him."
    assert reuse_against(candidate, earlier) == []


def test_an_abbreviation_is_not_a_sentence():
    """Mr., Dr., Mrs. and St. all ended a sentence in the first version, so the same
    fragment came back as a repeat in every chapter and buried the real findings."""
    earlier = {1: "Mr. Bell was seventy-eight. Dr. Reyes had gone home."}
    candidate = "Mr. Bell slept. Dr. Reyes was paged."
    assert [found.text for found in reuse_against(candidate, earlier)] == []


def test_a_short_line_becomes_a_finding_once_it_is_a_refrain():
    """Two pager buzzes are a hospital. Five are the book's only lever for dread."""
    earlier = {1: "The pager vibrated again. She stood.", 2: "The pager vibrated again. He looked up."}
    found = reuse_against("The pager vibrated again. The corridor was dark.", earlier)
    assert [(f.text, f.times) for f in found] == [("The pager vibrated again.", 3)]


@pytest.mark.skipif(not CORPUS.is_dir(), reason="books/ is not committed; this guards the local corpus")
def test_the_book_that_scored_ten_out_of_ten_is_caught_at_chapter_two():
    """The whole point, measured on the run that passed every gate.

    Checking chapter 2 against chapter 1 has to surface the coffee sentence — that
    is the moment the writer of chapter 3 could have been told, and was not.
    """
    chapters = {n: (CORPUS / f"chapter-{n:02d}.md").read_text(encoding="utf-8") for n in (1, 2, 3)}
    found = reuse_against(chapters[2], {1: chapters[1]})
    assert COFFEE in [item.text for item in found]


@pytest.mark.skipif(not CORPUS.is_dir(), reason="books/ is not committed; this guards the local corpus")
def test_real_prose_does_not_drown_the_finding_in_noise():
    """The first version reported 27 items for chapter 2, of which 26 were "Yes.",
    "Mr." and "she asked." A report nobody can read is a report nobody reads."""
    chapters = {n: (CORPUS / f"chapter-{n:02d}.md").read_text(encoding="utf-8") for n in (1, 2, 3)}
    found = reuse_against(chapters[3], {1: chapters[1], 2: chapters[2]})
    assert found, "the corpus is known to repeat itself; finding nothing means the detector broke"
    for item in found:
        assert len(item.text.split()) >= 4, f"too small to act on: {item.text!r}"
        assert not item.text.rstrip(".").endswith(("Mr", "Dr", "Mrs", "St")), item.text


def test_a_phrase_the_book_opens_sentences_with_over_and_over_is_found():
    """Not every repeat is verbatim. On books/prova-2 the same rhetorical move appears
    seven times across four characters — "That isn't an answer", "That wasn't my
    question", "That isn't what I asked" — and no two are the same string.

    Sentence openings catch what exact matching cannot: "Nora looked at" opens twenty
    sentences in three chapters. A reader feels that; a chapter-blind judge cannot.
    """
    from runner.repetition import repeated_openings

    chapters = {n: "Nora looked at him. Nora looked at the pager. The vein rolled." for n in (1, 2, 3)}
    assert [item.phrase for item in repeated_openings(chapters)] == ["nora looked at"]


def test_an_opening_used_once_or_twice_a_chapter_is_just_writing():
    from runner.repetition import repeated_openings

    chapters = {n: "He looked at her. The corridor was empty." for n in (1, 2, 3)}
    assert repeated_openings(chapters) == []


def test_the_threshold_scales_with_the_length_of_the_book():
    """Five uses across three chapters is a tic; across forty it is nothing. A fixed
    count would flood a long book with findings and miss them in a short one."""
    from runner.repetition import repeated_openings

    three = "Nora looked at him. Nora looked at the door. Nora looked at the clock."
    short = {n: three for n in (1, 2, 3)}
    long_book = dict.fromkeys(range(1, 41), "The corridor was empty.")
    long_book[1] = three
    assert [item.times for item in repeated_openings(short)] == [9]
    assert repeated_openings(long_book) == []


@pytest.mark.skipif(not CORPUS.is_dir(), reason="books/ is not committed; this guards the local corpus")
def test_the_corpus_tic_is_caught_and_ordinary_staging_is_not():
    from runner.repetition import repeated_openings

    chapters = {n: (CORPUS / f"chapter-{n:02d}.md").read_text(encoding="utf-8") for n in (1, 2, 3)}
    phrases = [item.phrase for item in repeated_openings(chapters)]
    assert "nora looked at" in phrases
    assert "the pager vibrated" in phrases
    assert "he looked at" not in phrases
