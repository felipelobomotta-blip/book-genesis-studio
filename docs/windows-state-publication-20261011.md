# Windows state publication recovery

Trial 28 on `49a7b8808a58bd65c063c9421f175d78e20e2fec` saved ten
chapters and 36,665 prose words. Immediately before its second continuity
check, replacing `.book-genesis/workflow.json` raised native `WinError 5`.
The CLI exited 1 with the current manuscript and original evidence preserved.
The later error-state save succeeded, supporting a transient failure rather
than an established permanent permissions defect. No complete book, revision,
export or numerical acceptance is claimed for that failed trial.

The exact source of the original blocking handle was not traced. A real Win32
reader that allows read/write sharing but excludes delete sharing reproduces
the same class of replacement denial. This is a normal status-reader or file
indexer interaction that a single-writer workflow must tolerate.

## Change

Prepare and fsync the replacement once. On Windows errors 5, 32 or 33, retry
the same atomic `os.replace` operation at most seven more times, with a total
delay of 0.76 seconds. Do not delete the current target, change permissions,
switch to an in-place write, regenerate model output or refund a role attempt.
Other filesystem errors remain immediate failures. Persistent denial preserves
the original file and surfaces the original error after the bounded retries.

Before retrying, verify the target's original file identity, size, modification
time and byte hash (or its original absence). A concurrent edit or newly
created target blocks publication and preserves that external work. Temporary
prepared bytes are cleaned up on failure as before. Model and revision budgets
are unchanged; these are OS replacement retries, not new generation attempts.

## Tests and scope

Five focused tests passed in 0.957 seconds. Two use real Windows file handles:
a temporary read handle reproduces denial and then releases for complete
atomic publication; a persistent handle fails within the bound without deleting
the current file. Three other tests preserve an external edit, preserve a new
external file and reject an unrelated filesystem failure without retrying it.

All 465 required automated tests passed in 455.795 seconds under normal Windows
filesystem permissions. The installer check also passed before the isolated
candidate was frozen for fresh native verification. Trial 28 remains
closed and unmodified. Trial 27 continues on its original source after its
authorized subscription reset; changing its installed code is not this fix.
This is a verified persistence fix, not literary evidence or a readiness claim.
