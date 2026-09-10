# Book Genesis

**Your creativity. Your agent. Your book.**

An open-source collection of writing skills that runs inside the AI agent you already use: Claude Code, Codex, Kimi Code, OpenClaw, Hermes Agent, or another file-aware agent.

Bring an idea. Book Genesis gives your agent a workflow for developing it into a manuscript: direction, characters, outline, chapters, editorial review, revision, and a publishing package. You keep the project files and creative decisions.

[MIT license](LICENSE) · [Installation guide](docs/portability.md) · [Writing skills](skills/book-genesis/SKILL.md) · [Project casebook](SHOWCASE.md)

## Back to the skills

This repository has returned to its portable-skills foundation, based on commit [`c974486`](https://github.com/felipelobomotta-blip/book-genesis-v4/commit/c9744863efab1a8de8728f8f67d2cbe0cfc6b8d6). The host agent handles models, authentication, tools, progress, and permissions. Book Genesis supplies the writing workflow and reference material.

The later standalone app and model-orchestration experiment is preserved in Git history. See [what was restored and verified](docs/restoration-20260910.md). Existing app book folders should be preserved; automatic migration of their state to the older skill workflow has not been verified.

## Install into your agent

You need Git and Python 3.10+ for this installer, plus the agent you want to use. The installer only copies skills and their references. It does not start a model, install the host agent, or collect API keys.

```bash
git clone https://github.com/felipelobomotta-blip/book-genesis-v4.git
cd book-genesis-v4
python runner/cli.py verify-suite
```

Choose **one** target:

```bash
python runner/cli.py install claude
python runner/cli.py install codex
python runner/cli.py install kimi
python runner/cli.py install openclaw
python runner/cli.py install hermes
```

PowerShell and shell shortcuts are also included:

```powershell
.\install.ps1 -Target hermes
```

```bash
bash install.sh openclaw
```

Use `--dry-run` to preview an installation. Existing modified skills block replacement; an explicit `--force` backs them up first. See the [installation guide](docs/portability.md) for profiles, custom destinations, remote agents, and updates. Copying just `SKILL.md` is insufficient: the reference folders are part of the workflow.

## Give it an idea

Open a new session in your agent with a writable folder for your book, then say:

> Use the book-genesis skill. My idea is a mystery about a retired train dispatcher who finds a farewell letter inside a station clock. Help me choose the direction, then develop the outline and write the book. Save the chapters and project state so we can continue later. Write in English.

In hosts that expose skill commands, use `/book-genesis`. You can also ask for `book-bestseller-studio` when you want the broader research, editorial, positioning, and launch workflow.

The agent asks for missing creative decisions and works within its own context and quota limits. If interrupted, return to the same project folder and ask it to read `PROJECT_STATE.yaml`, inspect the saved chapters, and continue from the unfinished step.

## How it works

1. **Direction:** clarify the reader, premise, language, form, and intended length.
2. **Foundation and outline:** develop the characters or argument, voice, and chapter structure.
3. **Writing:** draft chapter blocks and preserve progress in files.
4. **Editorial review:** audit the manuscript, identify specific weaknesses, and revise their responsible sections.
5. **Delivery:** prepare the synopsis, positioning, cover brief, and editorial handoff.

The original core includes audit, revision, and scoring references. Scores are internal editorial signals. A strong score does not establish human preference, publication readiness, or sales. Specialist skills are available when relevant; installation does not launch a team of background processes.

## What you install

The same [15-skill suite](distribution/portable-suite.json) goes to every supported target. It includes the universal core, narrative foundation, prose craft, book research, editing, reader simulations, manuscript management, series planning, and editorial packaging.

| Host | Default destination |
| --- | --- |
| Claude Code | `~/.claude/skills/` |
| Codex | `~/.codex/skills/` |
| Kimi Code | `~/.kimi-code/skills/` |
| OpenClaw | `~/.openclaw/skills/` |
| Hermes Agent | `~/.hermes/skills/` |
| Shared Agent Skills | `~/.agents/skills/` via `install shared` |

Host-specific home variables and `--dest` override these locations. The OpenClaw and Hermes destinations follow their official [OpenClaw](https://docs.openclaw.ai/tools/skills) and [Hermes](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) skill-directory conventions. Installer compatibility is tested separately from live writing in those hosts.

## The work behind it

The [casebook](SHOWCASE.md) preserves earlier experiments, including *The Source Code*, *Protocolo Não Encontrado*, and *Age of Aquarius*. Case notes distinguish planned work, reported manuscript progress, and public artifacts. Private manuscripts and historical model scores are not independent product benchmarks.

The idea is simple: creativity should be the starting point. People should be able to explore a book with the tools they already have. Writing quality still depends on the idea, model, direction, and editorial work; a literal bestseller cannot be guaranteed.

## Development

The optional Python helper installs the suite, scaffolds projects, validates files, and prepares phase packets. It does not call a model. You do not need to keep it running while your agent writes.

```bash
python -m unittest discover -s tests -v
```

[Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md) · [Issues](https://github.com/felipelobomotta-blip/book-genesis-v4/issues)

Created by [Felipe Lobo](https://github.com/felipelobomotta-blip). MIT licensed.
