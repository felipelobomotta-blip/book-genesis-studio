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
| Codex | `codex exec --skip-git-repo-check --ignore-user-config --ephemeral -s read-only -C <empty folder> -o <answer file> -m <authorized-model> -c model_reasoning_effort="<authorized-effort>"` when the author selected a model and effort | the answer file |
| Hermes Agent | `hermes chat -Q --query-file -` | standard output; drop lines that start with `Warning:` |
| Antigravity CLI | `agy --input-format stream-json --output-format stream-json`, sending one line `{"event":"user","message":{"content":"<packet>"}}` | the `result.response` of the `result` event; treat `result.status` other than success as a failure even when the exit code is 0 |
| OpenCode | `opencode run --format json` | the text parts of the JSON events; not verified end to end, so prefer its native subagent |

Add `--model` (Claude Code, Antigravity CLI), `-m` (Codex, Hermes) or `-m provider/model` (OpenCode) only when the author picked a model; otherwise let the tool use its default. For a fresh Codex session, propagate every explicitly authorized model and reasoning effort: for example, a requested `high` effort requires `-c model_reasoning_effort="high"` alongside `-m <authorized-model>`. `--ignore-user-config` must not silently erase those choices; supply replacements when they were authorized, and do not hardcode an effort when they were not.

Before attributing a run to the requested configuration, inspect the CLI header or equivalent host receipt for the actual `model:` and `reasoning effort:` values. Record a mismatch as a configuration failure or `not_run`; an exit code alone does not prove that the authorized model or effort was used.

## Guarding one native host call

When a phase needs one caller-selected native CLI, run it through
`scripts/run_host_call.py`. The guard launches the existing CLI and records
its outputs; the host still orchestrates the book and selects the model. The
caller chooses an already installed command. The wrapper does not author
prompts, install packages, select a provider, read global config or invoke a
provider SDK.

Use a fresh call id for every attempt and pass an argv JSON array (or an object
with `argv` and optional `timeout_seconds`):

```text
python <skill-root>/scripts/run_host_call.py --book-dir <book> --call-id chapter-03-reader-r1 --packet <packet> --command-json '{"argv":["<native-cli>","-o","{output}"],"timeout_seconds":900}'
```

The wrapper passes the immutable packet on standard input, with `shell=False`.
`{output}` expands to a per-call pending response path; after exit 0 and a
nonempty response, that file is atomically promoted to the stable `response`
path. `{cwd}` expands to a fresh
temporary working directory outside the book's tree (it may be a sibling under
the system temporary directory). The call keeps
`work/host-calls/<call-id>/packet`, `stdout`, `stderr`, `response.pending`,
`response` and `receipt.json`. A child must exit zero and leave a nonempty
response before a
receipt can be `completed`; a nonzero exit, timeout or empty response leaves a
`failed` receipt and all captured evidence, including any pending response.
A timeout terminates only the owned child process tree. Receipts include packet, argv, stdout, stderr and
response SHA-256 fields plus `started_at`, `finished_at` and the child exit
code; the captured streams remain raw so a reviewer can inspect host headers
and diagnostics independently. A stale lock is never auto-recovered by this
wrapper, even when recorded PIDs appear dead; inspect and resolve it
explicitly after confirming no child remains.

The book has one active external host call. A second invocation returns exit
75 with `status: busy`, the active call id and a wait instruction; it must wait
for the first receipt rather than launch another provider. A completed call id
is idempotent only when packet and argv hashes match and the saved packet,
stdout, stderr and response still match their receipt hashes. Reusing it with
changed input, tampered evidence or a failed call is rejected; retry with a
new id and preserve the old evidence. The native caller must await completion
and read the receipt, never infer failure from a missing response while the
receipt is still absent. An unreadable or uncertain lock fails closed; stale
recovery is disabled to avoid an unlink race, including when both recorded PIDs
appear dead.
