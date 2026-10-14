"""Repair packets must identify Chapter 8 without guessing zero-based slots."""
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
import workflow_roles
from autonomous_book import BookWorkflow
from workflow_roles import plan_schema, render_plan, text_catalog
from workflow_state import encoded, freeze, read_json
from test_autonomous_workflow import COMMAND, fixture_response, receipt_transport


class PlanRepairTargetTests(unittest.TestCase):
    def source(self):
        plan = fixture_response('architecture', '', plan_schema(2), Path('.'))
        original = plan['chapters'][0]
        plan['chapters'] = [{**copy.deepcopy(original), 'number': number,
            'title': f'Journey {number}', 'continuity': f'The sealed parcel is at station {number}.'}
            for number in range(1, 25)]
        rendered = render_plan(plan)
        catalog = text_catalog({'approved-brief': 'Return the parcel.',
            'outline': rendered['artifacts/07-outline.md'], 'ledger': rendered['artifacts/09-continuity-ledger.md']})
        passage = next(p for s in catalog['sources'] if s['source'] == 'outline'
            for p in s['passages'] if p['text'].startswith('**Continuity:** The sealed parcel is at station 8.'))
        return plan, catalog, passage

    def context(self, plan, catalog, findings):
        helper = getattr(workflow_roles, 'plan_repair_targets', None)
        self.assertTrue(callable(helper), 'Repairers need exact cited source text and chapter edit addresses')
        return helper(plan, catalog, findings)

    def test_chapter_eight_evidence_names_its_real_field_not_chapter_nine_or_eighteen(self):
        plan, catalog, passage = self.source()
        before = encoded(plan)
        context = self.context(plan, catalog, [{'evidence_ids': [passage['id']]}])
        evidence = context['cited_evidence']
        self.assertEqual(1, len(evidence))
        self.assertEqual(passage['text'], evidence[0]['text'])
        self.assertEqual(['/chapters/7/continuity'], evidence[0]['editable_paths'])
        self.assertEqual('The sealed parcel is at station 8.', context['editable_fields']['/chapters/7/continuity'])
        self.assertEqual({'chapter': 8, 'title': 'Journey 8', 'prefix': '/chapters/7'}, context['chapter_addresses'][7])
        self.assertEqual({'chapter': 9, 'title': 'Journey 9', 'prefix': '/chapters/8'}, context['chapter_addresses'][8])
        self.assertEqual({'chapter': 18, 'title': 'Journey 18', 'prefix': '/chapters/17'}, context['chapter_addresses'][17])
        self.assertEqual(before, encoded(plan))

    def test_approved_brief_is_visible_evidence_but_not_an_editable_plan_field(self):
        plan, catalog, _ = self.source()
        passage = catalog['sources'][0]['passages'][0]
        context = self.context(plan, catalog, [{'evidence_ids': [passage['id'], passage['id']]}])
        self.assertEqual(1, len(context['cited_evidence']))
        self.assertEqual(passage['text'], context['cited_evidence'][0]['text'])
        self.assertEqual([], context['cited_evidence'][0]['editable_paths'])
        self.assertFalse(any('approved-brief' in path for path in context['editable_fields']))

    def test_unknown_review_reference_cannot_be_silently_dropped(self):
        plan, catalog, _ = self.source()
        helper = getattr(workflow_roles, 'plan_repair_targets', None)
        self.assertTrue(callable(helper), 'Repair target binding is missing')
        with self.assertRaisesRegex(ValueError, 'Unknown plan repair evidence'):
            helper(plan, catalog, [{'evidence_ids': ['absent-reference']}])

    def test_multiline_scene_continuation_keeps_its_exact_chapter_field(self):
        plan, _, _ = self.source()
        plan['chapters'][7]['events'] = 'The courier enters.\n\nA uniquely marked latch snaps shut.'
        rendered = render_plan(plan)
        catalog = text_catalog({'outline': rendered['artifacts/07-outline.md']})
        passage = next(p for p in catalog['sources'][0]['passages'] if 'A uniquely marked latch' in p['text'])
        context = self.context(plan, catalog, [{'evidence_ids': [passage['id']]}])
        self.assertEqual(['/chapters/7/events'], context['cited_evidence'][0]['editable_paths'])

    def test_ledger_bullets_and_promise_payoff_keep_their_literal_edit_paths(self):
        plan, _, _ = self.source()
        plan['canon']['objects'] = ['The brass key is with Nora.']
        plan['promises'][0]['on_page_resolution'] = 'Nora opens the safe on the page.'
        rendered = render_plan(plan)
        catalog = text_catalog({'outline': rendered['artifacts/07-outline.md'], 'ledger': rendered['artifacts/09-continuity-ledger.md']})
        passages = {s['source']: next(p for p in s['passages'] if ('Nora opens the safe' if s['source'] == 'outline' else 'The brass key') in p['text']) for s in catalog['sources']}
        context = self.context(plan, catalog, [{'evidence_ids': [p['id'] for p in passages.values()]}])
        mapped = {row['source']: row['editable_paths'] for row in context['cited_evidence']}
        # The source passage contains the whole promise block, so every
        # overlapping editable field must remain available to the repairer.
        self.assertEqual(['/promises/0/promise', '/promises/0/setup_action',
                          '/promises/0/on_page_resolution'], mapped['outline'])
        self.assertEqual(['/canon/objects/0'], mapped['ledger'])

    def test_changed_rendered_source_cannot_inherit_a_prior_plan_address(self):
        plan, catalog, passage = self.source()
        plan['chapters'][7]['continuity'] = 'A different current custody fact.'
        with self.assertRaisesRegex(ValueError, 'Plan repair catalog differs'):
            self.context(plan, catalog, [{'evidence_ids': [passage['id']]}])

    def test_actual_planning_passes_bound_targets_and_retains_unrelated_plan_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze(root / '.book-genesis/project.json', encoded({'host': 'codex', 'collaboration': 'autonomous',
                'author_name': 'QA', 'model': 'exact-test-model', 'effort': 'high', 'idea': 'Return the letter.', 'language': 'English'}))
            freeze(root / '.book-genesis/skills/.book-genesis-install.json', b'{}')
            packets = []
            def generate(call_id, packet, schema, book):
                if 'architecture-repair-1' in call_id:
                    packets.append(packet)
                return fixture_response(call_id, packet, schema, book)
            with redirect_stdout(io.StringIO()):
                workflow = BookWorkflow(root, COMMAND, chapters=2, min_words=240, max_words=600,
                    transport=receipt_transport(generate))
                workflow.planning()
            self.assertEqual(1, len(packets))
            marker = '\nExact repair targets:\n'
            self.assertIn(marker, packets[0])
            context = json.loads(packets[0].split(marker, 1)[1].split('\nSupported defects:', 1)[0])
            original = read_json(root / 'work/plan-candidates/plan-0.json')
            approved = read_json(root / 'work/approved-plan.json')
            self.assertEqual(original['chapters'][0]['events'], context['editable_fields']['/chapters/0/events'])
            cited = {path for row in context['cited_evidence'] for path in row['editable_paths']}
            self.assertIn('/chapters/0/purpose', cited)
            self.assertIn('/chapters/0/point_of_view', cited)
            self.assertNotEqual(original['chapters'][0]['events'], approved['chapters'][0]['events'])
            self.assertEqual(original['chapters'][1], approved['chapters'][1])
            self.assertTrue(context['cited_evidence'])


if __name__ == '__main__':
    unittest.main()
