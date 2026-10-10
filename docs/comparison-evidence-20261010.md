# Source-bound evidence for anonymous comparisons

The real revision replay lost additional reader calls to inaccurately copied quotations, including one Chapter 2 response and one Chapter 4 response. Those reports remain invalid and preserved. Current-draft readers already used paragraph references; anonymous A/B comparisons still used the older copied-quote format.

New comparison bundles now number every visible paragraph in Draft A, Draft B and the shared prose context. Each reader receives a schema-3 response format and a frozen catalog digest. The catalog exposes anonymous version labels and source hashes, with no filenames, chapter titles, revision identity, old scores or private A/B mapping. The four-reader order remains counterbalanced: the candidate appears first for two readers and second for two. The schema defines its paragraph-ID enum once through a shared reference rather than repeating the full list in every evidence field.

Validation rebuilds the complete catalog from all assigned files, checks its digest, resolves IDs in a separate receipt and retains the raw `A`, `B` or `same` vote unchanged. Negative votes and negative findings remain valid. A missing shared-context file, changed prose, truncated catalog, opposite version order, wrong identity or unknown ID cannot reuse a report. Legacy quote reports and schema-2 current-draft reads remain supported. A comparison is still not a final current-draft panel read.

## Live four-reader experiment

The experiment declared four fresh calls, no retries, and no required preference before dispatch. It used copied original and staged Chapter 4 prose, with the original Chapters 3 and 5 as shared context. These were test inputs, not a promotion into the live manuscript. All calls used the prepared native command, Codex CLI 0.156.1, `gpt-5.6-luna`, high effort and separate read-only contexts.

| Reader | Original evidence validation | Resolved references | Raw report SHA-256 |
| --- | --- | --- | --- |
| Lena | Passed first call | 8 | `901198f5248976913a710d497b352781349ee58732a774c0d3165e5a40419b1a` |
| Mark | Passed first call | 12 | `e0eaa734c46c6bc7f1280b3800e7cfd438dea4f599ccd52a4ccf07b0d8a2b769` |
| Priya | Passed first call | 11 | `d5dffcda486e7db161bdf985b4f112679dffc238473b2b52989b54c412eee8aa` |
| Airport reader | Passed first call | 6 | `4fdaa3886730b3c9b58cd1c4ec06c7fa69e52e3e6e9f2c338c6e556ffd5e06dc` |

All **37 references** resolved, and all original packet/response/stream hashes matched their native receipts. Each reader retained at least one concrete confusion finding. The probe promoted no chapter, injected no feedback into the ongoing replay and did not reset a revision budget. Four successful calls demonstrate this protocol in the stated sample; they do not establish a general reliability rate or literary improvement.

Installer verification passed, and the full stable Windows suite passed **284 tests in 107.808 seconds**. New regressions cover anonymous full-text catalogs, A/B/same votes, preserved negative judgments, shared-context changes, rehashed truncated catalogs, swapped ordering, invented IDs and protocol misuse. Tests of current-draft reader evidence and original quote reports also passed.
