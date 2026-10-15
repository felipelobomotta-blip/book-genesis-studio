"""An unpublished creative group need not meet its final floor at every stage."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/book-genesis/scripts'))
import creative_groups as groups
from autonomous_book import BookWorkflow
from revision_context import decode_context
from workflow_state import encoded, freeze
from test_autonomous_workflow import COMMAND, receipt_transport
from test_creative_groups import group_report, comparison_report


class CoordinatedLengthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        freeze(self.root / '.book-genesis/project.json', encoded({'host': 'codex', 'collaboration': 'autonomous',
            'author_name': 'QA', 'model': 'exact-test-model', 'effort': 'high',
            'idea': 'A letter reaches its recipient.', 'language': 'English'}))
        freeze(self.root / '.book-genesis/skills/.book-genesis-install.json', b'{}')
        self.proposals = {1: self.prose(1, 'window', 100), 2: self.prose(2, 'courtyard', 350)}
        self.allowances, self.calls = {}, []
        self.workflow = BookWorkflow(self.root, COMMAND, chapters=3, min_words=600, max_words=800,
            transport=receipt_transport(self.generate))
        self.originals = {}
        for n in (1, 2, 3):
            raw = self.prose(n, 'lantern', 200).encode('utf-8')
            path = self.root / f'fixture/chapter-{n:02d}.md'
            freeze(path, raw)
            self.workflow.journal.publish(path, self.root / 'manuscript/chapters' / path.name)
            self.originals[path.name] = raw
        for name in ('00-brief.md', '03-characters.md', '05-voice.md', '09-continuity-ledger.md'):
            freeze(self.root / 'artifacts' / name, b'# Contract\n\nAda carries the letter; Jo holds the key.\n')
        self.tasks = [{'chapter': n, 'mode': 'creative', 'ticket': 'Coordinate the route scenes.',
            'preserve': 'Letter and key.', 'revision_class': 'prose', 'issue_ids': ['route']}
            for n in (1, 2)]

    @staticmethod
    def prose(number, word, count):
        return f'# Route {number}\n\n' + ' '.join([word] * count) + '\n'

    def generate(self, call_id, packet, schema, root):
        self.calls.append(call_id)
        if 'prose' in schema['properties']:
            value, _ = json.JSONDecoder().raw_decode('{"task":' + packet.split('\n\n{"task":', 1)[1])
            context = decode_context(value)
            n = context['task']['chapter']
            self.allowances.setdefault(n, []).append(context['production_words'])
            # No member is canonical while other proposals are being staged.
            for name, raw in self.originals.items():
                self.assertEqual(raw, (root / 'manuscript/chapters' / name).read_bytes())
            return {'prose': self.proposals[n], 'continuity_delta': 'Synthetic route candidate, not a book quality claim.'}
        if 'chapters' in schema['properties']:
            return group_report(packet, schema)
        if 'compare' in schema['properties']:
            return comparison_report(call_id, packet, schema, root)
        self.fail('Unexpected producer or review in staged-length fixture')

    def execute(self):
        with redirect_stdout(io.StringIO()):
            return groups.execute(self.workflow, 1, self.tasks, 'Coordinate both proposed route scenes.')

    def assert_originals(self):
        for name, raw in self.originals.items():
            self.assertEqual(raw, (self.root / 'manuscript/chapters' / name).read_bytes())

    def test_feasible_shortening_then_expansion_is_not_discarded_mid_group(self):
        outcomes = self.execute()
        self.assertTrue(all(row['decision'] == 'promote' for row in outcomes), outcomes)
        self.assertEqual(self.proposals[1].encode(), (self.root / 'manuscript/chapters/chapter-01.md').read_bytes())
        self.assertEqual(self.proposals[2].encode(), (self.root / 'manuscript/chapters/chapter-02.md').read_bytes())
        self.assertEqual(self.originals['chapter-03.md'], (self.root / 'manuscript/chapters/chapter-03.md').read_bytes())
        # Hand-counted final production:100+350+200=650 within600..800.
        self.assertEqual({'min': 100, 'max': 400}, self.allowances[1][0])
        self.assertEqual({'min': 300, 'max': 500}, self.allowances[2][0])
        before_calls = list(self.calls)
        before_allowance = (self.root / 'work/revisions/revision-1-c01/allowance.json').read_bytes()
        self.assertEqual(outcomes, self.execute())
        self.assertEqual(before_calls, self.calls)
        self.assertEqual(before_allowance, (self.root / 'work/revisions/revision-1-c01/allowance.json').read_bytes())

    def test_last_member_and_combined_gate_still_prevent_a_short_book(self):
        self.proposals[2] = self.prose(2, 'courtyard', 200)
        outcomes = self.execute()
        self.assertTrue(all(row['decision'] == 'reject' for row in outcomes), outcomes)
        self.assertEqual(300, self.allowances[2][0]['min'])
        self.assert_originals()
        self.assertFalse(any('-check-' in call or '-preference-' in call for call in self.calls))

    def test_first_member_still_needs_a_real_hundred_word_chapter(self):
        self.proposals[1] = self.prose(1, 'window', 99)
        outcomes = self.execute()
        first = next(row for row in outcomes if row['chapter'] == 1)
        self.assertEqual('reject', first['decision'])
        self.assertEqual(100, self.allowances[1][0]['min'])
        self.assertEqual(self.originals['chapter-01.md'], (self.root / 'manuscript/chapters/chapter-01.md').read_bytes())

    def test_standalone_chapter_keeps_its_whole_book_lower_allowance(self):
        with redirect_stdout(io.StringIO()):
            result = self.workflow.revise_chapter(1, self.tasks[0], 'Repair this scene only.')
        self.assertEqual('reject', result['decision'])
        self.assertEqual(200, self.allowances[1][0]['min'])
        self.assert_originals()

    def test_staged_chapter_without_future_members_keeps_existing_lower_allowance(self):
        with redirect_stdout(io.StringIO()):
            result = self.workflow.revise_chapter(1, self.tasks[0], 'Repair this scene only.', stage_only=True)
        self.assertEqual('reject', result['decision'])
        self.assertEqual(200, self.allowances[1][0]['min'])
        self.assert_originals()


if __name__ == '__main__':
    unittest.main()
