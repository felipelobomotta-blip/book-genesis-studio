# Orchestrator

The main agent's job: turn one idea into a complete book by running the eight phases in order, one active prompt at a time, with the author agreeing at each checkpoint.

When to load: at the start of every session, after `references/pipeline/host-contract.md`. Role: orchestrator.

## The loop

1. Apply `references/pipeline/host-contract.md` (start, resume, reconcile).
2. Read `pipeline.current_phase` in `PROJECT_STATE.yaml`. Load that phase's prompt and the references listed for it in `references/pipeline/manifest.yaml`, and nothing else.
3. Produce exactly the outputs the manifest lists for the phase. Save, read back, then update state and gates.
4. Check in with the author (host contract), unless the mode is autonomous.
5. Move `current_phase` to the next label and repeat.

## Non-negotiable rules

- Phase order is fixed. Never skip Phase 4, and never score before it.
- The writer never sees the rubric, targets or verdicts. Critics never see targets or earlier scores. You keep both apart (`references/scoring/evaluator-protocol.md`).
- Every important decision goes to a file: `ASSUMPTIONS.md` for inferences, `decisions` in `PROJECT_STATE.yaml` for choices, `RUN_REPORT.md` for what happened.
- Every new or revised chapter is written to `work/attempts/` first; the chapter file changes only after the new text is read back and accepted.
- Revision is bounded: three passes per gate (`references/prompts/revision-loop.md`).
- Write the book, its artifacts and every screen in the author's language. Keep this skill's file names and state keys in English.
- Specialist names are roles, not proof of separate processes. State what actually ran where, and at what independence grade.

## Phases

| Phase | Prompt | Main outputs |
|---|---|---|
| Phase 0: Intake | `references/prompts/intake.md` | brief, market map, story engine, panel personas, independence setup |
| Phase 1: Foundation | `references/prompts/foundation.md` | characters, theme, voice with rhythm contract, emotional curve |
| Phase 2: Architecture | `references/prompts/architecture.md` | outline with scene pressure, opening strategy, continuity ledger |
| Phase 3: Drafting | `references/prompts/drafting.md` | chapters, panel read of chapter 1, checks every five chapters |
| Phase 4: Adversarial Audit | `references/prompts/adversarial-audit.md` | audit with tickets and `audit_status` |
| Phase 5: Revision Loop | `references/prompts/revision-loop.md` | panel gate and rubric gate, at most three passes each |
| Phase 6: Final Score | `references/scoring/genesis-score.md` | final report with completeness, gates and independence |
| Phase 7: Editorial Package | `references/prompts/editorial-package.md` | package, hook test, exports |

## Starting from the middle

When the author brings existing material, start at the phase that material needs: a finished draft starts at Phase 4; a draft missing its package starts at Phase 7; a partial draft starts at Phase 3 after you rebuild the Phase 1 and 2 files the draft implies and the author agrees with them.
