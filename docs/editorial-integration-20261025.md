# Editorial integration: beta 7 candidate

Date: 2026-10-25. Local candidate only; no GitHub publication or installed-cache replacement in this work.

## Change

The [29-entry adoption map](research/editorial-adoption-20261025.md) records each researched mechanism and its actual scope. Original implementation, no third-party source vendored. The native host continues to own authentication, models, permissions and process execution; the book's journal owns publication and evidence.

New planning fields capture scene goal/resistance/choice/change/cost/consequence, knowledge acquisition versus reader disclosure, and arc change. The independent plan review examines these fields. Role-specific craft instructions add original voice samples and corpus confidence, nonlinear fact/disclosure handling, dependency-scoped diagnosis and a source-before-claim nonfiction policy. A read-only source index preserves every earlier accepted chapter and an exact handoff; provisional summaries are not certified facts.

Creative group manifest v4 uses report v3. Reviewers select a passage ID and a one-based literal span. The controller renders the actual source quote and applies existing source coverage, changed-mechanism and negative-verdict checks. Identical paragraph bytes may be referenced once across versions, but each version retains its own passage ID. Old report/manifest contracts remain verifiable. The whole-book stale-source guard explicitly includes v4.

The existing status command now exposes saved request identity, reservation age and failures. This does not establish process liveness. Launcher outcomes distinguish an exported draft with unmet literary gates from a reported passing result; an exit code alone does not certify a book.

## Real native diagnostic

Input: the original beta6 second creative-revision proposal, covering 24 chapters. No original manuscript, proposal, budget, verdict or receipt was changed.

- Model: **Codex gpt-5.6-luna**, reasoning **high**.
- Complete source packet: **902,939 characters**; final native schema: **167,838 bytes**.
- Lossless source-catalog round trip confirmed.
- Successful native call: 2026-10-25 14:05:13–14:07:07 UTC, approximately **114.35 seconds**.
- Result: valid report, **block**, **2 findings**, **15 located literal quotations**. A negative editorial result is preserved.
- Final source revalidation confirms the shipped packet and schema are byte-identical to that successful request, and its response still passes local validation.

Raw local evidence is under `outputs/editorial-integration-20261025/` in the parent task workspace, particularly `native-evidence-check-2/result.json` and `final-source-revalidation.json`. These are diagnostic receipts, not a new book or a literary before/after experiment.

Three real beta6 review packets serialize to 777,943 / 902,939 / 896,951 characters under the new lossless format; all fit the current 1,048,576-character native guard. This is evidence for those packets, not a guarantee for arbitrary manuscript sizes.

## Preserved failures and transport decision

The first diagnostic failed before generation because sandboxed Windows access prevented native app-server initialization; it was retained, then retried through the normal approved host access.

A fresh code review identified that the compact native schema could admit a unit number invalid for a particular passage. Exact conditional passage/unit schemas were implemented and tested locally, but the real provider refused both an 828,067-byte variant and a reduced 260,289-byte variant with `Incomplete response returned, reason: max_output_tokens` and reported zero used tokens. Those failures remain recorded. The observed refusal does not establish its internal cause.

Ruling: ship the transport format that actually completed, with native source membership and strict **local** passage/unit membership. Impossible or repeated pairs fail closed with precise feedback; no quote is guessed, no negative verdict becomes positive, and the existing two-attempt bound remains. Exact native pair enforcement is not claimed. The earlier successful response also passed the experimental stricter local schema.

## Verification and limits

Focused regressions cover lossless text reuse with distinct source identity, invalid/duplicate span selection, unchanged-mechanism accusations, old packet hashes, future/missing chapter exclusion, literal handoff, activity states and completion labels.

- Full suite: **655 tests passed**, 751.815 seconds. Log: parent workspace `outputs/editorial-full-suite-final-20261025.log`.
- Final focused run: **87 tests passed**, 166.446 seconds. Log: `outputs/editorial-focused-final-20261025.log`.
- After the final Unicode line-separator correction, all **7 repair-evidence tests passed** again. JSON-contained Unicode separators are preserved by splitting only physical LF record boundaries.
- Current discovery contains **658 tests**. Three regressions were added after the full run started and exercised in focused runs; this is not a claim that a single 658-test full suite ran.
- Fresh independent code review found no remaining correctness or promotion bypass. It accepted the documented compact-native-schema/strict-local-validation tradeoff as an efficiency risk, not proof of literary improvement.

The final distribution candidate is built separately under `dist/plugin-beta7-20261025-final/`. Package verification and its archive hash are recorded in the parent workspace `outputs/editorial-integration-20261025/final-candidate-verification.json`, outside the archive to avoid a self-referential hash. The previous package and installed beta6 cache remain unchanged.

The beta6 baseline remains **72.52/100** in automated literary review. No new complete beta7 book, blinded literary gain, human critical rating or sales result is claimed by this integration. Source-before-claim instructions are not a live retrieval service, and the source index is not an automatically verified knowledge graph.
