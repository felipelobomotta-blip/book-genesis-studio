# Installing Book Genesis

Book Genesis 6.0 is a set of Agent Skills. Every target receives the same four skill folders, and the host agent runs them with its own account, models, permissions and quotas. The installer copies and checks files; it never calls a model or writes a book.

## What gets installed

| Skill | What it is |
|---|---|
| `book-genesis` | The core: idea to complete book in eight phases, with its references, roles, patterns and scoring |
| `beta-reader` | Standalone: three very different test readers for any draft |
| `editorial-package` | Standalone: logline, blurb, synopsis, query letter and cover brief for any finished manuscript |
| `literary-agent-panel` | Standalone: simulated agents, editor, bookseller and readers judge market viability |

For Claude Code only, the installer also adds two subagents, `book-genesis-blind-reader` and `book-genesis-auditor`, generated from the core skill's role files. They let critics run with read-only tools. Other hosts use the same role files through their own subagent features.

Always install the whole folder. `SKILL.md` alone is not enough: the phases, roles and patterns live under `references/`.

## Check the checkout first

```bash
python runner/installer.py verify-suite
```

This checks that every shipped skill is self-contained (every `references/...` path exists inside it, no path points outside it, no retired skill is named), that the pipeline order and mandatory phases are intact, and that the Claude Code subagents match their role files.

## Install

```bash
python runner/installer.py targets
python runner/installer.py install claude --dry-run
python runner/installer.py install claude
python runner/installer.py verify-install claude
```

The shell and PowerShell wrappers pass everything through:

```bash
bash install.sh codex --dry-run
```

```powershell
.\install.ps1 -Target hermes -DryRun
```

| Target | Skills folder | How to start |
|---|---|---|
| `claude` (Claude Code) | `$CLAUDE_CONFIG_DIR/skills` or `~/.claude/skills`; subagents in `~/.claude/agents` | `/book-genesis` |
| `codex` | `$CODEX_HOME/skills` or `~/.codex/skills` | ask Codex to use `book-genesis` |
| `opencode` | `$OPENCODE_CONFIG_DIR/skills`, else `$XDG_CONFIG_HOME/opencode/skills`, else `~/.config/opencode/skills` | ask OpenCode to load `book-genesis` |
| `hermes` | `$HERMES_HOME/skills` or `~/.hermes/skills` | `/book-genesis`, or ask Hermes |
| `openclaw` | `$OPENCLAW_STATE_DIR/skills` or `~/.openclaw/skills` | ask OpenClaw to use `book-genesis` |
| `kimi` | `$KIMI_CODE_HOME/skills` or `~/.kimi-code/skills` | `/skill:book-genesis` |
| `cursor` | `~/.cursor/skills` | ask Agent to use `book-genesis` |
| `copilot` | `~/.copilot/skills` | ask Copilot to use `book-genesis` |
| `antigravity` (app and IDE) | `~/.gemini/config/skills` | ask Antigravity to use `book-genesis` |
| `antigravity-cli` | `~/.gemini/antigravity-cli/skills` | ask `agy` to use `book-genesis` |
| `gemini` | `$GEMINI_CLI_HOME/.gemini/skills` or `~/.gemini/skills` | ask Gemini to activate `book-genesis` |
| `deepseek` (DeepSeek Harness) | `$DSH_HOME/skills` or `~/.dsh/skills` | ask the harness to load `book-genesis` |
| `qwen` | `~/.qwen/skills` | `/book-genesis`, or ask Qwen |
| `pi` | `$PI_CODING_AGENT_DIR/skills` or `~/.pi/agent/skills` | `/skill:book-genesis` |
| `windsurf` (Cascade) | `~/.codeium/windsurf/skills` | `@book-genesis`, or ask Cascade |
| `shared` | `~/.agents/skills` | depends on the host that reads it |

Home variables must be absolute paths. A blank value is ignored and the default is used; a relative value is refused with an error that names the variable.

Gemini CLI stopped serving individual Google AI Pro, Ultra and free Code Assist accounts on 2026-06-18; Standard and Enterprise accounts still work. Its successor for individuals is the Antigravity CLI (`antigravity-cli`).

## Custom folders

Use `--dest` for a project, profile, container or remote skills folder. Run the installer where the host reads files.

```bash
python runner/installer.py install openclaw --dest /path/to/workspace/skills --dry-run
python runner/installer.py install opencode --dest /path/to/book/.opencode/skills
python runner/installer.py install claude --dest /path/to/book/.claude/skills --agents-dest /path/to/book/.claude/agents
```

With `--dest`, Claude Code subagents are installed only when `--agents-dest` is also given; the installer says so instead of guessing a folder. Pass the same `--dest` to `verify-install`.

## Safety

- Identical skills are skipped. A skill or subagent this installer put there and nobody changed since is updated, with a backup. One you changed blocks the install until you pass `--force`, which backs it up first.
- Links are never followed, replaced or moved. If a skill folder is a symlink or a Windows junction, the installer stops and names it.
- Every folder, skills and subagents alike, is copied before anything is swapped, so a failure while copying (a full disk, a folder where a file is) leaves the previous install untouched. If a swap fails, every swap already made is restored.
- Backups go to `.book-genesis-backups/<timestamp>/` inside the skills or subagents folder, with `SKILL.md` renamed to `SKILL.md.bak` and agent files ending in `.md.bak`, so no host loads a backup as a live skill. An existing `.bak` of yours is never overwritten.
- `.book-genesis-install.json` records a checksum for every installed skill and subagent. `verify-install` tells apart a file you changed from an install that is simply older than this checkout.

## Upgrading from 5.x

Version 5.x installed fifteen skills and, with `--include-legacy`, eight V4 agents and five knowledge files. In 6.0 their content lives inside `book-genesis`, and leaving the old folders in place lets them compete for book requests.

On install, the 6.0 installer moves an earlier Book Genesis skill or V4 file to the backup folder when the old install record proves the 5.x installer put it there and nobody changed it since. Anything changed, or not recorded, is left in place with a warning naming the path, so you can decide. Projects started in 5.x keep their files; their `PROJECT_STATE.yaml` uses an older schema, so start a new 6.0 session and ask Book Genesis to rebuild the state from the files that exist.

## Host notes

After installing, start a new host session in a writable book folder and ask it to use `book-genesis`. The installer does not install the host, change permissions, add credentials or start a model.

- **OpenClaw and Hermes.** Folder conventions follow [OpenClaw's skill loading](https://docs.openclaw.ai/tools/skills) and [Hermes skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills). For Hermes profiles, set the matching `HERMES_HOME` or pass `--dest`.
- **OpenCode, Antigravity and Gemini CLI.** See [OpenCode skills](https://opencode.ai/docs/skills/), [Antigravity skills](https://antigravity.google/docs/skills) and [Gemini CLI skills](https://geminicli.com/docs/cli/skills/). Install into one global folder per host, not into every historical path.
- **DeepSeek Harness, Cursor, Copilot, Qwen, Pi and Windsurf.** See [DeepSeek Harness skills](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/skills.md), [Cursor skills](https://cursor.com/docs/skills), [Copilot skills](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills), [Qwen skills](https://github.com/QwenLM/qwen-code/blob/main/docs/users/features/skills.md), [Pi skills](https://pi.dev/docs/latest/skills) and [Cascade skills](https://docs.devin.ai/desktop/cascade/skills). DeepSeek Harness is a separate product from the DeepSeek model API.

How each host isolates the critics is described in `skills/book-genesis/references/hosts.md`. What has actually been exercised per host is in [compatibility](compatibility.md).
