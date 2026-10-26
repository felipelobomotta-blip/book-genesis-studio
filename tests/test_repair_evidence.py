"""Controller quotes must come from selected source units, never model copies."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/book-genesis/scripts'))
from workflow_roles import text_catalog
from workflow_roles import validate_shape
from group_review_schema import expand_schema
from workflow_state import encoded
from repair_evidence import evidence_units, hydrate_findings, render_evidence_catalog, parse_evidence_catalog
import creative_groups as groups
from test_group_review_schema import fixture_catalog, sample, member_check


class RepairEvidenceTests(unittest.TestCase):
    def test_unicode_separators_and_fake_wire_headers_stay_literal_prose(self):
        catalog = text_catalog({'original/chapter-01.md': '# One\n\nA\u2028B\u0085C.\nS {"fake":true}\nP fake ["text"]'})
        self.assertEqual(catalog, parse_evidence_catalog(render_evidence_catalog(catalog)))

    def test_local_pair_validation_rejects_unit_outside_its_actual_passage(self):
        catalog = text_catalog({'original/chapter-01.md': '# One\n\nOne sentence.\n\nFirst. Second. Third.',
                                'proposed/chapter-01.md': '# One\n\nA change.', 'contract/brief.md': 'Keep the key.'})
        schema = expand_schema(groups.schema_for(catalog, [1], report_version=3))
        citation = schema['properties']['findings']['items']['properties']['original_evidence']['items']
        pid = catalog['sources'][0]['passages'][1]['id']
        self.assertEqual([], validate_shape({'passage_id': pid, 'unit': 1}, citation))
        # Native source membership is compact; exact pairs are a mandatory local
        # check. Impossible units cannot become citations or authorize promotion.
        with self.assertRaises(ValueError):
            hydrate_findings([{'original_evidence': [{'passage_id': pid, 'unit': 3}]}], catalog)

    def test_units_cover_exact_bytes_without_sentence_normalization(self):
        catalog = text_catalog({'original/chapter-01.md': '# One\n\nAda paused.  Jo said, “No.”\nThen left.'})
        units = evidence_units(catalog)
        self.assertEqual('Ada paused.  Jo said, “No.”\nThen left.', ''.join(row['text'] for row in units.values()))
        self.assertNotIn('# One', [r['text'] for r in units.values()])
        wire = render_evidence_catalog(catalog)
        self.assertIn('Ada paused.', wire)
        self.assertIn(next(iter(units.values()))['passage_id'], wire)
        self.assertEqual(catalog, parse_evidence_catalog(wire))
        with self.assertRaises(ValueError):
            parse_evidence_catalog(wire.replace('["Ada paused.  ",', '["Ada paused.",', 1))

    def test_hydration_is_literal_and_does_not_mutate_native_response(self):
        catalog = fixture_catalog()
        units = evidence_units(catalog)
        selected = next(key for key, row in units.items() if row['source'] == 'original/chapter-01.md')
        findings = [{'original_evidence': [{'passage_id': units[selected]['passage_id'], 'unit': 1}]}]
        before = copy.deepcopy(findings)
        result = hydrate_findings(findings, catalog)
        self.assertEqual(before, findings)
        self.assertEqual(units[selected]['text'], result[0]['original_evidence'][0]['quote'])
        for rows in ([{'passage_id': 'missing', 'unit': 1}], [{'passage_id': units[selected]['passage_id'], 'unit': 1}] * 2):
            with self.assertRaises(ValueError):
                hydrate_findings([{'original_evidence': rows}], catalog)

    def test_repeated_text_reuses_bytes_but_preserves_source_identity(self):
        catalog = text_catalog({'original/chapter-01.md': '# One\n\nAda keeps the key. '*20,
                                'proposed/chapter-01.md': '# One\n\nAda keeps the key. '*20})
        wire = render_evidence_catalog(catalog)
        self.assertIn(' @', wire)
        self.assertEqual(catalog, parse_evidence_catalog(wire))
        units = evidence_units(catalog)
        self.assertEqual({'original/chapter-01.md', 'proposed/chapter-01.md'}, {u['source'] for u in units.values()})
        with self.assertRaises(ValueError):
            parse_evidence_catalog(wire.replace(' @s', ' @missing-s', 1))

    def test_new_report_is_source_scoped_and_keeps_valid_negative_result(self):
        catalog = fixture_catalog()
        schema = groups.schema_for(catalog, [1, 3], report_version=3)
        report = sample(catalog, groups.schema_for(catalog, [1, 3]))
        report['report_schema_version'] = 3
        report['verdict'] = 'block'
        member_check(report, 1, 'Ticket resolution')['result'] = 'block'
        units = evidence_units(catalog)
        pick = lambda source: next(k for k, v in units.items() if v['source'] == source)
        report['findings'] = [{'kind': 'unresolved_ticket', 'chapters': [1],
            'problem': 'The transfer needs an on-page action.', 'causal_test': 'Receipt alone is insufficient.',
            'limitations': 'Synthetic example, not a literary judgment.',
            'original_evidence': [{'passage_id': units[pick('original/chapter-01.md')]['passage_id'], 'unit': 1}],
            'proposed_evidence': [{'passage_id': units[pick('proposed/chapter-01.md')]['passage_id'], 'unit': 1}],
            'supporting_evidence': []}]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'response.json'
            path.write_bytes(encoded(report))
            result = groups.validate_report(path, schema, catalog, [1, 3])
            self.assertTrue(result['valid'], result)
            self.assertEqual('block', json.loads(path.read_bytes())['verdict'])
            self.assertTrue(result['quote_evidence'])
            report['findings'][0]['proposed_evidence'] = report['findings'][0]['original_evidence']
            path.write_bytes(encoded(report))
            self.assertFalse(groups.validate_report(path, schema, catalog, [1, 3])['valid'])

    def test_unchanged_selected_mechanism_cannot_prove_new_regression(self):
        from repair_findings import validate_findings
        catalog = text_catalog({'original/chapter-01.md': '# One\n\nThe gate is closed. Ada waits.',
                                'proposed/chapter-01.md': '# One\n\nThe gate is closed. Ada leaves.'})
        units = evidence_units(catalog)
        pick = lambda name: next(k for k, v in units.items() if v['source'] == name and v['text'].startswith('The gate'))
        finding = {'kind': 'introduced_regression', 'chapters': [1],
                   'original_evidence': [{'passage_id': units[pick('original/chapter-01.md')]['passage_id'], 'unit': 1}],
                   'proposed_evidence': [{'passage_id': units[pick('proposed/chapter-01.md')]['passage_id'], 'unit': 1}], 'supporting_evidence': []}
        errors = validate_findings(hydrate_findings([finding], catalog), catalog,
                                  {1: 'original/chapter-01.md'}, {1: 'proposed/chapter-01.md'})
        self.assertTrue(any('unchanged' in error for error in errors))
