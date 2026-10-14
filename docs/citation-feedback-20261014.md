# Exact citation feedback for bounded repair checks

The real Luna/high partial-group probe on a508e3a returned two invalid reports.
Five rejected quotes existed in another passage of the same assigned source;
another supporting quotation did not exist there. Generic `quote is absent`
messages gave no field index, rejected passage or source, making a large report
difficult to repair within its two attempts.

The validator now identifies the finding, one-based evidence row, passage ID,
source and rejected quote. It lists exact matches only within that same source,
using the existing literal/unique-whitespace matching rules. It never relocates
evidence, changes the report, suggests another version, infers missing prose or
accepts an invalid response. The model must return a valid corrected report.
The original report, failed validation, feedback and native receipts remain
hash-bound by the existing executor.

Only deterministic citation diagnostics are returned to the second attempt.
The full previous verdict is still excluded from reviewer context. No score,
attempt budget, literary threshold, native lifecycle or publication rule changes.
A negative editorial verdict remains negative. The failed native probe and its
unchanged original manuscript are preserved; they are not a successful review
or a completed-book result.

Regression coverage verifies exact error locations, same-source-only hints,
absent/invented quotes, unchanged raw reports and a bounded negative group
review that remains negative after format repair and idempotent on replay.
