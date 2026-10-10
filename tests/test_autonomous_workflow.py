"""Crash, evidence, bounded-revision and actual export tests; no paid model calls."""
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
from autonomous_book import BookWorkflow
from workflow_state import Journal, WorkflowError, atomic, digest, encoded, freeze, read_json, verify_execution
from workflow_roles import obj, TEXT, validate_json
from verify_book import verify_book


COMMAND = {"argv": ["fixture", "exec", "-o", "{output}", "-"], "timeout_seconds": 30}


def receipt_transport(response_factory, after=None):
    def transport(root, call_id, packet, command_json):
        folder = root / "work/host-calls" / call_id
        folder.mkdir(parents=True, exist_ok=True)
        record = folder / "receipt.json"
        if record.exists():
            return {**read_json(record), "idempotent": True}
        command = json.loads(command_json)
        schema = read_json(Path(command["argv"][command["argv"].index("--output-schema") + 1]))
        data = response_factory(call_id, packet.read_text(encoding="utf-8"), schema, root)
        for name, content in {"packet": packet.read_bytes(), "response": encoded(data), "stdout": b"fixture output\n",
                              "stderr": b"model: exact-test-model\nreasoning effort: high\n"}.items():
            (folder / name).write_bytes(content)
        result = {"schema_version": 1, "call_id": call_id, "status": "completed", "exit_code": 0,
                  **{name + "_sha256": digest((folder / name).read_bytes()) for name in ("packet", "response", "stdout", "stderr")}}
        record.write_bytes(encoded(result))
        if after:
            after()
        return result
    return transport


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.j = Journal(self.root, {"model": "exact-test-model", "effort": "high"})

    def test_response_survives_crash_without_another_native_generation(self):
        calls = []
        def generate(*args):
            calls.append(1)
            return {"text": "saved"}
        def crash():
            raise KeyboardInterrupt()
        schema = obj({"text": TEXT})
        with redirect_stdout(io.StringIO()), self.assertRaises(KeyboardInterrupt):
            self.j.call("draft", b"packet", schema, COMMAND, lambda p: validate_json(p, schema), transport=receipt_transport(generate, crash))
        self.assertEqual("reserved", read_json(self.j.path)["steps"]["draft"]["attempts"][0]["status"])
        recovered = Journal(self.root, self.j.data["contract"])
        with redirect_stdout(io.StringIO()):
            recovered.call("draft", b"packet", schema, COMMAND, lambda p: validate_json(p, schema), transport=receipt_transport(generate))
        self.assertEqual(1, len(calls))
        self.assertEqual(1, len(recovered.data["steps"]["draft"]["attempts"]))

    def test_retry_budget_is_not_reset_by_resume(self):
        schema = obj({"text": TEXT})
        transport = receipt_transport(lambda *args: {"wrong": "shape"})
        with redirect_stdout(io.StringIO()), self.assertRaisesRegex(WorkflowError, "exhausted 2"):
            self.j.call("draft", b"packet", schema, COMMAND, lambda p: validate_json(p, schema), transport=transport)
        resumed = Journal(self.root, self.j.data["contract"])
        with self.assertRaisesRegex(WorkflowError, "exhausted 2"):
            resumed.call("draft", b"packet", schema, COMMAND, lambda p: validate_json(p, schema), transport=transport)
        self.assertEqual(2, len(resumed.data["steps"]["draft"]["attempts"]))

    def test_stale_vote_cannot_be_rebound_to_new_packet(self):
        schema = obj({"text": TEXT})
        with redirect_stdout(io.StringIO()):
            self.j.call("reader", b"old prose", schema, COMMAND, lambda p: validate_json(p, schema), transport=receipt_transport(lambda *args: {"text": "vote"}))
        with self.assertRaisesRegex(WorkflowError, "inputs changed"):
            self.j.call("reader", b"new prose", schema, COMMAND, lambda p: validate_json(p, schema))

    def test_changed_native_response_cannot_be_reused(self):
        schema = obj({"text": TEXT})
        with redirect_stdout(io.StringIO()):
            path, _ = self.j.call("reader", b"prose", schema, COMMAND, lambda p: validate_json(p, schema), transport=receipt_transport(lambda *args: {"text": "vote"}))
        path.write_bytes(b'{"text":"tampered"}')
        with self.assertRaisesRegex(WorkflowError, "evidence is missing or changed"):
            self.j.call("reader", b"prose", schema, COMMAND, lambda p: validate_json(p, schema))

    def test_publication_recovers_after_atomic_write_before_state_commit(self):
        source = self.root / "work/chapter.md"
        freeze(source, b"# One\n\nA story.\n")
        target = self.root / "manuscript/chapters/chapter-01.md"
        with patch.object(self.j, "recover_mutation", side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            self.j.publish(source, target)
        resumed = Journal(self.root, self.j.data["contract"])
        self.assertEqual(digest(source.read_bytes()), resumed.data["canonical"]["manuscript/chapters/chapter-01.md"])
        self.assertIsNone(resumed.data["pending_mutation"])

    def test_external_canonical_edits_are_preserved_and_block_resume(self):
        source = self.root / "work/chapter.md"
        freeze(source, b"# One\n\nA story.\n")
        target = self.root / "manuscript/chapters/chapter-01.md"
        self.j.publish(source, target)
        target.write_bytes(b"my changes")
        with self.assertRaisesRegex(WorkflowError, "outside a recorded publication"):
            Journal(self.root, self.j.data["contract"])
        self.assertEqual(b"my changes", target.read_bytes())

    def test_passes_reserved_before_dispatch_and_never_refunded(self):
        self.j.data["phase"] = 5
        self.j.save()
        self.j.reserve_pass(1, panel_failed=True, rubric_failed=False)
        resumed = Journal(self.root, self.j.data["contract"])
        resumed.reserve_pass(1, panel_failed=False, rubric_failed=False)
        self.assertTrue(resumed.data["passes"][0]["panel_failed"])
        resumed.reserve_pass(2, panel_failed=True, rubric_failed=True)
        resumed.reserve_pass(3, panel_failed=True, rubric_failed=True)
        with self.assertRaisesRegex(WorkflowError, "three-pass"):
            resumed.reserve_pass(4, panel_failed=True, rubric_failed=True)

    def test_phase_cannot_skip_required_evidence(self):
        with self.assertRaisesRegex(WorkflowError, "skip a phase"):
            self.j.finish_phase(2, [])

    def test_controlled_export_cannot_downgrade_by_deleting_journal(self):
        freeze(self.root / ".book-genesis/project.json", encoded({"autonomous_contract": {"chapters": 2}}))
        self.j.path.unlink()
        with self.assertRaisesRegex(WorkflowError, "durable workflow journal"):
            verify_execution(self.root)


def fixture_response(call_id, packet, schema, root):
    props = schema["properties"]
    if "files" in props:
        value = {"files": {name: f"# {name}\n\nA courier must return a stolen letter and confess. The two chapter story ends with the recipient choosing to forgive her."
                            for name in props["files"]["properties"]}}
        if "book" in props:
            value["book"] = {"title": "The Test Letter", "genre": "Literary short fiction", "audience": "adult fiction readers"}
        if "chapters" in props:
            value["chapters"] = [{"number": n, "title": f"Chapter {n}", **{key: "A consequential choice with a complete ending."
                for key in props["chapters"]["items"]["properties"] if key not in ("number", "title")}} for n in (1, 2)]
        return value
    if "prose" in props:
        revision = "revision-" in call_id
        number = 2 if "draft-02" in call_id else 1
        return {"prose": f"# Chapter {number}\n\n" + ("The courier chose to confess. " if revision else "The courier held the stolen letter. ") * 16
                + "\n\n" + "The recipient listened and opened the door. " * 14,
                "continuity_delta": "The courier arrived; the recipient opened the door."}
    if "coverage" in props and "checks" in props:
        catalog = json.loads(packet.split("Complete sources:\n", 1)[1])
        names = [s["source"] for s in catalog["sources"]]
        passes = props["checks"]["items"]["properties"]["name"]["enum"]
        defective = "measure-0-audit" in call_id or "audit-original" in call_id
        findings = [{"severity": "high", "kind": "character", "chapters": [1],
            "evidence_ids": [catalog["sources"][-1]["passages"][0]["id"]], "problem": "The courier has not confessed.",
            "fix": "Let the courier confess before the door opens.", "preserve": "The letter and the opened door."}] if defective else []
        return {"verdict": "revise" if defective else "pass", "coverage": names,
                "checks": [{"name": name, "result": "finding" if defective else "pass", "reason": "Checked the assigned sources."} for name in passes],
                "findings": findings, "ending_resolved": True, "limitations": "Synthetic response for deterministic integration tests only."}
    if "dimensions" in props:
        catalog = json.loads(packet.split("Complete frozen manuscript:\n", 1)[1].split("\ncatalog_sha256:")[0])
        ids = [p["id"] for c in catalog["chapters"] for p in c["passages"]]
        evidence = [{"passage_id": p, "reason": "A supported observation."} for p in ids[:2]]
        return {"schema_version": 2, "catalog_sha256": props["catalog_sha256"]["enum"][0],
            "coverage": {"scope": "full_manuscript", "chapters": [1, 2]},
            "dimensions": [{"name": name, "score": 8.8 if "measure-0" in call_id else 9.4, "evidence": evidence, "reason": "A demonstrated craft choice."}
                for name in props["dimensions"]["items"]["properties"]["name"]["enum"]],
            "strongest_passage": evidence[0], "weakest_passage": evidence[1],
            "confidence": {"level": "medium", "reason": "Test fixture."}, "limitations": "Synthetic test only, not literary evidence."}
    if "strategy" in props:
        return {"strategy": "Repair the missing confession.", "deferred": [], "tasks": [{"chapter": 1,
            "ticket": "Confess before the opened door.", "preserve": "Letter and door.", "revision_class": "character"}]}
    if "editorial_package" in props:
        return {"editorial_package": "# Package\n\nA full synthetic editorial package for the letter story.",
                "positioning": "# Positioning\n\nUnverified positioning hypothesis.",
                "options": [{"id": n, "title": f"The Letter {n}", "logline": "A stolen letter returns.", "blurb": "A courier has a choice."} for n in (1, 2, 3)]}
    if "options" in props:
        reader = packet.split("You are ")[1].split(",", 1)[0]
        return {"reader": reader, "options": [{"id": n, "click": True, "buy": n == 1, "keep_reading": True, "reason": "Specific premise."} for n in (1, 2, 3)]}
    if "turn_page" in props:
        reader = props["reader"]["enum"][0]
        comparison = "compare" in props
        ids = (schema["$defs"]["passageId"]["enum"] if comparison else props["strongest_passage"]["properties"]["passage_id"]["enum"])
        ev = {"passage_id": ids[0], "reason": "The choice holds attention."}
        result = {"schema_version": 3 if comparison else 2, "catalog_sha256": props["catalog_sha256"]["enum"][0],
            "reader": reader, "turn_page": "yes", "stopped_at": None, "why_stopped": None,
            "remember_tomorrow": [ev], "confused_by": [], "flags": [], "strongest_passage": ev,
            "weakest_passage": ev, "machine_tells": [], "felt": {"emotion": "curiosity", "reason": "The choice matters."}, "confidence": "medium"}
        if comparison:
            # Test fixture knows the private mapping to exercise a promotion;
            # real readers receive only their anonymous packet and schema.
            manifest = read_json(root / "work/comparisons/revision-1-c01/manifest.private.json")
            assignment = next(row for row in manifest["readers"] if row["reader"] == reader)
            result["compare"] = next(label for label, identity in assignment["mapping"].items() if identity == "candidate")
        return result
    raise AssertionError(call_id)


class FullWorkflowTests(unittest.TestCase):
    def test_idea_revised_book_export_resume_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze(root / ".book-genesis/project.json", encoded({"host": "codex", "collaboration": "autonomous",
                "author_name": "QA", "model": "exact-test-model", "effort": "high", "idea": "A stolen letter returned.", "language": "English",
                "autonomous_contract": {"chapters": 2, "min_words": 240, "max_words": 600, "quality_target": 8.5}}))
            freeze(root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
            kwargs = dict(chapters=2, min_words=240, max_words=600, transport=receipt_transport(fixture_response))
            with redirect_stdout(io.StringIO()):
                workflow = BookWorkflow(root, COMMAND, **kwargs)
                original_publish = workflow.journal.publish
                def interrupt_after_promotion(source, target, **options):
                    original_publish(source, target, **options)
                    if options.get("promote"):
                        raise KeyboardInterrupt()
                with patch.object(workflow.journal, "publish", side_effect=interrupt_after_promotion), self.assertRaises(KeyboardInterrupt):
                    workflow.run()
                self.assertEqual("blocked", read_json(workflow.journal.path)["status"])
                workflow = BookWorkflow(root, COMMAND, **kwargs)
                self.assertEqual(0, workflow.run())
            state = read_json(root / "PROJECT_STATE.yaml")
            self.assertEqual(1, state["pipeline"]["panel_passes"])
            self.assertEqual(1, state["pipeline"]["rubric_passes"])
            self.assertEqual(8, workflow.journal.data["phase"])
            self.assertEqual("completed", workflow.journal.data["status"])
            result = verify_book(root, "evaluations/final-reader-index.json")
            self.assertEqual("delivered", result["delivery"]["status"])
            self.assertEqual("current", result["reviews"]["status"])
            calls = len(list((root / "work/host-calls").iterdir()))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, BookWorkflow(root, COMMAND, **kwargs).run())
            self.assertEqual(calls, len(list((root / "work/host-calls").iterdir())))
            epub = next((root / "delivery").glob("*.epub"))
            epub.write_bytes(b"damaged export")
            with redirect_stdout(io.StringIO()), self.assertRaisesRegex(WorkflowError, "delivery is missing or stale"):
                BookWorkflow(root, COMMAND, **kwargs).run()


if __name__ == "__main__":
    unittest.main()
