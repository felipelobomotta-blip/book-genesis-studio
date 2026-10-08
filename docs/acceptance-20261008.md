# Complete-book acceptance work — 8 October 2026

The acceptance goal is one idea producing a complete, revised, exported book without a person repairing the running process. Automated tests, supported install destinations and valid export files each verify only part of that goal.

## Verified source checks

- 120 automated tests passed on Windows using real temporary files and subprocesses, with no model calls in that suite.
- The portable-skill checks and generated-role consistency check passed.
- Commit `6e6bae2f93ee68c16076b9d868b6ec2ef90b1b8b` passed GitHub CI on Windows, Linux and macOS with Python 3.10 and 3.12. Subsequent instruction changes require their own CI results.

## Real-host acceptance attempts

All three attempts below used the same English speculative-mystery idea and a 12-chapter, 30,000–34,000-word novella contract. They were separate empty-folder runs. None is claimed as a passing complete-product acceptance test.

| Attempt | Observed result | Why it failed acceptance |
|---|---|---|
| Initial Codex run | 12 chapters, 30,124 prose words; Markdown, EPUB, DOCX and PDF exported; independent text and hash preservation checks passed | Missing canonical audit artifact, invalid accepted reader evidence, and child reasoning settings that differed from the requested High configuration |
| Explicit Luna High repeat | Seven chapters before interruption | The supervisor inspected a running writer too early and launched a duplicate into the same attempt path |
| Luna High with native-call guard | Seven chapters before interruption; 28 completed calls with correct model/effort headers, intact receipt hashes and no overlapping call intervals | The supervisor forced empty defect fields in three reader retries, compromising their judgment. The draft also drifted from a one-night brief into a multi-day plan; checkpoint state lagged the saved files |

The interrupted attempts and their logs were preserved locally. No manuscript was manually repaired and then relabeled as unattended success. The first run's word count uses whitespace-separated prose, excluding chapter headings; its earlier token-based report used a different counting convention. The exporter now records a named deterministic method.

## Corrections and the next test

The native-call guard now serializes existing CLI calls and exposes responses only after completion. Reader validation checks required structure and exact quotations. Export preflight checks the required phase evidence, chapter inventory and approved word range. Technical proofreading belongs before final scoring.

The later instruction corrections require a brief-to-outline contract check before drafting, retain complete reader-role instructions on retries, and prohibit suppressing findings to obtain valid JSON. Reports obtained through such suppression are degraded even when their JSON validates.

A fresh mixed-host attempt uses a Claude Opus 5 Medium coordinator and critics with Codex Luna High writers. Its result is **pending**. A successful result on that configuration would be evidence for that tested configuration, not for every supported host or every book length. Simulated reader scores do not establish human readership, sales, bestseller quality or publication approval.
