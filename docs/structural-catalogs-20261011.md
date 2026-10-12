# Preserve structured plan citations in dense catalogs

The first fresh 24-chapter native full-novel trial failed before drafting.
Its native architecture response contained every required chapter field, but
the controller's dense-prose compaction merged multiple rendered field
paragraphs. Plan verification could locate only the first field in each block
and raised `Controller-rendered plan is missing a required chapter field`.
This was a controller regression, not a missing model response or an exhausted
author-input checkpoint. The original failed trial remains unchanged.

Dense catalogs now preserve Markdown **Field:** paragraphs as individual
citations, just as they already preserve headings. Ordinary prose still uses
the bounded contiguous-block representation. No text is selected, summarized,
rewritten or reordered; source hashes and exact quotation checks remain intact.
Each plan check still needs its required chapter fields. A genuinely missing
field continues to fail validation, and a supported negative judgment still
requires a bounded architecture repair.

Regression tests use the actual 24-chapter scale, verify all four coverage
checks per chapter and their separate field IDs, validate the resulting review
schema/report, preserve mixed prose and field boundaries and reject a missing
field. Fresh native plan and complete-book results are separate acceptance
evidence. The quality thresholds, scoring and revision budgets are unchanged.
