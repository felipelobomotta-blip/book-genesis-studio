# Phase 5: Revision Loop

Revise until two gates pass, the readers' and the rubric's, in at most three passes per gate, and stop with a precise account when they do not.

When to load: Phase 5. Roles: orchestrator coordinates; blind readers, rubric evaluators and the revision editor do the work.

## The two gates

| Gate | Decides | Passes when |
|---|---|---|
| Panel gate | whether the book holds its readers | the gate read in `references/roles/panel.md` gives every sampled chapter a majority to turn the page, and no high-severity defect remains |
| Rubric gate | what to fix | the calibrated floor in `references/scoring/genesis-score.md` reaches `project.quality_target` (default 8.5) and no dimension sits more than 1.0 below it |

Both must pass. Neither can be argued past: a strong rubric does not excuse readers quitting, and happy readers do not excuse a broken structure.

## One pass

1. **Measure.** Run the panel gate read and the rubric evaluation, each under `references/scoring/evaluator-protocol.md`. If the last audit was `revise`, also re-run the auditor on the chapters its tickets named. Save everything under `evaluations/`.
2. **Plan.** Write `evaluations/revision-plan.md`: tickets in priority order (audit high-severity tickets, then panel two-vote defects, then the lowest rubric dimensions), each with its quoted passage, the smallest fix, and the preserve list from the panel's memories. Use the smallest revision class that can work: cut or merge, structural, connective, character, voice, line.
3. **Revise.** Hand the tickets to the revision editor (`references/specialists/revision-editor.md`). It sees tickets and passages, never scores or targets. It keeps a copy of the accepted chapter under `work/revisions/` and writes each revision to `work/attempts/chapter-NN/revision-rK.md`, never over the chapter itself.
4. **Accept or reject.** For each revised chapter, give the preserved accepted draft and the revision to the panel in compare mode, unlabeled. Copy the revision into `manuscript/chapters/` only if the panel prefers it, or splits and the revision has fewer defects. Otherwise leave the chapter as it is, keep the rejected revision where it is, and record why.
5. **Record.** Append the pass to `evaluations/revision-loop.md`: gate results before and after, tickets closed, passages changed, strengths preserved, and the verdict `CONTINUE`, `PASSED` or `STOPPED`.
6. **Count.** Add one to `pipeline.panel_passes` if the panel gate was failing when the pass began, and one to `pipeline.rubric_passes` if the rubric gate was.

## Stop rules

- **Both gates pass:** set the gate to passed and move to Phase 6.
- **A failing gate reaches three passes:** stop. In check-in mode, show the author exactly what is missing (which chapters lose readers and where, which dimensions sit how far under target, which tickets resist) and offer: three more passes, accept the book as it stands, or change the plan. In autonomous mode, record the same account in `RUN_REPORT.md` and continue to Phase 6, which reports "Gates not met".
- **No progress:** if a pass closes no high-severity ticket and moves neither gate, stop early with the same account. Revision that changes nothing measurable is churn.

## Revision rules

- Preserve what readers remembered unless it is structurally false.
- Do not add decorative lyricism to chase a score. Prefer concrete pressure to abstract explanation, and scene behavior to thematic statement.
- If a character behaves correctly too often, add cost, evasion, contradiction or self-caused damage.
- If prose is smooth and forgettable, add a specific detail, an asymmetry, a silence or an interruption.
- If a chapter cannot justify its existence, cut or merge it, and update the outline and the ledger.
