# Preserve the exact target of a planning correction

The fresh native Codex Luna/high trial 41 stopped before drafting after its
three permitted plan repairs. A reviewer identified a Chapter 8 custody
contradiction, but the repairer wrote the replacement into Chapter 9 and then
Chapter 18. Literal edit application was correct. The repair packet supplied
zero-based JSON paths, one-based chapter numbers and review passage IDs without
binding the cited passage text to its editable fields.

The repair packet now supplies a chapter/address table, current editable field
values, and the original cited passages with their literal editable paths.
Bindings use the exact rendered source spans and verify the catalog's source
hash. Multiline continuations, complete promise blocks and continuity-ledger
bullets retain all overlapping editable fields. The approved brief remains
read-only evidence. An unknown reference or changed source fails closed.

This is address information, not an editorial verdict or an automatic repair.
The native author still chooses the substantive change and a fresh independent
review still decides whether the revised plan is coherent. Numeric chapter
assignments remain outside the existing text-only repair contract. No scoring
weights, thresholds, attempt limits, revision limits or review gates change.

Seven deterministic regressions cover Chapter 8 versus Chapters 9 and 18,
read-only brief evidence, unknown IDs, multiline passages, ledger and promise
bindings, source drift, and the actual planning packet. The existing planning
fixture now decodes the first JSON value rather than assuming that no further
context section follows it.

Two isolated native Luna/high reproductions of the initial patch changed the
requested Chapter 8 field and preserved unrelated chapters. Both subsequent
plan reviews still rejected their candidate: the later starting plan contained
inherited incorrect Chapter 9/21 edits, and the earlier starting plan had other
POV/calendar findings. These are targeting evidence, not approved plans. Their
original negative reports and trial 41 remain intact. The final implementation
also addresses multiline and ledger bindings found in code review; it is not
the exact helper snapshot used by those two native probes.

The first full regression run executed 533 tests and recorded two errors in
one Windows process-lifecycle test (a two-second retry timeout followed by a
locked cleanup file). That run overlapped one native plan probe. All 22 host
guard tests passed when rerun alone; the production guard and its timeouts
were not changed.

The following 536-test run exposed a different fixture race: an 80 ms timeout
correctly killed the child before it wrote its startup marker. A deterministic
reproduction delayed the real child's startup by 300 ms and reproduced that
failure. The test now records the created PID from the controller and checks
that it is dead, the timeout receipt verifies shutdown, the ownership lock is
released and an unrelated live process survives. The same delayed-start
reproduction passes without changing the 80 ms timeout or production code.

A read-only replay of all four original trial 41 plans also bound every cited
outline/ledger passage to current editable fields. It used no model calls and
verified that the original failed trial files remained byte-for-byte intact.

Final verification: all 536 tests passed in 505.936 seconds with no concurrent
native book job. `python runner/installer.py verify-suite` also passed. These
are regression and packaging results; the full-book acceptance below remains
separate.

The next fresh complete-book trial remains necessary. No complete-book,
literary-quality, human-reading or sales acceptance follows from this patch.
