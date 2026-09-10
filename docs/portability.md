# Portability

Book Genesis is an Agent Skills package. All 15 installation targets receive the same canonical skill folders. The consuming host executes them with its own account, models, permissions, and quotas. The target list contains 14 named hosts and one Shared directory export.

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
bash install.sh opencode
bash install.sh antigravity
bash install.sh gemini
bash install.sh shared
bash install.sh deepseek
bash install.sh cursor
bash install.sh copilot
bash install.sh qwen
bash install.sh pi
bash install.sh windsurf
```

Windows PowerShell:

```powershell
.\install.ps1 -Target claude
.\install.ps1 -Target codex
.\install.ps1 -Target kimi
.\install.ps1 -Target openclaw
.\install.ps1 -Target hermes
.\install.ps1 -Target opencode
.\install.ps1 -Target antigravity
.\install.ps1 -Target gemini
.\install.ps1 -Target shared
.\install.ps1 -Target deepseek
.\install.ps1 -Target cursor
.\install.ps1 -Target copilot
.\install.ps1 -Target qwen
.\install.ps1 -Target pi
.\install.ps1 -Target windsurf
```

Default user locations:

| Target | Skills directory | Invocation |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `/book-genesis` |
| Codex | `$CODEX_HOME/skills/` or `~/.codex/skills/` | ask Codex to use `book-genesis` |
| Kimi Code | `$KIMI_CODE_HOME/skills/` or `~/.kimi-code/skills/` | `/skill:book-genesis` |
| OpenClaw | `$OPENCLAW_STATE_DIR/skills/` or `~/.openclaw/skills/` | ask OpenClaw to use `book-genesis` |
| Hermes Agent | `$HERMES_HOME/skills/` or `~/.hermes/skills/` | `/book-genesis`, or ask Hermes to use it |
| OpenCode | `$OPENCODE_CONFIG_DIR/skills/`, otherwise `$XDG_CONFIG_HOME/opencode/skills/` or `~/.config/opencode/skills/` | ask OpenCode to load `book-genesis` |
| Antigravity | `~/.gemini/config/skills/` | ask Antigravity to use `book-genesis` |
| Gemini CLI | `$GEMINI_CLI_HOME/.gemini/skills/` or `~/.gemini/skills/` | ask Gemini to activate `book-genesis` |
| Shared | `~/.agents/skills/` | runtime-dependent |
| DeepSeek Harness | `$DSH_HOME/skills/` or `~/.dsh/skills/` | ask the harness to load `book-genesis` |
| Cursor | `~/.cursor/skills/` | ask Agent to use `book-genesis` |
| GitHub Copilot | `~/.copilot/skills/` | ask Copilot to use `book-genesis` |
| Qwen Code | `~/.qwen/skills/` | `/book-genesis`, or ask Qwen to use it |
| Pi | `$PI_CODING_AGENT_DIR/skills/` or `~/.pi/agent/skills/` | `/skill:book-genesis` |
| Windsurf / Cascade | `~/.codeium/windsurf/skills/` | `@book-genesis`, or ask Cascade to use it |

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

## OpenCode, Antigravity, and Gemini CLI

These are directory bundles with the original references, not platform-specific rewrites. Host permissions and skill enablement still apply. Current discovery conventions: [OpenCode skills](https://opencode.ai/docs/skills/), [OpenCode configuration](https://opencode.ai/docs/config/), [Antigravity skills](https://antigravity.google/docs/skills), and [Gemini CLI skills](https://geminicli.com/docs/cli/skills/).

For a workspace install, specify the host's actual directory:

```bash
python runner/cli.py install opencode --dest /path/to/book/.opencode/skills
python runner/cli.py install antigravity --dest /path/to/book/.agents/skills
python runner/cli.py install gemini --dest /path/to/book/.gemini/skills
```

Antigravity's current global directory is `~/.gemini/config/skills`. Older editions used `~/.gemini/antigravity/skills`; use `--dest` only if your installed edition expects that legacy path. Do not install duplicate copies into every historical path. Gemini CLI is a separate target with a different global directory.

After installing, run `python runner/cli.py verify-install TARGET` with the same `--dest`, if any. A changed checkout or locally edited skill will be reported as different; inspect before replacing it. This command performs no model calls. The host must still discover and activate the skill. [Compatibility evidence](compatibility.md) separates those checks.

A skills-only installation contains the startup/recovery contract and initial state template under `book-genesis/references/pipeline/`. Native agents can initialize and resume a book without the repository Python helper. Optional external marketing or image skills are not required to write.

## DeepSeek Harness, Cursor, Copilot, Qwen, Pi, and Windsurf

Added September 10, 2026, against official host documentation and source. These are native skill installations. DeepSeek Harness is a separate product from the DeepSeek model API; installing this target does not configure an API provider inside a different agent.

```bash
python runner/cli.py install deepseek --dry-run
python runner/cli.py install deepseek
python runner/cli.py verify-install deepseek
```

Open a fresh DeepSeek Harness session in a writable book folder. Ask it to locate `book-genesis`, read its phase manifest and host contract, and save the intake artifacts before continuing. The same steps apply to the other targets with the appropriate host and target name.

| Host | Configuration and discovery notes | Official reference |
| --- | --- | --- |
| DeepSeek Harness | Default `~/.dsh/skills`; `DSH_HOME` overrides the home. Empty or whitespace-only values use the default. Project `.dsh/skills` and `.agents/skills` are also supported. Explicit harness provider configuration can override the home; use `--dest` to match it. | [Skills subsystem](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/skills.md), [home resolver](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/util/home-paths/src/index.ts) |
| Cursor | User `.cursor/skills`, project `.cursor/skills`, and Agent Skills directories. Local user skills are not automatically copied into cloud or remote agent environments. | [Cursor skills](https://cursor.com/docs/skills) |
| GitHub Copilot | User `.copilot/skills`; project `.github/skills` is also supported. `COPILOT_SKILLS_DIRS` is a list of additional search paths, not a replacement home. In Copilot CLI, use `copilot skill list`; `/skills reload` refreshes an active session. | [Copilot skills](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills) |
| Qwen Code | User `.qwen/skills` or project `.qwen/skills`; inspect `/skills` in the host. | [Qwen skills](https://github.com/QwenLM/qwen-code/blob/main/docs/users/features/skills.md) |
| Pi | User `.pi/agent/skills`; `PI_CODING_AGENT_DIR` replaces `.pi/agent`. Project `.pi/skills` is available. | [Pi skills](https://pi.dev/docs/latest/skills), [configuration source](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/config.ts) |
| Windsurf / Cascade | User `.codeium/windsurf/skills` or project `.windsurf/skills`. The official documentation redirects to Devin Desktop; this target does not claim compatibility with Devin cloud's separate skill system. | [Cascade skills](https://docs.devin.ai/desktop/cascade/skills) |

For project or remote installations, pass the actual skills directory to `--dest`, for example:

```bash
python runner/cli.py install deepseek --dest /path/to/book/.dsh/skills
python runner/cli.py install cursor --dest /path/to/book/.cursor/skills
python runner/cli.py install copilot --dest /path/to/book/.github/skills
python runner/cli.py install qwen --dest /path/to/book/.qwen/skills
python runner/cli.py install pi --dest /path/to/book/.pi/skills
python runner/cli.py install windsurf --dest /path/to/book/.windsurf/skills
```

Run the installer where the host reads files. Avoid installing the same suite into several directories searched by the same host. Check discovery after an update, including possible duplicate skills from custom recursive search configurations. Host commands, trust settings, and release behavior can change; the [compatibility table](compatibility.md) records what was actually exercised.
