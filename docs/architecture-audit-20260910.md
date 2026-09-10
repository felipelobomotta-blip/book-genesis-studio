# Architecture and orchestration audit

## Decision

Keep one portable editorial core. The host owns model execution, authentication, tools, and user interaction; Book Genesis owns the manuscript workflow and its files. Adding a platform means adding its discovery path, not cloning the prompts or writing another model bridge. The Python helper remains optional and uses the standard library.

The review covered the installer, CLI, file helper, phase manifest, evaluator protocol, core orchestration instructions, and specialist dispatch. It was a focused reliability review, not an independent security certification or a comparative product benchmark.

## Fixed weaknesses

| Observed weakness | Change and evidence |
| --- | --- |
| A `.md` filename alone satisfied the drafting gate | Empty, heading-only, and template chapters now block; regression verifies state remains unchanged |
| Recorded length/chapter plans were not checked by the helper | Advancement from drafting onward checks saved floors and planned chapter coverage against files |
| Moving the state directly to scoring could skip earlier gates | Advancement checks prerequisite gates and retains the required audit artifact |
| State advancement performed several separate writes | Validate all addressed keys first, then atomically replace one flushed state snapshot; injected replacement failure preserves the previous snapshot |
| Duplicate `status` names depended on section order | Reads and writes target the intended project/runtime/pipeline/gates section; reordered-state regression protects manuscript status |
| Multiline input could break the generated YAML scalar | JSON-compatible escaping preserves quotes, newlines, and backslashes |
| Skill installation could overlap its source tree | Refuse identical, parent, or child source/destination overlaps before writing |
| Installed files had no user-facing integrity check | `verify-install` detects missing skills, missing/changed references, and invalid installation records |
| Skills-only hosts lacked an explicit startup/recovery contract | Bundle initial project state, path-resolution instructions, ownership, public progress, bounded retries, and recovery rules |
| Offline market planning was presented as verified evidence in a live test | Require source dates/links or explicit unverified hypotheses; research remains pending without access |

## Orchestration boundaries

One orchestrator owns state and each chapter has one active writer/editor. Independent work may run in parallel only when supported. Writer, critic, and editor remain separate roles; actual context isolation is recorded instead of inferred from role names. Unsupported delegation falls back to sequential work with diagnostic-only evaluation. File completion and editorial approval are distinct.

The host contract caps retries, preserves prior revisions, asks for simple recovery choices, and requires actual artifact inspection before reporting progress. This is an instruction contract: the host must follow it. The optional helper enforces mechanical checks when used; installing skills cannot compel an arbitrary model to comply.

## Remaining limits

- The state helper accepts the bundled two-space mapping layout; it is not a general-purpose YAML engine. Preserve that layout when using helper commands.
- State replacement is atomic, but it is not a multi-writer database or distributed lock. Do not run concurrent orchestrators on one book.
- The installer stages and backs up each changed skill. The entire multi-skill update is not one transaction; a disk failure may leave a partial update. Rerun after fixing the underlying error and check `verify-install` before starting a host session.
- Word counting is whitespace-based and excludes Markdown headings. It is a mechanical approximation, unsuitable as a universal linguistic tokenizer.
- File existence, length, and recorded gates do not establish factual accuracy, literary merit, genuine evaluator isolation, or sales.
- No measured competitor comparison supports a claim of best architecture, lowest cost, fastest generation, or universal complete-book reliability.

The practical acceptance target is reproducible: install cleanly, discover the complete bundle, initialize a project, save real chapters, resume in a fresh session, handle failures without losing work, and produce evidence-backed editorial reports. [Host compatibility evidence](compatibility.md) records which parts have actually been exercised.
