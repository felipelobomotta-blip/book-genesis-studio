"""The per-chapter loop.

writer -> disruptor (when the genre wants it) -> blind judge -> [editor -> judge]*
until the reader would turn the page and the new draft is not worse than the one
before it, or the genre's revision budget is spent. The runner owns every file;
the models only ever see text and return text (ADR 0001). No human is required;
``human_checkpoint=True`` restores the pause after chapter 1 (ADR 0002).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from typing import Callable, Dict, List, Optional, Protocol

from runner.adapters import Adapter, AdapterError
from runner.activity import complete_with_activity
from runner.brief import TAIL_WORDS, build_chapter_brief, tail_words, chapter_word_limits
from runner.constants import GenreProfile, load_genre_profile
from runner.filesystem import load_state_summary, set_human_checkpoint_required, update_state_value
from runner.history import load_manifest, project_relative, record_draft, reserve_attempt, sha256, write_manifest
from runner.judge import SingleJudge, Verdict

from runner.resources import resource_root

REPO_ROOT = resource_root()
AGENTS_DIR = REPO_ROOT / "agents"
FIRST_CHAPTER_SLUG = "chapter-01"

FLAG_MEANINGS = {
    "hook": "the first or last lines did not pull",
    "dialogue": "people sound alike, or say exactly what they mean",
    "pacing": "the reader skimmed",
    "ai_pattern": "it reads like a machine: balanced triplets, tidy morals, every metaphor explained",
    "exposition": "the reader was told instead of shown",
    "voice": "the narrator went generic",
    "continuity": "something contradicted what the reader had just read",
}

RUNNER_CONTRACT = (
    "# RUNNER CONTRACT (read this first)\n\n"
    "You are running inside the Book Genesis runner. You have NO tools: you cannot read, open, "
    "write, or update files, and there is no orchestrator to report to. Ignore every instruction "
    "below that asks you to do any of those things. Everything you need is in this message, and "
    "the runner saves what you return.\n\n"
)

_LEVEL_ONE_HEADING = re.compile(r"^#\s+\S")
_NOTES_HEADING = re.compile(
    r"^\s*(?:#{1,6}\s+|\*\*)(?:craft notes?|writer'?s notes?|author'?s notes?|self[- ]report|"
    r"notes? (?:for|to) the \w+|notes?)\b",
    re.IGNORECASE,
)
_OUTER_FENCE = re.compile(r"^```[a-zA-Z]*[ \t]*\r?\n(.*)\r?\n```\s*$", re.DOTALL)


class Judge(Protocol):
    label: str

    def judge(
        self,
        prose: str,
        previous_tail: str,
        genre: str,
        *,
        previous_draft: Optional[str] = None,
        reader: str = "",
    ) -> Verdict: ...


class AwaitingHuman(RuntimeError):
    """Human mode only: chapter 1 has to be read by a person before chapter 2 is written."""

    def __init__(self, chapter_path: Path, marker: Path) -> None:
        super().__init__(
            f"A human has to read {chapter_path} before chapter 2 is written. "
            f"When it holds up, run: book-genesis approve <project> {FIRST_CHAPTER_SLUG}"
        )
        self.chapter_path = chapter_path
        self.marker = marker


@dataclass
class ChapterResult:
    chapter: int
    accepted: bool
    status: str
    cycles: int
    draft_path: Optional[Path]
    verdicts: List[Verdict] = field(default_factory=list)
    #: Continuity findings the repair pass could not resolve. An accepted chapter
    #: may carry them; they belong in the report rather than in silence.
    unresolved_continuity: List[dict] = field(default_factory=list)


def approve(project: Path, slug: str) -> Path:
    approvals = project / "approvals"
    approvals.mkdir(parents=True, exist_ok=True)
    marker = approvals / f"{slug}.approved"
    marker.write_text("approved by a human reader\n", encoding="utf-8")
    return marker


def resolve_human_checkpoint(project: Path, *, requested: bool = False) -> bool:
    """Return the durable human-checkpoint requirement for this project.

    ``--human`` is an opt-in for a project, not only for the process that happened
    to create its first chapter. Older projects may have been left with the
    historical ``awaiting_human`` status before the opt-in flag existed; adopt
    that state on the first resume so they cannot be advanced accidentally.
    """
    summary = load_state_summary(project)
    required = requested or summary.get("human_checkpoint_required") == "true" or summary.get("status") == "awaiting_human"
    if required and summary.get("human_checkpoint_required") != "true":
        set_human_checkpoint_required(project, True)
    return required


def run_chapter(
    project: Path,
    chapter: int,
    adapters: Dict[str, Adapter],
    *,
    models: Optional[Dict[str, str]] = None,
    judge: Optional[Judge] = None,
    human_checkpoint: bool = False,
    progress: Optional[Callable[[str], None]] = None,
    seed_draft: Optional[str] = None,
    revise_on_flags: bool = False,
) -> ChapterResult:
    """Run one chapter through the loop.

    With ``seed_draft`` (polish mode, ADR 0006) the loop starts from existing
    prose instead of calling the writer: the seed becomes draft 1 and the
    blind judge decides whether the editor gets a turn at all. With
    ``revise_on_flags`` the editor also takes a pass on chapters the judge
    would still turn the page on but flagged; the ``vs_previous`` guard keeps
    the original whenever a revision does not improve it.
    """
    models = models or {}
    say = progress or (lambda _message: None)
    if resolve_human_checkpoint(project, requested=human_checkpoint) and chapter > 1:
        marker = project / "approvals" / f"{FIRST_CHAPTER_SLUG}.approved"
        if not marker.exists():
            raise AwaitingHuman(project / "manuscript" / "chapters" / f"{FIRST_CHAPTER_SLUG}.md", marker)

    if judge is None:
        judge = SingleJudge(adapters["judge"], models.get("judge", ""))

    summary = load_state_summary(project)
    genre = summary.get("genre", "")
    author_constraints = ("\n\n# AUTHOR REQUIREMENTS\n\n" + summary.get("idea", "") +
                          "\nBook language: " + summary.get("language", "") +
                          "\nPreserve the author's requested length, chapter count, and ending. "
                          "These override genre defaults.\n")
    notes_path = project / "work" / "author-notes.md"
    if notes_path.is_file():
        author_constraints += "\n# AUTHOR NOTES\n" + notes_path.read_text(encoding="utf-8")
    reader = summary.get("audience", "")
    profile = load_genre_profile(genre)
    previous_tail = _previous_tail(project, chapter)

    # Provider failures must happen before the immutable attempt marker is written.
    # Otherwise an unauthenticated CLI leaves a misleading pending attempt behind.
    for adapter in adapters.values():
        preflight = getattr(adapter, "preflight", None)
        if callable(preflight):
            preflight()
    if judge is not None:
        for member in getattr(judge, "members", []):
            preflight = getattr(getattr(member, "adapter", None), "preflight", None)
            if callable(preflight):
                preflight()

    drafts_dir = project / "manuscript" / "drafts" / f"chapter-{chapter:02d}"
    evaluations_dir = project / "evaluations"
    if seed_draft is None:
        seed_draft = _resumable_length_draft(project, chapter)

    from runner.revision import ensure_revision_plan, revision_context
    editorial = project / "work" / "editorial-revision.md"
    existing_chapter = project / "manuscript" / "chapters" / f"chapter-{chapter:02d}.md"
    rewrite = project / "work" / f"rewrite-chapter-{chapter:02d}.pending"
    if editorial.is_file() and existing_chapter.is_file() and rewrite.exists():
        ensure_revision_plan(project, adapters["editor"], models.get("editor", ""), say)
    author_constraints += revision_context(project, chapter)
    from runner.continuity import memory_before, memory_context, verify_candidate, select_facts
    memory_adapter = adapters.get("continuity")
    facts = (memory_before(project, chapter, memory_adapter, models.get("continuity", ""))
             if memory_adapter is not None else [])
    continuity_context = memory_context(select_facts(facts, build_chapter_brief(project, chapter, write=False))) if facts else ""
    author_constraints += continuity_context

    # Reserve before invoking writer/judge: a crashed/manual provider leaves a
    # durable pending attempt and the retry gets a new immutable filename.
    attempt_id, attempt_sequence = reserve_attempt(project, chapter)
    if seed_draft is not None:
        say(f"chapter {chapter}: polish: seeding from existing prose ({len(seed_draft.split())} words)")
        draft = clean_chapter(seed_draft)
    elif editorial.is_file() and existing_chapter.is_file() and rewrite.exists():
        say(f"chapter {chapter}: applying the whole-book audit to the saved chapter")
        prompt = (RUNNER_CONTRACT + "Edit the saved chapter only where the audit requests a concrete change. "
                  "Preserve what already works, factual continuity, names, and the ending. Do not add unrelated "
                  "creative flourishes or rewrite the whole plot. Return only the complete revised chapter, "
                  "starting with its existing heading.\n\n" + author_constraints +
                  "\n\n# AUDIT TO ADDRESS\n\n" + editorial.read_text(encoding="utf-8") +
                  "\n\n# SAVED CHAPTER\n\n" + existing_chapter.read_text(encoding="utf-8"))
        draft = clean_chapter(complete_with_activity(adapters["editor"], prompt,
                              model=models.get("editor", ""), task=f"Chapter {chapter} audit editor"))
    else:
        brief = build_chapter_brief(project, chapter) + continuity_context
        say(f"chapter {chapter}: writer ({adapters['writer'].name}{' ' + models['writer'] if models.get('writer') else ''})...")
        draft = clean_chapter(
            complete_with_activity(adapters["writer"], writer_prompt(brief, chapter, genre, profile), model=models.get("writer", ""), task=f"Chapter {chapter} writer")
        )
        say(f"chapter {chapter}: writer done, {len(draft.split())} words")
        say("Draft preview: " + " ".join(draft.splitlines()[1:]).strip()[:240])
        if profile.disruptor_default and "disruptor" in adapters:
            say(f"chapter {chapter}: disruptor...")
            draft = clean_chapter(
                complete_with_activity(adapters["disruptor"], disruptor_prompt(draft, chapter, genre) + author_constraints, model=models.get("disruptor", ""), task=f"Chapter {chapter} reviser")
            )
            say(f"chapter {chapter}: disruptor done, {len(draft.split())} words")

    draft = _fit_requested_length(project, chapter, draft, adapters, models, attempt_id, say)
    draft_number = 1
    draft_path = _attempt_draft_path(drafts_dir, attempt_id, attempt_sequence, draft_number)
    _write(draft_path, draft)
    record_draft(project, chapter, attempt_id, draft_path)
    say(f"chapter {chapter}: judge ({getattr(judge, 'label', 'judge')})...")
    verdict = judge.judge(draft, previous_tail, genre, reader=reader)
    verdict_path = _attempt_verdict_path(evaluations_dir, chapter, attempt_id, attempt_sequence, draft_number)
    _write(verdict_path, verdict.raw)
    say(f"chapter {chapter}: judge says {_verdict_line(verdict)}")
    verdicts = [verdict]

    best, best_verdict, best_draft_path, best_verdict_path = draft, verdict, draft_path, verdict_path
    accepted = _accepted(verdict)
    #: Source-backed continuity findings the repair pass could not resolve. They
    #: travel to the report so an accepted chapter never hides a known problem.
    unresolved_continuity: List[dict] = []
    cycles = 0
    while cycles < profile.max_revision_cycles and (not accepted or (revise_on_flags and best_verdict.flags)):
        cycles += 1
        say(f"chapter {chapter}: editor, cycle {cycles} of {profile.max_revision_cycles} (modes: {', '.join(best_verdict.flags) or 'stopped_at only'})...")
        candidate = clean_chapter(
            complete_with_activity(adapters["editor"],
                editor_prompt(best, best_verdict, chapter, genre, profile) + author_constraints,
                model=models.get("editor", ""),
                task=f"Chapter {chapter} editor",
            )
        )
        candidate = _fit_requested_length(project, chapter, candidate, adapters, models, attempt_id, say)
        draft_number += 1
        draft_path = _attempt_draft_path(drafts_dir, attempt_id, attempt_sequence, draft_number)
        _write(draft_path, candidate)
        record_draft(project, chapter, attempt_id, draft_path)
        say(f"chapter {chapter}: judge compares draft {draft_number} with the previous best...")
        verdict = judge.judge(candidate, previous_tail, genre, previous_draft=best, reader=reader)
        verdict_path = _attempt_verdict_path(evaluations_dir, chapter, attempt_id, attempt_sequence, draft_number)
        _write(verdict_path, verdict.raw)
        say(f"chapter {chapter}: judge says {_verdict_line(verdict)}")
        verdicts.append(verdict)
        if verdict.vs_previous != "worse":
            best, best_verdict, best_draft_path, best_verdict_path = candidate, verdict, draft_path, verdict_path
        elif _accepted(best_verdict):
            # Polish may seek to remove flags from an already accepted text. Once a
            # candidate is worse, retain the accepted best and stop spending calls.
            break
        accepted = _accepted(best_verdict)

    # The continuity reviewer is separate from the blind reader. It sees facts;
    # the reader continues to receive prose only. Never publish an unchecked repair.
    if accepted and memory_adapter is not None:
        conflicts = verify_candidate(project, chapter, best, facts, memory_adapter, models.get("continuity", ""))
        if conflicts:
            say(f"chapter {chapter}: repairing {len(conflicts)} source-backed continuity finding(s)")
            prompt = (RUNNER_CONTRACT + "Repair only the contradictions below. Preserve the heading, "
                      "unaffected prose, requested length, and ending. Return the complete chapter only.\n"
                      + author_constraints + "\nFINDINGS\n" + json.dumps(conflicts, ensure_ascii=False)
                      + "\nCHAPTER\n" + best)
            candidate = clean_chapter(complete_with_activity(adapters["editor"], prompt,
                model=models.get("editor", ""), task=f"Chapter {chapter} continuity editor"))
            candidate = _fit_requested_length(project, chapter, candidate, adapters, models, attempt_id, say)
            draft_number += 1
            path = _attempt_draft_path(drafts_dir, attempt_id, attempt_sequence, draft_number)
            _write(path, candidate)
            record_draft(project, chapter, attempt_id, path)
            check = judge.judge(candidate, previous_tail, genre, previous_draft=best, reader=reader)
            check_path = _attempt_verdict_path(evaluations_dir, chapter, attempt_id, attempt_sequence, draft_number)
            _write(check_path, check.raw)
            verdicts.append(check)
            remaining = verify_candidate(project, chapter, candidate, facts, memory_adapter, models.get("continuity", ""))
            if _accepted(check) and not remaining:
                best, best_verdict, best_draft_path, best_verdict_path = candidate, check, path, check_path
            else:
                # A failed repair means one of two different things, and they
                # deserve opposite answers.
                #
                # If canonical prose already exists, the new draft is a rewrite
                # that contradicts the book and could not be reconciled: keep the
                # canonical text and block, which is what "never publish an
                # unchecked repair" is for.
                #
                # If nothing is canonical yet, blocking preserves nothing. That is
                # what happened to chapter 3 on 2026-09-07: the blind reader said
                # `turn_page: yes`, the repair failed, and a reader-approved
                # chapter left no text at all — the run scored 8.0 instead of 10.0
                # entirely because of it. Here the accepted draft becomes
                # canonical and carries its unresolved findings into the report.
                # Chapters 1 and 2 of that same run shipped with a recorded
                # `continuity` flag; a visible finding beats a missing chapter.
                canonical = project / "manuscript" / "chapters" / f"chapter-{chapter:02d}.md"
                if canonical.is_file():
                    accepted = False
                    say(f"chapter {chapter}: continuity repair did not pass both checks; "
                        "previous canonical text is preserved")
                else:
                    unresolved_continuity = conflicts
                    say(f"chapter {chapter}: continuity repair did not pass both checks; "
                        f"keeping the accepted draft with {len(conflicts)} unresolved continuity finding(s)")

    label = getattr(judge, "label", "judge")
    if accepted:
        final = project / "manuscript" / "chapters" / f"chapter-{chapter:02d}.md"
        if (final.is_file() and final.read_text(encoding="utf-8") != best and
                (summary.get("status") == "completed" or
                 summary.get("current_phase", "").startswith(("Phase 4:", "Phase 5:", "Phase 6:")))):
            # Invalidate completion before replacing prose. Existing exports and
            # reports remain historical snapshots; resume rechecks the changed book.
            state = project / "PROJECT_STATE.yaml"
            update_state_value(state, "current_phase", "Phase 4: Adversarial Audit")
            update_state_value(state, "status", "in_progress")
            say("The manuscript changed; the whole-book review and delivery must run again.")
        _write(final, best)
        # `status` stays exactly "accepted": score.py, acceptance.py and review.py
        # compare it by equality, and widening the string here would quietly break
        # three call sites. The findings ride alongside it instead.
        result = ChapterResult(chapter, True, "accepted", cycles, final, verdicts, unresolved_continuity)
    else:
        result = ChapterResult(chapter, False, "blocked", cycles, best_draft_path, verdicts)
    _record_attempt(project, chapter, attempt_id, attempt_sequence, result, best_draft_path, best_verdict_path)
    if accepted and memory_adapter is not None:
        from runner.continuity import remember_accepted
        remember_accepted(project, chapter, best, facts, memory_adapter, models.get("continuity", ""))
    _append_run_report(project, result, label)
    say(f"chapter {chapter}: {result.status} after {cycles} revision cycle(s)")
    return result


def _resumable_length_draft(project: Path, chapter: int) -> Optional[str]:
    """Continue a saved length repair unless newer author/revision notes supersede it."""
    attempts = load_manifest(project, chapter)["attempts"]
    if not attempts:
        return None
    latest = attempts[-1]
    relative = latest.get("draft_path", "")
    if latest.get("status") != "drafted" or not isinstance(relative, str):
        return None
    path = (project / relative).resolve()
    expected = (project / "manuscript" / "drafts" / f"chapter-{chapter:02d}").resolve()
    if (not path.is_relative_to(project.resolve()) or path.parent != expected
            or not re.fullmatch(r"attempt-\d+-length-\d+\.md", path.name)
            or not path.is_file() or latest.get("sha256") != sha256(path)):
        return None
    for note in ("author-notes.md", "editorial-revision.md", f"rewrite-chapter-{chapter:02d}.pending",
                 f"retry-chapter-{chapter:02d}.md"):
        changed = project / "work" / note
        if changed.exists() and changed.stat().st_mtime_ns > path.stat().st_mtime_ns:
            return None
    return path.read_text(encoding="utf-8")


def _fit_requested_length(project, chapter, draft, adapters, models, attempt_id, say):
    from runner.revision import revision_context
    continuity = revision_context(project, chapter)
    limits = chapter_word_limits(project)
    if limits is None:
        return draft
    low, high = limits
    for repair in range(3):
        count = len(draft.split())
        if low <= count <= high:
            return draft
        # Keep every out-of-range version before attempting a repair.
        directory = project / "manuscript" / "drafts" / f"chapter-{chapter:02d}"
        number = 1
        saved = directory / f"{attempt_id}-length-{number}.md"
        while saved.exists():
            number += 1
            saved = directory / f"{attempt_id}-length-{number}.md"
        _write(saved, draft)
        record_draft(project, chapter, attempt_id, saved)
        if repair == 2:
            raise AdapterError(f"Chapter {chapter} is saved but still has {count} words; "
                               f"the requested range is {low}-{high}. Length repair stopped after two attempts.")
        say(f"chapter {chapter}: adjusting length ({count} words; requested {low}-{high})")
        if repair == 1 and count > high:
            draft = _select_length_cuts(draft, low, high, adapters["editor"], models.get("editor", ""), chapter, constraints=continuity)
            continue
        target = low + (high - low) // 5 if count > high else (low + high) // 2
        change = (f"DELETE at least {count - target} words. Remove secondary banter and incidental "
                  "description; do not merely swap words. " if count > high else "Develop existing moments without adding new plot threads. ")
        prompt = (RUNNER_CONTRACT + f"This is a strict length-editing task. Rewrite this chapter in about {target} words. "
                  f"{change}Allowed range: {low}-{high} whitespace-separated words INCLUDING the heading. The current text has "
                  f"{count} words. Preserve its language, central events, names, and ending. "
                  "Remove expendable lines when shortening; do not add new plot threads. Return only the full "
                  "revised chapter with the same heading, no commentary.\n\n" + continuity + "\n\n# CHAPTER\n\n" + draft)
        draft = clean_chapter(complete_with_activity(adapters["editor"], prompt, model=models.get("editor", ""),
                                                     task=f"Chapter {chapter} length editor"))
    return draft


def _select_length_cuts(draft, low, high, adapter, model, chapter, *, constraints=""):
    """An editor selects expendable paragraphs; the runner measures each removal.

    Used only after a prose rewrite missed the range. Never truncate a sentence,
    invent text, remove a heading/opening/ending, or bypass the blind reader gate.
    If the suggested cuts cannot meet the range, preserve the draft and fail the
    normal bounded length check. The original is already saved in draft history.
    """
    paragraphs = re.split(r"\n\s*\n", draft.strip())
    prose_ids = [i for i, p in enumerate(paragraphs) if not p.lstrip().startswith("#")]
    if len(prose_ids) < 3:
        return draft
    protected = {prose_ids[0], prose_ids[-1]} | {
        i for i, p in enumerate(paragraphs) if p.lstrip().startswith("#")
    }
    count = len(draft.split())
    numbered = "\n\n".join(
        f"[{i}] ({len(p.split())} words{'; KEEP' if i in protected else ''})\n{p}"
        for i, p in enumerate(paragraphs)
    )
    prompt = (RUNNER_CONTRACT + "You are doing a deletion-only editorial pass. The chapter is too long. "
              f"It has {count} words and must finish between {low} and {high}. Identify whole paragraphs "
              f"that can be removed, totaling at least {count - high} words. Rank the safest deletions first. "
              "Preserve essential events, clues, named facts, examples needed to understand instructions, "
              "dialogue responses needed for coherence, and the ending. Prefer repeated explanations, "
              "incidental description, and redundant banter. Do not select any paragraph marked KEEP. "
              "The runner will stop deleting once the length fits and blind readers will check coherence. "
              'Return only JSON: {"remove_order": [paragraph IDs in priority order]}. No rewritten prose.\n\n' + constraints + "\n\n" + numbered)
    raw = complete_with_activity(adapter, prompt, model=model, task=f"Chapter {chapter} precision length editor")
    try:
        payload = raw.strip()
        if payload.startswith("```"):
            payload = payload.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        order = json.loads(payload)["remove_order"]
        if not isinstance(order, list) or any(type(i) is not int or i < 0 or i >= len(paragraphs) for i in order):
            return draft
    except (ValueError, TypeError, KeyError, IndexError):
        return draft
    removed = set()
    for i in order:
        if i in protected or i in removed:
            continue
        words = len(paragraphs[i].split())
        if count - words < low:
            continue
        removed.add(i)
        count -= words
        if count <= high:
            return "\n\n".join(p for j, p in enumerate(paragraphs) if j not in removed) + "\n"
    return draft


def _verdict_line(verdict: Verdict) -> str:
    return (
        f"turn_page={'yes' if verdict.turn_page else 'no'}, flags=[{', '.join(verdict.flags)}]"
        + (f", vs_previous={verdict.vs_previous}" if verdict.vs_previous != "none" else "")
        + (f", stopped_at={verdict.stopped_at[:60]}" if verdict.stopped_at != "none" else "")
    )


def writer_prompt(brief: str, chapter: int, genre: str, profile: GenreProfile) -> str:
    return (
        RUNNER_CONTRACT
        + _template("book-writer.md")
        + craft_guidance(profile.key)
        + "\n\n# THE BRIEF\n\n"
        + brief.strip()
        + "\n\n# OUTPUT\n\n"
        + f"Return only Chapter {chapter}, as Markdown, starting with a level-1 heading of the form "
        + f"`# Chapter {chapter}: Title`, translated into the book's language (Portuguese: `# Capítulo {chapter}: Título`). Prose only: no craft notes, no self-report, no preamble, no "
        + "commentary before or after the chapter. Stay inside the target length given in the brief. "
        + "The author's explicit range overrides all genre or outline defaults.\n"
    )


def disruptor_prompt(draft: str, chapter: int, genre: str) -> str:
    return (
        RUNNER_CONTRACT
        + _template("book-disruptor.md")
        + f"\n\n# THE CHAPTER (Chapter {chapter}, {genre or 'fiction'})\n\n"
        + draft.strip()
        + "\n\n# OUTPUT\n\n"
        + "Return the full chapter with your disruptions applied, as Markdown, starting with the same "
        + "level-1 heading. Prose only: no report, no list of changes, nothing before or after the chapter.\n"
    )


def editor_prompt(draft: str, verdict: Verdict, chapter: int, genre: str, profile: GenreProfile) -> str:
    flags = [flag for flag in verdict.flags if flag in FLAG_MEANINGS]
    modes = "\n".join(f"- {flag}: {FLAG_MEANINGS[flag]}" for flag in flags) or (
        "- (no mode flagged: work only on the passage where the reader's attention left the page)"
    )
    remember = "\n".join(f"- {item}" for item in verdict.remember) or "- nothing"
    reader_report = (
        "# WHAT A BLIND READER SAID\n\n"
        f"- Would turn the page: {'yes' if verdict.turn_page else 'no'}\n"
        f"- Attention left the page at: {verdict.stopped_at}\n"
        f"- Would still remember tomorrow:\n{remember}\n"
        f"- Modes to run (see MODES in your instructions):\n{modes}\n\n"
    )
    return (
        RUNNER_CONTRACT
        + _template("book-editor.md")
        + craft_guidance(profile.key)
        + "\n\n"
        + reader_report
        + f"# THE CHAPTER (current best draft of Chapter {chapter}, {genre or 'fiction'})\n\n"
        + draft.strip()
        + "\n\n# OUTPUT\n\n"
        + "Return the full revised chapter as Markdown, starting with the same level-1 heading. Touch "
        + "only what the reader flagged and the passage where attention left the page; do not undo what "
        + "already works; do not change facts, names, or the ending. Prose only: no change log, nothing "
        + "before or after the chapter.\n"
    )


def craft_guidance(profile: str) -> str:
    if profile in {"nonfiction", "memoir"}:
        return ("\n\n# FORM-SPECIFIC GUIDANCE\nDevelop one clear question or practical outcome per chapter. "
                "Use concrete demonstrations and track quantities, durations, and examples consistently. "
                "Distinguish supplied facts, interpretation, and explicitly fictional illustrations. "
                "Label fictional examples briefly on first appearance; avoid repeated process disclaimers or explanations of how the book was generated. "
                "Do not invent citations, research, dialogue or biographical events presented as real. "
                "Avoid repeating the previous chapter's lesson or appending a generic moral.\n")
    return ("\n\n# FORM-SPECIFIC GUIDANCE\nGive each scene a concrete desire, credible resistance, "
            "a consequential choice, and a changed situation. Let resistance fit this story's scale. "
            "Differentiate speakers through vocabulary, attention, omissions and motives. "
            "Avoid shared aphoristic voices, repeated mechanism explanations, effortless solutions, "
            "and endings that explain the scene's meaning after the reader already understands.\n")


def clean_chapter(raw: str) -> str:
    """Keep the prose, drop what models add around it: fences, preambles, craft notes."""
    text = raw.strip()
    fence = _OUTER_FENCE.match(text)
    if fence:
        text = fence.group(1).strip()
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if _LEVEL_ONE_HEADING.match(line):
            lines = lines[index:]
            break
        title = line.strip().strip("*").strip()
        if re.fullmatch(r"(?:chapter|cap[ií]tulo)\s+\d+(?:\s*[:—–-]\s*\S.*)?", title, re.I):
            lines = ["# " + title, *lines[index + 1:]]
            break
    for index in range(1, len(lines)):
        if _NOTES_HEADING.match(lines[index]):
            lines = lines[:index]
            break
    while lines and lines[-1].strip() in ("", "---", "***"):
        lines.pop()
    return "\n".join(lines).rstrip() + "\n"


def _accepted(verdict: Verdict) -> bool:
    return verdict.turn_page and verdict.vs_previous != "worse"


def _attempt_draft_path(drafts_dir: Path, attempt_id: str, sequence: int, draft: int) -> Path:
    # Keep the original names for the first run so existing projects and scripts
    # retain their familiar layout. Subsequent runs cannot overwrite those files.
    return drafts_dir / (f"draft-{draft}.md" if sequence == 1 else f"{attempt_id}-draft-{draft}.md")


def _attempt_verdict_path(evaluations_dir: Path, chapter: int, attempt_id: str, sequence: int, draft: int) -> Path:
    stem = f"chapter-{chapter:02d}-judge-{draft}.md" if sequence == 1 else f"chapter-{chapter:02d}-judge-{attempt_id}-{draft}.md"
    return evaluations_dir / stem


def _record_attempt(
    project: Path, chapter: int, attempt_id: str, sequence: int, result: ChapterResult, draft_path: Path, verdict_path: Path
) -> None:
    manifest = load_manifest(project, chapter)
    record = {
        "attempt_id": attempt_id,
        "sequence": sequence,
        "status": result.status,
        "draft_path": project_relative(project, draft_path),
        "verdict_path": project_relative(project, verdict_path),
        "sha256": sha256(draft_path),
    }
    for index, existing in enumerate(manifest["attempts"]):
        if existing.get("attempt_id") == attempt_id:
            manifest["attempts"][index] = record
            break
    else:
        manifest["attempts"].append(record)
    if result.accepted:
        manifest["accepted"] = dict(record)
    write_manifest(project, chapter, manifest)


def _previous_tail(project: Path, chapter: int) -> str:
    if chapter <= 1:
        return ""
    previous = project / "manuscript" / "chapters" / f"chapter-{chapter - 1:02d}.md"
    if not previous.exists():
        return ""
    return tail_words(previous.read_text(encoding="utf-8"), TAIL_WORDS)


def _template(name: str) -> str:
    path = AGENTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"agent template missing: {path}")
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4 :]
    return text.strip()


def _append_run_report(project: Path, result: ChapterResult, judge_label: str) -> None:
    """RUN_REPORT.md is where the human reads afterwards what used to be said at a checkpoint."""
    path = project / "RUN_REPORT.md"
    last = result.verdicts[-1] if result.verdicts else None
    verdict_text = "no verdict"
    if last is not None:
        verdict_text = (
            f"turn_page={'yes' if last.turn_page else 'no'}, flags=[{', '.join(last.flags)}], "
            f"stopped_at={last.stopped_at}"
        )
    unresolved = ""
    if result.unresolved_continuity:
        unresolved = f"; unresolved continuity findings: {len(result.unresolved_continuity)}"
    line = (
        f"- chapter {result.chapter}: {result.status} after {result.cycles} revision cycle(s); "
        f"judge: {judge_label}; last verdict: {verdict_text}{unresolved}; file: {result.draft_path}"
    )
    if not path.exists():
        path.write_text("# Run Report\n\n## Chapter log\n\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)
