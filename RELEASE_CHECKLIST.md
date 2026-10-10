# Release checklist

Copy into an issue when preparing a release and tick as you go. The current
checkout is the unreleased 5.1 recovery build. Record the exact commit tested;
do not transfer acceptance from an earlier snapshot to a later code revision.

## Checks

- [ ] `python runner/installer.py verify-suite` passes
- [ ] `python -m unittest discover -s tests -v` passes, and CI is green on Windows, Linux and macOS
- [ ] `python runner/installer.py generate-agents` leaves `agents/` unchanged
- [ ] A real install into each first-class host, then `verify-install`, then the host lists `book-genesis`
- [ ] Upgrading over a 5.x install retires the old skills and warns about anything changed

## Evidence

- [ ] Every complete book claimed for this release is in the casebook with host, model families, independence grade, time and cost
- [ ] `docs/compatibility.md` states exactly what ran where, and nothing more
- [ ] README and landing numbers (phases, readers, dimensions, targets) match the code

## Author-journey acceptance

- [ ] A fresh, complete idea-to-export run uses the exact release snapshot and records the resolved host, model and effort.
- [ ] The independent plan check occurs before drafting; the required continuity checks, full audit, bounded revision, proofread and final assessment have actual saved evidence.
- [ ] No maintainer repairs prompts, manuscripts, receipts, phase state or exports during the claimed autonomous run. Record any intervention and label a checkpoint replay separately.
- [ ] Interrupt and resume at a real checkpoint: accepted chapters remain unchanged, active children stop, and spent revision or retry budgets do not reset.
- [ ] Every counted reader and rubric report still matches the final source hashes and its original validation receipt; encoding damage and stale evidence remain failures.
- [ ] Current Markdown and EPUB exports contain the complete planned chapter set, meet the declared length contract and open successfully in a reader.
- [ ] A failed literary gate is disclosed in the package; a passing reader preference vote alone does not close a continuity defect.
- [ ] At least one full-length run and one independent beginner session support the public complete-book claim.

An explicitly supervised beta may disclose outstanding acceptance work. A
general-ready release requires the complete author journey and the supported
host checks above. Automated tests, a process exit code, a short-book export or
a single simulated score cannot substitute for these checks.

## Docs and version

- [ ] `VERSION` and the README version line
- [ ] `CHANGELOG.md` entry with Added, Changed, Removed and Migration
- [ ] `docs/architecture.md` if the pipeline or roles changed; a new ADR for any decision a contributor would need to know

## Tag and publish

- [ ] Tag `vX.Y.Z` on `master`
- [ ] GitHub release with the changelog entry and links to the casebook runs
- [ ] Landing page redeployed (Pages builds `web/` on push to `master`)
