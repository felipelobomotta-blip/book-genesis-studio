# Host compatibility and evidence

Checked September 10, 2026. Every installer target receives the same 15 writing skills and complete references. Model behavior, permissions, context limits, and quotas belong to the host. A target name means a supported installation destination; it is not a full-book certification.

| Target | Actual isolated installation and integrity tests | Native host check in this change |
| --- | --- | --- |
| Claude Code | Passed | No fresh native writing run |
| Codex | Passed | No fresh native writing run |
| Kimi Code | Passed | CLI unavailable in the test environment |
| OpenClaw | Passed | No fresh native writing run |
| Hermes Agent | Passed | Native `hermes skills list`: all 15 enabled |
| OpenCode | Passed | v1.18.30 `opencode --pure debug skill`: all 15 discovered from the isolated config directory |
| Antigravity | Passed | CLI v1.1.27: real intake wrote six files; fresh read-only session recovered the next phase and identified inconsistencies |
| Gemini CLI | Passed | v0.56.0 `gemini skills list`: all 15 enabled from isolated user home |
| Shared Agent Skills | Passed | Generic directory export; discovery depends on the consuming host |

The regression suite verifies all nine targets through the Python CLI: preview, actual copying, reference integrity, and reinstall. CI runs the suite on Windows, Linux, and macOS with Python 3.10 and 3.12, plus installer wrapper previews. CI tests do not start commercial models. See the [recorded host observations](host-verification-20260910.json).

## Antigravity findings

The real intake used the installed bundle and native file tools, without the repository Python helper. It saved `PROJECT_STATE.yaml`, `ASSUMPTIONS.md`, `RUN_REPORT.md`, the brief, market map, and story engine. File inspection found unsupported market assertions and inconsistent state fields. The current intake and host contract now explicitly require evidence labels, directory creation, and consistent state transitions.

A subsequent write-recovery attempt encountered a host-denied terminal command. Its response envelope said `SUCCESS`, but contained no final response and a denied action; no repair is counted as completed. A fresh read-only probe then correctly recovered the title, Foundation phase, three required artifacts, and inconsistent gate/status fields from disk. This verifies reading and recovery diagnosis, not unattended repair or full-book production. The tightened creation instructions still need another complete intake acceptance run.

## Check your installation

```bash
python runner/cli.py verify-suite
python runner/cli.py install opencode --dry-run
python runner/cli.py install opencode
python runner/cli.py verify-install opencode
opencode debug skill
```

Replace the target and host command as appropriate. Pass the same `--dest` to install and verify-install when using a custom directory. `verify-install` compares all installed skill files with the current checkout and installation record. If your checkout or locally edited skills differ, inspect the differences before replacement.

Then open a new host session and ask it to locate `book-genesis`, read its phase manifest and host contract, initialize a small project, and list the actual saved files. Start another session to read those files and identify the next step. Do not count a chat message alone as proof of a written artifact.

For Gemini, workspace-local skill discovery requires a trusted workspace. Our untrusted-workspace probe correctly refused to load project skills. User-scope discovery worked without changing trust. `GEMINI_CLI_HOME` is a substitute home directory, so its skills live under `$GEMINI_CLI_HOME/.gemini/skills`; it is not the skills directory itself.

For Antigravity, current global skills live under `~/.gemini/config/skills`. The tested CLI read workspace `.agents/skills`. If your edition uses a legacy global path, use an explicit destination after checking its documentation. Install into the environment where the agent actually runs, including containers and remote hosts.

## Evidence still needed

Repeated complete manuscripts, context-limit recovery, quota recovery, controlled cost/latency measurements, and independent human reading across hosts are not established by these checks. No comparative benchmark supports calling this system the best architecture or guaranteeing bestseller sales.

Sources: [OpenCode skills](https://opencode.ai/docs/skills/), [OpenCode configuration](https://opencode.ai/docs/config/), [Antigravity skills](https://antigravity.google/docs/skills), [Gemini CLI skills](https://geminicli.com/docs/cli/skills/), [OpenClaw skills](https://docs.openclaw.ai/tools/skills), [Hermes skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills).
