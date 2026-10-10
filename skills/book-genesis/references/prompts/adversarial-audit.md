# Phase 4: Adversarial Audit

Break the system's bias toward approving itself before anything is scored: one skeptical, read-only audit of the whole manuscript.

When to load: Phase 4, and in Phase 5 when a pass needs a fresh audit. Role: orchestrator runs the auditor.

## Run the auditor

1. Build the auditor's packet exactly as `references/roles/auditor.md` lists: all chapters, the approved intake brief, the plan files, and the pattern standards. No targets, no scores, no panel verdicts. The auditor's first pass is the dedicated brief contract comparison; it must compare the intake premise, reader promise, declared time window or duration, and point of view with every planned chapter, the ledger timeline/world rules, and the manuscript even when the ledger is internally consistent.
2. Run it at the strongest independence level recorded in `PROJECT_STATE.yaml` (`references/scoring/evaluator-protocol.md`).
3. Save its report verbatim to `artifacts/10-adversarial-audit.md`. A read-only auditor returns the report; you save it.

For a mechanism-driven story, reconstruct the decisive causal chain from the
prose and inspect repeated middle-book explanations under
`references/specialists/causality.md`. Do not let knowledge available only in
the plan fill a gap on the page. Keep deliberate ambiguity distinct from a
contradiction, and quote the actual passages before making a ticket.

## Act on the verdict

The report ends with one `audit_status` line.

- `audit_status: pass`: set the gate to passed and move to Phase 5, which still runs its two gates. This is valid only when the brief contract check and all ten other passes have no open high-severity ticket.
- `audit_status: revise`: set the gate to `revise` and move to Phase 5 with the tickets as its first work.
- `audit_status: major_rewrite`: preserve that verdict and every blocker. In check-in mode, show the failing passes and offer three paths: re-architect the affected part, revise the existing structure, or stop; record the author's choice in `decisions`. In autonomous mode, choose a bounded repair of the existing book and continue to Phase 5 without asking the author to approve this routine editorial choice. Record it as an autonomous policy decision, not a new author approval. If linked scenes or mechanics need replanning, include that focused plan in `evaluations/revision-plan.md`; preserve the approved premise, viewpoint, time window, chapter/length contract and original manuscript. Use the existing three-pass revision budget, never a new or reset loop. Require fresh audit evidence before closing any high-severity ticket. If the budget cannot produce a compliant repair, retain the failed verdict and continue the documented autonomous path to an honestly labeled draft delivery; do not invent a pass or silently change the author's constraints. A genuinely missing input, denied permission, quota failure or incomplete manuscript still follows the host's explicit blocked-delivery path.

A strong panel result never overrides the audit. The audit judges the manuscript as a whole; the panel judges whether readers keep going.
