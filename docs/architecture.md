# Architecture

Coordinated repair findings carry the source contract described in
[repair-findings-20261011.md](repair-findings-20261011.md).

The dated metadata input for unattended planning is described in
[research-snapshot-20261011.md](research-snapshot-20261011.md).

How the 5.1 recovery build is put together. The creative policy returns to 5.0; portable installation and reliability retain the later design in [ADR 0012](adr/0012-book-genesis-6-one-skill-blind-critics.md). See [the recovery record](v5-recovery.md) for evidence and limitations.

## One product, three layers

1. **The skill** (`skills/book-genesis/`). Markdown instructions any agent host can load: a manifest of eight phases, one prompt per phase, three critic roles, a scoring rubric, an evaluator protocol, specialist references and a patterns library. It also ships deterministic file helpers for safe chapter promotion, strict blind-reader JSON validation and portable export. A separate native-command guard launches a caller-supplied existing CLI and records its completion; it is not a provider API client.
2. **Three standalone skills** (`skills/beta-reader/`, `skills/editorial-package/`, `skills/literary-agent-panel/`). Useful on any manuscript, with no dependency on the core or on each other.
3. **The installer** (`runner/`). Copies the skill folders into a host, records checksums, verifies them, retires files an earlier version installed, and generates the Claude Code subagents from the role files. It never calls a model.

The host agent does the writing with the author's own account and selected model. There is no hosted service, persistent background worker, provider API backend or subscription-token proxy. The optional [native launcher](native-cli.md) prepares a verified local skill installation. Guided projects hand the terminal to the unmodified Codex or Claude Code CLI. New unattended Codex and Claude projects use the [controlled native workflow](controlled-native-acceptance.md): the skill's `scripts/autonomous_book.py` owns phase order and dispatches scoped read-only roles through the same native-command guard. It consumes the shared manifest, role instructions, readers, promotion rules, rubric and exporter; no second LLM orchestrator operates beside it. Authentication stays in the official CLI.

`workflow_state.py` reserves calls and revision passes before dispatch, stores immutable request/evidence bindings, recovers interrupted publications and rejects unrecorded manuscript changes. `workflow_roles.py` validates structured planning and review artifacts. The host's model can produce creative work and judgments but cannot edit control state or choose when to export. The existing guard serializes native calls, preserves each attempt, and reports completion only after the child exits and its response is saved. The controlled path has Codex and [Claude subscription transports](native-claude-transport.md); each host's real acceptance status is tracked separately from guided and synthetic tests.

`provider_wait.py` recognizes only native Claude quota refusals with zero usage and an explicit session reset in a known IANA timezone. A pinned data-only timezone archive and Python's standard-library reader make the UTC conversion portable to Windows without installing dependencies. Ambiguous future times are rejected. The journal retains these failed physical requests and waits durably without spending a generated-output attempt. It permits eight deferrals and twelve cumulative waiting hours per book, verifies their original evidence on resume/export, and never changes account, model or provider. Other transport errors remain blocking failures.

Writer packets carry the relevant approved character cards and the complete preceding chapter. This keeps motivations, newly introduced identities and object transfers available even when a writer-generated summary omits them. Future chapter resolutions and quality targets remain outside that packet.

Factual editors address immutable paragraph ranges and supply only the proposed replacement text. `correction_edits.py` obtains the baseline from the frozen original, rejects overlapping or unknown ranges, and preserves every byte outside an accepted range. A heading may lose a redundant `Chapter N:` label while keeping its actual title; a retitle still requires creative revision. The independent factual checker and promotion guard inspect the complete difference before publication. Each revision freezes the complete current manuscript so both editor and factual checker can verify facts outside adjacent chapters. Blind comparison readers retain their limited packet. `editorial_feedback.py` removes explicit numeric evaluation sentences from the editorial view without changing raw critic reports, source quotations or scoring.

Factual tasks connected by a historical issue ID are staged together. `correction_groups.py` gives a fresh reviewer the complete original book and every companion proposal, clearly labeled as unaccepted. It checks the assembled proposed book while requiring independent original-book or contract support for each corrected fact. A valid negative verdict rejects the entire group. Two malformed reviews also retain the original group; authentication, transport and evidence failures still block. Conflicting on-page chronologies that need a new canon choice remain creative work, not factual corrections.

Technical group reviewers and historical-issue reconciliation receive specific output-contract errors on their existing second format attempt. They do not receive the previous review or scores. Completed evidence binds the failed response and validation used by that retry, and group publication verifies the exact resulting native packet. Blind preference and literary readers are unchanged. See [review format feedback](review-format-feedback-20261011.md) for the native failure behind this correction.

An approved factual group is published through one durable transaction. Export cannot proceed with a pending transaction. A restart verifies the original native review, source hashes, every current chapter and transaction-owned original holders before finishing interrupted replacements; it does not ask the model again. Concurrent author edits are preserved and stop recovery. Group sources, reviews, decisions and publication receipts become Phase 5 evidence and remain checked after delivery. This is recoverable group publication, not a filesystem-wide atomic rename.

Tool-free authoring roles cannot follow links to other skill files. `craft_context.py` therefore sends the actual permitted knowledge: prose-craft sections 1-5 as optional draft knowledge; the existing repair moves, prose and structure patterns and applicable language-specific AI-tell reference to the revision planner and creative editor. Factual editors receive no stylistic rewrite library. Executable reference snippets and rubric cross-links are excluded from editor views; the original references remain unchanged. Blind readers never receive this library. Unsupported languages do not silently inherit English AI-tell rules.

Creative revisions first receive a separate repair check against the original chapter, the proposed chapter, the complete other current chapters and the author contract. `revision_viability.py` requires source-bound evidence for ticket resolution, causal consistency, preserved strengths and authorized scope. Only a passing repair goes to the anonymous preference panel; that panel does not see the task or the repair verdict. A valid negative repair check rejects the candidate without another attempt to change its verdict. Two malformed checks also retain the accepted chapter, while transport or evidence failures still block. Original check evidence is verified again after comparison and before promotion. This implements the pre-comparison inspection already required by the revision method; it does not establish literary improvement until a native full-book test demonstrates it.

Creative tasks sharing issue IDs are also coordinated. `creative_groups.py` stages every proposal before acceptance, keeps originals separate from companion proposals, and reserves length for the staged changes. A source-bound reviewer checks every member's ticket, authorized scope, preserved strengths and causal dependencies in the assembled complete book. A passing group then receives four counterbalanced anonymous comparisons of both complete manuscript versions, including unchanged chapters. The only comparison transformation is lowering chapter heading levels below a common book heading; every prose byte is retained. The ordinary decisive three-of-four preference rule remains unchanged. Both gates must pass before the existing recoverable group transaction publishes any member. Invalid, incomplete, unchanged or rejected groups retain all original chapters. Actual native use of this path must be demonstrated separately from fixture tests.

Architecture format retries include the complete immutable rejected producer response and all duplicate-field diagnostics. The producer consolidates conflicting edits; the controller never chooses an after value by array order. The original two-format-attempt and three-substantive-repair budgets remain unchanged. Completed-book resume calls the full execution-evidence verifier before checking current readers and delivery, so a changed old revision source cannot be hidden by a valid final export.

Reader panels reuse the earliest original validated response only when the complete packet, response schema and selected native command are identical. Negative readings are retained as well as positive ones. A changed chapter receives new readings, and changed evidence blocks reuse. Two rubric replicas still run separately; this reuse policy does not turn one judgment into two independent evaluations. See [the observed native regressions](native-regressions-20261011.md) for the evidence behind these changes.

## The pipeline

```text
idea
 └─ Phase 0 Intake ........ brief, comps, reader panel, independence setup   ┐
    Phase 1 Foundation .... characters, theme, voice + rhythm contract       │ check in
    Phase 2 Architecture .. outline with scene pressure, continuity ledger   │ after each
    Phase 3 Drafting ...... chapters; four reader checkpoints; factual checks every 5      │ phase
    Phase 4 Audit ......... read-only, quoted tickets, audit_status line     │
    Phase 5 Revision ...... panel gate + rubric gate, 3 passes each          │
    Phase 6 Final Score ... completeness, gates, independence                │
    Phase 7 Package ....... logline, blurb, synopsis, query, hook test       ┘
 └─ complete book + report + package
```

`skills/book-genesis/references/pipeline/manifest.yaml` is the single source for phase order, prompts, references and outputs. The installer's suite check refuses a manifest with a missing phase, a broken order, a missing prompt or reference, or no adversarial audit.

## State lives in files

Every book is a folder: `PROJECT_STATE.yaml` (one schema, `schema_version: 6`), `ASSUMPTIONS.md`, `RUN_REPORT.md`, numbered artifacts, chapters, evaluations, delivery and work. A new session in any host resumes from those files. A chapter is written to `work/attempts/` first and replaces the accepted version only after it is read back and accepted, so a failure never leaves a half-written chapter as the canonical one.

The read-only `scripts/check_progress.py` helper compares the canonical chapter set and the exporter's deterministic prose count with the saved schema-6 progress fields. The host runs it before resuming and after checkpoints, reconciles mismatches from the actual saved work, and reruns it before continuing. Complete-pipeline export invokes the same check and requires Phase 7 with earlier phase outcomes recorded. The helper never edits a book, judges prose, or proves that a claimed review ran; saved review evidence still needs verification. It accepts the documented narrow progress-field YAML syntax or JSON state, rather than acting as a general YAML processor.

## Why the critics are trustworthy enough to listen to

The earlier versions let one context write, judge and approve its own prose, and revise until the judge agreed. The recovered build retains the later separation of what each role may see:

| Role | Sees | Never sees |
|---|---|---|
| Writer | the plan, a per-chapter brief and the approved production length contract (planned chapter range plus manuscript floor and ceiling) | the rubric, quality-score target, gate thresholds and verdicts |
| Blind reader | only prose, a persona card and the previous chapter's tail | the plan, targets, earlier scores |
| Auditor | the whole manuscript and the plan | targets, earlier scores, panel verdicts |
| Revision editor | quoted tickets and a preserve list | scores and targets |

Critics run at the strongest independence the host offers: another model family's CLI when one is installed, otherwise an isolated subagent (verified with a canary check where the host does not document isolation), otherwise the same context. The grade (A, B or C) is printed next to every verdict.

## Two gates, bounded

The neutral production source supplies exporter-counted whole-book word and
percentage intervals for each chapter. These measured locations help reviewers
avoid confusing local and whole-book pacing; they do not impose additional beat
or quality thresholds. See [measured-pacing-20261011.md](measured-pacing-20261011.md).

Later draft writers can learn from source-bound observations in earlier completed
reader checkpoints without receiving votes, grading or acceptance outcomes.
Critics remain blind to that history. The original voice benchmarks guide cadence
without mandatory rough sentences or universal paragraph quotas. See
[reader-experience-20261011.md](reader-experience-20261011.md) for the observed
problem, evidence checks and current validation limits.

- The **panel gate** asks whether the book holds its readers: four blind personas (primary, hostile, adjacent-genre, casual), majority to turn the page, a defect needs two votes.
- The **rubric gate** tells revision what to fix: ten weighted dimensions, calibrated for internal inflation, against a declared target of 8.5.

Both must pass. Each gets at most three revision passes, and a revised chapter is kept only under the recorded reader decision rule. When a gate remains unmet, the literary loop stops with an exact account of what is missing instead of looping until a critic agrees; an autonomous run may still complete scoring, package the manuscript and export delivery with the unmet gate recorded. Delivery is evidence that the files and formats passed their checks, not literary-gate passage or human publication approval.

## Patterns with names attached

`references/patterns/` holds the measured patterns (prose ranges, structural beats, emotional arcs) with the books and studies they come from, plus machine-prose tells with ceilings in English and Brazilian Portuguese. Research may override a genre default only with a named comparable title and passage; a genre or language label alone is never evidence.

## What the installer checks

- Every shipped skill is self-contained: each `references/...` path it mentions exists inside it, nothing points outside it, and no retired skill is named.
- The Claude Code subagents in `agents/` match what their role files generate.
- Installed files match this checkout and the install record.

## Current-text receipts

[plan-chapter-verification-20261011.md](plan-chapter-verification-20261011.md)
describes source-bound checks for every plan chapter and isolated repair history
after a real full-book run exhausted its architecture repairs.

[windows-state-publication-20261011.md](windows-state-publication-20261011.md)
describes bounded atomic replacement retries for demonstrated Windows sharing
denial, with byte and file-identity guards that preserve concurrent changes.

The causal-evidence and delivery candidate is described in
[causal-evidence-delivery-20261011.md](causal-evidence-delivery-20261011.md).
It extends existing source review with acquisition/use/payoff traces, preserves
uncertain knowledge routes, and addresses the demonstrated hook identity and
Windows schema-size failures without changing literary targets or old runs.

`verify_book.py` checks original reader receipts and raw reports against current chapter hashes before final aggregation. Old passes do not survive a prose edit. It also derives technical delivery from the source-bound export receipt and actual files. Export commits `STATUS.json` with the deliverables; the host reconciles its YAML from verified delivery, without changing literary gates or human publication approval.

[compact-review-catalogs-20261011.md](compact-review-catalogs-20261011.md)
describes complete, lossless evidence blocks that reduce native context overhead
and the explicit per-book native context request. Larger native capacity must
be demonstrated with the signed-in account before a full-book test.
