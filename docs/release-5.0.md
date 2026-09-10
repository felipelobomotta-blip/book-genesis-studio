# Book Genesis 5.0

Book Genesis 5.0 is the agent-native release. The public product is a portable set of Markdown skills, prompts, references, state contracts, and editorial gates that run inside the AI host a writer already uses.

## What changed

- Six new installation targets: DeepSeek Harness, Cursor, GitHub Copilot, Qwen Code, Pi, and Windsurf/Cascade.
- One 15-skill bundle for 14 named hosts plus a Shared Agent Skills directory.
- English-first public documentation and an evidence-aware launch kit.
- Remotion source updated to describe a native-agent workflow rather than a hosted “book factory.”
- The interactive book-generation CLI and standalone model-orchestration experiment are removed from the 5.0 product surface. Their historical commits remain visible in Git history.

## What remains deliberately small

The installer/verifier is a maintainer and automation helper. It copies skills, checks references, detects conflicts, and validates installation records. It does not select models, call provider APIs, run background agents, or write literary output. A host agent performs that work under its own account, permissions, context limits, and quota.

## User migration

If you used the old `book-genesis` interactive command, open the same project folder in your preferred supported host and ask it to use `book-genesis`, read `PROJECT_STATE.yaml`, and continue from the saved phase. Copy the complete skill tree into the host's directory using [the portability guide](portability.md). Do not copy only `SKILL.md`.

The 5.0 installer intentionally does not migrate or overwrite old project folders. Existing manuscript files stay where they are. Inspect any legacy state before asking a host to continue.

## Verification boundary

The CI suite verifies the portable bundle and installer across Windows, Linux, and macOS. The [compatibility table](compatibility.md) distinguishes those checks from native writing observations. Six new hosts have source/documentation-verified installation paths; a fresh complete-book run in each is still a separate acceptance task.

## Release acceptance

The tag is `v5.0.0`. The release is ready to distribute as an open-source agent-skills package. It is not a guarantee of bestseller sales or of unattended full-length manuscript production.
