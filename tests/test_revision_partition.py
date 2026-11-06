"""A failed candidate blocks its dependents, not every shared issue member."""
import unittest
from pathlib import Path
import sys
import io
from contextlib import redirect_stdout
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/book-genesis/scripts'))
from workflow_roles import text_catalog


def fixture(edges=(), blocked=(4,)):
    catalog = text_catalog({f'{kind}/chapter-{n:02d}.md': f'# Scene {n}\n\n{kind} scene {n}.'
                            for kind in ('original', 'proposed') for n in range(1, 5)})
    ids = {s['source']: s['passages'][-1]['id'] for s in catalog['sources']}
    rows = []
    for n in range(1, 5):
        checks = [{'name': 'Canon and causal dependencies', 'result': 'block' if n in blocked else 'pass',
            'evidence_ids': [ids[f'proposed/chapter-{dep:02d}.md'] for own, dep in edges if own == n]}]
        rows.append({'chapter': n, 'checks': checks})
    return ({'publications': [{'chapter': n} for n in range(1, 5)],
             'tasks': [{'chapter': n, 'issue_ids': ['same-style-issue']} for n in range(1, 5)]}, catalog,
            {'verdict': 'block', 'chapters': rows, 'findings': [{'chapters': list(blocked)}]})


class RevisionPartitionTests(unittest.TestCase):
    def partition(self, edges=(), blocked=(4,)):
        from revision_partition import partition_review
        return partition_review(*fixture(edges, blocked))

    def test_shared_issue_does_not_bind_independent_revisions(self):
        result = self.partition()
        self.assertEqual([[1], [2], [3]], result['units'])
        self.assertEqual([4], result['blocked'])

    def test_failed_dependent_does_not_block_its_valid_prerequisite(self):
        result = self.partition([(4, 1)])
        self.assertEqual([[1], [2], [3]], result['units'])
        self.assertEqual([4], result['blocked'])

    def test_failed_prerequisite_blocks_transitive_dependents_only(self):
        result = self.partition([(2, 4), (1, 2)])
        self.assertEqual([[3]], result['units'])
        self.assertEqual([1, 2, 4], result['blocked'])

    def test_mutual_dependencies_remain_atomic_and_precede_dependents(self):
        result = self.partition([(1, 2), (2, 1), (3, 2)])
        self.assertEqual([[1, 2], [3]], result['units'])

    def test_unknown_passage_cannot_create_or_hide_dependency(self):
        from revision_partition import partition_review
        manifest, catalog, report = fixture()
        report['chapters'][0]['checks'][0]['evidence_ids'] = ['forged']
        with self.assertRaises(ValueError):
            partition_review(manifest, catalog, report)


class IndependentAcceptanceTests(unittest.TestCase):
    def setUp(self):
        from test_creative_groups import CreativeGroupTests
        from test_autonomous_workflow import receipt_transport
        self.base = CreativeGroupTests('test_complete_group_passes_both_gates_and_replays_without_new_calls')
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        self.root, self.workflow, self.tasks = self.base.root, self.base.workflow, self.base.tasks
        self.calls, self.dependent, self.block_unit = [], False, False
        self.chain, self.unit_canon = False, {}
        self.workflow.transport = receipt_transport(self.generate)

    def generate(self, call_id, packet, schema, root):
        from test_creative_groups import group_report
        from repair_evidence import parse_evidence_catalog
        self.calls.append(call_id)
        if 'chapters' not in schema['properties']:
            return self.base.generate(call_id, packet, schema, root)
        report = group_report(packet, schema)
        members = list(report['chapters'])
        catalog = parse_evidence_catalog(packet.split('\nSelected evidence wire:\n', 1)[1])
        if '-unit-' in call_id:
            self.unit_canon[tuple(members)] = {s['source']: '\n'.join(p['text'] for p in s['passages']) for s in catalog['sources']}
        bad = 'chapter-01' if '-unit-' in call_id and self.block_unit else 'chapter-03'
        if bad not in members:
            return report
        rejected = group_report(packet, schema, blocked=True)
        loc = {p['id']: s['source'] for s in catalog['sources'] for p in s['passages']}
        report['verdict'] = 'block'
        report['chapters'][bad]['checks']['Ticket resolution']['result'] = 'block'
        finding = rejected['findings'][0]
        finding['chapters'] = [int(bad[-2:])]
        for field in ('original_evidence', 'proposed_evidence'):
            finding[field] = [r for r in finding[field] if loc[r['passage_id']].endswith(bad + '.md')]
        report['findings'] = [finding]
        if self.dependent and 'chapter-01' in report['chapters'] and 'chapter-03' in report['chapters']:
            source = next(s for s in catalog['sources'] if s['source'] == 'proposed/chapter-03.md')
            report['chapters']['chapter-01']['checks']['Canon and causal dependencies']['supporting_evidence_ids'].append(source['passages'][-1]['id'])
        if self.chain and 'chapter-02' in report['chapters'] and 'chapter-01' in report['chapters']:
            source = next(s for s in catalog['sources'] if s['source'] == 'proposed/chapter-01.md')
            report['chapters']['chapter-02']['checks']['Canon and causal dependencies']['supporting_evidence_ids'].append(source['passages'][-1]['id'])
        return report

    def run_partition(self):
        from revision_partition import execute_partitioned
        with redirect_stdout(io.StringIO()):
            return execute_partitioned(self.workflow, 1, self.tasks, 'Repair the route while preserving independent work.')

    def assert_original(self):
        for name, raw in self.base.originals.items():
            self.assertEqual(raw, (self.root / 'manuscript/chapters' / name).read_bytes())

    def test_good_revision_publishes_after_fresh_gates_while_failed_original_remains(self):
        result = self.run_partition()
        self.assertEqual(['promote', 'reject'], [r['decision'] for r in result])
        self.assertIn('gate is closed', (self.root / 'manuscript/chapters/chapter-01.md').read_text())
        self.assertEqual(self.base.originals['chapter-03.md'], (self.root / 'manuscript/chapters/chapter-03.md').read_bytes())
        unit_calls = [c for c in self.calls if '-unit-' in c]
        self.assertEqual(1, len([c for c in unit_calls if '-check-' in c]))
        self.assertEqual(4, len([c for c in unit_calls if any('-' + reader + '-' in c for reader in ('primary','hostile','adjacent','casual'))]))
        count = len(self.calls)
        self.assertEqual(result, self.run_partition())
        self.assertEqual(count, len(self.calls))

    def test_failed_prerequisite_cannot_be_removed_to_publish_dependent(self):
        self.dependent = True
        self.assertTrue(all(r['decision'] == 'reject' for r in self.run_partition()))
        self.assertFalse(any('-unit-' in c for c in self.calls))
        self.assert_original()

    def test_new_dependency_failure_in_smaller_assembly_blocks_publication(self):
        self.block_unit = True
        self.assertTrue(all(r['decision'] == 'reject' for r in self.run_partition()))
        self.assertFalse(any('-primary-' in c for c in self.calls))
        self.assert_original()

    def test_negative_preference_still_keeps_originals(self):
        self.base.prefer = False
        self.assertTrue(all(r['decision'] == 'reject' for r in self.run_partition()))
        self.assert_original()

    def test_author_edit_after_unit_vote_prevents_stale_publication(self):
        original = self.workflow.compare_revision
        def changed_after_vote(*args, **kwargs):
            result = original(*args, **kwargs)
            (self.root / 'manuscript/chapters/chapter-02.md').write_text('Author changed this chapter.', encoding='utf-8')
            return result
        with patch.object(self.workflow, 'compare_revision', side_effect=changed_after_vote):
            with self.assertRaises(ValueError):
                self.run_partition()
        self.assertEqual(self.base.originals['chapter-01.md'], (self.root / 'manuscript/chapters/chapter-01.md').read_bytes())

    def test_next_unit_reviews_the_newly_accepted_sibling_as_current_canon(self):
        self.tasks.insert(1, {**self.tasks[0], 'chapter': 2})
        result = self.run_partition()
        self.assertEqual(['promote','promote','reject'], [r['decision'] for r in result])
        self.assertIn('gate is closed', self.unit_canon[('chapter-02',)]['original/chapter-01.md'])
        count = len(self.calls)
        self.assertEqual(result, self.run_partition())
        self.assertEqual(count, len(self.calls))

    def test_preference_failure_blocks_later_dependent_without_new_poll(self):
        self.tasks.insert(1, {**self.tasks[0], 'chapter': 2})
        self.chain, self.base.prefer = True, False
        self.assertTrue(all(r['decision'] == 'reject' for r in self.run_partition()))
        self.assertNotIn(('chapter-02',), self.unit_canon)
        self.assert_original()

    def test_interruption_after_unit_publication_resumes_without_new_votes(self):
        import creative_groups
        save = creative_groups.save_outcomes
        def interrupted(workflow, tasks, key, *args, **kwargs):
            if '-unit-' in key:
                raise RuntimeError('interrupt after guarded publication')
            return save(workflow, tasks, key, *args, **kwargs)
        with patch.object(creative_groups, 'save_outcomes', side_effect=interrupted):
            with self.assertRaisesRegex(RuntimeError, 'guarded publication'):
                self.run_partition()
        count = len(self.calls)
        self.assertEqual(['promote','reject'], [r['decision'] for r in self.run_partition()])
        self.assertEqual(count, len(self.calls))

    def test_changed_parent_evidence_blocks_replay(self):
        from workflow_state import read_json
        self.run_partition()
        manifest = next((self.root / 'work/creative-groups').glob('revision-1-creative*/manifest.json'))
        manifest.write_text('{}', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.run_partition()


if __name__ == '__main__':
    unittest.main()
