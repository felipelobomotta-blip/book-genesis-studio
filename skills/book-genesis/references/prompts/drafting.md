# Phase 3: Drafting

Write the manuscript chapter by chapter, in the book's voice, saving each chapter before starting the next.

When to load: Phase 3. Roles: writer drafts; orchestrator runs the checks and the panel.

## Before each chapter: the chapter brief

Assemble `work/briefs/chapter-NN.md` for the writer from files, never from memory:

- the chapter's entry in `artifacts/07-outline.md`, including its scene pressure and planned length;
- the chapter's row in `artifacts/06-emotional-curve.md`: start and end emotion, peak moment, and the anchor the reader should carry away;
- the characters present, from `artifacts/03-characters.md`, with their voice cards;
- the rhythm contract and narrative voice from `artifacts/05-voice.md`;
- the ledger entries the chapter touches, from `artifacts/09-continuity-ledger.md`;
- the last 300 words or so of the previous chapter.

The brief never contains the rubric, the quality target, panel verdicts or audit findings. The writer writes for readers, not for a score.

## Writing

Follow `references/specialists/prose-craft.md` for openings, chapter endings and dialogue, and `references/patterns/prose.md` for the measured ranges. While drafting:

- Hold the rhythm baseline and move inside the envelope only where the outline marks scene pressure.
- Give every chapter at least one thing a reader could still recall tomorrow: a concrete image, a choice that changes how we see someone, or pressure between what a scene says and what it means.
- Trust scene and image. Do not explain the craft move inside the prose.
- Do not run machine-prose checks while writing. Draft first; the tells are for revision.

## After each chapter

1. Save the draft to `work/attempts/chapter-NN/attempt-1.md`, read it back, then copy it to `manuscript/chapters/chapter-NN.md`.
2. Count its words and update `manuscript.completed_chapters`, `manuscript.word_count_actual` and the running comparison with the plan.
3. Check: the chapter's function is clear, names and facts match the ledger, the voice is recognizable, the ending pulls forward, and the chapter adds something the previous one did not.

## Chapter 1 checkpoint

Run the reader panel on chapter 1 (`references/roles/panel.md`, chapter read). Save `evaluations/panel-chapter-01.md`. If the panel does not reach a majority to turn the page, revise chapter 1 once against the two-vote defects, run the panel again in compare mode, keep the preferred draft, and report both results. Then check in.

## Every fifth chapter

After chapters 5, 10, 15 and so on:

1. Update the ledger and run the continuity check (`references/specialists/continuity.md`). Send any finding to the revision editor as a targeted ticket and fix it before continuing.
2. Run the panel on the latest chapter (chapter read).
3. Compare the running word count with the plan. If the book is heading more than 15 percent under the floor, propose where to expand (a missing turn, a thin subplot) before writing on.
4. Check in.

## Finishing the draft

The phase ends when every planned chapter exists and has been read back. Set `manuscript.length_gate` to `PASS` (at or above the floor), `FLAG` (within 10 percent under it) or `BLOCK` (further under). A book under its floor goes to expansion before Phase 6 can call it complete, unless the intake declared a short form.
