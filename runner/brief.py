"""The chapter brief: the one document the writer sees.

Assembled deterministically from project files, never by a model: the chapter's
own section of the outline, the story engine, the characters, the tail of the
previous chapter, and the genre constants. Everything else stays out of the
writer's context on purpose (ADR 0001, decision 7).
"""

from __future__ import annotations

from pathlib import Path
import re

from runner.constants import load_genre_profile
from runner.filesystem import load_state_summary

TAIL_WORDS = 300
OUTLINE_PATH = "artifacts/05-outline.md"
ALWAYS_INCLUDE = (
    ("artifacts/02-story-engine.md", "Story engine"),
    ("artifacts/03-characters.md", "Characters"),
)
FIRST_CHAPTER_NOTE = "(This is the first chapter. Nothing came before it.)"

_HEADING = re.compile(r"^(#{1,6})\s*(.*?)\s*$")
_WORD = re.compile(r"\S+")

# A chapter marker is a heading (`## Chapter 3: Title`) or, because real architecture runs
# produced it, a bold line (`**Capítulo 3 — Título**`). English and Portuguese.
CHAPTER_MARK = re.compile(
    r"^\s*(?:(?P<hashes>#{1,6})\s*(?:#{1,6}\s+)?(?:\*\*\s*)?|\*\*\s*)(?:chapter|cap[ií]tulo|cap\.?)\s*0*(?P<number>\d+)\b",
    re.IGNORECASE,
)


def chapter_markers(outline: str):
    """Prefer actual headings for a chapter; retain legacy bold-only chapters.

    An outline may recap chapters in bold before its detailed chapter headings.
    Those summaries must not become extra chapters or the writer's brief.
    """
    matches = [(index, match) for index, line in enumerate(outline.splitlines())
               if (match := CHAPTER_MARK.match(line))]
    headings = [(index, match) for index, match in matches if match.group("hashes")]
    headed_numbers = {int(match.group("number")) for _, match in headings}
    return [(index, match) for index, match in matches
            if match.group("hashes") or int(match.group("number")) not in headed_numbers]


def chapter_word_limits(project: Path) -> tuple[int, int] | None:
    """Recognize explicit per-chapter ranges, never a whole-book total.

    Free-form requests remain supported; this check only applies when the author
    explicitly says e.g. '350 to 500 words each' or '350-500 palavras por capítulo'.
    """
    idea = load_state_summary(project).get("idea", "")
    match = re.search(r"\b(\d+)\s*(?:to|a|[-–—])\s*(\d+)\s+(?:words|palavras)\s+(?:each|per\s+chapter|por\s+cap[ií]tulo|cada)\b", idea, re.I)
    if match:
        low, high = map(int, match.groups())
        if 0 < low <= high:
            return low, high
    return None


def build_chapter_brief(project: Path, chapter: int, *, write: bool = True) -> str:
    summary = load_state_summary(project)
    genre = summary.get("genre", "")
    profile = load_genre_profile(genre)
    explicit_limits = chapter_word_limits(project)
    low, high = explicit_limits or (profile.words_per_chapter_min, profile.words_per_chapter_max)
    length_rule = ("The author's explicit range is required, including the heading."
                   if explicit_limits else "Use the outline's target if it specifies one.")

    outline_path = project / OUTLINE_PATH
    if not outline_path.exists():
        raise ValueError(f"outline not found at {outline_path}")
    section = extract_chapter_section(outline_path.read_text(encoding="utf-8"), chapter)

    previous_tail = ""
    if chapter > 1:
        previous = project / "manuscript" / "chapters" / f"chapter-{chapter - 1:02d}.md"
        if previous.exists():
            previous_tail = tail_words(previous.read_text(encoding="utf-8"), TAIL_WORDS)

    parts = [
        f"# Brief: Chapter {chapter}",
        "",
        "## Constants",
        "",
        f"- Book language: {summary.get('language') or 'infer from the idea'}. Write all prose in this language.",
        f"- Genre profile: {profile.key} (declared genre: {genre or 'unspecified'})",
        f"- Target length: {low}-{high} words. {length_rule}",
        f"- Dialogue share: {profile.dialogue_min_pct}-{profile.dialogue_max_pct}% of the chapter.",
        "",
        "## This chapter in the outline",
        "",
        section.strip(),
        "",
    ]
    if summary.get("idea"):
        parts += ["## Original author request", "", summary["idea"], "",
                  "Preserve explicit length, chapter-count, and ending requirements from this request. "
                  "They override genre defaults.", ""]
    for relative, heading in ALWAYS_INCLUDE:
        path = project / relative
        if path.exists():
            parts += [f"## {heading}", "", path.read_text(encoding="utf-8").strip(), ""]
    retry = project / "work" / f"retry-chapter-{chapter:02d}.md"
    if retry.is_file():
        parts += ["## Feedback from the previous attempt", "", retry.read_text(encoding="utf-8"), ""]
    editorial = project / "work" / "editorial-revision.md"
    if editorial.is_file():
        parts += ["## Whole-book editorial revision", "", editorial.read_text(encoding="utf-8"), ""]
        from runner.revision import revision_context
        parts += [revision_context(project, chapter)]
        previous_draft = project / "manuscript" / "chapters" / f"chapter-{chapter:02d}.md"
        if previous_draft.is_file():
            parts += ["## Previous version to revise", "", previous_draft.read_text(encoding="utf-8"), ""]
    notes = project / "work" / "author-notes.md"
    if notes.exists() and notes.read_text(encoding="utf-8").strip():
        parts += [
            "## Author notes",
            "",
            "The author asked for these while reading earlier results. They override the defaults above.",
            "",
            notes.read_text(encoding="utf-8").strip(),
            "",
        ]
    parts += [
        "## Where the previous chapter left the reader",
        "",
        previous_tail or FIRST_CHAPTER_NOTE,
        "",
    ]
    brief = "\n".join(parts)

    if write:
        briefs_dir = project / "briefs"
        briefs_dir.mkdir(parents=True, exist_ok=True)
        (briefs_dir / f"chapter-{chapter:02d}.md").write_text(brief, encoding="utf-8")
    return brief


def extract_chapter_section(outline: str, chapter: int) -> str:
    """Return the marker line + body of ``chapter`` from a Markdown outline.

    Accepts ``Chapter N`` / ``Capítulo N`` / ``Cap. N`` as a heading at any level or as a
    bold line. The section ends at the next chapter marker, or at the next heading of the
    same or a higher level (any heading, when the marker was a bold line).
    """
    lines = outline.splitlines()
    start = -1
    level = 0
    markers = dict(chapter_markers(outline))
    for index, match in markers.items():
        if int(match.group("number")) == chapter:
            start = index
            level = len(match.group("hashes") or "")
            break
    if start == -1:
        raise ValueError(f"chapter {chapter} not found in outline")
    end = len(lines)
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if index in markers:
            end = index
            break
        heading = _HEADING.match(line)
        if heading and (level == 0 or len(heading.group(1)) <= level):
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def tail_words(text: str, count: int) -> str:
    """Last ``count`` words of ``text`` with the original line breaks preserved."""
    spans = list(_WORD.finditer(text))
    if len(spans) <= count:
        return text.strip()
    return text[spans[-count].start() :].strip()
