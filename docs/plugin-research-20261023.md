# Native writing plugins: evidence and decisions

Date: 2026-10-23. Scope: a beginner installs Book Genesis in an existing agent, gives an idea, and obtains a saved, reviewed, exported manuscript. This is engineering/product research, not a market-share or literary-quality comparison.

## Sources inspected

| Project | Observed mechanism | Decision for Book Genesis |
|---|---|---|
| [Novelist](https://github.com/comfuture/novelist), MIT, inspected commit `64e4a2e1473ff0bad5893eff394ccbf1fa1cd580` | Separate Codex/Claude plugin manifests over shared skills; a safe project initializer; bounded chapter context; a review-only routing contract | Use native host manifests over one canonical suite. Keep book workspace distinct from installation. Route status/review/export before authoring. Preserve our existing context/evidence controls. |
| [Novel Creator](https://github.com/mave99a/novel-skill), MIT | Story concept, interactive decisions, chapter plan and EPUB in a Claude plugin | Natural-language entry and export are valuable. Its mandatory RPG interaction and genre-specific prose format do not fit our unattended, genre-flexible workflow. |
| [Auto-Graph](https://github.com/tdrml/auto-graph), MIT | Repository-backed stages, chapter word gates, bounded writer/editor/reviser loops, continuity state, recovery heartbeats; source includes AWS workflow timeouts | Retain our local saved-state and bounded revision design. Its AWS/GitHub infrastructure is not needed for plugin onboarding. The README's completed-novel claims were not independently evaluated. |
| [Sudowrite Story Bible](https://docs.sudowrite.com/getting-started/dQph1snuwbfMWG9wRjsNug/quick-start/2A4FjtiocrtxHPUyz6WZgR) | Official documentation presents braindump, genre/style, synopsis, characters and outline before chapter prose | Treat the author's idea as the entry point and hide implementation details. No private source or proprietary implementation was accessed or copied. |

Primary code inspected: Novelist `plugin.json`, host manifests, `create-novel-project/SKILL.md`, `novel-story-telling/SKILL.md`, `analytical-review/SKILL.md`; Novel Creator `SKILL.md`; Auto-Graph README and `packages/cdk/src/constructs/orchestration.ts`. Public source is sufficient for these observations. Following the REA skill's routing rule, this ordinary source-repository analysis used direct reads rather than binary/runtime REA tools. No decompilation or live competitor execution is claimed.

## What was incorporated

Book Genesis now has native host manifests, an experimental DSH skill provider, conversational request routing, workspace/cache separation and a reproducible allowlisted release archive. Implementation was written for this repository; no competitor code was vendored. The patterns above are credited as design references, not presented as proof that the resulting books will outperform theirs.

The initializer pattern is implemented by `plugin_entry.py`, reusing this
repository's existing installer and controlled workflow rather than duplicating
the writing engine. Live trials added bounded native preflight, verified skill
snapshots, normal permission recovery and explicit separation of the literary
brief from runtime/quality controls. Observed outcomes, including failed trials,
are in the [validation record](plugin-validation-20261023.md).

The DSH provider follows the official [packaged-skill example](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/experimental/skill-badge/src/index.ts) and [skills contract](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/skills.md). Codex packaging follows [OpenAI's manifest documentation](https://developers.openai.com/plugins/build/plugins); Claude packaging follows its [manifest reference](https://code.claude.com/docs/en/plugins-reference).

## Local strategy application

Consulted Felipe's `ESTRATEGIAS-DE-MERCADO.md`, its playbook and the linked additional cases. Applicable tactics: T13 (an editable example/first useful result), T15 (saved progress/resume), T11 (real evidence and disclosed limitations), T23 (reuse and selective context). These are hypotheses about reducing onboarding friction, not proven acquisition/retention effects.

Primary acceptance target: a freshly installed native plugin accepts one ordinary-language idea and produces the contracted complete, reviewed Markdown/EPUB without corrective operator prompts. This outcome is not yet established. Denominator: attempted fresh plugin book runs, including failures. Track installation/discovery, first saved artifact, chapters/words against contract, review receipts, export integrity, interruptions and corrective prompts. One maintainer session is not a beginner usability study or a causal conversion experiment.

Status: **EM_TESTE**. Installation canary and full-book acceptance are separate records. The historical v46 manuscript belongs to a different execution path and cannot stand in for this plugin's end-to-end result.
