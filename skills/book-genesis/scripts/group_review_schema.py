"""Source-scoped native review contracts; no verdicts or citations are invented."""
from repair_findings import _prose, finding_schema
from revision_viability import CHECKS
from workflow_roles import INTEGER, TEXT, array, enum, obj
from workflow_state import digest, encoded


INSTRUCTIONS = (
    'Use report_schema_version 2. The schema names every required chapter and check '
    'as an object key; fill each exactly once. coverage names each complete source '
    'with value read. In every check choose original_evidence_ids from that chapter\'s '
    'original prose and proposed_evidence_ids from its proposal. For Canon and causal '
    'dependencies, supporting_evidence_ids must name actual prose from another source, '
    'not either version of this chapter. Supporting IDs for other checks may be empty. '
    'Each reason explains what those actual passages establish. All existing repair, '
    'quote, changed-mechanism and negative-verdict rules still apply. Never invent or '
    'copy a citation merely to fill a slot. Return only the required JSON.'
)


def _ref(name):
    return {'$ref': '#/$defs/' + name}


def build_schema(catalog, members):
    originals = {n: f'original/chapter-{n:02d}.md' for n in members}
    proposals = {n: f'proposed/chapter-{n:02d}.md' for n in members}
    prose = _prose(catalog)
    definitions = {'check_result': enum(('pass', 'block')), 'read_marker': enum(('read',))}
    source_refs = {}
    for index, source in enumerate(catalog['sources']):
        ids = [p['id'] for p in source['passages'] if p['id'] in prose]
        if ids:
            name = f'passages_{index}'
            definitions[name] = enum(ids)
            source_refs[source['source']] = _ref(name)
    chapters = {}
    for n in members:
        own = {originals[n], proposals[n]}
        if not own.issubset(source_refs):
            raise ValueError('Creative group member lacks original or proposed prose')
        external = [ref for name, ref in source_refs.items() if name not in own]
        if not external:
            raise ValueError('Creative group lacks external dependency prose')
        support_name = f'supporting_{n}'
        definitions[support_name] = {'anyOf': external}
        checks = {}
        for name in CHECKS:
            dependency = name == 'Canon and causal dependencies'
            definition_name = f'dependency_check_{n}' if dependency else f'local_check_{n}'
            if definition_name not in definitions:
                definitions[definition_name] = obj({'result': _ref('check_result'), 'reason': TEXT,
                    'original_evidence_ids': {**array(source_refs[originals[n]]), 'minItems': 1},
                    'proposed_evidence_ids': {**array(source_refs[proposals[n]]), 'minItems': 1},
                    'supporting_evidence_ids': {**array(_ref(support_name)),
                        'minItems': 1 if dependency else 0}})
            checks[name] = _ref(definition_name)
        chapters[f'chapter-{n:02d}'] = obj({'checks': obj(checks)})
    findings = finding_schema(catalog, originals, proposals)
    evidence = findings['items']['properties']
    for field, names in (('original_evidence', originals.values()),
                         ('proposed_evidence', proposals.values()),
                         ('supporting_evidence', source_refs)):
        evidence[field]['items']['properties']['passage_id'] = {
            'anyOf': [source_refs[name] for name in names]}
    result = obj({'report_schema_version': {**INTEGER, 'enum': [2]},
        'catalog_sha256': enum((digest(encoded(catalog)),)), 'verdict': enum(('pass', 'block')),
        'coverage': obj({s['source']: _ref('read_marker') for s in catalog['sources']}),
        'chapters': obj(chapters), 'findings': findings, 'limitations': TEXT})
    result['$defs'] = definitions
    return result


def expand_schema(schema):
    """Resolve only local root definitions for the existing shape validator.

    Native transport receives the original shared schema. No external resource
    lookup, mutable schema rewrite or recursive definition is supported here.
    """
    definitions = schema.get('$defs', {})
    if not isinstance(definitions, dict):
        raise ValueError('Local schema definitions must be an object')

    def visit(node, active=(), root=False):
        if isinstance(node, list):
            return [visit(value, active) for value in node]
        if not isinstance(node, dict):
            return node
        if '$ref' in node:
            reference = node['$ref']
            if set(node) != {'$ref'} or not isinstance(reference, str) or not reference.startswith('#/$defs/'):
                raise ValueError('Only unambiguous local schema references are supported')
            name = reference[len('#/$defs/'):]
            if name not in definitions or '/' in name or '~' in name or name in active:
                raise ValueError('Missing, invalid or cyclic local schema reference')
            return visit(definitions[name], active + (name,))
        if '$defs' in node and not root:
            raise ValueError('Only root schema definitions are supported')
        return {key: visit(value, active) for key, value in node.items() if key != '$defs'}

    return visit(schema, root=True)


def normalized_report(report):
    """Validation-only view; preserve the raw native response and its verdict."""
    if report.get('report_schema_version') != 2:
        return report
    chapters = []
    for key, member in report['chapters'].items():
        checks = []
        for name, row in member['checks'].items():
            checks.append({'name': name, 'result': row['result'], 'reason': row['reason'],
                'evidence_ids': row['original_evidence_ids'] + row['proposed_evidence_ids']
                    + row['supporting_evidence_ids']})
        chapters.append({'chapter': int(key[len('chapter-'):]), 'checks': checks})
    return {**report, 'chapters': chapters, 'coverage': list(report['coverage'])}
