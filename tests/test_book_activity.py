from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from launcher.activity import collect_activity


class ActivityTests(unittest.TestCase):
    def test_active_request_is_reported_as_saved_state_not_proof_of_liveness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / '.book-genesis/workflow.json'
            path.parent.mkdir()
            path.write_text(json.dumps({'status': 'running', 'phase': 3, 'steps': {
                'draft-07': {'status': 'running', 'attempts': [{'status': 'reserved',
                    'call_id': 'wf-draft-07-1', 'reserved_at': '2026-10-25T12:00:00+00:00'}]}}}))
            before = path.read_bytes()
            result = collect_activity(root, now=datetime(2026, 10, 25, 12, 1, tzinfo=timezone.utc))
            self.assertEqual(60, result['requests'][0]['seconds_since_reserved'])
            self.assertEqual('Drafting chapter 7', result['requests'][0]['label'])
            self.assertEqual('not_checked', result['process_liveness'])
            self.assertEqual(before, path.read_bytes())

    def test_completed_and_invalid_journals_cannot_claim_active_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual('unavailable', collect_activity(root)['journal_status'])
            path = root / '.book-genesis/workflow.json'
            path.parent.mkdir()
            for payload in ('broken', '[]'):
                path.write_text(payload)
                result = collect_activity(root)
                self.assertEqual([], result['requests'])
                self.assertTrue(result['diagnostic'])
            path.write_text(json.dumps({'status': 'completed', 'phase': 8, 'steps': {}}))
            result = collect_activity(root)
            self.assertEqual('completed', result['journal_status'])
            self.assertEqual([], result['requests'])
            self.assertNotIn('literary_passed', result)

    def test_blocked_request_exposes_reason_without_reading_arbitrary_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / '.book-genesis/workflow.json'
            path.parent.mkdir()
            path.write_text(json.dumps({'status': 'blocked', 'phase': 3, 'steps': {
                'draft-07': {'status': 'failed', 'attempts': [{'status': 'failed',
                    'call_id': '../../secret', 'error': 'Native quota exhausted.'}]}}}))
            result = collect_activity(root)
            self.assertEqual('Native quota exhausted.', result['requests'][0]['detail'])
            self.assertIsNone(result['requests'][0]['seconds_since_reserved'])
