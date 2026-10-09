# Book Genesis 5.1 recovery validation — 2026-10-09

The official 5.0 creative policy is selectively recovered into an isolated development branch, retaining the current portable installation, native-call receipts, staged promotion and exports. No original source or frozen comparison manuscript was changed.

## Observed checks

| Check | Result | Boundary |
|---|---|---|
| Unit suite | 158 tests passed | Deterministic regression checks, not literary acceptance |
| Portable suite check | Passed | Self-contained references, phase order and generated roles |
| Skill frontmatter validation | Passed | Does not prove model behavior |
| Real 5.0 manuscript export | 12 chapters, 32,819 visible-prose words; Markdown, EPUB, DOCX and 182-page PDF passed | Historical draft export, not a new recovered-pipeline generation |
| Current delivery verification | Delivered; source/output hashes and format checks passed | Literary quality and human approval remain separate |
| Native causal canary | Authenticated Codex gpt-5.6-luna, high; one 28.38-second call; both cases passed with exact quotations | Synthetic contradiction and consistent control only |
| PDF visual check | Pages 1, 2, 93 and 182 inspected | Representative reading proof, not print-platform certification |
| Preservation | 148 original source files and 12 copied canonical chapters unchanged | Git metadata and global CLI bootstrap are outside this source-byte check |

## Defects caught and corrected

- Standalone HTML production comments appeared in reading formats and inflated counts. Outputs now omit them while retaining original source hashes; the count method is versioned as `whitespace_split_prose_v2`.
- Section headings and ledger tables appeared as raw Markdown in reading formats. EPUB/DOCX/PDF now render them semantically. DOCX content verification includes table cells in document order and rejects a missing table.
- Old reader reports could be reused after a canonical edit. The verifier checks the original receipt and raw report against the current source hashes, and reports missing or stale coverage rather than inheriting an old pass.
- Technical delivery could remain pending in saved state despite valid files. Export now commits `STATUS.json` with its receipt and outputs; the host reconciles YAML from actual verification.
- A shutdown regression test failed in the full suite and passed in isolation. Inspection showed that its fault injector waited for a second lock write that never happened, so it exercised ordinary timeout instead. Its three-second supervisor deadline also interrupted the allowed shutdown/fallback sequence. The corrected test injects on the actual post-launch PID binding, records the real owned PID, requires the failure receipt and dead child, closes subprocess pipes, and includes a full tree-timeout fallback case. It does not weaken the child-survival assertion or change production termination behavior.

The native CLI logged a nonfatal system-skill bootstrap directory-not-empty error before completing the canary. The exact recovered causal guidance was supplied in the frozen packet; no model tools were used. This is recorded, not a claim that global native-host startup is flawless.

## Still not run

- A new idea-to-complete-book generation with this recovered build.
- A comparative literary score for this build.
- Independent human reading feedback.
- Visual DOCX review, device-level EPUB reading and full acceptance in every supported agent.
- GitHub publication of this development branch.

The writing changes therefore remain a hypothesis to test. This build has verified local engineering and historical delivery evidence; it has no 9/10 or bestseller claim.
