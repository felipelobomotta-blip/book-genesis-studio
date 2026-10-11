# Regressions observed in the full-book native trial

The frozen `f4e7b35` build generated a real 12-chapter, 45,310-word first draft
using official Codex and `gpt-5.6-luna` at high effort. Its first calibrated
weighted literary score was 72.13/100. Revision and final delivery were still in
progress when the changes below were prepared in a separate checkout. These
observations do not establish 90/100 quality or completed autonomous delivery.

The active trial's code, installed skill, original responses and budgets were
left unchanged. The new implementation needs its own fresh native acceptance
run after the technical checks pass.

## Missing writer context

The approved foundation contained a particular history of public blame, but
the first-draft packet carried names and dialogue habits without the relevant
character cards. The full audit later found that history underdeveloped. New
identities and object transfers could also occur before the preceding chapter's
last 300 words, and compact writer summaries were not a reliable substitute.

The writer now receives the relevant approved cards verbatim and the full
preceding chapter. A legacy card format falls back to its approved character
document rather than disappearing. Regression coverage proves that an early
identity and custody transfer survive the handoff while an unrelated named card
and future payoff map stay out of the normal scoped packet. This proves input
retention, not that a model will execute the prose perfectly.

## Correction proposals failed by recopying the original

Two attempts to fix dialogue typography both changed a phrase while transcribing
the `before` text. Exact matching correctly rejected those unsafe proposals,
but the typo remained. A separate heading-format ticket collided with an overly
broad ban on changing any heading byte; the next proposal edited unrelated prose
and was correctly blocked by the independent checker.

Editors now name immutable paragraph IDs or inclusive ranges and give only their
new text. The controller supplies the original range, so an invented `before`
value cannot cause this failure. Unknown, reversed or overlapping ranges,
all-no-op proposals, missing text and title rewrites are rejected. Typography
may remove only a recognized redundant `Chapter N:` prefix while preserving the
actual title. All accepted candidates still need the existing independent
correctness evidence and guarded publication. Tests cover repeated identical
paragraphs, CRLF and surrounding whitespace, source corruption, title changes,
and a corrected chapter continuing through export and no-call resume.

## An unchanged chapter was evaluated again

The opening's draft checkpoint reported a shared attention dip. Measurement 0
read the same chapter again and reported no shared dip, despite no intervening
edit. Both sets of original reports remain part of the frozen trial.

The updated reader-panel path reuses the first validated read when the entire
packet, schema and command are identical. It revalidates the response against
the current source and retains its original receipt. A negative verdict cannot
be replaced by asking the same reader again on unchanged prose. Changed prose
gets fresh reads; modified historical evidence blocks reuse. The two rubric
replicas remain separate calls. This removes redundant calls and a source of
misleading improvement without lowering any quality threshold.

## Validation boundary

The newer Opus run exposed another lossy handoff at its five-chapter continuity
check: later chapters changed an early mentor's name and the month/method of a
payment. The earlier source prose contained those details, but the writer's
own continuity summary omitted them. The chapter-four packet did not contain
either mentor name. Supplying only the preceding chapter and accumulated
summaries therefore still discarded established facts from older scenes.

Future chapter packets now carry every earlier published chapter verbatim, in
order, as well as the immediately preceding chapter and the local plan. The
writer is told to treat that prose as the source of established facts and keep
character knowledge separate from reader knowledge. Summaries remain labelled
provisional. This does not expose future planned chapters, critic reports or
score targets. A four-chapter controller regression checks an early fact omitted
from every summary and from the immediately previous chapter. Larger input is
the explicit tradeoff: prompt size grows with the written manuscript. A native
run of this new handoff is still required; the running Opus book remains frozen.

One native run reached a complete manuscript but stopped when the revision
planner exhausted its bounded attempts: a timeout followed by a response that
omitted a mandatory historical finding. The timeout remains a transport failure,
and that original run is still blocked. It is not relabelled a completed book.

For the separately verified case where both attempts return intact native
responses that fail only output validation, the controller now retains the
current complete manuscript, its original reviews and all unresolved findings,
then delivers it explicitly as an unapproved draft. It never executes incomplete
revision tasks or rerates unchanged prose. The failed attempts remain hashed
evidence, and resume cannot create a third planning attempt or another pass.
Authentication, transport and altered evidence still block delivery.

An actual controller interruption test also reproduced unstable generated
reports at the end of Phase 5. The journal writes sorted JSON keys, while the
Markdown reports embedded insertion-order JSON. Resuming after reports were
saved but before the phase advanced could therefore reject the controller's own
unchanged content. Those reports now serialize deterministically. Tests cover
both a valid revision and an exhausted invalid plan, byte-identical reports on
resume, no repeated revision or evaluation calls, original evidence tampering,
and an authentication failure that must remain blocked.

The controlled panel caller also omitted an existing input supported by the
packet builder: the blind-reader role specifies the previous chapter's final
300 words, but the caller never supplied `context_chapter`. Readers consequently
received a later chapter without that intended transition context. This is a
verified handoff defect; it does not by itself invalidate any particular opinion.

The caller now freezes a separate copy of the preceding chapter for each reading
scope and lets the existing builder expose only its final 300 visible words.
The outline, future events and quality targets remain excluded. The context copy
and manifest are bound to the measurement evidence so later canonical revisions
cannot overwrite what an earlier reader saw. Identical visible input retains its
original negative reads; changed context triggers new reads. Missing context or a
changed source under an existing scope blocks before dispatch. These changes are
tested separately and are not applied to either active full-book run.
The complete suite passed 361 tests after this context fix, including negative
read reuse, changed-context dispatch, immutable history and missing-context rejection.

The first full Claude trial from `28334cc` stopped in foundation after two native
responses wrapped their JSON in Markdown fences. The JSON content was present,
but the strict transport treated presentation syntax as part of the document.
Its earlier intake had recovered automatically from the same first-attempt error.
The failed run is retained; no successful foundation or book delivery is claimed.

The Claude bridge now decodes one complete outer JSON fence while retaining the
native envelope byte-for-byte and the exact enclosed document. It does not edit
JSON values, prose, scores or findings. A second block, extra explanation,
malformed JSON or fenced non-object is rejected. Common role schemas and evidence
validators still run afterward. Real failed replies are replayed read-only into
separate QA files; a fresh native book must test the updated transport.

The same running Luna trial later made a false length allegation: its audit
treated a chapter's planning estimate as a hard limit and inferred a whole-book
overflow. The complete measured manuscript contained 45,088 prose words within
the frozen 40,000-48,000-word contract. The reviewer had the prose and planning
documents but no deterministic count record.

Neutral review sources now include counts computed from the exact supplied
snapshot by the same prose counter used for export, together with the original
chapter and whole-book length requirements. Audit, historical-finding follow-up
and revision planning receive this record. Per-chapter planning estimates are
identified as guides; pacing remains a literary judgment. Private quality targets,
grades, model identity and previous verdicts never enter this record. Partial or
duplicate snapshot inputs are rejected. This is source evidence, not an automatic
deletion of a negative finding or an instruction to approve the book.

This additional handoff passed the full 355-test suite and installer verification.
The earlier prepared Claude project had made no model call when it was superseded;
the updated source receives its own fresh installation and acceptance record.

A subsequent frozen `5ff430c` run produced a 46,758-word first draft and an
initial calibrated score of 70.32/100. Its unchanged opening and midpoint reused
all eight original reader responses, including an unfavorable opening result.
Paragraph IDs removed the old `before`-copy failure, but some proposed repairs
still failed the factual checker. Better transport does not establish better prose.

One rejection exposed a report-contract ambiguity: a reviewer returned `pass`
and all three checks true, but put a positive summary in the `findings` array.
The gate correctly refused to treat a nonempty findings list as approval. The
new packet and schema reserve that array for unresolved blocking defects; positive
explanations and observations about unchanged unrelated defects belong in evidence
reasons. A validator now rejects internally contradictory reports and missing
source coverage before the decision. A fresh format attempt receives no earlier
verdict. A coherent negative report remains final and never triggers rerating.

After two malformed optional correction checks, the candidate is rejected, its
original evidence remains bound to the journal, and the accepted chapter stays
available for the remaining workflow. Transport, authentication and altered
evidence still block. Regression tests exercise the actual controller decision,
original report retention, negative verdicts, exhausted attempts, no-call retry
after exhaustion, evidence tampering and transport failures. This change is
tested separately and is not injected into the active native trials.

The resulting build passed all 352 automated tests and `installer.py verify-suite`
on October 11, 2026. Its native Claude transport also passed the separately
recorded real scoped-response probe. Full-length acceptance remains ongoing.

Deterministic fixtures verify these execution properties. They are explicitly
synthetic and are not literary or human-usability evidence. The original native
trial continues to test the frozen build; a subsequent fresh trial must test
these new changes. No market, bestseller, other-host or 90/100 claim follows
from passing this regression suite.

## Distant evidence in revisions

The frozen `85579f2` Opus run reached a complete 47,930-word draft, then rejected
a chapter 3 factual repair because the verifier could not see chapters 1 and 12.
The ticket cited those chapters as the source for a repeated object's material
and price. The actual verifier response explicitly reported that neither
chapter's text was supplied, and that the summary documents omitted those facts.
This was an orchestration failure: rejecting an unsupported correction was
correct, but the controller had withheld the existing source evidence.

Each revision now freezes the complete current manuscript. The editor receives
all other chapters verbatim, and the factual checker receives the same frozen
chapters as citable canon sources. The blind preference readers still receive
their bounded anonymous comparison packet. Planning documents are not treated
as proof that an event happened. Conflicting sources can still produce a block;
supplying more context never overrides the verifier's judgment.

The regression exercises the controller with a correction in chapter 3 whose
only evidence occurs in chapters 1 and 5. It checks the editor packet, full
checker sources, original bytes, source-bound promotion and no repeated call
when the completed revision is resumed. No active native trial is patched.

## Numeric feedback separation

The same real run exposed a numeric Prose cap inside a critic's explanation.
Removing the structured `score` field alone did not prevent the revision planner
from seeing that number. The planner explicitly recorded the leak.

Editorial handoffs now make a separate view of feedback that omits sentences
containing explicit numeric evaluation language. Nearby defect observations,
passage IDs, dates, prices and source quotations are retained. Original critic
responses, scores and receipts are never modified. The boundary also applies to
the strategy and tickets sent to a prose editor. It is a conservative text
filter, not a guarantee against every possible paraphrase of a rating.

Tests reproduce the real cap sentence, decimal and Portuguese notation, nested
evidence, legitimate story numbers, and the complete controller path. The raw
score stays in its original report while the authoring packets exclude it.

The complete suite passed 372 tests in 255.078 seconds, with installer suite
verification. A read-only replay of the real twenty-dimension critic feedback
removed the numeric cap from both Prose explanations while retaining their
concrete prose observations. The original measurement hash and scores remained
unchanged. This is boundary evidence; the new build still needs a fresh native
full-book run.

## Incomplete comparison recovery

Trial 12 subsequently stopped during its first revision pass: the fourth
comparison reader returned paragraph IDs but omitted `schema_version` and
`catalog_sha256` twice. The controller had no complete verified panel and
correctly withheld promotion, but incorrectly stranded the entire manuscript.
The failed 47,803-word run remains preserved without an export. Its 70.74/100
baseline predates accepted revisions and is not a score of the stopped text.

The comparison path now treats two verified output-validation failures as a
rejection of that optional candidate. It retains the earlier chapter, original
responses and invalid attempts, records the missing reader, and proceeds within
the existing three-pass budget. It never invents a fourth vote, repairs raw
critic output, rerates unchanged prose or overrides a valid negative verdict.
Authentication, transport and evidence alteration still block. Regression tests
exercise actual export and no-call completed resume, plus tampering and native
authentication failures. Reader instructions now show the catalog response as
their primary example, including both mandatory binding fields.

The Claude bridge also requests a native structural schema using
[`--json-schema`](https://code.claude.com/docs/en/headless#get-structured-output).
The complete role schema still travels over stdin and is enforced by the host.
Only long source-ID enums and annotations are omitted from the bounded native
command argument. Required fields, ordinary enums and structural types remain;
an oversized command fails before model dispatch. Source citations, scope,
reviews and prose constraints still need their original validators.

When present, the native `structured_output` object supplies the role document;
its values and the complete original envelope are preserved. An invalid
structured field cannot fall back to a more favorable text result. Older public
result envelopes still use the existing validated decoding path. Subprocess
fixtures verify these boundaries. A real native canary is required before the
next full-book test; the two ongoing native books remain unchanged.

## Repair correctness before creative preference

Code inspection found another gap between the existing method and controlled
execution. The revision method requires inspecting whether a candidate fixes
its assigned tickets before spending comparison reads. The controller applied
this distinction to factual corrections but sent creative candidates directly
to preference voting. A preferred chapter could therefore still omit the
required setup or preserve the original causal mistake until the next audit.

Creative proposals now receive one fresh, read-only viability check with the
original and candidate text, all other current chapters, and the author
contract. The check covers the actual ticket, dependencies, preserved strengths
and authorized scope, with cited evidence in both versions and supporting
current-book sources. Planning notes or hypothetical later edits cannot supply
missing causal evidence. A check cannot approve its own prose or substitute for
the anonymous preference panel. The latter receives no repair verdict.

A coherent negative result rejects that proposal without rerating it. Two
malformed results retain the accepted manuscript and original failed attempts.
Authentication, transport and altered source evidence still block. Evidence is
verified again after the comparison calls and before publication. An interrupted
run reuses the original verified check rather than spending another call.

Focused synthetic controller regressions cover rejection before preference,
successful repair followed by blind voting, invalid source citations, native
authentication failure, changes to original review evidence during comparison,
interruption and completed no-call resume. These establish control behavior;
native literary improvement from this additional check remains unverified.

The final implementation passed all 386 automated tests in 290.681 seconds and
installer suite verification. A reproduced resume failure caused solely by
JSON field ordering was fixed with deterministic serialization; reloading the
same task in a different key order now reuses the original review. Native
component canaries and a fresh full-book run remain required.

## Native subscription limits before model execution

Fresh trial 14 wrote twelve chapters and 47,938 words, then native Claude refused
both initial-audit requests with HTTP 429, zero token usage, empty modelUsage and
an explicit session-reset time. Trial 16 stopped at the plan checker for the same
reason, before writing chapters. The bridge checked modelUsage first, producing
a misleading identity error; an immediate second request exhausted the role.
Neither book completed review or export. Original failed runs remain preserved.

The bridge now reports provider errors before checking successful model identity.
For the narrowly recognized zero-usage session refusal, the controller durably
waits until the native UTC reset plus thirty seconds. Raw failed receipts remain
physical requests; only these verified refusals are excluded from the two model
attempts. The entire book has eight deferrals and twelve cumulative waiting hours.
No account, model or API fallback occurs. Unrecognized errors remain failures.

Regressions cover zero-versus-nonzero usage, explicit reset parsing, midnight,
crash after receipt persistence, interrupted waits, source/receipt tampering,
producer feedback across a wait, durable model and wait budgets, full fixture
export and completed no-call resume. A cp1252 subprocess test also exposed mixed
stderr encodings; all bridge error diagnostics now emit UTF-8 bytes consistently.
Native component and full-book acceptance remain separately required.

The final candidate passed all 403 automated tests in 314.387 seconds and the
installer suite. The combined case of a quota wait followed by two malformed
optional revisions retains the original chapter, records both rejections and
exports the reviewed unapproved draft; its completed resume makes no model call.
This synthetic recovery result does not establish native complete-book delivery.

The subsequent native canary failed before any model usage: the Windows CLI
kept reporting `America/Sao_Paulo` despite the child-only UTC environment. Its
two original refusals remain failed; no trial-18 book was prepared or launched.
The follow-up handles the named zone using frozen IANA TZif data instead of an
environment assumption or a hardcoded UTC offset. The data-only archive comes
from checksum-pinned `tzdata 2026.5` and retains the upstream licenses. The
standard-library reader handles midnight and fractional offsets, and refuses
ambiguous/nonexistent DST times. It needs no global package installation and
does not change the user's clock, native settings or timezone. New native quota
recovery and complete-book validation are still required for this follow-up.

The named-timezone follow-up passed 407 automated tests in 338.689 seconds and
installer verification. Rebuilding the data-only archive from the pinned wheel
produced the same SHA-256. Tests decode all 598 shipped zones, reproduce the
actual Sao Paulo refusal, handle fractional offsets and local midnight, and
reject nonexistent or ambiguous future DST times without installed tzdata.

## Interdependent factual corrections cannot be approved in isolation

Frozen Codex trial 17 produced twelve chapters and 46,432 words, then received
an initial internal calibrated score of 71.73/100. Its review identified a
chronology conflict across several chapters. The first plan assigned separate
factual corrections; the checker rejected each because the other current
chapters retained the incompatible chronology. Some proposals also contained
unrelated wording changes, which correctly remained blocking findings. The
original refusals are preserved. Later accepted edits make that baseline score
stale; no new score or final delivery is inferred from those promotions.

The follow-up groups factual tasks connected by the same historical issue,
including transitive connections. It stages every member, checks the assembled
proposed book in one fresh evidence-bound review, and publishes all authorized
members through a durable transaction. Original chapters and companion
proposals are labeled separately; proposals cannot establish their own facts.
One unsupported or incomplete member rejects the group. Unsupported chronology
choices must still use creative revision, and sequential creative repairs remain
subject to their existing full-context viability check.

Ten targeted regressions cover coordinated promotion, preserved originals,
negative and malformed reports, independent factual support, transitive groups,
interruption between files and after claiming an original inode, concurrent
author edits, tampered reviews, full fixture export and a completed resume with
zero new calls. Original group sources remain verified even after export.
The fixture writes real Markdown and EPUB files but uses a synthetic transport;
it does not establish native literary improvement. Real component and fresh
full-book acceptance remain required for this candidate.

The final candidate passed all 417 automated tests in 330.238 seconds and the
installer suite. Native component verdicts, full-book delivery and the literary
90/100 target are separate outstanding checks, not conclusions from this count.

## Reader format constraint omitted from generation schema

Trial 17 stopped during the first revised-manuscript measurement after 127 native
requests. It retained twelve chapters and 45,468 words, with accepted revisions,
but did not reach final scoring or export. The adjacent reader for chapter 10
returned a long emotional reaction twice. The validator required `felt.emotion`
to be at most 120 characters; the generation schema only said it was a string.
Both original failed responses remain unchanged, and the old trial is not retried
under a different schema or with a reset budget. Its baseline score is stale.

The shared reader schema now sends that existing bound as `maxLength`, with an
explicit short-label description and a separate unrestricted `felt.reason`.
Single-chapter and comparison readers use the same bound as the host validator;
native Claude schema compaction retains it. No reaction is trimmed, rewritten or
accepted by weakening the validator. Native acceptance is separately required.

## Referenced craft knowledge missing from tool-free authoring calls

Inspection of actual draft and revision packets found that the native roles
could not access the prose-craft definitions referenced by their instructions.
The editor received links to the eight repair moves, but not their definitions,
while the scoped native command prohibited file access. The writer received the
book's voice and character cards but none of prose-craft sections 1-5, which the
existing specialist explicitly permits during drafting. This was a handoff gap,
not evidence that sending more instructions automatically improves a novel.

The follow-up supplies only material permitted at that phase. Drafts get optional
sections 1-5, without revision moves or AI-tell checking. The planner and creative
editor get the existing repair definitions and patterns, including the applicable
English or Portuguese AI-tell reference; unsupported languages do not silently
use English rules. Factual editors and blind readers do not receive that creative
repair library. Original reference files remain unchanged, and editor views omit
executable snippets and rubric cross-links. Tests exercise the actual full
fixture workflow, export and no-call completed resume while inspecting the
packets sent to each role. Literary improvement still requires a real book test.


The candidate passed all 423 automated tests in 381.376 seconds and the installer suite check. The six new checks include a complete synthetic workflow with no-call completed resume and real packet inspection; this is not native book acceptance. Full native trial 20 of its predecessor separately stopped after three bounded architecture repairs, with unresolved departure timing and physical clue dependencies. Its original ten responses and failed state remain preserved. No manuscript was written or delivered by that trial.
