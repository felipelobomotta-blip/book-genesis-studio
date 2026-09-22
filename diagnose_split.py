"""Replay a saved phase response through the splitter. Deterministic, offline, fast.

Phase 2 failed twice on claude-opus-5 with two thirds of the paid response
discarded and only the last of the required files recovered. The runs that failed
predate the code that saves `response.txt`, so there was nothing to replay. This is
the loop to run the moment one exists — no provider call, no waiting 19 minutes per
attempt.

    python diagnose_split.py books/opus-medium-full/work/phase-attempts/phase_2_architecture/000003/response.txt
"""

import sys
from pathlib import Path

from runner.phases import _FILE_MARK, _STATE_MARK, split_files

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
files, state = split_files(text)

print(f"response: {len(text)} chars, {len(text.split())} words")
print(f"markers matched: {len(_FILE_MARK.findall(text))} FILE, {len(_STATE_MARK.findall(text))} STATE")
print(f"recovered: {sorted(files)}")
print(f"state keys: {sorted(state)}")

accounted = sum(len(body.split()) for body in files.values())
print(f"words recovered {accounted} of {len(text.split())} "
      f"({accounted * 100 // max(len(text.split()), 1)}%)")

# Where did the rest go? Anything before the first marker is lost silently, and a
# marker the regex nearly matched is the likeliest culprit for a whole missing file.
first = min([m.start() for m in _FILE_MARK.finditer(text)] or [len(text)])
if first:
    print(f"\n--- {len(text[:first].split())} words before the first matched marker ---")
    print(text[:first][:1500])

print("\n--- every line containing FILE, whether or not it matched ---")
for number, line in enumerate(text.splitlines(), 1):
    if "FILE" in line or "===" in line:
        matched = bool(_FILE_MARK.match(line) or _STATE_MARK.match(line))
        print(f"  {number:5} {'OK ' if matched else 'NO '} {line[:100]!r}")
