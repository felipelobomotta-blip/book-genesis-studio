# Current-text evidence and delivery

Load when aggregating readers, freezing Phase 6, exporting or resuming after an edit. Technical delivery, current simulated-reader coverage, literary gates and a human publication decision are separate outcomes.

## Reader receipts

After a native read completes, save its raw JSON verbatim. Validate the exact assigned chapter files with `scripts/validate_blind_reader.py` and save its stdout as the original receipt. Keep both immutable. The receipt binds the raw report and source chapter bytes.

After any canonical edit, old evidence for that chapter is stale, even when its quotes still exist. Run a fresh read for the affected scope; never regenerate an old report's receipt against new prose to make it current. A comparison vote is not a new single-draft gate read. Invalid reads remain saved and do not enter a majority; retry only within the documented bounds.

Save `evaluations/review-index.json` for the currently required reads, using paths relative to the book folder. Each scope declares its exact canonical chapters and four distinct persona names. Copy a reader entry for each of the four required readers:

```json
{
  "schema_version": 1,
  "scopes": [{
    "scope": "opening",
    "chapters": ["chapter-01.md"],
    "readers": [{
      "reader": "<persona name from raw report>",
      "report": "evaluations/readers/opening-primary.json",
      "validation": "evaluations/readers/opening-primary-validation.json"
    }]
  }]
}
```

The compact example shows one entry; a real scope requires all four. A gate scope covers only its declared sample; it does not claim every chapter was read. Freeze the final sample from `references/roles/panel.md`, including chapters revised in the pass. Run:

```bash
python "<skill-root>/scripts/verify_book.py" --book-dir . --review-index evaluations/review-index.json --check reviews
```

The helper rejects stale source hashes, changed reports, duplicate identities, missing reads and invalid quotes. Current coverage means four valid reads for each declared scope; it is neither a literary pass nor proof of human reading. Record any incomplete coverage beside the verdict instead of recycling a previous pass.

## Delivery

Export the frozen canonical chapters with `scripts/export_book.py`. The export commits `manuscript.md`, EPUB, its receipt and `STATUS.json` together. Requested DOCX/PDF use existing libraries. `STATUS.json` reports technical delivery and distinguishes a standalone draft export from complete-pipeline preflight.

After export run:

```bash
python "<skill-root>/scripts/verify_book.py" --book-dir . --check delivery
```

Use that observed result to reconcile `delivery.status`, `delivery.scope` and `delivery.receipt` in `PROJECT_STATE.yaml`, and inventory the actual files in `RUN_REPORT.md`. Do not leave the author-facing status pending when the verified files are delivered; do not claim delivery on a failed receipt. If prose changes later, verification reports the old export as stale until it is replaced deliberately.

For the final inventory, run `--check all` with the final review index and save the JSON report verbatim. Report missing reader coverage or unmet literary gates even if exports pass. This helper never updates project YAML, fabricates a review, grades prose or grants publication approval.
