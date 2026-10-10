# Deterministic comparison decisions

During the real native revision replay, the orchestrator wrote its own tally
script and reported fixing a branch-selection bug in it. A later Chapter 5
comparison illustrates why the product should own this calculation: all four
readers chose anonymous Draft A, but the counterbalanced order meant two votes
for the candidate and two for the accepted text. Its separate complaint-count
calculation grouped complaints by which draft each reader preferred. That does
not measure defects in each draft. The candidate was rejected, so this evidence
does not show an incorrect canonical promotion.

`skills/book-genesis/scripts/decide_comparison.py` now translates votes from the
original private mapping. It revalidates the four original responses and their
saved validation receipts against all frozen source files, anonymous catalogs,
packets and schemas. Changed evidence, swapped mappings, stale sources and a
report reused as two readers are rejected. The original raw votes remain intact.

The automatic route authorizes only a complete, decisive panel with at least
three votes for the revision. `same` stays neutral and `unsure` is not changed
to a decisive signal. A two-two split keeps the accepted text pending separate,
source-bound evidence of fewer defects in the candidate. The helper does not
derive those counts from the complaints of readers who liked either version,
and does not solicit replacement readers to break a tie.

## Verification

Six regressions exercise a real temporary-file promotion and byte-for-byte
backup, the all-A counterbalanced tie, neutral votes, altered raw responses and
validation evidence, swapped mappings, reused reports and an existing decision
that must not be overwritten. The generated blind-reader instructions now also
distinguish schema-3 comparison catalogs from legacy copied-quote reports.

The helper was then run against the four original real-model reports from
[the anonymous comparison experiment](comparison-evidence-20261010.md), with
their original receipts. It produced three revision votes and one accepted-text
vote: Lena A, Mark B and Priya A mapped to the revision; Airport reader A mapped
to the accepted text. No response was regenerated, no additional model call was
made and no chapter was promoted in this tally check. The decision's private
manifest digest is
`6b45356e01b73a7cc637a47af3e418dda930cae71dfcadd8a64d65c04342f348`.

Installer verification passed. The full Windows regression suite passed
**290 tests in 103.396 seconds**. These are workflow and evidence checks, not a
literary-quality score. The ongoing replay uses its earlier frozen skill
snapshot; this helper has not been injected into that run or counted as proof
that the complete current release passes autonomous acceptance.
