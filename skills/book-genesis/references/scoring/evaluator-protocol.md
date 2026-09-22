# Evaluator protocol

How to get criticism the writer cannot grade for itself: who may read what, how independent each critic is, and how verdicts are aggregated.

When to load: Phase 0 (set up independence), Phases 3 to 6 (every panel, audit and score). Role: orchestrator.

## Roles and what each may see

| Role | Sees | Never sees | May edit |
|---|---|---|---|
| Writer | brief, foundation, voice, outline, chapter brief | rubric, targets, verdicts | the chapter being drafted |
| Blind reader | persona card, genre line, previous chapter tail, the text, tells file | plan files, targets, earlier scores and verdicts, writer notes | nothing |
| Auditor | whole manuscript, plan files, pattern standards | targets, earlier scores, panel verdicts | nothing |
| Rubric evaluator | manuscript or declared sample, `references/scoring/genesis-score.md`, pattern standards, tells file; the market position only when scoring Market | targets, earlier scores, revision rationale, writer notes | nothing |
| Revision editor | tickets, quoted passages, preserve list, voice file | targets, numeric scores | only the passages in its tickets |
| Orchestrator | everything | | state and reports |

The orchestrator freezes each critic's report as written before applying any target or threshold.

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

1. Panels follow the table in `references/roles/panel.md`.
2. Rubric: take the median per dimension across evaluators; the lowest median is the floor.
3. When evaluators disagree by 1.5 points or more on a dimension, run one more evaluator or mark confidence low. Never hide a harsh evaluator inside an average.
4. Calibrate after reports are frozen: subtract 0.8 from each median unless an outside human critique is attached in `evaluations/`. Internal scores run high; the calibrated number is the one compared with the target.
5. Apply the target from `project.quality_target` only after calibration.

## Integrity failures

Mark an evaluation `DEGRADED` when a critic edited the text it judged, saw a target or earlier score, claimed full coverage after reading excerpts, made claims without quotes, or when a missing answer was counted as a pass. A degraded evaluation can produce tickets. It cannot pass a gate.
