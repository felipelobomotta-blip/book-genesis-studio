# Release acceptance

A green suite, a complete file, a model verdict and a successful customer journey are different evidence.

```bash
book-genesis acceptance "books/my story" --minimum-words 50000
```

This command returns JSON and exit code 0 only when mechanical checks pass: chapter coverage, accepted source hashes, text integrity, pending rewrites, pipeline status, audit, Markdown inclusion, and EPUB archive/XML/manifest/spine integrity. It reports the current source fingerprint and call metrics. The default minimum is 50,000 words; use the requested scale for a short-book test.

It leaves release_ready false because human and platform gates require external evidence. Mechanical acceptance is not production approval.

## Benchmark protocol

Freeze a source revision or snapshot. Record Python, OS, provider/CLI versions, models, author request, call/time budgets, scripted versus human answers, and source fingerprints at start/end. Preserve failed attempts. Runs repaired across different code versions are not a controlled speed comparison.

| Case | Required evidence |
| --- | --- |
| Short fiction | Complete ending, distinct voices, credible resistance, consistent identities/dates, blind checks and full audit |
| Practical nonfiction | Stable examples, supported arithmetic, useful explanations, no invented citations |
| Full-length fiction | At least 50,000 words at the requested chapter count; all chapters audited and exported |
| Full-length nonfiction | Requested scale and structure; consistent examples, claims and references |
| Recovery | Checkpoint stop/resume, pause during a slow call, transient failure, authentication failure and unusable output |
| Installation | Fresh wheel with all runtime resources and no checkout dependency |
| Platforms | Separate live evidence for each advertised OS and connection |

Measure journey time separately from summed provider-call durations. Compare first visible text, median call time, calls per accepted chapter and repair overhead on identical inputs. Report variability; do not extrapolate tiny probes into book-generation speed.

## External gates

- Observe ten actual first-time users. Proposed target: nine complete the assigned short-work journey without developer intervention; no lost accepted text. Record confusion, assistance and ability to reopen/export. This small convenience sample does not establish population-wide reliability.
- Obtain independent human feedback on complete books, preferably blinded comparisons. Record criteria and unresolved objections. Model personas are not participants.
- Open EPUBs in real reading software and inspect navigation, language, headings and layout. XML validity alone is insufficient.
- Repeat full-length cases before making reliability claims. One short book cannot validate a novel-generation promise.

Unperformed sessions remain unverified. Never populate the evidence ledger with invented readers or results.
