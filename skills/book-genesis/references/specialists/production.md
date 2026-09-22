# Production

Turns the locked manuscript into clean deliverables: a technical proofread for spelling, grammar and consistency, ebook and print formatting, and an EPUB and PDF export when the author's machine has pandoc.

When to load: Phase 7: Editorial Package (orchestrator, as the production specialist), after Phase 6: Final Score, once the manuscript text is locked.

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
- Apply the "apply" lines as literal replacements through the same file flow as a revision (`references/specialists/revision-editor.md`): copy the accepted chapter to `work/revisions/chapter-NN.pre-rK.md`, write the corrected text to `work/attempts/chapter-NN/revision-rK.md`, read it back, confirm that only the logged text changed, then copy it to `manuscript/chapters/chapter-NN.md`.
- After the corrections, repeat pass 3 on the changed chapters.

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

### Detect, never install

Run, do not guess:

1. `pandoc --version`. Exit code 0 means pandoc is usable.
2. A PDF engine: the first of `xelatex`, `lualatex`, `tectonic`, `typst`, `weasyprint`, `pdflatex` whose `--version` exits 0. A program that is on the PATH but fails `--version` does not count; broken installations do exactly this. pdflatex, pandoc's default engine, comes last because it handles fewer Unicode characters.

Never install pandoc, a PDF engine or anything else without asking the author. If something is missing, say what, and write `delivery/EXPORT.md` so the author can finish later.

### Prepare (always, even without pandoc)

1. **Chapter files.** Each starts with exactly one level-1 heading (`# ...`) and holds only prose: pandoc starts a new chapter, and a contents entry, at every `#` line. If a heading is missing or at another level, correct it as a formatting fix through the same file flow as the proofread corrections, rather than working around it in the command.
2. **The proofread manuscript.** Write `delivery/<slug>.md`: the title and author on top, then every chapter file in order, separated by blank lines. Reading and joining the files needs no tool.
3. **Metadata.** Write `work/export/metadata.yaml`, saved as UTF-8 like the chapter files. The title comes from `project.title` in `PROJECT_STATE.yaml`; the language tag is the BCP 47 form of `project.language` (Portuguese (Brazil) is `pt-BR`, English (US) is `en-US`); the author's name is the one the author wants printed. If neither `artifacts/00-brief.md` nor `ASSUMPTIONS.md` records it, ask, and wait for the answer before exporting; never invent a name.

```yaml
title: "A Casa das Marés"
author: "Author Name"
lang: pt-BR
# Optional lines:
# subtitle: "..."
# rights: "Copyright 2026 Author Name. All rights reserved."   # printed on the title page
# belongs-to-collection: "Series Name"                          # EPUB series metadata
# group-position: 2                                             # volume number
```

pandoc uses `lang` for the EPUB's language and for hyphenation in the PDF.

4. **Stylesheet.** Write `work/export/ebook.css`. pandoc's own EPUB stylesheet spaces paragraphs apart with no indent, and `--css` replaces that stylesheet entirely, so this file is complete on its own:

```css
p { margin: 0; text-indent: 1.25em; widows: 2; orphans: 2; }
h1 { margin: 3em 0 2em 0; text-indent: 0; page-break-before: always; }
h1 + p, hr + p { text-indent: 0; }
hr { width: 30%; margin: 1.5em auto; border: 0; border-top: 1px solid; }
.titlepage { text-align: center; margin-top: 30%; }
.titlepage p { text-indent: 0; margin-top: 1em; }
nav#toc ol { list-style-type: none; padding: 0; margin-left: 1em; }
```

pandoc turns a `* * *` line into a scene break (`<hr />`), which the `hr` rules center.

5. **File name.** `<slug>` is `project.id` from `PROJECT_STATE.yaml` when it is set, or else the title in lowercase ASCII letters, digits and hyphens: "A Casa das Marés" becomes `a-casa-das-mares`.

### Run (only when pandoc works)

List every chapter file explicitly, in order. PowerShell and cmd do not expand wildcards, and pandoc then fails (pandoc 3.9 reports `withBinaryFile: invalid argument`). In a POSIX shell (macOS, Linux, Git Bash, WSL), `manuscript/chapters/chapter-??.md` expands in the right order because chapter numbers have two digits.

EPUB:

```bash
pandoc --metadata-file=work/export/metadata.yaml --css=work/export/ebook.css --toc -o delivery/<slug>.epub manuscript/chapters/chapter-01.md manuscript/chapters/chapter-02.md
```

- `--toc` adds a visible contents page right after the title page; the EPUB's navigation contents are generated either way.
- Add `--epub-cover-image=<file>` only when the author supplied a cover image.
- A dedication or an about-the-author page is a short file in `work/export/` (for example `# Dedication {.unlisted}` followed by one line), listed before or after the chapters in the command. `{.unlisted}` keeps it out of the contents.

PDF, only with a working engine:

```bash
pandoc --metadata-file=work/export/metadata.yaml --toc --pdf-engine=<engine> -o delivery/<slug>.pdf manuscript/chapters/chapter-01.md manuscript/chapters/chapter-02.md
```

- With a LaTeX engine (xelatex, lualatex, tectonic, pdflatex), a trade-size proof adds `-V documentclass=book -V "geometry:paperwidth=6in,paperheight=9in,inner=1in,outer=0.75in,top=0.75in,bottom=0.875in"`. Each chapter then opens on a right-hand page.
- This PDF is a reading and proof copy. A printer that requires PDF/X, a CMYK cover or bleed needs a layout tool or the printer's own template.

When the author needs a Word file, pandoc alone makes one, no PDF engine required; each chapter heading becomes a Heading 1:

```bash
pandoc --metadata-file=work/export/metadata.yaml -o delivery/<slug>.docx manuscript/chapters/chapter-01.md manuscript/chapters/chapter-02.md
```

After each command: the exit code is 0, and the output file exists and is not empty. If a command fails, keep whatever succeeded, copy the first line of the error into `delivery/EXPORT.md`, and never report a file that does not exist.

### delivery/EXPORT.md (always)

Write it on every run, so the author can repeat the export after any later correction:

```markdown
# Export: <title>
Author: <author>. Language: <lang>. Chapters: chapter-01.md to chapter-NN.md (NN files).

## Status
- pandoc: <version>, or not found
- PDF engine: <engine>, or none working (checked: xelatex, lualatex, tectonic, typst, weasyprint, pdflatex)
- delivery/<slug>.md: the proofread manuscript
- delivery/<slug>.epub: created, or not created (reason)
- delivery/<slug>.pdf: created, or not created (reason)
- delivery/<slug>.docx: created on request, or not requested

## Commands (run from the book folder)
<the exact EPUB command, every chapter listed>
<the exact PDF command, every chapter listed>
<the exact DOCX command, if the author asked for a Word file>

## If you choose to install what is missing
- pandoc: https://pandoc.org/installing.html
- a PDF engine: a TeX distribution (TeX Live, MiKTeX or MacTeX) provides xelatex and lualatex

## Before you publish
<the ebook and print checklist items still open>
```

Summarize the chosen platform, trim size and file status in the formatting notes of `artifacts/12-editorial-package.md`, and list in `RUN_REPORT.md` only the files that exist, read back from disk.
