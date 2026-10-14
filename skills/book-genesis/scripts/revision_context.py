"""Lossless large editor views; native readers still receive complete originals."""
import copy
import difflib
import hashlib
import json

from workflow_state import encoded

MAX_INITIAL_CHARACTERS = 900000  # Leave room for the existing producer format retry.
FORMAT = 'original-line-replacements-v1'
INSTRUCTIONS = (
    'This is a lossless view of the complete editor context, not a summary. '
    'Every other_current_chapters value is the complete original prose. '
    'A companion encoded as original-line-replacements-v1 is that same named original '
    'with exactly the listed replacements applied simultaneously to its ORIGINAL lines. '
    'Line ranges are zero-based, start inclusive and end exclusive; equal endpoints insert text. '
    'before is exact original evidence, after is the actual proposed prose. '
    'Every original line outside those ranges remains verbatim in the complete proposal. '
    'A string companion is already its complete proposed text. These proposals are not accepted canon. '
    'An adjacent_context reference names the complete original already supplied in other_current_chapters. '
    'Read those full originals and all actual proposed changes, preserving their separate versions. '
    'No tools or further file access are needed. Hashes bind exact bytes; they are not story facts.'
)


def _text_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _line_view(original, proposed):
    before, after = original.splitlines(keepends=True), proposed.splitlines(keepends=True)
    edits = [{'lines': [a, b], 'before': ''.join(before[a:b]), 'after': ''.join(after[c:d])}
             for operation, a, b, c, d in difflib.SequenceMatcher(None, before, after, autojunk=False).get_opcodes()
             if operation != 'equal']
    return {'encoding': FORMAT, 'original_sha256': _text_hash(original),
            'candidate_sha256': _text_hash(proposed), 'edits': edits}


def _restore(original, view):
    if view.get('encoding') != FORMAT or _text_hash(original) != view.get('original_sha256'):
        raise ValueError('Compact companion does not match its complete original source')
    lines = original.splitlines(keepends=True)
    edits = view.get('edits')
    if not isinstance(edits, list):
        raise ValueError('Compact companion lacks explicit line edits')
    previous_end, previous_start = 0, -1
    for edit in edits:
        span = edit.get('lines')
        if (not isinstance(span, list) or len(span) != 2 or any(type(n) is not int for n in span)
                or not 0 <= span[0] <= span[1] <= len(lines)
                or span[0] < previous_end or span[0] == previous_start
                or not isinstance(edit.get('before'), str) or not isinstance(edit.get('after'), str)):
            raise ValueError('Compact companion has invalid, overlapping or reordered line ranges')
        a, b = span
        if ''.join(lines[a:b]) != edit['before']:
            raise ValueError('Compact companion before text differs from its complete original')
        previous_start, previous_end = a, b
    restored = list(lines)
    for edit in reversed(edits):
        a, b = edit['lines']
        restored[a:b] = edit['after'].splitlines(keepends=True)
    candidate = ''.join(restored)
    if _text_hash(candidate) != view.get('candidate_sha256'):
        raise ValueError('Compact companion does not reconstruct its exact candidate bytes')
    return candidate


def decode_context(view):
    """Reconstruct and validate every original field without modifying the input."""
    data = copy.deepcopy(view)
    metadata = data.pop('_lossless_context', None)
    if metadata is None:
        return data
    if metadata.get('version') != 1 or metadata.get('instructions') != INSTRUCTIONS:
        raise ValueError('Unknown compact editor context contract')
    originals = data['other_current_chapters']
    for name, proposed in list(data['unaccepted_companion_proposals'].items()):
        if isinstance(proposed, dict):
            if name not in originals or not isinstance(originals[name], str):
                raise ValueError('Compact companion lacks its complete original chapter')
            data['unaccepted_companion_proposals'][name] = _restore(originals[name], proposed)
        elif not isinstance(proposed, str):
            raise ValueError('Unknown compact companion representation')
    for index, adjacent in enumerate(data['adjacent_context']):
        if isinstance(adjacent, dict):
            if set(adjacent) != {'from_current_chapter'} or adjacent['from_current_chapter'] not in originals:
                raise ValueError('Adjacent context reference lacks its complete original chapter')
            data['adjacent_context'][index] = originals[adjacent['from_current_chapter']]
    if hashlib.sha256(encoded(data)).hexdigest() != metadata.get('original_context_sha256'):
        raise ValueError('Compact view differs from its exact original editor context')
    return data


def compact_context(context):
    if '_lossless_context' in context:
        raise ValueError('Editor context already contains reserved compact-view metadata')
    data = copy.deepcopy(context)
    originals = data['other_current_chapters']
    for name, proposed in list(data['unaccepted_companion_proposals'].items()):
        if name not in originals or not isinstance(proposed, str) or not isinstance(originals[name], str):
            raise ValueError('Companion proposal must have its complete current original')
        view = _line_view(originals[name], proposed)
        if len(json.dumps(view, ensure_ascii=False)) < len(json.dumps(proposed, ensure_ascii=False)):
            data['unaccepted_companion_proposals'][name] = view
    for index, adjacent in enumerate(data['adjacent_context']):
        names = [name for name, original in originals.items() if original == adjacent]
        if len(names) == 1:
            data['adjacent_context'][index] = {'from_current_chapter': names[0]}
    data['_lossless_context'] = {'version': 1, 'instructions': INSTRUCTIONS,
        'original_context_sha256': hashlib.sha256(encoded(context)).hexdigest()}
    if encoded(decode_context(data)) != encoded(context):
        raise ValueError('Compact view did not preserve the complete editor context')
    return data


def render_context(context, *, prefix_chars=0):
    legacy = json.dumps(context, ensure_ascii=False)
    if len(legacy) + prefix_chars <= MAX_INITIAL_CHARACTERS:
        return legacy
    compact = json.dumps(compact_context(context), ensure_ascii=False)
    if len(compact) + prefix_chars > MAX_INITIAL_CHARACTERS:
        raise ValueError('Complete revision context is still too large for the native character limit; '
                         'no source was truncated and no native call was dispatched')
    return compact
