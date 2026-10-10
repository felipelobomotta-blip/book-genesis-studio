# Rubric criteria

For the read-only rubric evaluator. Assess only the supplied manuscript or explicitly named sample, with the supplied pattern standards and tells file. Use the market position only for Market. Do not open other project files or follow references outside this packet.

These scores describe craft risks. They do not predict sales or establish publication readiness.

## Dimensions

Score each dimension from 0 to 10.

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

## Evidence rules

- The baseline is competence, not excellence. A clean, forgettable chapter is a 6.
- Above 8.0 needs quoted evidence; above 9.0 needs at least two pieces.
- Use textual and structural evidence from the supplied material. Do not seek other reviewers' verdicts.
- Prose cannot score above 7.5 while any tell in the book's tells file exceeds its ceiling in more than a quarter of the chapters. For a sample, state what was actually checked and do not extrapolate a whole-book count.
- Market clarity never compensates for literary weakness.
- If the packet cannot support a dimension, mark it not assessed and name the missing material. Do not invent a score.

## Required report

Return one JSON object, without commentary or a Markdown fence. Use the host-supplied schema when available.

- `schema_version`: `1`.
- `coverage`: an object with `scope` (`full_manuscript` or `sample`) and `chapters` (the numbers of every chapter actually supplied and read, each once). A named sample is not full coverage.
- `dimensions`: all ten dimensions above, each exactly once. Each entry has `name`, `score` (a number from 0 to 10, or `null` when not assessed), `evidence` (an array), and `reason` (the assessment, main defect or missing information). Every assessed dimension needs at least one source excerpt; a score above 9.0 needs two distinct excerpts.
- Each evidence object has `chapter` (the source chapter number), `quote` (an exact contiguous excerpt from that chapter's visible prose), and `reason` (why it supports the assessment). Put locations and explanations outside `quote`; no appended citations, ellipses, invented wording or text from the instructions. Market-position context can guide Market, but textual evidence still comes from the manuscript.
- `strongest_passage` and `weakest_passage`: each uses that same evidence-object shape.
- `confidence`: an object with `level` (`low`, `medium` or `high`) and `reason`.
- `limitations`: a nonempty statement of what this reading cannot establish.

If evidence cannot support a score, use `null` and explain. Do not manufacture a quotation or a complete assessment to satisfy the format. The structured-output schema can be emitted by `scripts/validate_rubric.py --schema`; the host supplies it, not private gate policy.

Do not edit the manuscript. Report observations and proposed fixes; leave their application to the author and revision editor.
