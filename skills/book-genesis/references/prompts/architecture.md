# Phase 2: Architecture

Turn the foundation into a chapter plan with momentum, a first page that makes a promise, and a ledger that keeps the facts straight for the whole draft.

When to load: Phase 2. Role: orchestrator as architect, with the continuity specialist.

## Input

Read the approved intake contract in `artifacts/00-brief.md` together with
`artifacts/02-story-engine.md`, `artifacts/03-characters.md`,
`artifacts/04-theme.md`, `artifacts/05-voice.md` and
`artifacts/06-emotional-curve.md`. The brief remains authoritative for the
premise, reader promise, declared time window or duration, and point of view;
the architecture may repair its plan to fit those constraints but may not
rewrite them silently.

## Outputs

- `artifacts/07-outline.md`: macro structure; one entry per chapter with its narrative function, the value shift (what is better or worse by the end), the ending turn, a **scene pressure** marker for the rhythm contract (for example action, dread, grief, comedy, exposition, rest), and the planned word count. Add the tension map and mark where the structural beats fall, using the percentages in `references/patterns/structure-and-emotion.md` converted to word positions for this book's planned length.
- `artifacts/08-opening-strategy.md`: the opening strategy, three to five candidate first lines, the promise the first page makes, and how chapter 1 ends.
- `artifacts/09-continuity-ledger.md`: characters, physical facts, relationships, who knows what and when, places, objects, the timeline and world rules, built from the foundation and outline as `references/specialists/continuity.md` describes.
- `PROJECT_STATE.yaml` updated, including `manuscript.chapter_count_planned`.

Before the outline is accepted, add a `## Brief contract check` section to
`artifacts/07-outline.md`. Read `artifacts/00-brief.md` as the approved intake
source and quote the exact brief text for the premise, reader promise, declared
time window or duration, and point of view. For every planned chapter and every
relevant entry in the seeded ledger (including every timeline row and world-rule
entry), record the matching outline/ledger reference and mark the comparison
`PASS` or `BLOCK`. A `BLOCK` is any chapter, ledger entry or planned turn that
cannot fit the approved premise, reader promise, time window or point of view.
Do not silently amend the brief to fit a contradictory outline; in autonomous
mode, write the repair plan inside the brief-check section and stay in Phase 2
until the outline and ledger fit the existing brief.

When the host can isolate a fresh read-only context, have it verify the brief,
outline and ledger comparison before accepting the outline. Record the context's
result and evidence in that same section. If isolation is unavailable, record
`verification: degraded (not independent)`; do not invent a passing result.

## Rules

- Every chapter has a job no other chapter does. If two chapters share one, merge them now; it is cheaper than cutting later.
- Vary the internal shape of consecutive chapters so a reader cannot predict the next one's template.
- The opening promises what the book will actually deliver, and the ending turn pays it.
- The planned chapter lengths must add up to the length contract. If they do not, fix the plan before drafting.
- The brief contract check is a dedicated pre-draft gate, separate from word-count arithmetic and literary preference. Phase 3 cannot begin while its status is `BLOCK` or while the verification record is missing. A host without isolation may proceed only with the explicitly recorded `degraded (not independent)` status; it must not turn that limitation into a fabricated pass.
