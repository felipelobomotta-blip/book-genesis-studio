"""Coordinated continuity corrections keep original evidence and crash safety."""
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
import correction_groups as groups
from autonomous_book import BookWorkflow
from workflow_state import Journal, WorkflowError, encoded, freeze, read_json, verify_execution
from test_autonomous_workflow import COMMAND, receipt_transport, fixture_response


class CorrectionGroupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        freeze(self.root / ".book-genesis/project.json", encoded({
            "host": "codex", "collaboration": "autonomous", "author_name": "QA",
            "model": "exact-test-model", "effort": "high", "idea": "The repair.", "language": "English"}))
        freeze(self.root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
        self.packets, self.block, self.malformed = {}, False, False
        self.workflow = self.new_workflow()
        self.originals = {}
        for n in range(1, 5):
            sentence = "The receipt specifies a galvanised mesh gate." if n in (1, 3) else "She handled the plastic gate."
            raw = (f"# Gate {n}\n\n{sentence}\n\n" + "She carried the letter down the lane. " * 20 + "\n").encode()
            path = self.root / "fixture" / f"chapter-{n:02d}.md"
            freeze(path, raw)
            self.workflow.journal.publish(path, self.root / "manuscript/chapters" / path.name)
            self.originals[path.name] = raw
        for name in ("00-brief.md", "03-characters.md", "05-voice.md", "07-outline.md", "09-continuity-ledger.md"):
            freeze(self.root / "artifacts" / name, b"# Notes\n\nThe gate is galvanised mesh.\n")
        self.tasks = [{"chapter": n, "mode": "factual", "ticket": "Correct the gate material from the receipt.",
                       "preserve": "Actions and voice.", "revision_class": "continuity", "issue_ids": ["material"]} for n in (2, 4)]

    def new_workflow(self):
        return BookWorkflow(self.root, COMMAND, chapters=4, min_words=400, max_words=1800,
                            transport=receipt_transport(self.generate))

    def generate(self, call_id, packet, schema, root):
        self.packets[call_id] = packet
        if "corrections" in schema["properties"]:
            context = json.loads(packet.rsplit("\n\n", 1)[1])
            self.assertEqual(len(self.tasks) - 1, len(context["companion_tasks"]))
            p = next((p for p in context["accepted_chapter"] if "plastic gate" in p["text"]), None)
            if p is None:
                return {"corrections": []}
            return {"corrections": [{"from_passage": p["id"], "through_passage": p["id"],
                                     "after": p["text"].replace("plastic", "galvanised mesh")}]}
        if self.malformed:
            return {"verdict": "pass"}
        catalog = json.JSONDecoder().raw_decode(packet.split("\nSources:\n", 1)[1])[0]
        by_name = {s["source"]: s for s in catalog["sources"]}
        for n in [task["chapter"] for task in self.tasks]:
            self.assertIn(f"original/chapter-{n:02d}.md", by_name)
            self.assertNotIn("plastic gate", str(by_name[f"proposed/chapter-{n:02d}.md"]))
        return {"catalog_sha256": schema["properties"]["catalog_sha256"]["enum"][0],
                "verdict": "block" if self.block else "pass", "coverage": list(by_name),
                "chapters": [{"chapter": n, "canon_supported": not self.block, "factual_only": True,
                    "dependencies_safe": True, "reason": "Receipt supports this material in both corrected references.",
                    "evidence_ids": [by_name[name]["passages"][1]["id"] for name in
                        (f"original/chapter-{n:02d}.md", f"proposed/chapter-{n:02d}.md", "contract/09-continuity-ledger.md")]} for n in [t["chapter"] for t in self.tasks]],
                "findings": ["Unsupported material."] if self.block else [], "limitations": "Synthetic transport exercises code, not literary quality."}

    def run_group(self):
        with redirect_stdout(io.StringIO()):
            return self.workflow.revise_factual_group(1, self.tasks, "Correct both references together.")

    def assert_original(self):
        for name, raw in self.originals.items():
            self.assertEqual(raw, (self.root / "manuscript/chapters" / name).read_bytes())

    def test_shared_issues_connect_transitively_without_grouping_unrelated_tasks(self):
        tasks = [{"chapter": i, "mode": "factual", "issue_ids": ids} for i, ids in
                 [(1, ["a"]), (2, ["b"]), (3, ["a", "b"]), (4, []), (5, ["c"])]]
        self.assertEqual([[1, 2, 3], [4], [5]], [[t["chapter"] for t in g] for g in groups.connected_tasks(tasks)])

    def test_complete_group_promotes_both_without_losing_originals_or_calling_again(self):
        result = self.run_group()
        self.assertEqual(["promote", "promote"], [r["decision"] for r in result])
        for n in (2, 4):
            self.assertIn("galvanised mesh gate", (self.root / f"manuscript/chapters/chapter-{n:02d}.md").read_text())
        manifest = self.root / "work/correction-groups/revision-1-facts-group-2-4/manifest.json"
        groups.verify(self.workflow.journal, manifest, "revision-1-facts-group-2-4-check")
        for name, row in read_json(manifest)["sources"].items():
            if name.startswith("original/"):
                self.assertEqual(self.originals[Path(name).name], (self.root / row["path"]).read_bytes())
        count = len(self.packets)
        self.workflow = self.new_workflow()
        self.assertEqual(result, self.run_group())
        self.assertEqual(count, len(self.packets))

    def test_already_correct_member_is_reviewed_but_never_rewritten_or_counted_as_promoted(self):
        self.tasks.insert(0, {**self.tasks[0], "chapter": 1})
        with patch.object(groups, "replace_verified", wraps=groups.replace_verified) as replace:
            result = self.run_group()
        self.assertEqual(["unchanged", "promote", "promote"], [r["decision"] for r in result])
        self.assertEqual(2, replace.call_count)
        self.assertEqual(self.originals["chapter-01.md"], (self.root / "manuscript/chapters/chapter-01.md").read_bytes())
        self.assertEqual([2, 4], self.workflow.journal.data["revision_chapters"])
        manifest_path = self.root / "work/correction-groups/revision-1-facts-group-1-2-4/manifest.json"
        manifest = groups.verify(self.workflow.journal, manifest_path, "revision-1-facts-group-1-2-4-check")
        self.assertEqual([1], [r["chapter"] for r in manifest["unchanged_members"]])
        self.assertEqual([2, 4], [r["chapter"] for r in manifest["publications"]])
        calls = len(self.packets)
        self.workflow = self.new_workflow()
        self.assertEqual(result, self.run_group())
        self.assertEqual(calls, len(self.packets))

    def test_all_unchanged_group_requires_review_and_creates_no_fake_promotion(self):
        self.tasks = [{**self.tasks[0], "chapter": n} for n in (1, 3)]
        with patch.object(groups, "replace_verified", wraps=groups.replace_verified) as replace:
            result = self.run_group()
        self.assertEqual(["unchanged", "unchanged"], [r["decision"] for r in result])
        self.assertEqual(0, replace.call_count)
        self.assertEqual(3, len(self.packets))
        self.assert_original()
        self.assertFalse(list((self.root / "evaluations/promotions").glob("*.json")))
        manifest = self.root / "work/correction-groups/revision-1-facts-group-1-3/manifest.json"
        with self.assertRaisesRegex(WorkflowError, "cannot be published"):
            groups.publish(self.workflow.journal, manifest, "revision-1-facts-group-1-3-check", self.root / "fake-receipt.json")
        self.workflow = self.new_workflow()
        self.assertEqual(result, self.run_group())
        self.assertEqual(3, len(self.packets))

    def test_false_unchanged_claim_is_not_an_automatic_approval(self):
        original = self.generate
        def incomplete(call_id, packet, schema, root):
            self.packets[call_id] = packet
            if "corrections" in schema["properties"] and "c04-facts" in call_id:
                return {"corrections": []}
            if "chapters" in schema["properties"]:
                catalog = json.loads(packet.split("\nSources:\n", 1)[1])
                by_name = {s["source"]: s for s in catalog["sources"]}
                self.assertIn("plastic gate", str(by_name["proposed/chapter-04.md"]))
                return {"catalog_sha256": schema["properties"]["catalog_sha256"]["enum"][0],
                    "verdict": "block", "coverage": list(by_name),
                    "chapters": [{"chapter": n, "canon_supported": n != 4, "factual_only": True,
                        "dependencies_safe": n != 4, "reason": "Chapter 4 still contradicts the original material receipt.",
                        "evidence_ids": [by_name[name]["passages"][1]["id"] for name in
                            (f"original/chapter-{n:02d}.md", f"proposed/chapter-{n:02d}.md", "contract/09-continuity-ledger.md")]} for n in (2, 4)],
                    "findings": ["The unchanged chapter 4 still needs its assigned correction."], "limitations": "Synthetic gate check."}
            return original(call_id, packet, schema, root)
        self.workflow.transport = receipt_transport(incomplete)
        self.assertTrue(all(r["decision"] == "reject" for r in self.run_group()))
        self.assert_original()
        self.assertEqual(3, len(self.packets))

    def test_retained_member_tampering_is_detected_before_crash_recovery(self):
        self.tasks.insert(0, {**self.tasks[0], "chapter": 1})
        self.interrupt_between_members()
        target = self.root / "manuscript/chapters/chapter-01.md"
        target.write_bytes(b"Author changed the retained chapter.")
        with self.assertRaisesRegex(WorkflowError, "collided with another manuscript edit"):
            self.new_workflow()
        self.assertEqual(b"Author changed the retained chapter.", target.read_bytes())

    def test_one_negative_group_review_rejects_every_member_without_repolling(self):
        self.block = True
        result = self.run_group()
        self.assertTrue(all(r["decision"] == "reject" for r in result))
        self.assert_original()
        self.assertEqual(3, len(self.packets))
        self.assertEqual(result, self.run_group())
        self.assertEqual(3, len(self.packets))

    def test_two_malformed_reviews_reject_group_and_preserve_bounded_budget(self):
        self.malformed = True
        self.assertTrue(all(r["decision"] == "reject" for r in self.run_group()))
        self.assert_original()
        self.assertEqual(4, len(self.packets))
        self.run_group()
        self.assertEqual(4, len(self.packets))

    def interrupt_between_members(self):
        real = groups.replace_verified
        count = 0
        def interrupted(*args):
            nonlocal count
            count += 1
            if count == 2:
                raise KeyboardInterrupt()
            return real(*args)
        with patch.object(groups, "replace_verified", side_effect=interrupted), self.assertRaises(KeyboardInterrupt):
            self.run_group()
        self.assertEqual("factual_correction_group", read_json(self.workflow.journal.path)["pending_mutation"]["kind"])

    def test_crash_between_members_recovers_whole_group_with_no_model_replay(self):
        self.interrupt_between_members()
        calls = len(self.packets)
        self.workflow = self.new_workflow()
        result = self.run_group()
        self.assertEqual(calls, len(self.packets))
        self.assertTrue(all(r["decision"] == "promote" for r in result))
        self.assertIsNone(self.workflow.journal.data["pending_mutation"])
        self.workflow.journal.check_canonical()

    def test_concurrent_edit_blocks_group_recovery_without_overwriting_user_text(self):
        self.interrupt_between_members()
        target = self.root / "manuscript/chapters/chapter-04.md"
        target.write_bytes(b"Author's concurrent replacement.")
        with self.assertRaisesRegex(WorkflowError, "collided with a target edit"):
            self.new_workflow()
        self.assertEqual(b"Author's concurrent replacement.", target.read_bytes())

    def test_tampered_review_blocks_group_recovery_before_another_write(self):
        self.interrupt_between_members()
        response = self.root / "work/host-calls/wf-revision-1-facts-group-2-4-check-1/response"
        response.write_bytes(response.read_bytes() + b" ")
        with self.assertRaisesRegex(WorkflowError, "evidence is missing or changed"):
            self.new_workflow()
        self.assertEqual(self.originals["chapter-04.md"], (self.root / "manuscript/chapters/chapter-04.md").read_bytes())

    def test_process_death_after_claiming_original_inode_recovers_without_author_input(self):
        def die_after_claim(target, candidate, before, transaction_id):
            holder = groups.transaction_path(target, transaction_id, "holder")
            target.rename(holder)
            raise KeyboardInterrupt()
        with patch.object(groups, "replace_verified", side_effect=die_after_claim), self.assertRaises(KeyboardInterrupt):
            self.run_group()
        self.assertFalse((self.root / "manuscript/chapters/chapter-02.md").exists())
        calls = len(self.packets)
        self.workflow = self.new_workflow()
        self.assertTrue(all(r["decision"] == "promote" for r in self.run_group()))
        self.assertEqual(calls, len(self.packets))
        self.assertFalse(list((self.root / "manuscript/chapters").glob("*.group-holder-*")))

    def test_reviewer_cannot_use_only_companion_proposal_to_establish_canon(self):
        original = self.generate
        def unsupported(call_id, packet, schema, root):
            result = original(call_id, packet, schema, root)
            if "chapters" in result:
                result["chapters"][0]["evidence_ids"] = result["chapters"][0]["evidence_ids"][:2] * 2
            return result
        self.workflow.transport = receipt_transport(unsupported)
        self.assertTrue(all(r["decision"] == "reject" for r in self.run_group()))
        self.assert_original()

    def test_missing_canon_feedback_names_the_member_and_preserves_original_invalid_report(self):
        original = self.generate
        attempts = []
        def omit_canon(call_id, packet, schema, root):
            report = original(call_id, packet, schema, root)
            if "chapters" not in schema["properties"]:
                return report
            attempts.append(call_id)
            if len(attempts) == 1:
                member = next(r for r in report["chapters"] if r["chapter"] == 4)
                member["evidence_ids"] = member["evidence_ids"][:2] + member["evidence_ids"][:1]
            else:
                self.assertIn("Chapter 4: missing independent existing-canon evidence", packet)
                self.assertIn("another original/ chapter or a contract/ source", packet)
                self.assertNotIn("Chapter 2: missing independent", packet)
            return report
        self.workflow.transport = receipt_transport(omit_canon)
        self.assertTrue(all(r["decision"] == "promote" for r in self.run_group()))
        self.assertEqual(2, len(attempts))
        self.assertEqual(4, len(self.packets))
        step = self.workflow.journal.data["steps"]["revision-1-facts-group-2-4-check"]
        self.assertTrue(step["attempts"][-1].get("feedback_evidence"))
        self.assertFalse(read_json(self.root / "work/workflow/revision-1-facts-group-2-4-check/validation-1.json")["valid"])
        self.workflow = self.new_workflow()
        self.run_group()
        self.assertEqual(4, len(self.packets))
        response = self.root / "work/host-calls" / attempts[0] / "response"
        response.write_bytes(response.read_bytes() + b" ")
        with self.assertRaisesRegex(WorkflowError, "evidence is missing or changed"):
            self.run_group()


class FullGroupDeliveryTests(unittest.TestCase):
    def test_group_reaches_both_exports_and_completed_resume_rechecks_its_sources(self):
        self.run_group_delivery(retain_second=False)

    def test_mixed_retention_and_correction_reaches_export_and_unchanged_completed_resume(self):
        self.run_group_delivery(retain_second=True)

    def run_group_delivery(self, *, retain_second):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze(root / ".book-genesis/project.json", encoded({"host": "codex", "collaboration": "autonomous",
                "author_name": "QA", "model": "exact-test-model", "effort": "high", "idea": "Ada returns a letter.",
                "language": "English", "autonomous_contract": {"chapters": 2, "min_words": 240, "max_words": 600, "quality_target": 8.5}}))
            freeze(root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
            calls = []
            def generate(call_id, packet, schema, book):
                calls.append(call_id)
                props = schema["properties"]
                if "corrections" in props:
                    context = json.loads(packet.rsplit("\n\n", 1)[1])
                    p = next((p for p in context["accepted_chapter"] if "Ida Vale" in p["text"]), None)
                    if p is None:
                        return {"corrections": []}
                    return {"corrections": [{"from_passage": p["id"], "through_passage": p["id"],
                                             "after": p["text"].replace("Ida Vale", "Ada Vale")}]}
                if "catalog_sha256" in props and "chapters" in props:
                    catalog = json.loads(packet.split("\nSources:\n", 1)[1])
                    sources = {s["source"]: s for s in catalog["sources"]}
                    return {"catalog_sha256": props["catalog_sha256"]["enum"][0], "verdict": "pass", "coverage": list(sources),
                        "chapters": [{"chapter": n, "canon_supported": True, "factual_only": True, "dependencies_safe": True,
                            "reason": "The synthetic name correction matches the saved contract.",
                            "evidence_ids": [sources[name]["passages"][-1]["id"] for name in
                                (f"original/chapter-{n:02d}.md", f"proposed/chapter-{n:02d}.md", "contract/03-characters.md")]} for n in (1, 2)],
                        "findings": [], "limitations": "Synthetic flow check, not model or literary validation."}
                result = fixture_response(call_id, packet, schema, book)
                if "prose" in props and "draft-" in call_id:
                    name = "Ada Vale" if retain_second and "draft-02" in call_id else "Ida Vale"
                    result["prose"] = result["prose"].replace("The courier", name, 1)
                if "strategy" in props:
                    task = result["tasks"][0]
                    task.update(mode="factual", ticket="Correct Ida Vale to established Ada Vale.", revision_class="continuity")
                    result["tasks"] = [{**task, "chapter": n} for n in (1, 2)]
                if "checks" in props:
                    for finding in result["findings"]:
                        finding.update(kind="continuity", chapters=[1, 2], problem="The courier's name is misspelled.", fix="Use Ada Vale.")
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
                workflow = BookWorkflow(root, COMMAND, **options)
                self.assertEqual(0, workflow.run())
            self.assertEqual("verified", verify_execution(root, required_phase=8)["status"])
            self.assertTrue(list((root / "delivery").glob("*.epub")))
            self.assertTrue(list((root / "delivery").glob("*.md")))
            for n in (1, 2):
                self.assertIn("Ada Vale", (root / f"manuscript/chapters/chapter-{n:02d}.md").read_text())
            receipt = read_json(next((root / "evaluations/promotions").glob("*.json")))
            self.assertEqual([1] if retain_second else [1, 2], [r["chapter"] for r in receipt["publications"]])
            before = len(calls)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, BookWorkflow(root, COMMAND, **options).run())
            self.assertEqual(before, len(calls))
            manifest_path = next((root / "work/correction-groups").glob("*/manifest.json"))
            source_name = "original/chapter-02.md" if retain_second else "original/chapter-01.md"
            source = root / read_json(manifest_path)["sources"][source_name]["path"]
            source.write_bytes(source.read_bytes() + b"Tampered original.")
            with self.assertRaisesRegex(WorkflowError, "evidence is missing or changed"):
                verify_execution(root, required_phase=8)


if __name__ == "__main__":
    unittest.main()
