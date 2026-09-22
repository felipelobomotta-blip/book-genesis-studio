# Release checklist

Copy into an issue when preparing a release and tick as you go.

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

Release bars:

| Release | Needs |
|---|---|
| 6.0.0-beta.1 | the structure in this branch, and one complete book by the maintainer in Claude Code |
| 6.0.0 | one complete book by someone else in any first-class host, and one by the maintainer in each other first-class host |

## Docs and version

- [ ] `VERSION` and the README version line
- [ ] `CHANGELOG.md` entry with Added, Changed, Removed and Migration
- [ ] `docs/architecture.md` if the pipeline or roles changed; a new ADR for any decision a contributor would need to know

## Tag and publish

- [ ] Tag `vX.Y.Z` on `master`
- [ ] GitHub release with the changelog entry and links to the casebook runs
- [ ] Landing page redeployed (Pages builds `web/` on push to `master`)
