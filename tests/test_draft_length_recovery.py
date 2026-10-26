"""Near-boundary drafts get bounded, source-bound edits, never silent truncation."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/book-genesis/scripts'))
from autonomous_book import BookWorkflow
from workflow_state import Journal, WorkflowError, read_json, freeze, encoded
from workflow_roles import PROSE_SCHEMA, validate_prose
from test_autonomous_workflow import COMMAND, receipt_transport, fixture_response
from verify_book import verify_book


class DraftLengthRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.workflow = BookWorkflow.__new__(BookWorkflow)
        self.workflow.root = self.root
        self.workflow.command = COMMAND
        self.workflow.journal = Journal(self.root, {})
        self.original = '# Door\n\nThe very brass latch clicked.\n\n' + 'Word ' * 96
        self.calls = []
        self.repair = {'replacements': [{'before': 'The very brass latch clicked.', 'after': 'The brass latch clicked.'}]}
        def generate(call_id, packet, schema, root):
            self.calls.append(call_id)
            if 'replacements' in schema['properties']:
                return self.repair
            return {'prose': self.original, 'continuity_delta': 'The latch clicked.'}
        self.workflow.transport = receipt_transport(generate)

    def exhaust(self):
        with redirect_stdout(io.StringIO()), self.assertRaises(WorkflowError):
            self.workflow.call('draft-01', 'Draft a chapter.', PROSE_SCHEMA,
                lambda p: validate_prose(p, low=100, high=100), feedback=True, feedback_response=True)

    def recover(self):
        from draft_length_recovery import recover
        with redirect_stdout(io.StringIO()):
            return recover(self.workflow, 'draft-01', low=100, high=100)

    def test_one_word_over_is_edited_once_without_resetting_failed_draft_attempts(self):
        self.exhaust()
        original_response = self.root / 'work/host-calls/wf-draft-01-2/response'
        raw = original_response.read_bytes()
        result = self.recover()
        self.assertEqual(100, result['validation']['words'])
        self.assertEqual(self.original.replace('very ', ''), result['prose'])
        self.assertEqual(raw, original_response.read_bytes())
        self.assertEqual(2, len(self.workflow.journal.data['steps']['draft-01']['attempts']))
        self.assertEqual('failed', self.workflow.journal.data['steps']['draft-01']['status'])
        self.assertEqual(3, len(self.calls))
        self.assertEqual(result, self.recover())
        self.assertEqual(3, len(self.calls))
        self.assertEqual('The latch clicked.', read_json(result['source_response'])['continuity_delta'])
        original_response.write_bytes(raw + b' ')
        with self.assertRaises(WorkflowError):
            self.recover()

    def test_invalid_edits_exhaust_their_own_budget_without_relaxing_original_length(self):
        self.exhaust()
        self.repair = {'replacements': [{'before': 'not in the source', 'after': 'invented'}]}
        with self.assertRaises(WorkflowError):
            self.recover()
        self.assertEqual(4, len(self.calls))
        with self.assertRaises(WorkflowError):
            self.recover()
        self.assertEqual(4, len(self.calls))

    def test_large_length_error_or_invalid_prose_does_not_get_a_new_budget(self):
        self.original += ' extra' * 100
        self.exhaust()
        self.assertIsNone(self.recover())
        self.assertEqual(2, len(self.calls))

    def test_transport_failure_does_not_become_a_length_repair(self):
        def fail(*args):
            raise OSError('native auth unavailable')
        self.workflow.transport = fail
        self.exhaust()
        self.assertIsNone(self.recover())

    def test_single_word_overflow_cannot_authorize_rewriting_a_paragraph(self):
        self.original = '# Door\n\n' + ' '.join(f'word{i}' for i in range(101))
        self.exhaust()
        self.repair = {'replacements': [{'before': ' '.join(f'word{i}' for i in range(20)),
                                        'after': ' '.join(f'other{i}' for i in range(19))}]}
        with self.assertRaises(WorkflowError):
            self.recover()

    def test_saved_record_cannot_switch_to_another_failed_attempt(self):
        self.exhaust()
        result = self.recover()
        record = read_json(result['record_path'])
        first = self.workflow.journal.record_file(self.root / 'work/host-calls/wf-draft-01-1/response')
        self.assertIn(first, record['evidence'])
        record['source_response'] = first
        result['record_path'].write_bytes(encoded(record))
        with self.assertRaisesRegex(WorkflowError, 'final failed draft attempt'):
            self.recover()

    def test_recovery_survives_publication_interruptions_and_delivers_verified_export(self):
        for after_publication in (False, True):
            with self.subTest(after_publication=after_publication):
                root = self.root / str(after_publication)
                freeze(root / '.book-genesis/project.json', encoded({
                    'host': 'codex', 'collaboration': 'autonomous', 'author_name': 'QA',
                    'model': 'exact-test-model', 'effort': 'high', 'idea': 'A stolen letter returned.',
                    'language': 'English', 'autonomous_contract': {
                        'chapters': 2, 'min_words': 240, 'max_words': 600, 'quality_target': 8.5}}))
                freeze(root / '.book-genesis/skills/.book-genesis-install.json', b'{}')
                calls = []
                def generate(call_id, packet, schema, book):
                    calls.append(call_id)
                    if 'draft-01-length-repair' in call_id:
                        return self.repair
                    if call_id.startswith('wf-draft-01-'):
                        return {'prose': '# Chapter 1\n\nThe very brass latch clicked.\n\n' + 'Word ' * 496,
                                'continuity_delta': 'The latch clicked.'}
                    if call_id.startswith('wf-draft-02-'):
                        return {'prose': '# Chapter 2\n\nThe recipient opened the door.\n\n' + 'Word ' * 95,
                                'continuity_delta': 'The door opened.'}
                    return fixture_response(call_id, packet, schema, book)
                kwargs = dict(chapters=2, min_words=240, max_words=600, transport=receipt_transport(generate))
                with redirect_stdout(io.StringIO()):
                    workflow = BookWorkflow(root, COMMAND, **kwargs)
                    original_publish = workflow.journal.publish
                    def interrupt(source, target, **options):
                        if target.name == 'chapter-01.md' and not options.get('promote'):
                            if after_publication:
                                original_publish(source, target, **options)
                            raise KeyboardInterrupt()
                        return original_publish(source, target, **options)
                    with patch.object(workflow.journal, 'publish', side_effect=interrupt), self.assertRaises(KeyboardInterrupt):
                        workflow.run()
                    self.assertTrue((root / 'work/draft-length-recovery/draft-01.json').exists())
                    workflow = BookWorkflow(root, COMMAND, **kwargs)
                    self.assertEqual(0, workflow.run())
                self.assertEqual(3, sum('wf-draft-01-' in call for call in calls))
                draft = workflow.journal.data['steps']['draft-01']
                self.assertEqual('failed', draft['status'])
                self.assertEqual(2, len(draft['attempts']))
                later = (root / 'work/workflow/draft-02/packet.md').read_text(encoding='utf-8')
                self.assertIn('The latch clicked.', later)
                self.assertIn('Provisional writer summary', later)
                result = verify_book(root, 'evaluations/final-reader-index.json')
                self.assertEqual('delivered', result['delivery']['status'])
                self.assertTrue(list((root / 'delivery').glob('*.epub')))
                count = len(calls)
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(0, BookWorkflow(root, COMMAND, **kwargs).run())
                self.assertEqual(count, len(calls))


if __name__ == '__main__':
    unittest.main()
