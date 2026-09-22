# Continuity

Keeps a plain-file continuity ledger for the book and checks the manuscript against it, so that no name, physical fact, relationship, date, rule or piece of knowledge contradicts itself.

When to load: Phase 2: Architecture (orchestrator as the continuity specialist, to create `artifacts/09-continuity-ledger.md`); Phase 3: Drafting (orchestrator, for each chapter brief and after every block of five chapters); Phase 4: Adversarial Audit (auditor, continuity pass); Phase 5: Revision Loop (orchestrator, ledger updates and rechecks after repairs).

## What this catches

A writer sees one chapter at a time; this process holds the whole book. It catches "Marcos" in chapter 3 and "Marco" in chapter 9, grey eyes that turn blue, a character who mentions a secret three chapters before anyone tells them, a thread that opens and never closes, one person in two cities on the same Tuesday, seven boats that become eight.

## Design

- **Plain files only.** The ledger is a markdown artifact and each check is a markdown file in `evaluations/`. No database, no script, nothing beyond reading and writing files. A text search can find candidates; only a reading decides.
- **Ownership.** The orchestrator owns `artifacts/09-continuity-ledger.md`, and one role writes it at a time.
- **Independence.** The orchestrator runs the checks. When the host can delegate, it hands each check to a fresh context bound by the auditor's rules (`references/roles/auditor.md`: never edit, quote everything); otherwise it runs the check itself and records that the check was not independent. The writer never checks its own block.
- **Blindness.** The blind reader and the reader panel never see the ledger or any continuity check.
- **Anchored to the page.** An on-page entry carries the exact words that establish it, copied from the chapter, with chapter and paragraph. Paragraphs are counted from the first paragraph after the chapter heading, one per blank-line block; scene-break lines do not count. Inside the ledger, `ch07 p12` is short for chapter-07, paragraph 12.

## The ledger (`artifacts/09-continuity-ledger.md`)

Sections, with IDs that findings can cite:

| Section | ID | Each entry records |
|---|---|---|
| Characters | C- | canonical name and aliases; physical facts (eyes, hair, height, build, marks, glasses, habitual items); age with the date it was true; fixed traits (left-handed) and changeable ones (a fear, an addiction); a location log, one line per chapter |
| Relationships | R- | the pair, the type, where it was established, its current status, each change with its source |
| Knowledge | K- | the fact; who knows it, since when, and how (told by whom, overheard, witnessed, discovered, inferred from clues on the page); who must not know it yet; the reveal the outline plans |
| Locations | L- | name and aliases; layout and directions; distances with travel times |
| Objects | O- | where introduced and with what emphasis; who holds it; where last seen; status (open, paid off, background, destroyed, lost); the planned payoff |
| Timeline | T- | one row per chapter: day, date or time of day; time elapsed since the previous chapter; season and year; flashback marker |
| World rules | W- | the rule, its exact limit, its cost; what is not revealed yet, and when it will be |
| Threads | TH- | the question, promise or mystery; where it opened; importance (major, subplot, detail); status (open, resolved, abandoned); the planned close |
| Conflicts | X- | two values that disagree, each with its quote and source; status |

Source notation: `ch07 p12 "exact words"` for the page; `plan: 03-characters` or `plan: 07-outline ch12` for facts that exist only in the plan so far.

```markdown
# Continuity Ledger
Updated after: chapter 10 (check 02)

## Characters
### C-01 Mara Ilves (aliases: Ilves, "the diver")
- Eyes: grey. ch02 p14 "her grey eyes"
- Age: 34 in autumn 2019. ch01 p3 "thirty-four that October"
- Fixed: left-handed. ch02 p19 "signed with her left hand"
- Changeable: afraid of deep water; plan: overcome in ch24 (07-outline)
- Location: ch01 harbor; ch02 flat; ch03 ferry to Helsinki (travel shown, ch03 p1)

## Knowledge
- K-07 The warehouse fire was arson. ch09 p14 "someone had poured the diesel" (Tomas, witnessed). Known by: Tomas. Not yet: Mara, Enn. Plan: Mara learns in ch12.

## Timeline
| Ch | When | Elapsed | Season, year | Note |
|---|---|---|---|---|
| 01 | Monday morning | start | autumn 2019 | |
| 02 | Monday night | same day | | |

## Conflicts
- X-01 Mara's eyes: grey (ch02 p14 "her grey eyes") against blue (ch09 p7 "blue eyes narrowed"). Open; finding CC-02-01.
```

### Ledger rules

- **Seed it in Phase 2: Architecture**, before any chapter exists, from `artifacts/02-story-engine.md`, `artifacts/03-characters.md`, `artifacts/04-theme.md` where it fixes facts, `artifacts/07-outline.md` and `artifacts/08-opening-strategy.md`. Every seeded entry is a plan entry. The outline's reveals become Knowledge entries with their planned chapter and who is present; its set-ups become Objects and Threads with their planned payoff.
- **The page becomes canon once written.** A drafted fact that differs from the plan is a finding: either the page or the plan changes, and the decision is recorded in the ledger.
- **Never overwrite on contradiction.** When an update meets a value that disagrees with an entry, add a Conflict entry with both quotes. The check turns it into a finding.
- **Legitimate change is history, not conflict.** Dyed hair, a healed limp, a year of aging: record the new value with the scene that changed it, and keep the old one with the chapters in which it held.
- **Numbers show their arithmetic.** Ages, counts, money, distances and elapsed days are recorded with their sources, and any check that combines them shows each operand with its source: "34 in ch01 (autumn 2019); ch20 is autumn 2021; 34 + 2 = 36; ch20 p5 says 'thirty-five'." Correct arithmetic does not prove the reading: state the interpretation used ("three days later" counted from which day?).
- **Uncertain identity gets a new entry.** If you cannot tell whether "Ana" is a new character or C-04's nickname, create an entry marked "review: possible alias of C-04". A wrong merge destroys data; a wrong split only raises a question.
- **Track what carries weight.** Named characters and recurring unnamed ones ("the bartender at the Red Door"), places where scenes happen, objects given narrative emphasis (a close-up, an exchange, a reaction). A cup of coffee is not an object; a bloodstained cup is. With more than 30 named characters, mark each one major, supporting, minor or mentioned.
- **Flashbacks** carry a flashback marker and never enter the present-day location log.

## The writer's slice

Each chapter brief (`work/briefs/chapter-NN.md`) carries the ledger entries that chapter touches: the characters present, the places, the objects and open threads in play, the knowledge that matters in its scenes, every world rule, and the latest timeline rows. Not the whole ledger. A slice is not exhaustive recall, so the block check reads the chapters themselves, and Phase 4: Adversarial Audit reads every chapter.

## When it runs

| When | Scope | Output |
|---|---|---|
| Phase 2: Architecture | the foundation and outline artifacts | the seeded ledger |
| Phase 3: Drafting, after chapters 5, 10, 15 and so on, and after the last chapter | the new block, read against the ledger and every earlier chapter | the ledger updated, then `evaluations/continuity-check-NN.md` (NN is the block number: 01 for chapters 1 to 5) |
| Phase 4: Adversarial Audit | every chapter; the auditor's continuity pass applies every check below at full depth, thread payoffs included | tickets in `artifacts/10-adversarial-audit.md`, in the auditor's format |
| After any revision, in Phase 3: Drafting or Phase 5: Revision Loop | the revised chapter and its neighbors, before the orchestrator promotes it | the ledger updated for the changed chapters; a Recheck section in the check file whose findings it verifies, or a note with the pass in `evaluations/revision-loop.md` |

A block check first updates the ledger, then checks. The update reads the block's chapters in order and records new facts with their quotes, the location log and the timeline row, knowledge acquired and how, objects introduced, moved or paid off, threads opened or closed, and new named entities. After a revision, reread the changed chapters: an entry whose only source changed is revalidated, a value no longer on any page is marked "last confirmed chNN", and a conflict with one side edited away is closed with a note.

Block checks record threads as they open but do not flag them as unresolved, since they may close later. The Phase 4: Adversarial Audit continuity pass flags them.

## The checks

### 1. Characters and physical facts

- Names: spelling drift (Marcos, Marco), surname variants, a nickname used before it is introduced, a title that changes (Dr. Mendes, Professor Mendes). A name that appears fewer than three times may be a typo for another. Search each name's stem (Helen finds Helena and Helene), common swaps (c and k, s and z, ph and f) and doubled letters.
- Physical facts against the ledger: eyes, hair, height, build, age, marks.
- Behavior against `artifacts/03-characters.md`: the one who never cries cries without comment, the technophobe hacks a system, the left-hander writes with the right hand. A change the arc plans is not an error.
- Location: nobody is in two places at once, and travel is shown or plausible in the time available.
- Dialogue attribution: the speaker is present, conscious and able to speak; no accidental swap of names.

### 2. Relationships

A "stranger" who spoke with the protagonist two chapters earlier; "old friends" with no shared history; married in one chapter and "partner" in another with no explanation; a boss who changes without a reason.

### 3. Information flow

The hardest contradictions to see from inside one chapter, so this check gets the largest share of the effort.

- **Room audit.** For every scene with several characters, list who is present at each reveal, and who entered or left before it. A character who left before the secret was spoken does not know it.
- **Knowledge path.** For every piece of knowledge a character uses, in dialogue, action, an emotional reaction or narration inside their head, confirm one of: present at the reveal; told on the page; told plausibly off the page (medium: consider showing it); discovered; inferred from clues the reader has seen.
- **Communications.** A character who cites "the message" or "the call" received one on the page, or the text clearly implies it.
- **Classic violations.** Reacting to news before it arrives (the reaction was written before the delivery); referencing an event that has not happened yet; narration revealing a point-of-view character's thoughts about something they do not know.

### 4. Timeline

- Mark every temporal reference per chapter: days, dates, years, seasons, time of day, relative time. Words to search for: in English, yesterday, tomorrow, the next morning, later, ago, the days of the week, the months; in Portuguese, ontem, amanhã, na manhã seguinte, depois, atrás, the days of the week (segunda, terça, sábado...), the months.
- Sequence: "three days later" matches the count; a chapter that ends Saturday night followed by one that opens Monday morning accounts for Sunday; travel times and opening hours are plausible.
- Season, weather and daylight fit the date and place: morning rain means wet streets in the afternoon, or the text says it stopped.
- Ages: compute each character's age at each point from its anchor, and check birthdays. Show the arithmetic.
- Quantities: counts, money, distances. Show the arithmetic.

### 5. World rules

- Technology and period: no device or service before it existed (a character posting on Instagram in 2008, two years before it launched), no unexplained anachronism.
- Geography: distances and directions stay the same (the river stays east of town).
- Institutions: names, ranks, hierarchy and procedures stay the same (a badge needed in chapter 2 is still needed in chapter 11).
- Economy: currency, prices in proportion to each other and to the period, a character's finances (broke in chapter 5 and buying a house in chapter 7 needs a reason).
- Language: dialect, regional vocabulary and code-switching stay consistent.
- Systems (magic, technology, powers): limits and costs are respected, and no new rule appears just to solve the climax.

### 6. Objects and threads

- Set-up without payoff: an object, skill, mystery or threat introduced with emphasis and never used (flagged in Phase 4: Adversarial Audit only). Not every detail needs a payoff; only emphasized ones create expectations.
- Payoff without set-up: "she finally used the lockpick her father taught her" with no scene of the teaching.
- Contradictory plot points: a door locked from the inside that someone later opens without a key.

## Findings

Every finding quotes the contradicting passages exactly, with chapter and paragraph, cites the ledger entry, and has a severity on the auditor's scale. A finding without quotes is not a finding. For a wrong value that repeats, list every occurrence so one ticket can cover them all.

| Severity | Use for |
|---|---|
| high | knowledge used before it could be learned; a character in two places; a physical fact contradicted with no reason; an age off by two years or more; a resolution that depends on something never set up; a plot contradiction a careful reader would catch |
| medium | knowledge whose path is plausible but never shown; an ambiguous time gap; a character's whereabouts unclear for three chapters or more; season or weather against the timeline; an age off by one year; a major set-up with no payoff |
| low | a clothing detail; a minor detail introduced with emphasis and never mentioned again; a spelling variant of a minor name |

When in doubt, choose the higher severity. An inconsistency the plan records as arc (a character changing, an unreliable narrator's deliberate lie) is not a finding.

```markdown
### CC-02-03 | severity: high | Mara knows about the arson before anyone tells her
Check: information flow
Ledger: K-07 (arson; known by Tomas since ch09 p14; Mara not told)
Passages:
- chapter-09, paragraph 14: "someone had poured the diesel" (the reveal; Mara is not in the scene)
- chapter-10, paragraph 22: "Whoever set that fire, Mara said" (she uses it)
Why it contradicts: no chapter shows anyone telling Mara, and she has seen no clue.
Smallest fix: show Tomas telling her before chapter-10, paragraph 22, or turn her line into suspicion.
Cascade: chapter-10, paragraph 30 depends on her certainty; recheck it after the fix.
```

Finding IDs are `CC-<check number>-<finding number>`. In Phase 4: Adversarial Audit the auditor writes its continuity findings directly as tickets, with the ledger entry as `evidence`.

Before saving, reread every high finding: confirm each quote is exact and sits where the finding says (a plain text search of the chapter confirms it), and that the contradiction is real and not a misreading.

## Repairs

1. The orchestrator turns each finding into a ticket in the auditor's format (`references/roles/auditor.md`), with the finding ID and the ledger entry as `evidence`. The passage to change is the ticket's quote, and the class follows the fix: `continuity` for replacing a wrong value, `prose` for turning a line into suspicion, `structural` when a scene must show a knowledge path. The revision editor applies it (`references/specialists/revision-editor.md`).
2. In Phase 3: Drafting, every finding is ticketed and fixed before the next block is drafted, because errors compound. Low findings in one chapter can share one ticket.
3. Chapters that no ticket names keep their files. Nothing is redrafted to fix a local contradiction.
4. Before a revision is promoted, recheck it and its neighbors against the ledger, and mark every earlier finding closed or open. This applies in Phase 5: Revision Loop too, after the panel prefers a revision: structural fixes break continuity. A revision that fails the recheck is never promoted; the chapter file keeps its accepted version, and the finding stays open.
5. When the page is better than the plan, change canon instead of the page: the orchestrator updates the ledger entry, notes "canon revised" with the reason, and rechecks every chapter that relied on the old value.
6. At most three repair passes per check. A pass that leaves the same findings open over the same text is not repeated: stop at a checkpoint, record what remains in `RUN_REPORT.md`, and tell the author.

## Check file (`evaluations/continuity-check-NN.md`)

```markdown
# Continuity check 02: chapters 6 to 10
Ledger updated: yes (new entries: C-09, K-11, O-04)
Run by: fresh context under the auditor's rules (or: orchestrator, not independent)
Findings: high N, medium N, low N

## High
### CC-02-01 | severity: high | ...

## Medium

## Low

## Threads opened in this block

## Recheck after revision r1
| Finding | Status (closed, open) | Evidence (quote after the fix) |
|---|---|---|
```
