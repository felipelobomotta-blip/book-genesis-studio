"""Group dense short paragraphs for review without selecting or rewriting prose."""
from __future__ import annotations

import re


def evidence_passages(text: str, *, separator: str = r"\n[ \t]*\n") -> list[str]:
    """Keep small catalogs unchanged; bound citation overhead in dense ones.

    Each block is an exact contiguous substring of the supplied visible text.
    All nonempty paragraphs occur once, in their original order. Headings and
    an individually long paragraph remain separate. There is no summarization,
    truncation, paragraph reflow, or change to the source file or its hash.
    """
    visible = text.strip()
    boundaries = list(re.finditer(separator, visible))
    starts = [0] + [match.end() for match in boundaries]
    ends = [match.start() for match in boundaries] + [len(visible)]
    spans = [(start, end) for start, end in zip(starts, ends)
             if visible[start:end].strip()]
    if len(spans) <= 128:
        return [visible[start:end] for start, end in spans]

    blocks = []
    block_start = block_end = None
    words = 0

    def flush():
        nonlocal block_start, block_end, words
        if block_start is not None:
            blocks.append(visible[block_start:block_end])
        block_start = block_end = None
        words = 0

    for start, end in spans:
        paragraph = visible[start:end]
        count = len(paragraph.split())
        if re.match(r"\s*#{1,6}\s", paragraph):
            flush()
            blocks.append(paragraph)
            continue
        if block_start is not None and (words + count > 320 or end - block_start > 2400):
            flush()
        if block_start is None:
            block_start = start
        block_end = end
        words += count
    flush()
    return blocks
