"""Prose the book has already used, found by reading it — no provider call.

The judge is blind on purpose (ADR 0001): it sees one chapter and the tail of the
one before. That is right for judging prose and useless for catching a book that
repeats itself, which is a fact about strings and belongs in code.
"""

import re
from dataclasses import dataclass

SENTENCE_END = re.compile(r"(?<=[.!?])[\"'’”]?\s+")
QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})

# A title is not the end of a sentence. Leaving these in split "Mr. Bell was
# seventy-eight" into two, and "Mr." then came back as a repeat in every chapter.
ABBREVIATIONS = ("mr.", "mrs.", "ms.", "dr.", "st.", "prof.", "sgt.", "lt.", "no.", "vs.")

# A sentence is worth reporting when reusing it is a defect rather than English.
# Ten words repeated verbatim is a machine; "Yes." twice is a conversation.
DISTINCT_WORDS = 6
REFRAIN_WORDS = 4
REFRAIN_TIMES = 3


@dataclass(frozen=True)
class Reuse:
    """One sentence this chapter shares with a chapter that came before it."""

    text: str
    first_used_in: int
    times: int = 2


def sentences(text: str) -> list:
    stripped = "\n".join(line for line in text.splitlines() if not line.startswith("#"))
    parts, merged = SENTENCE_END.split(stripped), []
    for part in (p.strip() for p in parts if p.strip()):
        if merged and merged[-1].split()[-1].casefold() in ABBREVIATIONS:
            merged[-1] = f"{merged[-1]} {part}"
        else:
            merged.append(part)
    return merged


def normalise(sentence: str) -> str:
    return " ".join(sentence.translate(QUOTES).casefold().split()).strip("\"' ")


OPENING_WORDS = 3
OPENING_MIN_TIMES = 3
OPENING_PER_CHAPTER = 2.0


@dataclass(frozen=True)
class Opening:
    """A phrase the book keeps starting sentences with."""

    phrase: str
    times: int


def repeated_openings(chapters: dict) -> list:
    """Sentence openings the book leans on, which exact matching cannot see.

    The same move appeared seven times across four characters in books/prova-2 with
    no two wordings alike; "Nora looked at" opened twenty sentences in three chapters.
    The bar is a rate rather than a count, so a forty-chapter book is not flooded with
    findings a three-chapter book would never produce.
    """
    count = {}
    for number in sorted(chapters):
        for sentence in sentences(chapters[number]):
            words = normalise(sentence).split()
            if len(words) > OPENING_WORDS:
                phrase = " ".join(words[:OPENING_WORDS])
                count[phrase] = count.get(phrase, 0) + 1
    limit = max(OPENING_MIN_TIMES, OPENING_PER_CHAPTER * max(len(chapters), 1))
    return sorted(
        (Opening(phrase, times) for phrase, times in count.items() if times >= limit),
        key=lambda item: -item.times,
    )


def worth_reporting(words: int, times: int) -> bool:
    return words >= DISTINCT_WORDS or (words >= REFRAIN_WORDS and times >= REFRAIN_TIMES)


def already_repeated(chapters: dict) -> list:
    """Sentences the book has used more than once, across the chapters given.

    `reuse_against` asks "does this new draft repeat the book"; this asks "what is
    the book already repeating", which is what the writer needs before it drafts.
    """
    first, count, order = {}, {}, []
    for number in sorted(chapters):
        for sentence in sentences(chapters[number]):
            key = normalise(sentence)
            if key not in first:
                first[key], order = number, order + [(key, sentence)]
            count[key] = count.get(key, 0) + 1
    return [
        Reuse(text=sentence, first_used_in=first[key], times=count[key])
        for key, sentence in order
        if count[key] > 1 and worth_reporting(len(key.split()), count[key])
    ]


def accepted_before(project, chapter: int) -> dict:
    """The chapters the book has already accepted, keyed by chapter number."""
    folder = project / "manuscript" / "chapters"
    found = {}
    for number in range(1, chapter):
        path = folder / f"chapter-{number:02d}.md"
        if path.is_file():
            found[number] = path.read_text(encoding="utf-8")
    return found


def reuse_against(candidate: str, earlier: dict) -> list:
    """Sentences in `candidate` that a chapter in `earlier` already used.

    `earlier` maps chapter number to that chapter's accepted text.
    """
    seen, times = {}, {}
    for number in sorted(earlier):
        for sentence in sentences(earlier[number]):
            key = normalise(sentence)
            seen.setdefault(key, number)
            times[key] = times.get(key, 0) + 1

    found, reported = [], set()
    for sentence in sentences(candidate):
        key = normalise(sentence)
        times[key] = times.get(key, 0) + 1
        if key not in seen or key in reported:
            continue
        if worth_reporting(len(key.split()), times[key]):
            reported.add(key)
            found.append(Reuse(text=sentence, first_used_in=seen[key], times=times[key]))
    return found
