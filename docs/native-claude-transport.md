# Controlled Claude subscription transport

The controlled book workflow can now dispatch its existing scoped roles through
Claude Code. The same controller owns the eight phases, source-bound corrections,
reader decisions, revision budgets, journal, export and completed resume. There
is no second book-writing agent in charge of the controller.

This is a development transport. A one-word native availability probe on October
11, 2026 resolved `opus` to `claude-opus-5-5` at medium effort using an existing
claude.ai subscription. That verifies connectivity and a model available to that
account, not a complete book or the historical Opus 5.0 model. Full-length Claude
acceptance is still pending; native Codex trials retain their original sources.

A second real probe passed through the installed bridge, native-call guard,
journal and response validator using the exact `claude-opus-5-5` ID at medium
effort. It preserved Unicode and the original native model-usage evidence.
The full automated suite passed 347 tests and the installer suite verified on
October 11, 2026. These checks still do not establish complete-book delivery.

## Starting a separate project

```bash
python book_genesis.py new ./books/claude-novel --host claude \
  --model claude-opus-5-5 --effort medium --author "Your Name" \
  --autonomous --chapters 12 --min-words 40000 --max-words 48000 \
  --weighted-quality-target 9.0 --idea-file idea.txt
```

Use an exact model ID enabled on your account. Changing native aliases are
rejected for a frozen unattended book. Existing books do not change providers or
models when a new transport is added. The original model, effort, source snapshot
and budgets remain required on resume.

## Authentication and isolation

The launcher checks the installed native CLI's advertised capabilities. Each
role runs in the host guard's new empty working directory with restricted mode,
no built-in tools, no skills, strict MCP selection, no local settings and no
session persistence. Native authentication remains inside Claude Code. The
bridge never reads, copies or stores an OAuth token.

`--bare` is deliberately absent: the installed CLI documents that bare mode does
not read OAuth and instead requires API authentication. The controlled Claude
bridge verifies `claude auth status` reports native claude.ai login, rejects
explicit API credentials or third-party routing in its environment, and never
adds a fallback model. Existing guided native sessions retain their own behavior.

## Original response evidence

The native JSON envelope is retained byte-for-byte as stdout, including a failed
response. Successful generations must identify exactly the frozen model in
`modelUsage` before their role document can be extracted. Provider errors are
reported before this success check; a zero-usage quota refusal does not falsely
claim that a different model wrote a response. Plain JSON is passed verbatim. When the
entire field is one JSON Markdown fence, the bridge removes only that outer
presentation wrapper and passes its exact enclosed JSON document. It records
which presentation was decoded; the original envelope and result field remain
unchanged in stdout. Extra prose, multiple blocks and non-object fenced payloads
are not salvaged. JSON string values, negative findings and story wording are
never edited. The existing schema, prose and evidence validators still decide
whether the response is usable.
Selected effort is supplied in both native argv and the child-only environment.

The wrapper regression was reproduced with all three original failed native
replies, without changing their hashes. A new real Opus call returned a fenced
negative response and passed on its first attempt, with unchanged verdict and
finding values. The updated full automated suite passed 359 tests; a fresh
full-length book run is required to establish delivery with this transport.

Passage-reference schemas can exceed Windows command-line limits. The bridge
sends the full role packet and schema through UTF-8 stdin. It additionally requests
a bounded structural schema through native `--json-schema`; long passage-ID
enums remain authoritative in the full host validator. Native `structured_output`,
when present, supplies the role document without changing its values. A present
invalid field cannot fall back to a more favorable textual result. Binary stream
handling preserves Unicode even when the launching console uses cp1252. The
pending response uses exclusive creation; existing evidence is never replaced.

The outer native-call guard still owns timeouts, retry reservations and original
receipts. The launcher owns the process job and shutdown. Failed authentication,
unavailable models or malformed responses remain visible failures, not empty
chapters or passing votes.

## Subscription limits

A proven native HTTP 429 session refusal with empty model usage and zero input,
output and cache tokens can defer a request until the provider's explicit reset
time. Python's standard-library `zoneinfo` converts the reported IANA timezone
using a pinned data-only archive shipped with the skill. Windows needs no extra
package installation; global settings and the system timezone remain untouched. Unknown formats,
ambiguous zones, authentication failures and other errors still stop with their
actual reason. There is no account, model or API fallback.

The journal preserves every failed physical request, the original native
envelope, its hashes and the saved retry deadline. It displays the wait and
retries automatically after a 30-second grace period. An interrupted wait resumes
from that deadline. Only verified zero-usage refusals are excluded from the two
model-attempt budget; malformed generated responses still consume it. The entire
book permits at most eight deferrals and twelve cumulative waiting hours.
These limits survive resume. Evidence is checked again after waiting and before
export; a changed refusal or deadline cannot refund an attempt.

This handling follows two frozen native books stopping at their first review
requests when the account reached its session limit. Those failed runs remain
failed with their original budgets. Synthetic tests use fake time and cover
interruption, receipt recovery, producer feedback, limits, tampering, complete
export and no-call resume. Native wait/resume acceptance is recorded separately.

The first real wait canary showed that the Windows native CLI ignores a
child-only `TZ=UTC` override and continues reporting `America/Sao_Paulo`. The
UTC-only candidate correctly refused to guess but failed recovery. The updated
parser preserves the reported zone, uses its actual transition rules, and rejects
nonexistent or ambiguous future daylight-saving times. Fractional UTC offsets
and a reset after local midnight are covered. The archive contains 598 TZif
records from the Python-maintained [tzdata 2026.5 release](https://pypi.org/project/tzdata/2026.5/),
with its original licenses and pinned wheel checksum; no package code executes.
The reproducible build is `python runner/vendor_timezones.py /path/to/the/pinned.whl`.
The [Python zoneinfo documentation](https://docs.python.org/3/library/zoneinfo.html)
describes the binary-data reader and timezone behavior used here.

## Validation boundary

Subprocess fixtures cover Unicode and large schemas, actual model metadata,
subscription checks, unexpected provider routing, failed native envelopes,
output preservation, fenced JSON without changed values, rejected ambiguous
wrappers and capability checks. A synthetic complete-book fixture
exercises all eight phases, revision, export and no-call resume with a Claude
project contract. Neither fixture establishes native literary quality or human
usability. A full native run must still pass the separately recorded acceptance
contract before this transport can claim unattended delivery.
