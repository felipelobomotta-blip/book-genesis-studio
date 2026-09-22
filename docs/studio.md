# Writing Studio

The local visual workspace uses the same books, runner, checkpoints and exports as the command line.

```bash
book-genesis studio
book-genesis studio "books/my story"
```

Studio opens a local browser workspace bound to your computer's loopback interface. The browser interface does not require Tcl/Tk.

Installing this checkout also creates a `book-genesis-studio` desktop entry point (a windowed .exe launcher on Windows). It opens Studio without a terminal window. It is a Python application launcher, not a standalone bundled installer.

## Write a book

1. Add an idea and a language code such as en or pt.
2. Use saved connection setup or select an installed CLI. An optional writing model override applies to writing roles on that connection; it must be available in your provider account.
3. Test connection requests a short sample using your provider allowance. It verifies returned text, not book quality.
4. Begin your book creates a project in your library. Use Yes, continue, Pause here, or written guidance at the brief, outline, and chapter-one checkpoints.
5. Follow Live writing, Activity and the saved chapter list. Buffered providers deliver text after responding; Claude supports public prose streaming. Private reasoning and raw tool events are excluded.
6. Pause safely stops at the next provider boundary. The current call may take until its configured timeout. Close workspace requests cancellation, waits for the worker, and shuts down the server.
7. Reopen the book and Resume writing. Add guidance while idle before another repair pass. Download book exports EPUB or Markdown. A separately labeled working draft can recover saved unaccepted prose without promoting it to an accepted chapter.

Connection settings includes a request allowance, defaulting to 200 requests per writing session. Reviews and revisions count. Studio pauses before exceeding it; Resume starts a new allowance. This is not a currency or token spending cap.

Files stay local. Prompts and manuscript text go to the selected model provider. Studio does not silently change providers or grant tool permissions.

## Recovery

Temporary problems offer a retry. Authentication, allowance, model availability and tool-permission failures require a connection change or provider action. Select another connection or writing model before resuming. The local event journal preserves errors across restarts.

If a phase response cannot be parsed or lacks a required artifact, its full text is retained in the project's `work/phase-attempts/` directory. Agreeing to retry lets the model reuse the rejected response when it fits the retry context limit. Every required artifact must still pass validation before the phase advances. The saved response is never automatically treated as an accepted outline or manuscript.

For APIs or local model servers, expand Connect an API or a local model in Connection settings. Enter model names available in your account. Test and use this setup checks both writing and reader models before accepting the configuration. Leave Remember unchecked for session-only use. Remember stores the key in your local configuration file and replaces the active role setup. Cancelling prevents subsequent probes and saving once the current request returns.

Every repair must pass the checks. Three unsuccessful whole-book repair passes exhaust the saved campaign, including after application restart. Add specific guidance or choose another editing connection before a new campaign.

## Validation boundary

This is a beta interface. Scripted browser and controller tests verify mechanics, not literary quality or novice success. Actual novice sessions, independent human readers, reading-device checks and repeated full-length runs remain release requirements.

A portable Windows bundle can be built with packaging/book_genesis_studio.spec. Successful compilation alone does not establish clean-machine compatibility.
