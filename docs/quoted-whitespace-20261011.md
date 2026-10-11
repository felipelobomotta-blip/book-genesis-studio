# Physical line wrapping in repair evidence

A native dense repair control correctly identified a new custody contradiction,
but flattened physical line breaks when quoting the supplied prose. Both format
attempts failed literal substring validation. The original run and failure are
retained; this change neither accepts that old run nor changes its verdict.

The repair validator first uses its existing exact substring rule. If that
fails, it allows whitespace differences only at the quotation's existing word
boundaries. Every other character, including case and punctuation, must match.
The normalized match must occupy exactly one location within the already
assigned passage. It cannot search another passage, swap versions, skip words,
complete an ellipsis or reconstruct an inferred event. Ambiguous matches fail.

Validation metadata records the original source excerpt, passage ID, source,
finding and row, matching rule and character offsets. The native response and
its execution receipt remain untouched. The changed-mechanism test uses the
same whitespace rule: joining lines does not make unchanged prose a new
regression. Interpretation, scope checks, negative verdicts, group publication,
two format attempts, revision budgets and literary grading stay unchanged.

Local tests cover the actual wrapped synthetic-control failure, literal source
metadata, report immutability, Unicode whitespace, ambiguous overlapping
matches, altered words and punctuation, omitted text, source swaps and unchanged
mechanisms. Fresh native controls and complete-book acceptance are separate
outcomes; a unit-test pass does not establish them.
