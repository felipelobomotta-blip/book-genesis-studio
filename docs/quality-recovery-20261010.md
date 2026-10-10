# Quality recovery acceptance, October 10, 2026

The requested product target is above 90/100. **That target has not been established.** This record separates implemented improvements, observed behavior and release work still outstanding. It does not convert a unit-test percentage or simulated literary score into a product rating.

## What changed

- Revision tickets now include factual dependencies, the effect needed in the scene and a checkable repair outcome. A payoff problem can require linked scenes; changing one token is insufficient when another fact depends on it.
- Candidates that still contain the named contradiction or introduce another one return to planning before comparison. Counts come from the deterministic exporter, not the editor's estimate. A fresh audit must close a ticket; reader preference alone cannot close it.
- A failed strategy gets one materially different attempt within the original three-pass budget before a no-progress exit. Attempts remain recorded and counters are not reset.
- The auditor traces the central question through evidence, choice and consequence, distinguishing purposeful ambiguity from an absent payoff.
- Status shows phase, real chapter/word counts, delivery, current reader evidence and saved literary gates. Full reports remain available through `--json`. Changed project snapshots can be inspected with this checkout's trusted helpers while resume remains blocked.
- Rubric validation checks all ten dimensions, explicit coverage, finite scores, exact source excerpts and evidence for high scores. Samples and unassessed dimensions cannot pass a complete-book aggregate. Original source/report hashes prevent stale evidence being reused, even if the quoted words still exist. This verifies evidence, not the correctness of an interpretation.

## Deterministic verification

`verify-suite` and skill validation passed. The full Windows suite passed **234 tests**, including process-tree shutdown, installation, preservation of saved work, status failures, stale reader evidence, exports and thirteen new rubric-validation regressions.

The first full run used `-X utf8` for the test parent without propagating UTF-8 to installer children. One test failed while decoding the child's Portuguese Windows error (`UnicodeDecodeError`, byte `0xe3`). The isolated test passed with `PYTHONUTF8=1` inherited by parent and children; the final full run used that environment and passed. An isolated launcher test also hit the restricted sandbox's known atomic-directory-rename denial; its unrestricted rerun passed. Those failed attempts remain in the private logs, not silently discarded.

The real saved book's status correctly reports delivered files and current reader evidence alongside `audit = revise` and `revision = not_passed`. Status exit zero means the technical checks passed; it is not literary approval. Malformed JSON, contradictory successful exits, missing evidence, permission errors and timeouts remain failures.

## Native editorial experiment

All calls in this experiment used the installed **Codex CLI 0.156.1, `gpt-5.6-luna`, high effort**, in fresh scoped contexts. This is same-family simulated criticism (grade B), not independent human validation or a Claude test.

Three small repair cases were tested against both the original editor policy and its revision: a dependent age joke, a water-capacity calculation, and a character using a code before learning it. Both policies passed all three. These probes do not establish that the new wording alone improved performance; the earlier failed age repair also had an overly restrictive orchestration instruction.

The original six-chapter QA book contained 7,310 visible prose words. Three staged editorial attempts produced a 6,919-word candidate, preserving the first three chapters. The original manuscript and its delivery were not changed. A full-manuscript A/B comparison randomized and counterbalanced version order. Four valid simulated readers preferred the candidate, chiefly for the clearer causal account and Arthur's signed admission. Two readers needed one exact-quote retry each; rejected raw reports were preserved. This is whole-manuscript comparative evidence, not a substitute for per-chapter promotion or final current-draft panel coverage.

A fresh complete audit still returned **`revise`**. It found a letter-custody contradiction introduced in chapter four, questioned whether the decisive act satisfied the clock-stopping deadline, and reported an explicit time mismatch and remaining pacing/prose issues. The custody contradiction is directly visible in the text. Favorable reader votes did not erase it.

The first rubric response contained three unsupported quotations. Its numeric result was excluded. Two fresh retries using the new structured schema also failed exact-quote validation, and the bound was respected. **No passing rubric score is claimed.** These real rejected responses exercise the new guard; they do not establish reliable critic completion. Fixing evidence production is still required for an unattended journey.

A separate, byte-identical copy of the candidate was exported and independently verified as Markdown and EPUB, explicitly with `delivery_scope: draft`. It is a reading proof, not a completed new pipeline run or publication approval.

## Remaining acceptance work

1. Repair object custody and resolve the deadline decision against the original brief without changing the promise to excuse the prose. Recheck the complete resulting manuscript, not only the requested sentence.
2. Obtain source-supported rubric reports reliably within the bounded retry protocol. Exact-quote failures must remain visible; weakening the checks or dropping failed dimensions is not a solution.
3. Demonstrate a fresh idea-to-export run using the updated skill with no operator repairs, passing current-text literary gates as well as technical delivery.
4. Repeat complete-book acceptance on the second advertised native launcher host and at full commercial length. The supervised short Codex run does not establish either result.
5. Observe real beginner use and independent human reading before making strong public claims about usability or book quality.

The implementation and private evidence are local. This record does not claim a GitHub release, a production deployment, bestseller capability or viral results.
