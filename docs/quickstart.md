# Quickstart

Book Genesis is a local, provider-agnostic writing runner. You bring the idea, the choices, and the creative direction. It coordinates a structured draft-and-read process around the model providers you choose.

It is a technical beta. It can help make a manuscript, preserve its history, and surface editorial problems. It cannot promise a bestseller, publication readiness, sales, or a response from human readers.

## Before you begin

- Python 3.10 or later.
- A supported route to a text model: a logged-in `claude` or `codex` CLI, a provider you configure in `setup`, a compatible local server, a declared CLI adapter, or `--manual`.
- An idea you care enough about to revise. The program is designed to keep authorship in the loop; it does not replace taste, lived experience, or editorial judgment.

Clone the repository and install the local checkout:

```bash
git clone https://github.com/felipelobomotta-blip/book-genesis-v4.git
cd book-genesis-v4
python -m pip install -e .
book-genesis --help
```

The project is not published as a hosted service. `pip install -e .` installs the copy you cloned. For a portable local build, create a wheel with:

```bash
python -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .
```

## Connect a provider

For a visual workspace after connecting a provider, run `book-genesis studio`. It supports idea entry, detected CLI selection, writing samples, checkpoints, live public prose where supported, saved chapters, safe pause/resume, and EPUB export. See [Writing Studio](studio.md).

Run the setup wizard once:

```bash
book-genesis setup
book-genesis doctor
```

`setup` detects compatible local CLIs, configured key variables, and local servers; it can also configure supported HTTP providers. It keeps personal configuration in `~/.book-genesis/config.yaml` (or `BOOK_GENESIS_CONFIG`). Do not commit that file. Keys are not stored in this repository, prompts, or run logs.

Book Genesis uses your own provider accounts and subscriptions. Model use can cost money. The number of calls depends on genre, chapter count, and revision cycles, so inspect `doctor` and your provider's pricing before a long run.

For the Codex CLI route, authenticate once with `codex login`. If the executable is installed but
the account is not authenticated, Book Genesis stops before writing a chapter attempt and tells you
to run that command; it does not wait indefinitely for the provider.

If you have no CLI or API route, use manual mode. The runner writes each prompt to `work/manual/`; paste a model's response into the matching response file and repeat the command. Manual mode exits with code 5 while waiting for a reply.

## Create a book

Start an interactive run:

```bash
book-genesis new --idea "A night-shift archivist discovers that returned library books remember their readers." --language en
```

You can also let the command ask for the idea, choose a project folder, or keep the session fully non-interactive:

```bash
book-genesis new
book-genesis new --idea "..." --language en --path books/returned-books --yes --plain
```

The guided session pauses after the brief, the outline, and a blind reading of chapter 1. Press Enter to continue. Type feedback to save it as author notes and rerun that checkpointed stage. Type `q` to stop safely, then continue later:

```bash
book-genesis resume books/returned-books
```

If a chapter fails the blind-reader gate during an interactive run, the runner explains what
happened and asks `Try again? (yes/no)`. Answer `yes` to let it start another attempt automatically
(up to three retries), or `no` to keep the best draft and stop safely. `--yes` remains fully
non-interactive and stops on a blocked chapter so scripts and CI keep deterministic behavior.

Use `--human` to require a deliberate human approval after chapter 1. The choice is saved with that project, so every later `resume` continues to require `approve` even when invoked with `--yes`. Without it, the model-reader panel runs and the session continues automatically. Use `--chapters N` for a limited run.

## Read and export

Every project remains a local directory containing its manuscript, drafts, verdicts, artifacts, state, and report. Generate a local reader page or exports when you are ready to inspect them:

```bash
book-genesis review books/returned-books
book-genesis review books/returned-books --open
book-genesis export books/returned-books --format markdown
book-genesis export books/returned-books --format epub --output releases/returned-books.epub
```

`review` creates `review/index.html`; it does not upload the manuscript. `export` writes canonical chapters only, labels incomplete work as partial, and refuses to overwrite an existing export unless you add `--overwrite`.

## If the audit stops the run

The manuscript-level audit must end with exactly one status: `audit_status: pass`, `audit_status: revise`, or `audit_status: major_rewrite`. The last two stop the session at Audit, preserve the report, and return exit code 4. Score and Package do not run.

In an interactive session, the app asks **Revise the book for me? (yes/no)**. Answer `yes` or `ok` to use the audit report to revise the chapters, then run the reader checks and whole-book audit again. Previous versions remain in history. This uses more model calls and does not guarantee that the next audit will pass. Answer `no` to stop with your work saved. With `--yes` or redirected input, an audit failure stops the run instead of starting additional rewrites.

Before those chapter edits, the editor reads the complete saved manuscript and creates one shared revision plan. It settles conflicting dates, names, quantities, and terminology once, then gives each chapter specific actions. The plan is saved under `work/revision-plans/` and reused on resume. Chapter editors and length repairs receive those decisions; blind readers still receive prose rather than the plan. A new audit or new author notes creates a new plan while preserving the earlier one.

When you stop a failed or blocked session with saved canonical chapters, the app still prepares a reading page and draft Markdown/EPUB files. They are labelled as unfinished; this does not bypass the audit or declare the book publication-ready.

## Visible progress and delivery

While a model is working, the session shows its role, provider, and elapsed time every five seconds. Claude Code also streams public prose previews during writing and editing, so you can see the text arrive before the request finishes. Reasoning, tool, and system events are never shown. Connections that buffer their response keep the activity timer and show a preview when the response arrives. A partial stream is never accepted as a finished chapter.

If a length rewrite still overshoots an explicit per-chapter range, the editor can select expendable paragraphs and the runner measures the cuts. Headings, the opening, and the ending are preserved; the normal reader check still applies. Saved drafts remain available, and an unsuccessful repair offers a simple retry.

If a step fails, an interactive session offers a bounded retry in the same session. For a chapter rejected by the model readers, it first explains the changes it will try, using their feedback. You can answer `yes`, `no`, or `ok`.

After all stages pass, the app automatically prepares a local reading page, a Markdown manuscript, and an EPUB in the project folder and displays their paths. Existing export files are preserved under their original names. Your selected book language is retained across stages, and explicit requirements in your idea are passed to the writer and revisers.

For an enforceable short test, include an explicit per-chapter range in your idea, such as `350 to 500 words each` or `350-500 palavras por capítulo`. The runner measures whitespace-separated words, including the chapter heading, and allows up to two length repairs before asking for recovery. It preserves out-of-range drafts. Other free-form length requests remain instructions to the models rather than a guaranteed numerical check.

The internal score counts a rewritten chapter as a revision even if the new attempt passes its first reader check. It also excludes chapters that needed a length repair from first-draft acceptance. This process signal is not a rating of literary quality or the app itself.

## Common local commands

```bash
book-genesis doctor
python -m runner status books/returned-books
python -m runner validate books/returned-books
python -m runner chapter books/returned-books 1 --manual
python -m runner panel books/returned-books 1
python -m runner judge path/to/chapter.md --genre thriller --adapter codex
```

For the full command reference, exit codes, adapters, and operational limits, read [runner.md](runner.md).
