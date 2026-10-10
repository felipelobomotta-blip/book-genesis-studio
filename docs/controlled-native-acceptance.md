# Controlled native acceptance contract

Recorded before the first live run of the controlled workflow. This is a
development acceptance protocol, not a testimonial or a production-readiness
claim. Synthetic integration tests are reported separately from native runs.

## What changed

The unattended Codex path runs the existing skill through a deterministic
controller. Each native process is a scoped read-only role in a fresh empty
directory. The official CLI still owns authentication and subscription limits.
The skill manifest, creative references, reader packets, comparison rules,
calibrated rubric and exporter remain the shared core.

The controller owns phase transitions, native attempt reservations, revision
pass reservations, original call evidence, canonical chapter publication and
final export checks. Writers and reviewers cannot edit these records. Native
response text is preserved; visible progress reports real roles, elapsed time,
saved chapters and measured counts, never fabricated model thoughts.

The guided native-agent path and existing projects remain available. An existing
project is not silently migrated or upgraded. This controlled path is currently
implemented for Codex; it is not a claim of end-to-end coverage for other hosts.

## Fresh live test

- Official Codex CLI, exact model `gpt-5.6-luna`, effort `high`.
- A new English standalone novel, 12 chapters and 40,000–48,000 prose words.
- A new idea, a verified project-local snapshot, original responses retained.
- An independent plan verification before any chapter, creative checkpoints
  during drafting, factual checks at chapters 5, 10 and 12, full adversarial
  audit, bounded revisions, current reader/rubric evidence, technical proofread,
  editorial package and source-verified Markdown/EPUB delivery.
- No manual editorial rescue, copied chapters, adjusted word contract, replaced
  reviews, model fallback or injected code upgrade during this run.
- At most two native attempts per scoped call and three revision passes. Every
  attempt/pass is saved before dispatch. Exhaustion is recorded, not reset.

## Required technical evidence

All of these are required; averaging cannot hide a failed item:

1. The exact selected model/effort is confirmed in each native header.
2. All eight phases have saved original evidence in order.
3. A failed plan verification prevents drafting.
4. Every planned chapter exists and the fixed word contract is met.
5. Chapter publication preserves the raw response, extracted/staged bytes and
   accepted backups; revisions pass the existing promotion guard.
6. Original review packets, schemas, responses and source hashes match. A
   review of earlier prose cannot count as a review of later prose.
7. Revision and retry budgets persist across interruption.
8. Progress state agrees with actual chapters and word counts.
9. Final manuscript, current evaluations, package and EPUB pass source-bound
   verification. A complete file alone is insufficient.
10. The process finishes without operator intervention, releases owned native
    work, and can verify a completed book on resume without another model call.

Fault-injection tests separately cover interrupted response publication,
interrupted chapter promotion, stale reviews, changed files, missing journals,
budget exhaustion and export corruption. They cannot establish literary merit.

## The 90/100 bar

Do not assign a combined 90+ score merely because technical checks pass.
The literary result uses the existing ten-dimension rubric, two fresh
evaluators, median per dimension, then the existing minus-0.8 calibration.
The manuscript's calibrated weighted result must exceed 9.0/10, its calibrated
floor must meet the existing 8.5 target, the sampled reader gate must pass,
the ending must be resolved, and there must be no remaining high-severity audit
or blocking proofread findings. Confidence and reviewer disagreements stay
visible. These internal simulated readings still do not establish bestseller
potential or replace independent human reading and beginner usability sessions.

If the bounded run misses that bar, deliver and label the actual complete draft,
retain the failing evidence and improve the source before another fresh run.
Never ask additional critics merely to fish for a favorable score, lower the
threshold, suppress findings, or change the sample to obtain a pass.

## Run it

```powershell
python book_genesis.py new C:\Books\MyNovel --host codex --model gpt-5.6-luna --effort high --author "Your Name" --autonomous --chapters 12 --min-words 40000 --max-words 48000 --idea "Your book idea"
python book_genesis.py resume C:\Books\MyNovel
python book_genesis.py status C:\Books\MyNovel
```

Use an explicit author for unattended execution. Run `connect codex` first if
the official CLI is not signed in. No API key or credential extraction is used.
