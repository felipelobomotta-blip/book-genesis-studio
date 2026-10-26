"""Source-selected repair quotations; location is not semantic proof.

Units are lossless lexical spans, not a linguistic sentence parser. Reviewers
can cite adjacent units when an abbreviation or dialogue crosses a boundary.
The frozen catalog binds every selected ID to exact source text.
"""
import copy
import json
import re


INSTRUCTIONS = """Use report_schema_version 3. In findings, select a passage_id and
unit (one-based index into that P record's JSON array); never transcribe quotations.
P IDs also remain the citations for chapter checks. The controller renders the
exact selected source span as the quote. Units are lexical chunks, not claims or verified facts: select all
chunks needed to support the finding, including adjacent chunks when necessary.
Never duplicate a passage/unit pair in a finding field. Valid IDs prove location
only. Explain the actual support and uncertainty in problem, causal_test and
limitations. A changed chunk alone does not establish a changed causal mechanism;
state the specific change that introduces the alleged regression. Preserve
negative verdicts when supported; no score or approval is implied by valid IDs.
"""


def evidence_units(catalog):
    units = {}
    seen = set()
    for source in catalog['sources']:
        for passage in source['passages']:
            pid, text = passage['id'], passage['text']
            if pid in seen:
                raise ValueError('Duplicate source passage ID')
            seen.add(pid)
            if re.fullmatch(r'#{1,6}\s+[^\n]+', text.strip()):
                continue
            boundaries = [0] + [m.end() for m in re.finditer(r'[.!?][\"\u201d\u2019\x27)]*\s+', text)] + [len(text)]
            spans = [(a, b) for a, b in zip(boundaries, boundaries[1:]) if b > a]
            for number, (start, end) in enumerate(spans, 1):
                units[f'{pid}e{number:04d}'] = {'source': source['source'], 'passage_id': pid,
                    'start': start, 'end': end, 'text': text[start:end]}
    return units


def hydrate_findings(findings, catalog):
    units = evidence_units(catalog)
    result = copy.deepcopy(findings)
    for finding in result:
        for field in ('original_evidence', 'proposed_evidence', 'supporting_evidence'):
            if field not in finding:
                continue
            seen, rows = set(), []
            for row in finding[field]:
                unit_number = row.get('unit')
                identifier = f"{row.get('passage_id')}e{unit_number:04d}" if type(unit_number) is int else None
                if set(row) != {'passage_id', 'unit'} or type(unit_number) is not int:
                    raise ValueError(f'{field}: evidence requires passage_id and an integer unit')
                if identifier not in units:
                    count = sum(unit['passage_id'] == row['passage_id'] for unit in units.values())
                    raise ValueError(f"{field}: passage {row['passage_id']} has {count} selectable units; "
                                     f'unit {unit_number} is invalid. Select a real one-based array position from that passage.')
                if identifier in seen:
                    raise ValueError(f'{field}: repeated passage/unit pair {identifier}')
                seen.add(identifier)
                unit = units[identifier]
                rows.append({'passage_id': unit['passage_id'], 'quote': unit['text']})
            finding[field] = rows
    return result


def render_evidence_catalog(catalog):
    """Render complete text once with both paragraph and selected-span IDs."""
    units = evidence_units(catalog)
    by_passage = {}
    for identifier, unit in units.items():
        by_passage.setdefault(unit['passage_id'], []).append((identifier, unit))
    rows, previous = [], {}
    for source in catalog['sources']:
        rows.append('S ' + json.dumps({k: source[k] for k in ('source', 'sha256')}, ensure_ascii=False) + '\n')
        for passage in source['passages']:
            if passage['text'] in previous:
                rows.append(f"P {passage['id']} @{previous[passage['text']]}\n")
                continue
            selected = by_passage.get(passage['id'], [])
            body = [unit['text'] for _, unit in selected] if selected else [passage['text']]
            rows.append(f"P {passage['id']} " + json.dumps(body, ensure_ascii=False, separators=(',', ':')) + '\n')
            previous[passage['text']] = passage['id']
    return ''.join(rows)


def parse_evidence_catalog(wire):
    """Lossless round trip: JSON protects embedded newlines and wire headers."""
    sources, current, previous = [], None, {}
    if wire and not wire.endswith('\n'):
        raise ValueError('Truncated evidence catalog')
    # Unicode line/paragraph separators inside JSON strings are source content,
    # not physical wire boundaries. Only the renderer's ASCII LF is structural.
    for header in wire.split('\n')[:-1]:
        if header.startswith('S '):
            current = {**json.loads(header[2:]), 'passages': []}
            sources.append(current)
        elif header.startswith('P ') and current is not None:
            _, identifier, raw = header.split(' ', 2)
            if raw.startswith('@'):
                if raw[1:] not in previous:
                    raise ValueError('Missing earlier literal passage')
                chunks = previous[raw[1:]]
            else:
                chunks = json.loads(raw)
            if not isinstance(chunks, list) or not chunks or any(not isinstance(chunk, str) for chunk in chunks):
                raise ValueError('Invalid selected evidence chunks')
            current['passages'].append({'id': identifier, 'text': ''.join(chunks)})
            if identifier in previous:
                raise ValueError('Duplicate passage ID')
            previous[identifier] = chunks
        else:
            raise ValueError('Invalid evidence catalog order')
    result = {'sources': sources}
    if render_evidence_catalog(result) != wire:
        raise ValueError('Evidence IDs or lexical spans differ from their sources')
    return result
