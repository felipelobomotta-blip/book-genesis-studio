---
name: book-genesis
description: Use when someone wants to write a complete book from an idea, even a one-line one, or to continue, audit, revise or package a book in progress. Book Genesis plans the book, drafts every chapter in a consistent voice, has blind simulated readers and a read-only auditor critique it, revises in bounded passes, and delivers a commercial-length manuscript with a scored report and an editorial package (logline, blurb, synopsis, query letter, cover brief). The author agrees at each step or lets it run to the end. Fiction and memoir first; nonfiction works but is not calibrated.
---

# Book Genesis

Take an idea to a complete, commercial-length book inside the author's own agent: planned, drafted, read blind, audited, revised and packaged, with every decision saved to files.

The goal is a book written with the measured patterns of books readers finish, audited the way a demanding editor would audit it, and packaged to sell. It is a goal, not a promise: no workflow can guarantee sales.

## Start here

1. Read `references/pipeline/host-contract.md`. It covers starting, resuming, checking in with the author, and recovering from failures.
2. Read `references/prompts/orchestrator.md`. It is the main loop.
3. Open or create the author's book folder. If `PROJECT_STATE.yaml` exists, resume from it; otherwise start at Phase 0 with whatever idea the author gave.

Resolve every `references/...` path from this skill's folder. The author's files live in the book folder:

```text
<book>/
  PROJECT_STATE.yaml   ASSUMPTIONS.md   RUN_REPORT.md
  artifacts/           plan, audit, score and package files (00 to 13)
  manuscript/chapters/ chapter-01.md, chapter-02.md, ...
  evaluations/         panel verdicts, continuity checks, revision passes
  delivery/            proofread manuscript and exports
  work/                chapter briefs, draft attempts, critic packets
```

## The eight phases

Load only the active phase's prompt and the references `references/pipeline/manifest.yaml` lists for it.

| Phase | Prompt |
|---|---|
| Phase 0: Intake | `references/prompts/intake.md` |
| Phase 1: Foundation | `references/prompts/foundation.md` |
| Phase 2: Architecture | `references/prompts/architecture.md` |
| Phase 3: Drafting | `references/prompts/drafting.md` |
| Phase 4: Adversarial Audit | `references/prompts/adversarial-audit.md` |
| Phase 5: Revision Loop | `references/prompts/revision-loop.md` |
| Phase 6: Final Score | `references/scoring/genesis-score.md` |
| Phase 7: Editorial Package | `references/prompts/editorial-package.md` |

`references/pipeline/phases.md` is the one-screen overview.

## What makes the criticism worth reading

- **Critics are blind.** Readers see only prose; the auditor sees the plan but never targets or earlier scores; the writer never sees the rubric. `references/scoring/evaluator-protocol.md` sets who sees what.
- **Independence is measured and shown.** Critics run in isolated subagents or in a second installed tool from another model family when the host allows it (`references/hosts.md`). Every verdict carries its grade.
- **Four readers decide, not one.** Primary, hostile, adjacent-genre and casual readers, built per book (`references/roles/panel.md`, `references/roles/blind-reader.md`).
- **Two gates, bounded.** The panel decides whether the book holds readers; the rubric (`references/scoring/genesis-score.md`) decides what to fix. Three passes per gate, then an honest stop.
- **Measured patterns, named sources.** `references/patterns/index.md` points to prose, structure and emotion patterns from named books and studies, and to machine-prose tells in English and Brazilian Portuguese.

## Specialists

Load when the phase calls for them:

- `references/specialists/research.md`: comps and market in the book's own language
- `references/specialists/narrative-foundation.md`: characters, theme, voice and the rhythm contract
- `references/specialists/prose-craft.md`: openings, chapter endings, dialogue, revision moves
- `references/specialists/continuity.md`: the ledger and the five-chapter checks
- `references/specialists/revision-editor.md`: ticket-driven, targeted revision
- `references/specialists/production.md`: proofreading and export
- `references/specialists/series.md`: only when the book belongs to a series

## Rules that never bend

- Save important decisions to files; keep `PROJECT_STATE.yaml` true to what exists.
- Never skip Phase 4, and never score before it.
- Write the book and every message to the author in the book's language.
- A book is "complete" when it meets its length contract (or a declared short form), every planned chapter exists, and the package exists. Quality gates are reported beside that label, never hidden.
- Never claim a book will sell, is a bestseller, or is ready to publish without a human decision.
