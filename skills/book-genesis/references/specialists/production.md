# Production

Turns the locked manuscript into clean deliverables: a technical proofread for spelling, grammar and consistency, ebook and print formatting, and a default portable manuscript-plus-EPUB export. DOCX/PDF are optional when their libraries already exist; pandoc is an optional alternative, never a prerequisite.

When to load: Part 1 (technical proofread) at the Phase 5 exit, before Phase 6 freezes the final score; Parts 2 and 3 at Phase 7 after Phase 6, once the manuscript text is locked.

## Principle

When the text reaches production, the story is locked: nobody changes plot, character or structure. The job is zero technical errors and a professional presentation. Proofreading is not editing: you hunt errors, and you never rewrite a sentence because you would have phrased it differently. Anything that needs rewriting goes back to the orchestrator as a finding; it should have been caught in Phase 4: Adversarial Audit or Phase 5: Revision Loop.

Order: proofread, then format, then export. Never format text that still has errors, and format once, on the clean text. The cover is developed alongside the editorial package (`artifacts/12-editorial-package.md`).

Before formatting, read the planned platforms and formats (ebook, print or both) from `artifacts/13-positioning.md`, or ask the author. KDP, IngramSpark and Apple Books publish different specifications, and the platform's current specification overrides every number below.

## Part 1: technical proofread

### Eight error categories

1. **Spelling and accents**: misspellings, missing or wrong accents, hyphenation, a proper name spelled two ways. Pick one spelling standard and keep it (US or UK English; for Portuguese, the orthographic agreement in force).
2. **Punctuation**: missing commas, semicolon against period, dash conventions (em dash, en dash and hyphen: one convention per use, kept throughout; in Portuguese the dialogue dash is standard), ellipses always three dots or always the single ellipsis character, punctuation inside or outside quotation marks by the convention of the book's language.
3. **Agreement**: subject and verb, noun and adjective, pronoun consistency (in Portuguese, "você" mixed with "te" or "ti" without intent).
4. **Undue repetition**: the same word in nearby sentences, the same connector in consecutive sentences, repeated syntax. Deliberate repetition (anaphora, a voice effect) stays.
5. **Factual inconsistency**: names, facts, numbers, dates and chronology that disagree between mentions. `artifacts/09-continuity-ledger.md` is canon; see `references/specialists/continuity.md`.
6. **Verb tense**: unmotivated switches (in Portuguese, pretérito perfeito against imperfeito), a tense change mid-scene with no dramatic function.
7. **Internal formatting**: italics or quotation marks opened and never closed, inconsistent chapter-heading capitalization, mixed scene-break markers, stray blank space.
8. **Invisible errors**: typos that form a real word ("form" for "from"; in Portuguese, "cama" for "cana"), missing words ("she went the store"), homophones (their, there, they're; its, it's), double spaces, a space before punctuation, doubled blank lines, straight quotes mixed with curly ones, number style (three against 3), leftover placeholders ([TODO], [TK], [CHECK]).

### Three passes

1. **Read aloud, for flow.** The ear catches what the eye normalizes: sentences that trip the tongue, a word repeated within three sentences, rhythm breaks, missing words, homophones.
2. **Read backwards, for detail.** Paragraph by paragraph, starting from the last. Breaking the story's pull forces attention onto each sentence: spelling, accents, punctuation, agreement, tense, number style.
3. **Targeted search, for consistency.** One category at a time, never everything at once: character names, place names, timeline, physical details, terminology, heading style, scene breaks, dialogue punctuation.

Optional portable counts for pass 3, in a POSIX shell, on the author's chapter files:

```bash
grep -n "[^ ]  [^ ]" manuscript/chapters/chapter-*.md               # double spaces
grep -nE " [,.;:!?]" manuscript/chapters/chapter-*.md                # space before punctuation
grep -nE "TODO|\[TK\]|\[CHECK\]" manuscript/chapters/chapter-*.md    # placeholders
```

### Log and corrections

Log every error in `evaluations/proofread.md`, one line each. Paragraphs are counted from the first paragraph after the chapter heading, one per blank-line block:

```text
[Punctuation] | chapter-07, paragraph 12 | "text with the error" -> "correction" | apply
[Repetition]  | chapter-09, paragraph 3  | "possible style choice" -> "suggestion" | ask the author
```

- Anything that could be a style choice is marked "ask the author" and is never applied without an answer. Anything larger than a correction is a ticket, and the author decides.
- Complete this proofread before Phase 6 final scoring. Apply approved "apply" lines through the same staged revision flow (`references/specialists/revision-editor.md`): copy the accepted chapter to `work/revisions/chapter-NN.pre-rK.md`, write the corrected text to `work/attempts/chapter-NN/revision-rK.md`, read it back, confirm that only the logged text changed, and let the orchestrator promote it through the Phase 5 revision protocol. The Phase 7 production specialist never writes a correction directly into a locked canonical chapter after Phase 6.
- After the corrections, repeat pass 3 on the changed chapters.

If a new factual, continuity or prose defect is discovered after Phase 6, do
not patch `manuscript/chapters/` in Phase 7. Return the finding to the
orchestrator as a Phase 5 ticket, stage and promote it through the normal
revision evidence, rerun the affected reader/audit evidence, refresh Phase 6,
and only then export. There is no skip-votes path for a production edit.

## Part 2: formatting

### Ebook

Order of contents:

1. title page (title and author)
2. copyright page
3. dedication (optional)
4. epigraph (optional)
5. table of contents, generated, never typed by hand
6. the text
7. acknowledgments (optional)
8. about the author
9. also by the author (optional)

Typography:

- do not set a font; the reader chooses one on the device
- relative sizes in CSS for headings and body
- first-line indent of about 1.25em and no space between paragraphs (spaced paragraphs look like a blog, not a book)
- no indent on the first paragraph after a chapter heading or a scene break
- scene breaks centered, with space before and after

Metadata:

- title exactly as on the cover, plus the subtitle if any
- author
- description: the store description from `artifacts/12-editorial-package.md`
- categories: the most specific ones the platform allows
- keywords: phrases a reader would type into the store's search (KDP's form has seven keyword fields)
- language
- series name and volume number, if any (`references/specialists/series.md`)
- ISBN, optional for ebooks

Cover: KDP's guideline is 2,560 px tall by 1,600 px wide, RGB, high-quality JPEG. Confirm the current specification at upload.

Before upload, the author opens the EPUB in Kindle Previewer (free, from Amazon) or another reading app and checks the contents links, chapter breaks and scene breaks; EPUBCheck, the official EPUB validator, goes further if the author has it. Authors who build ebooks by hand often use Sigil (free) or Vellum (paid, Mac).

### Print on demand

- **Trim size.** 14 x 21 cm is widely used for adult fiction in Brazil; 5.5 x 8.5 in and 6 x 9 in are common US trade sizes, 6 x 9 in especially for nonfiction. Confirm the printer offers the size.
- **Margins**, as a starting point for 200 to 350 pages: outside 1.9 cm (0.75 in), top 1.9 cm, bottom 2.2 cm, inside 2.5 cm (1 in). The inside margin grows with thickness, roughly 3 mm (0.125 in) per extra 100 pages. The printer's published minimums override these.
- **Type.** A book serif (Garamond, Palatino, Baskerville, Caslon) at 10 to 11 pt; leading about 1.3 to 1.5 times the type size (for example, 11 pt type on 14 pt leading); chapter titles 16 to 24 pt, starting about a third of the way down the page; first-line indent 0.6 to 0.8 cm set as a paragraph style, never with tabs; justified text with automatic hyphenation.
- **Page furniture.** Running heads carry the book title and the author name on facing pages, and none appear on chapter-opening pages. Roman numerals for the front matter, arabic from chapter 1. Every chapter opens on a right-hand (odd) page. No page number on the title page, copyright page, chapter openers or blank pages. A half-title page, title page and copyright page up front.
- **Printer file.** PDF/X-1a or PDF/X-4, fonts embedded, images at 300 DPI or more, grayscale interior unless it is a color book, CMYK cover, 3 mm (0.125 in) bleed on anything that touches the edge. Spine width comes from the printer's calculator for the chosen paper and the final page count; KDP and IngramSpark both publish cover templates. The ISBN and barcode go on the back cover.

### Final checklist

Content

- [ ] all three proofread passes done and every "apply" correction made
- [ ] factual claims verified; names, places and timeline consistent with the ledger
- [ ] no placeholder text left ([TODO], [TK], [CHECK])

Legal

- [ ] every quotation attributed and every data source cited
- [ ] no copyrighted material used without permission, epigraphs and song lyrics included
- [ ] real people depicted with care; legal review if in doubt

Ebook

- [ ] contents links work; chapter and scene breaks render
- [ ] no spaced paragraphs; indents come from CSS, not from spaces
- [ ] metadata complete; the file opens in a previewer; the cover meets the platform's specification

Print

- [ ] trim, margins and inside margin fit the page count
- [ ] fonts embedded; bleed where needed; spine from the printer's calculator
- [ ] running heads and page numbers correct; ISBN barcode on the back cover

## Part 3: export

### Portable Book Genesis export helper

After the manuscript is locked and the Phase 4, Phase 5 and Phase 6 records are
complete, reconcile the outline and state to confirm that every planned chapter
exists. Do not export a contiguous subset as a finished book. Use
`scripts/export_book.py` from this skill as the default Phase 7 action; the host
should invoke it rather than asking the author to assemble files by hand:

```bash
python scripts/export_book.py \
  --book-dir <book-folder> \
  --delivery-dir <book-folder>/delivery \
  --title "<project title>" \
  --author "<author name>" \
  --language <BCP-47 language>
```

Add `--docx` and/or `--pdf` when the host already has `python-docx` and/or
`reportlab` plus `pypdf` available. The optional files are staged and validated
with the EPUB in the same transaction. DOCX uses a 5.5 x 8.5 inch serif reader
layout with chapter page breaks and page numbers; PDF uses an embedded
accessible serif font and is explicitly a reading proof, not print-certified.
If an optional dependency or usable font is missing, the helper fails clearly
without installing anything.

The helper reads `manuscript/chapters/chapter-NN.md` in numeric order and
refuses gaps, duplicate numbers, malformed chapter headings and a non-empty
delivery directory unless the host deliberately passes `--overwrite`. It
accepts only a simple slug and `book_dir/delivery` as the delivery target, and
re-reads the canonical chapter set immediately before and after promotion. It
holds the cooperative `.book-genesis-write.lock` in the chapter directory for the transaction; the chapter
promotion helper uses the same lock convention. This is a single-writer guard
for cooperating Book Genesis operations, not an impossible guarantee against a
separate process that ignores the lock. It stages all artifacts before
promotion, so a failed export leaves a previous delivery untouched. It writes
`delivery/manuscript.md`, a generated EPUB 3 with
navigation and a visible table of contents, optional DOCX/PDF reading proofs,
`delivery/export-receipt.json` with source/output hashes, chapter count and a
deterministic per-chapter/total word count, and `delivery/EXPORT.md` with the
validation result. The receipt's `word_count.method` is
`whitespace_split_prose_v1`: count every nonblank prose line by whitespace,
excluding level-one headings, frontmatter and standalone scene/formatting
separator lines. Use `word_count.total` and its chapter entries in the final
inventory; do not ask a model to estimate or recalculate it. This is a
deterministic reporting measure, not a mutable literary target or quality gate.

The receipt always records `quality.status: not_assessed` and
`quality.quality_gate_passed: false`. The helper is an assembler and format
validator; it never turns a score, panel verdict or package into a quality or
publication-readiness claim. The host must keep the gate and human decision
records separate, and must not call the helper until the author has supplied a
name for the title page. Never install a missing exporter dependency: the
manuscript and EPUB path uses only the Python standard library; DOCX and PDF
are opt-in and use only libraries already present on the host.

For the complete-book Phase 7 path, derive the approved chapter count and
prose floor/ceiling from the actual intake and approved outline contract, then
add these assertions before the final inventory:

```bash
python scripts/export_book.py \
  --book-dir <book-folder> \
  --delivery-dir <book-folder>/delivery \
  --title "<project title>" \
  --author "<author name>" \
  --language <BCP-47 language> \
  --require-complete-pipeline \
  --expected-chapters <approved chapter count> \
  --min-words <approved prose floor> \
  --max-words <approved prose ceiling>
```

`--require-complete-pipeline` checks that every canonical `artifacts/00` to
`artifacts/13` file, `ASSUMPTIONS.md`, `RUN_REPORT.md`, `PROJECT_STATE.yaml`,
`evaluations/panel-chapter-01.md`, `evaluations/proofread.md`,
`evaluations/revision-loop.md`, `evaluations/revision-plan.md`, and the
canonical chapter set exists and is
nonempty. It does not inspect whether a literary gate passed: an honest failed
audit or score is valid evidence. The optional count assertions compare the
deterministic `word_count` receipt measure and fail before staging any
delivery when the approved contract does not match. Standalone draft exports
remain available without this flag.

### Optional alternatives (never install)

The portable helper above is the mandatory default and must be attempted before
an alternative. Pandoc, PDF engines and LibreOffice may be used only when they
already exist and the author requests that format or the host has a documented
compatibility need. Verify the selected command and output; do not write a
second manuscript by hand. A missing optional tool affects only that optional
format: the standard-library manuscript and EPUB remain the default delivery.
If the default helper is blocked by a host, permission, quota or incomplete
source problem, preserve the checkpoint and write `delivery/DELIVERY_STATUS.md`
or `delivery/EXPORT.md` with `status: blocked`, the exact error and next action.

### delivery/EXPORT.md (always)

Write it on every run, so the author can repeat the export after any later correction:

```markdown
# Export: <title>
Author: <author>. Language: <lang>. Chapters: chapter-01.md to chapter-NN.md (NN files).

## Status
- portable helper: passed, or blocked (exact error)
- delivery/manuscript.md: created, or not created (reason)
- delivery/<slug>.epub: created, or not created (reason)
- delivery/export-receipt.json: created, or not created (reason)
- word count: `<receipt.word_count.total>` prose words; per-chapter counts are in the receipt
- optional DOCX/PDF: created only when requested and dependencies already existed, or not created (reason)
- quality gates: passed, gates not met, or not assessed; never infer publication approval

## Commands (run from the book folder)
<the exact portable helper command, including title, author and language>
<the exact optional command, if one was run>

## Before you publish
<the ebook and print checklist items still open>
```

Summarize the chosen platform, trim size and file status in the formatting notes of `artifacts/12-editorial-package.md`, and list in `RUN_REPORT.md` only the files that exist, read back from disk.
