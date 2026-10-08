# Genesis Score

ORCHESTRATOR ONLY. This file contains private gate policy and the final-report format. Never include it in a critic's packet.

When to load: Phase 5 (rubric gate) and Phase 6 (final score). Role: orchestrator calibrates and reports. Rubric evaluators receive only `references/scoring/rubric-criteria.md` and their allowed evidence.

## What it is for

The score answers one question: would this manuscript survive demanding readers, a skeptical agent, and the shelf it claims? It measures craft risk. It does not predict sales: commercially huge books have scored low on craft and strong books have sold little. Use it to aim revision, never as a promise.

The reader panel decides whether the book holds its audience. This rubric decides what to fix. Both are gates in Phase 5; both appear in the final report.

## Order

1. Phase 4 audit first. Never score before the adversarial audit.
2. Assemble fresh-context critic packets under `references/scoring/evaluator-protocol.md`, using `references/scoring/rubric-criteria.md`. Do not send this file or the protocol itself: both contain private gate policy. Omit targets and earlier scores.
3. The orchestrator calibrates and applies `project.quality_target` (default 8.5) afterwards.

## Criteria and evidence

The ten dimensions, weights and evidence requirements live in `references/scoring/rubric-criteria.md`. Keep a single source for them. The orchestrator may attach panel verdicts to the Emotion and Pacing evidence after scores are frozen, never before.

## Calculation

- If any dimension is not assessed or required evidence is missing, report the rubric as incomplete. Do not compute a passing gate from the remaining dimensions.
- Floor: the lowest calibrated dimension.
- Weighted average: the weighted mean of the ten calibrated dimensions.
- Calibration: see `references/scoring/evaluator-protocol.md` (default minus 0.8).
- The rubric gate passes when the calibrated floor is at or above `project.quality_target` and no dimension sits more than 1.0 below it.

## Final report

Save to `artifacts/11-genesis-score.md`, in the author's language:

1. **Where the book stands**, in three plain sentences an author understands without this file.
2. **Completeness.** Chapters and words against the plan; the length gate result; whether the book is labeled complete. "Complete" means the length contract is met (or the intake declared a short form), every planned chapter exists, and the editorial package exists. Quality gates do not change the label; they are reported beside it.
3. **Reader panel.** The final gate read: turn-the-page votes per sampled chapter, remaining defects, what readers remembered.
4. **Rubric.** Raw medians, calibrated scores, floor, weighted average, target, and the gate result.
5. **Gates.** "Gates met", or "Gates not met:" followed by each unmet gate and exactly what is missing.
6. **Independence.** Level, grade, model families, isolation check.
7. **Disagreements** between critics, and confidence.
8. **Next move.** The weakest dimension and the single intervention most likely to raise it.

Never write that the book is a bestseller, will sell, or is ready for publication without a human decision. Write what was measured.
