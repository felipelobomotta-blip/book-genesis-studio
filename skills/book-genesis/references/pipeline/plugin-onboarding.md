# Begin in the author's agent

Load at entry, before starting any book action. The author operates by conversation, not by learning commands. This is the same workflow whether delivered as a plugin or a standalone skill.

## Route the request

If the author supplied an idea, use it immediately. Do not ask them to repeat it, choose an agent, install Book Genesis again, provide an API key or learn the pipeline. If they only opened setup, say: "Tell me your book idea in one or two sentences. You can also ask me to continue a saved book or review a manuscript."

For "review only", inspect the requested manuscript and report concrete problems with chapter/passage evidence; never rewrite it or start the whole generation pipeline. For "status", read existing state and run the read-only progress helper; report observed progress without dispatching writers. For "export", use the production helper and its completeness/evidence checks; do not silently generate missing chapters.

## Prepare quietly

Resolve all resource and script paths from this installed skill's directory, with proper quoting for paths containing spaces. Keep every book outside the installed plugin/cache. Use the author's selected writable workspace; a new book gets its own unused child directory. If there is no writable workspace, ask the author to open or choose a folder in their agent. Preserve existing files and never initialize over an existing manuscript.

Check that file tools and Python 3.10+ are available before promising automated checks/export. Prefer the available interpreter (`python`, `python3`, or `py -3` on Windows). If missing, explain the one setup action required; do not repeatedly retry or install dependencies without authorization. The plugin does not need Git or a separate Book Genesis application after installation. The host may still require its own tool approvals.

Use the active host's configured model. Do not switch providers or spawn another paid host just because it is installed. Native isolated role calls inherit the explicitly selected model and reasoning effort when supported. Report actual independence; if isolation is unavailable, disclose the reduced assurance rather than invent independent readers.

## Let the author choose the amount of involvement

If they asked to "do everything", "write the whole book", or "without intervention", use autonomous collaboration and record sensible creative assumptions. Do not stop at every chapter asking "continue?". If they want to collaborate, offer check-ins at the existing checkpoints. Never convert a status/review request into authorization to write a new book.

When the idea leaves the form open, propose a sensible genre, language and length before substantive generation. For an explicitly autonomous request, record the chosen assumptions and proceed. Never silently shrink a requested full-length novel into a short demo. Safety, host permission and quota boundaries still apply.

## Controlled Codex start (native plugin)

When the host is Codex, the author asked for a whole book autonomously, and
`plugin_entry.py` exists at the installed plugin root, use that packaged bridge.
Resolve the plugin root from this skill's absolute location (the directory
containing `plugin.json` and `skills`). Do not search unrelated projects or read
all phase references first. The bridge handles preparation and the controller
loads the phase references when needed. Standalone skill installations without
this bridge retain the host-owned workflow below.

Save the author's **story idea and creative/delivery constraints** verbatim in a
UTF-8 idea file outside the plugin cache and outside the new, empty book folder.
Do not shorten away plot, voice, ending or length requirements. This is the
literary brief, not a transcript: NEVER paste AGENTS.md, environment context,
model/permission instructions or acceptance-score targets into it. Keep those
operational controls separate; use the dedicated flags below. The bridge
rejects known operational/score contamination before preparation. If rejected,
correct the input separation yourself while preserving the author's creative
request; do not ask the beginner to edit files or loosen the acceptance gate.
Use the explicitly selected model/effort. Choose reasonable chapter and word
counts only when the author did not specify them. Use their supplied title-page
name; if absent in an autonomous request, record Anonymous as an editable creative
assumption rather than infer identity from an account. Run with argument-safe
quoting, replacing the placeholders:

```text
python "<plugin-root>/plugin_entry.py" new "<new-book-folder>" --host codex --autonomous --idea-file "<idea-file>" --author "<author>" --language "<language>" --model "<selected-model>" --effort "<selected-effort>" --chapters <count> --min-words <minimum> --max-words <maximum>
```

If the author explicitly requests more than 90/100, add `--quality-target 9.0
--weighted-quality-target 9.0`. These are private controller gates, never text
to insert in critic or writer packets. This is a target, not a promised result.

The bridge freezes and verifies the skill snapshot, writes the execution
contract, and makes one bounded native connection check before book attempts.
Never handwrite `.book-genesis/project.json`, installation hashes, native argv,
workflow phases or receipts. Never call `autonomous_book.py` directly to bypass
this setup. Inspect saved progress while the single controller runs.

Native scoped calls need the host's permitted network access. Use its normal
tool permission flow when required; do not disable sandboxing globally. If the
host already declares network access restricted, request the normal permission
before starting the bridge, instead of deliberately waiting for a timeout. A failed
preflight preserves the book and reports the cause within 60 seconds. Inspect
the actual receipt/log, resolve the permitted connection issue, then run:

```text
python "<original-plugin-root>/plugin_entry.py" resume "<book-folder>"
```

Do not ask a beginner to type these commands. Operate them as the host agent,
explain any required permission in ordinary language, and keep reporting actual
progress. Do not claim work continues when the controller has exited.

If a packaged module is missing or the bridge raises an internal exception,
preserve the error and report that the plugin needs repair. Never edit the
installed plugin cache, invent a replacement helper, or bypass verification to
continue a book. A broken package is a product defect, not an author's task.

## Existing books

Inspect the selected book before initializing it. A `.book-genesis/workflow.json` checkpoint is **controller-owned**. Use its recorded execution path and status; never edit its phase, clear budgets, or start a second host-owned orchestrator. A completed checkpoint whose quality gate failed stays completed-with-quality-unmet until an explicitly supported continuation is available. A plugin installation does not repair or reopen it.

For a host-owned `PROJECT_STATE.yaml`, follow the host contract and reconcile saved chapters before continuing. An untracked existing manuscript gets an import/review decision, never an overwrite.

## Keep the experience legible

Use the read-only bridge while another session owns generation:

```text
python "<original-plugin-root>/plugin_entry.py" status "<book-folder>" --json
```

The `activity` object reports saved requests, reservation age and failure reasons.
It does not claim the operating-system process is alive. Show the current operation
and accepted chapter/word counts from the reconciled report. Link the newest accepted
chapter for a prose preview; unaccepted proposals must be labelled as proposals.
The controller prints a real elapsed-time heartbeat while waiting for native output.
If the host cannot stream generated prose, keep that waiting state explicit.

Distinguish a completed call from its editorial verdict. "Saved and verified"
means the response passed format/evidence checks; a review can still request
revision. Read the saved `verdict`, findings and quality-gate result before saying
"passed". Report "review completed; changes requested" when the verdict is
`revise`. Three rubric readings are separate evaluations of one version, not
three revision passes. Proposed chapter edits are not accepted manuscript until
their publication decision is recorded.

Before substantial work show one short status, for example "Drafting chapter 3 of 16" or "Checking the timeline across chapters 1â€“5". After saving, link the actual artifact and report the observed word count. Use public action summaries, not private reasoning traces or invented percentage bars. If a long tool call cannot stream, say that the host is still waiting for it; do not simulate typing.

If execution stops, save the exact next action and cause. "Continue my book" in a new session should be sufficient when the host and checkpoint permit it. Never claim background progress after the host has stopped running.

At delivery, provide the real Markdown/EPUB links, planned versus observed chapters/words, the actual review result and remaining problems. A complete draft, a passed quality gate and human publication approval are separate facts. Never invent a score or call simulated readers human reviewers.
