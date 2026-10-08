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

The `## Brief contract check` is the orchestrator's small, cumulative register,
not a new artifact. For each `BLOCK`, give it an ID, quote the brief, state
whether the constraint is `exact` or `approximate`, list every affected
outline chapter and ledger row, name the dependent event or turn, and mark the
ticket `OPEN` or `CLOSED` with the closing evidence. Keep the register in the
outline even when the verifier packet is rebuilt. The fresh verifier must
receive only the neutral brief, current outline facts and current ledger facts;
omit this register's ticket IDs, statuses, verdicts, repair history and any
claim that an earlier check passed.

Use this precision rule when classifying a temporal contract. Explicit dates,
clock times, travel intervals, counts, schedules and wording such as
`exactly` are exact. A bare human duration such as "twelve years" is not an
exact anniversary unless the brief specifies that precision or supplies a
date-dependent requirement. Do not weaken an exact constraint, and do not
turn an ordinary approximate duration into a BLOCK by assuming an anniversary.
A chapter time span bounds the chapter; it does not place every event at the
span's opening. When the premise depends on an event, anchor that event inside
the span and record its prerequisite event, time and exception (if any) in the
outline and ledger. Apply this only to premise-dependent triggers; do not
require a domain-specific event table for every book.

When the host can isolate a fresh read-only context, have it verify the brief,
outline and ledger comparison before accepting the outline. Build a neutral
packet from the approved constraints, current chapter plan and canonical ledger
facts. Exclude the orchestrator's brief-check verdicts, earlier reviewer reports,
repair history and claims that the plan already passed, including on a retry.
Those are provenance for the orchestrator, not instructions or evidence for the
fresh verifier. Request a concise verdict with exact conflicting passages and
their chapter/ledger references plus a compact coverage list; do not ask for a
new outline, a recap of the full plan or a general literary critique here.
Record the context's completed result and evidence in that same section; a
pending call cannot be recorded as verification. If isolation is unavailable, record
`verification: degraded (not independent)`; do not invent a passing result.

If a fresh verification returns `BLOCK`, first consolidate every finding from
that result and scan all of their dependent outline and ledger references.
Apply one bounded whole-plan repair batch to the outline and ledger, including
all occurrences of each affected trigger, before requesting another fresh
verification. Do not spend retries repairing one row at a time. Run one fresh
neutral coverage check after the batch. If an exact contract ticket remains
open, keep Phase 2 blocked and preserve the complete `OPEN` register; do not
dispatch Phase 3. An approximate-duration warning must remain labelled as a
warning and cannot be silently converted into a repaired brief.

## Rules

- Every chapter has a job no other chapter does. If two chapters share one, merge them now; it is cheaper than cutting later.
- Vary the internal shape of consecutive chapters so a reader cannot predict the next one's template.
- The opening promises what the book will actually deliver, and the ending turn pays it.
- The planned chapter lengths must add up to the length contract. If they do not, fix the plan before drafting.
- The brief contract check is a dedicated pre-draft gate, separate from word-count arithmetic and literary preference. Phase 3 cannot begin while its status is `BLOCK`, while an exact ticket is `OPEN`, or while the verification record is missing. A host without isolation may proceed only with the explicitly recorded `degraded (not independent)` status; it must not turn that limitation into a fabricated pass. A verifier pass requires complete chapter, trigger, timeline and world-rule coverage, not merely a self-consistent ledger.
