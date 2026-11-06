# Independent Revisions Implementation Plan

> Use superpowers:executing-plans task by task, with test-driven-development and verification-before-completion.

**Goal:** Accept independently verified good revisions without unrelated failures blocking them.
**Architecture:** Preserve the existing coordinated review. On a valid negative check, partition conservative evidence-linked dependencies and freshly review/vote each eligible unit against current canon. Reuse guarded publication.
**Tech Stack:** Python standard library, unittest, official native Codex transport.
**Spec:** `docs/superpowers/specs/2026-10-27-independent-revisions.md`.

## Global Constraints

- gpt-5.6-luna high only for native experimental roles.
- No complete-book run, score rerating, main manuscript edit or automation restart.
- Scoring policy, repair checks, preference votes and cumulative revision budgets remain unchanged.
- Preserve all pre-existing checkout changes and immutable release/evidence.

## Review Focus

- A rejected upstream revision blocks only its dependents, never its prerequisites.
- A new missing dependency discovered in a smaller assembly blocks publication.
- Accepted siblings change the current-canon snapshot for the next unit.
- Changed reports, candidates or current canon block resume/publication.
- Cycles, retained originals, negative votes and interrupted publication retain evidence.

## Tasks

### 1. Evidence-based partition
Files: create `skills/book-genesis/scripts/revision_partition.py`, `tests/test_revision_partition.py`.
- [x] Add failing tests: independent candidate survives; directed failure propagation; cycles stay atomic; shared issue alone creates no edge.
- [x] Implement `partition_review(manifest, catalog, report)` using normalized validated review evidence, producing blocked chapters, prerequisite graph and ordered components.
- [x] Run focused tests; require all cases pass.

### 2. Fresh unit acceptance and safe resume
Files: modify `creative_groups.py`, `correction_groups.py`; extend partition tests.
- [x] Add failing integration tests using real journal/transport fixtures for fresh checks/votes, rejection, stale canon and interruption.
- [x] Extract the staged-proposal input boundary without changing the legacy path.
- [x] Implement `execute_partitioned(...)` with immutable parent/partition evidence and a manifest version supporting a single freshly checked publication.
- [x] Snapshot current canon per unit, preserve original outcomes, retain failed prerequisites and avoid re-polling.
- [x] Verify targeted creative/correction/recovery/export suites.

### 3. Engine opt-in and native pilot
Files: modify `autonomous_book.py`; create an experiment helper and evidence report under workspace outputs.
- [x] Opt new passes into a versioned partition policy; frozen passes retain old behavior.
- [x] Prepare isolated evaluation inputs from four actual candidate responses with exact provenance.
- [x] Use the selected official Codex command, verify Luna high headers, run fresh native checks and votes only.
- [x] Verify accepted bytes/receipts, retained rejected originals, exact main-book hashes, unchanged policy and paused automation. Report bounded experiment results and limitations.
- [x] Run installer verification and appropriate full regression checks before any commit. No publishing is authorized by this task.
