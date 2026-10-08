# Phase 5: Revision Loop

Revise until two gates pass, the readers' and the rubric's, in at most three passes per gate. If a bounded loop ends with a gate unmet, record that result precisely and continue the autonomous path through Phase 6, Phase 7, and the portable delivery export.

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
4. **Accept or reject.** For each revised chapter, give the preserved accepted draft and the revision to the panel in compare mode, unlabeled. Freeze the four complete reader votes, the accepted and candidate SHA-256 values, and the decision in a JSON record. Copy the revision into `manuscript/chapters/` only if the panel prefers it by the recorded rule: at least three of four prefer the revision, or a two-two split where the revision has fewer concrete defects. Use `scripts/promote_chapter.py` for the replacement; it snapshots the accepted file, rechecks for stale inputs, replaces atomically, and writes a receipt. A failed check leaves the accepted chapter untouched. Otherwise leave the chapter as it is, keep the rejected revision where it is, and record why.
5. **Record.** Append the pass to `evaluations/revision-loop.md`: gate results before and after, tickets closed, passages changed, strengths preserved, and the verdict `CONTINUE`, `PASSED` or `STOPPED`.
6. **Count.** Add one to `pipeline.panel_passes` if the panel gate was failing when the pass began, and one to `pipeline.rubric_passes` if the rubric gate was.

## Phase 5 exit: technical proofread

Before moving to Phase 6, load Part 1 of `references/specialists/production.md`,
run its three technical proofread passes on the currently accepted canonical
chapters, and save the complete log to `evaluations/proofread.md`. If a
proofread correction changes a chapter, route it through the staged revision
editor, guarded promotion and affected reader/audit evidence above, then repeat
the proofread on the changed chapter. Phase 6 starts only after this evidence
exists for the frozen chapter set; a failed literary gate does not waive the
proofread requirement.

## Stop rules

- **Both gates pass:** set the gate to passed and move to Phase 6.
- **A failing gate reaches three passes:** in check-in mode, show the author exactly what is missing (which chapters lose readers and where, which dimensions sit how far under target, which tickets resist) and offer: three more passes, accept the book as it stands, or change the plan. If the author accepts or autonomous mode is active, record the same account in `RUN_REPORT.md`, continue to Phase 6 (which reports `Gates not met`), then Phase 7 and its default manuscript-plus-EPUB export with a receipt. Acceptance of the current text does not erase the unmet-gate record.
- **No progress:** if a pass closes no high-severity ticket and moves neither gate, use the same check-in or autonomous path; do not spend unbounded revision passes. An actual host, permission, quota, or incomplete-chapter blocker may block export only after the checkpoint is preserved and `delivery/DELIVERY_STATUS.md` (or `delivery/EXPORT.md`) records `status: blocked`, the exact error, and the next action. Never export an incomplete chapter set as a finished book.

## Revision rules

- Preserve what readers remembered unless it is structurally false.
- Do not add decorative lyricism to chase a score. Prefer concrete pressure to abstract explanation, and scene behavior to thematic statement.
- If a character behaves correctly too often, add cost, evasion, contradiction or self-caused damage.
- If prose is smooth and forgettable, add a specific detail, an asymmetry, a silence or an interruption.
- If a chapter cannot justify its existence, cut or merge it, and update the outline and the ledger.

## Safe promotion record

Run `python "<skill-root>/scripts/promote_chapter.py" --accepted manuscript/chapters/chapter-NN.md --candidate work/attempts/chapter-NN/revision-rK.md --decision evaluations/decisions/chapter-NN-rK.json --receipt evaluations/promotions/chapter-NN-rK.json --lock-file manuscript/chapters/.book-genesis-write.lock` from the book folder, replacing `<skill-root>` with the absolute installed skill path (add `--backup-dir` when the project keeps snapshots elsewhere). All manuscript writers and exporters should use this same cooperative lock path. The decision JSON is workflow evidence, not a writer-facing score: it must have `schema_version: 1`, `decision: "promote"`, the chapter number, four distinct reader votes, each with `reader`, `prefers` (`revision` or `accepted`) and `turn_page` (`yes` or `no`), plus the SHA-256 values of both chapter files. For a two-two split it also contains the two non-negative concrete-defect counts. The helper rejects missing or degraded votes, stale hashes, and failed snapshots before changing the canonical file; it does not call a model or a network service.

If Python is unavailable, use the same manual protocol under the same cooperative lock: hash the accepted and staged files and record the four complete votes; copy the accepted file to a dated backup; hash both files again; copy the candidate to a temporary file beside the accepted chapter; hash it and recheck the accepted file; atomically rename the temporary file into place; then write a receipt containing both hashes and the backup path. If any check or write fails, retain the accepted file and record the rejection. The lock is cooperative rather than a claim of protection against arbitrary writers; if a concurrent version is detected, preserve it and the holder/backup for reconciliation instead of overwriting it. Do not replace a chapter by ordinary copy-paste after a tied, incomplete, or degraded panel record.
