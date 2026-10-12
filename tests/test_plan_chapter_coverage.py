"""Chapter coverage and repair history are enforced without invented judgments."""
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/book-genesis/scripts'))
from autonomous_book import BookWorkflow
from plan_verification import chapter_requirements
from workflow_roles import PLAN_PASSES, plan_schema, render_plan, review_schema, text_catalog, validate_review
from workflow_state import encoded, freeze, read_json
from test_autonomous_workflow import COMMAND, fixture_response, receipt_transport


class PlanChapterCoverageTests(unittest.TestCase):
    @staticmethod
    def long_plan():
        plan = fixture_response('architecture', '', plan_schema(24), Path('.'))
        template = plan['chapters'][0]
        plan['chapters'] = [{**copy.deepcopy(template), 'number': number,
                            'title': f'Delivery stage {number}',
                            'events': 'Word target 3400. The courier chooses the next delivery route.'}
                           for number in range(1, 25)]
        return plan

    def setUp(self):
        plan = fixture_response('architecture', '', plan_schema(2), Path('.'))
        rendered = render_plan(plan)
        self.catalog = text_catalog({'approved-brief': 'Return the letter before departure in close third person.',
            'outline': rendered['artifacts/07-outline.md'], 'ledger': rendered['artifacts/09-continuity-ledger.md']})
        self.schema = review_schema(self.catalog, passes=PLAN_PASSES)
        self.data = fixture_response('plan-check-1', 'Complete sources:\n' + json.dumps(self.catalog), self.schema, Path('.'))

    def validate(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'response.json'
            path.write_bytes(encoded(data))
            return validate_review(path, self.schema, self.catalog, PLAN_PASSES, max_chapter=2)

    def test_complete_exact_field_coverage_passes_without_semantic_certification(self):
        self.assertTrue(self.validate(self.data)['valid'])
        requirements = chapter_requirements(self.catalog)
        self.assertEqual([1, 2], [r['chapter'] for r in requirements])
        self.assertEqual(4, len(requirements[0]['checks']))

    def test_markdown_subheading_inside_a_scene_does_not_hide_later_chapter_fields(self):
        plan = fixture_response('architecture', '', plan_schema(2), Path('.'))
        plan['chapters'][0]['events'] += '\n\n## At the gate\n\nAda knocks and waits.'
        rendered = render_plan(plan)
        catalog = text_catalog({'approved-brief': 'Return the letter.',
            'outline': rendered['artifacts/07-outline.md'], 'ledger': rendered['artifacts/09-continuity-ledger.md']})
        requirements = chapter_requirements(catalog)
        self.assertEqual([1, 2], [r['chapter'] for r in requirements])
        self.assertEqual(4, len(requirements[0]['checks']))

    def test_twenty_four_chapter_plan_keeps_every_required_field_citation(self):
        plan = self.long_plan()
        rendered = render_plan(plan)
        outline = rendered['artifacts/07-outline.md']
        self.assertGreater(len(outline.split('\n\n')), 128)
        catalog = text_catalog({'approved-brief': 'Return the letter before departure.',
            'outline': outline, 'ledger': rendered['artifacts/09-continuity-ledger.md']})
        requirements = chapter_requirements(catalog)
        self.assertEqual(list(range(1, 25)), [row['chapter'] for row in requirements])
        passages = {p['id']: p['text'] for source in catalog['sources'] for p in source['passages']}
        for row in requirements:
            self.assertEqual(4, len(row['checks']))
            for check in row['checks']:
                for passage_id in check['required_evidence_ids']:
                    self.assertTrue(passages[passage_id].startswith('**'))
                    self.assertNotIn('\n\n**', passages[passage_id])
        schema = review_schema(catalog, passes=PLAN_PASSES)
        report = fixture_response('plan-check-1', 'Complete sources:\n' + json.dumps(catalog), schema, Path('.'))
        with tempfile.TemporaryDirectory() as tmp:
            response = Path(tmp) / 'response.json'
            response.write_bytes(encoded(report))
            validation = validate_review(response, schema, catalog, PLAN_PASSES, max_chapter=24)
            self.assertTrue(validation['valid'], validation['errors'])

    def test_an_actually_missing_field_still_blocks_a_long_plan(self):
        plan = self.long_plan()
        rendered = render_plan(plan)
        outline = rendered['artifacts/07-outline.md'].replace('**Point of view:**', '**Other:**', 1)
        with self.assertRaisesRegex(ValueError, 'missing a required chapter field'):
            chapter_requirements(text_catalog({'outline': outline}))

    def test_full_twenty_four_chapter_planning_reaches_drafting_without_author_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze(root / '.book-genesis/project.json', encoded({'host': 'codex', 'collaboration': 'autonomous',
                'author_name': 'QA', 'model': 'exact-test-model', 'effort': 'high',
                'idea': 'Deliver the letter.', 'language': 'English'}))
            freeze(root / '.book-genesis/skills/.book-genesis-install.json', b'{}')
            calls = []
            def generate(call_id, packet, schema, book):
                calls.append(call_id)
                if 'canon' in schema['properties']:
                    return self.long_plan()
                return fixture_response(call_id, packet, schema, book)
            options = dict(chapters=24, min_words=80000, max_words=88000,
                           transport=receipt_transport(generate))
            with redirect_stdout(io.StringIO()):
                workflow = BookWorkflow(root, COMMAND, **options)
                workflow.planning()
                before = len(calls)
                BookWorkflow(root, COMMAND, **options).planning()
            self.assertEqual(3, workflow.journal.data['phase'])
            self.assertTrue((root / 'artifacts/07-outline.md').is_file())
            self.assertEqual(before, len(calls))
            review = read_json(root / 'work/host-calls/wf-plan-check-1-1/response')
            self.assertEqual(list(range(1, 25)), [row['chapter'] for row in review['chapter_checks']])

    def test_duplicate_chapter_or_check_cannot_claim_complete_coverage(self):
        changed = copy.deepcopy(self.data)
        changed['chapter_checks'][1] = changed['chapter_checks'][0]
        self.assertFalse(self.validate(changed)['valid'])
        changed = copy.deepcopy(self.data)
        changed['chapter_checks'][0]['checks'][1] = changed['chapter_checks'][0]['checks'][0]
        self.assertFalse(self.validate(changed)['valid'])

    def test_other_chapter_or_heading_citation_cannot_replace_required_fields(self):
        changed = copy.deepcopy(self.data)
        changed['chapter_checks'][0]['checks'][1]['evidence_ids'] = changed['chapter_checks'][1]['checks'][1]['evidence_ids']
        self.assertFalse(self.validate(changed)['valid'])
        changed['chapter_checks'][0]['checks'][1]['evidence_ids'] = [self.catalog['sources'][1]['passages'][1]['id']]
        self.assertFalse(self.validate(changed)['valid'])

    def test_negative_chapter_finding_is_valid_but_cannot_hide_behind_a_pass(self):
        changed = copy.deepcopy(self.data)
        check = changed['chapter_checks'][0]['checks'][1]
        check['result'] = 'finding'
        changed['verdict'] = 'revise'
        changed['findings'] = [{'severity': 'high', 'kind': 'continuity', 'chapters': [1],
            'evidence_ids': check['evidence_ids'], 'problem': 'The return happens after departure.',
            'fix': 'Move the return before departure.', 'preserve': 'The returned letter.'}]
        self.assertTrue(self.validate(changed)['valid'])
        changed['verdict'] = 'pass'
        self.assertFalse(self.validate(changed)['valid'])
        changed['verdict'] = 'revise'
        changed['findings'] = []
        self.assertFalse(self.validate(changed)['valid'])

    def test_general_finding_requires_its_affected_chapter_check(self):
        changed = copy.deepcopy(self.data)
        changed['verdict'] = 'revise'
        changed['findings'] = [{'severity': 'high', 'kind': 'continuity', 'chapters': [2],
            'evidence_ids': changed['chapter_checks'][1]['checks'][1]['evidence_ids'],
            'problem': 'The return happens after departure.', 'fix': 'Move the return before departure.', 'preserve': 'The letter.'}]
        self.assertFalse(self.validate(changed)['valid'])

    def test_earlier_findings_reach_second_repair_only_and_replay_makes_no_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze(root / '.book-genesis/project.json', encoded({'host': 'codex', 'collaboration': 'autonomous',
                'author_name': 'QA', 'model': 'exact-test-model', 'effort': 'high', 'idea': 'Return the letter.', 'language': 'English'}))
            freeze(root / '.book-genesis/skills/.book-genesis-install.json', b'{}')
            calls, packets = [], {}
            def generate(call_id, packet, schema, book):
                calls.append(call_id); packets[call_id] = packet
                result = fixture_response(call_id, packet, schema, book)
                if 'plan-check-1' in call_id:
                    check = result['chapter_checks'][1]['checks'][1]
                    check['result'] = 'finding'
                    result['verdict'] = 'revise'
                    result['findings'] = [{'severity': 'high', 'kind': 'continuity', 'chapters': [2],
                        'evidence_ids': check['evidence_ids'], 'problem': 'CURRENT_SECOND_DEFECT: return is too late.',
                        'fix': 'Return before departure.', 'preserve': 'The letter.'}]
                return result
            options = dict(chapters=2, min_words=240, max_words=600, transport=receipt_transport(generate))
            with redirect_stdout(io.StringIO()):
                workflow = BookWorkflow(root, COMMAND, **options)
                workflow.planning()
                count = len(calls)
                BookWorkflow(root, COMMAND, **options).planning()
            self.assertEqual(count, len(calls))
            self.assertIn('The courier has not confessed.', packets['wf-architecture-repair-2-1'])
            self.assertIn('CURRENT_SECOND_DEFECT', packets['wf-architecture-repair-2-1'])
            for key, packet in packets.items():
                if key.startswith('wf-plan-check-'):
                    self.assertNotIn('CURRENT_SECOND_DEFECT', packet)
                    self.assertNotIn('Earlier repair findings', packet)
                    self.assertNotIn('The courier has not confessed.', packet)
            self.assertEqual(1, len(workflow.journal.data['steps']['architecture-repair-2']['attempts']))
            self.assertEqual(3, workflow.journal.data['phase'])


if __name__ == '__main__':
    unittest.main()
