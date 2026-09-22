---
name: book-genesis-codex
description: "Use when the user wants the portable Book Genesis pipeline for Claude Code, Codex, Antigravity, Kimi, or another file-aware agent: intake, foundation, architecture, drafting, adversarial audit, Genesis Score, and editorial package with durable project files."
---

# Book Genesis Universal Core

Book Genesis Universal Core is Felipe's portable book-production pipeline for file-aware AI agents. It works in Claude Code, Codex, Antigravity, Kimi, and similar tools that can read project files and write artifacts.

The skill folder is still named `book-genesis-codex` for compatibility with existing installs and slash commands. The workflow is not Codex-only. It is the canonical lightweight workflow for new runs, separate from the legacy V4/V5 multi-skill system kept elsewhere in this repository.

Use this skill for:

- fiction, memoir, nonfiction, or hybrid book projects
- turning a rough idea into a structured book
- drafting full manuscripts chapter by chapter
- auditing AI-written prose and narrative structure
- producing Genesis Score evaluations
- creating synopses, cover briefs, launch/editorial packages, and formatting handoff notes

Do not use the legacy V4 17-phase workflow as the default. It is copied only for historical reference in `references/legacy-v4-book-genesis.md`.

## Core Rule

Persist important decisions to files. A Book Genesis run should leave a durable project tree, not just chat output.

Default project layout:

```text
<project>/
  PROJECT_STATE.yaml
  ASSUMPTIONS.md
  artifacts/
  manuscript/
    chapters/
  evaluations/
  delivery/
```

## Canonical Pipeline

Load `references/pipeline/manifest.yaml` before starting or advancing phases.

1. Phase 0: Intake
2. Phase 1: Foundation
3. Phase 2: Architecture
4. Phase 3: Drafting
5. Phase 4: Adversarial Audit
6. Phase 5: Final Score
7. Phase 6: Editorial Package

Use `references/pipeline/phases.md` for the compact phase overview.

## Phase References

Read only the prompt for the active phase:

- Intake: `references/prompts/intake.md`
- Foundation: `references/prompts/foundation.md`
- Architecture: `references/prompts/architecture.md`
- Drafting: `references/prompts/drafting.md`
- Adversarial Audit: `references/prompts/adversarial-audit.md`
- Final Score: `references/scoring/genesis-score-codex.md`
- Editorial Package: `references/prompts/editorial-package.md`

`references/prompts/orchestrator.md` contains the portable orchestration rules.

## Operating Loop

1. Identify or create the project directory.
2. Read `PROJECT_STATE.yaml` if it exists. If not, initialize it from the manifest phases and user idea.
3. Read `ASSUMPTIONS.md` if it exists. If not, create it and mark inferred assumptions clearly.
4. Load the current phase prompt and produce only that phase's required outputs.
5. Update `PROJECT_STATE.yaml` after every phase, chapter block, audit, or score.
6. Do not skip Phase 4. Audit before final scoring.
7. When drafting, write in chapter files under `manuscript/chapters/` and keep the state synchronized.
8. When user feedback changes direction, record it in project files before continuing.

## Quality Policy

- Prefer fewer constraints during drafting; evaluate and repair afterward.
- Separate drafting, audit, scoring, and editorial judgment in the workflow.
- Use the Genesis Score floor principle: the book is only as strong as its weakest major dimension.
- For Portuguese books, write artifacts and prose in Portuguese unless the user requests otherwise.
- If a task is only editing, scoring, or packaging an existing manuscript, start from the matching phase instead of forcing a full restart.

## Complementary Skills

Use these only when relevant and already available:

- `copy-editing` for prose-level cleanup
- `humanizer` for less synthetic phrasing
- `launch-strategy` or `content-strategy` for go-to-market assets
- `imagegen` or cover-specific workflows for cover ideation
