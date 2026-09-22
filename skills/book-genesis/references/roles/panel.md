# Reader panel

Four blind readers with different stakes decide whether a chapter, a manuscript sample or a package would hold the audience it was written for.

When to load: Phase 0 (build the personas), Phase 3, Phase 5, Phase 6 and Phase 7 (run the panel). Role: orchestrator runs it; each reader follows `references/roles/blind-reader.md`.

## The four personas

Build the first three from the brief and the market map in Phase 0 and save them in the "Panel" section of `artifacts/00-brief.md`. The fourth is fixed.

1. **Primary reader.** Buys this genre on purpose. Knows its pleasures and its tired moves.
2. **Hostile reader.** Did not want to read this book. Reads for the flaw that justifies closing it, the way a one-star reviewer reads.
3. **Adjacent-genre reader.** Loves a neighbouring shelf named in the market map. Curious, not loyal.
4. **Casual reader (fixed).** Gives any book ten pages in an airport. Reads fast, skips description, has no patience for setup.

Each card has: a name; one line of identity; two or three recent reads taken from the comps in `artifacts/01-market-map.md`; what keeps them reading; what makes them quit. Keep each card under 80 words.

## Running a panel

- Every reader receives the same packet plus its own card, in its own fresh context, as set up in `references/scoring/evaluator-protocol.md`. Readers never see each other's verdicts.
- Save each verdict verbatim, then the aggregate, in `evaluations/panel-<scope>.md` (for example `panel-chapter-01.md`, `panel-gate-pass-2.md`, `panel-hook-test.md`).

## Aggregation

The orchestrator aggregates; readers never do.

| Signal | Rule |
|---|---|
| Turn the page | Majority: at least 3 of 4 say yes. A 2 to 2 split does not pass. |
| Defect | A flag counts as a defect only when at least 2 readers raise the same flag, or quote the same paragraph. A single reader's flag is kept as a note. |
| Stop point | Two readers stopping inside the same paragraph make that paragraph a high-severity ticket. |
| Memory | The union of `remember_tomorrow` is the list of strengths the revision editor must preserve. |
| Draft comparison | A revision is accepted when at least 3 of 4 prefer it, or when readers split and the revision has fewer defects. |

Report the table, the tickets it produced, and the preserve list. Never average feelings into a number.

## Modes

- **Chapter read** (Phase 3): chapter 1 after it is drafted, then the latest chapter at every fifth-chapter checkpoint.
- **Gate read** (Phase 5 and Phase 6): the declared sample is chapter 1, the chapter at the midpoint, the climax chapter, the final chapter, and every chapter revised in the current pass. Name the sample in the report. The gate passes when every sampled chapter gets a majority to turn the page and no defect of high severity remains.
- **Hook test** (Phase 7): each reader sees three to five packages (title, logline, back-cover blurb) and the first 250 words, and answers three questions per package: would you click, would you buy, would you keep reading. Rank packages by total yes answers; the primary reader breaks ties.

## Honesty

The panel is simulated. Report it as "read blind by four simulated readers" with the model families and the independence grade, never as "validated by readers". The signal is useful because the readers cannot see the plan, not because they are people.
