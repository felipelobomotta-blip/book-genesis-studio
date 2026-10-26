# Competitive mechanisms adopted into Book Genesis

This is an implementation map, not a claim of feature parity or superior books. The research is in `competitive-study-20261025.md` and its commit-pinned evidence manifest. No third-party implementation was copied or vendored: these are original implementations and editorial instructions informed by documented mechanisms. Commercial internal implementations were not available for inspection.

## What is in the candidate

- `editorial-method.md`: role-specific planning, drafting and revision method shared by native workflow and host skill references.
- `workflow_roles.py`: required `scene_contract`, `knowledge_boundary`, `arc_change` fields; existing independent plan verification now explicitly examines these fields.
- `editorial_context.py`: complete accepted-source index, hashes, literal previous-chapter handoff, explicitly provisional summaries. It does not extract a verified knowledge graph or discard complete prose.
- `repair_evidence.py`, group-review schema v3 and group manifest v4: select a source passage and a numbered literal span; the controller inserts exact quotes. Shared identical passages use lossless references while retaining distinct source/version IDs. Semantic correctness still requires review; source selection alone is not proof.
- `craft_context.py`: role-specific method injection, preserving score blindness and separation from blind readers.
- `launcher/activity.py`: read-only journal request/age/failure reporting through the existing `plugin_entry.py status` route. No new daemon or competing runtime.

## Every researched entry and its disposition

| Reference | Mechanism worth adopting | Book Genesis disposition |
|---|---|---|
| Nellie | One idea to complete deliverable; easy first result | Existing idea intake and Markdown/EPUB workflow retained. Exact new status observations improve legibility. Audio and generated covers are outside this writing-engine patch. |
| ImagineYourBook | Explicit creative constraints and consistent rewrites | Planning method preserves required/excluded events; existing author contract and simultaneous revision checks remain authoritative. Series-canon automation not newly implemented. |
| Sopher | Visible stages and coordinated chapter production | Existing sequential controller/heartbeat plus new status activity. No speculative parallel writing of dependent chapters. |
| Squibler | Chapter/scene scope and reusable character/context | New scene contracts plus existing character-card selection and ticket-scoped revision. No graphical editor claim. |
| BookBud | Sources before factual drafting; export gate | Source-before-claim instructions integrated; existing deterministic EPUB/export verification retained. No live OpenAlex/retrieval connector added; absent sources remain unverified. |
| AuthorMagic | Observable work, reviewable changes and production readiness | New status observations plus existing proposal, comparison and promotion receipts. The competitor was prelaunch at research time; no runtime feature-parity claim. |
| BookAutoAI | Deliverable-oriented book/package workflow | Existing manuscript/EPUB/editorial package retained. No claim of new KDP/PDF layout or sales-page generation. |
| DibblyCreate | Versioned edits and factual support | Existing immutable proposals plus source-bound selected-span evidence. Real-time collaboration and external fact lookup are separate unimplemented services. |
| WriteABookAI | Reader outcome and expertise as starting point | Shared planning method explicitly supports nonfiction reader problem, prerequisites, outcome and supplied evidence. Completion-rate advertising is not adopted as evidence. |
| Novelyn | Clear writing/revision/export states | Existing command routes with new activity detail and explicit export-versus-editorial distinction. |
| Sudowrite | Scene-first drafting and representative style samples | Required causal scene fields; two original samples at rest/under pressure in existing foundation voice artifact; role-specific drafting guidance. No Muse model or training claims. |
| Novelcrafter | Time-aware context/knowledge | New local knowledge-boundary field and accepted-chapter horizon/index; full prior prose retained. This is not a new verified temporal database. |
| NovelAI | Deliberate context activation | Existing character-card selection plus complete accepted-source view. Critical/distant facts are not pruned by recency. No new embedding service or lore engine. |
| Inkloom | Traceable context and fact states | Explicit provisional summaries versus accepted source, source hashes, existing raw request/response receipts. No claim that writer summaries are verified facts. |
| RedPencil | Separate source observation, inference and editorial judgment | Revision method requires those distinctions; selected source evidence leaves semantic support and uncertainty explicit. Simulated readers stay labelled as such. |
| NovLore | Recoverable versions and continuation | Existing checkpoints/immutable attempts preserved; read-only status tells the host what is saved. No beta-reader sharing service introduced. |
| Story Skills | Advisory pacing and state changes | `arc_change` and scene-contract review target repeated deferrals. No language-agnostic hard paragraph/beat quota. |
| Quill | Exact handoff and selective context | Literal prior tail and complete source index added. Full canonical prose remains available, avoiding unproven fixed summary caps. |
| Novel Writing | Proposed/inferred/confirmed distinctions and guarded updates | Existing hash-guarded staged publication; new source/provisional distinction and knowledge instructions. No second writable canon store. |
| Claude Book Skill | Author-corpus confidence and voice calibration | Foundation method labels original design versus evidence from supplied author samples, with distinct character samples. No Claude model calls required. |
| Calliope Writing Skills | Diagnosis before rewriting | Source/problem/reader effect/repair direction in revision instructions; existing review-only host path retained. No wholesale adoption of its augmentation-only product policy. |
| Oh Story DSH | Host owns account/session/tools; files own book state | Existing native plugin design retained. Status reads file state; no credential broker, second agent runtime or UI-owned hidden canon. |
| NovelNovel | Constrained identifiers with safe fallback | Source-scoped passage enums, locally bounded literal unit selection, fail-closed validation. No model-generated source IDs accepted. |
| DSH Tool Writing | Dynamic custody and relevant state | Knowledge-boundary/continuity method tracks acquisition, custody, event and disclosure separately. Existing all-prior-prose context avoids dropping old clues by a fixed recency cap. |
| Long Novel Agent Kit | Session/state fingerprints and proposals | Existing journal, hashes and compare-before-publication remain; legacy source review replay retained. No giant second CLI imported. |
| Snowflake Novel Writer | Progressive premise-to-scene expansion | Planning method plus required causal fields connects premise, character contradiction, scene choice, cost and arc movement. |
| Awesome Novel Skills | Baselines and repeated/blinded evaluation | Existing blind original/candidate comparison retained; validation records distinguish fixture, native transport and literary evidence. Catalog entries are not treated as tested products. |
| Book-writing-skill | Deterministic production checks | Existing EPUB structure/TOC/XML/word-count/current-source verification retained. Rendered PDF geometry is not implemented because this patch does not add a PDF renderer. |
| Yunn novel-writer | Arc checkpoints and precise continuation | Existing early/quarter/mid/late reader checkpoints plus literal handoff and arc-change field. Chinese-character thresholds are not applied to English fiction. |

## What still needs proof

The beta6 historical delivery remains 24 chapters / 83,517 words / 72.52 automated literary score. Changes here do not regrade it. Technical tests validate state, evidence, integration and packaging; a new blind native experiment and complete-book run must establish any literary benefit. Human reading and commercial results are separate evidence. No competitor's marketing claim substitutes for those tests.

The source-before-claim policy does not make unsourced nonfiction fact-checked. The continuity index is not a semantic knowledge validator. The status view is not process-liveness detection. Selected literal evidence removes transcription errors but cannot prove a critic's interpretation. These boundaries are intentional and tested where mechanical enforcement is possible.
