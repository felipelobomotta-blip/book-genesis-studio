# Hook test

A simulated signal, not a market measurement. Three AI-played readers react to alternative pitches so the author can choose with reasons. The label goes at the top and at the bottom of the result.

Run it after the main package is drafted, so every option is built from the real book.

## 1. Build three to five pitch options

Each option is a set: a title, a logline, and a blurb in the same 100 to 180 word range as the main package, all built on one angle. Give each option a different angle:

- **Character:** who they are and what they want.
- **Premise:** the situation, the "what if".
- **Question:** the mystery or dilemma at the center.
- **Mood and voice:** how the book feels to read.
- **Shelf:** the promise this category's readers look for (the trope, the stakes, the kind of ending).

If the author already has a title or pitch, it enters unchanged as one of the options. It is the control.

Every option must be honest to the book. No option may promise a genre, a twist, or a tone the manuscript doesn't deliver.

Letter the options A to E in random order, so the author's option is not always A.

## 2. Build three readers from the target audience

Start from the reader line in the package card.

- **The Regular (R):** reads this shelf constantly and has read the comparable titles. Knows the tropes, is bored by sameness, and rewards a fresh angle on a familiar promise.
- **The Occasional (O):** buys a handful of books a year from recommendations, front tables, or a social feed. Decides in seconds.
- **The Crossover (X):** reads a neighboring shelf (a thriller reader for a literary mystery, a fantasy reader for a historical novel) and could be won over, or not.

Give each a two-line profile: age range, the last book they loved, where they find books. Invent them; never use real people.

## 3. Ask the three questions

The readers judge blind: nothing they see says which option is the author's or which one you prefer.

- **If your host can run subagents,** give each reader its own subagent with only: their profile, the lettered options in a shuffled order, the first 250 words, and the three questions below.
- **If it cannot,** run the readers one at a time in this conversation, shuffle the options for each reader, and finish one reader's answers before starting the next.

Record which way the test ran. Each reader answers yes, maybe, or no, with the thought in their head, in their own voice.

1. **Would you click?** They see only the title and the logline, as in a store listing or a feed.
2. **Would you buy?** They read the blurb.
3. **Would you keep reading after the first 250 words?** Right after that option's blurb, they read the first 250 words of the story itself (skip the title page, dedication, epigraph, and contents), unchanged. They answer as someone who picked the book because of that blurb: does this opening deliver what it promised? The opening is the same for every option, so the differences here show which pitch sets up the right expectations for the book the author actually wrote.

## 4. Score and rank

- yes = 2, maybe = 1, no = 0. Three readers times three questions gives each option a score from 0 to 18.
- Rank by total. Break ties by the buy answers, then by the keep-reading answers.
- The score only orders the options for discussion. It is not a probability or a forecast.

Read the pattern, not just the ranking:

- **Every option weak on "click":** the title or the category signal may be off for this shelf.
- **Strong on "buy", weak on "keep reading":** the pitch promises a book the opening doesn't deliver.
- **Every option weak on "keep reading":** the problem is probably the opening, not the pitch. Say so.

Recommend the top option unless a reader's reason shows it would mislead buyers, and explain any departure from the ranking. If the reasons point to a mix (one option's title with another's blurb), run the mix past the same three readers with the same three questions before recommending it.

## 5. Output

```markdown
## Hook test
Simulated signal, not a market measurement.

Readers: R = the Regular, O = the Occasional, X = the Crossover.
How the readers ran: [separate subagents / one after another in this conversation (less independent)]

| Rank | Option | Title | Click (R/O/X) | Buy (R/O/X) | Keep reading (R/O/X) | Score /18 |
|---:|---|---|---|---|---|---:|
| 1 | C | ... | yes/yes/maybe | yes/maybe/maybe | yes/yes/no | 13 |

### Option C: [title]
- Logline: ...
- Best reason for: "[a reader's words]" (Regular)
- Best reason against: "[a reader's words]" (Crossover)

[the same block for each option; mark the author's own option "(current)" here, after the scoring]

### Recommendation
[the pick, and why, in two or three sentences]

Simulated signal from three AI-played readers, not a market test. Before committing, try the top two options on real readers: a newsletter poll, a reader group, or a small ad test.
```
