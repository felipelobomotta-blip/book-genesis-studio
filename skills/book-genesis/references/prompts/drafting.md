# Phase 3: Drafting

Write the manuscript chapter by chapter, in the book's voice, saving each chapter before starting the next.

When to load: Phase 3. Roles: writer drafts; orchestrator runs the checks and the panel.

## Before each chapter: the chapter brief

Assemble `work/briefs/chapter-NN.md` for the writer from files, never from memory:

- the chapter's entry in `artifacts/07-outline.md`, including its scene pressure and planned length;
- the author's approved premise, reader promise and explicit time/POV constraints from `artifacts/00-brief.md`, plus this chapter's single validated timeline row. Check these against the outline's brief-to-plan contract review before dispatch. If the packet says both "one night" and "Morning 2", stop and repair the plan or packet; never send contradictory instructions to the writer or silently relax the author's constraint;
- the approved production length contract: this chapter's planned word range and the manuscript floor and ceiling from intake and `PROJECT_STATE.yaml`;
- the chapter's row in `artifacts/06-emotional-curve.md`: start and end emotion, peak moment, and the anchor the reader should carry away;
- the characters present, from `artifacts/03-characters.md`, with their voice cards;
- the rhythm contract and narrative voice from `artifacts/05-voice.md`;
- the ledger entries the chapter touches, from `artifacts/09-continuity-ledger.md`;
- a compact canonical fact block assembled from those same character and ledger entries: exact names and relationships for referenced cast, the known present-time/date/tide state, and what each character currently knows. Do not invent alternate names, relationships or dates when canon is incomplete; use the existing form and surface the assumption for continuity review;
- the last 300 words or so of the previous chapter.

The brief never contains the rubric, a quality-score target, gate thresholds, panel verdicts or audit findings. The production length contract is allowed because it plans scope; the writer writes for readers and scenes, not for a score.

## Writing

Follow `references/specialists/prose-craft.md` for openings, chapter endings and dialogue, and `references/patterns/prose.md` for the measured ranges. While drafting:

- Hold the rhythm baseline and move inside the envelope only where the outline marks scene pressure.
- Give every chapter at least one thing a reader could still recall tomorrow: a concrete image, a choice that changes how we see someone, or pressure between what a scene says and what it means.
- Trust scene and image. Do not explain the craft move inside the prose.
- Do not run machine-prose checks while writing. Draft first; the tells are for revision.

## After each chapter

1. Save the draft to `work/attempts/chapter-NN/attempt-1.md` and read it back. For a new chapter with no accepted file, create the canonical file only after that read-back. When replacing an existing accepted chapter during revision, stage the draft and use the safe promotion record in `references/prompts/revision-loop.md`; never overwrite an accepted chapter with an ordinary copy.
2. Count its words and update `manuscript.completed_chapters`, `manuscript.word_count_actual` and the running comparison with the plan. After every chapter, record the cumulative count and the projection from the remaining planned chapter lengths. If that projection materially misses the manuscript floor or approaches its ceiling, stop before the next chapter: add a missing scene or turn, or replan the remaining chapter lengths. Do not add padding.
3. Check: the chapter's function is clear, names and facts match the ledger, the voice is recognizable, the ending pulls forward, and the chapter adds something the previous one did not.

## Chapter 1 checkpoint

Run the reader panel on chapter 1 (`references/roles/panel.md`, chapter read). Save `evaluations/panel-chapter-01.md`. If the panel does not reach a majority to turn the page, revise chapter 1 once against the two-vote defects, run the panel again in compare mode, keep the preferred draft, and report both results. Then check in.

## Every fifth chapter

After chapters 5, 10, 15 and so on:

1. Update the ledger and run the continuity check (`references/specialists/continuity.md`). Send any finding to the revision editor as a targeted ticket and fix it before continuing.
2. Run the panel on the latest chapter (chapter read).
3. Review the length trend against the approved contract and the next block's scene work before checking in.
4. Check in.

## Finishing the draft

The phase ends when every planned chapter exists and has been read back. Set `manuscript.length_gate` to `PASS` (within the approved floor and ceiling), `FLAG` (within 10 percent under the floor) or `BLOCK` (further under, or above the ceiling). A book outside its approved range needs targeted expansion or compression before Phase 6 can call its length contract complete. A declared short form uses its own approved range; it does not waive that range or permit silently reclassifying an incomplete novel as a novella.
