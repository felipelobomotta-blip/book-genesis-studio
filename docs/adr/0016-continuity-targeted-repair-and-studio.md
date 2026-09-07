# ADR 0016 — Continuity, targeted repairs, and Writing Studio

Status: implemented locally; release validation is separate.

## Problem

The September QA campaign preserved five complete short manuscripts, but only one passed its final editorial pipeline. Names, dates, quantities and calendars drifted. Whole-book repair scheduled every chapter again. Terminal checkpoints were difficult for beginners to interpret.

## Decisions

1. Live role setup supplies `continuity` using the configured extractor and `auditor` using the configured reader provider/model. The auditor has a different prompt contract from a blind reader. Same-family warnings remain relevant; separate prompts are not human judgment.
2. Before drafting, memory indexes planning and preceding canonical chapters. Models select IDs from exact excerpts; the runner copies the quotation and hashes its source. Invalid IDs, absent quotes and malformed schemas are rejected. One informed correction is allowed. Invalid replies remain in project-local diagnostic history.
3. Supported arithmetic uses explicit source numbers and Decimal addition. A model selects the relationship; correct arithmetic does not prove its interpretation. Unsupported operands are rejected; there is no eval or external verification claim.
4. Writers receive at most 160 retrieved facts. The complete index remains on disk, candidate continuity checks use preceding evidence, and the final audit reads every canonical chapter. Retrieval is not exhaustive semantic recall.
5. A reader-approved candidate also receives a continuity check. One focused repair is followed by another blind-reader comparison and continuity check. A failed repair cannot replace the old canonical chapter. Blind readers never receive book-memory or revision-plan instructions.
6. Revision plans declare affected chapters; validated non-target chapters keep their files. Legacy plans without that field retain their full-book behavior. The next audit checks the complete changed manuscript and prior findings. Issue closure remains model-evaluated.
7. Repair campaigns persist their three-pass budget. Unchanged manuscript/report/connection combinations cannot repeat a completed no-progress pass. New guidance or a different editing connection starts another campaign. Historical drafts and exports remain intact.
8. `book-genesis studio` opens a local browser workspace over run_session. The loopback HTTP server authenticates actions and checks request origins. Model work runs on a worker; questions and activity use queues. Pause waits for a provider boundary. Claude public prose can stream; buffered connections display text after a response. Private reasoning is excluded. The earlier Tk implementation remains a separate module.
9. OS-owned locks prevent simultaneous guided sessions on a project and release on process termination. Chapter writes use atomic replacement. Lower-level legacy commands and external editors still require caller coordination.
10. Recovery distinguishes authentication, quota, configuration, permission, transient failures and unusable outputs. No silent provider switching or permission changes occur.
11. Metrics record task, connection/model, duration, first public text latency, character/word counts and outcome. They exclude prompts, responses, keys and raw errors. Metrics failure cannot replace a provider result.
12. Phase context excludes irrelevant artifacts. Complete manuscript access remains required for audit, score and packaging.

## Compatibility and limits

Legacy sequential fake-response and manual contracts do not automatically gain continuity calls. New contract tests supply that role explicitly. Live setup enables it automatically. Standalone callers must supply a continuity adapter to use the additional gate.

Studio uses installed CLIs or saved setup. Graphical API setup verifies the selected writing and reader models before accepting configuration; saving locally is optional. Explicit writing-model overrides leave reader selection intact. A PyInstaller specification builds a portable Windows directory, not a signed installer. Clean-machine testing remains separate.

The software cannot establish human literary acceptance, novice usability, full-length reliability, sales or virality by itself. The acceptance command reports mechanical evidence and leaves external release gates unverified.

## Validation

Offline tests cover provenance, source changes, extraction correction, arithmetic, blind-reader isolation, failed-repair preservation, targeted repair, recovery classification, telemetry redaction, pause boundaries and locking. Real-provider outputs retain failed attempts separately from fixtures. UI testing and repeated full-length cases remain release requirements.
