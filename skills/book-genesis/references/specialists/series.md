# Series Architecture

Plans a book that belongs to a series so that each volume satisfies on its own while the series story advances, with no contradictions between volumes.

When to load: only when the intake positions the book as part of a series (`project.series: true` in `PROJECT_STATE.yaml`, set in Phase 0: Intake). The orchestrator then reads it in Phase 0: Intake, Phase 1: Foundation, Phase 2: Architecture and Phase 7: Editorial Package, and the auditor uses the volume checklist in Phase 4: Adversarial Audit. Standalone books skip this file.

## Core principle: two stories per volume

Each volume tells the story of the book, which begins and ends inside the volume, and the story of the series, which began in volume 1 and ends only in the last. The reader needs closure on the first to tolerate suspense on the second. Never trade a volume's closure for a series hook.

Harry Potter and the Philosopher's Stone (J.K. Rowling) closes its own mystery, who is trying to steal the Stone, while the war with Voldemort runs across all seven books.

## Where the series lives

There is no separate series file. Series material goes into the artifacts that already exist, each in a section headed `## Series`. Together those sections are the series bible, and what they fix is canon: changing it requires a "canon revision" note, with the reason, in the artifact that changes.

| Artifact | Its `## Series` section holds | Written in |
|---|---|---|
| `artifacts/02-story-engine.md` | series premise, the protagonist's series arc and series lie, the volume map | Phase 0: Intake |
| `artifacts/03-characters.md` | arcs across volumes, the core wound volume by volume, relationships as arcs, exits and deaths | Phase 1: Foundation |
| `artifacts/06-emotional-curve.md` | this volume's complete curve, plus one line per volume for the series curve | Phase 1: Foundation |
| `artifacts/07-outline.md` | where this volume's closure lands, where the next-volume hook is planted, the intentional open mysteries | Phase 2: Architecture |
| `artifacts/08-opening-strategy.md` | how chapter 1 delivers this volume's core promise | Phase 2: Architecture |
| `artifacts/09-continuity-ledger.md` | series canon: world systems, geography and power, canonical timeline, glossary | Phase 2: Architecture |
| `artifacts/13-positioning.md` | series name, volume number, reading order | Phase 7: Editorial Package |

Each volume is its own book folder. When a new volume starts, the orchestrator copies the previous volume's `## Series` sections and its final continuity ledger into the new folder during Phase 0: Intake. From then on the previous volume's folder is read-only.

Minimum input: the premise of volume 1, the planned number of volumes and the main protagonist. Ideal input: the finished previous volume, the next volume's outline and any existing worldbuilding notes.

## Series engine (`artifacts/02-story-engine.md`)

- **Series premise**, one paragraph: the macro conflict that justifies several volumes, why one book cannot resolve it, and what is at stake at series level rather than volume level.
- **Protagonist's series arc**: beliefs, wounds and behaviors on volume 1, page 1; what each volume must change and what must not change yet; where the protagonist ends at the close of the final volume.
- **Series lie**: the core belief that is challenged only at the final climax.
- **Volume map**, one block per planned volume:

```markdown
### Volume 2: working title
- Core promise: what the reader buys into with this volume
- Internal conflict (this volume only):
- External conflict (this volume only):
- Resolves: the volume's own closure
- Opens: the question or threat that leads to volume 3
- Protagonist at the end: what changed, visibly and irreversibly
- Series reveal: what the macro story discloses here
```

## Characters across volumes (`artifacts/03-characters.md`)

For every main and recurring secondary character:

- their state at the start of each volume: emotional, relational, functional
- what cannot regress without a scene that motivates it
- what must evolve, and at what pace
- the core wound: each volume presses on it in a new way, and it deepens, scars or heals. It never quietly resets between volumes.

Relationships are arcs of their own. For each key relationship, record its state at the start of every volume (one line), the moment of greatest tension in the series, and whether it resolves in the final volume or earlier.

Exits and deaths: who may die in which volume without breaking the series; who cannot die before volume X, and the narrative function that protects them; how an absence keeps the reader's investment.

## Emotional curve at two levels (`artifacts/06-emotional-curve.md`)

The volume's own curve is complete inside the volume, with its own low point and its own release; it never borrows its release from the next book. The series curve is one line per volume: the emotional state the volume leaves the reader in. A volume that leaves the reader where the previous one did has not moved the series.

## The volume ending and the next-volume hook

Record both in the `## Series` section of `artifacts/07-outline.md`.

Closure, mandatory:

- the volume's central conflict is resolved and the reader gets catharsis
- the protagonist has changed visibly and irreversibly
- no loose end that reads as an oversight; the intentional open mysteries are listed

Opening, strategic:

- a question or threat that makes the next volume necessary
- planted before the final climax, never tacked onto an epilogue. Checkable: the first plant falls before the last 20% of the outline's chapters
- hook types: a world revelation that changes what the reader thought they knew; an escalated threat; an irreversible loss; the promise of an answer the reader needs

The Hunger Games (Suzanne Collins) ends its own story when the Games end, but the defiance that drives the sequels is planted well before the climax, when Katniss covers Rue's body with flowers and District 11 answers with a gift of bread.

Chapter 1 of every later volume delivers that volume's core promise from the volume map, and it works for a reader who starts there: orient through action and consequence, not through a recap block. Record how in `artifacts/08-opening-strategy.md`.

## Series canon (`artifacts/09-continuity-ledger.md`)

Document once, then check against it. Inside a volume the ledger follows `references/specialists/continuity.md`; the series layer adds:

- **World systems** (magic, technology, powers): what is possible and its exact limit, the cost of use, what the reader has not been told yet and in which volume they will be, and the inconsistencies that must never happen.
- **Geography and power**: who controls what and why, what changes between volumes (a city destroyed, an alliance broken), what stays constant as the reader's anchor.
- **Canonical timeline**, one line per event, including backstory the reader does not know yet:

```markdown
| Event | When | Who knows | Revealed in volume |
|---|---|---|---|
```

- **Glossary**: terms, names and concepts with exact definitions. Later volumes add entries; they never redefine one without a canon revision note.

At the end of each volume, in Phase 7: Editorial Package, the final ledger becomes the next volume's starting ledger.

## When to consult the series sections

- before writing any scene of volume 2 or later
- when a plot point in the current volume could create a contradiction later
- when a character decision affects a future arc
- when reviewing the ending of any volume (closure plus hook)

## Volume checklist

The auditor runs it in Phase 4: Adversarial Audit; the orchestrator confirms it before Phase 7: Editorial Package.

- [ ] Every world rule is respected; no new power or rule appears only to solve the climax
- [ ] Names, dates and places match the series canon and earlier volumes
- [ ] Characters act from their established psychology, or a scene justifies the change
- [ ] The world at this volume's start reflects the previous volume's end
- [ ] Resolving this volume's conflict opened no plot hole
- [ ] The next-volume hook is planted before the last 20% of the chapters
- [ ] The series story advanced: a reader can say what changed in the macro arc
- [ ] Every open thread is either closed or listed as an intentional mystery

Findings use the continuity finding format (`references/specialists/continuity.md`: quoted passages with chapter and paragraph, the canon entry, a severity) and reach the revision editor as tickets in the auditor's format.
