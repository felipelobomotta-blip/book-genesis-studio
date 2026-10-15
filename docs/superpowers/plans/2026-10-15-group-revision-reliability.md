# Coordinated Revision Reliability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make bounded coordinated revisions executable without losing source evidence, rejecting a feasible intermediate shortening, or relying on underconstrained native reports.

**Architecture:** Keep the V5 writing approach and deterministic controller. Add a lossless planning view, correct only intermediate creative-group lower bounds, and version source-scoped review schemas while preserving legacy verification.

**Tech Stack:** Python3.11 standard library, unittest, native Codex, existing JSON Schema transport.

**Spec:** `docs/group-revision-reliability-20261015.md`.

## Global Constraints

- Base0dcaadf; trial44 remains failed and all original artifacts/budgets unchanged.
- Native Codex gpt-5.6-luna/high only; one native job at a time; no Claude/API fallback.
- No grade/calibration/gate/attempt-policy changes, manual prose edits or push/deploy.
- Existing final native1048576-character preflight remains authoritative.
- Full source evidence, valid negative reviews, four blind preference votes and atomic publication remain mandatory.
- English code/docs/artifacts; Portuguese conversation; complete updated suite and installer before commit.

## Review Focus

- Historical text that differs from current prose must stay literal: Task1 unmatched/stale-source tests.
- Unicode, CRLF, repeated occurrences and reserved reference markers must not alter data: Task1 roundtrip/tamper tests.
- A later no-op or invalid member must not authorize a too-short book: Task2 final-length rejection test.
- Previously accepted v1/v2 groups must retain their exact packet/schema/receipt meaning: Task3 legacy replay tests.
- A well-shaped false accusation or invalid native schema reference must still fail: Task3 quotation/mechanism/ref tests.

### Task 1: Bound planning context without omitting evidence

**Files:** create `skills/book-genesis/scripts/revision_plan_context.py`; modify `skills/book-genesis/scripts/autonomous_book.py`; create `tests/test_revision_plan_context.py`.

**Interfaces:** `render_plan_context(context, *, prefix_chars=0) -> str`, `compact_plan_context(context) -> dict`, `decode_plan_context(view) -> dict`. Context uses complete `current_sources` and `unresolved_findings[].original_evidence[].text`. Small JSON uses the existing ensure_ascii=False/sort_keys=True rendering. Large views reference only exact same-source literal spans and reconstruct all original fields. Return a complete best representation; the existing journal guards final size and preserves impossible requests.

- [x] Write a real revision_plan handoff regression: repeated-source input above1048576 must reach the transport below that limit with every source/issue/strategy/outcome recoverable and no score leakage.
- [x] Run it against the base; expect the real input-size failure, not a fixture typo.
- [x] Add/implement roundtrip, unmatched-history, malformed/range/hash, Unicode/newline, unchanged-small-packet and uncompressible-input tests. The latter must retain the durable global no-dispatch block without losing full input or spending extra calls on resume.
- [x] Verify focused context/native-limit/plan tests; reproduce the saved1103718-character packet offline and record original/new hashes and sizes.

### Task 2: Keep unpublished shortening feasible

**Files:** modify `skills/book-genesis/scripts/autonomous_book.py` and `skills/book-genesis/scripts/creative_groups.py`; create `tests/test_coordinated_length_floor.py`.

**Interfaces:** extend `BookWorkflow.revise_chapter(..., remaining_companions=None)`; `creative_groups.execute` supplies only the not-yet-processed task suffix. For stage_only creative proposals with a nonempty explicit suffix, use lower100; keep the existing upper allowance, final-member and standalone calculations. Expose that the final group still owes the complete length contract; original manuscript stays unchanged during staging.

- [x] Write/run a production staging regression with originals200+200+200, contract600..800 and paired proposals100+350: final650 is feasible, first100 must not be discarded solely by the intermediate lower floor. Base must fail that assertion.
- [x] Implement only the staged creative lower-bound correction and explicit remaining-member handoff.
- [x] Verify100-word floor, final member/standalone constraints, immutable originals, unchanged resume allowance and complete-group short-length rejection before review/poll/publication.
- [x] Recheck existing creative-group, partial-group, word-budget and context tests.

### Task 3: Make native review structure satisfy existing obligations

**Files:** create `skills/book-genesis/scripts/group_review_schema.py`; modify `skills/book-genesis/scripts/creative_groups.py` and the shared freshness guard in `skills/book-genesis/scripts/correction_groups.py`; create `tests/test_group_review_schema.py`; update existing fixture helpers for the explicitly new version while retaining legacy tests.

**Interfaces:** `build_schema(catalog, members) -> dict`, `expand_schema(schema) -> dict`, and a pure report-to-validation view. New manifest v3 uses report contract v2 with required chapter/check object keys, source-scoped original/proposed IDs and external support for dependency checks. Shared local $defs avoid repeating every source enum. Existing `schema_for(..., report_version=1)` and packet construction must retain legacy v1/v2 bytes. No rewritten native response files, inferred evidence or changed verdicts.

- [x] Write/run a boundary regression proving the current native schema admits a report that business validation rejects for forgotten support or a duplicated member; expect native-shape acceptance to expose the underconstraint.
- [x] Implement the new schema/validation view, strict local ref expansion, new manifest dispatch and explicit legacy paths.
- [x] Verify missing/wrong-source/duplicate coverage cannot satisfy new native shape; valid negative reports still block, invented/mislocated quotes and unchanged-mechanism accusations still fail, and legacy replay remains exact.
- [x] Verify full-size schema/enum bounds and all affected creative/group/replay tests; no change to preference or publication semantics.

### Task 4: Freeze and prove the integrated recovery

**Files:** branch review/evidence under workspace outputs; update the spec with actual results, without claiming book acceptance.

- [ ] Run one fresh whole-branch Luna/high review. Fix Critical/Important issues in one bounded RED-to-GREEN pass; ledger minor deferrals.
- [ ] Run complete unittest discovery and `python runner/installer.py verify-suite`; read results, then commit only the coherent tested change. Preserve all red/failure logs.
- [ ] Freeze clean commit, final suite/installer/review hashes, unchanged native lifecycle/gates and original trial44 file hashes.
- [ ] Run serialized bounded native planning/schema component canaries on frozen source, verify exact model/effort, original receipts, replay and owned shutdown; do not grade them as books.
- [ ] Start a fresh unattended24-chapter/80000..88000 book from the same idea under unchanged strict >90 system/book acceptance. Preserve every failure; export alone is not a quality pass.

All tasks run inline. User already authorized continuous fixes and tests; no per-task confirmation or implementer agents. Exactly one final fresh reviewer is allowed by the execution skill, using the user's requested Luna/high. Record decisions and results in this plan's ledger.
