# Rubric evidence recovery — October 10, 2026

The previous six-chapter experiment exhausted its rubric retries because the evaluator paraphrased or combined words inside supposedly exact quotations. Those reports remain invalid and unchanged. This update removes that transcription step from new rubric calls without changing scores or suppressing criticism.

## Changed behavior

`prepare_rubric.py` freezes every visible body paragraph in chapter order, assigns a passage ID, and records each source file's SHA-256. The complete catalog goes to the evaluator as its manuscript. Schema 2 reports select passage IDs and explain their observations. `validate_rubric.py` rebuilds the catalog from current source files, verifies the report's catalog digest, and resolves each reference to the exact source text in a separate receipt. It never edits the raw report.

Unknown references, missing or altered passages, a different book's digest, stale sources and changed reports fail. Partial coverage and unassessed dimensions remain incomplete. Scores above nine still require two distinct source passages. Legacy exact-quote reports remain supported. The catalog contains the complete assigned text, not passages selected to favor a score.

This validates provenance, coverage declarations and structure. It cannot establish that a critic actually understood a passage, detected every contradiction, or produced a calibrated quality judgment. The independent audit remains necessary.

## Observed evidence

Before calling a model, the experiment declared two trials and no retries. Both used the unchanged 6,919-word staged manuscript from the earlier experiment, Codex CLI 0.156.1, `gpt-5.6-luna`, high effort, fresh read-only contexts, and the existing native-call guard. No earlier scores, audit findings or desired verdicts were supplied.

| Trial | Raw report validation | Source references | Raw report SHA-256 |
| --- | --- | --- | --- |
| 1 | Passed on its first call | 25 | `637ea56f84be38a3cc171002486f86465aa0341bfb480921548e84b74568e538` |
| 2 | Passed on its first call | 22 | `4b564522f1ae1c19ad95b4c2ea64844d28d601b9e6543b4624ad9a9b316daa59` |

Both passed a second verification against their original receipts. The frozen catalog digest was `e779b49bf9f0c036bc0860fc93d54ca96e45fe14b953b80dfa7ce7401d840791`. The first evaluator still criticized pacing, exposition and prose patterns. It also underestimated an existing continuity defect, demonstrating why valid references do not replace the audit.

The repository suite passed: **244 tests**, including source mutation, catalog tampering, invented references, repeated evidence, incomplete assessments, original-receipt reuse and overwrite refusal. Installer verification and skill validation also passed. Private manuscripts, native logs and raw responses remain outside Git.

This is evidence that the revised citation protocol worked in two real calls, not a statistically established reliability rate or a passing literary gate. It does not reset the earlier revision budget, promote the staged manuscript, validate a full-length novel or establish a 90/100 product rating. A new complete workflow test uses this updated snapshot separately.

## Issues exposed by the subsequent native run

The real launcher run at `892e96c` spent time trying to inspect its own terminal and manually copying a hash manifest before writing the book. It also encountered Windows socket error 10013 in its first sandboxed isolation call, interrupted that attempt, and obtained an approved fresh retry. The original interrupted call retained its packet and streams but no completion receipt; the recorded helper and child were subsequently verified absent. This is not a successful original call.

The startup message now states that the agent is already inside the native writing session, that commentary renders automatically, and that the launcher has already verified the saved install record. The call guard now catches a keyboard interruption during a running call, preserves a failed receipt and partial output, and verifies owned-child shutdown before releasing the lock. An unverified tree shutdown retains ownership. The host contract gives connectivity/isolation checks a maximum 60-second timeout and directs denied-network retries through ordinary host permissions.

Two new actual-child regression tests cover the interruption paths. The complete suite passed **246 tests in 96.859 seconds**. This test evidence concerns the updated startup/interrupt changes; the ongoing manuscript run still uses its frozen `892e96c` skill snapshot. No already-running book was silently upgraded.

The same native run advanced to drafting without the required brief-contract register and independent architecture verification. The saved architecture packet had replaced the actual phase instructions with a short agent-written recap. Its successful word/count reconciliation did not validate this editorial work. This omission remains an acceptance failure in that run.

CLI progress checks now return `phase_context`: the exact active prompt read from the installed manifest, its source hash, and the reference paths. They explicitly identify their verification scope as saved state and manuscript counts. Missing or escaping phase references fail visibly. This gives the orchestrator the actual playbook at its existing checkpoint rather than relying on recall of the phase overview; it does not manufacture or mechanically prove completion of editorial instructions. Author-facing progress is also directed toward writing actions and decisions, with technical details retained in diagnostics.

The complete suite then passed **248 tests in 94.250 seconds**, including the actual CLI's phase-context output, preserved book state, manifest routing and invalid references. A subsequent native workflow must still demonstrate compliance with this changed prompt delivery.

## Current-draft reader evidence

The native run exposed the same quotation problem in blind-reader panels: three of four Chapter 2 first reports failed evidence checks, and one reader remained invalid after its two retries. Those raw attempts and the degraded final result remain preserved. They have not been repaired or relabeled as successful.

`prepare_readers.py` now prepares four fresh-persona packets and structured response schemas from a complete frozen paragraph catalog. Each receives the prose, its reader role, the language's machine-prose tells, the audience line and optional previous-chapter tail. Source paths and the private manifest stay with the orchestrator. Current-draft schema-2 readers identify paragraphs instead of retyping sentences. The validator resolves IDs into a separate receipt, preserving the raw response. The final review index includes the catalog; verification checks its original digest, resolved evidence, current source hashes and original report hash. Anonymous A/B comparisons retain their existing quote format.

A separate experiment declared four reads and zero retries before calling a model. It used the unchanged 932-word second chapter of the new manuscript, with its previous-chapter tail, Codex CLI 0.156.1 and `gpt-5.6-luna` at high effort. No old verdict, desired vote or repair ticket was supplied.

| Reader | Evidence validation | References | Raw report SHA-256 |
| --- | --- | --- | --- |
| Primary | Passed first attempt | 12 | `815243a1620cbb772d39dfcc648575b990d4472bc07ecdd7a1fe3298d25f9a17` |
| Hostile | Passed first attempt | 16 | `7c5eefd407e91c081f0f8442900d970b8018835f2719594e71d1758f52bff09a` |
| Adjacent | Passed first attempt | 12 | `6388086cebdbd9d71838e330aff57abc0f18045851b2f96803f9e8813671011e` |
| Casual | Passed first attempt | 14 | `f19152c41bb16eeb374553f961c7057657523c091367c0752414fb28d82fec97` |

All four would continue reading, but they also reported defects. The primary reader identified the mixed currency terms and a confusing document handoff, and described an attention drop during repetitive procedural action. These are simulated reader responses, not human approval. All 54 references resolved; this tests evidence handling in four calls, not broad reliability or literary quality. The separate reports were not injected into the live workflow and did not reset its revision budget.

The suite passed **258 tests in 99.781 seconds** with ordinary Windows filesystem/process permissions. An earlier sandboxed export-test run failed with Windows access-denied errors on atomic directory rename; the complete unsandboxed suite passed. New regressions cover negative findings, every evidence field, wrong IDs, altered and incomplete catalogs, stale source text, old reports against a new catalog, wrong identities, invalid enums, duplicate JSON keys, nonfinite values, catalog reuse and modified original receipts. The manuscript run retains its original installed snapshot and must be evaluated on that evidence.
