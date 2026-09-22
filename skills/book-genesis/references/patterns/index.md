# Patterns library index

The single entry point to the measured patterns Book Genesis uses to plan, audit and revise a book: the length contract, the beat map, where every pattern lives and how each role uses it.

When to load: Phase 0: Intake and Phase 1: Foundation (orchestrator, research); Phase 1: Foundation through Phase 3: Drafting (writer); Phase 4: Adversarial Audit and Phase 6: Final Score (auditor); Phase 7: Editorial Package (orchestrator, for Packaging signals).

## Read first: these numbers measure craft risk

Every threshold in this library measures craft risk: the chance that a demanding reader, editor or agent stops trusting the book. None of them predicts sales. No count or score built on this library may be reported as a sales forecast, a bestseller claim or a promise of virality.

The project's own record shows why. An earlier Book Genesis benchmark scored E.L. James's Fifty Shades of Grey, one of the best-selling novels of the 2010s, at a craft floor of 6.0, below books in the same benchmark that sold far less. Ben Blatt's counts in references/patterns/prose.md point the same way: the author at the top of his -ly adverb chart (E.L. James) and the most cliché-heavy of his 50 authors (James Patterson) are both among the best-selling writers he measured. A book can fail these checks and sell, or pass all of them and not sell.

Two claims from the retired knowledge files are withdrawn on the same grounds:

- "7.5 prose with 9.0 pacing outsells 9.0 prose with 7.5 pacing by 10x" had no source. No study used here measures a trade-off between prose and pacing; the rubric scores them separately.
- The sales figure given for The Silent Patient was wrong by about ten times. This library carries no sales figures.

Use the patterns to decide what to fix. The aim stays a goal: a complete book written with measured patterns, audited the way a demanding editor would audit it, and packaged to sell.

## Genre length contract

At Phase 0: Intake the orchestrator copies one row into PROJECT_STATE.yaml: the floor into `target_floor_words`, the ceiling into `target_ceiling_words`, and floor to ceiling into `target_range_words`. The contract must be settled before Phase 2: Architecture. The floor is a hard gate: a manuscript below it cannot be called complete, final-scored as ready or packaged for launch unless intake positioned it as a novella, short novel or serial installment. Reedsy gives 40,000 words as the usual threshold for a novel.

| Genre | Floor | Sweet spot | Ceiling |
|---|---:|---:|---:|
| Literary fiction | 80,000 | 90,000 | 100,000 |
| Women's fiction | 75,000 | 87,500 | 100,000 |
| Historical fiction | 90,000 | 105,000 | 120,000 |
| Mystery | 80,000 | 85,000 | 90,000 |
| Cozy mystery | 60,000 | 65,000 | 70,000 |
| Thriller (espionage may run longer) | 80,000 | 85,000 | 90,000 |
| Noir | 70,000 | 80,000 | 90,000 |
| Romance, mainstream | 70,000 | 80,000 | 90,000 |
| Romance, category | 50,000 | 62,500 | 75,000 |
| Romantasy | 90,000 | 95,000 | 100,000 |
| Science fiction | 90,000 | 100,000 | 110,000 |
| Fantasy | 90,000 | 105,000 | 120,000 |
| Horror* | 70,000 | 85,000 | 100,000 |
| Young adult | 50,000 | 65,000 | 80,000 |
| Young adult fantasy | 65,000 | 77,500 | 90,000 |
| Memoir and biography | 65,000 | 77,500 | 90,000 |
| Narrative nonfiction | 70,000 | 85,000 | 100,000 |
| True crime | 70,000 | 85,000 | 100,000 |
| Prescriptive nonfiction* | 50,000 | 65,000 | 80,000 |

Sources. Floors and ceilings: Dana Isaacson, "Publishers Want Shorter Books! An Updated Genre Word-Count Guide", Career Authors, updated 25 May 2026, written with input from literary agent Paula Munier. Rows marked * come from Reedsy, "How Many Words in a Novel?" (updated for 2026), because the Career Authors guide does not list them. The sweet spot is the midpoint of the range: a project default the outline plans against, not a measured average.

Notes:

- Literary fiction, resolved. The old table paired a sweet spot of about 98,000 with a range of 80,000-95,000 because it mixed two populations. The 98,000 figure is Kindlepreneur's average for Amazon's top-100 literary fiction sellers (updated July 2026; the same analysis gives 91,000 for mystery, thriller and suspense), a pool that includes established and self-published authors. The 80,000-95,000 band is an agent's stated preference for a literary debut, reported by the Manuscript Academy (June 2026). This table follows agent guidance, and its 90,000 sweet spot sits inside both the full range and the debut band.
- Near the ceiling. The Career Authors guide warns that any manuscript over 100,000 words makes publishers nervous. A debut planned above 100,000 needs a stated reason in artifacts/07-outline.md.
- Other languages and markets. These ranges are US agent guidance for books in English. For another language or market, research sets floor and ceiling from named comps in that language (see "How agents use this"); until it does, the English row applies. The casebook's Vicente case (Brazilian spiritist fiction, 51,945 words) is shorter than every adult fiction floor in this table, so a length like that passes the gate only on named Brazilian comps or a short-novel positioning recorded at intake.

## Beat map

Jessica Brody's Save the Cat! Writes a Novel (Ten Speed Press, 2018) adapts Blake Snyder's screenplay beats to novels as percentages of length and presents them as a guide. Word position = offset x manuscript words. Shown for a 90,000-word book, the literary fiction sweet spot:

| Beat | Offset | Words at 90,000 |
|---|---|---|
| Opening Image | 0-1% | 0-900 |
| Theme Stated | 5% | 4,500 |
| Setup | 1-10% | 900-9,000 |
| Catalyst | 10% | 9,000 |
| Debate | 10-20% | 9,000-18,000 |
| Break Into 2 | 20% | 18,000 |
| B Story | 22% | 19,800 |
| Fun and Games | 20-50% | 18,000-45,000 |
| Midpoint | 50% | 45,000 |
| Bad Guys Close In | 50-75% | 45,000-67,500 |
| All Is Lost | 75% | 67,500 |
| Dark Night of the Soul | 75-80% | 67,500-72,000 |
| Break Into 3 | 80% | 72,000 |
| Finale | 80-99% | 72,000-89,100 |
| Final Image | 99-100% | 89,100-90,000 |

The checks for each beat, with the default placement tolerance, are in references/patterns/structure-and-emotion.md, section 3. At audit, compute positions from the manuscript's actual word count, not the planned one.

## Where each family lives

| File | What it holds | Main readers |
|---|---|---|
| references/patterns/index.md | length contract, beat map, packaging signals, source homes, usage rules | orchestrator, research, writer, auditor |
| references/patterns/prose.md | sentence length, paragraph variation, adverbs, exclamation marks, dialogue share and tags, familiar phrases, Leonard's rules | writer (for artifacts/05-voice.md), blind reader, auditor, revision editor |
| references/patterns/structure-and-emotion.md | emotional arcs, The Bestseller Code, beats as checks, scenes, tension, curiosity, transportation, chapters and endings, sharing | writer, auditor, revision editor |
| references/patterns/ai-tells-en.md | twelve tells of machine-sounding prose in English, with counts, default ceilings and repairs | blind reader, auditor, revision editor |
| references/patterns/ai-tells-pt-br.md | the same twelve for Brazilian Portuguese, with the travessão rule and the Vicente worked example | blind reader, auditor, revision editor |

## Source homes

Each source is summarized in exactly one file. Other files point to that file instead of restating it.

| Source | Home |
|---|---|
| Blatt, Nabokov's Favorite Word Is Mauve (2017); Leonard, New York Times (2001); Liberman, Language Log (2017); Authors A.I. (2024); Readable (2020) | references/patterns/prose.md |
| Reagan et al., EPJ Data Science (2016); Archer and Jockers, The Bestseller Code (2016); Coyne, The Story Grid (2015); Swain, Techniques of the Selling Writer; Zak, Cerebrum (2015); Maass, The Fire in Fiction (2009); Loewenstein, Psychological Bulletin (1994); Green and Brock, JPSP (2000); Jericho Writers (2020); Romance Writers of America; Berger (2011); Berger and Milkman (2012) | references/patterns/structure-and-emotion.md |
| Brody (2018) beat offsets (the checks built on her beat definitions are in references/patterns/structure-and-emotion.md, section 3); Career Authors, Reedsy, Manuscript Academy and Kindlepreneur on length; Penguin Random House and Jane Friedman's site on comps | references/patterns/index.md |
| Wikipedia: Signs of AI writing (inspiration only) | references/patterns/ai-tells-en.md and references/patterns/ai-tells-pt-br.md |

## Packaging signals

The former commercial-patterns file is retired. Its conversion, review, email-list, BookTok and price statistics came from blogs and vendor pages, and its two price tables contradicted each other. Only these items had a checkable source or a named example:

- Comps. Penguin Random House Author News ("Comp Titles: An Elevator Pitch for Your Book", 2015): comps published within the last two or three years are ideal; match genre, audience and format; pick books with a typical sales path that are on booksellers' radar or on category bestseller lists, and avoid phenomena. Jane Friedman's site (Star Wuerdemann, "How to Find Compelling Comps for Your Book", 2021, updated 2025): go back as far as ten years only when an older comp is paired with a recent one, and treat a ubiquitous book, or one already adapted as a film, as too big to comp. Research applies these rules when it names comps in artifacts/01-market-map.md, and only comps that meet them may override a default in this library.
- Subtitles. Memoir and nonfiction often use the subtitle to state the genre or the promise, as in Tara Westover's Educated: A Memoir. This is a convention with a named example; there is no statistic behind it. Record the choice in artifacts/13-positioning.md.
- Title length. The widely repeated "85% of bestsellers have titles of one to six syllables" traces to a blog post with no dataset and is not used. Project check instead, recorded in artifacts/13-positioning.md: the title can be said aloud in conversation and typed from memory after one hearing.
- Thumbnail. Project check: the cover brief in artifacts/12-editorial-package.md states that the title and the focal image stay legible at thumbnail size. The click-through figures once attached to this check came from vendor blogs and are not used.

## How agents use this

- Orchestrator. At Phase 0: Intake, copies the genre row (or research's override) into PROJECT_STATE.yaml and plans the chapter count from the sweet spot. It decides which files each role receives, as listed below, and never hands the blind reader the beat map, the outline or any target. At Phase 7: Editorial Package, it applies Packaging signals to artifacts/12-editorial-package.md and artifacts/13-positioning.md.
- Research (references/specialists/research.md). May override a genre default in this library (length range, dialogue share, chapter length, a beat offset) only with a named comp: title, author, year, publisher or market, the value, and how it was measured. Comps follow the rules in Packaging signals and come from the book's language and market. Record the override in PROJECT_STATE.yaml and the evidence in ASSUMPTIONS.md. Without a named comp, the default stands.
- Writer. Reads this index and references/patterns/structure-and-emotion.md in Phase 1: Foundation, Phase 2: Architecture and Phase 3: Drafting, and references/patterns/prose.md while writing artifacts/05-voice.md. The writer may open the tells file for the book's language in Phase 1 only to record voice exemptions in artifacts/05-voice.md. It is not a drafting checklist, and no counts run during drafting.
- Blind reader (references/roles/blind-reader.md). Receives references/patterns/prose.md and the tells file for the book's language (references/patterns/ai-tells-en.md or references/patterns/ai-tells-pt-br.md), plus the prose under review. Nothing else from this library.
- Auditor (references/roles/auditor.md). Receives all five files in Phase 4: Adversarial Audit, runs the structure checks on the full manuscript and the counts on every chapter, and writes findings to artifacts/10-adversarial-audit.md.
- Revision editor (references/specialists/revision-editor.md). In Phase 5: Revision Loop, works the auditor's tickets with the repair moves in references/patterns/prose.md and the tells file, and recounts after each pass.
- Reader panel (references/roles/panel.md). Reads as readers; this library is not part of its brief.
- Final score (references/scoring/genesis-score.md). Counts are evidence for dimension scores, never the score itself, and the caveat at the top of this file governs every reported number.
- Other languages. Only English and Brazilian Portuguese have a tells file. For another language, adapt references/patterns/ai-tells-en.md with a native reader's review and record the adaptation in ASSUMPTIONS.md.
- Author overrides. Every numeric ceiling in this library is a project default. The author may change any of them; record the new value and the reason in ASSUMPTIONS.md.
