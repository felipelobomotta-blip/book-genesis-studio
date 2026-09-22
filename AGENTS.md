# Agent instructions

This repository contains Book Genesis, a set of Agent Skills for writing complete books inside an agent host.

## Writing a book from this checkout

When asked to create, plan, draft, audit, revise, score or package a book, use the installed `book-genesis` skill. If it is not installed, read `skills/book-genesis/SKILL.md` and follow it, resolving `references/...` paths from `skills/book-genesis/`.

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
