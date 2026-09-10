# A 30-day launch plan built around people finishing a first chapter

## Objective and positioning

Help a new user save a chapter they want to keep, return in a fresh session, and continue writing. That is the first useful adoption milestone. Stars and impressions help distribution but cannot establish that the product works for writers.

Core message: **Your creativity. Your agent. Your book.** The specific hook is: **Your coding agent can help you write a book.** The initial call to action is: “Try one chapter and tell me where the process breaks.”

Start with people who already use coding agents and have a story, guide, or nonfiction idea. They already understand installation and host accounts. Invite curious beginners into supported pilots next. Reach professional authors through actual manuscript examples and candid editorial feedback; do not lead with a promise to replace their craft.

Keep Book Genesis as the name for this campaign. Call the update “More agents, one writing workflow.” A new brand would add another recognition problem before the product has demonstrated retention.

## Which integrations deserve attention

The September 10 repository snapshot is in [baseline.json](baseline.json). GitHub stars are a dated attention proxy, not an active-user count or growth-rate ranking.

| Priority | Integration | Why test this audience | Evidence and limitation |
| --- | --- | --- | --- |
| 1 | DeepSeek Harness | New official harness gives the requested launch hook a concrete technical basis | [Official developer preview](https://www.deepseek.com/harness/en/) and [repository](https://github.com/deepseek-ai/deepseek-harness); 218,623 stars in the snapshot, created August 13, 2026. New install target, no fresh native book run. |
| 1 | Existing Claude Code and Codex users | Fits the project's existing workflow and the founder's experience | Audience-fit hypothesis, not a measured acquisition ranking. Record a current chapter/resume demonstration. |
| 2 | Pi and Qwen Code | Agent communities are plausible early testers of a portable skills package | [Pi](https://github.com/earendil-works/pi): 103,730 stars; [Qwen Code](https://github.com/QwenLM/qwen-code): 27,743 at the snapshot. Install targets added; native book acceptance remains open. |
| 2 | Cursor and GitHub Copilot | Reach people who prefer an editor or existing development workflow | Official skill support: [Cursor](https://cursor.com/docs/skills), [Copilot](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills). Reach is a hypothesis; local installation does not imply remote-agent setup. |
| 3 | Windsurf/Cascade, OpenCode, Antigravity, Gemini, Kimi, OpenClaw, Hermes | Useful choice and targeted community demonstrations | Keep a specific host setup page and evidence row. Prioritize requests from actual users over another logo. |

The next distribution experiment should be a verified, curated skills.sh package, not dozens of speculative wrappers. Its [directory](https://www.skills.sh/docs) is a relevant discovery channel for Agent Skills. Its install metrics come from its own CLI telemetry; our Python installations do not automatically count there. Test that only the canonical 15 skills and complete references are installed before advertising any new one-command marketplace instruction. No listing is claimed in this release.

## Proof gates before a broad launch

Use a small, clearly labeled writing pilot while these gates are open. Hold the broad Product Hunt/Show HN push until they pass.

- A clean machine or clean profile can follow the README without the founder fixing files manually.
- Ten external users attempt the same first-chapter journey; at least eight save a non-template chapter and resume correctly in a fresh session. Record all attempts, including failures. This small pilot is a usability screen, not a population reliability estimate.
- No observed lost or overwritten manuscript content remains unresolved. Stop promotion and investigate a data-loss report immediately.
- Record one complete short-book run with target length, actual word count, chapter count, review, revision, timing, host/model, and interruptions. Label it a short book; do not imply full-length reliability from it.
- Two independent humans read a permitted sample without being shown an internal model score. Ask what they remember, where they stopped, and what would make them continue. Report mixed feedback as mixed feedback.
- Publish a real installation-to-artifact walkthrough and its limits. Any cut around a wait must be labeled. Record the chapter/resume segment before claiming it in post copy.

Passing these gates supports a credible skills launch. A separate repeated full-length manuscript benchmark is still needed before promising dependable full-length production.

## Thirty days, in four phases

**Days 1–7: make the proof easy to inspect.** Capture a current host demonstration, recruit ten willing pilot users, observe installation and resume, fix the biggest common blocker, and finish the sample short book. Have readers assess the sample. Produce one 3–5 minute walkthrough, one 60-second cut, and three real screenshots. If the pilot fails, repeat the failed journey before buying reach or scheduling a large launch.

**Days 8–14: learn which message brings writers.** Post the founder story on LinkedIn, show the real workflow on X, publish the walkthrough on YouTube, and adapt two short clips for Shorts/Reels/TikTok. Answer questions personally. Publish a technical explanation on DEV. Share in at most one or two relevant communities after checking their rules. Ask users which agent they use and whether they reached a saved chapter.

**Days 15–21: broaden only after the proof gate.** Prepare Product Hunt and let the founder write a Show HN submission independently. Send up to five relevant, personalized creator invitations during the week where contact is welcome. Publish a host tutorial requested by pilot users and an example of a revision improving a specific paragraph. Do not repost the same launch everywhere at once; leave time to support each audience.

**Days 22–30: make user outcomes the story.** Share permitted author examples, review second-session usage, improve the largest remaining friction point, publish a candid month-one report, and decide which two channels and hosts deserve another month. Keep all calendar entries conditional on evidence; missing a date is preferable to promoting an unverified workflow.

The [calendar](calendar.csv) provides one concrete action and completion criterion per day. Suggested daily time budget: 40 minutes supporting users, 30 minutes producing or adapting one asset, and 20 minutes collecting feedback and metrics. Reserve separate development time for fixes. If support exceeds capacity, reduce posting frequency.

## Channel execution

| Channel | What to publish | Initial cadence | Action to request |
| --- | --- | --- | --- |
| GitHub | Clear install guide, evidence table, sample, concise release note; issues for actual problems | One release/update per meaningful change | Try a chapter; include host and reproduction steps in feedback |
| X | Actual clip, founder notes, a failed attempt and fix, host-specific walkthrough | Three useful posts a week; one thread in launch week | Try it with an existing agent |
| LinkedIn | Founder story, what simplification changed, permitted user result | Two posts a week | Share the book idea or report setup friction |
| YouTube | Searchable 3–5 minute tutorial and measured follow-up | One walkthrough, then one evidence-based follow-up | Follow the README and attempt the same journey |
| Shorts / Reels / TikTok | Native vertical cuts of the real demo; readable captions | Two distinct clips a week, adapted per platform | Visit the profile/repository link where supported |
| DEV | Technical article on portable skills, saved state, and honest evaluation | One substantial article, update after feedback | Inspect the repo and test a host |
| Reddit / agent communities | A useful host-specific demonstration and frank limitations | One or two relevant communities initially | Feedback on the specific workflow |
| Product Hunt | Working package, real screenshots, maker comment, walkthrough | One launch when the gate passes | Try the product and give feedback |
| Hacker News | Founder-written account of the working project and technical tradeoffs | One appropriate submission after the gate | Let readers explore and discuss naturally |

Community candidates include agent-specific forums, r/LocalLLaMA, r/SideProject, and r/opensource. This is a research shortlist, not confirmation that a promotional post is allowed. Check the current community rules and recent moderator guidance before writing or posting; Reddit's [spam policy](https://support.reddithelp.com/hc/en-us/articles/360043504051-Spam) does not grant a universal self-promotion allowance. Participate where the project answers a real question.

Product Hunt supports maker submissions and recommends preparation around a real product; ask for feedback rather than votes. Its product URL should be the direct project URL, without a shortened or tracking link. See the [launch guide](https://www.producthunt.com/launch/preparing-for-launch). Do not purchase votes or pay someone for a promised ranking.

Hacker News prohibits generated or AI-edited post text. This kit deliberately supplies no HN submission draft. The founder must write that submission and replies independently, after reading the [guidelines](https://news.ycombinator.com/newsguidelines.html) and [Show HN requirements](https://news.ycombinator.com/showhn.html). Do not request coordinated votes or comments.

## A sharing loop worth earning

One person has an idea, saves a chapter, improves a weak passage, and chooses to show that result. Link the permitted result to a reproducible host setup. A second person recognizes their own idea in the process and tries it. The shareable object is an author's outcome, not an internal score badge.

Offer an optional “Made with Book Genesis” credit and a short case-study format: idea, host/model, version, sample excerpt, what the author changed, what still needs editing, and link. Never insert promotional text into someone's manuscript without their choice. Obtain permission for excerpts, names, images, and testimonials; allow anonymous feedback. Keep private manuscripts and participant-level tracking outside the public repository.

For creators, select people who already teach a supported agent or document writing workflows. Score relevance, quality of actual demos, engaged discussion, and whether they welcome submissions. Five carefully chosen invitations are more useful than a mass mailing. Offer a reproducible example and invite criticism; do not request praise or a paid endorsement disguised as a review. Outreach copy is in the [platform kit](platform-copy.md); nothing has been sent.

## Measurement and decisions

The repository snapshot started at **114 stars and 38 forks**. We have no measured install count, activated-author count, or retention baseline. Leave unknowns blank in [metrics.csv](metrics.csv); never turn unknown into zero or infer installations from stars.

The funnel is: platform impressions → project visits → reported install attempts → a saved first chapter → a successful fresh-session resume → use again at least seven days later → an optional public share. Record unique consenting pilot participants privately, not their manuscripts. Publish only aggregates. Count “activated” only after both chapter and fresh-session resume are confirmed by participant feedback or a permitted observation.

Use native platform analytics for impressions, views, watch time, profile visits, and clicks when available. Record missing data as unavailable. Ask an optional “Where did you hear about this?” question for attribution. GitHub query strings alone do not give campaign analytics. If a measured landing page is introduced later, disclose its analytics and use consistent campaign tags there; do not invent attribution from the current repository.

**Thirty-day planning targets, not forecasts:** 10 observed pilot attempts with 8 successful chapter/resume journeys; 30 total activated projects; 10 users who return after at least seven days; 5 permission-based examples. A stretch goal of 300 repository stars is secondary. Missing a star target with good retention can still justify continuing.

Test two hooks: A, “Your coding agent can help you write a book”; B, “What if that idea became a chapter?” Use comparable clips and equal observation windows. Log impressions and attributed attempts where available. With very small samples, treat differences as leads to investigate, not statistical proof. After at least 10 attributable install attempts per hook, prioritize the one producing more successful chapter/resume journeys per attempt, while checking support burden. If both fail activation, fix onboarding rather than rewriting the headline again.

Review weekly: which host attracts attempts, where users stop, which channel produces return users, and which content answers repeated questions. Keep two productive channels; pause channels that consume support time without bringing people who write. Start with no paid advertising. Consider a small, explicitly budgeted test only after activation and retention are observable.

## The founder's next five actions

1. Record one real chapter/resume demonstration on a host with verified access.
2. Observe ten pilot attempts and publish the aggregate result, including failures.
3. Post the founder story and demo with a single invitation to try a chapter.
4. Turn the most common failure into the next product fix and public update.
5. Expand the campaign after the evidence gate; let real author outcomes introduce the project.
