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

Deterministic fixtures verify these execution properties. They are explicitly
synthetic and are not literary or human-usability evidence. The original native
trial continues to test the frozen build; a subsequent fresh trial must test
these new changes. No market, bestseller, other-host or 90/100 claim follows
from passing this regression suite.
