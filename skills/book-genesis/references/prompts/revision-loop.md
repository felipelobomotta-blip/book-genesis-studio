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

1. **Measure.** Run the panel gate read and the rubric evaluation, each under `references/scoring/evaluator-protocol.md`. If the last audit was `revise` or `major_rewrite`, also re-run the auditor on the chapters its tickets named and their dependent scenes. An autonomous `major_rewrite` uses this same bounded loop, with the original constraints and all high-severity blockers carried forward; it is not an approval to restart the book or reset counters. Save everything under `evaluations/`.
2. **Plan.** Write `evaluations/revision-plan.md`: tickets in priority order (audit high-severity tickets, then panel two-vote defects, then the lowest rubric dimensions), each with its quoted passage, the smallest effective fix, and the preserve list from the panel's memories. Identify what must change for the reader, the setup and consequences it depends on, and how a fresh recheck can determine whether it was fixed. Use the smallest revision class that can work: cut or merge, structural, connective, character, voice, line. A payoff failure needs the relevant scene or linked scenes; do not reduce it to sentence polishing. A factual correction must include the expressions that depend on the value. Do not change approved canon just to erase a finding. If the bounded pass cannot address every blocker, record the deferral and reason.
3. **Revise.** Hand the tickets to the revision editor (`references/specialists/revision-editor.md`). It sees tickets and passages, never scores or targets. It keeps a copy of the accepted chapter under `work/revisions/` and writes each revision to `work/attempts/chapter-NN/revision-rK.md`, never over the chapter itself.
4. **Accept or reject.** Before spending comparison reads, inspect whether the candidate actually addresses its tickets and stays coherent with the surrounding scene. A candidate that still contains the named factual contradiction, creates a dependent contradiction, omits a required consequence or exceeds its authorized scope returns to planning; preserve it and count the attempt. A strictly factual correction against existing canon uses the separate correctness check below. For a viable creative revision, freeze anonymous packets with `scripts/build_comparison.py --accepted <accepted.md> --candidate <revision.md> --output-dir <fresh-bundle>`. It assigns four distinct readers and counterbalances which version appears first. Only the individual `.packet.md` and `.schema.json` go to that reader; keep `manifest.private.json` with the orchestrator. Each reader has a frozen anonymous `.catalog.json`: schema-3 reports cite its paragraph IDs, including shared context, without exposing which version is accepted. Never tell a reader which version is accepted, revised, earlier or newer. When supported, use the host's structured output with that schema (Codex: `--output-schema <reader.schema.json>`). Validate the unaltered raw response against both input chapters with `scripts/validate_blind_reader.py --chapter <accepted.md> --chapter <revision.md> --report <raw.json> --expected-reader <assigned-name> --catalog <reader.catalog.json>` (also repeat `--chapter` for every shared context file in the private manifest) before counting it. A wrong identity, stale catalog or invalid reference is a failed read, never renamed or repaired; preserve it and retry only that reader within the bounds. Translate valid A/B votes using the private mapping. `same` provides no evidence of improvement and retains the accepted text. Freeze the four complete reader votes, the accepted and candidate SHA-256 values, and the decision in a JSON record. Copy the revision into `manuscript/chapters/` only if the panel prefers it by the recorded rule: at least three of four prefer the revision, or a two-two split where the revision has fewer concrete defects. Use `scripts/promote_chapter.py` for the replacement; it snapshots the accepted file, rechecks for stale inputs, replaces atomically, and writes a receipt. A failed check leaves the accepted chapter untouched. Otherwise leave the chapter as it is, keep the rejected revision where it is, and record why. Only a fresh check against the new canonical text may close an audit ticket; a preference vote alone does not close it.
5. **Record.** Append the pass to `evaluations/revision-loop.md`: gate results before and after, tickets closed, passages changed, strengths preserved, and the verdict `CONTINUE`, `PASSED` or `STOPPED`.
6. **Count.** Add one to `pipeline.panel_passes` if the panel gate was failing when the pass began, and one to `pipeline.rubric_passes` if the rubric gate was.

## Factual corrections have a correctness check

A wrong name, date, amount or physical fact already settled by the brief or
continuity canon is not a question of literary taste. A preference panel may
prefer the wording of an error. Do not invent votes to bypass that result, and
do not ask the same panel repeatedly until it agrees. Preserve any earlier vote.

For a strictly factual candidate with the same chapter heading, prepare a fresh
bundle with `scripts/check_correction.py prepare --accepted <chapter-NN.md>
--candidate <candidate.md> --canon <existing-canon.md> --context <dependent-chapter.md>
--ticket "<specific factual defect and preserved meaning>" --output-dir <fresh-bundle>`.
Repeat `--canon` and `--context` as needed. Include every directly dependent scene;
when linked chapters must change together, stage the complete coherent batch
first and disclose proposed context as such. An uncommitted companion is not
accepted canon and does not close a whole-book finding.

Send only `review.packet.md` and `review.schema.json` to a fresh, read-only
reviewer through the native-call guard. It must check all differences against
existing canon, reject new canon choices and unrelated creative edits, and
cite the frozen paragraphs in both versions and the supporting canon. It receives no scores, targets,
preference votes or prior verdicts. Then run `scripts/check_correction.py decide
--manifest <bundle>/manifest.private.json --call-dir <completed-native-call-dir>
--output <fresh-decision.json>`. A blocked or invalid original response produces
no decision. Keep it and count the attempt; follow the existing retry/pass bounds.

The resulting schema-2 decision goes to the same `scripts/promote_chapter.py`
guard. It verifies the original response and native receipt, source hashes,
resolved supporting passages and unchanged evidence before replacing anything. Its
receipt reports a correction check, with no invented preference panel. The
reviewer can still miss a semantic error; mechanical validation is not a
literary score or a guarantee of correctness.

A new canon choice, changed action or motivation, chronology repair that changes
events, missing payoff, voice edit or scene rewrite stays on the creative
revision path with blind comparison. A factual label cannot authorize it.
After any promotion, refresh the affected current-text reader/audit evidence.
Only the fresh full dependency check may close the broader audit ticket. This
path does not reset either gate budget or convert an unmet gate to passed.

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
- **No progress:** inspect the saved rejected candidates and identify why the repair failed: insufficient scope, missing setup, lost strength, ineffective change, invalid evidence or an unresolved choice in the story. While the original three-pass budget remains, attempt one materially different, explicitly ticketed strategy before declaring a plateau. A scope expansion, a changed scene consequence or a corrected dependency counts; the same instruction in a fresh context does not. Record the changed strategy before dispatch, keep every attempt, and never reset counters. If that changed strategy also produces no progress, or the budget is exhausted, use the same check-in or autonomous path with the unresolved findings disclosed. An actual host, permission, quota, or incomplete-chapter blocker may block export only after the checkpoint is preserved and `delivery/DELIVERY_STATUS.md` (or `delivery/EXPORT.md`) records `status: blocked`, the exact error, and the next action. Never export an incomplete chapter set as a finished book.

## Revision rules

- Measure the proposed chapter set with the exporter's deterministic word counter before comparison; an editor's estimated word count is not a receipt. Keep the complete manuscript inside its approved production floor and ceiling. Distinguish a suggested per-chapter aim from an exact contract; record a justified variation instead of treating every estimate as a hard limit.
- Give the editor one or two supported blockers per chapter and the remembered strengths. For a causal or pacing defect, use `references/specialists/causality.md`: prefer an action, consequence or cut to more explanation. Do not hand the editor every taste complaint as a mandate to rewrite the whole chapter.
- Every canonical change invalidates prior evidence for the affected scope. Preserve original validation receipts and verify the final reads with `references/pipeline/evidence.md`; a comparison vote alone does not replace the current-draft panel.
- Preserve what readers remembered unless it is structurally false.
- Do not add decorative lyricism to chase a score. Prefer concrete pressure to abstract explanation, and scene behavior to thematic statement.
- If a character behaves correctly too often, add cost, evasion, contradiction or self-caused damage.
- If prose is smooth and forgettable, add a specific detail, an asymmetry, a silence or an interruption.
- If a chapter cannot justify its existence, cut or merge it, and update the outline and the ledger.

## Safe promotion record

For a paragraph-bound creative comparison, record each persona's unaltered
response and original validation paths in a JSON index:

```json
{
  "primary": {"report": "primary.json", "validation": "primary.validation.json"},
  "hostile": {"report": "hostile.json", "validation": "hostile.validation.json"},
  "adjacent": {"report": "adjacent.json", "validation": "adjacent.validation.json"},
  "casual": {"report": "casual.json", "validation": "casual.validation.json"}
}
```

Paths are relative to the index file or absolute. Run
`scripts/decide_comparison.py --manifest <bundle>/manifest.private.json
--index <reports-index.json> --chapter <number> --output <fresh-decision.json>`.
It revalidates all four original reports against the frozen sources and private
mapping. Never replace this with model-written tally code. Four `A` votes in a
counterbalanced panel mean a two-two split, not unanimous preference for either
draft. `same` and `unsure` remain nondecisive; this automatic route does not
promote an incomplete or nondecisive panel even if other readers prefer the
candidate. Preserve those signals rather than changing them to make a record pass.

A two-two result retains the accepted text through this helper. The separate
tie exception below needs actual source-bound defects for each version, not
the sum of complaints from people who preferred that version. A complaint can
refer to the other version or to both. Without that separate evidence, keep
the rejection; do not ask new readers until a majority appears.

The schema-1 record below is for creative revisions. A verified factual correction
uses the generated schema-2 record above, with its bound original reviewer call;
it cannot supply hand-written votes or self-certify correctness.

Run `python "<skill-root>/scripts/promote_chapter.py" --accepted manuscript/chapters/chapter-NN.md --candidate work/attempts/chapter-NN/revision-rK.md --decision evaluations/decisions/chapter-NN-rK.json --receipt evaluations/promotions/chapter-NN-rK.json --lock-file manuscript/chapters/.book-genesis-write.lock` from the book folder, replacing `<skill-root>` with the absolute installed skill path (add `--backup-dir` when the project keeps snapshots elsewhere). All manuscript writers and exporters should use this same cooperative lock path. The decision JSON is workflow evidence, not a writer-facing score: it must have `schema_version: 1`, `decision: "promote"`, the chapter number, four distinct reader votes, each with `reader`, `prefers` (`revision` or `accepted`) and `turn_page` (`yes` or `no`), plus the SHA-256 values of both chapter files. For a two-two split it also contains the two non-negative concrete-defect counts. The helper rejects missing or degraded votes, stale hashes, and failed snapshots before changing the canonical file; it does not call a model or a network service.

If Python is unavailable, use the same manual protocol under the same cooperative lock: hash the accepted and staged files and record the four complete votes; copy the accepted file to a dated backup; hash both files again; copy the candidate to a temporary file beside the accepted chapter; hash it and recheck the accepted file; atomically rename the temporary file into place; then write a receipt containing both hashes and the backup path. If any check or write fails, retain the accepted file and record the rejection. The lock is cooperative rather than a claim of protection against arbitrary writers; if a concurrent version is detected, preserve it and the holder/backup for reconciliation instead of overwriting it. Do not replace a chapter by ordinary copy-paste after a tied, incomplete, or degraded panel record.
