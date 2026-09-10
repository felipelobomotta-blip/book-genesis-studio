# Local Runner (historical)

Book Genesis 5.0 is a markdown-first, native-agent workflow. The old interactive
book-generation CLI has been removed from the public product. The maintainer
installer is `runner/installer.py` and only installs or verifies the skill bundle.

The mechanical helpers below are retained for regression fixtures and historical
reproduction; they do not call an LLM and do not claim literary quality.

It does not call an LLM and it does not claim literary quality. Agents still write, audit, score, and package the manuscript using the active phase prompt.

## Commands

```bash
python runner/installer.py verify-suite
```

The maintainer installer exposes only `install`, `verify-suite`, and
`verify-install`. The native host reads phase prompts and dispatches its own
agents. The helper does not scaffold a book or simulate a completed run.

Historical helper behavior:

`prepare-phase` used to write:

```text
my-book/work/current-phase.md
```

That file contains the phase label, gate, required outputs, and the full active phase prompt from `skills/book-genesis/references/`.

`prepare-swarm` used to write:

```text
my-book/evaluations/book-swarm/<date>-launch-reaction/
```

That folder contains the Book Swarm Panel contract: persona roster, sample map, cohort reports, interviews, public-opinion report, risk heatmap, revision tickets, score calibration, summary, and an optional `mirofish-requirement.md` bridge file for external MiroFish runs.

`prepare-agent-packet` used to write:

```text
my-book/work/agent-packets/prose_writer.md
```

That file contains the specialist mission, missing inputs, required outputs, gates, score floor, and relevant skill prompt from `skills/book-bestseller-studio/references/agent-registry.yaml`.

## Historical Mechanical Demo

The old deterministic demo is not exposed by the 5.0 installer and must not be
used as evidence of literary output. It remains represented in regression
fixtures solely to protect the file-contract logic.

## What The Runner Guarantees

- `PROJECT_STATE.yaml` exists and tracks the current phase.
- `ASSUMPTIONS.md`, `RUN_REPORT.md`, `artifacts/`, `manuscript/chapters/`, `evaluations/`, and `delivery/` exist.
- Phase outputs must be replaced before `advance-phase` succeeds.
- Phase 4 cannot be skipped because phase order is read from the manifest.
- Book-swarm runs use a durable folder contract before clean-room simulation or external MiroFish import.
- Specialist agents use packet files so worldbuilding, writing, pacing, continuity, scoring, packaging, and launch work have explicit ownership.

## What The Runner Does Not Do

- It does not call Claude, Codex, Kimi, OpenAI, or any other model.
- It does not generate real prose.
- It does not score a manuscript by itself.
- It does not run MiroFish. It prepares import/export files for an external MiroFish run when available.
- It does not build EPUB/PDF files.

Those steps belong to the agent executing the phase prompt.
