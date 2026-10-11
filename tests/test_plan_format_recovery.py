"""A plan format retry keeps the producer's full proposal and all conflicts."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from autonomous_book import BookWorkflow
from workflow_roles import apply_plan_edits, plan_schema
from workflow_state import digest, encoded, freeze, read_json
from test_autonomous_workflow import COMMAND, fixture_response, receipt_transport


class PlanFormatRecoveryTests(unittest.TestCase):
    def test_all_duplicate_fields_reported_without_applying_or_selecting_any(self):
        plan = fixture_response("architecture", "", plan_schema(2), Path('.'))
        before = encoded(plan)
        changes = [{"path": path, "after": value} for path in ("/chapters/0/events", "/chapters/1/events")
                   for value in ("One mutually exclusive scene.", "A different scene.")]
        with self.assertRaises(ValueError) as error:
            apply_plan_edits(plan, changes)
        self.assertIn("/chapters/0/events", str(error.exception))
        self.assertIn("/chapters/1/events", str(error.exception))
        self.assertIn("Consolidate", str(error.exception))
        self.assertEqual(before, encoded(plan))

    def test_actual_planning_retry_gets_unmodified_rejected_proposal_and_does_not_reset_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze(root / ".book-genesis/project.json", encoded({"host": "codex", "collaboration": "autonomous",
                "author_name": "QA", "model": "exact-test-model", "effort": "high", "idea": "Return the letter.", "language": "English"}))
            freeze(root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
            calls, repair_packets = [], []
            rejected = None
            def generate(call_id, packet, schema, book):
                nonlocal rejected
                calls.append(call_id)
                result = fixture_response(call_id, packet, schema, book)
                if "architecture-repair-1" in call_id:
                    repair_packets.append(packet)
                    if len(repair_packets) == 1:
                        result["edits"].append({**result["edits"][0], "after": "The courier must depart while the door stays closed."})
                        rejected = result
                return result
            options = dict(chapters=2, min_words=240, max_words=600, transport=receipt_transport(generate))
            with redirect_stdout(io.StringIO()):
                workflow = BookWorkflow(root, COMMAND, **options)
                workflow.planning()
                count = len(calls)
                BookWorkflow(root, COMMAND, **options).planning()
            self.assertEqual(2, len(repair_packets))
            self.assertIn("Duplicate plan edit paths", repair_packets[1])
            self.assertIn("The courier must depart while the door stays closed.", repair_packets[1])
            self.assertIn(rejected["edits"][0]["after"], repair_packets[1])
            step = workflow.journal.data["steps"]["architecture-repair-1"]
            self.assertEqual(2, len(step["attempts"]))
            self.assertEqual(count, len(calls))
            original = root / "work/host-calls/wf-architecture-repair-1-1"
            self.assertEqual(rejected, read_json(original / "response"))
            self.assertEqual(digest((original / "response").read_bytes()), read_json(original / "receipt.json")["response_sha256"])


if __name__ == "__main__":
    unittest.main()
