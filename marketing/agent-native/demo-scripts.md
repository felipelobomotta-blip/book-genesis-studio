# Record a real demonstration

Status: recording scripts and shot list. No video has been produced by this kit. Historical videos in the repository may show a different product version.

## Prepare the capture

Use a clean, writable demonstration folder and a host you can actually access. Record the commit, OS, host/version, model if known, and whether this is a subscription or other model setup. Hide credentials and personal paths. Show readable text at normal playback size; a terminal at 150% or larger is better than an unreadable full desktop.

Use a fictional idea that is safe to publish:

> Use the book-genesis skill. Write in English. My idea is a mystery about a retired train dispatcher who finds a farewell letter inside a station clock. Help me choose a direction and make a three-chapter short story, aiming for about 1,000 words per chapter. Save the project state and artifacts. Start with the intake and ask me about the major creative decisions.

This is a **short-story demonstration**, not a full-length book benchmark. Use a separate, appropriately sized run for any complete-book claim.

Capture the real commands, selecting the tested target:

```bash
git clone https://github.com/felipelobomotta-blip/book-genesis-v4.git
cd book-genesis-v4
python runner/installer.py verify-suite
python runner/installer.py install deepseek
python runner/installer.py verify-install deepseek
```

The example names DeepSeek because it is the new integration; it must be exercised natively before using DeepSeek footage or claiming a successful writing run. Select another verified host for the first recording if necessary. The installer cannot prove native writing by itself.

## Sixty-second cut

| Time | Picture | Suggested narration |
| --- | --- | --- |
| 0–5s | Idea on screen, then the chosen real agent | “You already have an AI agent. What if you used it to work on your book idea?” |
| 5–13s | Actual install and verification result; host name visible | “Book Genesis adds a writing workflow to the agent you already use.” |
| 13–24s | Paste the idea; show one actual creative decision | “Start with your idea. Choose the direction.” |
| 24–37s | Actual saved outline and chapter file | “Develop the outline and save the writing in your project.” |
| 37–47s | A concrete editorial criticism and the resulting changed passage | “Then read critically and revise the parts that need work.” |
| 47–55s | Fresh host session reads the saved state and identifies next step | “Here is the project continuing in a new session.” |
| 55–60s | Repository URL and simple call to action | “It's open source. Try a chapter and help me improve it.” |

Only use the review and recovery lines if the recording actually demonstrates them. Capture long waits normally, then label shortened sections “edited for time” and display actual elapsed time in the description. Do not invent token streams, agent activity, reader reactions, or hidden reasoning. Visible host status and actual writing are sufficient.

If only intake succeeds, publish a clearly titled intake demonstration and report the unfinished part. Do not assemble unrelated outputs into an apparent uninterrupted success.

## Three-to-five-minute walkthrough

1. **0:00–0:25:** Show what the package is, the target host/version, and the limited demo goal.
2. **0:25–1:05:** Install, verify, and confirm the host discovered the skill. Explain prerequisites in one sentence.
3. **1:05–1:50:** Start from the sample idea and show one meaningful choice the author makes.
4. **1:50–2:40:** Open the real outline and chapter file. Show where they are saved. Include actual elapsed writing time as an overlay.
5. **2:40–3:25:** Show one weakness found during review and the specific revision. Do not present a model score as reader approval.
6. **3:25–4:15:** End the session, begin another in the same folder, and ask it to read state and continue. Keep the evidence of the new session visible.
7. **4:15–4:45:** Explain any failure, quota, permission prompt, or unresolved issue. Invite a first-chapter test and link the host evidence table.

Suggested capture formats: a 1920×1080 horizontal master and a separately framed 1080×1920 vertical cut. These are production choices, not mandatory platform limits. Add accurate captions. Keep keyboard text and manuscript excerpts large enough to read.

## Acceptance record

Before uploading, record the tested commit; host/version; date; goal; actual files; word count; elapsed time; whether installation, chapter saving, and fresh-session recovery succeeded; what was edited out; and the exact public URL after upload. Obtain permission for anything written by a tester. Leave failed steps in the evidence record even if the shorter clip focuses on the working section.

Required screenshots: actual installation result, saved chapter beside project files, and fresh-session state recovery. Product Hunt needs its own correctly sized gallery assets; check its current preparation guide before export. This kit's carousel is copy only until those visuals are made.
