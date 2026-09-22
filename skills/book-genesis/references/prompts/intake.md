# Phase 0: Intake

Turn a one-line idea into a brief the whole book can stand on, with every inference written down so the author can correct it in one reply.

When to load: Phase 0. Role: orchestrator, with the research specialist.

## Input

The only required input is the idea, however short. Infer the rest: language, genre, audience, form, length, point of view, tone, comparable titles. Write every inference to `ASSUMPTIONS.md` as one line with the reason ("Language: Portuguese (Brazil), because the idea was written in it").

## Steps

1. **Language and origin.** Detect the book's language from the idea. Research and write in that language; for a translation, also research the source language. Follow `references/specialists/research.md`.
2. **Form and length.** Choose the positioning (full-length novel, novella, short novel, serial installment, memoir, nonfiction) and take the floor, sweet spot and ceiling from `references/patterns/index.md`. Record `target_range_words`, `target_floor_words`, `target_ceiling_words`, `chapter_count_planned` and `average_words_per_chapter_planned`. Full length is the default unless the idea asks for something shorter.
3. **Market map.** Two to four comparable titles, the patterns they share, and the gap this book can own, as `references/specialists/research.md` describes. Without browsing, comps are provisional and the market gate stays unverified.
4. **Series.** If the idea implies more than one book, set `project.series: true` and load `references/specialists/series.md` now.
5. **Story engine.** Premise expansion, central conflict, escalation logic, and what makes this version different from its comps.
6. **Panel.** Build the primary, hostile and adjacent-genre reader cards from the brief and comps (`references/roles/panel.md`) and add the fixed casual reader.
7. **Independence.** Find the strongest critic setup the host allows (`references/scoring/evaluator-protocol.md`, `references/hosts.md`). If another model family's CLI is installed, propose it in the check-in: "I found Codex on this machine. Can it read the chapters blind as a second opinion? It uses your Codex quota." Run the isolation check where the host needs it. Record the result under `independence`.
8. **Quality target.** Keep `project.quality_target` at 8.5 unless the author names another number.

## Outputs

- `ASSUMPTIONS.md`
- `artifacts/00-brief.md`: the idea verbatim, inferred direction, language, genre, audience, positioning, target range, floor and ceiling, planned chapters and words per chapter, point of view and narrative mode, the reader promise in one sentence, and the "Panel" section with the four reader cards.
- `artifacts/01-market-map.md`: comps with why each is comparable, shared patterns, whitespace, and a source and checked date for every factual claim, or the label "unverified hypothesis".
- `artifacts/02-story-engine.md`: premise, conflict, escalation, differentiation.
- `PROJECT_STATE.yaml` with the project, collaboration, independence and manuscript fields filled.

## Check-in

The intake screen is the author's main chance to steer. Show the title idea, the one-sentence promise, genre and length, the comps, the independence proposal, and the five assumptions most worth correcting. Do not bury the author in files; point to `artifacts/00-brief.md` for the rest.
