# Genesis Score

The rubric that tells the revision what to fix, and the final report that tells the author where the book stands.

When to load: Phase 5 (rubric gate) and Phase 6 (final score). Roles: rubric evaluator scores; orchestrator calibrates and reports.

## What it is for

The score answers one question: would this manuscript survive demanding readers, a skeptical agent, and the shelf it claims? It measures craft risk. It does not predict sales: commercially huge books have scored low on craft and strong books have sold little. Use it to aim revision, never as a promise.

The reader panel decides whether the book holds its audience. This rubric decides what to fix. Both are gates in Phase 5; both appear in the final report.

## Order

1. Phase 4 audit first. Never score before the adversarial audit.
2. Rubric evaluators follow `references/scoring/evaluator-protocol.md`: fresh context, no targets, no earlier scores.
3. The orchestrator calibrates and applies `project.quality_target` (default 8.5) afterwards.

## Dimensions

| # | Dimension | Weight | Measures |
|---|---|---|---|
| 1 | Originality | 1.1 | premise, lens and execution beyond stale imitation |
| 2 | Theme | 1.0 | depth of the central question; resonance beyond plot |
| 3 | Characters | 1.2 | wound, desire, need, contradiction, memorability |
| 4 | Prose | 1.0 | precision, texture, rhythm, freedom from cliche and machine tells |
| 5 | Pacing | 1.0 | tension control, variation, forward pull |
| 6 | Emotion | 1.1 | whether the intended feeling actually lands |
| 7 | Coherence | 0.9 | logic, continuity, causality |
| 8 | Market | 0.8 | comp clarity, audience legibility, packaging viability |
| 9 | Voice | 1.1 | recognizable, distinct, durable over hundreds of pages |
| 10 | Opening | 0.8 | first-page grip, first-chapter promise, payoff by the end |

## Scoring rules

- The baseline is competence, not excellence. A clean, forgettable chapter is a 6.
- Above 8.0 needs quoted evidence; above 9.0 needs at least two pieces.
- Evidence is textual, structural or reader-impact (from panel verdicts, which the orchestrator may attach to the Emotion and Pacing evidence after scoring, never before).
- Prose cannot score above 7.5 while any tell in the book's tells file exceeds its ceiling in more than a quarter of the chapters.
- Market clarity never compensates for literary weakness.

## Calculation

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
