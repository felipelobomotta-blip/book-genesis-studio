"""Planning must not resend historical passages already present in full sources."""
from contextlib import redirect_stdout
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/book-genesis/scripts'))
from autonomous_book import BookWorkflow
from workflow_state import WorkflowError, encoded, freeze, read_json
from test_autonomous_workflow import COMMAND, receipt_transport


def small_context():
    body = '# One\r\n\r\n' + ''.join(f'Café {n}: Ada waits beside the gate — Jo holds the key.\r\n' for n in range(100))
    return {'current_sources': {'chapter-01.md': body, 'chapter-02.md': '# Two\n\nJo returns.\n'},
        'unresolved_findings': [{'id': 'old-01', 'requires_resolution': True,
            'finding': {'problem': 'The earlier record was ambiguous.'},
            'original_evidence': [{'source': 'chapter-01.md', 'text': body[200:2400]},
                                  {'source': 'chapter-02.md', 'text': 'An old sentence that no longer exists.'}]}],
        'earlier_strategies': [{'strategy': 'An earlier unsuccessful approach.'}],
        'earlier_revision_outcomes': [[{'chapter': 1, 'decision': 'reject'}]],
        'craft_knowledge': {'voice': 'Preserve human asymmetry.'},
        'reader_experience': [{'reader': 'casual', 'would_continue': False}]}


class RevisionPlanHandoffTests(unittest.TestCase):
    def build(self, root, factory, *, uncompressible=False, chapters=3):
        freeze(root / '.book-genesis/project.json', encoded({'host': 'codex', 'collaboration': 'autonomous',
            'author_name': 'QA', 'model': 'exact-test-model', 'effort': 'high',
            'idea': 'A letter reaches its recipient.', 'language': 'English'}))
        freeze(root / '.book-genesis/skills/.book-genesis-install.json', b'{}')
        command = copy.deepcopy(COMMAND)
        command['argv'].insert(2, '--ignore-user-config')
        workflow = BookWorkflow(root, command, chapters=chapters, min_words=chapters * 100, max_words=300000,
            transport=receipt_transport(factory))
        originals = {}
        for n in range(1, chapters + 1):
            body = (f'# Chapter {n}\n\n' + ''.join(
                f'Paragraph {i}: Ada carries the sealed letter past the courtyard wall and counts the lit windows.\n\n'
                for i in range(1800)))
            if uncompressible and n == 1:
                body += '\nUnique material with no historical copy. ' + 'x' * 1060000
            source = root / f'fixture/chapter-{n:02d}.md'
            freeze(source, body.encode('utf-8'))
            workflow.journal.publish(source, root / f'manuscript/chapters/{source.name}')
            originals[source.name] = body
        for name in ('00-brief.md', '02-story-engine.md', '03-characters.md', '04-theme.md',
                     '05-voice.md', '07-outline.md', '08-opening-strategy.md', '09-continuity-ledger.md'):
            freeze(root / 'artifacts' / name, b'# Contract\n\nAda carries the letter; Jo holds the key.\n')
        issues = [{'id': f'old-{i:02d}', 'requires_resolution': True,
                   'finding': {'problem': 'Correct the supported route dependency.', 'severity': 'high'},
                   'original_evidence': [{'source': 'chapter-01.md', 'text': originals['chapter-01.md'][2000:17000]}]}
                  for i in range(40)]
        measurement = {'number': 2, 'rubric': {'readings': [{'data': {'dimensions': [
            {'name': 'Coherence', 'reason': 'The route needs support.', 'evidence': ['s01p0001']}]}}]},
            'audit': {'data': {'findings': [], 'causal_traces': []}},
            'proofread': {'data': {'findings': []}}, 'panels': [{'reports': []}],
            'issue_ledger': {'open': issues}}
        workflow.journal.data['passes'] = [{'outcomes': [{'chapter': 1, 'decision': 'reject',
            'reason': 'Original negative outcome retained.'}]} for _ in range(2)]
        workflow.journal.data['strategies'] = [{'strategy': 'Original earlier strategy retained.',
            'tasks': []} for _ in range(2)]
        workflow.journal.save()
        return workflow, measurement, originals

    def test_large_actual_planner_reaches_native_with_complete_reconstructible_context(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            captured = []
            def generate(_id, packet, _schema, _root):
                self.assertLessEqual(len(packet), 1048576)
                value, _ = json.JSONDecoder().raw_decode(packet[packet.rfind('\n\n{') + 2:])
                from revision_plan_context import decode_plan_context
                context = decode_plan_context(value)
                self.assertEqual(40, len(context['unresolved_findings']))
                for issue in context['unresolved_findings']:
                    self.assertEqual(originals['chapter-01.md'][2000:17000], issue['original_evidence'][0]['text'])
                for name, text in originals.items():
                    self.assertEqual(text, context['current_sources'][name])
                self.assertEqual('Original earlier strategy retained.', context['earlier_strategies'][0]['strategy'])
                self.assertEqual('Original negative outcome retained.', context['earlier_revision_outcomes'][0][0]['reason'])
                self.assertNotIn('"quality_target"', packet)
                captured.append(packet)
                return {'strategy': 'Repair only the supported route dependency.', 'deferred': [],
                    'tasks': [{'chapter': 1, 'ticket': 'Repair the route.', 'preserve': 'Letter and key.',
                        'mode': 'creative', 'issue_ids': [f'old-{i:02d}' for i in range(40)],
                        'revision_class': 'continuity'}]}
            workflow, measurement, originals = self.build(root, generate)
            with redirect_stdout(io.StringIO()):
                try:
                    result = workflow.revision_plan(3, measurement)
                except WorkflowError as exc:
                    self.fail('The real planning handoff must fit without dropping evidence: ' + str(exc))
            self.assertEqual('creative', result['tasks'][0]['mode'])
            self.assertEqual(1, len(captured))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(result, workflow.revision_plan(3, measurement))
            self.assertEqual(1, len(captured))
            for name, text in originals.items():
                self.assertEqual(text.encode('utf-8'), (root / 'manuscript/chapters' / name).read_bytes())

    def test_retry_feedback_names_duplicate_pairs_and_where_to_attach_missing_issue(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            captured = []
            issue_id = 'measure-1-audit-f001'

            def generate(call_id, packet, _schema, _root):
                if call_id.endswith('-1'):
                    return {'strategy': 'Move the act turn earlier.', 'deferred': [], 'tasks': [
                        {'chapter': 3, 'ticket': 'Move the turn.', 'preserve': 'Keep the danger and route knowledge.',
                         'mode': 'creative', 'issue_ids': [], 'revision_class': 'structural'},
                        {'chapter': 3, 'ticket': 'Tighten the turn.', 'preserve': 'Keep the danger and route knowledge.',
                         'mode': 'creative', 'issue_ids': [], 'revision_class': 'structural'}]}
                captured.append(packet)
                return {'strategy': 'Move the act turn earlier.', 'deferred': [], 'tasks': [
                    {'chapter': 3, 'ticket': 'Move the turn by compressing pre-turn material.',
                     'preserve': 'Keep the failed piano move, physical danger, and Ruth\'s route knowledge.',
                     'mode': 'creative', 'issue_ids': [issue_id], 'revision_class': 'structural'}]}

            workflow, measurement, _ = self.build(root, generate)
            measurement['issue_ledger']['open'] = [{
                'id': issue_id, 'requires_resolution': True,
                'finding': {'chapters': [3], 'problem': 'The act turn is late.', 'severity': 'high'},
                'original_evidence': []}]
            with redirect_stdout(io.StringIO()):
                result = workflow.revision_plan(3, measurement)

            self.assertEqual([issue_id], result['tasks'][0]['issue_ids'])
            self.assertEqual(1, len(captured))
            retry_packet = captured[0]
            self.assertIn('chapter 3 creative', retry_packet)
            self.assertIn(issue_id, retry_packet)
            self.assertIn('affected chapter(s): 3', retry_packet)
            self.assertIn('consolidate', retry_packet.lower())

    def test_uncompressible_plan_stays_durably_blocked_without_dispatch_or_budget_reset(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            def forbidden(*_args):
                self.fail('Impossible native input must never be dispatched')
            workflow, measurement, _ = self.build(root, forbidden, uncompressible=True)
            with redirect_stdout(io.StringIO()), self.assertRaisesRegex(WorkflowError, 'character limit'):
                workflow.revision_plan(3, measurement)
            step = workflow.journal.data['steps']['revision-plan-3']
            self.assertEqual('blocked_input_size', step['status'])
            self.assertFalse(step['attempts'][0]['native_dispatched'])
            original_packet = (root / 'work/workflow/revision-plan-3/packet-attempt-1.md').read_bytes()
            self.assertIn(b'Unique material with no historical copy.', original_packet)
            self.assertGreater(len(original_packet.decode('utf-8')), 1048576)
            with redirect_stdout(io.StringIO()), self.assertRaisesRegex(WorkflowError, 'character limit'):
                workflow.revision_plan(3, measurement)
            self.assertEqual(1, len(workflow.journal.data['steps']['revision-plan-3']['attempts']))
            self.assertEqual(original_packet, (root / 'work/workflow/revision-plan-3/packet-attempt-1.md').read_bytes())


class PlanningSpanTests(unittest.TestCase):
    def test_small_context_keeps_original_packet_bytes(self):
        from revision_plan_context import render_plan_context
        value = small_context()
        self.assertEqual(json.dumps(value, ensure_ascii=False, sort_keys=True), render_plan_context(value))

    def test_unicode_line_endings_history_and_all_metadata_round_trip_without_mutation(self):
        from revision_plan_context import compact_plan_context, decode_plan_context
        value = small_context()
        before = encoded(value)
        view = compact_plan_context(value)
        self.assertEqual(before, encoded(decode_plan_context(view)))
        self.assertEqual(before, encoded(value))
        self.assertLess(len(encoded(view)), len(before))
        self.assertEqual('An old sentence that no longer exists.',
            view['unresolved_findings'][0]['original_evidence'][1]['text'])
        self.assertEqual(value['current_sources'], view['current_sources'])

    def test_matching_text_in_a_different_source_never_relabels_historical_evidence(self):
        from revision_plan_context import compact_plan_context, decode_plan_context
        value = small_context()
        value['unresolved_findings'][0]['original_evidence'][0]['source'] = 'missing-old-chapter.md'
        view = compact_plan_context(value)
        self.assertEqual(value['unresolved_findings'][0]['original_evidence'][0],
            view['unresolved_findings'][0]['original_evidence'][0])
        self.assertEqual(value, decode_plan_context(view))

    def test_stale_sources_ranges_hashes_and_metadata_are_rejected(self):
        from revision_plan_context import compact_plan_context, decode_plan_context
        view = compact_plan_context(small_context())
        for change in ('source', 'range', 'text_hash', 'context_hash', 'source_hash'):
            edited = copy.deepcopy(view)
            span = edited['unresolved_findings'][0]['original_evidence'][0]['text']['from_current_source']
            if change == 'source':
                edited['current_sources']['chapter-01.md'] += 'Changed.'
            elif change == 'range':
                span['start'] = True
            elif change == 'text_hash':
                span['sha256'] = '0' * 64
            elif change == 'context_hash':
                edited['_lossless_context']['original_context_sha256'] = '0' * 64
            else:
                edited['_lossless_context']['source_hashes']['chapter-01.md'] = '0' * 64
            with self.subTest(change=change), self.assertRaises(ValueError):
                decode_plan_context(edited)

    def test_reserved_metadata_cannot_be_silently_overwritten(self):
        from revision_plan_context import compact_plan_context
        value = small_context()
        value['_lossless_context'] = {'author_data': 'Must not disappear.'}
        with self.assertRaises(ValueError):
            compact_plan_context(value)


if __name__ == '__main__':
    unittest.main()
