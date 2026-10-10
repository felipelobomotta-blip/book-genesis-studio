# Preserve review receipts through Windows shell pipelines

The real native replay produced a valid rubric response and then saved its
validator output through a shell pipeline. The saved receipt contained 44
replacement characters in resolved manuscript quotations. Its first cited
passage no longer matched the manuscript. Of 27 saved reader validation
attempts inspected at that checkpoint, 26 also contained replacement
characters. These counts include failed attempts; they are not reader votes.

The raw model reports and manuscript remained unchanged. The defect was in the
transport of a validator's Unicode JSON output through differing Windows
encodings. New reader, rubric and book-verification CLI outputs use standard
ASCII JSON escapes. Parsing the JSON restores the exact original Unicode;
accents, smart quotes and non-Latin characters are not stripped or rewritten.
The rubric's original-receipt check now also rejects altered resolved passage
evidence, matching the existing reader-evidence check.

## Reproduction and checks

Using a frozen copy of the six-chapter text, its original real rubric report
and the matching catalog, the old and new validator commands were piped through
PowerShell with `PYTHONIOENCODING=cp1252:strict`. No model was called and no
existing receipt was overwritten.

| Saved receipt | Replacement characters | Resolved references | Original-receipt reuse check |
| --- | ---: | ---: | --- |
| Original live replay receipt | 44 | 30 | Rejected |
| Old command through shell pipeline | 44 | 30 | Rejected |
| New command through the same pipeline | 0 | 30 | Passed |

Additional real subprocess regressions run both reader and rubric validators
with `ascii:strict` and `cp1252:strict`, using smart quotes, Portuguese, Greek
and an emoji in the source. They require exact round-trip passage preservation.
A separate test requires rejection of an already-corrupted original receipt.
Installer verification passed; the full Windows suite passed **293 tests in
99.753 seconds**.

This change does not repair old evidence in place, improve a literary score or
establish autonomous full-book success. Any later revalidation must retain its
own identity and the original failed receipt. The live replay continues on its
earlier frozen snapshot, so the new output format is not counted as a fix
inside that already-running acceptance test.
