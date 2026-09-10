# Agent-native restoration — September 10, 2026

## Source and preservation

The owner requested a return to skills installed inside users' own agents. The restored foundation is `c9744863efab1a8de8728f8f67d2cbe0cfc6b8d6`, already published as `codex/portable-skill-runtime`. It contains the portable distribution manifest, installer, canonical universal core, specialist skills, and deterministic file helper.

The restoration is a new commit on top of `ad26cf63d799f3814f01b0719c5a6051323ae76f`, the public master before restoration. No force-push or history deletion is needed. The standalone application remains recoverable at that commit and its prior releases. The separate local application checkout and its unpublished changes were left intact.

Historical case notes report longer manuscripts under agent-based workflows. They do not prove this exact commit produces the best prose, and no new full manuscript was generated to justify the restoration. This is a product-direction restoration with installation verification.

## Changes relative to the recovered foundation

- Add OpenClaw and Hermes targets to the existing installer, including their runtime-home variables.
- Keep the same complete 15-skill package for each host and the existing conflict/backup behavior.
- Clarify installed reference resolution and use of native file tools when the optional repository helper is absent.
- Replace the public README with the agent-native setup and an explicit evidence boundary.
- Retain current exclusions for private/generated files.
- Add Windows/Linux CI for suite validation, regressions, and installer previews.

The original editorial workflow has not been redesigned during restoration. See [ADR 0011](adr/0011-restore-agent-native-skills.md).

## Local verification

- `python runner/cli.py verify-suite`: passed.
- `python -m unittest discover -s tests -v`: 28 tests passed in 20.041 seconds on Windows / Python 3.11.
- Tests install the suite into isolated directories for Claude, Codex, Kimi, OpenClaw, Hermes, and Shared targets.
- OpenClaw/Hermes CLI tests verify dry-run, actual copying, byte-for-byte core reference integrity, reinstall behavior, and destinations containing spaces.
- Existing tests cover conflict refusal and backup before forced replacement.
- Both new PowerShell target previews passed with explicit temporary destinations.
- Git whitespace checks passed.

The 28 tests cover the recovered installer and file helper. They are not replacements for, or a numerical comparison with, the later application's hundreds of tests. This restored tree does not include that application.

## What is not claimed

No fresh full-book run inside OpenClaw or Hermes, no new human-reader study, no automatic migration of standalone-app project state, and no guarantee of bestseller sales. The host supplies the model, authentication, permissions, persistence behavior, and quota. Installation does not certify those host capabilities.

Sources for host directory conventions: [OpenClaw skills](https://docs.openclaw.ai/tools/skills) and [Hermes skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills), checked September 10, 2026.
