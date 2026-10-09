# Review a continuity error without rewriting the draft

Nora sends someone to fetch a hidden key at 8:40. She first learns where it is at 9:00. Can a reviewer catch that and leave the author's words alone?

This small Book Genesis example contains three synthetic excerpts and a second, consistent version. It exercises the continuity specialist and read-only auditor. It does not run the whole book pipeline.

## Try it with your agent

Install Book Genesis using the [main instructions](../../README.md#install), then open this example folder in a new session of your agent. Paste [prompt.txt](prompt.txt). The agent should save its own report as `review-a.md` without changing the sample. Your host's model usage and account limits still apply.

For a second check, start another fresh session and replace `sample-a.md` with `sample-b.md` and `review-a.md` with `review-b.md` in the prompt. Keep the recordings and this explanation out of each reviewer's context. Different models may return different findings.

To try your own chapter, replace the sample path in the prompt. Include earlier chapters needed to establish who knows what. The reviewer should state what it could not verify when context is missing.

## What happened in the recorded check

Two fresh-context Codex subagents reviewed one version each on 8 October 2026, using Book Genesis's auditor and continuity references. They did not receive the other version, expected answers or earlier feedback.

| Case | On-page knowledge path | Recorded result |
|---|---|---|
| [Sample A](sample-a.md) | Nora is absent at 8:20, uses the secret at 8:40, learns it at 9:00 | One high-severity continuity finding |
| [Sample B](sample-b.md) | Nora hears it at 8:20, uses it at 8:40, confirms it at 9:00 | No supported contradiction |

The sample A reviewer quoted both the premature instruction and the later first reveal. It suggested changing the premature instruction, without writing or applying replacement prose. Both source files had identical SHA-256 hashes before and after the reviews.

Read the unedited reviewer outputs: [A](recorded/review-a.json), [B](recorded/review-b.json). The [run record](recorded/run.json) describes execution and file checks.

## Check the saved evidence

From the repository root:

```bash
python examples/continuity-review/verify_recording.py
```

This checks the saved sample contents, before/after hashes and every quote against its chapter and paragraph. It makes no model call and does not generate a fresh review. Text hashes are normalized for Windows and Unix line endings when checking the checkout.

## What this example establishes

The recorded reviewers found the planted knowledge error and accepted the consistent control, while leaving both samples unchanged. This is one small demonstration with one review per case, in one model family. It is not an accuracy benchmark, a standalone CLI test, proof of full-book reliability, or a comparison showing that Book Genesis outperforms an ordinary prompt. Its usefulness to writers needs testing on real drafts.
