# Native acceptance: failure preserved, recovery fixes tested

**Outcome: not ready for an autonomous complete-book claim or a 90/100 rating.**
The current code has tested fixes for several observed failures. A fresh
complete generation on that final code has not yet passed acceptance.

Both runs below used actual Codex CLI 0.156.1, `gpt-5.6-luna`, high effort. No
model fallback was substituted. The declared test was six chapters and
6,000–7,500 words in English, not a full-length novel. No human editorial
repair was supplied to either native run.

## What the runs established

| Run | Frozen skill source | Observed result |
| --- | --- | --- |
| Fresh idea-to-book run | `892e96c` | Six chapters, 6,859 words, then a `major_rewrite` audit. The policy stopped for an author choice despite autonomous mode. No final assessment, editorial package or export. Independent pre-draft plan verification was not established. |
| Isolated checkpoint replay | `8a1dca7` | Continued into revision and reached six chapters, 7,169 words. QA stopped it after finding stale comparison evidence. The original run and manuscript were preserved. No final assessment of the latest canonical text, editorial package or export. |

The replay ran for 6,159.399 seconds, approximately 103 minutes, including
startup and orchestration. It completed 91 new scoped native calls and recorded
seven failed call receipts; interrupted or merely prepared call directories are
not counted as completed calls. These figures do not establish acceptable
performance or a monetary cost. The shorter transport and evidence probes use
later code and cannot retroactively improve this frozen run's result.

## Decisive evidence failure

In the second revision round, a new Chapter 5 candidate was compared using
three reader responses from an earlier candidate and one fresh response. The
old readers ran around 22:11–22:13 UTC; the new candidate was returned around
22:52 UTC. The original native receipt's packet hash differed from the new
comparison packet for the primary, hostile and casual readers. Only the fresh
adjacent reader matched the new packet.

The orchestrator revalidated surviving quotations, then counted the old votes
against the new candidate. Quotations can remain present while the rest of a
scene changes; that does not make an old reading current. Its resulting
decision was a rejection, so this case does **not** establish an incorrect
canonical promotion. It does invalidate this comparison and the claimed
autonomous evidence chain.

QA interrupted the run after preserving that evidence. The native CLI then
exited normally. Its recorded launcher, native, scoped-helper and child PIDs
were absent on readback. The launcher lock was released; the interrupted
scoped lock was copied and hash-verified before removing that specific stale
lock. No test process was left running and no manuscript was deleted.

## Other open findings

- The saved state still reported 6,859 words while canonical prose contained
  7,169. Both revision counters remained zero after the orchestrator announced
  its second pass. Durable checkpoint and budget ownership need enforcement.
- Windows shell encoding corrupted saved evidence passages. The raw model
  reports and manuscript remained intact; the later output fix is documented
  in [Windows evidence](windows-evidence-20261010.md).
- The first-pass rubric had a calibrated coherence floor of 5.8, prose 6.5 and
  pacing 6.9. The fresh audit still requested revision. Those are measurements
  of the preserved first-pass text, not current final-book scores.
- A separate complete-manuscript consistency read found unresolved note
  custody/content, a reversed apprenticeship relationship and mismatched key
  inventories. Individual reader preferences did not close these findings.
- The replay does not replace missing pre-draft verification in the original
  run, and does not prove any other host, model, full-length book or beginner
  session.

## Fixes and verification on the current code

The latest source supplies prepared headless native commands, complete frozen
paragraph evidence, a separate factual-correction check, deterministic
comparison decisions and encoding-safe receipt output. See the linked evidence
reports in the README for the individual real-model probes and their limits.

The exact stale Chapter 5 reports were also processed against a fresh bundle
through the current decision helper. It blocked them, wrote no decision and
changed no manuscript, with no additional model call. A new regression changes
an uncited paragraph while retaining every previously cited paragraph and
requires rejection of all old reads against the new comparison.

Installer verification passed. The final full Windows suite passed **294 tests
in 104.251 seconds**. Generated role files match their sources. All changes are
local to the recovery branch; this report is not a release or deployment.

The remaining acceptance work is in the [recovery roadmap](../ROADMAP.md) and
[release checklist](../RELEASE_CHECKLIST.md). In particular, the orchestrator
must actually use the guards, persist pass state, execute every required phase
and complete a fresh idea-to-export run before unattended readiness can be
claimed. A simulated score or a clean unit suite cannot supply that evidence.
