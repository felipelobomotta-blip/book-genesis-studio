# ADR 0011: Restore agent-native skills as the public product

Accepted September 10, 2026, following the owner's explicit request to restore the working skills approach on GitHub and install it into users' own CLIs, OpenClaw, and Hermes agents.

## Decision

Restore the repository tree from `c9744863efab1a8de8728f8f67d2cbe0cfc6b8d6` (`codex/portable-skill-runtime`) as the foundation of a new commit descended from the existing public master. Preserve history; do not force-push or erase the standalone application experiment.

The canonical workflow is `skills/book-genesis/SKILL.md`. The host agent owns inference, permissions, tool execution, and conversation. The optional Python helper handles installation and project files; it does not call model providers. This decision supersedes ADR 0001's requirement that the Python model runner orchestrate creative work.

Restore the existing skill content rather than redesigning its literary protocols. Add OpenClaw and Hermes installation targets, retain complete references, verify conflict handling, document the evidence boundary, and run portable-install CI on Windows and Linux.

## Evidence and limits

The recovered branch contains a portable installer, dependency manifest, and file-based orchestration tests. The casebook reports earlier long-form work, including approximately 80–90k words and 25 chapters for The Source Code. Those historical notes are not a newly reproduced benchmark and do not prove this exact commit is the strongest literary version.

The later standalone campaign repeatedly edited chapter one without producing an accepted chapter in its saved evidence. That supports revisiting the product architecture; it is not a controlled quality comparison across versions.

No automatic conversion of standalone-app project state is claimed. Keep those projects intact and inspect them before importing into the native skill workflow. Former app releases and commits remain available for recovery.
