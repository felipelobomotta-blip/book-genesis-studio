# Recovering an oversized revision request

Normal resume preserves a book's installed runtime. It does not silently upgrade
an ongoing manuscript. A developer may explicitly repair a stopped autonomous
Codex book whose Phase 5 request exceeded the native input limit before dispatch:

```text
python plugin_entry.py recover-runtime "<book>" --archive "<new-archive-folder>"
python plugin_entry.py resume "<book>"
```

The archive must be new, outside the book, and have an existing parent directory.
The recovery command does not call a model. It checks exclusive ownership,
canonical manuscript hashes, the original installation and execution contract,
and prior file evidence. It copies and verifies the complete original book before
installing the current checkout through the normal installer. Existing snapshots,
attempts and consumed passes remain available. The public release is untouched.

The model, reasoning effort, production length, scoring references, scoring
methods and pass budgets must match. The recovery receipt binds the original
journal, archive inventory and old/new runtime hashes. Later resume/export checks
verify the receipt and historical attempt evidence. This is a recovered run, not
an uninterrupted test of the released package.

An undispatched oversized factual check keeps its original identity and packet.
The replacement check receives a separate `-compact` identity. Its source wire
references repeated literal passages while preserving every source, passage ID
and source hash. No book text is discarded. A negative review remains negative;
format recovery never substitutes for literary acceptance.

Already-started revision passes keep their original schedule. New passes repair
essential factual dependencies, then creative defects, then independent
proofreading. An obsolete proofreading proposal may leave the text unchanged;
that does not count as an accepted correction or a passing review.
