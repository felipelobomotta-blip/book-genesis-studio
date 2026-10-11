"""Keep numeric evaluation commentary out of authoring handoffs.

Original critic responses remain immutable evidence. This makes a separate
editor-facing view; it never changes scores or cleans manuscript/contract text.
"""
from __future__ import annotations

import re


_NUMBER = r"(?<![\w.])(?:100|[1-9]?\d)(?:[.,]\d+)?(?!\w|[.,]\d)"
_RATING = re.compile(
    rf"{_NUMBER}\s*(?:/\s*(?:10|100)\b|out\s+of\s+(?:10|100)\b)", re.I)
_EVALUATION = re.compile(
    r"\b(?:scores?|scored|scoring|ratings?|rated|rubric|calibrat\w*|"
    r"grade[sd]?|notas?|pontua\w*|"
    r"(?:prose|pacing|coherence|voice|opening|theme|market|emotion|characters?|originality)"
    r"\s+(?:cap|floor|ceiling|threshold)|"
    r"(?:cap|floor|ceiling)\s+(?:of|at|is|was|applies|applied)|"
    r"teto\s+(?:de|da\s+prosa)|piso\s+de)\b", re.I)
_DIGIT = re.compile(_NUMBER)


def score_blind(value):
    """Remove scored sentences, retaining adjacent observations and locations.

    Chapters, dates, prices and observation counts alone are not scores. Match
    explicit rating notation or evaluation language and a number together.
    This is a conservative textual boundary, not a semantic classifier.
    """
    if isinstance(value, dict):
        # Quoted source prose is evidence, even when a character mentions a
        # grade or sports score. Only editorial commentary is filtered.
        return {key: item if key in {"text", "quote"} else score_blind(item) for key, item in value.items()}
    if isinstance(value, list):
        return [score_blind(item) for item in value]
    if not isinstance(value, str):
        return value
    parts = re.split(r"(?<=[.!?])\s+|\n+", value)
    kept = [part for part in parts if not (
        _RATING.search(part) or (_EVALUATION.search(part) and _DIGIT.search(part)))]
    return " ".join(kept) if len(kept) != len(parts) else value
