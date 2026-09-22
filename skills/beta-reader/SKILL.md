---
name: beta-reader
description: Use when you want beta reader feedback on your draft from three sharply different test readers, one who reads for pace, one who reads for depth, and one who hunts for plot holes and weak logic. Each reads your pages in order and reports where they would stop reading, what confused them, and what they loved, quoting your own lines. You also get a map of where attention drops and a short list of what to fix first, separating the problems all three readers agree on from matters of taste. Works on a chapter, a part, or a whole novel, memoir, or nonfiction book, in any language, and the report comes back in the language of your book. The readers are simulated, not real people, so use them to find what to fix before real readers see the book.
---

# Beta Reader

Three simulated readers with different tastes, habits, and tolerances read the draft in order and report honestly. The goal is diagnosis, not praise: where each reader would stop, what confuses them, what delights them, and what is missing.

Why three and not ten: one model playing many readers produces many versions of the same bias. Three readers with deep, conflicting instructions give more signal and less noise. When all three flag the same problem from their own angles, it is real. When only one does, it may be taste.

## The readers

| Reader | Reads for | Quits when | Brief |
|---|---|---|---|
| The Page-Turner | pace, feeling, momentum | patience runs out | `references/page-turner.md` |
| The Critic | depth, originality, precision | they stop trusting the author | `references/critic.md` |
| The Skeptic | logic, consistency, credibility | a hole breaks belief | `references/skeptic.md` |

Each brief is long on purpose. Load a reader's brief only for that reader's pass.

## What the readers may see

Readers know only what a real reader knows before opening the book: the title, the genre, and the back-cover copy if the author has one. They never see the outline, synopsis, author notes, research, or earlier feedback.

If the author has an outline, a synopsis, or goals for the book, read them yourself, but keep them away from the readers. They feed only the final "What you meant vs what readers felt" section.

If you are given a middle chapter on its own, the readers may read a short summary of what came before (and nothing after), the way a returning reader remembers the story. Say so in the report.

## Process

1. **Collect the text.** A chapter, a part, or the whole manuscript: pasted, one file, or a folder of chapter files read in order. Note what was read, for example "chapters 1-8 of 24" or "full manuscript".
2. **Infer what you can.** Genre, audience, and language come from the text when the author did not say. State your guess at the top of the report instead of asking.
3. **Check scope.** The readers are built for prose books: novels, novellas, story collections, memoir, and narrative or practical nonfiction. For poetry, picture books, or scripts, say so and offer a lighter read.
4. **Set the language.** Write the whole report in the manuscript's language unless the author asks for another one. A Portuguese draft gets a Portuguese report, read by readers of that market with that market's references. Translate the reader names naturally. Quote passages exactly as written, never translated.
5. **Run the readers apart.** If your host can run subagents, give each reader its own subagent with only: the text (plus title, genre, and back-cover copy if any), that reader's brief, the reading rules, and the report format below. If it cannot, run the readers one at a time in this conversation, finish each report before starting the next, and never revise an earlier report after writing a later one. Record which way you ran them.
6. **Write the synthesis** (below), then the honesty lines.

## Reading rules for all three readers

- Read in order. No skipping ahead, no reading the ending first.
- For a long manuscript, read in consecutive parts and keep a running log for each reader, so the stop points are real.
- Quote exactly. Locate every point by chapter and page, or by a short quote the author can search for.
- When a reader quits, record the quit point, then keep reading as a favor to the author. Mark everything after it "read past my quit point", and say whether anything later would have won them back.
- Stay in character. Each reader reports only from their own seat. Fairness happens in the synthesis, not in the reader reports.

## Report order

1. **Header:** what was read, the genre and audience (stated by the author or guessed by you), and the language.
2. **The three reader reports,** in this order: the Page-Turner, the Critic, the Skeptic.
3. **The synthesis.**
4. **The honesty lines.**

## Report format for each reader

```markdown
### [Reader name]
**Verdict:** Finished it / Quit at [location] / Finished out of duty
**Where I'd stop reading:** [location] "[quote]" [what went through my head]. If nowhere: "No reason to stop."
**Close calls:** [where I nearly quit, and what pulled me back]
**What confused me:** [location, what, why] or "Nothing."
**What delighted me:** [location] "[quote]" [why]
**Top 3 problems:** [each with a quote and a location]
**What's missing:** [what I wanted and never got]
**The morning after:** [the one image or line still in my head tomorrow] or "Nothing stuck."
**Engagement:** [X]/10, [one-line reason]
**Would I recommend it?** [yes or no, to whom, and in what words]
[The reader's own section, from their brief]
```

Verdicts, the same for all readers:

- **Finished it:** kept reading because they wanted to.
- **Quit at [location]:** would have stopped there for good; everything after it was read only as a favor to the author.
- **Finished out of duty:** never hit a stopping point, but kept going without wanting to.

Engagement anchors, the same for all readers:

- 3: quit early and would not come back
- 5: would finish it only if stuck on a long flight
- 7: finished it and was glad to
- 9: would press it on friends
- 10: among the best books I have read in this genre (rare)

Score like a stranger who paid for the book, not like the author's friend. Any score of 8 or more needs a quoted reason.

## Synthesis: where the readers agree

### Agreement table

| Issue | Page-Turner | Critic | Skeptic | Call |
|---|---|---|---|---|

One row per issue or standout passage. In each reader's cell, write what that reader said in a few words, or leave it empty. Decide the call with these rules:

| Situation | Call |
|---|---|
| All three flag the same problem | Critical: fix first |
| Two of three flag it | Real problem: very likely worth fixing |
| Only one flags it | May be taste: look closely before acting |
| All three praise the same passage | Confirmed strength: protect it in revision |
| The Skeptic praises it | Exceptional moment: probably a selling point |
| Only the Page-Turner quits, and inside the first chapter | Important anyway: an opening that loses a casual reader loses browsers too |
| Nothing stuck for any reader the morning after | Important: the book has no moment people will remember |

### Convergence check

Agreement counts only when readers reach it from their own seats: the Page-Turner is bored in chapter 5, the Critic finds it cliched, the Skeptic does not believe it. That is three signals. If two reports flag the same passage for the same reason in similar words, count it once and write "readers converged here".

### Attention map (more than one chapter)

| Chapter | Page-Turner | Critic | Skeptic |
|---|---|---|---|
| 1 | in | in | drifting |

Map each reader's own log onto three words only: `in`, `drifting`, `out`. Two or more readers drifting or out in the same stretch marks a danger zone. Name it.

### Fix first (at most five)

Order: logic and character problems first, then structure and pace, then line-level prose. Polishing a passage that will be cut is wasted work. Each fix names the location, the problem, and a concrete direction ("cut the town history in chapter 4 to one paragraph and move it after the body is found"), never just "tighten this".

### Protect

The passages the revision must not touch, and why.

### What you meant vs what readers felt

Only if the author shared goals, an outline, or a synopsis. One line per gap, for example: "You meant chapter 9 to devastate; the Page-Turner skimmed it and the Skeptic did not believe it."

### Honesty lines (always the last lines of the report)

- **How the readers ran:** "separate subagents, each seeing only the text" or "one after another in this conversation (less independent)".
- **Simulated readers:** "These are AI-simulated readers, not real people. Use this report to decide what to fix and what to test with real readers; it does not replace them."
- **Self-review warning**, only if you, in this conversation, wrote or rewrote any of the text: "Models tend to go easy on prose they helped write. Weigh the praise accordingly."

## Saving the report

If you can write files, save the report beside the manuscript as `beta-reader-report-YYYY-MM-DD.md`, and never overwrite an earlier one. Otherwise, reply in the conversation.

If an earlier report exists, the readers still read blind; you compare afterwards: what got fixed, what is still there, and what is new, including problems the revision itself created.

## When to use it

- After each part of a draft. Don't wait for the whole book.
- Before sending the manuscript to agents, editors, or real beta readers.
- After a big revision, to check that the fix did not break something else.
- When you are unsure whether a passage works.

This skill stands alone. The full idea-to-book workflow is the Book Genesis skill.
