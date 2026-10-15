"""Native shape must enforce existing member and source-evidence obligations."""
import copy
from collections import Counter
import hashlib
import json
import re
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/book-genesis/scripts'))
import creative_groups as groups
from workflow_roles import text_catalog, validate_shape
from workflow_state import encoded


def fixture_catalog():
    return text_catalog({
        'original/chapter-01.md': '# One\n\nAda keeps the key by the gate.\n',
        'original/chapter-02.md': '# Two\n\nJo waits under the lamp.\n',
        'original/chapter-03.md': '# Three\n\nAda opens the gate with her key.\n',
        'proposed/chapter-01.md': '# One\n\nJo receives the key by the gate.\n',
        'proposed/chapter-03.md': '# Three\n\nJo opens the gate with the received key.\n',
        'contract/00-brief.md': '# Contract\n\nKeep the key handoff on the page.\n'})


def sample(catalog, schema):
    legacy = {'catalog_sha256': hashlib.sha256(encoded(catalog)).hexdigest(), 'verdict': 'pass',
        'coverage': [s['source'] for s in catalog['sources']],
        'chapters': [{'chapter': n, 'checks': [{'name': name, 'result': 'pass',
            'evidence_ids': ids, 'reason': 'The original and proposal support the assigned handoff.'}
            for name in groups.CHECKS]} for n, ids in
            ((1, ['s01p0002', 's04p0002', 's06p0002']), (3, ['s03p0002', 's05p0002', 's06p0002']))],
        'findings': [], 'limitations': 'Synthetic format test only.'}
    if schema['properties']['chapters']['type'] == 'array':
        return legacy
    result = {**legacy, 'report_schema_version': 2,
        'coverage': {name: 'read' for name in legacy['coverage']}, 'chapters': {}}
    for row in legacy['chapters']:
        checks = {}
        for check in row['checks']:
            ids = check['evidence_ids']
            checks[check['name']] = {'result': check['result'], 'reason': check['reason'],
                'original_evidence_ids': ids[:1], 'proposed_evidence_ids': ids[1:2],
                'supporting_evidence_ids': ids[2:]}
        result['chapters'][f"chapter-{row['chapter']:02d}"] = {'checks': checks}
    return result


def member_check(report, number, name):
    if isinstance(report['chapters'], list):
        return next(c for r in report['chapters'] if r['chapter'] == number
                    for c in r['checks'] if c['name'] == name)
    return report['chapters'][f'chapter-{number:02d}']['checks'][name]


class GroupReviewSchemaTests(unittest.TestCase):
    def setUp(self):
        self.catalog = fixture_catalog()
        self.schema = groups.schema_for(self.catalog, [1, 3])
        self.report = sample(self.catalog, self.schema)

    def native_shape_errors(self, report):
        schema = self.schema
        if '$defs' in schema:
            from group_review_schema import expand_schema
            schema = expand_schema(schema)
        return validate_shape(report, schema)

    def validated(self, report=None, raw=None):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'review.json'
            path.write_bytes(encoded(self.report if report is None else report) if raw is None else raw)
            before = path.read_bytes()
            result = groups.validate_report(path, self.schema, self.catalog, [1, 3])
            self.assertEqual(before, path.read_bytes(), 'Validation must never rewrite native evidence')
            return result

    def test_native_shape_requires_external_dependency_support(self):
        check = member_check(self.report, 1, 'Canon and causal dependencies')
        if 'evidence_ids' in check:
            check['evidence_ids'] = ['s01p0002', 's04p0002']
        else:
            check['supporting_evidence_ids'] = []
        self.assertTrue(self.native_shape_errors(self.report),
            'The native contract must prevent a forgotten mandatory support citation')

    def test_native_shape_cannot_substitute_own_prose_for_external_support(self):
        check = member_check(self.report, 1, 'Canon and causal dependencies')
        if 'evidence_ids' in check:
            check['evidence_ids'] = ['s01p0002', 's04p0002', 's01p0002']
        else:
            check['supporting_evidence_ids'] = ['s01p0002']
        self.assertTrue(self.native_shape_errors(self.report))

    def test_native_shape_requires_original_and_proposal_in_each_check(self):
        check = member_check(self.report, 3, 'Preserved strengths')
        if 'evidence_ids' in check:
            check['evidence_ids'] = ['s05p0002', 's06p0002']
        else:
            check['original_evidence_ids'] = []
        self.assertTrue(self.native_shape_errors(self.report))

    def test_native_shape_rejects_wrong_version_source(self):
        check = member_check(self.report, 1, 'Ticket resolution')
        if 'evidence_ids' in check:
            check['evidence_ids'] = ['s04p0002', 's04p0002', 's06p0002']
        else:
            check['original_evidence_ids'] = ['s04p0002']
        self.assertTrue(self.native_shape_errors(self.report))

    def test_native_shape_requires_each_named_member_once(self):
        if isinstance(self.report['chapters'], list):
            self.report['chapters'][1] = copy.deepcopy(self.report['chapters'][0])
        else:
            del self.report['chapters']['chapter-03']
        self.assertTrue(self.native_shape_errors(self.report))

    def test_valid_positive_report_is_not_rewritten(self):
        self.assertFalse(self.native_shape_errors(self.report))
        self.assertTrue(self.validated()['valid'])

    def negative(self):
        self.report['verdict'] = 'block'
        member_check(self.report, 1, 'Ticket resolution')['result'] = 'block'
        self.report['findings'] = [{'kind': 'unresolved_ticket', 'chapters': [1],
            'problem': 'The actual transfer remains insufficiently dramatized.',
            'causal_test': 'Naming receipt is not the physical transfer itself.',
            'limitations': 'Synthetic negative example, no literary rating.',
            'original_evidence': [{'passage_id': 's01p0002', 'quote': 'Ada keeps the key by the gate.'}],
            'proposed_evidence': [{'passage_id': 's04p0002', 'quote': 'Jo receives the key by the gate.'}],
            'supporting_evidence': [{'passage_id': 's06p0002', 'quote': 'Keep the key handoff on the page.'}]}]

    def test_valid_negative_review_remains_valid_and_negative(self):
        self.negative()
        self.assertTrue(self.validated()['valid'])
        self.assertEqual('block', self.report['verdict'])

    def test_invented_quotation_still_invalidates_a_negative_report(self):
        self.negative()
        self.report['findings'][0]['proposed_evidence'][0]['quote'] = 'Ada sold the key to Max.'
        self.assertFalse(self.validated()['valid'])

    def test_unchanged_mechanism_accusation_remains_invalid(self):
        self.negative()
        finding = self.report['findings'][0]
        finding['kind'] = 'introduced_regression'
        for field in ('original_evidence', 'proposed_evidence'):
            finding[field][0]['quote'] = 'the key'
        result = self.validated()
        self.assertFalse(result['valid'])
        self.assertTrue(any('unchanged' in error for error in result['errors']))

    def test_duplicate_physical_json_keys_cannot_hide_a_verdict(self):
        raw = json.dumps(self.report, ensure_ascii=False).replace(
            '"verdict": "pass"', '"verdict": "block", "verdict": "pass"', 1).encode()
        self.assertFalse(self.validated(raw=raw)['valid'])

    def test_legacy_wire_schema_and_both_packets_stay_byte_identical(self):
        schema = groups.schema_for(self.catalog, [1, 3], report_version=1)
        self.assertEqual('c0534ba8a9f4e9186387fdc1498fd881f04271d9b03f67e05d36660f7ff00c70',
            hashlib.sha256(encoded(schema)).hexdigest())
        tasks = [{'chapter': n, 'mode': 'creative', 'ticket': 'Show the key handoff.', 'preserve': 'Gate and lamp.',
            'revision_class': 'continuity', 'issue_ids': ['key']} for n in (1, 3)]
        for version, expected in ((1, '9b9d9374c2a3419887bc177377a92dba2748a460db8f48e6e4f8b21cd399b382'),
                                  (2, '103d74c366c151d7b041b1deb2bd72339fd3f9730cc488ffc6a2170710cdc741')):
            manifest = {'schema_version': version, 'tasks': tasks,
                'strategy': 'Show the handoff before the gate opens.'}
            if version == 2:
                manifest['retained_members'] = [{'chapter': 2, 'status': 'unresolved_original_retained',
                    'reason': 'Synthetic retained original.',
                    'outcome': {'path': 'fixture/retained.json', 'sha256': '0' * 64}, 'evidence': []}]
            with self.subTest(version=version):
                self.assertEqual(expected, hashlib.sha256(groups.packet_for(manifest, self.catalog)).hexdigest())

    def test_local_schema_refs_expand_without_mutating_the_native_schema(self):
        from group_review_schema import expand_schema
        schema = {'$defs': {'id': {'type': 'string', 'enum': ['actual']}}, 'type': 'object',
            'properties': {'id': {'$ref': '#/$defs/id'}}, 'required': ['id'], 'additionalProperties': False}
        before = encoded(schema)
        expanded = expand_schema(schema)
        self.assertFalse(validate_shape({'id': 'actual'}, expanded))
        self.assertTrue(validate_shape({'id': 'invented'}, expanded))
        self.assertEqual(before, encoded(schema))

    def test_external_missing_cyclic_and_ambiguous_refs_are_rejected(self):
        from group_review_schema import expand_schema
        for ref in ('file:///secret.json', 'https://invalid.example/schema', '#/$defs/missing', '#/$defs/a'):
            schema = {'$defs': {'a': {'$ref': '#/$defs/a'}}, 'type': 'array', 'items': {'$ref': ref}}
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                expand_schema(schema)
        with self.assertRaises(ValueError):
            expand_schema({'$defs': {'a': {'type': 'string'}}, 'type': 'array',
                'items': {'$ref': '#/$defs/a', 'type': 'integer'}})

    def test_source_passage_enums_are_shared_instead_of_repeated_for_every_check(self):
        ids = []
        def walk(value):
            if isinstance(value, dict):
                ids.extend(x for x in value.get('enum', []) if isinstance(x, str) and re.fullmatch(r's\d+p\d+', x))
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(self.schema)
        self.assertEqual(Counter({f's{n:02d}p0002': 1 for n in range(1, 7)}), Counter(ids))

    def test_twenty_four_member_native_schema_stays_bounded(self):
        sources = {}
        for prefix in ('original', 'proposed'):
            for n in range(1, 25):
                sources[f'{prefix}/chapter-{n:02d}.md'] = f'# Chapter {n}\n\n' + '\n\n'.join(
                    f'Passage {i}. ' + 'key ' * 200 for i in range(18))
        sources['contract/00-brief.md'] = '# Contract\n\nKeep the key transfer visible.'
        schema = groups.schema_for(text_catalog(sources), list(range(1, 25)))
        self.assertLess(len(encoded(schema)), 200000)


if __name__ == '__main__':
    unittest.main()
