# Book Genesis plugin beta

Install Book Genesis in your existing agent, then describe your book. You do not need a Book Genesis account, API key, separate writing application or server. Your host's subscription, quotas and tool permissions still apply. Python 3.10+ is needed for verification and export; the agent checks this before starting.

Version **5.1.0-beta.7** is distributed from the GitHub repository and its [pre-release ZIP](https://github.com/felipelobomotta-blip/book-genesis-studio/releases/tag/v5.1.0-beta.7). It is **not listed in the public plugin directories**. The complete writing workflow requires desktop/local execution; normal web/mobile chat compatibility has not been established.

Beta 7 adds scene/cost/consequence planning, character knowledge boundaries, voice calibration guidance, source-selected repair citations, bounded chapter-length recovery and clearer saved activity. Read the [integration evidence](editorial-integration-20261025.md) and [release notes](releases/5.1.0-beta.7.md) for validation limits. An update applies to new projects; existing books keep their frozen engine, evidence and attempt budgets.

## Codex: two commands

Run in a terminal with a recent Codex CLI:

```bash
codex plugin marketplace add felipelobomotta-blip/book-genesis-studio --ref v5.1.0-beta.7
codex plugin add book-genesis@book-genesis
```

Start a new conversation in a writable folder for your book. Enable **Book Genesis** in Plugins if needed, then select it in the composer. Do not generate books inside the plugin installation/cache folder.

The tag pins the tested beta. Register the repository root, not a raw `marketplace.json` URL. The repository contains `.agents/plugins/marketplace.json` for Codex.

## Claude Code: two commands

Inside Claude Code:

```text
/plugin marketplace add felipelobomotta-blip/book-genesis-studio
/plugin install book-genesis@book-genesis
```

Start a new session. The plugin bundles four skills and two generated reviewers. Installation and manifest validation do not establish a complete Claude book run. No Claude model calls were made for this release preparation.

In Claude's graphical interface, open **Customize > Plugins > Add > Add marketplace**, enter `https://github.com/felipelobomotta-blip/book-genesis-studio`, then install Book Genesis. Skills may be available in other Claude surfaces; the unattended local workflow and reviewer behavior must be verified in the intended runtime.

## Give it your idea

> Use Book Genesis. My idea is a mystery about a piano tuner who discovers a message hidden in an old recording. Write the complete book in English, revise it and export Markdown and EPUB. Make reasonable creative decisions and continue without asking me to approve every chapter.

For guided collaboration: "Check the plan with me first." To resume: "Continue my book in this folder." For a review: "Review this manuscript for continuity problems without rewriting it."

The host may request access to the book folder and permission to run local tools. The plugin never asks you to paste account tokens. Your model subscription or API usage belongs to the host; the plugin does not bypass quota or billing limits.

## ZIP installation and troubleshooting

1. Download `book-genesis-5.1.0-beta.7.zip` and `SHA256SUMS.txt` from the release.
2. Extract the ZIP into a new folder. Keep hidden `.agents`, `.codex-plugin` and `.claude-plugin` folders. Do not overwrite an installed/frozen book engine.
3. For Codex, use `codex plugin marketplace add "<absolute path to extracted folder>"`, then `codex plugin add book-genesis@book-genesis`.
4. For Claude Code, use `/plugin marketplace add <absolute path to extracted folder>`, then `/plugin install book-genesis@book-genesis`.
5. Restart the agent session. If plugin commands are unavailable, update the host through its official installer. If Python is missing, install Python 3.10+ and restart so it is on PATH.

If an older local Book Genesis marketplace is already configured, inspect `codex plugin marketplace list` or `/plugin marketplace list`. Remove/re-register only that marketplace source if necessary, leaving your book folders intact. Do not overwrite cache files by hand. Installed old books still keep their frozen runtime.

For a future Codex update, register the desired published tag and use the host's plugin install controls. For Claude Code: `/plugin marketplace update book-genesis`, then `/plugin update book-genesis@book-genesis`, and restart. Always confirm the version before a new project.

[Support](../SUPPORT.md) · [Privacy](../PRIVACY.md) · [Use and limitations](../TERMS.md) · [Directory submission packet](directory-submission.md)

## DeepSeek Harness (experimental)

The package exposes a native Cordis plugin at `distribution/deepseek/index.mjs`, injecting the `skills` service and registering the same four skills with their packaged resource directories. Its `dsh.bundle` manifest activates `cordis.patch.yml` through the native plugin manager:

```text
dsh plugin --profile book-genesis-test add "<absolute path to the book-genesis plugin folder>"
dsh --profile book-genesis-test --dump-config
```

The composed configuration must contain the `book-genesis-skills` row. This follows the developer-preview bundle and `registerProvider` contracts inspected on 2026-10-23.

No npm registry publication is implied by `package.json`. A provider contract test does not establish installation or full-book compatibility with a live DeepSeek session. The package does not replace your configured model or start its own model client.

## What happens after your idea

For autonomous Codex books, the bundled bridge prepares a verified skill snapshot and immutable execution contract, then checks the selected native connection for at most 60 seconds before consuming book attempts. The host must permit that connection through its normal approval flow. Book Genesis resolves the workspace, records creative assumptions, plans the book, drafts chapters, runs simulated reader reviews and a structural audit, makes bounded revisions, and exports the saved manuscript. Progress is saved in your book folder. The agent reports actual files and chapter counts. If a host limit interrupts the session, reopen that folder and ask to continue.

Existing controller-owned checkpoints keep their original controller. The plugin does not reset revision budgets, reopen a failed quality gate or claim that a finished draft met a score it did not achieve. Runtime isolation and literary results must be verified per host. Sales and bestseller status are never guaranteed.

## Build and check (maintainers)

```text
python runner/installer.py verify-suite
python runner/plugin_bundle.py build --output dist/plugin-beta
python runner/plugin_bundle.py verify dist/plugin-beta/book-genesis
python -m unittest discover -s tests -p test_plugin_bundle.py -v
claude plugin validate dist/plugin-beta/book-genesis --strict
```

Choose a new output directory for each build. Run npm packaging only from this clean built folder, never from an unreviewed development checkout. `distribution/plugin-files.json` explicitly lists every shipped path. Update that reviewed list when adding a resource; never generate it from arbitrary untracked files. The ZIP contains the selected skills, reviewers, manifests, small plugin assets, license, this guide and the existing preparation/controller bridge. The bridge is operated by the host agent; authors do not need to learn its commands. Its receipt hashes every payload file. The receipt detects accidental modifications; it is not a cryptographic publisher signature. Development folders, personal manuscripts, authentication files and runtime caches are not package inputs.

The source manifests all use one version; the builder fails on disagreement. GitHub and public-directory publication are separate release actions. See `docs/plugin-validation-20261023.md` for observed checks and limitations once available.
