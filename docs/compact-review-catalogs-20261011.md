# Dense evidence catalogs and native context

A real 43,737-word book's coordinated revision check sent 247,152 tokens in
its packet alone. The 8,533 short paragraphs in the paired sources carried
111,971 prose tokens; repeated citation markup supplied most of the remainder.
The locally observed Codex Luna context window was 272,000 tokens. These are
one observed book and one local host configuration, not universal limits.

Dense source and anonymous-comparison catalogs now group consecutive short
paragraphs into evidence blocks of at most 320 whitespace-delimited words or
2,400 characters. An individually longer paragraph remains whole. Catalogs
with at most 128 paragraphs retain their existing representation. Headings stay
separate; blocks never cross them. Every block is an exact contiguous source
substring, and every nonempty paragraph occurs once in the original order.

Coordinated creative checks render these blocks as original multiline text
with source hashes, passage IDs and lengths. A deterministic length-delimited
decoder reconstructs the exact catalog. Text that resembles a source or
passage header cannot change the boundaries. This removes JSON line-break
escaping overhead without removing any source text. Saved catalogs and
structured report validation retain the same evidence binding.

This changes citation granularity, not manuscript prose, review coverage,
scores, independence calibration, revision authorization, or call budgets.
The complete sources and their original hashes remain bound to each catalog.
Exact-quote checks still operate on the assigned block. Changed uncited prose
still invalidates reuse. Older installed versions and books remain untouched.

Grouping does not establish any host's context capacity or literary quality.
Before a larger native test, measure its representative paired-book packets
and structured schema, reserve room for role output and host instructions,
and record the actual local model limit. Never truncate the book to fit or
silently substitute a different model or account. Full native delivery,
exports, completed resume, and literary acceptance remain separate checks.

The public autonomous Codex command can explicitly request a per-book capacity
with `--native-context-window`. It freezes that value in the original project
and native argv, along with a 95-percent auto-compaction threshold. Resume
reuses the same command. Native defaults stay unchanged when it is omitted;
global Codex configuration is never edited. The setting alone is not evidence
that the signed-in account accepts a larger request.

The official [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
documents `model_context_window` and `model_auto_compact_token_limit`. The
[Luna model page](https://developers.openai.com/api/docs/models/gpt-5.6-luna)
lists API capacity separately. A native subscription must pass a real larger
request before that capacity is used for a full-book acceptance experiment.
