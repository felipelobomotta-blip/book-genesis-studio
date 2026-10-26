# Beta 7 CI portability follow-up

Date: 2026-10-26. The beta7 runtime, package version, ZIP and tag are unchanged. This follow-up changes test fixtures only; no production guard is weakened to make CI green.

## Observed failures

The original release passed 658 tests on local Windows/Python 3.11.9. Its first GitHub matrix exposed platform assumptions in tests:

- Plugin-entry preparation tests tried to discover a real Codex executable on runners where it was absent, before reaching the mocked preflight. They now stub the native lookup as well as the authoring process; these tests cannot start inference.
- A Windows case-insensitivity test patched `os.name` but retained POSIX `os.path.normcase`. It now supplies `ntpath.normcase` for the simulated Windows behavior.
- macOS temporary folders use an alias under `/var`. Fixtures constructing incomplete workflows and build paths now resolve their root just as the real `BookWorkflow` does. The package's linked-directory guard stays intact.
- Windows CI also exposes temporary roots through an 8.3 alias; the same canonical-root correction handles it. A fixture simulating the Python 3.11 reparse-point fallback now explicitly disables the newer `os.path.isjunction` API during that simulation, including when running under Python 3.12.
- The POSIX process-tree fixture created a child without reaping it on SIGTERM. Its parent now waits for that child during group shutdown. The production launcher still retains its lock whenever shutdown cannot be verified, with its separate negative regression preserved.

Original failed jobs remain visible in the GitHub Actions history for release commit `b7b768b23d8ba679388bdf8ff4db8ea64d938fe1`. This report does not rewrite those outcomes. Corrected matrix results are recorded separately in the GitHub release's validation attachments.

## Distribution evidence

A clean Codex profile installed the published `v5.1.0-beta.7` tag and a clean short Claude profile installed the public repository, both reporting beta7 enabled. The initial Claude attempt in a long sandboxed temporary profile failed clone cleanup with EPERM and remains in local evidence. A separate retry in a short isolated profile outside the sandbox succeeded; the specific effect of path length versus sandboxing was not isolated.

The publicly downloaded ZIP is 616,795 bytes and matches SHA-256 `c39a97705224025fdc65d9bcc9586c55a9ddac6b3008a9221cf2132510f4774d`. Directory submission is prepared, not approved or submitted. None of these checks establishes a new beta7 full-book literary result.
