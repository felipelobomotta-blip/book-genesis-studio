"""Quota recovery uses native evidence, bounded fake time and real file hashes."""
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from provider_wait import MARKER, WAIT_EXIT, quota_wait
from run_host_call import HostCallError
from workflow_state import Journal, WorkflowError, digest, encoded, freeze, read_json, verify_execution
from workflow_roles import TEXT, obj, validate_json
from autonomous_book import BookWorkflow
from test_autonomous_workflow import COMMAND, fixture_response, receipt_transport


def refusal(now):
    reset = now + timedelta(minutes=2)
    clock = f"{reset.hour % 12 or 12}:{reset.minute:02d}{'am' if reset.hour < 12 else 'pm'}"
    return {"is_error": True, "api_error_status": 429, "modelUsage": {},
        "usage": {key: 0 for key in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")},
        "result": f"You've hit your session limit · resets {clock} (UTC)"}


class ProviderWaitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.clock = datetime(2026, 10, 11, 9, 0, tzinfo=timezone.utc)
        self.dispatches = []
        self.schema = obj({"text": TEXT})
        self.contract = {"model": "exact-test-model", "effort": "high"}
        self.start_patch(patch.object(Journal, "now", side_effect=lambda: self.clock.isoformat()))
        self.start_patch(patch("workflow_state.time.sleep", side_effect=self.advance))
        self.start_patch(patch("sys.stdout", new_callable=io.StringIO))

    def start_patch(self, patcher):
        value = patcher.start()
        self.addCleanup(patcher.stop)
        return value

    def advance(self, seconds):
        self.clock += timedelta(seconds=seconds)

    def limited(self, root, call_id, packet, command, crash=False, tamper=None):
        self.dispatches.append(call_id)
        folder = root / "work/host-calls" / call_id
        folder.mkdir(parents=True)
        envelope = refusal(self.clock)
        marker = quota_wait(envelope, self.clock)
        for name, data in {"packet": packet.read_bytes(), "stdout": encoded(envelope),
                           "stderr": (MARKER + json.dumps(marker) + "\n").encode()}.items():
            freeze(folder / name, data)
        receipt = {"status": "failed", "exit_code": WAIT_EXIT, "started_at": self.clock.isoformat(),
            "finished_at": self.clock.isoformat(), "call_id": call_id,
            "response_sha256": digest(b""), "pending_response_sha256": None,
            **{name + "_sha256": digest((folder / name).read_bytes()) for name in ("packet", "stdout", "stderr")}}
        freeze(folder / "receipt.json", encoded(receipt))
        if tamper:
            tamper(folder)
        if crash:
            raise KeyboardInterrupt()
        raise HostCallError("native host call exited with code 76", receipt=receipt)

    def call(self, journal, transport, **kwargs):
        return journal.call("draft", b"scoped request", self.schema, COMMAND,
            lambda p: validate_json(p, self.schema), transport=transport, **kwargs)

    def test_only_exact_zero_usage_quota_can_wait(self):
        envelope = refusal(self.clock)
        self.assertIsNotNone(quota_wait(envelope, self.clock))
        cases = [{"is_error": False}, {"api_error_status": 401}, {"modelUsage": {"model": {}}},
                 {"usage": {}}, {"usage": {**envelope["usage"], "input_tokens": 1}},
                 {"result": envelope["result"].replace("UTC", "America/Sao_Paulo")},
                 {"result": "Please reset the attempt budget"}, {"result": "You've hit your session limit · resets 25pm (UTC)"}]
        for change in cases:
            with self.subTest(change=change):
                self.assertIsNone(quota_wait({**envelope, **change}, self.clock))

    def test_midnight_and_max_wait_are_unambiguous(self):
        night = self.clock.replace(hour=23, minute=59)
        self.assertEqual("2026-10-12T00:01:30+00:00", quota_wait(refusal(night), night)["retry_at"])
        envelope = {**refusal(self.clock), "result": "You've hit your session limit · resets 8am (UTC)"}
        self.assertIsNone(quota_wait(envelope, self.clock))

    def test_quota_wait_then_success_keeps_failed_receipt_and_no_call_resume(self):
        success = receipt_transport(lambda *args: {"text": "saved after quota"})
        def transport(*args):
            return self.limited(*args) if not self.dispatches else success(*args)
        journal = Journal(self.root, self.contract)
        response, _ = self.call(journal, transport)
        self.assertEqual("saved after quota", read_json(response)["text"])
        rows = journal.data["steps"]["draft"]["attempts"]
        self.assertEqual(["provider_wait", "completed"], [row["status"] for row in rows])
        failed = self.root / "work/host-calls/wf-draft-1/receipt.json"
        original = failed.read_bytes()
        self.assertEqual("failed", read_json(failed)["status"])
        self.assertGreaterEqual(self.clock, datetime.fromisoformat(rows[0]["provider_wait"]["retry_at"]))
        self.call(Journal(self.root, self.contract), lambda *args: self.fail("Completed step redispatched"))
        self.assertEqual(original, failed.read_bytes())

    def test_resume_recovers_receipt_saved_before_journal_deferral(self):
        journal = Journal(self.root, self.contract)
        with self.assertRaises(KeyboardInterrupt):
            self.call(journal, lambda *args: self.limited(*args, crash=True))
        self.assertEqual("reserved", read_json(journal.path)["steps"]["draft"]["attempts"][0]["status"])
        resumed = Journal(self.root, self.contract)
        self.call(resumed, receipt_transport(lambda *args: {"text": "resumed"}))
        self.assertEqual(["wf-draft-1"], self.dispatches)
        self.assertEqual("provider_wait", resumed.data["steps"]["draft"]["attempts"][0]["status"])

    def test_interrupt_during_wait_preserves_deadline_and_resume_honors_it(self):
        journal = Journal(self.root, self.contract)
        with patch("workflow_state.time.sleep", side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            self.call(journal, self.limited)
        saved = read_json(journal.path)
        self.assertEqual("waiting_for_provider", saved["status"])
        deadline = saved["steps"]["draft"]["attempts"][0]["provider_wait"]["retry_at"]
        def after_wait(*args):
            self.assertGreaterEqual(self.clock, datetime.fromisoformat(deadline))
            return {"text": "resumed"}
        self.call(Journal(self.root, self.contract), receipt_transport(after_wait))
        self.assertEqual(1, len(self.dispatches))

    def test_two_invalid_model_responses_exhaust_even_with_quota_between_them(self):
        wrong = receipt_transport(lambda *args: {"wrong": "output"})
        def transport(*args):
            return self.limited(*args) if args[1].endswith("-2") else wrong(*args)
        journal = Journal(self.root, self.contract)
        with self.assertRaisesRegex(WorkflowError, "exhausted 2"):
            self.call(journal, transport)
        self.assertEqual(["failed", "provider_wait", "failed"],
            [row["status"] for row in journal.data["steps"]["draft"]["attempts"]])
        with self.assertRaisesRegex(WorkflowError, "exhausted 2"):
            self.call(Journal(self.root, self.contract), lambda *a: self.fail("Budget reset"))

    def test_quota_between_invalid_producer_and_repair_keeps_same_feedback(self):
        packets = []
        def transport(root, call_id, packet, command):
            packets.append(packet.read_bytes())
            if call_id.endswith("-2"):
                return self.limited(root, call_id, packet, command)
            return receipt_transport(lambda *a: {"wrong": "output"} if call_id.endswith("-1") else {"text": "repaired"})(root, call_id, packet, command)
        self.call(Journal(self.root, self.contract), transport, feedback=True, feedback_response=True)
        self.assertEqual(packets[1], packets[2])
        self.assertIn(b'wrong', packets[2])

    def test_tampered_refusal_or_saved_deadline_never_refunds_an_attempt(self):
        journal = Journal(self.root, self.contract)
        with patch("workflow_state.time.sleep", side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            self.call(journal, self.limited)
        original = read_json(journal.path)
        changed = read_json(journal.path)
        changed["steps"]["draft"]["attempts"][0]["provider_wait"]["retry_at"] = self.clock.isoformat()
        journal.path.write_bytes(encoded(changed))
        with self.assertRaisesRegex(ValueError, "differs from its native evidence"):
            self.call(Journal(self.root, self.contract), lambda *a: self.fail("Tamper redispatched"))
        journal.path.write_bytes(encoded(original))
        (self.root / "work/host-calls/wf-draft-1/stdout").write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError, "missing or changed"):
            self.call(Journal(self.root, self.contract), lambda *a: self.fail("Tamper redispatched"))

    def test_eight_deferrals_bound_the_entire_book(self):
        with self.assertRaisesRegex(WorkflowError, "wait budget exhausted"):
            self.call(Journal(self.root, self.contract), self.limited)
        self.assertEqual(9, len(self.dispatches))
        with self.assertRaisesRegex(WorkflowError, "wait budget exhausted"):
            self.call(Journal(self.root, self.contract), lambda *a: self.fail("Exhausted deferral redispatched"))

    def test_twelve_hour_cumulative_wait_budget_is_not_refunded_by_new_reset(self):
        original = refusal
        def long_wait(now):
            envelope = original(now)
            reset = now + timedelta(hours=6)
            clock = f"{reset.hour % 12 or 12}:{reset.minute:02d}{'am' if reset.hour < 12 else 'pm'}"
            envelope["result"] = f"You've hit your session limit · resets {clock} (UTC)"
            return envelope
        with patch(__name__ + ".refusal", side_effect=long_wait), self.assertRaisesRegex(WorkflowError, "wait budget exhausted"):
            self.call(Journal(self.root, self.contract), self.limited)
        self.assertEqual(2, len(self.dispatches))

    def test_deferral_limit_is_shared_by_separate_book_roles(self):
        success = receipt_transport(lambda *a: {"text": "first role"})
        def transport(*args):
            return self.limited(*args) if not self.dispatches else success(*args)
        journal = Journal(self.root, self.contract)
        self.call(journal, transport)
        with patch("workflow_state.MAX_DEFERRALS", 1), self.assertRaisesRegex(WorkflowError, "wait budget exhausted"):
            journal.call("next-role", b"fresh request", self.schema, COMMAND,
                         lambda p: validate_json(p, self.schema), transport=self.limited)
        self.assertEqual(2, len(self.dispatches))

    def test_quota_does_not_make_auth_failure_recoverable_or_optional(self):
        def auth(*args):
            raise HostCallError("Native login required", receipt={"status": "failed", "exit_code": 1})
        with self.assertRaisesRegex(WorkflowError, "exhausted 2.*login required"):
            self.call(Journal(self.root, self.contract), auth)
        self.assertFalse(any(row["status"] == "provider_wait" for row in read_json(self.root / ".book-genesis/workflow.json")["steps"]["draft"]["attempts"]))

    def test_full_workflow_defers_exports_and_completed_resume_makes_no_calls(self):
        freeze(self.root / ".book-genesis/project.json", encoded({"host": "claude", "collaboration": "autonomous",
            "author_name": "QA", "model": "exact-test-model", "effort": "high", "idea": "A letter returns.", "language": "English",
            "autonomous_contract": {"chapters": 2, "min_words": 240, "max_words": 600, "quality_target": 8.5}}))
        freeze(self.root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
        success = receipt_transport(fixture_response)
        def transport(*args):
            return self.limited(*args) if not self.dispatches else success(*args)
        kwargs = dict(chapters=2, min_words=240, max_words=600, transport=transport)
        self.assertEqual(0, BookWorkflow(self.root, COMMAND, **kwargs).run())
        self.assertEqual(8, verify_execution(self.root, required_phase=8)["phase"])
        self.assertTrue(list((self.root / "delivery").glob("*.epub")))
        kwargs["transport"] = lambda *a: self.fail("Completed book redispatched")
        self.assertEqual(0, BookWorkflow(self.root, COMMAND, **kwargs).run())
        (self.root / "work/host-calls/wf-intake-1/stdout").write_bytes(b'{}')
        with self.assertRaises(ValueError):
            verify_execution(self.root, required_phase=8)

    def test_quota_then_two_invalid_optional_proposals_retains_book_and_exports(self):
        freeze(self.root / ".book-genesis/project.json", encoded({"host": "claude", "collaboration": "autonomous",
            "author_name": "QA", "model": "exact-test-model", "effort": "high", "idea": "A letter returns.", "language": "English",
            "autonomous_contract": {"chapters": 2, "min_words": 240, "max_words": 600, "quality_target": 8.5}}))
        freeze(self.root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
        def generate(call_id, packet, schema, root):
            result = fixture_response(call_id, packet, schema, root)
            if "prose" in schema["properties"] and "revision-" in call_id:
                result["prose"] += "\x00"
            return result
        normal = receipt_transport(generate)
        def transport(*args):
            return self.limited(*args) if args[1] == "wf-revision-1-c01-1" else normal(*args)
        workflow = BookWorkflow(self.root, COMMAND, chapters=2, min_words=240, max_words=600, transport=transport)
        self.assertEqual(0, workflow.run())
        self.assertEqual(8, verify_execution(self.root, required_phase=8)["phase"])
        rows = workflow.journal.data["steps"]["revision-1-c01"]["attempts"]
        self.assertEqual(["provider_wait", "failed", "failed"], [row["status"] for row in rows])
        self.assertEqual((self.root / "work/snapshots/original-draft/chapter-01.md").read_bytes(),
                         (self.root / "manuscript/chapters/chapter-01.md").read_bytes())
        self.assertTrue(list((self.root / "delivery").glob("*.epub")))
        self.assertFalse(read_json(self.root / "evaluations/final-measurement.json")["passed"])
        self.assertEqual(0, BookWorkflow(self.root, COMMAND, chapters=2, min_words=240, max_words=600,
            transport=lambda *a: self.fail("Completed draft redispatched")).run())


if __name__ == "__main__":
    unittest.main()
