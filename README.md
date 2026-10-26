# Book Genesis

**Your creativity. Your agent. Your book.**

Book Genesis gives your AI agent a workflow for turning an idea into a complete book: planning, chapter-by-chapter writing, blind simulated readers, an editorial audit, bounded revision, and an export with a logline, blurb, synopsis, query letter and cover brief. You agree at each step, or tell it to run to the end. Complete unattended runs are still being validated; this is a beta, and the reports preserve failed checks.

**Read a book it made:** [Vicente, O Lago das Mensagens](https://github.com/felipelobomotta-blip/book-genesis-studio/releases/tag/case-vicente-v1) · 32 chapters · 51,945 words · EPUB and PDF · Brazilian Portuguese. Made with an earlier version; its score is self-assessed and no outside reader has reviewed it yet. Judge it yourself.

![An idea moving through files and writing skills into an open book](assets/brand/book-genesis-workflow.png)

Version 5.1.0-beta.7 · native plugin beta · MIT licensed · free · runs on your own agent and account.

**Try a small review first:** [Catch a character using a secret before learning it](examples/continuity-review/README.md). Three short excerpts, a consistent control, real recorded AI feedback and unchanged manuscript files. Copy the prompt into your agent to run your own review. The supplied verification script checks the saved evidence; it does not call a model.

**Recovery build:** [What was recovered from 5.0, what was missing, and what still needs validation](docs/v5-recovery.md). Prose-first drafting is restored; current execution, isolated-review and export safeguards are retained. Beta 7 carries this recovery work into the native plugin release. [Observed recovery checks and remaining validation](docs/recovery-validation-20261009.md).

**Current validation:** beta 6 completed a revised/exported 24-chapter, 83,517-word draft, with a final automated literary result of **72.52/100** and unmet quality gates. Beta 7 adds causal scene contracts, source-selected repair evidence, explicit knowledge boundaries and more precise progress. See the [integration evidence](docs/editorial-integration-20261025.md) and [mechanism-by-mechanism adoption map](docs/research/editorial-adoption-20261025.md). A new beta 7 full-book result above 90/100 has not been established. Historical plugin failures remain in the [native test report](docs/plugin-validation-20261023.md).

## The goal

A book written with the measured patterns of books readers finish, criticized by readers who cannot see the plan, and packaged to sell. That is the goal every part of the workflow is built around. It is not a promise: no workflow can guarantee a bestseller, and this one says so in every report.

## How it works

1. **Intake.** Your idea becomes a brief: genre, reader, length, comparable books in your idea's language, and four simulated readers built for this book.
2. **Foundation and architecture.** Characters with wounds and contradictions, a theme asked as a question, a voice with a rhythm anchored to real books, a chapter plan, and a ledger that keeps facts straight.
3. **Drafting.** Every chapter saved as a file. Chapter 1 goes to the four readers before the rest is written; continuity checks follow five-chapter blocks, with reader checkpoints at the opening, around 25 and 50 percent, and before the final movement.
4. **Audit and revision.** A read-only auditor quotes exact passages. Revision runs against two gates, the readers' and a ten-part rubric, at most three passes each. Creative revisions follow the recorded reader decision rule; narrowly factual corrections require an independent check against existing canon. Both preserve the original and require current evidence.
5. **Score and package.** A plain report of where the book stands, plus the editorial package, a hook test of alternative titles and blurbs, and the portable `manuscript.md` plus validated EPUB by default. DOCX and PDF are optional when their dependencies already exist. Delivery records any unmet literary gates; it is not publication approval by a human.

Everything lives in a folder you own. Close the session, come back tomorrow in any supported agent, and it picks up from the files.

## Install

**Install beta 7 in your existing agent.** No Book Genesis account or separate API key. Python 3.10+ and your host's local tools are required; your subscription quotas still apply.

**Codex** — paste these two commands into a terminal:

```bash
codex plugin marketplace add felipelobomotta-blip/book-genesis-studio --ref v5.1.0-beta.7
codex plugin add book-genesis@book-genesis
```

**Claude Code** — paste these two commands inside Claude Code:

```text
/plugin marketplace add felipelobomotta-blip/book-genesis-studio
/plugin install book-genesis@book-genesis
```

Start a new conversation in a folder for your book and select **Book Genesis**. Then say:

> Use Book Genesis. My idea is a mystery about a piano tuner who discovers a message hidden in an old recording. Write the complete book in English, revise it and export Markdown and EPUB. Make reasonable creative decisions and continue without chapter-by-chapter approval.

[Download beta 7 ZIP](https://github.com/felipelobomotta-blip/book-genesis-studio/releases/download/v5.1.0-beta.7/book-genesis-5.1.0-beta.7.zip) · [Installation, updates and troubleshooting](docs/plugins.md) · [Release notes](docs/releases/5.1.0-beta.7.md) · [Support](SUPPORT.md)

The GitHub marketplace is available independently of the public plugin directories. **Directory approval is pending; Book Genesis is not listed there yet.** The unattended workflow needs local execution; general ChatGPT web/mobile and Claude chat compatibility is not established. Claude and experimental DeepSeek full-book reliability must be validated separately from installation. [Observed native evidence](docs/plugin-validation-20261023.md).

The standalone skill installer remains available for other hosts:

You need Python 3.10 or newer, Git, and an agent that can read and write files.

```bash
git clone https://github.com/felipelobomotta-blip/book-genesis-studio.git
cd book-genesis-studio
python runner/installer.py install claude
```

Replace `claude` with your agent. `python runner/installer.py targets` lists them all; `--dry-run` shows what would change first; `verify-install` checks the result. Upgrading from the original 5.0 bundle retires its superseded skills automatically when they are unchanged. Details: [installation guide](docs/portability.md).

| Agent | Target | Status |
|---|---|---|
| Claude Code | `claude` | installer supported; full-book acceptance pending |
| Codex | `codex` | installer supported; full-book acceptance pending |
| OpenCode | `opencode` | installer supported; full-book acceptance pending |
| Hermes Agent | `hermes` | installer supported; full-book acceptance pending |
| OpenClaw | `openclaw` | installer supported; full-book acceptance pending |
| Kimi Code, Cursor, GitHub Copilot, Antigravity (app and CLI), Gemini CLI, DeepSeek Harness, Qwen Code, Pi, Windsurf, a shared folder | see `targets` | installs; not yet tested with a full book |

What has actually been run where is tracked in [compatibility](docs/compatibility.md). A verified full book in each host remains part of the release plan.

## Start a book

After installing the plugin, open a new Codex conversation in an empty folder
for your book and send your idea:

> Use Book Genesis. A retired train dispatcher finds a farewell letter inside a station clock. Write the complete book in English, revise it, and export Markdown and EPUB. Make the creative decisions and continue without chapter approvals.

The agent handles setup and the writing workflow. It saves progress, reports
what it is doing and keeps your manuscript in your folder. To check progress,
say "How is my book going?" To return later, open the same folder and say
"Continue my book." Your agent's subscription and permission limits still apply.
The [local plugin guide](docs/plugins.md) explains installation and current limits.

<details>
<summary>Optional developer launcher and earlier skill installations</summary>

New unattended projects have a [controlled native execution path](docs/controlled-native-acceptance.md), with durable revision budgets, original-call evidence, phase prerequisites and source-verified export. Codex is in full-length acceptance testing; the added [Claude subscription transport](docs/native-claude-transport.md) has separate validation. Neither path's existence is a claim that the 90/100 quality bar has passed.

```bash
python book_genesis.py new ./books/my-novel --host codex --model gpt-5.6-luna --effort high --author "Your Name" --autonomous --idea "Your idea"
```

This freezes a 12-chapter, 40,000–48,000-word production contract by default. Set `--chapters`, `--min-words` and `--max-words` when creating a different length. Progress shows the active role, elapsed time and saved chapter counts. `resume` retains the original snapshot and counters; it does not silently upgrade an existing book.

This recovery checkout also includes an optional [small native CLI launcher](docs/native-cli.md): `python book_genesis.py doctor`, then `python book_genesis.py new ./books/my-book --host codex` or `--host claude`. It prepares a verified project and opens your existing agent's own live terminal UI and sign-in. One supervised Codex run delivered six chapters and a verified EPUB; literary gates failed. The launcher remains an unreleased prototype, with unattended and full-length acceptance still unverified.

Open your agent in an empty folder for the book and say:

> Use book-genesis. My idea: a retired train dispatcher finds a farewell letter inside a station clock.

In agents with skill commands, `/book-genesis` works too. The agent writes in the language you use. To let it finish without stopping, say "go to the end" at any check-in.

</details>

## What you install

- **book-genesis**: the full workflow, with its phase prompts, the three critic roles, the rubric, the patterns library and the specialists for research, character, prose, continuity, revision, production and series.
- **beta-reader**: three very different test readers for any draft.
- **editorial-package**: logline, blurb, synopsis, query letter and cover brief for any finished manuscript.
- **literary-agent-panel**: simulated agents, an acquiring editor, a bookseller and target readers judge market fit.

The three smaller skills work on their own, on any manuscript.

## Why the criticism is worth reading

- The writer never sees the rubric, quality-score target or gate thresholds; the approved production length contract may be shared. The readers never see the plan or earlier scores.
- Critics run in isolated subagents, or in a second AI tool from another company when you have one installed, and every verdict prints how independent it was.
- Four readers with different stakes decide, not one: the genre fan, the reader who did not want to like it, a reader from the next shelf over, and one who gives any book ten pages at an airport.
- Revision stops after three passes per gate and says exactly what is still missing, instead of polishing until a critic agrees.

It is simulated reading, and the reports say so. Architecture: [docs/architecture.md](docs/architecture.md). Questions: [FAQ](docs/faq.md).

## The casebook

[Eleven projects](SHOWCASE.md) across genres and languages, with what each one taught the system. Every case so far is the maintainer's, which is the biggest gap in this repository. **Wrote a book with it?** Add it through [issue #13](https://github.com/felipelobomotta-blip/book-genesis-studio/issues/13); an honest note about what worked and what did not is worth more than a star.

## Development

```bash
python runner/installer.py verify-suite
python -m unittest discover -s tests -v
```

The suite check refuses any skill that points outside itself, names a retired skill, or breaks the pipeline order. Edit role files under `skills/book-genesis/references/roles/`, then run `python runner/installer.py generate-agents`. See [contributing](CONTRIBUTING.md), [roadmap](ROADMAP.md), [security](SECURITY.md) and the [changelog](CHANGELOG.md).

Created by [Felipe Lobo](https://github.com/felipelobomotta-blip). MIT licensed.
