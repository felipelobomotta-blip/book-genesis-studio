# Research specialist

Builds the per-book market map, comp set and sentence rhythm evidence in the book's own language and market, with every market claim sourced or labelled as a hypothesis.

When to load: Phase 0: Intake (orchestrator, or a subagent it delegates research to) to write artifacts/01-market-map.md; Phase 1: Foundation (orchestrator) only to fill gaps in the rhythm evidence behind artifacts/05-voice.md; Phase 3: Drafting (orchestrator) when a non-fiction chapter needs an evidence package; Phase 7: Editorial Package (orchestrator) to refresh comps for artifacts/13-positioning.md.

Credit: language-aware research contributed by Thinh Hoang, PR #14.

## Rules

1. **Source or hypothesis.** Every market claim (list position, prize, review count, trend, length norm, audience) carries a URL and the date it was checked. Anything else is labelled `unverified hypothesis`.
2. **Offline rule.** When browsing is unavailable or not permitted, comps are provisional hypotheses (label each one `provisional hypothesis`), the market gate stays unverified, and the research status reads `offline`. Never present recall as verified market data: no sales figures, ranks, review counts or "rising demand" from memory. Creative work continues; the orchestrator records the unverified gate in PROJECT_STATE.yaml and the pending checks in RUN_REPORT.md.
3. **No prose rules from labels.** Never infer a prose rule (rhythm, sentence length, register, paragraphing, dialogue share, readability) from a genre label ("thrillers are punchy") or a language label ("prose in [language] runs long"). Every such recommendation cites a named comp title AND a location or passage in it: a chapter and page range with the edition, or a position such as "first 300 words of chapter 3". A recommendation missing either is deleted, not softened. A rhythm inferred from a label is a documented failure: it cascades into the voice spec and produces choppy prose.
4. **The book's market, in the book's language.** Research the market where the book will be sold, in the language it is written in.
5. **Describe, measure, locate; never copy.** Quote at most a ten-word fragment to mark a location. Never paste pages of a comp into the project.
6. **Position, not promise.** The market map says where the book can sit. It never forecasts sales or bestseller status.
7. **Evidence only.** Research never writes manuscript prose.

## Step 1: Language, origin, segment

From the idea, artifacts/00-brief.md and ASSUMPTIONS.md, determine:

- **Writing language:** the language of the prose.
- **Market:** the country or region, and the retail channels, where the book will sell.
- **Origin:** an original work; a translation (name the source and target languages); or an author writing in a second language.
- **Segment:** one of the three below.

Record every inferred value in ASSUMPTIONS.md, marked as inferred, with the words in the idea that suggested it.

| Segment | What it is | Where its evidence lives | Rhythm-evidence caution |
|---|---|---|---|
| Translated fiction | Foreign originals published in the book's language | translation prizes, imprints that specialize in translation, reviews that name the translator | The cadence is partly the translator's. Cite translator and edition; never mix measurements from the original with the translation. |
| Locally authored literary fiction | Written in the book's language for prizes, critics and book clubs | national literary prizes and shortlists, literary press, independent bookshop selections | Measure the local edition. |
| Locally authored commercial fiction | Written in the book's language for mass retail and genre readers | retail bestseller lists, genre communities, reader platforms | Measure the local edition. |

Treat the three as separate markets: they sit on different shelves, lists and prizes, and their readers expect different things. Build the comp set mostly from the book's own segment; a comp from another segment states why it belongs. Non-fiction and memoir split the same way (translated, locally authored).

## Step 2: Queries in the book's language

English-only templates such as "goodreads best [genre] [year]" research the wrong market for most books. Write every query in the book's language. For a translation, run the same intents in the source language (the original's reception) and in the target language (the market it will enter). Use English only when English is the book's language, or to check an English original's reception.

Run six intents for the market:

1. Current bestseller lists for the category.
2. Best-of lists and reader rankings from the last five years.
3. Prizes and shortlists for the category.
4. Locally authored titles and translated titles, searched separately.
5. Reader reviews of each candidate comp, positive and negative.
6. Samples and previews for rhythm evidence: publisher excerpts, retailer previews, the author's site.

Example phrasings. For other languages translate the intent, not the words, and check that a phrasing returns lists rather than ads.

| Intent | Portuguese (Brazil) | Vietnamese |
|---|---|---|
| Bestseller lists | `livros mais vendidos [gênero] [ano]` | `sách bán chạy [thể loại] [năm]` |
| Best-of lists | `melhores livros de [gênero] [ano]` | `sách [thể loại] hay nhất [năm]` |
| Prizes | `vencedores do prêmio [nome] [ano]` | `giải thưởng [tên giải] [năm]` |
| Locally authored | `autores nacionais de [gênero] [ano]` | `tiểu thuyết [thể loại] của tác giả Việt Nam` |
| Translated | `romances de [gênero] traduzidos [ano]` | `văn học dịch [thể loại] [năm]` |
| Reviews | `[título] resenha` | `đánh giá sách [tên sách]` |
| Samples | `[título] primeiro capítulo` | `[tên sách] đọc thử` |

Find the market's own signals (bestseller lists, dominant retailers, national prizes, reader communities) and record each with URL and date. Do not assume one country's platforms are another's main signal. Starting points to verify, not an endorsed list: in Brazil, the PublishNews bestseller list, the Prêmio Jabuti and the Skoob reader community; in Vietnam, the bestseller rankings of Fahasa and Tiki and the Vietnam Writers' Association award.

Log each query: intent, query text, where it ran, date, and whether it returned lists or noise.

## Step 3: Map the field

Collect 10-15 titles in the category from the last five years. For a translation, use the date it came out in this market and note the original's date. For each title record:

- title, author, year, original language, segment, translator if any, publisher or imprint;
- positioning angle, in one sentence;
- visibility evidence: a list position or prize with its date, or a review count on a named platform with its date. Review counts show visibility, not sales; never convert them into a sales estimate;
- reader sentiment: the most repeated praise and the most repeated complaint, from reviews in the market's language;
- source URL and checked date, or `unverified hypothesis`.

## Step 4: Extract patterns

Each observation names the titles it comes from ("seen in 5 of 12: A, B, C, D, E").

- **Common elements:** what the successful titles share.
- **Missing angles:** what no title addresses. This is the opportunity.
- **Reader frustrations:** what negative reviews ask for.
- **Format:** length range (each figure with its source, such as a publisher page count), chapter structure, POV, tense, dialogue share where measured.
- **Audience:** who reads these books, from reviews and publisher positioning.

**Pattern check.** The general patterns in references/patterns/index.md were measured mostly on English-language books (Archer and Jockers modelled New York Times bestsellers; Blatt counted English-language authors). For each numeric pattern applied to this book, record whether the comps confirm it, contradict it, or were not measured. For a book in another language or market, an unconfirmed pattern stays a hypothesis. Flesch-Kincaid and similar readability formulas are calibrated on English text: do not apply their grade targets to other languages; compare with the comps directly.

## Step 5: Choose comps

Pick 3-4 comp titles ("readers who loved X will love this"):

- mostly well-known titles, plus one or two recent titles whose traction you can cite;
- each comp names a different strength the project shares;
- most come from the book's segment, and every comp is labelled with its segment;
- at least one is read in the book's writing language (an original, or a translation into it), because rhythm anchors must be;
- a runaway phenomenon is never the only comp: it says little about where this book sits;
- a comp known only from recall stays a `provisional hypothesis` until verified.

## Step 6: Sentence rhythm evidence

This section of the market map is the evidence behind the Rhythm contract in artifacts/05-voice.md, defined in references/specialists/narrative-foundation.md. It records the default register and how it shifts under scene pressure, each anchored to a named comp title and a location in it.

Record at least three passages, read in the book's language:

- a **baseline** passage: narration with no one speaking and no special pressure;
- a passage near the **fastest** cadence the book will need (action, the break of dread);
- a passage near the **slowest** (grief, reflection, the build of dread).

```
Comp: [title], [author], [edition/year], [language]; translator: [name | n/a]
Location: [chapter or section; page range or position, e.g. "chapter 12, first 300 words"]
Access: [publisher sample | retailer preview | author-supplied copy | public-domain text | recall, unverified]
Scene pressure: [rest (baseline) | action | dread | grief | comedy | exposition]
Measured over about one page: unit [words | syllables | characters]; sentences [n];
  mean length [n]; shortest [n]; longest [n];
  short sentences (under half the mean) [n]; long sentences (over twice the mean) [n];
  paragraph length [min-max] sentences
What the cadence does: [one or two lines, e.g. "long openings; each paragraph closes on a fragment"]
Marker: "[fragment of at most ten words]"
```

Measure by hand. Count sentences at terminal punctuation. Name the unit and keep it identical for comps and manuscript: words for languages that put spaces between words; syllables for Vietnamese, where spaces separate syllables; characters for Chinese and Japanese, which do not space words. For a translated comp, measure the translation this market reads, never the original.

If no passage can be found for an end, write `not found`; the voice spec cannot claim that end without an anchor. From recall, never invent page numbers: give the location only as precisely as you actually know it, mark it `recall, unverified`, and treat it as a provisional anchor.

## Step 7: Positioning

- **The gap:** one or two sentences on what this book does that the comps do not.
- **Target reader:** specific, never "everyone who likes X".
- **Reader job:** what reviews of the comps praise most. House taxonomy (a Book Genesis convention, not a market finding): empathy, fascination, self-insertion, intellectual stimulation, aspiration. Name the primary and secondary engines, with the review evidence; the orchestrator records the chosen engine in artifacts/02-story-engine.md.
- **Length:** compare the floor, sweet spot and ceiling in references/patterns/index.md with the comps' lengths (each figure cited) and report any mismatch. The orchestrator records the length contract in PROJECT_STATE.yaml.
- **Risks:** saturation, timing, audience size, each sourced or labelled `unverified hypothesis`.

## Step 8: Panel evidence

The panel cards live in the "Panel" section of artifacts/00-brief.md, in the format of references/roles/panel.md; the casual reader is fixed and not derived here. Research supplies what the other three are built from, each line pointing to the review or comp it came from:

- **Adjacent shelf:** the neighbouring category the adjacent-genre reader comes from, with two or three titles on it.
- **For the primary, hostile and adjacent-genre readers:** who they are; two or three recent reads from the field or the comps; what keeps them reading; what makes them quit. Take the last two from reviews in the market's language.
- **Hostile reader, also:** the objection they will raise first, and the clichés and tells they catch.

## Output: artifacts/01-market-map.md

```
# Market map: [working title]

## Research status
Browsing: [yes | no]. Market gate: [verified | unverified]. Checked: [date].
Writing language: [ ]. Market: [ ]. Origin: [original | translation from X | second-language author]. Segment: [ ].

## Queries run
| Intent | Query | Where | Date | Result |

## Field
| # | Title | Author | Year | Original language | Segment | Translator | Angle | Visibility evidence | Source + date |

## Patterns
Common elements. Missing angles. Reader frustrations. Format. Audience. (Each names its titles.)

## Pattern check (references/patterns/index.md)
| Pattern | Confirmed / contradicted / not measured | Evidence |

## Comps
1. [Title], [author], [year], [segment]: comp because [strength]. [Source + date | provisional hypothesis]

## Sentence rhythm evidence
[passage records from Step 6]

## Positioning
Gap. Target reader. Reader job. Length. Risks.

## Panel evidence (for the cards in artifacts/00-brief.md)
Adjacent shelf: [category]; titles [ ]. Primary. Hostile. Adjacent-genre.

## Sources
[URL, checked date] for every claim above
```

## Phase 7: Editorial Package revisit

- Re-check each comp: still inside the five-year window, still in print in this market, not displaced by a newer title.
- If Phase 0: Intake ran offline and browsing now exists, verify the hypotheses and ask the orchestrator to update the market gate. If still offline, artifacts/13-positioning.md repeats the labels.
- Supply, in the book's language, the shelf categories and search terms the comps are listed under (retailer pages, with date).
- Supply the refreshed comps and the category that the recommendation in artifacts/13-positioning.md cites; the hook test itself runs as references/roles/panel.md describes.
- Check that the recent reads on the panel cards still come from current comps.
- Hand all of this to artifacts/13-positioning.md and update the research status in artifacts/01-market-map.md.

## Non-fiction evidence packages (Phase 3: Drafting, on request)

When a non-fiction chapter needs data, build work/evidence-chapter-NN.md before the chapter is drafted.

Source hierarchy, strongest first:

1. official statistics (national statistics offices, census);
2. peer-reviewed research;
3. reports from public and intergovernmental institutions;
4. data journalism that publishes its method;
5. industry reports and surveys (check who paid for them);
6. expert blogs and publications.

For each claim record: the claim; the full citation (author, institution, publication, year); sample and method; the primary source's URL; freshness (under three years old, or searched for an update); counter-evidence.

Search with 3-5 queries per chapter thesis, in the book's language and in the language of the primary sources. Look for contradiction as hard as for support: none found makes the data stronger; some found gets flagged. Trace every figure to its primary source, not to someone citing it.

Red flags:

- a figure too clean ("95% of [group]...") with no sample or method;
- no method described;
- a single survey with fewer than 500 respondents;
- data from a company that sells the solution to the problem it measures;
- a figure found only on blogs, never at its source.

Quantify uncertainty ("a [year] [institution] study of [N] people found" beats "research suggests"), flag what you could not verify, and date everything.

```
# Evidence: chapter NN, [title]
Thesis: [the argument this chapter makes]
## Supporting
1. [Claim]. Source: [citation]. Sample/method: [ ]. Year: [ ]. URL: [ ]. Strength: [strong | moderate | weak]
## Contradicting
1. [Counter-claim]. Source: [ ]. Handling: [acknowledge | contextualize | rebut]
## Searched, not found
- [data that would strengthen the chapter but does not exist]
```

How data enters the prose is covered in references/specialists/prose-craft.md (non-fiction prose).
