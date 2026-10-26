# Book Genesis native plugins

The author installs Book Genesis inside an existing agent, then describes a book in ordinary language. The host supplies its model, conversation, file tools and permissions. Book Genesis supplies the writing workflow, bounded reviews, saved checkpoints and export helpers. User approval: the shared-core/plugin approach was proposed and explicitly accepted in the chat on 2026-10-23.

## Approach

Use one portable skill bundle, Codex and Claude manifests/catalogs, and a small DeepSeek Harness skill-provider plugin. Reuse the four existing skills and generated Claude reviewers. Keep the optional controller for advanced unattended execution. A new standalone application would duplicate the host UI; a remote MCP service would add hosting and authentication without improving this file-based workflow. Neither is needed for this release.

## Experience and constraints

- Install in the host's plugin manager. New users describe their idea; the agent handles files and technical commands. No Book Genesis account, API key, backend or provider auto-install.
- If no idea was supplied, offer starting, continuing or reviewing a book. Ask only for missing decisions. Use the current workspace, never the installed plugin cache, for manuscripts.
- Existing controlled checkpoints remain controller-owned. Status or review requests must not start generation or rewrite a manuscript. Missing tools produce actionable messages.
- Explain saved progress and the next action in plain language. Show real activity and saved artifacts, never fabricated percentages, hidden reasoning or simulated work.
- Product assets and documentation are English; author conversation and prose follow the chosen book language.
- Preserve evidence and quality gates. Packaging success is not evidence of a completed book or a score above 90. Host quotas still apply.
- Ship an allowlisted, reproducible archive with hashes. Exclude personal books, sessions, caches, credentials and development debris. Refuse symlinked inputs and overwriting an existing build.
- Codex/Claude are primary targets. DeepSeek is experimental against the inspected developer-preview skill-provider API.

## Boundaries

Root manifests and marketplace entries refer to this checkout's canonical skills. A release builder creates a clean marketplace directory and ZIP from explicitly allowed product paths. DeepSeek registers those same skills with per-skill resource directories; it must never accept an arbitrary candidate path as a file to read. No hooks or background services are necessary.

This task does not publish a marketplace listing or claim host/book acceptance before tests. Native installation and deterministic helper checks require no model call. Real conversational authoring and full-book acceptance are recorded separately.

## Acceptance

Validate manifests, install the clean bundle into isolated Codex and Claude configurations, load all DeepSeek skill resources with its provider contract, and exercise progress/export helpers from the extracted archive outside the repository. Verify exclusions, byte identity, archive integrity, malformed inputs and install paths with spaces. Document the observed host versions and remaining live-book checks.
