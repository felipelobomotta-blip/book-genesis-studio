# Directory submission packet — beta 7

Prepared 2026-10-26. GitHub release distribution and public directory approval are separate. This document prepares submission; it does not claim a portal upload, approval or listing.

## Listing copy

- Name: Book Genesis
- Subtitle: Your idea. A book you own.
- Publisher: Felipe Lobo (must match the verified developer identity)
- Category: Productivity
- License: MIT
- Price: free plugin; host subscription/API charges and quotas are separate
- Runtime: desktop/local execution, Python 3.10+, filesystem access and a configured agent host
- Package: `book-genesis-5.1.0-beta.7.zip` from the GitHub release; verify against `SHA256SUMS.txt`

Description:

Book Genesis helps turn an idea into a saved manuscript inside your existing agent. It guides planning, chapter drafting, simulated reader reviews, editorial audit, bounded revision and Markdown/EPUB export. It saves progress and source evidence in your workspace so you can inspect and continue the work. Beta: literary quality varies, host limits apply and no bestseller outcome is guaranteed. The complete workflow requires local execution; cloud-chat and mobile compatibility have not been established.

Starter prompts are bundled in `plugin.json`. Icon: `assets/plugin/icon.svg`. Public source, support, privacy and usage links are declared in the OpenAI interface metadata. The package has no MCP server, publisher account login, API backend or telemetry service.

## OpenAI: ChatGPT and Codex directory

1. Open https://platform.openai.com/plugins in the publisher's organization/project.
2. Confirm submission permission and verified individual/business identity; the publisher must complete any identity declarations personally.
3. Upload the skills-only ZIP. `extensions.com.openai.requires_local_executor` is true, marking the local execution requirement. The legacy Codex manifest carries the same flag.
4. Inspect every metadata/skill finding. A local validator is not a substitute for the portal scan. Correct source, build a new immutable package and re-upload if required.
5. Supply the public support/privacy pages and exact reviewer steps below. Do not paste provider tokens or private books.
6. Submit only after installation and workflow evidence meet the directory's current requirements. Approval and public listing remain unestablished until the portal confirms them.

This is a skills-only plugin. The documented allowlist restriction for local MCP submissions does not establish an approval requirement for this package; it has no local MCP server. Portal access/metadata requirements still apply.

Primary sources checked 2026-10-26:
- https://developers.openai.com/plugins/deploy/submission
- https://developers.openai.com/plugins/deploy/desktop-only
- https://developers.openai.com/plugins/plugin-guidelines

## Anthropic directory

The GitHub marketplace supports direct Claude Code installation independently of directory inclusion. Anthropic's current directory portal is https://claude.ai/directory/manage. Submission requires a paid Claude plan and the appropriate account/organization role. Run `claude plugin validate <plugin-folder> --strict`, then prepare the GitHub repository URL, manifest, README, MIT license, support/privacy pages and reviewer instructions for the portal. Check which components run in Claude chat, Cowork and Claude Code; directory installation does not make local process tools available in ordinary chat. Do not claim official approval or full-book runtime validation from a manifest check. No Claude inference calls were made to prepare this release.

Primary sources:
- https://code.claude.com/docs/en/plugins/publish
- https://code.claude.com/docs/en/plugin-marketplaces
- https://code.claude.com/docs/en/discover-plugins
- https://support.claude.com/en/articles/13837440-use-plugins-in-claude

## Reviewer workflow

1. Use a clean local workspace outside the plugin cache. Confirm Python 3.10+ and a signed-in supported agent. Do not provide tokens to the plugin.
2. Install through the pinned GitHub marketplace or extracted release. Confirm the installed version is 5.1.0-beta.7 and four skills are visible.
3. Start a fresh conversation. Ask: `Use Book Genesis. Review these excerpts for a character knowing something before learning it. Do not rewrite the manuscript.` Use the public `examples/continuity-review/` source examples from the repository. Check that quoted evidence is literal and originals stay unchanged.
4. For a generation smoke test, request a short complete mystery with explicit length, then check actual chapter files, review records and Markdown/EPUB. This smoke test does not replace a full-length acceptance run.
5. Interrupt an authorized run, reopen the same book folder and ask to continue. Inspect saved progress and failures, without resetting its budgets or replacing historical receipts.
6. Check final delivery status and literary findings independently. An EPUB file does not mean literary gates passed.

## Outstanding before a readiness claim

- A complete new beta7 book above the requested literary threshold is not demonstrated.
- Live Claude complete-book reliability has not been established; DeepSeek remains experimental.
- Portal automated checks, publisher verification, reviewer acceptance and listing status have not been observed.
- Independent human reading and commercial outcomes are still separate evidence.
