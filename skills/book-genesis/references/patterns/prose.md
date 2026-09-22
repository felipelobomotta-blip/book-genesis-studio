# Prose patterns

Sentence-level measurements from published fiction, each tied to its source and named titles, turned into counts a chapter file can be checked against.

When to load: Phase 1: Foundation (writer, while setting artifacts/05-voice.md); Phase 4: Adversarial Audit (blind reader, auditor); Phase 5: Revision Loop (revision editor).

## How to read this file

- Evidence is either a measurement from a named study of named books or a rule stated by a named author. Default numbers are Book Genesis project defaults built on that evidence. The author may change any default; record the new value and the reason in ASSUMPTIONS.md.
- Counts run on one chapter file at a time (manuscript/chapters/chapter-NN.md). A count over a default sends the auditor back to reread the passage. On its own it is never a verdict.
- A decision recorded in artifacts/05-voice.md can exempt a pattern by name: a narrator who exclaims, a memoir voice built on long sentences.
- The sources measured English. Where Portuguese needs its own form, it is given here. For PT-BR books, the tells in references/patterns/ai-tells-pt-br.md also apply, including the rule that dialogue travessões are never counted as dashes.
- Commands are in "How to count" at the end. None of these numbers predicts sales (references/patterns/index.md).

## 1. Sentence length

Evidence:

- Ben Blatt ran every #1 New York Times bestseller from 1960 to 2014 through reading-level formulas (Nabokov's Favorite Word Is Mauve, Simon & Schuster, 2017). Average sentence length fell from 17 words in the 1960s to 12 in the 2000s, and the Flesch-Kincaid grade fell from about 8 to about 6. Of the 37 #1 bestsellers of 2014, 36 scored below grade 7.2. Blatt notes that most reading-level formulas weigh sentence length heavily.
- Readable's blog post on popular fiction and readability (Laura Kelly, 2020) scores To Kill a Mockingbird at grade 4.6, The Great Gatsby at 5.5 and Orwell's 1984 at 8.9, and cites the readability researcher George Klare for the finding that most popular novels are written at about a 7th-grade level.

Checks (defaults):

- P1. Mean sentence length in narration: flag a chapter above 20 words or below 8.
- P2. English only, and only if the host can compute it: flag a chapter above Flesch-Kincaid grade 8.0, the 1960s level. A literary voice may run higher by decision in artifacts/05-voice.md (1984 sits at 8.9). The formula is built for English; for Portuguese, use P1 alone.
- The spread of sentence lengths matters more than the mean. That check is tell 7 in the tells file for the book's language.

## 2. Paragraph variation

Evidence: Elmore Leonard's tenth rule is to leave out the parts readers skip, and he names the thick paragraph with too many words as the part they skip ("Easy on the Adverbs, Exclamation Points and Especially Hooptedoodle", New York Times, 16 July 2001). No study used here measures paragraph length in bestsellers, so these checks are defaults.

Checks (defaults):

- P3. Flag any narration paragraph over 200 words in which nothing happens: no action, no dialogue, no new information.
- P4. In any run of six consecutive paragraphs, the longest should be at least twice as long as the shortest. Flag runs of uniform blocks.
- P5. Flag a chapter whose narration has no paragraph under 20 words: the prose never changes gear.

## 3. Adverbs

Evidence:

- Blatt counted -ly adverbs per 10,000 words. He narrowed the count to -ly forms because rates for all adverbs barely separate authors. Results: Toni Morrison 76, Ernest Hemingway 80, Mark Twain 81, John Steinbeck 93, John Updike 102, Stephen King 105, Herman Melville 126, Jane Austen 128, Stephenie Meyer 134, J.K. Rowling 140, E.L. James 155. Within one author the most praised books tend to run lower: Steinbeck's The Grapes of Wrath measures 79.
- Morrison has said she never modifies a speech verb with "softly": the space around the line has to make it soft. Leonard's fourth rule forbids any adverb on "said".
- Austen and Rowling sit well above the ceiling below. The count flags a habit worth reviewing; it does not rank quality.

Checks (defaults):

- P6. -ly adverbs in narration: at most 105 per 10,000 words, Stephen King's rate (King is the best-known advocate of cutting them).
- P7. A speech verb carrying an adverb ("said softly", "asked quietly"; PT-BR "disse suavemente"): 0 per chapter.
- P8. Portuguese: count adverbs in -mente. No Portuguese measurement exists in this library, so the English ceiling of 105 per 10,000 words is the starting default. Look first at paired -mente adverbs ("lenta e cuidadosamente").

## 4. Exclamation marks

Evidence: Blatt, per 100,000 words across 50 authors and 580 books. The highest rates belong to James Joyce (1,105), Tom Wolfe (929), Sinclair Lewis (844), E.B. White (782) and J.R.R. Tolkien (767). The lowest is Elmore Leonard, 49 across 45 novels. Leonard's fifth rule allows two or three per 100,000 words of prose; nobody Blatt measured got that low, Leonard included. With Joyce and Tolkien at the top, this is a habit count that says nothing about quality.

Checks (defaults):

- P9. At most 1 per 1,000 words per chapter, about twice Leonard's measured practice.
- P10. Narration outside dialogue: flag every exclamation mark unless artifacts/05-voice.md declares an exclaiming narrator.

## 5. Dialogue share

Evidence:

- Authors A.I., the company behind the Marlowe manuscript-analysis tool, co-founded by The Bestseller Code co-author Matthew Jockers with the novelists Alessandra Torre and J.D. Lasica, states that a typical bestselling novel is 25% to 35% dialogue (Torre on the Alliance of Independent Authors podcast, 19 June 2024). Its reports add that the share varies by genre.
- Mark Liberman measured the share of text inside quotation marks ("Proportion of dialogue in novels", Language Log, 29 December 2017): Virginia Woolf's To the Lighthouse 3.3%, Hemingway's The Old Man and the Sea 15.0% and The Sun Also Rises 29.4%, Dan Brown's The Da Vinci Code 29.6%, Arthur Conan Doyle's The Adventures of Sherlock Holmes 47.0%, Bram Stoker's Dracula 47.5%, F. Scott Fitzgerald's The Great Gatsby 51.3%. Careers drift upward: Agatha Christie went from 49% (The Mysterious Affair at Styles, 1920) to 76% (Postern of Fate, 1973), Elmore Leonard from 34% (The Law at Randado, 1954) to 61% (Raylan, 2012). Liberman warns that errors in the texts can distort such counts.

Resolved conflict. The knowledge base carried both 25-35% and 30-50%, and the earlier evaluator used genre bands (30-50% for thrillers, among others). No source for the 30-50% band or the genre bands could be verified; the Language Log post cited for them contains none of those figures. One band remains, with its source.

Checks (defaults):

- P11. Manuscript dialogue share outside 25-35%: flag for comparison with the book's comps. It is a question for research before it is a defect. If the named comps run outside the band (a Christie-style mystery, a Woolf-style literary novel), research records a comp's measured share and that becomes the band.
- P12. Three or more consecutive chapters with no dialogue: flag, whatever the genre.

How to measure: in English, words inside quotation marks divided by all words. In Portuguese with travessões, words in paragraphs that open with a dash divided by all words; this includes the narrator's tags inside those paragraphs, a small overcount.

## 6. Dialogue tags and exchanges

Evidence: Leonard's third rule is to use only "said" to carry dialogue, because any other verb is the writer intruding on the character's line. His fourth forbids an adverb on "said".

Checks (defaults):

- P13. At least 80% of speech-verb tags are said or asked (PT-BR: disse, perguntou, respondeu, falou).
- P14. Where the speaker is clear from context, use no tag or an action beat.
- P15. Clean exchanges, a pattern from the pipeline's earlier scan: flag a dialogue scene in which every line answers the previous one completely and in order, with no interruption, non-answer, misreading or cross-talk.

## 7. Familiar phrases

Evidence: Blatt counted clichés per 100,000 words against Christine Ammer's The Dictionary of Clichés, about 4,000 entries. James Patterson scored 160, the highest of his 50 authors; Jane Austen scored 45; the lowest rates include Virginia Woolf, Veronica Roth and Khaled Hosseini. Five of the ten most clichéd books he found on Publishers Weekly bestseller lists since 2000 are Patterson's.

So a stock phrase does not stop a commercial reader turning pages, and the rubric still penalizes cliché. Both hold, because a familiar phrase is invisible in some positions and a tell in others.

Invisible, do not flag:

- in dialogue, where people really talk in stock phrases, and in a narrator whose entry in artifacts/05-voice.md is colloquial;
- in connective tissue: transitions, logistics, fast action read for event;
- when a character uses a stock phrase knowingly, mocks it or twists it.

A tell, flag:

- at a load-bearing position: the first or last paragraph of a chapter, the chapter's emotional peak, the first description of a main character or place;
- as the body's report of an emotion (a heart that skips, a chill down the spine); see tell 6 in the tells file;
- two or more in one paragraph;
- the same stock phrase more than once in the book.

Checks (defaults):

- P16. No stock phrase at a load-bearing position.
- P17. Flag clusters (two in one paragraph) and repeats across the book. No ceiling applies elsewhere.
- When the Prose dimension in references/scoring/genesis-score.md penalizes cliché, P16 and P17 are its test.

## 8. Leonard's rules as checks

Leonard's ten rules (New York Times, 2001), paraphrased, with the check each becomes. Blatt found bestsellers breaking them: nearly half of Danielle Steel's openings involve weather, while Morrison and Hemingway never open that way. The rules flag craft risk and say nothing about sales.

| Leonard's rule | Check (default) |
|---|---|
| 1. Don't open a book with weather, unless it is a character's reaction to it | Read the first paragraph of chapter 1 |
| 2. Avoid prologues | A prologue must justify itself in artifacts/07-outline.md |
| 3. Use only "said" to carry dialogue | P13 |
| 4. Never put an adverb on "said" | P7 |
| 5. Two or three exclamation points per 100,000 words | P9, P10 |
| 6. Never "suddenly" or "all hell broke loose" | 0 in narration; PT-BR "de repente", "subitamente", "repentinamente": at most 1 per chapter |
| 7. Use regional dialect sparingly | Phonetic spelling: a few markers per speaker, never every word |
| 8. Avoid detailed descriptions of characters | Flag a single block of physical description over 60 words |
| 9. Don't describe places and things in great detail | Flag a place description over 120 words with no action in it |
| 10. Leave out the parts readers skip | P3 |

His summary rule: if it sounds like writing, rewrite it.

## 9. Word choice

Archer and Jockers's style findings (everyday register, contractions, fewer qualifiers, adjectives and exclamation points) live with the rest of their study in references/patterns/structure-and-emotion.md, section 2.

## How to count

Conventions:

- One paragraph per line. If a chapter file is hard-wrapped, unwrap a copy first:
  `awk 'BEGIN{RS="";ORS="\n\n"}{gsub(/\n/," ");print}' manuscript/chapters/chapter-NN.md > work/chapter-NN.txt`
- Word counts replace dashes with spaces first, because `wc -w` counts a spaced dash as a word.
- English narration is the text outside quotation marks; Portuguese narration is every paragraph that does not open with a dash.
- The commands use standard POSIX tools (grep, sed, tr, awk, wc, sort, uniq). Where the host has no shell, run the same patterns with its search tool, or count by hand on the passages named.
- Candidate lists need reading: delete false hits before comparing a count with its default.

```sh
f=manuscript/chapters/chapter-NN.md

# Words
sed -E 's/—|–/ /g' "$f" | wc -w

# P1 mean sentence length, English narration paragraphs (no quotation marks)
sed -E 's/“|”/"/g' "$f" | grep -v '"' | grep -v -E '^\s*#|^\s*([-*_]\s*){3,}$' | tr '\n' ' ' \
  | sed -E 's/—|–/ /g; s/([.!?]) +/\1\n/g' | awk 'NF{n++; s+=NF} END{printf "%d sentences, mean %.1f words\n", n, s/n}'

# P1 mean sentence length, Portuguese narration paragraphs
grep -v -E '^\s*(—|–|-|#)' "$f" | tr '\n' ' ' \
  | sed -E 's/—|–/ /g; s/([.!?]) +/\1\n/g' | awk 'NF{n++; s+=NF} END{printf "%d sentences, mean %.1f words\n", n, s/n}'

# P3-P5 words per paragraph (line number: words)
awk 'NF{print NR": "NF}' "$f"

# P6 -ly adverb candidates in English narration
sed -E 's/“|”/"/g; s/"[^"]*"//g' "$f" | grep -o -i -E '\b[a-z]+ly\b' \
  | grep -v -i -E '^(only|early|family|reply|apply|supply|rely|ally|fly|july|italy|belly|jelly|holly|lily|bully|rally|silly|ugly|holy|lonely|lovely|friendly|likely|daily|weekly|monthly|yearly|elderly|curly|chilly|costly|deadly|lively|orderly|comply|imply|multiply|butterfly|anomaly|assembly|melancholy|monopoly|emily|sally|kelly|molly|billy|polly)$' \
  | sort | uniq -c | sort -rn

# P8 -mente candidates in Portuguese narration (prune somente, semente, demente...)
grep -v -E '^\s*(—|–|-)' "$f" | grep -o -i -E '\b[a-z]+mente\b' | sort | uniq -c | sort -rn

# P7 speech verb plus adverb
grep -o -i -E '\b(said|asked|replied|answered|whispered)\s+[a-z]+ly\b' "$f"
grep -o -i -E '\b(disse|perguntou|respondeu|falou|sussurrou)\s+[a-z]+mente\b' "$f"

# P9 exclamation marks, all; P10 narration only (English, then Portuguese)
grep -o '!' "$f" | wc -l
sed -E 's/“|”/"/g; s/"[^"]*"//g' "$f" | grep -o '!' | wc -l
grep -v -E '^\s*(—|–|-)' "$f" | grep -o '!' | wc -l

# P11 dialogue share, English (paragraphs that continue a quote without closing it are missed; add them by hand)
q=$(sed -E 's/“|”/"/g' "$f" | grep -o '"[^"]*"' | sed -E 's/—|–/ /g' | wc -w)
w=$(sed -E 's/—|–/ /g' "$f" | wc -w)
awk -v q="$q" -v w="$w" 'BEGIN{printf "dialogue %.0f%%\n", 100*q/w}'

# P11 dialogue share, Portuguese with travessões
d=$(grep -E '^\s*(—|–|-)' "$f" | sed -E 's/—|–/ /g' | wc -w)
w=$(sed -E 's/—|–/ /g' "$f" | wc -w)
awk -v d="$d" -v w="$w" 'BEGIN{printf "dialogue %.0f%%\n", 100*d/w}'

# P13 speech tags by verb (share = said + asked over the total; prune non-tag uses)
grep -o -i -E '\b(said|asked|whispered|murmured|shouted|yelled|hissed|snapped|exclaimed|replied|muttered|growled|breathed|sighed|demanded|insisted|admitted)\b' "$f" | sort | uniq -c | sort -rn
grep -o -i -E '\b(disse|perguntou|respondeu|falou|sussurrou|murmurou|gritou|exclamou|retrucou|rosnou|suspirou|sibilou|resmungou|insistiu|admitiu)\b' "$f" | sort | uniq -c | sort -rn

# Leonard 6
grep -o -i -E '\bsuddenly\b|all hell broke loose' "$f" | wc -l
grep -o -i -E 'de repente|subitamente|repentinamente' "$f" | wc -l
```

P16 and P17 have no portable word list: read the first and last paragraph of each chapter, the emotional peak and first descriptions, and mark stock phrases by hand.

## Claims not carried over

- "14-20 words per sentence", "about 1% of words over four syllables" and "sentences rarely exceed 25-30 words": no source; replaced by Blatt's measured means.
- 30-50% dialogue for commercial fiction and a "Cornwell, Kellerman, Cussler" sample at 43-59%: not in the Language Log post cited, and no other source found.
- "Under 200 exclamation marks per 100,000 words": no source; replaced by P9.
- Blatt's quiet, neutral and loud dialogue-tag bands; the ranking of first-sentence types from an analysis of 100 openings; the POV-by-genre table; the deep-POV trend; the sense-frequency table: not verified for this release.
- Chapter lengths for Gone Girl, The Hunger Games and Middlesex: not verified. Verified chapter lengths are in references/patterns/structure-and-emotion.md, section 8.
- The Silent Patient sales figure, wrong by about ten times, and every other sales figure.
