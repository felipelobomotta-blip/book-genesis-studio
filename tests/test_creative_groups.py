"""Dependent creative repairs are compared and published as complete versions."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
import correction_groups as transactions
import creative_groups as groups
from autonomous_book import BookWorkflow
from workflow_state import WorkflowError, encoded, freeze, read_json, verify_execution
from test_autonomous_workflow import COMMAND, receipt_transport, fixture_response


def group_report(packet, schema, blocked=False):
    catalog = json.JSONDecoder().raw_decode(packet.split("\nSources:\n", 1)[1])[0]
    sources = {s["source"]: s for s in catalog["sources"]}
    members = schema["properties"]["chapters"]["items"]["properties"]["chapter"]["enum"]
    return {"catalog_sha256": schema["properties"]["catalog_sha256"]["enum"][0],
        "verdict": "block" if blocked else "pass", "coverage": list(sources),
        "chapters": [{"chapter": n, "checks": [{"name": name, "result": "block" if blocked else "pass",
            "reason": "Synthetic coordinated repair evidence.", "evidence_ids": [sources[s]["passages"][-1]["id"] for s in
                (f"original/chapter-{n:02d}.md", f"proposed/chapter-{n:02d}.md", "contract/00-brief.md")]}
            for name in groups.CHECKS]} for n in members],
        "findings": [{
            "kind": "unresolved_ticket", "chapters": members,
            "problem": "The paired rescue is still inconsistent.",
            "causal_test": "Synthetic code fixture keeps the assigned rescue unresolved.",
            "limitations": "Synthetic negative judgment, not a native literary verdict.",
            **{field: [{"passage_id": sources[f"{prefix}/chapter-{n:02d}.md"]["passages"][-1]["id"],
                        "quote": sources[f"{prefix}/chapter-{n:02d}.md"]["passages"][-1]["text"]}
                       for n in members] for field, prefix in
               (("original_evidence", "original"), ("proposed_evidence", "proposed"))},
            "supporting_evidence": [],
        }] if blocked else [], "limitations": "Synthetic code test only."}


def comparison_report(call_id, packet, schema, root, prefer=True):
    # The synthetic test can inspect the mapping; native readers cannot.
    stripped = json.loads(json.dumps(schema))
    stripped["properties"].pop("compare")
    result = fixture_response(call_id, packet, stripped, root)
    result["schema_version"] = 3
    paths = list((root / "work/comparisons").glob("*-preference/manifest.private.json"))
    manifest = read_json(paths[-1])
    assignment = next(r for r in manifest["readers"] if r["reader"] == result["reader"])
    result["compare"] = next(label for label, kind in assignment["mapping"].items() if kind == ("candidate" if prefer else "accepted"))
    return result


class CreativeGroupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        freeze(self.root / ".book-genesis/project.json", encoded({"host": "codex", "collaboration": "autonomous",
            "author_name": "QA", "model": "exact-test-model", "effort": "high", "idea": "Rescue through the gate.", "language": "English"}))
        freeze(self.root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
        self.calls, self.block, self.prefer, self.malformed, self.noop = [], False, True, False, False
        self.workflow = self.new_workflow()
        self.originals = {}
        for n in (1, 2, 3):
            text = (f"# Gate {n}\n\nThe passage is open.\n\n" + "She carried the lantern along the lane. " * 20 + "\n")
            p = self.root / "original" / f"chapter-{n:02d}.md"
            freeze(p, text.encode())
            self.workflow.journal.publish(p, self.root / "manuscript/chapters" / p.name)
            self.originals[p.name] = text.encode()
        for n in ("00-brief.md", "03-characters.md", "05-voice.md", "09-continuity-ledger.md"):
            freeze(self.root / "artifacts" / n, b"# Contract\n\nRescue the courier without changing identity or location.\n")
        self.tasks = [{"chapter": n, "mode": "creative", "ticket": "Choose a closed gate and route the escape through the window.",
            "preserve": "Lantern, character and setting.", "revision_class": "continuity", "issue_ids": ["route"]} for n in (1, 3)]

    def new_workflow(self):
        return BookWorkflow(self.root, COMMAND, chapters=3, min_words=400, max_words=1500,
                            transport=receipt_transport(self.generate))

    def generate(self, call_id, packet, schema, root):
        self.calls.append(call_id)
        props = schema["properties"]
        if "prose" in props:
            context = json.loads(packet.rsplit("\n\n", 1)[1])
            self.assertEqual(1, len(context["companion_tasks"]))
            if context["task"]["chapter"] == 3:
                self.assertIn("closed", context["unaccepted_companion_proposals"]["chapter-01.md"])
                self.assertIn("open", context["other_current_chapters"]["chapter-01.md"])
            prose = context["accepted_chapter"]
            if not (self.noop and context["task"]["chapter"] == 3):
                prose = prose.replace("The passage is open.", "The gate is closed. She chooses the window.")
            return {"prose": prose, "continuity_delta": "The gate is closed; she uses the window."}
        if "chapters" in props:
            return {"verdict": "pass"} if self.malformed else group_report(packet, schema, self.block)
        if "compare" in props:
            self.assertIn("Gate 1", packet)
            self.assertIn("Gate 2", packet)
            self.assertIn("Gate 3", packet)
            self.assertNotIn('"tasks"', packet)
            return comparison_report(call_id, packet, schema, root, self.prefer)
        raise AssertionError(call_id)

    def run_group(self):
        with redirect_stdout(io.StringIO()):
            return groups.execute(self.workflow, 1, self.tasks, "Close the gate in both affected chapters and use the window.")

    def assert_originals(self):
        for name, raw in self.originals.items():
            self.assertEqual(raw, (self.root / "manuscript/chapters" / name).read_bytes())

    def test_complete_group_passes_both_gates_and_replays_without_new_calls(self):
        result = self.run_group()
        self.assertTrue(all(r["decision"] == "promote" for r in result))
        for n in (1, 3):
            self.assertIn("gate is closed", (self.root / f"manuscript/chapters/chapter-{n:02d}.md").read_text())
        self.assertEqual(self.originals["chapter-02.md"], (self.root / "manuscript/chapters/chapter-02.md").read_bytes())
        self.assertEqual(7, len(self.calls))
        self.workflow = self.new_workflow()
        self.assertEqual(result, self.run_group())
        self.assertEqual(7, len(self.calls))

    def test_dependency_rejection_keeps_every_original_without_a_preference_poll(self):
        self.block = True
        self.assertTrue(all(r["decision"] == "reject" for r in self.run_group()))
        self.assert_originals()
        self.assertEqual(3, len(self.calls))
        self.run_group()
        self.assertEqual(3, len(self.calls))

    def test_preference_rejection_cannot_be_overridden_by_repair_checker(self):
        self.prefer = False
        self.assertTrue(all(r["decision"] == "reject" for r in self.run_group()))
        self.assert_originals()
        self.assertEqual(7, len(self.calls))

    def test_two_malformed_group_reports_preserve_originals_and_bounded_attempts(self):
        self.malformed = True
        self.assertTrue(all(r["decision"] == "reject" for r in self.run_group()))
        self.assert_originals()
        self.assertEqual(4, len(self.calls))

    def test_missing_original_feedback_identifies_exact_member_and_check_before_bounded_retry(self):
        original = self.generate
        attempts = []
        def omit_original(call_id, packet, schema, root):
            report = original(call_id, packet, schema, root)
            if "chapters" not in schema["properties"]:
                return report
            attempts.append(call_id)
            if len(attempts) == 1:
                member = next(r for r in report["chapters"] if r["chapter"] == 3)
                check = next(c for c in member["checks"] if c["name"] == "Preserved strengths")
                check["evidence_ids"] = check["evidence_ids"][1:]
            else:
                self.assertIn("Chapter 3, check 'Preserved strengths'", packet)
                self.assertIn("missing evidence from original/chapter-03.md", packet)
                self.assertNotIn("missing evidence from original/chapter-01.md", packet)
            return report
        self.workflow.transport = receipt_transport(omit_original)
        self.assertTrue(all(r["decision"] == "promote" for r in self.run_group()))
        self.assertEqual(2, len(attempts))
        self.assertEqual(8, len(self.calls))
        step = self.workflow.journal.data["steps"]["revision-1-creative-group-1-3-check"]
        self.assertTrue(step["attempts"][-1].get("feedback_evidence"))
        self.assertFalse(read_json(self.root / "work/workflow/revision-1-creative-group-1-3-check/validation-1.json")["valid"])
        self.workflow = self.new_workflow()
        self.run_group()
        self.assertEqual(8, len(self.calls))
        response = self.root / "work/host-calls" / attempts[0] / "response"
        response.write_bytes(response.read_bytes() + b" ")
        with self.assertRaisesRegex(WorkflowError, "evidence is missing or changed"):
            self.run_group()

    def test_unchanged_member_cannot_partially_publish_the_group(self):
        self.noop = True
        self.assertTrue(all(r["decision"] == "reject" for r in self.run_group()))
        self.assert_originals()
        self.assertEqual(2, len(self.calls))

    def interrupt(self):
        original = transactions.replace_verified
        count = 0
        def fail_second(*args):
            nonlocal count
            count += 1
            if count == 2:
                raise KeyboardInterrupt()
            return original(*args)
        with patch.object(transactions, "replace_verified", side_effect=fail_second), self.assertRaises(KeyboardInterrupt):
            self.run_group()

    def test_crash_between_members_resumes_exact_approved_group_without_repolling(self):
        self.interrupt()
        self.assertEqual("creative_revision_group", read_json(self.workflow.journal.path)["pending_mutation"]["kind"])
        self.workflow = self.new_workflow()
        self.assertTrue(all(r["decision"] == "promote" for r in self.run_group()))
        self.assertEqual(7, len(self.calls))

    def test_changed_native_vote_blocks_recovery_before_next_member(self):
        self.interrupt()
        p = next((self.root / "work/host-calls").glob("*preference-primary-*/response"))
        p.write_bytes(p.read_bytes() + b" ")
        with self.assertRaisesRegex(WorkflowError, "evidence is missing or changed"):
            self.new_workflow()
        self.assertEqual(self.originals["chapter-03.md"], (self.root / "manuscript/chapters/chapter-03.md").read_bytes())

    def test_concurrent_author_edit_is_preserved_during_recovery(self):
        self.interrupt()
        target = self.root / "manuscript/chapters/chapter-03.md"
        target.write_bytes(b"The author's new scene.")
        with self.assertRaisesRegex(WorkflowError, "collided with a target edit"):
            self.new_workflow()
        self.assertEqual(b"The author's new scene.", target.read_bytes())

    def test_comparison_view_must_keep_the_entire_original_and_proposed_book(self):
        self.run_group()
        path = self.root / "work/creative-groups/revision-1-creative-group-1-3/manifest.json"
        manifest = read_json(path)
        actual = groups.volume(self.workflow.journal, manifest, False).decode()
        for raw in self.originals.values():
            self.assertIn("#" + raw.decode(), actual)
        p = self.root / manifest["volumes"]["candidate"]["path"]
        p.write_text("# Incomplete\n\nA flattering excerpt.\n")
        with self.assertRaisesRegex(WorkflowError, "evidence is missing or changed"):
            groups.verify(self.workflow.journal, path, "revision-1-creative-group-1-3-check")


class FullCreativeGroupDeliveryTests(unittest.TestCase):
    def test_whole_workflow_exports_group_then_completed_resume_detects_changed_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze(root / ".book-genesis/project.json", encoded({"host": "codex", "collaboration": "autonomous",
                "author_name": "QA", "model": "exact-test-model", "effort": "high", "idea": "Return the letter.", "language": "English",
                "autonomous_contract": {"chapters": 2, "min_words": 240, "max_words": 600, "quality_target": 8.5}}))
            freeze(root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
            calls = []
            def generate(call_id, packet, schema, book):
                calls.append(call_id)
                props = schema["properties"]
                if "catalog_sha256" in props and "chapters" in props:
                    return group_report(packet, schema)
                if "compare" in props:
                    return comparison_report(call_id, packet, schema, book)
                result = fixture_response(call_id, packet, schema, book)
                if "strategy" in props:
                    result["tasks"] = [{**result["tasks"][0], "chapter": n} for n in (1, 2)]
                if "prose" in props and "revision-" in call_id:
                    context = json.loads(packet.rsplit("\n\n", 1)[1])
                    result["prose"] = context["accepted_chapter"].replace("held the stolen letter", "chose to confess")
                if "checks" in props:
                    for finding in result.get("findings", []):
                        finding["chapters"] = [1, 2]
                        if "chapter_checks" in result:
                            for row in result["chapter_checks"]:
                                row["checks"][0]["result"] = "finding"
                                finding["evidence_ids"] = list(dict.fromkeys(
                                    finding["evidence_ids"] + row["checks"][0]["evidence_ids"]))
                if "statuses" in props:
                    catalog = json.loads(packet.split("Current complete sources:\n", 1)[1])
                    ids = [s["passages"][1]["id"] for s in catalog["sources"] if s["source"].startswith("chapter-")]
                    for row in result["statuses"]:
                        row["evidence_ids"] = ids
                return result
            options = dict(chapters=2, min_words=240, max_words=600, transport=receipt_transport(generate))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, BookWorkflow(root, COMMAND, **options).run())
            self.assertEqual("verified", verify_execution(root, required_phase=8)["status"])
            self.assertTrue(list((root / "delivery").glob("*.epub")))
            self.assertTrue(list((root / "delivery").glob("*.md")))
            self.assertEqual(1, len(list((root / "evaluations/promotions").glob("*creative-group*.json"))))
            count = len(calls)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, BookWorkflow(root, COMMAND, **options).run())
            self.assertEqual(count, len(calls))
            path = root / "work/creative-groups/revision-1-creative-group-1-2/manifest.json"
            source = root / read_json(path)["sources"]["original/chapter-01.md"]["path"]
            source.write_bytes(source.read_bytes() + b"Changed original evidence.")
            with redirect_stdout(io.StringIO()), self.assertRaisesRegex(WorkflowError, "evidence is missing or changed"):
                BookWorkflow(root, COMMAND, **options).run()
            self.assertEqual(count, len(calls))


if __name__ == "__main__":
    unittest.main()
