import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from launcher.autonomous import recorded_completion


class CompletionTests(unittest.TestCase):
    def test_exit_zero_alone_never_means_book_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual('completed_result_not_verified', recorded_completion(root, 0))
            self.assertEqual('incomplete', recorded_completion(root, 1))
            (root / 'delivery').mkdir()
            (root / 'evaluations').mkdir()
            (root / 'delivery/STATUS.json').write_text(json.dumps({'status': 'delivered'}))
            final = root / 'evaluations/final-measurement.json'
            final.write_text(json.dumps({'passed': False}))
            self.assertEqual('exported_draft_literary_gates_unmet', recorded_completion(root, 0))
            final.write_text(json.dumps({'passed': True}))
            self.assertEqual('export_and_literary_gates_reported_passed', recorded_completion(root, 0))
            final.write_text('[]')
            self.assertEqual('completed_result_not_verified', recorded_completion(root, 0))
