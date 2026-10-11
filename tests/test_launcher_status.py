from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from launcher import status


def response(value, code=0, stderr=""):
    return subprocess.CompletedProcess([], code, json.dumps(value), stderr)


def progress():
    return {"schema_version": 1, "ok": True,
            "canonical": {"chapter_count": 6, "word_count": 7310},
            "state": {"chapter_count_planned": 6, "current_phase": "Phase 7: Editorial Package",
                      "gates": {"adversarial_audit": "revise", "revision_loop": "not_passed"}}}


def verified():
    return {"schema_version": 1, "delivery": {"status": "delivered"}, "reviews": {"status": "current"}}


class StatusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "PROJECT_STATE.yaml").write_text("preserve this state", encoding="utf-8")

    def collect(self, replies):
        with patch.object(status.subprocess, "run", side_effect=replies):
            report = status.collect_status(self.root, self.root / "scripts")
        self.assertEqual("preserve this state", (self.root / "PROJECT_STATE.yaml").read_text(encoding="utf-8"))
        return report

    def test_delivered_with_failed_literary_gates_does_not_appear_ready(self):
        report = self.collect([response(progress()), response(verified())])
        self.assertTrue(report["technical_checks_passed"])
        self.assertEqual("needs_revision", report["reported_quality_gates"])
        self.assertEqual("not_assessed", report["publication_approval"])
        with redirect_stdout(io.StringIO()) as output:
            status.print_status(report)
        self.assertIn("6/6 chapters | 7310 words", output.getvalue())
        self.assertIn("Editorial work remains", output.getvalue())
        self.assertIn("audit = revise", output.getvalue())

    def test_stale_evidence_fails_even_when_delivery_exists(self):
        result = verified()
        result["reviews"] = {"status": "stale", "errors": ["chapter-06 changed"]}
        report = self.collect([response(progress()), response(result, 1)])
        self.assertFalse(report["technical_checks_passed"])
        self.assertEqual(result, report["checks"]["verification"]["report"])
        with redirect_stdout(io.StringIO()) as output:
            status.print_status(report)
        self.assertIn("chapter-06 changed", output.getvalue())

    def test_zero_exit_with_invalid_or_conflicting_json_fails_closed(self):
        for value in ([], {}, {"schema_version": 1, "delivery": {"status": "missing"}, "reviews": {"status": "current"}}):
            with self.subTest(value=value):
                report = self.collect([response(progress()), response(value)])
                self.assertFalse(report["technical_checks_passed"])
                self.assertIn("invalid report", report["checks"]["verification"]["error"])

    def test_infrastructure_error_is_visible_and_other_check_still_runs(self):
        for error in (PermissionError("Access denied"), subprocess.TimeoutExpired(["check"], 60)):
            with self.subTest(error=error):
                report = self.collect([error, response(verified())])
                self.assertFalse(report["technical_checks_passed"])
                self.assertEqual("delivered", report["checks"]["verification"]["report"]["delivery"]["status"])
                with redirect_stdout(io.StringIO()) as output:
                    status.print_status(report)
                self.assertIn("could not finish", output.getvalue())

    def test_malformed_output_retains_diagnostic_and_never_claims_missing_book(self):
        report = self.collect([subprocess.CompletedProcess([], 7, "not json", "Permission denied"), response(verified())])
        self.assertFalse(report["technical_checks_passed"])
        self.assertEqual("not json", report["checks"]["progress"]["stdout"])
        with redirect_stdout(io.StringIO()) as output:
            status.print_status(report)
        self.assertIn("Permission denied", output.getvalue())
        self.assertIn("exit code: 7", output.getvalue())

    def test_passed_saved_gates_are_not_a_new_literary_evaluation(self):
        p = progress()
        p["state"]["gates"] = {"adversarial_audit": "passed", "revision_loop": "passed"}
        report = self.collect([response(p), response(verified())])
        self.assertEqual("reported_pass", report["reported_quality_gates"])
        self.assertEqual("not_assessed_by_this_tool", report["literary_quality"])

    def test_expected_pending_export_is_not_reported_as_a_failure_or_delivery(self):
        p = progress()
        p["state"].update(pipeline_status="in_progress", current_phase="Phase 3: Drafting")
        v = {"schema_version": 1, "delivery": {"status": "pending", "errors": ["no export receipt"]},
             "reviews": {"status": "not_run", "errors": ["no current-text review index supplied"]}}
        report = self.collect([response(p), response(v, 1)])
        self.assertFalse(report["technical_checks_passed"])
        self.assertTrue(report["completion_pending"])
        self.assertEqual(0, report["status_exit_code"])
        with redirect_stdout(io.StringIO()) as output:
            status.print_status(report)
        self.assertIn("Final export and full-book reader verification are still pending", output.getvalue())
        self.assertNotIn("Needs attention: no export receipt", output.getvalue())
        p["state"]["pipeline_status"] = "blocked"
        report = self.collect([response(p), response(v, 1)])
        self.assertFalse(report["completion_pending"])
        self.assertEqual(1, report["status_exit_code"])

    def test_controlled_final_index_is_used_and_failed_quality_is_visible(self):
        index = self.root / "evaluations/final-reader-index.json"
        index.parent.mkdir()
        index.write_text("{}", encoding="utf-8")
        p = progress()
        p["state"]["gates"] = {"adversarial_audit": "pass", "revision_loop": "gates_not_met"}
        with patch.object(status.subprocess, "run", side_effect=[response(p), response(verified())]) as run:
            report = status.collect_status(self.root, self.root / "scripts")
        self.assertIn(str(index), run.call_args_list[1].args[0])
        self.assertTrue(report["technical_checks_passed"])
        self.assertEqual("needs_revision", report["reported_quality_gates"])


if __name__ == "__main__":
    unittest.main()
