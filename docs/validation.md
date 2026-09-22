# Validation record — Imagination Edition

This is an engineering evidence record for `v5.1.0b1`, updated on September 8, 2026. It distinguishes software behavior from manuscript quality. A passing test suite does not establish that the resulting books are publishable.

## Latest local verification — September 8

The current checkout passed **473 Python tests in 66.14 seconds**. This includes preservation of complete rejected phase responses and reuse during an author-approved correction. Malformed responses cannot publish incomplete artifacts or overwrite the saved failure record. The earlier suite counts below describe historical runs.

Fresh bounded probes outside the restricted development sandbox passed for `gpt-5.6-luna` at high effort (9.34 seconds) and `claude-opus-5` at medium effort (4.95 seconds). The earlier sandbox login result was not evidence that the user's host CLI was logged out. Connection probes establish connectivity only.

The [September 7 campaign](verification-20260907.md) produced three chapters from a forty-chapter outline. It must not be described as a completed book. A separate complete two-chapter campaign began September 8 with scripted approvals; its final audit and delivery are unverified until that run finishes.

## Studio and portable verification — September 8

Browser interaction exposed a modal-layer bug: rejected API input displayed a toast behind the active dialog. Feedback now stays visibly inside the dialog until it closes. Browser retests confirmed missing-model and invalid-request-limit messages. At 390 pixels, the progress rail appears above the manuscript, the activity log is not hidden, and the page has no horizontal overflow. Desktop workspace layout was also inspected at 1280 pixels.

A simulated local HTTP endpoint exercised the graphical API workflow through the actual browser, Studio server and OpenAI-compatible adapter: distinct writer and reader checks, visible slow-response activity, a rejected model, and a successful sample through the previously accepted setup after that rejection. Remember was unchecked; no real API credentials were entered. This is transport/UI evidence, not a live Ollama or commercial API verification. Luna and Opus connectivity were tested separately against real providers.

The portable executable was rebuilt after these UI changes and launched outside the checkout with a fresh temporary library. Authenticated state, bundled JS/CSS equality, and graceful shutdown passed. Executable SHA-256: `f919cc070173986bdfeec862ab9094aa7ea23b218db88e78c909224acd05e03d`. The matching ZIP has SHA-256 `02c881f5f0190f0829bbbf3a5daaf61a7bec14df1926a2609307849ff2ed1c17`. These checks ran on the developer's Windows machine, not a clean installation. JavaScript syntax and all three polling regressions passed after the feedback change.

## Automated verification

The publication checkout passed **418 tests in 65.33 seconds** on Windows with Python 3.11. The suite includes interrupted phase recovery, immutable attempt history, canonical text/hash integrity, persisted author checkpoints, adapter errors and timeouts, audit rejection, local reader escaping and containment, Markdown/EPUB integrity, live Studio activity, provider preflight, and package resources installed outside the source checkout.

The wheel test builds the package, installs it into an isolated temporary target, changes out of the source directory, and exercises the installed resource lookup. The configured GitHub workflow runs the same suite and a wheel build on Windows and Ubuntu with Python 3.10 and 3.12. Its current remote results are visible in [GitHub Actions](https://github.com/felipelobomotta-blip/book-genesis-v4/actions/workflows/test.yml).

Independent code review identified issues in provider isolation, publication recovery, history integrity, and manuscript audit gating during the quality pass. Those findings were corrected and reviewed again; the final focused audit-gate regression set passed 21 tests. Review does not guarantee the absence of defects.

## A real provider exercise

A limited run used Claude for writing and Codex for the model-reader panel. It produced one 1,910-word Portuguese chapter, *Data de Devolução*. The three reader personas used the same judge model; they were not three human readers or three independent model families.

The original panel accepted the chapter and the process card reported 10/10. A later audit of the **full manuscript prose** found that the ending did not resolve a key premise distinction: disappearance versus death. It requested **MAJOR REWRITE**. That contradicted the favorable early signal and exposed a software issue: an audit artifact existed, but its editorial rejection had not blocked completion.

The corrected implementation requires an explicit audit status. `revise` and `major_rewrite` keep Phase 4 current with `awaiting_revision` and exit code 4. A replay using the saved real audit response verified that Score and Package did not run and that the canonical chapter remained unchanged. That replay used frozen responses; it was not a second live-provider book generation.

See the [case study](../examples/data-de-devolucao/README.md) for the artifact fingerprint and implications.

## Reader UI evidence

The local reader was exercised at desktop and narrow phone dimensions during the quality pass. The public [reader sample](../examples/reader-demo/README.md) uses scripted English text to make navigation, attempt history, comparison, and audit status reproducible. Its screenshot is captured from the actual HTML reader. Neither the sample nor its fixture verdicts measure literary quality.

## Limits still open

- No completed human-reader preference study or publication outcome study.
- No validated relationship between the internal Genesis Score and sales, literary quality, or human preference.
- One short real-provider exercise does not establish long-book continuity, context-window behavior, or reliability across every adapter.
- CLI/API configuration remains part of onboarding. Ease of use for people new to terminals needs direct user testing.
- A rejected structural audit blocks completion. Interactive sessions offer an author-approved repair campaign and repeat the whole-book audit; unattended runs stop for revision. Repair is not guaranteed to succeed.
- Model services can time out or reject a request. In the live exercise, a Claude audit timed out at 180 seconds; a later Codex audit path returned a usable result.

The appropriate release status is **beta**. The next evidence should come from reproducible first-chapter runs and consenting human readers, with the model verdicts kept separate from human feedback.

## Reproduce the software checks

```bash
python -m pip install pytest rich wheel setuptools
python -m pytest tests -q
python -m pip wheel --no-deps --no-build-isolation --no-cache-dir --wheel-dir dist .
```

No API key or live model call is needed for the regression suite. Live provider runs are separate and may incur the selected provider's costs.

## Clean-runner findings

The first GitHub CI run exposed three unit tests that depended on installed Claude/Codex commands, a doctor test that depended on local provider configuration, and a Windows-only separator in a rollback fixture. The fixtures now declare their environment explicitly and use path components. Their behavioral assertions remain in place. The latest isolated local suite passed 418 tests; remote matrix results remain inspectable in GitHub Actions.

## Remote matrix result

Commit `4ba8ce2` passed all four GitHub jobs: Windows/Python 3.10, Windows/Python 3.12, Ubuntu/Python 3.10, and Ubuntu/Python 3.12. Each job ran the regression suite (including isolated wheel installation) and built a wheel. [Inspect the successful run](https://github.com/felipelobomotta-blip/book-genesis-v4/actions/runs/33947757174). The Windows process-tree test is deliberately platform-specific.
