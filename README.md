# Book Genesis

**Your creativity. Your agent. Your book.**

Book Genesis gives your AI agent a workflow for turning an idea into a complete book: planning, chapter-by-chapter writing, blind simulated readers, an editorial audit, bounded revision, and an export with a logline, blurb, synopsis, query letter and cover brief. You agree at each step, or tell it to run to the end. Complete unattended runs are still being validated; this is a beta, and the reports preserve failed checks.

**Read a book it made:** [Vicente, O Lago das Mensagens](https://github.com/felipelobomotta-blip/book-genesis-studio/releases/tag/case-vicente-v1) · 32 chapters · 51,945 words · EPUB and PDF · Brazilian Portuguese. Made with an earlier version; its score is self-assessed and no outside reader has reviewed it yet. Judge it yourself.

![An idea moving through files and writing skills into an open book](assets/brand/book-genesis-workflow.png)

Version 6.0.0-beta.1 · MIT licensed · free · runs on your own agent and account.

**Try a small review first:** [Catch a character using a secret before learning it](examples/continuity-review/README.md). Three short excerpts, a consistent control, real recorded AI feedback and unchanged manuscript files. Copy the prompt into your agent to run your own review. The supplied verification script checks the saved evidence; it does not call a model.

## The goal

A book written with the measured patterns of books readers finish, criticized by readers who cannot see the plan, and packaged to sell. That is the goal every part of the workflow is built around. It is not a promise: no workflow can guarantee a bestseller, and this one says so in every report.

## How it works

1. **Intake.** Your idea becomes a brief: genre, reader, length, comparable books in your idea's language, and four simulated readers built for this book.
2. **Foundation and architecture.** Characters with wounds and contradictions, a theme asked as a question, a voice with a rhythm anchored to real books, a chapter plan, and a ledger that keeps facts straight.
3. **Drafting.** Every chapter saved as a file. Chapter 1 goes to the four readers before the rest is written; every fifth chapter gets a continuity check and another read.
4. **Audit and revision.** A read-only auditor quotes exact passages. Revision runs against two gates, the readers' and a ten-part rubric, at most three passes each. A revised chapter is kept only under the recorded reader decision rule.
5. **Score and package.** A plain report of where the book stands, plus the editorial package, a hook test of alternative titles and blurbs, and the portable `manuscript.md` plus validated EPUB by default. DOCX and PDF are optional when their dependencies already exist. Delivery records any unmet literary gates; it is not publication approval by a human.

Everything lives in a folder you own. Close the session, come back tomorrow in any supported agent, and it picks up from the files.

## Install

You need Python 3.10 or newer, Git, and an agent that can read and write files.

```bash
git clone https://github.com/felipelobomotta-blip/book-genesis-studio.git
cd book-genesis-studio
python runner/installer.py install claude
```

Replace `claude` with your agent. `python runner/installer.py targets` lists them all; `--dry-run` shows what would change first; `verify-install` checks the result. Upgrading from 5.x retires the old skills automatically when they are unchanged. Details: [installation guide](docs/portability.md).

| Agent | Target | Status |
|---|---|---|
| Claude Code | `claude` | installer supported; full-book acceptance pending |
| Codex | `codex` | installer supported; full-book acceptance pending |
| OpenCode | `opencode` | installer supported; full-book acceptance pending |
| Hermes Agent | `hermes` | installer supported; full-book acceptance pending |
| OpenClaw | `openclaw` | installer supported; full-book acceptance pending |
| Kimi Code, Cursor, GitHub Copilot, Antigravity (app and CLI), Gemini CLI, DeepSeek Harness, Qwen Code, Pi, Windsurf, a shared folder | see `targets` | installs; not yet tested with a full book |

What has actually been run where is tracked in [compatibility](docs/compatibility.md). A verified full 6.0 book in each host remains part of the release plan.

## Start a book

Open your agent in an empty folder for the book and say:

> Use book-genesis. My idea: a retired train dispatcher finds a farewell letter inside a station clock.

In agents with skill commands, `/book-genesis` works too. The agent writes in the language you use. To let it finish without stopping, say "go to the end" at any check-in.

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
