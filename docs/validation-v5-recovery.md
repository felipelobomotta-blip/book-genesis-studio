# V5 recovery validation — 2026-10-10

The recovery restores V5's creative drafting approach while retaining source-bound reviews, guarded chapter promotion and portable exports. This is a development build, not a release approved for unattended beginner use.

## Complete-book pilot

The frozen build `962504b8038f9073cb9858286e4aeeb0766b0686` was installed locally and its 51 payload files were checked before and after every native call. The same premise used in the earlier version comparison was requested as an English adult speculative mystery novella with 12 chapters and an approved 30,000–34,000-word range.

The orchestrator and every native writing/review role used the existing authenticated Codex CLI with `gpt-5.6-luna` and `high` effort. Completed role headers and saved packet/response hashes were independently verified. The second parent attempt ran for 2h 36m 56s and completed 228 scoped native calls without transport failures. The first attempt required intervention after attempting nested whole-book orchestration; it produced no manuscript and is retained as a failed journey.

The second attempt produced **The Unlisted Crossing**, 12 canonical chapters and 34,080 deterministic visible prose words. It reached the editorial package. Complete-pipeline export correctly refused a manuscript 80 words above the approved ceiling. Rejected trims were retained, and unfavorable comparison votes were not changed to force delivery.

The pipeline rubric remained below its quality target: calibrated minimum dimension 6.6, weighted average 7.71, target 8.5. Final current-draft reader coverage was verified for chapters 1, 2, 6, 8, 10 and 12, with four distinct valid readers per scope. Every selected raw report matched an actual native response byte-for-byte, and its packet contained the assigned current prose. These are simulated readers from the same model family, not human validation.

An additional anonymous prose-only review produced two valid reports out of three slots. The third was excluded after three bounded exact-quote failures. Its nine-dimension raw median mean was 8.12 and coherence was 6.4; the result is **degraded**, not a three-reader pass or a product-readiness score. A separate causal review failed exact-quote verification on all three attempts; no validated causal verdict is claimed. Initial Windows CLI startup failures are preserved separately from the corrected execution, with the identical anonymous corpus and sample identity.

A separate byte-identical manuscript copy was exported as a **standalone reading proof**, not a successful complete-pipeline delivery. Markdown, EPUB, DOCX and a 180-page PDF passed the portable export checks. PDF pages 1, 2, 90, 137 and 180 were visually inspected for clipping, missing characters and layout. The original book's blocked delivery record was preserved.

## Follow-up fixes

The pilot exposed comparison packets that told readers which version was accepted and which was revised. Those votes came from real executions, but they were not blind to revision identity. The follow-up adds `scripts/build_comparison.py` to freeze four anonymous packets with randomized, counterbalanced A/B order, distinct identities, response schemas and a private mapping. Headings and HTML metadata that could expose source identity are withheld without changing the original files.

`validate_blind_reader.py --expected-reader` rejects a report that names a different reader. It never renames or repairs a raw report, and assigned identity does not waive exact-quote validation. Existing callers without that option retain their receipt shape.

Workflow instructions now require unique raw report/receipt paths, keep the private mapping with the orchestrator, identify the applying session as the existing orchestrator, and prohibit nested whole-book calls or terminating its owning launcher. Drafting instructions clarify stage validation, remaining length allowances, compact chapter-specific packets and checkpoints before continuing. These prompt changes still need a new complete-book test; they were not retroactively applied to the frozen pilot.

Eight new regression tests cover anonymous order, metadata/heading exclusion, source preservation, immutable packet collisions, malformed input, identity mismatch, negative votes and fabricated quotes. The complete suite passes **166 tests** and `verify-suite` passes. The unrestricted Windows test process used a short workspace-owned temporary folder and propagated `PYTHONUTF8=1`; earlier sandbox rename/long-path failures and the mismatched child-encoding failure remain in the run logs.

Four fresh native Luna High readers also tested the actual comparison helper on a synthetic chapter pair with `--output-schema`. All four returned their assigned identities and valid source quotes on their first attempt. Input hashes remained unchanged. This validates the component protocol, not the revised full-book workflow or literary quality.

## Open release gates

- A new frozen full-book run must satisfy the original chapter and length contract and finish complete-pipeline export without operator repair.
- Supported continuity defects must be repaired through real staged candidates and source-bound acceptance, then re-audited.
- Revised workflow instructions need native end-to-end verification; passing deterministic tests cannot establish that an LLM follows them.
- Human reading, first-time-user sessions and complete-book runs in other hosts remain unverified.
- There is no bestseller, sales, virality or 9/10 readiness guarantee from these results.

The earlier V5 comparison manuscript remains frozen. This pilot does not establish a literary improvement over it.
