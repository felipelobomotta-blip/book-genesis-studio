# Revision recovery and quality repairs implementation plan

> Execute task by task with regression tests before production changes. User approved the evidence-backed diagnosis and requested recovery of the same book with Luna high and unchanged scoring.

**Goal:** Finish the blocked book's real revision and verified export, then report its actual literary gate outcome. Never manufacture a >90 result.

**Architecture:** Preserve the original beta7 execution and all prior attempts. Use a lossless, versioned factual-review wire, a dependency-aware revision schedule for new passes, and an explicit audited runtime recovery for the existing book. Reuse the current controller, installer, validators and export pipeline.

**Tech stack:** Python standard library, unittest, existing native Codex transport.

**Spec:** `outputs/beta7-release-20261026/quality-diagnosis-20261026.md` in the parent workspace. The accepted user constraints override redundant design approval gates.

## Constraints

- Native model remains gpt-5.6-luna, effort high. No Claude inference.
- Quality target 9.0 and weighted target 9.0, calibration -0.8, dimensions, voting and pass budgets unchanged.
- Preserve the released ZIP/tag, existing native reports and all manuscript versions. No manual chapter edits or checkpoint budget resets.
- Source hashes, complete-source coverage and negative findings remain mandatory.
- Describe the recovered run as an explicit runtime recovery, not a clean beta7 run.

## Tasks

- [x] Reproduce the oversized factual group with realistic complete-source input. Add lossless repeated-passage references with strict roundtrip checks and legacy support. Upgrade only new or undispatched oversized group checks with a new identity, preserving the blocked packet.
- [x] Schedule independent cosmetic proofreading after creative work in new passes, while keeping true factual dependencies coordinated and preserving already-started pass ordering. Test overlapping chapter tasks and resume behavior.
- [x] Strengthen planning/revision instructions for demonstrated clue tests, consequences, repeated scene mechanisms and image/interpretation repairs; apply only to future calls. Do not force arbitrary beat percentages or pad the ending.
- [x] Add an explicit recovery utility: require stopped/blocked state, verify snapshot and all prior evidence, archive original bytes, install the current tested runtime through the installer, record exact old/new hashes and preserve the model/scoring/attempt contracts. Test rejection of altered evidence, active ownership and score changes.
- [x] Run focused tests, installer suite, full unittest suite, and exact saved-packet offline replay. Record any remaining failures.
- [ ] Recover this book once, resume through plugin_entry.py with native permissions, monitor a single controller, verify current-text reviews, manuscript counts, final score and exports.

## Review focus

- A malicious or accidental wire header inside prose cannot become a reference.
- Identical text in different sources retains distinct passage IDs and source hashes.
- Unchanged members do not become fabricated edits or automatic approvals.
- Recovery never erases a consumed literary pass or reuses old scores for changed prose.
- A stopped or gated-out run is reported accurately, including if it never reaches 90.

## Execution checkpoint

The full suite passed 673 tests; focused runtime recovery passed nine tests. The actual saved packet roundtripped at 692,583 characters with 50 sources preserved. Explicit recovery succeeded and native Luna high resumed in session 58395. The recovered factual review rejected an unrelated typography change; no negative verdict was overridden. Creative revision has started. Final quality and export remain pending. New early-draft intervention and upstream functional-plan validation are separate future work; this recovery does not retroactively change the original architecture or draft.
