# Phase 7: Editorial Package

Give the finished manuscript what it needs to meet agents, editors and readers, tested on simulated readers before anyone real sees it.

When to load: Phase 7. Roles: orchestrator, research specialist for positioning, production specialist for proofreading and export, reader panel for the hook test.

## Outputs

- `artifacts/12-editorial-package.md`:
  - logline, one or two sentences, market-legible;
  - back-cover blurb that sells without spoiling the ending;
  - editorial synopsis for professionals, ending included;
  - query letter, with comps and no inflated claims;
  - cover brief that signals genre, tone and audience at thumbnail size;
  - formatting notes for ebook and print.
- `artifacts/13-positioning.md`: the hook test and the recommended package.
- `delivery/`: the proofread `manuscript.md`, validated EPUB, `export-receipt.json`, and `EXPORT.md`, produced by the portable `scripts/export_book.py`; DOCX/PDF are optional formats when their libraries already exist (`references/specialists/production.md`).

## Hook test

1. Draft three to five packages, each a title, a logline and a blurb, that differ in angle, not only in wording.
2. Run the panel in hook-test mode (`references/roles/panel.md`) with each package and the first 250 words of chapter 1.
3. Rank the packages by yes answers to click, buy and keep reading. Record every reader's reasons, the winner, and the runner-up.
4. Write the recommendation in `artifacts/13-positioning.md` with the comps and category from `references/specialists/research.md`, labeled as a simulated signal. It is a reason to prefer one package, not a sales forecast.

## Rules

- The package promises only what the manuscript delivers.
- Proofreading changes spelling, grammar and consistency. It does not rewrite style; any larger change is a ticket, and the author decides. Complete `evaluations/proofread.md` before Phase 6 freezes the final score. Phase 7 consumes those locked canonical chapters and never writes corrections directly into `manuscript/chapters/`.
- If production finds a new defect after Phase 6, return it to the orchestrator for a staged Phase 5 revision, affected evidence rerun and Phase 6 score refresh. Do not create a production-only edit or skip reader votes.
- Before export, reconcile the plan and state and confirm that every planned chapter exists; a contiguous subset is not a complete book. For a complete-book delivery, use the actual approved intake/outline contract values and run the portable helper with `--require-complete-pipeline`, `--expected-chapters`, `--min-words`, and `--max-words` before the final inventory. Its default delivery is `manuscript.md` plus a validated EPUB and receipt; do not make pandoc a prerequisite. Never install software. Optional DOCX/PDF or a pandoc alternative may be used only when already available and requested. The preflight requires nonempty canonical pipeline evidence but does not require a literary pass: a failed audit or score is still valid evidence when saved. Standalone draft exports remain allowed without the preflight flag. If a host, permission, quota, incomplete-source, missing-evidence, or count-contract blocker remains, preserve the checkpoint and write `delivery/DELIVERY_STATUS.md` (or `delivery/EXPORT.md`) with `status: blocked`, the exact error, and the next action; do not claim delivery or completion.
- Close the book with the inventory from `references/pipeline/host-contract.md`.
