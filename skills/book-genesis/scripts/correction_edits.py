"""Source-bound correction spans; a model supplies new text, never the baseline."""
from __future__ import annotations

import re


def retains_title(original, proposed):
    """Allow only the same title, or removal of a redundant Chapter N: label."""
    if original == proposed:
        return True
    match = re.fullmatch(r"(?i:chapter)[ \t]+([^:\n]+):[ \t]+(\S.*)", original)
    if not match or proposed != match[2]:
        return False
    number = match[1].lower()
    units = "one two three four five six seven eight nine".split()
    words = set(units + "ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen one hundred".split())
    tens = "twenty thirty forty fifty sixty seventy eighty ninety".split()
    words.update(tens)
    words.update(f"{ten}{join}{unit}" for ten in tens for join in (" ", "-") for unit in units)
    return bool(re.fullmatch(r"[0-9]{1,3}|[ivxlcdm]+", number)) or number in words or number == "one hundred"


def source_passages(original):
    """Give immutable positions to the heading and paragraphs, preserving gaps."""
    first = original.find("\n")
    first = len(original) if first < 0 else first
    boundaries = [(0, first)]
    start = min(first + 1, len(original))
    for separator in re.finditer(r"\r?\n[ \t]*\r?\n", original[start:]):
        end = min(first + 1, len(original)) + separator.start()
        boundaries.append((start, end))
        start = min(first + 1, len(original)) + separator.end()
    boundaries.append((start, len(original)))
    passages = []
    for start, end in boundaries:
        block = original[start:end]
        if not block.strip():
            continue
        left = start + len(block) - len(block.lstrip())
        right = start + len(block.rstrip())
        passages.append({"id": f"p{len(passages) + 1:04d}", "text": original[left:right], "start": left, "end": right})
    return passages


def correction_schema(original, *, allow_unchanged=False):
    ids = [row["id"] for row in source_passages(original)]
    fields = {"from_passage": {"type": "string", "enum": ids},
              "through_passage": {"type": "string", "enum": ids}, "after": {"type": "string"}}
    return {"type": "object", "properties": {"corrections": {"type": "array", "minItems": 0 if allow_unchanged else 1, "maxItems": len(ids),
            "items": {"type": "object", "properties": fields, "required": list(fields), "additionalProperties": False}}},
            "required": ["corrections"], "additionalProperties": False}


def apply_passage_corrections(original, corrections, *, allow_unchanged=False):
    passages = {row["id"]: row for row in source_passages(original)}
    spans = []
    for correction in corrections:
        try:
            first, last = passages[correction["from_passage"]], passages[correction["through_passage"]]
        except KeyError as exc:
            raise ValueError("Correction names a passage outside the frozen chapter") from exc
        if first["start"] > last["start"]:
            raise ValueError("Correction passage range is reversed")
        after = correction["after"]
        if not isinstance(after, str) or not after.strip():
            raise ValueError("Factual corrections cannot remove a whole source passage")
        spans.append((first["start"], last["end"], after))
    spans.sort()
    if any(left[1] > right[0] for left, right in zip(spans, spans[1:])):
        raise ValueError("Correction passage ranges overlap")
    candidate = original
    for start, end, after in reversed(spans):
        candidate = candidate[:start] + after + candidate[end:]
    if candidate == original and not allow_unchanged:
        raise ValueError("No substantive correction; the accepted chapter is unchanged")
    if (not candidate.startswith("# ") or not original.startswith("# ")
            or not retains_title(original.splitlines()[0][2:], candidate.splitlines()[0][2:])):
        raise ValueError("Factual corrections must retain the title; only a redundant Chapter N: label may be removed")
    return candidate
