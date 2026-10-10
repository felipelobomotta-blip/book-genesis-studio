# Native CLI launcher prototype

Book Genesis can have a small command line while keeping its writing architecture in the existing skill. This local prototype prepares a verified project and opens **the unmodified Codex or Claude Code CLI**, with its own login, terminal UI and permission prompts. The native agent remains the single orchestrator.

It is a working entry point for the current recovery checkout, not a new released application or a new editorial engine. One supervised Codex run delivered a complete six-chapter manuscript and verified EPUB within its 6,000–7,500-word contract. It required author and execution-review interventions, and its literary gates failed. That establishes technical delivery for this short test, not unattended reliability, full-length novel quality or publication readiness. The underlying longer recovery pilot also has unresolved length and literary-quality checks; adding a launcher does not resolve them.

## Use it from this checkout

You need Python 3.10+ and a separately installed Codex or Claude Code. The launcher does not install agent runtimes, change their settings, copy credentials or create provider accounts.

```bash
python book_genesis.py doctor
python book_genesis.py connect codex
python book_genesis.py new ./books/my-book --host codex
```

The new command asks for an idea and the title-page author or pen name before handing your terminal to the native UI. At the name prompt, Enter explicitly chooses `Anonymous`. Supply `--author` to skip that prompt; `--prepare-only` never asks for a name or calls a model. No name is inferred from your account or computer. If you omit `--host`, it detects the available hosts and asks you to choose when both exist. Native permission and workspace-trust prompts remain visible. Enter `ok` at the skill's author checkpoints, request a change, or ask the agent to go to the end.

To use Claude Code, use `connect claude` and `--host claude`. Sign-in completes through the official native CLI, not a Book Genesis login form.

Explicit selections are forwarded without a model fallback:

```bash
python book_genesis.py new ./books/my-book --host codex \
  --idea "A station clock records the trains that never arrived." \
  --model gpt-5.6-luna --effort high
```

Model availability depends on the user's account and native CLI. Omitting `--model` or `--effort` uses that native CLI's configured default; Book Genesis does not select a hidden alternative. `--language` defaults to `English`. Use `--idea-file` for a longer UTF-8 idea, and `--autonomous` to request the existing skill's go-to-the-end mode.

For an explicit Claude effort, the launcher forwards `--effort` and the matching `CLAUDE_CODE_EFFORT_LEVEL` in both the child's inherited environment and CLI-scoped `--settings`. Native saved settings can reapply their environment values after startup, so forwarding a flag or process environment alone is insufficient. Only this effort key is overridden; the parent environment and saved native settings stay unchanged. Omitting effort keeps the native default. The native UI remains the place to verify the effective level and any account restrictions. See [Claude effort configuration](https://code.claude.com/docs/en/model-config#adjust-effort-level) and [CLI settings](https://code.claude.com/docs/en/cli-reference).

Prepare without making a model call:

```bash
python book_genesis.py new ./books/my-book --host codex \
  --idea "A station clock records the trains that never arrived." --prepare-only
python book_genesis.py resume ./books/my-book
python book_genesis.py status ./books/my-book
```

Run `new` only on an empty folder; it never writes into a folder that already has files, so an existing manuscript is never overwritten. Preparation claims its metadata folder atomically, so two simultaneous attempts cannot overwrite one another. If preparation fails, cleanup checks the resolved paths and removes only the directories that attempt claimed; unrelated files remain. A cleanup failure is reported and the partial files are kept. `new` and `resume` without `--prepare-only` need an interactive terminal. Without one, they stop before preparing or locking anything and print the command to run.

`resume` opens a new native context, which reconciles the book from files; it does not claim to resume a provider's original conversation ID. In this prototype, `resume` accepts projects prepared by this launcher, for the host they were prepared for (`--host` cannot switch an existing book to another agent). An original pending author checkpoint remains pending. An existing project uses its installed skill snapshot; a changed skill file, a changed Claude agent, or a Claude project that was moved or copied to another folder blocks launch instead of silently upgrading the book.

`resume --author` supplies an explicit title-page name for that invocation, without rewriting the original project defaults. A newer author credit already saved with the book takes precedence when no override is supplied. Older prepared projects remain supported; when no author is known, the native agent is instructed to collect it at the first checkpoint instead of discovering the missing metadata after drafting. A `--prepare-only` launch plan preserves explicit model, effort and author selections in its displayed resume command, using literal PowerShell arguments on Windows.

`status` prints the project's host, language and collaboration mode, any launcher lock, the number of launches and the last launch receipt, and then runs the installed core's progress and delivery checks. When `evaluations/review-index.json` exists, it supplies that saved index to the core so the original raw reviews are checked against the current prose. It does not regenerate evidence. A missing index, invalid or stale review, or invalid delivery still returns a failure. These checks are separate from literary gates and publication approval.

## Same core, small launcher

```text
book_genesis.py
  -> local project preparation + install verification
  -> official native CLI + its user-owned sign-in and live UI
  -> skills/book-genesis: the same eight phases and role packets
  -> existing native-call guard, reader validation and promotion helpers
  -> saved chapters, current-text reviews, verified exports
```

The launcher copies the suite to `<book>/.book-genesis/skills/` using the existing installer. Claude projects also receive the generated reader and auditor agents in their own `.claude/agents/` folder. The startup message names the project-local skill, its host contract and its orchestrator prompt. It does not copy phase policy, score rules or role prompts into launcher code.

The launcher passes the terminal streams directly to the native CLI. Activity is the native agent's actual output. There is no simulated thinking feed or fabricated percentage. A future Book Genesis terminal UI can render supported native events, elapsed time and saved artifacts; it must keep the same skill as its source of editorial policy and preserve native approvals.

`.book-genesis/launcher.lock` prevents two launcher sessions owning a project. It is separate from the core's scoped `work/host-calls/.active.lock`, so launching the parent does not block its independent readers. While the native CLI runs, the lock names both the launcher PID and the native PID. Launch receipts in `.book-genesis/launches/` record the exact native command (without the long start prompt, which is stored as a SHA-256), the selected host/model/effort, the native PID and the exit status.

Process lifecycle:

- A nonzero native exit, including a native CLI rejecting a flag, is returned as the launcher's exit code and recorded as `native_session_exited` with that code.
- A missing native CLI stops before any lock or receipt. A native CLI that cannot start is recorded as `launch_failed` and releases the lock, because no process was started.
- Interruption (Ctrl+C reaching the launcher, or a termination request) stops the owned native process tree with the core's existing shutdown helper, records `interrupted`, and only then releases the lock. The launcher waits in short intervals so Ctrl+C is handled on Windows while the native process is still alive. While a native terminal UI has the keyboard, Ctrl+C belongs to that UI, as usual.
- On Windows the native process is created suspended, assigned to a private kill-on-close job, and then resumed. Its descendants belong to that job, even after their immediate parent exits. A normal native exit also stops remaining descendants and checks that the job has no active processes before releasing the book lock. If the launcher is terminated after registration, Windows closes its private job handle and stops the owned tree; the stale ownership record remains for inspection. No other session's jobs are opened. This uses the documented [Windows Job Objects](https://learn.microsoft.com/windows/win32/procthread/job-objects) API through Python's standard library.
- If shutdown cannot be verified, the receipt says `shutdown_unverified` and the lock is kept. Stale locks are never cleared automatically: check that the recorded PIDs have stopped, then delete the lock file yourself.
- On macOS and Linux the native CLI runs in its own session so its whole tree can be stopped; the launcher forwards terminal resizes to it, and after the native CLI exits it stops any processes that CLI left running before releasing the lock. These POSIX paths have not yet been exercised on a POSIX machine.

An exit code of zero says that the native session exited successfully. It does **not** mean a book was completed. `status` runs this checkout's read-only progress and current-text delivery/review verifiers; it does not manufacture scores, receipt evidence or a publication approval.

`status` now shows the saved phase, measured chapter and word counts, exported-file status, current-reader evidence, and the saved audit/revision outcomes in a compact English summary. A delivered manuscript with failed literary gates explicitly says that editorial work remains. `status --json` emits one JSON object containing the full verifier reports and launch records for automation. Status exit zero means the technical checks passed, even when the report says `needs_revision`; it is not a quality score.

Status can inspect a project whose installed skill no longer matches this checkout. It uses the verifier scripts shipped here, never a modified script inside that project, and separately reports whether the snapshot permits resume. Resume still requires its verified original snapshot; status does not upgrade or edit the book. Malformed checker output, a contradictory successful exit, a timeout or a permission error remains a visible failed check with diagnostics. Missing evidence never becomes a successful empty result.

### Windows paths

The installed skill sits several folders deep inside the book, and the installer stages a copy next to it. Windows without long-path support limits ordinary paths to 260 characters, so the launcher uses Windows' extended path form for installation, verification and its own records. A book folder whose own path is shorter than about 240 characters is supported even when the installed files exceed 260 characters. The native agent and the core's Python scripts open the book's own files with ordinary paths, so a short book folder path is still the safest choice.

Some restricted Windows sandboxes deny renaming a staged directory (`WinError 5`). The installer's atomic promotion depends on that rename, so preparation fails there; it is an environment restriction, not a passing state.

## Subscriptions and billing

Checked against official documentation on October 10, 2026:

- **Codex:** the native CLI supports signing in with ChatGPT for subscription access, alongside API-key billing. Its noninteractive execution can also reuse saved native authentication. The launcher delegates sign-in to `codex login` and inspects `codex login status`; it does not read `auth.json`. [Authentication](https://learn.chatgpt.com/docs/auth), [noninteractive mode](https://learn.chatgpt.com/docs/non-interactive-mode).
- **Claude Code:** the unmodified native CLI lets the end user sign in with an eligible Claude subscription. Anthropic's documentation distinguishes that native use from a third-party app collecting Claude credentials or routing subscription tokens. The launcher opens the native CLI and its own `auth login` flow. It does not implement Claude.ai OAuth, redistribute a modified binary or intermediate inference billing. A distributed product must also meet Anthropic's stated commercial and branding conditions. [Authentication](https://code.claude.com/docs/en/authentication), [legal and compliance](https://code.claude.com/docs/en/legal-and-compliance).

The official CLIs retain all their authentication methods. `doctor` reports a billing category and version, without emitting account email, organization or tokens. It does not verify remaining quota or prove that a requested model can run. Account limits, enabled extra usage and native API/provider configuration still apply; the launcher does not promise unlimited use or zero additional charges.

OpenCode, Hermes, OpenClaw, Antigravity and the other installer targets are **not subscription connections verified by this prototype**. A host accepting the skill is a separate fact from its providers supporting subscription billing. Each additional launch adapter needs an official supported authentication path, current CLI-contract checks and an actual integration test before it is advertised.

## Validation boundaries

The later [October 10 quality-recovery record](quality-recovery-20261010.md) covers the readable status, rubric-evidence checks, 234-test result and staged editorial experiment. The chronological table below remains the original launcher acceptance record; it is not a fresh full-book test of those later changes.

`tests/test_native_launcher.py` covers native argument forwarding, account-output redaction, explicit model/effort, preserving an existing manuscript, rollback of a failed preparation, local core verification, changed-snapshot and moved-project rejection, author-checkpoint preservation, one owner, and truthful exit receipts. Lifecycle tests start a real child process in place of the native CLI to check nonzero exits, startup failure, the lock naming the running PID, interruption stopping a child and its descendant before the lock is released, and an unverified shutdown keeping the lock. A long-path test prepares, verifies and launches a Claude project whose installed files exceed 260 characters. These tests establish launcher behavior, not a complete-book result.

Status as of October 10, 2026, on Windows 11 with Codex CLI 0.156.1 and Claude Code 2.1.280:

| Check | Result |
| --- | --- |
| Deterministic suite after the status fix | Installer suite verification passed; 213 unit and integration tests passed on Windows. Process fixtures exercise actual child trees; synthetic review fixtures are not literary evidence. |
| `doctor` against both real CLIs | Signed in: ChatGPT plan (Codex) and Claude plan (Claude Code). No model call. |
| `new --prepare-only`, `resume --prepare-only` and `status` for both hosts, folder with spaces and non-ASCII characters | Passed. No model call. |
| Real Codex and Claude Code binaries rejecting an unknown flag through the launcher | Exit 2 and 1 recorded; lock released. No model call. |
| Headless canary: Claude Code subscription, `--model opus --effort medium`, launcher start prompt, print mode | Reported model `claude-opus-5-5`; read the project-local skill; stopped at the Phase 0 author checkpoint and saved it. A second headless session given the resume prompt showed the same checkpoint again without accepting it. |
| Interactive Codex terminal session through `new` | Passed through Phase 0, with native trust prompts and live activity, using `gpt-5.6-luna` / `high`. Saved the author checkpoint, exited with native code 0, recorded the PID and released the launcher lock. This was not a complete book. |
| Interactive Codex terminal session through `resume` | Reconciled the same saved project, verified 43/43 skill files and showed the pending Phase 0 checkpoint again without accepting it. The native UI reported `GPT-5.6-Luna high`. |
| Interactive Claude terminal session through `resume` | Entered the actual native UI with live tool activity and kept the existing Phase 0 checkpoint pending. Discovered that native saved environment settings overrode `--effort medium`; process environment alone did not fix it. After adding CLI-scoped settings, the native status confirmed medium effort. Closed through native `/exit`: exit 0, receipt saved and lock released. A complete checkpoint render and book through Claude remain unverified. |
| Complete short book through the launcher | Supervised Codex run: six chapters, 7,310 visible prose words, eight phases, Markdown and EPUB. Independent post-run core verification passed for complete progress, source/output hashes, EPUB content and the five declared current-reader scopes. The earlier 25-percent checkpoint remains degraded. Two revision passes promoted no candidate; an age/canon conflict remains open. Calibrated floor 6.40, weighted average 7.15, target 8.5 unmet. Private QA credit only; not publication-ready. |
| Final native-session shutdown | Closed through native `/exit`, exit 0. Launcher and scoped-call locks absent; recorded launcher/native processes absent in Windows process readback. Session success remains separate from book completion. |

The main book session used Codex CLI 0.156.1 with `gpt-5.6-luna` / high effort. Most early scoped calls resolved a different installed Codex build, 0.162.0-alpha.17.2, while keeping the exact model and effort; a later approved scoped call used 0.156.1. The startup instruction now tells scoped roles to reuse the executable prefix in the current launcher receipt. A new complete run with that instruction and upfront author collection remains outstanding. The existing test is preserved rather than presented as a fresh acceptance of every later launcher change.

Keep validation evidence outside the repository. Native sign-in checks, an actual agent reading the installed build, first-checkpoint terminal behavior and a complete idea-to-export run are separate checks. A headless print-mode canary is not the interactive terminal test. Record which were actually run; never substitute `doctor` or an installer pass for full-book acceptance.
