# Portability

Book Genesis is an Agent Skills package, not a hosted model wrapper. Claude Code, Codex, Kimi Code, OpenClaw, and Hermes Agent install the same canonical skill folders and execute them with their own accounts, models, permissions, and quotas.

## Canonical Package

`skills/book-genesis/` is the universal core. `distribution/portable-suite.json` lists every skill required by the portable Bestseller Studio profile. Specialist agent ownership lives in `skills/book-bestseller-studio/references/agent-registry.yaml`.

`skills/book-genesis-codex/` and `skills/book-genesis-full/` remain compatibility packages. They are excluded from default portable installs.

Do not copy only `SKILL.md`. Phase prompts, scoring rules, and evaluator protocol live under `references/`.

## Verify Before Installing

```bash
python runner/cli.py verify-suite
```

Validation checks skill frontmatter, dependency closure, phase prompts, mandatory adversarial audit, Literary Barrier loop, evaluator protocol, and target definitions.

## Runtime Installers

macOS/Linux:

```bash
bash install.sh claude
bash install.sh codex
bash install.sh kimi
bash install.sh openclaw
bash install.sh hermes
bash install.sh shared
```

Windows PowerShell:

```powershell
.\install.ps1 -Target claude
.\install.ps1 -Target codex
.\install.ps1 -Target kimi
.\install.ps1 -Target openclaw
.\install.ps1 -Target hermes
.\install.ps1 -Target shared
```

Default user locations:

| Target | Skills directory | Invocation |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `/book-genesis` |
| Codex | `$CODEX_HOME/skills/` or `~/.codex/skills/` | ask Codex to use `book-genesis` |
| Kimi Code | `$KIMI_CODE_HOME/skills/` or `~/.kimi-code/skills/` | `/skill:book-genesis` |
| OpenClaw | `$OPENCLAW_STATE_DIR/skills/` or `~/.openclaw/skills/` | ask OpenClaw to use `book-genesis` |
| Hermes Agent | `$HERMES_HOME/skills/` or `~/.hermes/skills/` | `/book-genesis`, or ask Hermes to use it |
| Shared | `~/.agents/skills/` | runtime-dependent |

Use `--dest PATH` with the Python command for an isolated or project-specific skills directory:

```bash
python runner/cli.py install kimi --dest ./sandbox/skills --dry-run
```

## Conflict Safety

- unchanged skills are skipped
- changed destination skills block installation by default
- `--force` or `-Force` moves changed skills into `.book-genesis-backups/<timestamp>/` before replacement
- `.book-genesis-install.json` records installed skill checksums
- `--include-legacy` adds compatibility skills; for Claude it also installs native V4 agents and knowledge files. Default remains portable-only.

## Agent Dispatch

Portable agents are roles, packets, and gates rather than duplicated platform prompts.

```bash
python runner/cli.py prepare-agent-packet my-book prose_writer
python runner/cli.py prepare-agent-packet my-book adversarial_auditor
python runner/cli.py prepare-agent-packet my-book scorekeeper
```

Give each packet to a fresh runtime-native subagent. Claude Code may use custom or general-purpose subagents, Codex may dispatch isolated subagents, and Kimi Code may dispatch its built-in subagents. When isolation is unavailable, run roles sequentially and record Evaluation Independence Grade C.

## Generic Agents

Minimum runtime capabilities:

- read a directory of Markdown files
- follow YAML phase manifest
- create and update project files
- preserve state across turns
- isolate drafting, revision, and evaluation when possible

Generic instruction:

```text
Run Book Genesis as a file-backed book-production pipeline. Read AGENTS.md and skills/book-genesis/SKILL.md. Follow skills/book-genesis/references/pipeline/manifest.yaml exactly. Load only the active phase prompt. Persist decisions to files. Never score before adversarial audit. Apply the independent evaluator protocol before any final quality claim.
```

## Runtime Boundary

Runner scaffolds projects, validates files, prepares phase packets, advances mechanical gates, and prepares specialist packets. It never calls a model, writes literary prose, or certifies literary quality. Runtime performs creative and critical work using user's own account.

## OpenClaw and Hermes details

These targets copy the complete portable suite into the host's skill directory. They do not install the host, modify permissions, add credentials, enable tools, or start a model. Start a new host session after installing, and ask it to locate `book-genesis` before beginning a book. Use `--dest` for a specific remote/container/profile directory; run the installer in the environment where the agent reads files.

OpenClaw can use workspace-local skills instead of shared state skills:

```bash
python runner/cli.py install openclaw --dest /path/to/openclaw-workspace/skills --dry-run
```

Remove `--dry-run` after reviewing the destination. Keep the host's normal permission and tool-approval settings. For Hermes profiles, select the matching `HERMES_HOME` or an explicit skills destination. The folder paths follow [OpenClaw's skill-loading documentation](https://docs.openclaw.ai/tools/skills) and [Hermes's skills documentation](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills), checked September 10, 2026.

Installer tests establish copied-file integrity and conflict handling. They do not establish a complete-book run inside each host. See [restoration verification](restoration-20260910.md).
