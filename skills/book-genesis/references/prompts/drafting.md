# Phase 3: Drafting

Draft in chapter blocks while preserving voice, momentum and structural variation. This restores the 5.0 drafting approach: fewer constraints while writing; evaluate and repair after the prose exists.

When to load: Phase 3. The writer drafts; the orchestrator handles persistence, checks and readers.

## The writer's packet

Assemble `work/briefs/chapter-NN.md` from the approved files:

- the premise, reader promise, point of view and time window;
- this chapter's outline entry, narrative purpose and planned word range;
- the relevant character and voice cards;
- only the continuity facts this chapter uses: current knowledge, location, object custody and any causal rule it depends on;
- the published story so far: every earlier chapter in order, plus the immediately
  previous chapter in full. A detail omitted from an earlier summary is still
  established on the page. Preserve names, dates, memories, transactions and
  custody from that source prose. Treat writer-reported summaries as provisional,
  and distinguish reader knowledge from each character's demonstrated knowledge.

The controlled runner supplies this history without lossy compression. This
increases native input with the length of the manuscript; it never silently drops
old source scenes to fit a context limit. The local chapter plan remains separate,
and no future planned chapter or critic report is added to the writer's history.

The orchestrator checks that these facts fit the approved brief before dispatch. Select the actual chapter-relevant facts; do not paste every character card, the complete outline or future continuity resolutions into each packet. Include the manuscript length range as production scope. Calculate a concrete remaining production allowance from the deterministic cumulative count, reserving the planned work of later chapters. The last chapter's upper allowance must fit the approved ceiling minus the words already accepted. Do not send the whole pipeline, audit history, reader verdicts, scores, thresholds or rubric. An evolving chapter may depart from the outline when it honors the author's constraints; record the resulting canon after the block.

Use the approved character-card text rather than asking the writer to reconstruct
motives from names and dialogue tics. The controlled runner selects named cards
for the local cast and POV. If a legacy foundation has no recognizable named-card
headings, it preserves the approved character file instead of silently dropping
it. Character arcs describe direction; they do not make future resolutions
current facts.

## Writing

Keep character behavior connected to desire, fear and contradiction. Keep the opening promise and ending pressure alive. Trust scene, image, pressure and voice; do not explain the craft move in the prose. Consecutive chapters may have different shapes. A quiet chapter can deepen character or atmosphere; it need not manufacture a cliffhanger or fit a rhythm quota.

Write before checking. Do not perform line-by-line anti-AI compliance or optimize sentences for a score. The craft and pattern references are available when useful, rather than another checklist inside the writer's packet.

## After a chapter block

The orchestrator, outside the writing context:

1. Saves the actual returned prose byte-for-byte through a staged attempt and reads it back before accepting it using `references/pipeline/host-contract.md`. Stage the extracted payload with `scripts/stage_chapter.py --source <extracted-prose.md> --output-dir <new-attempt-directory>` before copying to canonical. Its sole optional presentation transformation converts an initial H2-H6 to H1 while preserving the title and every body byte; it retains the unmodified source and records separate source, staged and body hashes. Do not spend a model retry on that heading-level defect. Other malformed or over-budget attempts still require a fresh explicit attempt within the retry bound; do not publish first, invent a missing heading or alter prose. Check the staged file's deterministic count fits the remaining production allowance, read it back and copy those exact staged bytes to the new canonical path. An existing accepted chapter is never silently overwritten.
2. Runs `scripts/check_progress.py`, updates actual chapters and prose counts from the report, and reruns it before continuing. Check the remaining length projection against the approved floor and ceiling; replan missing scene work before a large deficit accumulates. Do not pad.
3. Checks that the block has a narrative function, adds something the previous block did not, and keeps names, facts, voice and character knowledge consistent. A factual contradiction uses the bounded continuity path; literary changes wait for Phase 5.

## Reader checkpoints

Use four creative checkpoints: the opening, about 25 percent, about 50 percent, and before the final movement. At each, run the four simulated readers on the relevant chapter under `references/roles/panel.md`. Save their raw reports and original validation receipts using `references/pipeline/evidence.md`. A failed or stale read is not a vote.

Run each checkpoint when drafting reaches it, before dispatching the next chapter. Running all four after the complete manuscript exists is a retrospective read, not evidence that the checkpoints guided drafting.

At chapter 1, if fewer than three readers would turn the page, permit one staged revision against the supported defects and a complete comparison panel. Keep the accepted text unless the recorded promotion rule passes. In autonomous mode continue with the unresolved opening warning after that bound; never describe it as a passing panel.

Every five chapters and after the final chapter, update the continuity ledger and run its bounded factual check (`references/specialists/continuity.md`). This is a continuity checkpoint, not an additional mandatory literary panel. Combine coincident checkpoints. Preserve unresolved findings for the full audit rather than restarting the block.

## Finish the draft

Every planned chapter must exist, with a genuine ending and a read-back. Set the length gate to PASS within the approved range, FLAG within ten percent under the floor, or BLOCK farther under or above the ceiling. A short form must have been explicitly positioned from intake. Missing scenes, an unresolved ending or an unfinished novel are not repaired by changing the label to novella.
