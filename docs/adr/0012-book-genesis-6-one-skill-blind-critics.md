# ADR 0012: Book Genesis 6.0, one skill with blind critics and bounded gates

Status: accepted on 2026-09-22 by the maintainer, after a three-round design interview. Supersedes the 5.0 package layout; keeps ADR 0011's agent-native direction.

## Context

A full review of 5.0 on 2026-09-22 found that the install layer was sound but the product layer carried three earlier generations: five overlapping descriptions of the pipeline, a 98 KB copy of the core that had already diverged, two incompatible `PROJECT_STATE.yaml` schemas in one bundle, a skill instructing agents to run a file that no longer existed, a mandatory script on the maintainer's desktop, two skills copied from third parties without attribution, and pattern files that nothing could read because every consumer pointed at a folder that did not exist. The system also graded its own prose and revised until its own evaluator agreed.

A second line of work, a command-line runner that called models directly (`release/imagination-edition`), had diverged into a different product. The maintainer chose the agent-native skills as the only product; that line is frozen under the tag `archive/imagination-edition-2026-09-22`, and its best ideas are ported here.

## Decisions

1. **Product.** One core skill, `book-genesis`, runs inside the author's host agent. No CLI of its own. First-class hosts: Claude Code, Codex, OpenCode, Hermes Agent, OpenClaw. Other targets stay installable and labeled untested.
2. **Goal, not promise.** A complete, commercial-length book written with measured bestseller patterns, audited the way a demanding editor would audit it, and packaged to sell. Never a promise of sales.
3. **Check-in by default.** The author agrees at every phase boundary, after chapter 1, and every fifth chapter. "Go to the end" switches to autonomous mode. An absent author leaves the book at a saved checkpoint.
4. **Blind critics, measured independence.** Blind readers see only prose; the auditor sees the plan but never targets; the writer never sees the rubric. Independence levels, in order: a second tool from another model family, an isolated subagent, the same context. The grade is always reported and never blocks the "complete" label. Where a host does not document subagent isolation, a canary check tests it. (From archived ADRs 0001 and 0008.)
5. **Two gates, three passes each.** The four-persona reader panel decides whether the book holds readers; the ten-dimension rubric, target 8.5 after calibration, decides what to fix. Both must pass; each gets at most three passes, and a revision is kept only when blind readers prefer it. (Panel and comparison from archived ADRs 0001 and 0002.)
6. **Audit verdict line.** The audit ends with `audit_status: pass`, `revise` or `major_rewrite`; `major_rewrite` always stops for the author. (From archived ADR 0015.)
7. **Attempts before publication.** Chapters are written to `work/attempts/` and replace the accepted version only after read-back and acceptance. (From archived ADR 0011.)
8. **Continuity.** A ledger built in Phase 2, checked every five chapters and in the audit, with targeted repairs of quoted passages. (From archived ADR 0016.)
9. **Patterns with sources.** The knowledge files move into the skill as `references/patterns/`, contradictions resolved, unsourced statistics removed, and machine-prose tells written in English and Brazilian Portuguese. Every prose rule names a comparable book; research follows the book's language (contributed by Thinh Hoang in PR #14).
10. **Rhythm has one owner.** The voice file's rhythm contract holds a baseline and an envelope; the writer moves inside the envelope only where the outline marks scene pressure. Resolves issue #35.
11. **Package.** One core skill with specialists as references, plus three standalone skills: `beta-reader`, `editorial-package`, `literary-agent-panel`. Claude Code subagents are generated from the role files and checked for drift in CI.
12. **Cut.** Removed: `book-genesis-full`, `book-genesis-codex`, `optional/`, `deprecated/`, the eight V4 agents, `humanizer` and `copy-editing` (third-party copies), `book-bestseller-studio`, `book-swarm-panel` and the other folded specialists, launch and marketing material, and sixteen outdated documents. Git history and the archive tag keep all of it.
13. **Surface.** Product surface in English; the book and every message to the author in the idea's language. Fiction and memoir first-class; nonfiction works but is not calibrated. EPUB and PDF only when pandoc is present.
14. **Release.** `6.0.0-beta.1` ships with this structure and one complete book by the maintainer in Claude Code. `6.0.0` requires one complete book by someone else and one by the maintainer in each other first-class host, all recorded in the casebook with independence, time and cost.

## Test seams

- `runner.distribution.find_skill_problems`: missing references, paths outside the skill, retired skill names.
- `runner.distribution.read_frontmatter`: wrapped and block descriptions, unterminated frontmatter.
- `runner.distribution.resolve_install_root`: blank and relative home variables for every target.
- `runner.agents.render_agents` and `agent_drift`: generated subagents match role files; strays are reported.
- `runner.distribution.install_suite` and `verify_install` through the command line: every target, Claude subagents, retirement of 5.x files, failure without a traceback.

## Consequences

Projects started in 5.x need a one-time state migration, described in the host contract. The skill's quality now depends on host features the installer cannot test, which is why the release criteria are complete books, not green tests.
