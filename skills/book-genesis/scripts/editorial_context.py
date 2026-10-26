"""Read-only role views over existing source files; no second canon database."""
import copy
import re

from evidence_passages import evidence_passages
from workflow_state import digest


def method_section(skill, section):
    if section not in {'Planning', 'Drafting', 'Revision'}:
        raise ValueError('Unknown editorial role section')
    text = (skill / 'references/specialists/editorial-method.md').read_text(encoding='utf-8')
    match = re.search(r'^## ' + re.escape(section) + r'\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    if not match:
        raise ValueError('Missing editorial role section')
    return match[1].strip()


def continuity_view(sources, *, through, provisional):
    """Index all accepted chapters, preserving distant evidence and time bounds.

    No extraction or summarization call is made. The complete source prose is
    already in the writer packet; the index is a navigation/handoff aid only.
    """
    if type(through) is not int or through < 0:
        raise ValueError('Invalid continuity horizon')
    expected = [f'chapter-{n:02d}.md' for n in range(1, through + 1)]
    if set(sources) != set(expected):
        raise ValueError('Continuity needs exactly the accepted chapters through this horizon')
    if any(type(row.get('chapter')) is not int or not 1 <= row['chapter'] <= through for row in provisional):
        raise ValueError('Provisional summary lies outside the accepted chapter horizon')
    rows, handoff = [], None
    for n, name in enumerate(expected, 1):
        text = sources[name]
        paragraphs = evidence_passages(text)
        rows.append({'chapter': n, 'source': name, 'sha256': digest(text.encode('utf-8')),
                     'passages': len(paragraphs), 'status': 'accepted_source_not_fact_certification'})
        if n == through:
            prose = [p for p in paragraphs if not re.fullmatch(r'#{1,6}\s+[^\n]+', p.strip())]
            if prose:
                tail = prose[-1]
                words = list(re.finditer(r'\S+', tail))
                if len(words) > 150:
                    tail = tail[words[-150].start():]
                handoff = {'chapter': n, 'source': name, 'text': tail,
                           'source_sha256': rows[-1]['sha256'], 'status': 'literal_tail'}
    return {'through_chapter': through, 'source_index': rows, 'handoff': handoff,
            'summary_status': 'Writer-reported summaries remain provisional; accepted source scenes take precedence.',
            'provisional_summaries': copy.deepcopy(provisional),
            'rule': 'Read the full accepted chapters already supplied. Keep event time, character knowledge, reader disclosure, '
                    'custody and inference separate. This index does not validate claims or discard distant unresolved facts.'}
