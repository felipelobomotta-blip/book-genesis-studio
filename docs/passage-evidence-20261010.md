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
