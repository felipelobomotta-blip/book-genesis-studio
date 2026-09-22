# Host compatibility and evidence

What has actually been exercised, per host. A supported install target means the files land where the host looks for them; it is not a claim that a full book was written there.

Updated 2026-09-22 for 6.0.0-beta.1.

## Full-book runs on 6.0

| Host | Complete book, idea to package | Independence reached | Time and cost |
|---|---|---|---|
| Claude Code | pending: required for 6.0.0-beta.1 | | |
| Codex | pending: required for 6.0.0 | | |
| OpenCode | pending: required for 6.0.0 | | |
| Hermes Agent | pending: required for 6.0.0 | | |
| OpenClaw | pending: required for 6.0.0 | | |
| Any host, by someone other than the maintainer | pending: required for 6.0.0 | | |

Each run is recorded in the [casebook](../SHOWCASE.md) with its independence grade, wall-clock time and cost, and those numbers become the "what a book costs" line in the README. Until then, this table stays empty rather than estimated.

## Installation

The test suite installs every target into a temporary folder through the real command line, checks every copied file byte for byte, reinstalls to confirm nothing changes, and runs on Windows, Linux and macOS with Python 3.10 and 3.12. It never starts a model. It covers all sixteen targets listed by `python runner/installer.py targets`.

## Headless tools for cross-family critics

Flags checked against installed tools on 2026-09-22; details in `skills/book-genesis/references/hosts.md`.

| Tool | Version checked | Status |
|---|---|---|
| Claude Code (`claude -p`) | 2.1.272 | flags present; drove real chapter runs in the archived CLI line |
| Codex (`codex exec`) | 0.155.1 | flags present; drove real chapter runs in the archived CLI line |
| Hermes Agent (`hermes chat --query-file -`) | 0.21.1 | flags present |
| Antigravity CLI (`agy`) | 1.2.7 | flags present; an earlier run hit the individual quota and returned exit 0 with an error status |
| OpenCode (`opencode run --format json`) | 1.18.31 | flags present; output parsing not verified end to end |

## Observations carried over from 5.0 (2026-09-10)

These were made with the 5.0 bundle and remain useful facts about the hosts:

- **Hermes** listed all installed skills as enabled; **OpenCode** 1.18.30 discovered them from an isolated config folder; **Gemini CLI** 0.56.0 listed them from an isolated home.
- **Antigravity** CLI 1.1.27 ran a real intake with native file tools and wrote six files; a fresh read-only session recovered the next phase from disk. One response envelope said `SUCCESS` while containing a denied action and no answer: check the content, not the envelope.
- **Gemini** loads workspace skills only in a trusted workspace; user-scope discovery works without changing trust. `GEMINI_CLI_HOME` is a substitute home, so skills live under `$GEMINI_CLI_HOME/.gemini/skills`.

## Check your own install

```bash
python runner/installer.py verify-suite
python runner/installer.py install opencode
python runner/installer.py verify-install opencode
opencode debug skill
```

Then open a new host session, ask it to use `book-genesis`, start a small project, and list the files it saved. A chat message is not proof that a file exists.

## Not yet established

Repeated complete manuscripts per host, recovery after context limits and quota exhaustion, measured cost and latency, and reading by independent humans. No benchmark supports calling this the best book workflow, and nothing here guarantees sales.
