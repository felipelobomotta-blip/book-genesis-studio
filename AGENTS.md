# Agent instructions

This repository contains Book Genesis, a set of Agent Skills for writing complete books inside an agent host.

## Writing a book from this checkout

When writing from this recovery checkout, read `skills/book-genesis/SKILL.md` directly and resolve `references/...` paths from `skills/book-genesis/`. A global installed skill may be a different release; do not silently use it to validate this build. For a project-local installation, run the installer's `verify-install` against this checkout before starting and record the installed version and file hashes in the run report.

- Start with `skills/book-genesis/references/pipeline/host-contract.md`, then `references/prompts/orchestrator.md`.
- Write the book in a folder outside this repository, or under `books/`, which git ignores.
- Never skip Phase 4, and never score before it.
- Critics never see targets or earlier scores; the writer never sees the rubric.
- Write the book and every message to the author in the book's language.

## Working on the repository

- Product instructions live in `skills/book-genesis/`. The three standalone skills live beside it and must not depend on it.
- `agents/` is generated. Edit `skills/book-genesis/references/roles/`, then run `python runner/installer.py generate-agents`.
- Before committing, run `python runner/installer.py verify-suite` and `python -m unittest discover -s tests -v`.
- See `CONTRIBUTING.md` for the rules and `docs/architecture.md` for the design.
