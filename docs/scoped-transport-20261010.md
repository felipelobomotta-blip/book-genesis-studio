# Prepared native role commands

The native checkpoint replay exposed a transport failure before editorial work: the orchestrator reconstructed the interactive Codex command for piped reviewer calls. It tried unsupported flags, passed supported flags to the wrong parser, invoked a terminal-only mode without a terminal, and carried the book directory into a context intended to start elsewhere. Removing structured output did not address the cause.

The launcher now saves a separate `scoped_command` in each new Codex launch receipt. It reuses the exact resolved executable prefix and explicitly selected model and effort, with `exec`, read-only mode, ordinary native approvals, stdin input and a dedicated response file. It does not copy interactive terminal flags or override the guard's fresh working directory. The orchestrator gives `run_host_call.py` the launch receipt rather than inventing another command.

`--output-schema` adds an existing JSON object schema inside the book folder. `--timeout-seconds` allows a bounded canary. Old receipts without the prepared command fail with a clear instruction to use an explicitly verified command; they are not silently rewritten. Other hosts retain their existing call contract. This change neither obtains credentials nor changes native account configuration.

## Live transport checks

Before the calls, the experiment declared two trials, zero retries, and a 60-second timeout per trial. Both used the actual CLI and the production command builder and guard. A clearly labelled synthetic launch-record fixture supplied the recipe; it was not an interactive launcher session. Separate automated integration tests verify that a real launcher invocation records the same executable prefix and explicit model/effort.

| Trial | Actual result | Duration | Response SHA-256 |
| --- | --- | --- | --- |
| Plain response | `READY`, first call | 13.159 seconds | `c2e3ac47f4a325469c1a2d5f117e463ec943c721986d5d9f09ac4540b7d80526` |
| Structured response | `{"ready":true}`, first call | 10.014 seconds | `b342fc286d0216cc212e0d7ba234894e2e7283ddf14f959adf0fe7fd5924308a` |

Both CLI headers reported Codex 0.156.1, `gpt-5.6-luna`, high effort, read-only mode and `on-request` approvals. Both ran in different temporary directories outside the book. Packet, response, stdout and stderr hashes matched their original receipts. No active scoped-call lock remained. The calls used normal approved network access; restricted-network behavior is not a successful transport check.

Installer verification passed, and the complete Windows suite passed **268 tests in 109.454 seconds**. The five added tests exercise actual subprocess piping, schema forwarding, invalid recipes and schema locations, unchanged saved commands, timeout validation, and launcher-to-receipt wiring. They use process fixtures, not literary evidence.

These results establish two real transport calls and the specified integration behavior. They do not establish model quality, complete-book reliability, human reader approval or a 90/100 product rating. The ongoing repair replay retains its frozen earlier skill snapshot and is assessed separately; it has not been silently upgraded by this code change.
