# Architecture

How Book Genesis 6.0 is put together, and why. The decisions behind it are recorded in [ADR 0012](adr/0012-book-genesis-6-one-skill-blind-critics.md).

## One product, three layers

1. **The skill** (`skills/book-genesis/`). Markdown instructions any agent host can load: a manifest of eight phases, one prompt per phase, three critic roles, a scoring rubric, an evaluator protocol, specialist references and a patterns library. This is the product.
2. **Three standalone skills** (`skills/beta-reader/`, `skills/editorial-package/`, `skills/literary-agent-panel/`). Useful on any manuscript, with no dependency on the core or on each other.
3. **The installer** (`runner/`). Copies the skill folders into a host, records checksums, verifies them, retires files an earlier version installed, and generates the Claude Code subagents from the role files. It never calls a model.

The host agent does the writing, with the author's own account and models. There is no hosted service, background process or bundled model runner.

## The pipeline

```text
idea
 └─ Phase 0 Intake ........ brief, comps, reader panel, independence setup   ┐
    Phase 1 Foundation .... characters, theme, voice + rhythm contract       │ check in
    Phase 2 Architecture .. outline with scene pressure, continuity ledger   │ after each
    Phase 3 Drafting ...... chapters; panel after ch. 1; checks every 5      │ phase
    Phase 4 Audit ......... read-only, quoted tickets, audit_status line     │
    Phase 5 Revision ...... panel gate + rubric gate, 3 passes each          │
    Phase 6 Final Score ... completeness, gates, independence                │
    Phase 7 Package ....... logline, blurb, synopsis, query, hook test       ┘
 └─ complete book + report + package
```

`skills/book-genesis/references/pipeline/manifest.yaml` is the single source for phase order, prompts, references and outputs. The installer's suite check refuses a manifest with a missing phase, a broken order, a missing prompt or reference, or no adversarial audit.

## State lives in files

Every book is a folder: `PROJECT_STATE.yaml` (one schema, `schema_version: 6`), `ASSUMPTIONS.md`, `RUN_REPORT.md`, numbered artifacts, chapters, evaluations, delivery and work. A new session in any host resumes from those files. A chapter is written to `work/attempts/` first and replaces the accepted version only after it is read back and accepted, so a failure never leaves a half-written chapter as the canonical one.

## Why the critics are trustworthy enough to listen to

The earlier versions let one context write, judge and approve its own prose, and revise until the judge agreed. 6.0 separates what each role may see:

| Role | Sees | Never sees |
|---|---|---|
| Writer | the plan and a per-chapter brief | the rubric, targets, verdicts |
| Blind reader | only prose, a persona card and the previous chapter's tail | the plan, targets, earlier scores |
| Auditor | the whole manuscript and the plan | targets, earlier scores, panel verdicts |
| Revision editor | quoted tickets and a preserve list | scores and targets |

Critics run at the strongest independence the host offers: another model family's CLI when one is installed, otherwise an isolated subagent (verified with a canary check where the host does not document isolation), otherwise the same context. The grade (A, B or C) is printed next to every verdict.

## Two gates, bounded

- The **panel gate** asks whether the book holds its readers: four blind personas (primary, hostile, adjacent-genre, casual), majority to turn the page, a defect needs two votes.
- The **rubric gate** tells revision what to fix: ten weighted dimensions, calibrated for internal inflation, against a declared target of 8.5.

Both must pass. Each gets at most three revision passes, and a revised chapter is kept only if blind readers prefer it to the previous one. When a gate does not pass, the book stops with an exact account of what is missing instead of looping until a critic agrees.

## Patterns with names attached

`references/patterns/` holds the measured patterns (prose ranges, structural beats, emotional arcs) with the books and studies they come from, plus machine-prose tells with ceilings in English and Brazilian Portuguese. Research may override a genre default only with a named comparable title and passage; a genre or language label alone is never evidence.

## What the installer checks

- Every shipped skill is self-contained: each `references/...` path it mentions exists inside it, nothing points outside it, and no retired skill is named.
- The Claude Code subagents in `agents/` match what their role files generate.
- Installed files match this checkout and the install record.
