# Structure and emotion patterns

Findings about story shape, rhythm and reader response from named studies, each turned into a check the writer can plan against and the auditor can verify on the full manuscript.

When to load: Phase 1: Foundation and Phase 2: Architecture (writer, for artifacts 03 to 08); Phase 3: Drafting post-block checks (writer); Phase 4: Adversarial Audit (auditor); Phase 5: Revision Loop for structural tickets (revision editor).

## How to use this file

- Each section gives the finding, its source, and numbered checks (SE1, SE2...) that tickets can cite. Tags say who applies a check: [plan] the writer, while writing the Phase 1 and Phase 2 artifacts; [block] the writer, in the post-block check of Phase 3; [audit] the auditor, on the whole manuscript in Phase 4, recording findings in artifacts/10-adversarial-audit.md; [blind] a blind reader, from the prose alone.
- Positions are percentages of the manuscript's word count. Convert them with the beat map in references/patterns/index.md.
- Numbers marked "default" are project defaults; the author may change them (record the change in ASSUMPTIONS.md). Unmarked numbers are measurements from the named source.
- These sources describe what past books share. None of them is a formula, and none predicts sales (references/patterns/index.md).

## 1. Emotional arcs (Reagan et al., 2016)

Finding. Andrew Reagan, Lewis Mitchell, Dilan Kiley, Christopher Danforth and Peter Dodds ("The emotional arcs of stories are dominated by six basic shapes", EPJ Data Science 5, 2016) scored the sentiment of 1,327 English works of fiction from Project Gutenberg (20,000 to 100,000 words, more than 40 downloads) in sliding windows of 10,000 words. Six core shapes emerged:

| Arc | Shape |
|---|---|
| Rags to riches | rise |
| Tragedy, or riches to rags | fall |
| Man in a hole | fall, then rise |
| Icarus | rise, then fall |
| Cinderella | rise, fall, rise |
| Oedipus | fall, rise, fall |

By download count, the three most successful arcs were Icarus, Oedipus and two Man in a hole arcs in sequence (fall, rise, fall, rise). The shapes that held the most books were not the most downloaded. The authors call downloads a rough proxy for success, and these are downloads of public-domain books, not sales of new ones.

Checks:

- SE1 [plan] artifacts/06-emotional-curve.md names the book's arc in these terms (one shape or a sequence of shapes) and plots the protagonist's fortune at each tenth of the book on a scale from -2 to +2.
- SE2 [plan] A single steady rise or fall needs a stated reason in artifacts/06-emotional-curve.md.
- SE3 [audit] Score each chapter's closing fortune on the same -2 to +2 scale from the manuscript and compare the drafted curve with the planned one. A shape that drifted (planned Man in a hole, drafted flat) is a structural finding.

## 2. The Bestseller Code (Archer and Jockers, 2016)

This is the single home for Jodie Archer and Matthew Jockers's findings in this library (The Bestseller Code, St. Martin's Press, 2016). By their account, a model trained on the text of about 5,000 novels, a little over 500 of them New York Times bestsellers, told the bestsellers from the rest with about 80% accuracy.

a) Topic focus. Bestselling authors give about 30% of a novel to one or two topics; less successful authors need three or more topics to fill the same share. About a third of John Grisham's paragraphs concern the legal system, and about a third of Danielle Steel's concern domestic life.

- SE4 [plan] artifacts/04-theme.md names the book's one or two dominant topics.
- SE5 [audit] Estimate the share of scenes whose main business is one of those topics. Default flag: below 30%.

b) Human closeness. The topic that best separated bestsellers was human closeness: people connecting in moments of shared intimacy, in any kind of relationship, romance included but not required (a shopping trip with a mother, cooking with a new partner). In Fifty Shades of Grey the model put human closeness at 21% of the text and intimate conversation at 13%, ahead of the sex scenes. Those two figures describe that one book. The old knowledge base turned them into a target for all bestsellers, which the source does not support.

- SE6 [plan] artifacts/07-outline.md marks at least one closeness scene (two people connecting without plot pressure) in every tenth of the book (default).
- SE7 [audit] Count closeness scenes per tenth. Default flag: any tenth with none.

c) Emotional rhythm. The authors report that the specific plot shape matters less than a regular beat of highs and lows, and they rank Fifty Shades of Grey and Dan Brown's The Da Vinci Code among the most regular books in their collection. Reviewing the book, Nick Richardson counted five emotional ups and five downs in Fifty Shades, spaced as regularly as a metronome, and found The Da Vinci Code's curve matching it until the very end (London Review of Books, 17 November 2016).

- SE8 [audit] On the SE3 plot, mark every major reversal: a swing of 2 or more points. Default flags: any stretch longer than 15% of the book without a reversal, and a longest gap between reversals more than twice the shortest.

d) Character verbs. Characters in bestsellers "need" and "want" about twice as often as characters in other novels, and "miss" and "love" about 1.5 times as often. Characters in the other novels "wish", "suppose" and "dislike" more. Bestselling protagonists act: they grab, think, ask, look and hold, where others murmur, protest and hesitate.

- SE9 [plan] artifacts/03-characters.md states the protagonist's want and need as active verbs.
- SE10 [audit] By the end of chapter 1, the protagonist has acted on a want the reader can name (default).

e) Style. Bestsellers sit closer to everyday speech. They are more likely to use contractions, question marks and words such as "do", "okay" and "thing" ("do" about twice as often), and less likely to use "very" (about half as often), exclamation points, strings of adverbs and adjectives.

- SE11 [audit] Apply the counts in references/patterns/prose.md and tell 11 (hedges) in the tells file for the book's language.

## 3. Beats as checks (Brody, 2018)

Offsets and word positions live in the beat map in references/patterns/index.md, taken from Jessica Brody's Save the Cat! Writes a Novel (2018), which presents them as a guide.

- SE12 [plan] artifacts/07-outline.md assigns each of the 15 beats to a chapter and records the word position where it lands.
- SE13 [audit] The single-scene beats (Catalyst, Break Into 2, Midpoint, All Is Lost, Break Into 3) exist as scenes within 5 percentage points of their offsets (default tolerance). The multi-scene beats cover their spans.
- SE14 [audit] The Midpoint is a false victory or a false defeat (Brody's definition) that changes how the protagonist pursues the goal. A Midpoint that only raises the volume is a finding.
- SE15 [audit] All Is Lost is the protagonist's lowest point on the SE3 plot.
- Memoir: check for turning points near 25%, 50% and 75% and treat the other beat labels as optional.

## 4. Scenes (Coyne; Swain)

Findings:

- Shawn Coyne (The Story Grid, Black Irish Entertainment, 2015) asks for five commandments in every unit of story, from beat to whole book: an inciting incident; progressive complications that make things harder, beyond merely adding more; a crisis that forces a choice between incompatible options; a climax in which the character chooses; and a resolution that shows the consequence. Every scene turns a value from positive to negative or the reverse, and Coyne treats a scene that does not turn as dead.
- Dwight V. Swain (Techniques of the Selling Writer, University of Oklahoma Press) splits narrative into scenes (goal, conflict, disaster) and sequels (reaction, dilemma, decision), and builds prose from motivation-reaction units: an outside stimulus, then the character's reaction in the order feeling, action, speech.

Checks:

- SE16 [block] For each scene, write one line: the value at the start and the value at the end. No turn means cut, merge or rewrite.
- SE17 [block] Each scene's crisis offers two options that both cost something.
- SE18 [audit] Map scenes and sequels per chapter. Default flag: three or more sequels in a row with no scene between them.
- SE19 [audit] Flag reactions out of order, such as a character explaining a feeling before the body registers the stimulus. This pairs with tell 6 in the tells files.

## 5. Tension (Zak; Maass)

Findings:

- Paul Zak ("Why Inspiring Stories Make Us React: The Neuroscience of Narrative", Cerebrum, February 2015) showed viewers a 100-second film of a father talking about his two-year-old son's terminal cancer, built as a dramatic arc with tension rising to a climax. It raised blood cortisol and oxytocin, and the oxytocin change tracked viewers' reported empathy and their donations. A control film of the same father and son spending a day at the zoo, without the tension, lost viewers' attention midway and drew few donations. Oxytocin findings of this kind, blood measurements included, have been disputed (Nave, Camerer and McCullough, Perspectives on Psychological Science, 2015). Use the result for what it shows about attention to a rising arc; treat the hormones as the lab's explanation.
- Donald Maass (The Fire in Fiction, Writer's Digest Books, 2009) locates micro-tension in conflicting emotions inside the viewpoint character, line by line, in quiet scenes and in dialogue as much as in action.

Checks:

- SE20 [block] Every chapter has tension that rises to a peak. A chapter that shows the same people without pressure (the zoo chapter) is a cut or rewrite candidate.
- SE21 [block] Before a chapter's peak, the reader has seen what the character stands to lose.
- SE22 [audit] Take the quietest page of each chapter and name the inner conflict on it in one line. Flag the chapter if there is none.

## 6. Curiosity (Loewenstein, 1994)

Finding. George Loewenstein ("The psychology of curiosity: A review and reinterpretation", Psychological Bulletin 116, 1994) describes curiosity as a felt deprivation that arises when attention falls on a gap between what one knows and what one wants to know. Curiosity needs a base: a small dose of information sharpens it, while knowing nothing, or knowing everything, dulls it.

Checks:

- SE23 [blind] At the end of each chapter, the blind reader writes, in one sentence, the question they most want answered. If they cannot, flag the chapter.
- SE24 [plan] artifacts/08-opening-strategy.md states what the first page tells the reader (who, where, what is at risk) and the question it opens. A first page that withholds so much that no specific question can form is a finding; so is one that answers its own question.
- SE25 [audit] Read the SE23 questions in order. Default flag: the same question, unchanged, for five or more consecutive chapters.

## 7. Transportation (Green and Brock, 2000)

Finding. Melanie Green and Timothy Brock ("The role of transportation in the persuasiveness of public narratives", Journal of Personality and Social Psychology 79, 2000) define transportation as absorption in a story that joins attention, imagery and feeling. More transported readers held more story-consistent beliefs and rated the protagonist more favorably. In their second experiment, readers asked to go back and mark the "false notes" (passages that did not ring true) found fewer of them the more transported they had been. Labeling the story as fact or as fiction made no difference.

Checks:

- SE26 [blind] While reading each chapter, the blind reader marks every place where they stopped picturing the scene, stopped caring how it would end, or felt their attention drift, with its location.
- SE27 [blind] After the chapter, the reader goes back and marks false notes: moments that did not ring true, with the reason.
- SE28 [audit] A location marked by two or more readers (blind readers or panel members) is a finding.

## 8. Chapters and endings

Finding (chapter length). Harry Bingham divided word count by chapter count for named novels (Jericho Writers, "How long should a chapter be?", 2020): James Patterson's Along Came a Spider about 1,100 words per chapter, Margaret Atwood's The Handmaid's Tale 2,100, John Green's The Fault in Our Stars 2,630, George Orwell's 1984 3,700, Stephenie Meyer's Twilight 4,720, George R.R. Martin's A Game of Thrones 4,970. He found most books between 2,000 and 4,000 words per chapter.

Finding (genre promise). The Romance Writers of America define a romance by two elements: a central love story and an emotionally satisfying, optimistic ending.

Checks:

- SE29 [plan] artifacts/07-outline.md sets a chapter-length band. Default: 2,000 to 4,000 words. A shorter band needs a named comp; Patterson is the standing one for thrillers.
- SE30 [audit] Default flags: a chapter longer than twice the book's median or shorter than half of it, unless the outline marks it; a book whose chapters all sit within 10% of the median.
- SE31 [audit] Classify every chapter ending: cliffhanger (action cut off), revelation (new information that demands the next chapter), emotional turn (the character arrives somewhere new) or reflection. Default flags: four or more consecutive endings of the same type; more than one reflection ending per ten chapters (see tell 4 in the tells files).
- SE32 [audit] Template repetition, a pattern from the pipeline's earlier scan: flag five or more consecutive chapters that follow the same internal sequence (normal, anomaly, escalation, close on tension).
- SE33 [plan] artifacts/07-outline.md states the ending's promise: how the protagonist's emotional arc resolves, and which plot threads, if any, stay open. A romance meets the definition above.
- SE34 [audit] The protagonist's emotional arc resolves on the page even when plot threads stay open (default).

## 9. Sharing (Berger)

Finding. Jonah Berger ("Arousal increases social transmission of information", Psychological Science, 2011) found that people made to feel high-arousal emotions such as amusement or anxiety were more willing to share content than people made to feel low-arousal ones such as contentment or sadness. Berger and Katherine Milkman ("What makes online content viral?", Journal of Marketing Research, 2012) found that New York Times articles evoking awe, anger or anxiety were more likely to make the most-emailed list, and sad ones less likely. Both studies used news articles and short clips; neither studied books. A 2024 replication of Berger's exercise-arousal study did not reproduce its result (Prowten and colleagues, Psychological Science). Treat the finding as a hypothesis about a book's shareable moments.

Check:

- SE35 [audit] Name the three moments a reader is most likely to tell a friend about (a line, a turn, a scene) and the emotion each produces. Default flag: all three are low-arousal (sadness, contentment).

## Claims not carried over

- "About 8 regular oscillations" as a bestseller target: no source found (the LRB's reading of the authors' Fifty Shades graph shows five ups and five downs); SE8 replaces it.
- Reagan et al. as "1,737 books downloaded 150+ times": the paper reports 1,327 books with more than 40 downloads.
- The "W" as a curve named in The Bestseller Code: not verified. The W shape (fall, rise, fall, rise) is sourced to Reagan's pair of Man in a hole arcs.
- Human closeness at "21% of content in typical bestsellers" and "30%+ of the book": the 21% and 13% figures are Fifty Shades only.
- "Vulnerability, not strength, triggers oxytocin": not verified in Zak's work for this release; SE21 keeps the craft point (the reader sees the stake before the peak).
- The Zeigarnik effect as the basis for cliffhangers, a University at Buffalo cliffhanger study, cliffhanger fatigue, neural coupling, mirror neurons, and recall studies from 2023 and 2025: not verified for this release. The open-question rule rests on Loewenstein.
- "Bestsellers got 42% shorter in seven years" and "the average bestseller runs 273 pages": no primary source.
