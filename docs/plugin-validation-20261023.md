# Native plugin validation — 2026-10-23

Status: **local beta; complete-book acceptance not established**. These records
separate packaging, live host discovery and actual manuscript production.

## Installed package

Codex CLI 0.163.0 installed and enabled `book-genesis@book-genesis`, version
`5.1.0-beta.6`, through its native marketplace/plugin commands. The local
marketplace points to `dist/plugin-beta6-20261023/book-genesis`. Every installed
payload hash matched the clean archive receipt. This is not a public listing.

Archive SHA-256:
`68392ed129df7d2b72586e80655aabb470db84faa752bf84cd645474b375af77`.

The tested source is the uncommitted working tree based on `89ecbfb`, including
earlier recovery changes. A commit hash alone does not identify this build;
the immutable archive and its per-file receipt identify its actual contents.

## Automated and native checks

- 21 plugin/bridge tests passed on beta 4: extracted resources and actual child-process
  launch from the clean package, deterministic
  ZIPs, allowlisted files, malformed indexes, Windows reparse points, destination
  protection, hash verification, DSH skill provider/activation contract,
  verified project preparation, preserved original idea and quality contract,
  rejected modified snapshots, Anonymous author default, verified resume and
  bounded preflight failures and rejection of the observed input contamination.
  These checks took 32.109 seconds on this machine.
- 41 distribution tests passed with a short Windows temporary directory.
  The default deeply nested sandbox temporary directory hit MAX_PATH in an
  earlier attempt. This environmental limitation remains relevant on Windows.
- `verify-suite` passed after the onboarding/bridge changes.
- Claude Code 2.1.280 validated the plugin and marketplace manifests strictly.
  No Claude model quota was used. Installation/production in Claude is not proven.
- DSH was tested against its provider and package composition contracts only.
  No live DSH installation, sign-in or generated book is claimed.
- The complete repository suite started on beta 3 passed **616 tests in
  898.339 seconds**. The subsequent beta 4 input-routing changes passed the
  **21-test plugin suite**, including its two added regressions; these counts
  overlap and must not be added together. No commit or GitHub publication was
  made in this task.

### Beta 5 full regression result

The complete updated suite passed **631 tests in 921.184 seconds**, with short
workspace TEMP. Log: `outputs/plugin-beta-20261023/full-suite-beta5-final.log`
in the task workspace. The initial beta 5 run had two stale fixture errors:
the synthetic correction responders still tried to read the removed wire enum.
Both now obtain real IDs from the supplied length-framed catalog; all existing
promotion/export assertions remain. The 19 targeted handoff/recovery tests then
passed before the clean full-suite rerun. These are overlapping test counts.
No production package bytes changed after beta 5 was installed; its receipt was
rechecked while the fresh book run was writing. No commit or publication occurred.

## Live Codex attempts (failures included)

### Discovery canary, beta 1

One real Codex `gpt-5.6-luna`, high-effort call completed in 39.8 seconds. It
found the installed plugin in the actual skill catalog, read its SKILL and
onboarding resources, found the export helper and confirmed Python 3.11.9.
This did not generate or score a manuscript.

### Fresh book attempt 1, beta 1 — failed startup

The native host received the original idea for a 24-chapter, 80–88k-word novel.
It improvised an incomplete installation record and project configuration,
then launched nested Codex without working network access. The child transport
reported Windows error 10013. No chapter was produced. The test's owned process
tree was stopped after 681.1 seconds; this is a forced interruption, not a
completed native run. All logs and partial project files were preserved.

Root fixes: the packaged `plugin_entry.py` now reuses the existing installer and
controller to prepare actual hashes, the full idea and an execution contract.
It checks the selected isolated native connection with a 60-second deadline
before consuming a manuscript attempt. It reports the failure and preserves
the folder for normal host permission/sign-in recovery. It does not bypass
network permissions or rewrite checkpoint budgets.

Packaging review also caught an omitted timezone resource/license, incomplete
DSH activation metadata and Windows junction/input-index weaknesses. These
were corrected and covered by tests before beta 2 was built.

### Fresh book attempt 2, beta 2 — failed startup

The host used the preparation bridge correctly. The first preflight failed on
sandbox network access within its bounded timeout, without consuming a book
attempt. The agent inspected the receipt, used the normal elevated permission
flow and resumed autonomously. The next real connection check succeeded.

The process then failed because `launcher/windows_job.py`, imported lazily on
Windows, was omitted from the archive. This is our packaging defect. No chapter
was produced. The owned test process tree was stopped at 199.5 seconds; the
installed cache remained hash-identical. Its evidence uses `beta2-full-*` files.

Beta 3 includes that module. A regression test first reproduced the missing
module failure, then passed after the fix by launching a real harmless Python
child through the extracted package's process owner. It makes no model call.
The bridge also defaults an omitted publishing name to Anonymous, and the
onboarding forbids improvising runtime repairs or editing the installed cache.

### Fresh book attempt 3, beta 3 — interrupted for input contamination

Native startup reached the controller. Inspection of the saved idea revealed
that the host copied the full user message, including AGENTS.md instructions
and the 90/100 acceptance target, into the literary brief. The controller
preserved exactly what it was given, but that input could disclose the private
target through planning context. The run was stopped at 247.7 seconds during
intake, with no chapter produced. It is not a valid blind evaluation.

Beta 4 clarifies story-only input routing and adds a narrow validation for the
observed instruction/quality-target contamination before preparation or calls.
It rejects rather than silently rewriting the author's creative idea. This
heuristic does not claim to recognize all possible semantic leakage. Operational
settings remain flags; story constraints retain their original wording.

### Fresh book attempt 4, beta 4 — failed during revision

A new native Codex session receives the same original idea, author name and
permission to make creative decisions. All model work is restricted to
`gpt-5.6-luna` with high effort. Acceptance requests both reliable delivery and
literary quality above 90/100; a target is not a measured result. Critics must
not receive that numeric target. No prior prose or checkpoints are reused.

Evidence is saved in the task's `outputs/plugin-beta-20261023/` folder:
`beta4-full-prompt.txt`, `beta4-full-launch.json`, `beta4-full-events.jsonl`,
`beta4-full-stderr.log`, and the final result when it exists. The manuscript
workspace is `books/plugin-codex-beta4-20261023`, outside the repository.

The native host ended after 4,183 seconds. Its exit code 0 means the agent
reported the blocked outcome successfully; it is NOT a completed-book result.

Observed so far: the host recovered the sandbox connection through the normal
permission flow; the bounded retry succeeded. Intake, foundation and architecture
returned verified responses. Seven early artifacts were saved. The first plan
review found one concrete chapter-13 deadline inconsistency and the controller
started its targeted repair. No numeric-target marker or AGENTS.md marker was
found in those seven early artifacts. No completed chapter or export is claimed
at this checkpoint.

Later checkpoint: the plan's deadline defect was repaired and its second
review passed. The controller reached 12 saved chapters / 41,186 canonical
prose words, with chapter 12's draft review pending. The first two five-chapter
continuity checks produced saved findings for revision. This is actual progress
in the same unmodified beta 4 run, not a completed/revised/exported book result.

Draft-completion checkpoint: all **24 chapters / 83,148 canonical prose words**
were saved within the 80–88k contract. The chapter-24 continuity check is pending.
The requested whole-book audit, repairs, final review and exports must still
complete before this can be counted as an end-to-end delivery.

### Beta 4 outcome and beta 5 context repair

The fresh run produced 24 chapters / 83,148 words, then completed the whole-book
structural audit. That audit requested revision. The baseline automated literary
measurement was 7.25/10 weighted (72.5/100), with a 6.5 floor; it did not pass.
This is model-based feedback, not independent human critical acclaim.

During factual revision of chapter 16, both native verification calls failed
before any output with `Incomplete response returned, reason: max_output_tokens`.
The original attempt budgets and all evidence remain unchanged. No final EPUB
or accepted final editorial package was delivered. Four fresh attempts have
therefore produced zero fully accepted plugin deliveries so far.

Isolated diagnosis, same Luna/high model:

| Request | Result |
|---|---|
| Original text and exhaustive schema, explicit 400k context | Same failure |
| Same 400k context and text, bounded wire schema; exact local ID validation | Completed in 22.4s, valid report |
| Lossless length-framed packet + bounded wire schema, original default context | Completed in 16.8s, valid report |

Estimated o200k token sizes fell from 267,129 text + 89,448 schema to 230,185
text + 284 schema. These are local tokenizer estimates, not server usage bills.
Every source paragraph and ID remains available. The new v2 correction format
uses the existing catalog wire renderer; exhaustive membership validation and
promotion receipt checks remain local. Version 1 frozen packets still verify
using their original rendering. No diagnostic response was promoted into the
failed manuscript or counted as a clean run.

The repair passed 49 correction tests, followed by the expanded report-contract
suite including invented-ID rejection. Short workspace TEMP is required in this
Windows sandbox; the initial default-TEMP run failed on sandbox path permissions,
not model output. Beta 5 is a new immutable package; beta 4 remains preserved.
The native beta 5 full-book attempt started in a new workspace, using the same
original idea, exact model/effort and private quality targets. Its evidence files
are `beta5-full-*`; no prose, checkpoints or diagnostic responses are reused.

Compatibility boundary: beta 5 applies to newly prepared books. Old projects
keep their verified immutable skill snapshot, frozen requests and consumed
budgets. A blocked oversized v1 call is not silently migrated or refunded by
installing beta 5. Completed v1 correction receipts remain verifiable. The
catalog preserves normalized paragraph text and IDs; raw source hashes preserve
byte-level tamper protection.

## Additional scale risk identified during review

Code review found that historical issue reconciliation resends every earlier
finding and its full quotations alongside the complete current manuscript.
Beta 4's first such request was 882,502 characters; the native input guard is
1,048,576. Later passes can add findings. This is a concrete unbounded-growth
risk, not a failure yet observed in the beta 5 run. Do not describe the engine
as supporting arbitrary book lengths or revision history. The current frozen
trial is not modified in place. Candidate mitigation: deterministic allegation
batches, each retaining the complete current source catalog and exact original
evidence, with all statuses and receipts aggregated without dropping issues.

### Beta 5 final outcome and beta 6 corrections

The fifth fresh attempt stopped after **22 of 24 chapters / 82,494 prose words**.
Both completed chapter-23 responses contained 2,841 words against the current
100–2,840 allowance. The two attempts were retained and correctly exhausted,
but the controller lacked a small automatic length repair. No chapter 23 was
published, no final literary measurement was reached, and no EPUB was delivered.
The root host ended after 2,885.7 seconds with an honest blocked report; exit 0
does not change that outcome. Five fresh attempts have zero accepted deliveries.

Beta 6 adds a separate bounded literal-edit recovery for near-boundary drafts.
It preserves both failed attempts, their original length limits and responses.
The replacement must be unambiguous and its size is tied to the actual drift;
program counting verifies the resulting prose before publication. Recovery is
recorded before publication and checked again on resume. The original writer
summary remains explicitly provisional; the next writer receives current prose.

An isolated native replay of the actual failed chapter exposed ambiguous edit
instructions: both responses exceeded the newly narrowed edit-size cap. After
adding the exact cap and actionable validation feedback, a second isolated
diagnostic succeeded in one Luna/high call: **2,841 → 2,840 words**, one short
literal substitution. Both diagnostics and both original draft failures remain
on disk. No diagnostic output was promoted into the old book. This is a repair
test, not a clean full-book completion or evidence of literary quality.

The historical issue-growth risk above is addressed in new beta 6 runs with
deterministic allegation batches. Every batch receives the complete current
catalog; exhaustive passage membership remains checked locally. Aggregation
requires every original issue exactly once, and an invalid batch cannot resolve
an issue. A single issue plus complete sources that exceed the bound still
blocks explicitly; no source is discarded. Old immutable requests are unchanged.

Targeted checks passed: 7 draft-recovery tests, including interrupted publication,
full synthetic revision/export and idempotent resume; 3 batch tests including
interrupted resume and invented-ID rejection; 14 existing recovery tests.
These are not real literary scores. Full beta 6 regression and fresh acceptance
results are recorded separately when complete.

### Beta 6 complete regression result

The complete suite passed **641 tests in 1,009.967 seconds**, including the new
recovery and batching integration tests. Log:
`outputs/plugin-beta-20261023/full-suite-beta6.log` in the task workspace.
`verify-suite`, whitespace checks and the installed payload receipt also passed.
The fresh sixth native book attempt is running from a new workspace with the
same original idea and exact Luna/high configuration. No earlier chapters,
checkpoints or isolated repair responses were reused. Installation and these
automated tests do not establish the unfinished manuscript's final quality.

Observed host narration defect in this fresh trial: the outer Codex agent said
the chapter-20 continuity check "passed", but the saved report's verdict is
`revise`, with one medium-severity key-custody finding. The controller retained
the finding correctly. A completed/validated review is not necessarily a pass;
user-facing progress must report the actual verdict. This narration issue is
not fixed in the immutable beta 6 currently executing.

The fresh draft completed at **24 chapters / 83,517 prose words**, with no failed
draft attempts. An independent read-only `check_progress.py` reconciliation
confirmed chapter sequence, counts and stored state. The full audit requested
revision with four findings. During baseline issue reconciliation, batch 001
returned issue IDs in `evidence_ids` on both attempts instead of current passage
IDs. Strict local validation rejected them; the existing fail-closed path kept
every assigned allegation open and continued to batch 002. This is a real
structured-output failure despite passing deterministic tests. The compact
wire schema and generic enum feedback are candidates for correction; the
running immutable trial is not patched in place.

### Unpackaged fixes observed during beta 6 acceptance

A regression test reproduced the missing native passage-membership constraint.
The issue-check schema now retains its single exhaustive current-passage enum,
and its prompt distinguishes finding IDs from passage IDs explicitly. Unlike
the earlier factual-correction schema, this schema does not repeat the enum
across many checks. The four batching tests pass, including the new regression.

A schema-only native replay used the **identical original 682,405-character
packet** and a 19,957-byte exhaustive schema. Luna/high returned a locally valid
report in **51.995 seconds** on its first call. The diagnostic is saved under
`outputs/plugin-beta-20261023/strict-issue-wire-replay/`. Its response was not
promoted into the running book. The beta 6 failures remain recorded.

The development source also emits the actual review verdict/finding count in
the progress log and clarifies narration in onboarding: completed validation
is not editorial approval; three rubric readings are not three revision passes;
proposed edits are not accepted text. These changes are not installed into the
running beta 6 cache or its frozen book. A complete post-fix regression run is
in progress; the 641-test result above belongs to the immutable beta 6 build.

## What remains unproven

One ordinary idea producing the contracted complete, revised, technically
verified Markdown/EPUB through the installed plugin without corrective
operator prompts. A >90 literary result. Beginner usability. Repeated runs.
Claude/DSH end-to-end support. The older v46 book had complete exports but an
unmet literary gate; it cannot be counted as this plugin's acceptance proof.

See [research and product decisions](plugin-research-20261023.md) for source
attribution and the explicitly unproven onboarding hypothesis.
