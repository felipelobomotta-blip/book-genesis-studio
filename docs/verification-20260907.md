# Verification — 2026-09-07

Writer on Codex `gpt-5.6-luna` at high effort, judge and reader panel on Claude
`claude-opus-5` at medium. Both live, both on this machine, both this date.

## What the previous record listed as blocked, and what it actually was

| Reported | Measured on 2026-09-07 |
| --- | --- |
| `codex login status` returns Not logged in | `Logged in using ChatGPT`, exit 0. A bounded `gpt-5.6-luna` high probe returned in **12s** |
| A `claude-opus-5` medium call times out | Bounded probe returned in **8s** |

Both were shell-scoped, not product-scoped: the earlier probes used 20s and 60s
ceilings against a cold start that takes eight to twelve, in a terminal without
Codex auth. Nothing in the runner had to change for either.

## A capability that was described but unreachable

The adapters have always accepted a reasoning level, and `tests/test_cli_effort.py`
proved the flag reaches both CLIs — but nothing in the runner ever built an
adapter with one. There was no config key and no flag, so **a run planned as
"writer on Luna high, judge on Opus medium" could be written down and never
configured**; every call went out at the CLI default while the plan said
otherwise. The test passed and the feature did not exist.

`effort` is now a per-role config key, read by `models.yaml` and the user config,
passed to the Claude and Codex adapters, and printed by `doctor`. The adapter
cache is keyed by `(adapter, effort)`: sharing one instance across roles would
have given every role on a CLI whichever level happened to be built first.

## A defect found by running the product

A first three-chapter run scored **8.0 / 10** with chapter 3 blocked. The blind
reader had said `turn_page: yes`; the continuity repair pass then failed its
checks, and one assignment —

```python
accepted = _accepted(check) and not remaining
```

— wrote the repair's verdict back over the chapter's own. Declining an
*improvement* discarded the accepted prose it was improving, and the chapter
ended with no canonical text at all. The whole gap between 8.0 and 10.0 was that
one line.

A failed repair now means two things with opposite answers: with canonical text
present the rewrite is refused and the canonical text survives (unchanged rule,
already pinned by `test_continuity_memory`); with nothing canonical yet the
accepted draft is published carrying its unresolved findings into
`RUN_REPORT.md`. Chapters 1 and 2 of that same run shipped with a recorded
`continuity` flag — a visible finding beats a missing chapter.

## The run that closed it

Same idea, same models, after the fix:

```
GENESIS SCORE: 10.0 / 10 — model readers turned every page
  Reader panel            100%  3 of 3 blind readers would turn the page
  First-draft acceptance  100%  3 of 3 chapters accepted on the first draft
  Chapters accepted       100%  3 of 3 chapters accepted in the end
  Memorable               100%  3 of 3 chapters left the reader with something specific
```

9,135 words over three chapters. 21 provider calls, **0 failed**, median call
66.5s. The judge produced specific reader criticism rather than approval — it
named the line where it skimmed, the reread it gave, and the point where the
dialogue "becomes a machine". That is the cross-family gate of ADR 0001 working
as designed.

## Clean-machine installation

Wheel built from this checkout, installed into a fresh virtualenv outside it:

- both entry points created (`book-genesis`, `book-genesis-studio`)
- CLI runs with the checkout absent from `sys.path`
- packaged resources present: `web/` 4 files, `config/` 3, `data/` 50
- `doctor` reads the role plan including effort
- Studio serves `HTTP 200`, and `/api/state` **refuses an unauthorized request**

## Suites

435 Python tests. 3 JavaScript tests via
`node --test tests/web/studio_poll.test.cjs` — pointing `node --test` at the
directory fails on Windows because Node treats the directory itself as a failing
test. `python -m compileall runner tests` clean.

## What is still not established, and cannot be from here

`acceptance` returns `release_ready: false` on this book and is right to: it is 3
chapters of a 40-chapter outline, so `chapter_coverage`, `pipeline_complete` and
`whole_book_audit` fail by construction. Every integrity check passes — accepted
source hashes, text integrity, Markdown coverage, EPUB order, manifest, XML,
staleness.

The four external gates the command declines to decide remain open, and no
machine run closes them:

- **human literary review** — a person reading the book
- **novice usability** — an observed session with someone who has not seen it
- **platform matrix** — live evidence per advertised OS
- **full-length repetition** — repeated 40-chapter books with live providers

Nothing has been pushed to GitHub. The four commits are local.
