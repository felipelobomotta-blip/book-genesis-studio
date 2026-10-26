"""Long allegation histories retain every issue and complete current sources."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/book-genesis/scripts'))
from autonomous_book import BookWorkflow
from workflow_state import Journal, WorkflowError, freeze
import workflow_issues as issues_module
from test_autonomous_workflow import COMMAND, receipt_transport


class IssueBatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.workflow = BookWorkflow.__new__(BookWorkflow)
        self.workflow.root = self.root
        self.workflow.command = COMMAND
        self.workflow.journal = Journal(self.root, {})
        self.texts = {'chapter-01.md': '# One\n\nThe latch clicked.\n\nThe door opened.'}
        self.workflow.neutral_sources = lambda snapshot: self.texts
        self.snapshot = [self.root / 'chapter-01.md']
        freeze(self.snapshot[0], self.texts['chapter-01.md'].encode())
        self.issues = [{'id': f'issue-{i}', 'requires_resolution': True,
                        'finding': {'chapters': [1], 'problem': 'Original allegation.'},
                        'original_evidence': [{'source': 'chapter-01.md', 'text': 'Quote ' * 45}]}
                       for i in range(3)]
        self.packets = []
        self.schemas = []
        self.invalid = False
        def response(call_id, packet, schema, root):
            self.packets.append((call_id, packet))
            self.schemas.append(schema)
            catalog = json.JSONDecoder().raw_decode(packet.split('Current complete sources:\n', 1)[1])[0]
            ids = schema['properties']['statuses']['items']['properties']['id']['enum']
            return {'statuses': [{'id': identifier, 'status': 'resolved', 'reason': 'Current action resolves the allegation.',
                                  'evidence_ids': ['invented' if self.invalid else catalog['sources'][0]['passages'][1]['id']]}
                                 for identifier in ids]}
        self.workflow.transport = receipt_transport(response)

    def reconcile(self):
        with patch.object(issues_module, 'collect_issues', return_value=self.issues), \
                patch.object(issues_module, 'MAX_HISTORY_CHARS', 600), redirect_stdout(io.StringIO()):
            return issues_module.reconcile_issues(self.workflow, 0, self.snapshot)

    def test_every_issue_and_complete_source_survive_batches_and_interrupted_resume(self):
        original_call = self.workflow.call
        def interrupt(*args, **kwargs):
            original_call(*args, **kwargs)
            raise KeyboardInterrupt()
        with patch.object(self.workflow, 'call', side_effect=interrupt), self.assertRaises(KeyboardInterrupt):
            self.reconcile()
        result = self.reconcile()
        self.assertTrue(result['passed'])
        self.assertEqual(3, len(self.packets))
        self.assertEqual([i['id'] for i in self.issues], [s['id'] for s in result['statuses']])
        for _, packet in self.packets:
            catalog = json.loads(packet.split('Current complete sources:\n', 1)[1])
            self.assertEqual(['# One', 'The latch clicked.', 'The door opened.'],
                             [p['text'] for p in catalog['sources'][0]['passages']])
        self.workflow.journal.verify_files(result['evidence'])
        self.assertEqual(result, self.reconcile())
        self.assertEqual(3, len(self.packets))

    def test_invalid_current_passage_ids_never_resolve_an_issue(self):
        self.invalid = True
        result = self.reconcile()
        self.assertFalse(result['passed'])
        self.assertEqual(3, len(result['open']))
        self.assertEqual(6, len(self.packets))
        self.workflow.journal.verify_files(result['evidence'])

    def test_native_schema_distinguishes_issue_ids_from_current_passage_ids(self):
        self.reconcile()
        for schema in self.schemas:
            fields = schema['properties']['statuses']['items']['properties']
            allowed = fields['evidence_ids']['items'].get('enum', [])
            self.assertEqual(['s01p0001', 's01p0002', 's01p0003'], allowed)
            self.assertFalse(set(allowed).intersection(fields['id']['enum']))

    def test_unrepresentable_single_issue_fails_before_native_calls_without_omission(self):
        with patch.object(issues_module, 'MAX_REQUEST_CHARS', 100), self.assertRaises(WorkflowError):
            self.reconcile()
        self.assertEqual([], self.packets)


if __name__ == '__main__':
    unittest.main()
