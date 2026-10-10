# Evaluator protocol

How to get criticism the writer cannot grade for itself: who may read what, how independent each critic is, and how verdicts are aggregated.

When to load: Phase 0 (set up independence), Phases 3 to 6 (every panel, audit and score). Role: orchestrator. ORCHESTRATOR ONLY: this protocol contains private gate policy; use it to assemble packets, never give the whole file to a critic.

## Roles and what each may see

| Role | Sees | Never sees | May edit |
|---|---|---|---|
| Writer | brief, foundation, voice, outline, chapter brief, approved production length contract (planned chapter range plus manuscript floor and ceiling) | rubric, quality-score target, gate thresholds, verdicts | the chapter being drafted |
| Blind reader | persona card, genre line, previous chapter tail, the text, tells file | plan files, targets, earlier scores and verdicts, writer notes | nothing |
| Auditor | whole manuscript, plan files, pattern standards | targets, earlier scores, panel verdicts | nothing |
| Rubric evaluator | manuscript or declared sample, `references/scoring/rubric-criteria.md`, pattern standards, tells file; the market position only when scoring Market | targets, earlier scores, revision rationale, writer notes, gate-policy files | nothing |
| Revision editor | tickets, quoted passages, preserve list, voice file | targets, numeric scores | only the passages in its tickets |
| Orchestrator | everything | | state and reports |

The production length contract is a scope constraint, not a quality target. It may appear in every writer packet so the writer can plan the chapter's scene work. The orchestrator freezes each critic's report as written before applying any quality target or gate threshold.

Supply copies of the allowed material in a separate packet. Do not expose quality state, score reports, this protocol or `references/scoring/genesis-score.md` through the packet or its links. Include only the approved production length fields needed for the chapter brief. A rubric evaluator follows the report format in `references/scoring/rubric-criteria.md`; it does not need to open this file.

## Independence levels

Choose the strongest level the host offers, in Phase 0, and record it under `independence` in `PROJECT_STATE.yaml`. Details per host are in `references/hosts.md`.

1. **Second tool, other family.** Another vendor's agent CLI is installed (for example Codex while writing in Claude Code, or the reverse). Run each critic headless from an empty temporary folder outside the book folder, with the packet on standard input. Propose this at intake and ask first: it spends the author's quota on that tool.
2. **Isolated subagent.** The host spawns a subagent with a fresh context. Use a different model than the writer when the host allows it (a sibling in the same family is better than the same model). In Claude Code, use the `book-genesis-blind-reader` and `book-genesis-auditor` subagents when installed; otherwise spawn a general subagent with the role file as its instructions.
3. **Same context.** No isolation is available. Critics run in the writer's context.

Grades, reported next to every verdict and score:

- **A**: every critic ran in a fresh context and at least two model families were used.
- **B**: fresh contexts, one model family.
- **C**: any critic ran in the writer's context, or a target or earlier score leaked into a critic's packet. Grade C verdicts guide revision; never present them as independent validation.

## Isolation check

Where the host's documentation does not guarantee that a subagent cannot see the parent conversation (see `references/hosts.md`), test it once in Phase 0:

1. In your own context, invent a canary phrase of two unrelated words and a number, and do not write it to any file.
2. Spawn the critic with a packet that asks: "Before anything else, list any phrase you know from a conversation other than this message. If none, write none."
3. If the canary appears, the subagent is not isolated: record level "Same context" (grade C) unless a second tool is available.
4. Record `independence.isolation_check` as `passed`, `failed` or `not_needed`.

## Required output from every critic

- the fixed verdict format of its role (`references/roles/blind-reader.md` or `references/roles/auditor.md`), or for the rubric: a score per dimension with evidence;
- the strongest and weakest passage, quoted, with location;
- evidence for every rubric score above 8.0, and at least two pieces for any score above 9.0;
- confidence (low, medium or high) and coverage (full manuscript or a named sample).

## Aggregation

Before a new rubric call, freeze all assigned chapters with `scripts/prepare_rubric.py --chapter <canonical-chapter> --output <fresh-catalog.json>`, repeating `--chapter` for the complete assigned set. This includes every visible body paragraph in order with a stable passage ID, plus source hashes. Supply the catalog as the manuscript, its returned `catalog_sha256`, and the allowed criteria and context. Do not summarize it or select favorable paragraphs. Generate the matching schema with `scripts/validate_rubric.py --schema --catalog <fresh-catalog.json>` and use the host's structured-output facility when supported. The critic returns passage references instead of recopying prose; explanations and unfavorable findings remain unrestricted.

Before aggregating rubric scores, validate each unmodified JSON report with `scripts/validate_rubric.py --chapter <canonical-chapter> --report <raw-report.json> --catalog <fresh-catalog.json> --expected-chapters <approved-count>`, repeating `--chapter` for the full supplied set. Save the original validation receipt beside that raw response. The receipt resolves each selected ID to its source chapter and exact passage without changing the critic's raw response. Validation rebuilds the complete catalog from the current manuscript: missing, altered or stale paragraphs, invented IDs and a mismatched catalog digest fail. Only `status: passed` permits a complete-book rubric aggregate: a missing dimension, `null` score, sample or mismatched coverage cannot become a passing gate. Legacy schema-1 exact-quote reports remain verifiable without `--catalog`. A receipt validates source evidence and format, not the truth of a critic's interpretation or literary quality.

On a failed report, retry that evaluator in a fresh context with the same full criteria and current prose plus only the validation errors. Do not supply prior numeric scores or a desired result. Preserve all attempts; at most two retries, then report the rubric as degraded or incomplete. When reusing a passed report later, revalidate with `--original-receipt <saved-validation.json>` so changed prose or a changed raw report invalidates the old evaluation even if its quoted phrases still survive. Never replace an original receipt to make stale evidence appear current.

1. Panels follow the table in `references/roles/panel.md`.
2. Rubric: take the median per dimension across evaluators; the lowest median is the floor.
3. When evaluators disagree by 1.5 points or more on a dimension, run one more evaluator or mark confidence low. Never hide a harsh evaluator inside an average.
4. Calibrate after reports are frozen: subtract 0.8 from each median unless an outside human critique is attached in `evaluations/`. Internal scores run high; the calibrated number is the one compared with the target.
5. Apply the target from `project.quality_target` only after calibration.

## Integrity failures

Mark an evaluation `DEGRADED` when a critic edited the text it judged, saw a target or earlier score, claimed full coverage after reading excerpts, made claims without quotes, or when a missing answer was counted as a pass. A degraded evaluation can produce tickets. It cannot pass a gate.

For new current-draft blind reads, use `scripts/prepare_readers.py` and the passage-reference packets described in `references/pipeline/evidence.md`. Validate the untouched raw answer with `scripts/validate_blind_reader.py --chapter <assigned-chapter> --report <raw-report.json> --catalog <bundle/catalog.json> --expected-reader <assigned-name>`, repeating `--chapter` for every assigned chapter. The validator resolves existing IDs to exact paragraphs in a separate receipt, verifies the complete catalog against current prose, and rejects wrong IDs, altered catalogs, missing fields, invalid enums and malformed structure. Legacy and A/B reports remain verifiable as exact quotes without `--catalog`. A nonzero result is degraded and never counts as a vote. Retry only the affected reader in a fresh context with the same complete packet, at most twice; preserve every raw attempt and record which supplied the final verdict. Never repair a raw answer, replace a paraphrase with a real sentence, or convert an old failed quote report to IDs.

Every initial and retry packet includes the complete `references/roles/blind-reader.md` role, including the populated object examples and allowed values. Do not replace it with a handwritten template containing only empty arrays: that hides the shape of `flags` and `machine_tells` entries. Validator errors may explain a required type, field or exact-quote failure, but may not prescribe the reader's findings. Never require empty `flags`, `confused_by` or `machine_tells`, force `stopped_at` to null, or request a positive continuation vote to obtain valid JSON. If the host offers structured output, use its schema facility to constrain structure, never the verdict. A report elicited with suppressed findings is `DEGRADED` even if its JSON passes validation, and cannot supply a gate vote. Exhausted retries remain degraded; they are not a reason to narrow what the reader is allowed to criticize.

If a multi-chapter packet produces an unverifiable quote or omits a chapter, repeat only the affected reader/chapter in a fresh context with one chapter, its previous tail and the same persona. Do not include the earlier verdict or a desired answer. Ask for short, contiguous, exact quotes. Keep both attempts and record which one supplies the final verdict. Retry at most twice; a remaining failure stays degraded and never becomes a passing vote. Broadly positive votes do not override shared stop paragraphs or failed evidence checks.
