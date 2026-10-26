# Editorial Integration Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement task-by-task.

**Goal:** Integrate researched writing mechanisms into the existing plugin without weakening source evidence or duplicating its runtime.

**Architecture:** Versioned evidence transport plus small deterministic context/status helpers. Shared editorial references feed the current planning, writing and revision stages; existing independent gates retain authority.

**Tech Stack:** Python standard library, unittest, Markdown skill references, existing native Codex transport.

**Spec:** `docs/superpowers/specs/2026-10-25-editorial-integration.md`

## Global constraints

- Codex gpt-5.6-luna/high only for live book experiments; no Claude calls.
- Preserve historical receipts, negative outcomes and installed beta6.
- English product material; no sales or literary-quality claims from unit tests.
- No copied third-party code; provenance of mechanisms in adoption matrix.

## Review focus

- Valid location mistaken for semantic proof: preserve explicit support assessment and negative outcomes.
- Old book resume: versioned packets/schema verification stay unchanged.
- Future knowledge leakage: continuity helper refuses out-of-range source chapters.
- Headless and interrupted runs: status is read-only and handles incomplete optional artifacts.
- Export mistaken for acceptance: separate statuses in tests and user output.

### Task 1: Source-selected evidence

Files: `repair_evidence.py`, `group_review_schema.py`, `creative_groups.py`, `tests/test_repair_evidence.py`.
- [x] Test exact selection, unknown/duplicate IDs, changed-mechanism rejection, old schema compatibility.
- [x] Implement new opt-in report version and manifest version; preserve raw responses.
- [x] Run focused schema/group/repair tests.

### Task 2: Shared craft and temporal context

Files: `editorial-method.md`, `editorial_context.py`, `autonomous_book.py`, `craft_context.py`, skill references, `tests/test_editorial_context.py`.
- [x] Test chapter provenance, future exclusion, exact handoff and separation of provisional claims.
- [x] Integrate planning/writer/editor guidance and source context, without changing blind-reader packets.
- [x] Run workflow and score-boundary regression tests.

### Task 3: Observable progress

Files: `launcher/activity.py`, `launcher/status.py`, `launcher/autonomous.py`, plugin onboarding, `tests/test_book_activity.py`, `tests/test_controlled_outcome.py`. Reused the existing status entry point instead of adding a competing helper or runtime.
- [x] Test active/completed/blocked/missing-artifact states and literary/export separation.
- [x] Add read-only status entry point and actionable output.
- [x] Run plugin tests.

### Task 4: Distribution and evidence

- [x] Write adoption matrix for all 29 researched entries with actual implementation scope.
- [x] Run full unittest suite and `python runner/installer.py verify-suite`; inspect every failure.
- [x] Review final diff, package a fresh immutable beta, verify bundle contents.
- [x] Record exact evidence and remaining literary validation; update shared decision register when writable.

No automatic commits: preserve the existing mixed working tree for review.

## Execution rulings and evidence

- The compact source-selection schema completed a real Codex Luna/high 24-chapter review. Two larger schemas enforcing exact native passage/unit pairs were refused by the provider with `max_output_tokens` before any reported token use. The final candidate retains the successful native schema and strict local pair validation; no invalid selection is promoted.
- The real result remains `block`: two findings, 15 literal quotations. Original manuscripts, budgets, receipts and installed beta6 remain untouched.
- Full suite: 655 passing tests. Final focused run: 87 passing tests. Seven evidence tests rerun after the Unicode record-boundary fix. Current discovery: 658 tests, not a single 658-test full run.
- Fresh-context review resolved the instruction-version and completion-label findings and accepted the documented schema tradeoff. No remaining correctness or promotion bypass was found.
- Final evidence and limits: `docs/editorial-integration-20261025.md`; package receipt outside the archive in the parent workspace's `outputs/editorial-integration-20261025/final-candidate-verification.json`.
