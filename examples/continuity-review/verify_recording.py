"""Check the saved demo's evidence. No model call or new literary evaluation."""

from hashlib import sha256
import json
from pathlib import Path
import re
import sys


def paragraphs(text: str) -> dict[tuple[int, int], str]:
    result = {}
    parts = re.split(r"^## Chapter (\d+)\s*$", text, flags=re.MULTILINE)
    for index in range(1, len(parts), 2):
        chapter = int(parts[index])
        blocks = [block.strip() for block in parts[index + 1].strip().split("\n\n") if block.strip()]
        result.update({(chapter, number): block for number, block in enumerate(blocks, 1)})
    return result


def verify(root: Path) -> list[str]:
    run = json.loads((root / "recorded/run.json").read_text(encoding="utf-8"))
    errors = []
    for name, record in run["files"].items():
        text = (root / name).read_text(encoding="utf-8")
        if sha256(text.encode("utf-8")).hexdigest() != record["normalized_sha256"]:
            errors.append(f"{name}: canonical sample content changed")
        if record["before_sha256"] != record["after_sha256"]:
            errors.append(f"{name}: recorded before/after hashes differ")
        report = json.loads((root / "recorded" / record["report"]).read_text(encoding="utf-8"))
        locations = paragraphs(text)
        findings = report["findings"]
        if name == "sample-a.md":
            if len(findings) != 1 or findings[0]["severity"] != "high":
                errors.append("sample-a.md: recording does not contain the expected one high finding")
            if findings and {item["chapter"] for item in findings[0]["evidence"]} != {1, 2, 3}:
                errors.append("sample-a.md: evidence does not cover the knowledge path")
        elif findings:
            errors.append("sample-b.md: the control recording contains a finding")
        for finding in findings:
            for item in finding["evidence"]:
                location = (item["chapter"], item["paragraph"])
                quote = item["quote"]
                if not quote or quote not in locations.get(location, ""):
                    errors.append(f"{name}: quote does not match chapter {location[0]}, paragraph {location[1]}")
    return errors


if __name__ == "__main__":
    try:
        failures = verify(Path(__file__).resolve().parent)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        failures = [str(exc)]
    if failures:
        print("Recording verification FAILED:")
        for failure in failures:
            print(f"- {failure}")
        sys.exit(1)
    print("PASS: sample contents, saved before/after hashes and all quoted locations match.")
    print("Recorded outcome: one high finding in sample A; no finding in control B.")
    print("This checks saved evidence. It does not run a model or measure detection accuracy.")
