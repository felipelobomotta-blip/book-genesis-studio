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
response. Its `modelUsage` must identify exactly the frozen model before the
public result field can be extracted. Plain JSON is passed verbatim. When the
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
sends the role packet and schema through UTF-8 stdin, then uses the common host
validator. It does not claim provider-side schema enforcement. Binary stream
handling preserves Unicode even when the launching console uses cp1252. The
pending response uses exclusive creation; existing evidence is never replaced.

The outer native-call guard still owns timeouts, retry reservations and original
receipts. The launcher owns the process job and shutdown. Failed authentication,
unavailable models or malformed responses remain visible failures, not empty
chapters or passing votes.

## Validation boundary

Subprocess fixtures cover Unicode and large schemas, actual model metadata,
subscription checks, unexpected provider routing, failed native envelopes,
output preservation, fenced JSON without changed values, rejected ambiguous
wrappers and capability checks. A synthetic complete-book fixture
exercises all eight phases, revision, export and no-call resume with a Claude
project contract. Neither fixture establishes native literary quality or human
usability. A full native run must still pass the separately recorded acceptance
contract before this transport can claim unattended delivery.
