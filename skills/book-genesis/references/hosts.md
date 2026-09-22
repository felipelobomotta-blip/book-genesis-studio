# Host notes

Per-host facts the orchestrator needs to set up critics: how to spawn an isolated reader, and how to borrow a second tool from another model family.

When to load: Phase 0, when setting `independence` in `PROJECT_STATE.yaml`. Role: orchestrator. Checked against each host's documentation on 2026-09-22; hosts change, so prefer what the running host reports about itself.

## Spawning an isolated critic

| Host | Isolated subagent | How | Limit to note |
|---|---|---|---|
| Claude Code | yes, documented | Use the `book-genesis-blind-reader` and `book-genesis-auditor` subagents when installed; otherwise a general subagent with the role file as instructions | Subagents share the model family |
| Hermes Agent | yes, documented | `delegate_task` with the role file and packet | Children inherit every tool; blindness holds by instruction only |
| OpenClaw | yes, when requested | `sessions_spawn` with `context: "isolated"` stated explicitly; thread-bound spawns default to a fork | Pass the isolation flag every time |
| Codex | separate thread; blindness not documented | Subagent from `~/.codex/agents/` or the host's delegation | Run the isolation check in `references/scoring/evaluator-protocol.md` |
| OpenCode | not documented | `mode: subagent` agent through the Task tool | Run the isolation check |
| Kimi Code | yes, documented | Subagent with `tools` limited to reading | |
| Cursor | yes, documented | Subagent in `.cursor/agents/` | Only a read-only switch limits tools |
| GitHub Copilot CLI | own context; blindness not documented | Custom agent with `tools` limited | Delegation is up to the model; run the isolation check |
| Antigravity | yes, documented | `invoke_subagent` with a `tools` list | Agents can read each other's transcripts; headless denials can pass silently |
| Gemini CLI | own history; blindness not documented | Subagent in `.gemini/agents/` | Stopped serving individual accounts on 2026-06-18; Standard and Enterprise still work |

Hosts where a subagent can be pinned to another vendor's model (OpenCode, OpenClaw, Kimi Code, Cursor, Copilot CLI, Hermes) can reach grade A without a second tool: pin the critics to a family different from the writer.

## Borrowing a second tool

Every host above can run shell commands, so an installed CLI from another family can serve as the blind reader. Rules that apply to all of them:

- Ask the author first; it spends that tool's quota.
- Write the packet to a file and send it on standard input. Never pass a chapter as a command-line argument: Windows cuts command lines near 32,000 characters.
- Run from an empty temporary folder outside the book folder, so the tool cannot pick up the plan as context.
- Check the tool's own status, not only its exit code: some return 0 with an error inside the output.
- Save the raw answer to `work/critics/` before parsing it.

Every flag below was checked against the installed tools on 2026-09-22 (Claude Code 2.1.272, Codex 0.155.1, Hermes Agent 0.21.1, Antigravity CLI 1.2.7, OpenCode 1.18.31). The Claude Code and Codex lines also drove real chapter runs in an earlier Book Genesis line in September 2026; the other three are checked for flags only.

| Tool | Command (packet on standard input) | Read the answer from |
|---|---|---|
| Claude Code | `claude -p --output-format text --no-session-persistence --safe-mode --disable-slash-commands --tools ""` | standard output |
| Codex | `codex exec --skip-git-repo-check --ignore-user-config --ephemeral -s read-only -C <empty folder> -o <answer file>` | the answer file |
| Hermes Agent | `hermes chat -Q --query-file -` | standard output; drop lines that start with `Warning:` |
| Antigravity CLI | `agy --input-format stream-json --output-format stream-json`, sending one line `{"event":"user","message":{"content":"<packet>"}}` | the `result.response` of the `result` event; treat `result.status` other than success as a failure even when the exit code is 0 |
| OpenCode | `opencode run --format json` | the text parts of the JSON events; not verified end to end, so prefer its native subagent |

Add `--model` (Claude Code, Antigravity CLI), `-m` (Codex, Hermes) or `-m provider/model` (OpenCode) only when the author picked a model; otherwise let the tool use its default.
