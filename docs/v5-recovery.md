# Book Genesis 5.1 recovery build

Unreleased local development build. The creative baseline is the official 5.0.0 core at commit `d1bf644660115f3e9b67e1a7ebb4c94052e0faf4`. The portable installer, native execution guard, isolated critics, staged revision and exporters are retained from the current reliability work. State schema 6 is retained for those helpers; it is independent of the product version.

This is a selective recovery of the 5.0 writing approach, not a reset that discards current source work. The original checkout and frozen comparison remain untouched.

## What the comparison supports

With authenticated native Codex `gpt-5.6-luna`, high reasoning, the same speculative-mystery seed and a 30,000–34,000-word novella contract:

| Version | Observed result | Limit |
|---|---|---|
| 5.0 | 12 chapters, 32,819 canonical prose words; 2h37m43s | No assembled manuscript or EPUB/DOCX/PDF delivery; own literary gate unmet |
| Current 6.0 beta with reliability changes | 12 chapters, 33,953 words; 2h09m58s; Markdown/EPUB/DOCX/PDF delivery | Own literary gate unmet; stale opening-panel provenance and pending delivery state found |
| Corrected 4.2-era workflow | One chapter, 2,759 words; checkpoint after 2h55m46s | Full book not delivered in this native Codex adaptation |

A common blind LLM jury favored 5.0's voice and emotional choices in this one pilot. Its median mean was 8.67 versus 8.00 for the current version, but current-version coverage was only two valid reads out of three and the individual ranges overlapped. These are simulated judgments, not human feedback or evidence that a book will sell. The pilot was a novella, not an 80,000-word novel. Original Claude/Opus performance was not tested here.

## What was missing in 5.0

- Consistent cause and effect: events, character knowledge, similar mechanism terms, costs and exceptions must agree across chapters.
- A middle that changes the situation rather than repeatedly explaining the system.
- Reliable delivery: the whole manuscript in reading formats, with source and output hashes.
- Evidence bound to the final text, truthful status and bounded failure recovery.

## Changes in this build

- Restore prose-first drafting and four creative checkpoints. Keep factual continuity checks after five-chapter blocks and the final block; avoid an extra mandatory literary panel at every continuity check.
- Give the writer a compact chapter packet. Keep scores, rubric, verdict history and production bookkeeping in orchestration rather than in the writing context.
- Add a small causal contract only for stories that need it, and review the decisive causal chain from the actual prose. Repair one or two supported blockers at a time while preserving remembered strengths.
- Verify original reader receipts against the current chapter hashes; changed text requires a new read, even when an old quote still matches.
- Omit hidden production comment blocks from reading formats and visible-prose counts while preserving canonical source bytes. Render section headings and ledger tables in EPUB, DOCX and PDF; verify DOCX table text in the complete chapter stream. The corrected count method is `whitespace_split_prose_v2`.
- Publish technical delivery status in the same transaction as exports, then verify files and reconcile saved status. Preserve unmet literary gates and human publication approval separately.

## Local validation

Use Python 3.10+ and an existing agent account. The installer never calls a model or requires an API key.

```bash
python runner/installer.py generate-agents
python runner/installer.py verify-suite
python -m unittest discover -s tests -v
python runner/installer.py install codex --dest /absolute/path/to/empty-book/.agents/skills
```

Open that book folder in the chosen agent and request `book-genesis`, including the intended form and word range. The installed pipeline must be used for any new generation test; exporting an old manuscript is a delivery regression, not evidence that the new writing prompts improve literary quality.

Before public readiness claims, repeat an idea-to-book run with the recovered build, validate all required current-text reads, verify export integrity and obtain independent human reading feedback. Longer novels and every supported agent remain separate acceptance work. No 9/10 or bestseller guarantee is claimed.
