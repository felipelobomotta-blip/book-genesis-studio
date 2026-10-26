# Native Plugins Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task. The user has authorized the shared-core plugin approach; execute in this chat.

**Goal:** Install Book Genesis as a native plugin in Codex and Claude, with an experimental DeepSeek provider, without a separate author-facing CLI.

**Architecture:** Existing self-contained skills remain canonical. Manifests expose the suite, a small provider integrates DeepSeek, and a standard-library builder produces clean distributable archives.

**Tech Stack:** Python 3.10+, JSON, Markdown, Node ESM for DeepSeek.

**Spec:** `docs/superpowers/specs/2026-10-23-native-plugins-design.md`

## Global constraints

English product copy; no model calls, API keys, hooks or servers during installation; preserve uncommitted work and checkpoints; no unsupported >90 or bestseller claims.

## Review focus

- Plugin cache paths with spaces must resolve all skill references and scripts.
- Local manuscript/session files must not leak into release archives.
- An existing controlled checkpoint must not become a second host-owned writing run.
- DSH candidate metadata must not enable arbitrary filesystem reads.
- A completed package must not be described as a successful model-driven book test.

## Tasks

- [x] Add Codex/portable and Claude manifests, catalogs and English onboarding instructions, referring to canonical skill resources.
- [x] Add `runner/plugin_bundle.py` with `build_bundle(destination, repo_root)` and read-only `verify_bundle(root)`; add regression tests for allowlists, hashes, paths and overwrite protection.
- [x] Add the DeepSeek ESM provider and contract tests for all four skills, bodies/resources, invalid names and disposal ownership.
- [x] Build artifacts; validate with native tools; install in the user's actual Codex profile as explicitly requested; run extracted helper and real child-process smoke checks and suite verification. Claude installation is not claimed.
- [x] Update README and `docs/plugins.md` with accurate install paths, observed tests, distribution status and release limitations; wire archive creation into CI.
- [x] Add a packaged autonomous preparation bridge reusing the existing engine; freeze verified skills and contract, bound network preflight before book budgets, preserve resume.
- [ ] Complete the fresh native Codex book acceptance test. Two startup failures and one input-contaminated attempt are recorded and retained in the denominator. Beta 4 produced 24 chapters but failed revision verification; beta 5 repaired that request and then stopped at chapter 23 on a one-word length excess. Beta 6 repairs near-boundary drafts and batches growing issue histories. Installation success does not establish book quality.
- [x] Read the repository test result: beta 5 passed the complete 631-test suite in 921.184 seconds after updating two stale wire-schema fixtures. Complete-book acceptance remains separate.

No commit is part of this task. Repository policy requires the full test suite before any later commit.
