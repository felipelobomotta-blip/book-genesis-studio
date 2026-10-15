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
from catalog_wire import parse_catalog
from autonomous_book import BookWorkflow
from workflow_state import WorkflowError, encoded, freeze, read_json, verify_execution
from test_autonomous_workflow import COMMAND, receipt_transport, fixture_response


def group_report(packet, schema, blocked=False):
    catalog = parse_catalog(packet.split("\nCatalog wire:\n", 1)[1].split("\n\nDeterministic output validation rejected", 1)[0])
    sources = {s["source"]: s for s in catalog["sources"]}
    scoped = "report_schema_version" in schema["properties"]
    members = ([int(key[len("chapter-"):]) for key in schema["properties"]["chapters"]["properties"]]
        if scoped else schema["properties"]["chapters"]["items"]["properties"]["chapter"]["enum"])
    report = {"catalog_sha256": schema["properties"]["catalog_sha256"]["enum"][0],
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
    if scoped:
        # Test producer emits the explicitly versioned contract; production
        # validation never supplies a missing citation or rewrites a verdict.
        locations = {p["id"]: s["source"] for s in catalog["sources"] for p in s["passages"]}
        chapters = {}
        for member in report["chapters"]:
            number = member["chapter"]
            own = {"original_evidence_ids": f"original/chapter-{number:02d}.md",
                   "proposed_evidence_ids": f"proposed/chapter-{number:02d}.md"}
            checks = {}
            for check in member["checks"]:
                checks[check["name"]] = {"result": check["result"], "reason": check["reason"],
                    **{field: [pid for pid in check["evidence_ids"] if locations[pid] == source]
                       for field, source in own.items()},
                    "supporting_evidence_ids": [pid for pid in check["evidence_ids"]
                        if locations[pid] not in own.values()]}
            chapters[f"chapter-{number:02d}"] = {"checks": checks}
        report.update(report_schema_version=2, chapters=chapters,
                      coverage={name: "read" for name in report["coverage"]})
    return report


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
        self.invalid = set()
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
            context, _ = json.JSONDecoder().raw_decode('{"task":' + packet.split('\n\n{"task":', 1)[1])
            self.assertEqual(len(self.tasks) - 1, len(context["companion_tasks"]))
            if context["task"]["chapter"] == 3 and 1 not in self.invalid:
                self.assertIn("closed", context["unaccepted_companion_proposals"]["chapter-01.md"])
                self.assertIn("open", context["other_current_chapters"]["chapter-01.md"])
            prose = context["accepted_chapter"]
            if context["task"]["chapter"] in self.invalid:
                return {"prose": "# Too short\n\nNo scene.", "continuity_delta": "No usable proposal."}
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

    def legacy_receipt_fixture(self, version):
        # All calls in this helper are synthetic unit-test receipts. Reuse the
        # same source-bound volumes and anonymous votes, then supply the exact
        # old correctness contract; no real historical book is relabelled.
        if version == 2:
            self.invalid = {3}
        self.run_group()
        key = "revision-1-creative-group-1-3"
        manifest = read_json(self.root / "work/creative-groups" / key / "manifest.json")
        manifest["schema_version"] = version
        legacy = self.root / f"fixture/legacy-v{version}/manifest.json"
        freeze(legacy, encoded(manifest))
        catalog = groups.catalog_for(self.workflow.journal, manifest)
        members = [row["chapter"] for row in manifest["publications"]]
        schema = groups.schema_for(catalog, members, report_version=1)
        call_key = f"legacy-v{version}-check"
        with redirect_stdout(io.StringIO()):
            self.workflow.call(call_key, groups.packet_for(manifest, catalog), schema,
                lambda path: groups.validate_report(path, schema, catalog, members))
        receipt = read_json(self.root / "evaluations/promotions" / (key + ".json"))
        receipt.update(manifest=self.workflow.journal.record_file(legacy), review_key=call_key)
        path = legacy.parent / "promotion.json"
        freeze(path, encoded(receipt))
        count = len(self.calls)
        original_receipt = path.read_bytes()
        self.assertEqual(manifest, transactions.verify_receipt(self.workflow.journal, legacy, call_key, path))
        self.assertEqual(manifest, transactions.verify_receipt(self.workflow.journal, legacy, call_key, path))
        self.assertEqual(count, len(self.calls))
        self.assertEqual(original_receipt, path.read_bytes())

    def test_legacy_v1_review_and_promotion_receipt_replay_without_new_calls(self):
        self.legacy_receipt_fixture(1)

    def test_legacy_v2_partial_review_and_promotion_receipt_replay_without_new_calls(self):
        self.legacy_receipt_fixture(2)

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
                report["chapters"]["chapter-03"]["checks"]["Preserved strengths"]["original_evidence_ids"] = []
            else:
                feedback = packet.split("Deterministic output validation rejected", 1)[1]
                self.assertIn("response.chapters.chapter-03.checks.Preserved strengths.original_evidence_ids", feedback)
                self.assertNotIn("response.chapters.chapter-01", feedback)
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

    def test_unchanged_member_is_retained_while_valid_companion_still_needs_both_reviews(self):
        self.noop = True
        result = self.run_group()
        self.assertEqual(["promote", "reject"], [r["decision"] for r in result])
        self.assertEqual(self.originals["chapter-03.md"], (self.root / "manuscript/chapters/chapter-03.md").read_bytes())
        self.assertEqual([1], self.workflow.journal.data["revision_chapters"])
        self.assertEqual(7, len(self.calls))

    def test_precise_quote_feedback_repairs_a_negative_report_without_reversing_its_verdict(self):
        self.block = True
        original = self.generate
        attempts, correct = [], []
        def wrong_passage(call_id, packet, schema, root):
            report = original(call_id, packet, schema, root)
            if "chapters" not in schema["properties"]:
                return report
            attempts.append(call_id)
            if len(attempts) == 1:
                catalog = parse_catalog(packet.split("\nCatalog wire:\n", 1)[1])
                source = next(s for s in catalog["sources"] if s["source"] == "proposed/chapter-01.md")
                passage = next(p for p in source["passages"] if p["text"].startswith("The gate is closed."))
                correct.append(passage["id"])
                report["findings"][0]["proposed_evidence"][0]["quote"] = passage["text"]
            else:
                feedback = packet.split("Deterministic output validation rejected", 1)[1]
                self.assertIn("proposed_evidence[1]", feedback)
                self.assertIn("proposed/chapter-01.md", feedback)
                self.assertIn("Exact quote matches within this same source: " + correct[0], feedback)
                self.assertNotIn('"verdict"', feedback)
                self.assertNotIn("Previous rejected producer response", packet)
            return report
        self.workflow.transport = receipt_transport(wrong_passage)
        outcomes = self.run_group()
        self.assertTrue(all(r["decision"] == "reject" for r in outcomes))
        self.assert_originals()
        self.assertEqual(2, len(attempts))
        self.assertFalse(any("preference" in c for c in self.calls))
        step = self.workflow.journal.data["steps"]["revision-1-creative-group-1-3-check"]
        self.assertEqual("completed", step["status"])
        self.assertEqual("block", read_json(self.root / step["response"])["verdict"])
        self.assertFalse(step["request"]["feedback_response"])
        calls = len(self.calls)
        self.workflow = self.new_workflow()
        self.assertEqual(outcomes, self.run_group())
        self.assertEqual(calls, len(self.calls))

    def test_invalid_member_does_not_discard_valid_companion_without_full_book_review(self):
        self.invalid = {3}
        result = self.run_group()
        self.assertEqual(["promote", "reject"], [r["decision"] for r in result])
        self.assertEqual(self.originals["chapter-03.md"], (self.root / "manuscript/chapters/chapter-03.md").read_bytes())
        self.assertEqual([1], self.workflow.journal.data["revision_chapters"])
        self.assertEqual(8, len(self.calls))
        manifest = read_json(self.root / "work/creative-groups/revision-1-creative-group-1-3/manifest.json")
        self.assertEqual(3, manifest["schema_version"])
        self.assertEqual([3], [r["chapter"] for r in manifest["retained_members"]])
        self.assertNotIn("proposed/chapter-03.md", manifest["sources"])
        self.assertIn("The passage is open.", groups.volume(self.workflow.journal, manifest, True).decode())
        self.workflow = self.new_workflow()
        self.assertEqual(result, self.run_group())
        self.assertEqual(8, len(self.calls))

    def test_partial_group_still_blocks_a_dependency_on_the_missing_repair(self):
        self.invalid = {3}
        original = self.generate
        def missing_companion(call_id, packet, schema, root):
            if "chapters" not in schema["properties"]:
                return original(call_id, packet, schema, root)
            self.calls.append(call_id)
            assignments, _ = json.JSONDecoder().raw_decode(packet.split("Tasks and shared strategy:\n", 1)[1])
            self.assertEqual([3], [r["chapter"] for r in assignments["retained_members"]])
            self.assertEqual("unresolved_original_retained", assignments["retained_members"][0]["status"])
            self.assertEqual([1, 3], [t["chapter"] for t in assignments["tasks"]])
            self.assertIn("depends on an absent companion edit", packet)
            sources = {s["source"]: s for s in parse_catalog(packet.split("\nCatalog wire:\n", 1)[1])["sources"]}
            self.assertNotIn("proposed/chapter-03.md", sources)
            retained_open = any("The passage is open." in p["text"] for p in sources["original/chapter-03.md"]["passages"])
            proposed_closed = any("The gate is closed." in p["text"] for p in sources["proposed/chapter-01.md"]["passages"])
            self.assertTrue(retained_open and proposed_closed)
            return group_report(packet, schema, blocked=retained_open and proposed_closed)
        self.workflow.transport = receipt_transport(missing_companion)
        self.assertTrue(all(r["decision"] == "reject" for r in self.run_group()))
        self.assert_originals()
        self.assertEqual(4, len(self.calls))
        self.assertTrue(any("-check-" in c for c in self.calls))
        self.assertFalse(any("preference" in c for c in self.calls))

    def test_all_invalid_members_keep_originals_without_review_or_poll(self):
        self.invalid = {1, 3}
        self.assertTrue(all(r["decision"] == "reject" for r in self.run_group()))
        self.assert_originals()
        self.assertEqual(4, len(self.calls))
        self.assertFalse(any("-check-" in c or "preference" in c for c in self.calls))

    def test_partial_group_keeps_preference_rejection_and_never_changes_retained_member(self):
        self.invalid, self.prefer = {3}, False
        self.assertTrue(all(r["decision"] == "reject" for r in self.run_group()))
        self.assert_originals()
        self.assertEqual(8, len(self.calls))

    def test_failed_native_attempt_tampering_blocks_partial_group_replay(self):
        self.invalid = {3}
        self.run_group()
        response = next((self.root / "work/host-calls").glob("*-revision-1-c03-*/response"))
        response.write_bytes(response.read_bytes() + b" ")
        with self.assertRaisesRegex(WorkflowError, "evidence is missing or changed"):
            self.run_group()
        self.assertEqual(8, len(self.calls))

    def test_all_rejected_group_also_preserves_failed_native_evidence(self):
        self.invalid = {1, 3}
        self.run_group()
        response = next((self.root / "work/host-calls").glob("*-revision-1-c01-*/response"))
        response.write_bytes(response.read_bytes() + b" ")
        with self.assertRaisesRegex(WorkflowError, "evidence is missing or changed"):
            self.run_group()

    def test_new_retained_canon_after_review_prevents_partial_publication(self):
        self.invalid = {3}
        compare = self.workflow.compare_revision
        def change_retained(*args, **kwargs):
            result = compare(*args, **kwargs)
            original = self.root / "manuscript/chapters/chapter-03.md"
            original.write_bytes(original.read_bytes() + b"\nNew authorized canon.\n")
            self.workflow.journal.data["canonical"]["manuscript/chapters/chapter-03.md"] = groups.digest(original.read_bytes())
            self.workflow.journal.save()
            return result
        self.workflow.compare_revision = change_retained
        with self.assertRaisesRegex(WorkflowError, "complete reviewed manuscript is stale"):
            self.run_group()
        self.assertEqual(self.originals["chapter-01.md"], (self.root / "manuscript/chapters/chapter-01.md").read_bytes())

    def test_new_unassigned_canon_after_full_group_review_prevents_publication(self):
        compare = self.workflow.compare_revision
        def change_unassigned(*args, **kwargs):
            result = compare(*args, **kwargs)
            target = self.root / "manuscript/chapters/chapter-02.md"
            target.write_bytes(target.read_bytes() + b"\nA separately authorized new fact.\n")
            self.workflow.journal.data["canonical"]["manuscript/chapters/chapter-02.md"] = groups.digest(target.read_bytes())
            self.workflow.journal.save()
            return result
        self.workflow.compare_revision = change_unassigned
        with self.assertRaisesRegex(WorkflowError, "complete reviewed manuscript is stale"):
            self.run_group()
        for n in (1, 3):
            self.assertEqual(self.originals[f"chapter-{n:02d}.md"],
                (self.root / f"manuscript/chapters/chapter-{n:02d}.md").read_bytes())
        self.assertIn(b"A separately authorized new fact.",
            (self.root / "manuscript/chapters/chapter-02.md").read_bytes())

    def three_member_partial(self):
        self.invalid = {3}
        self.tasks.insert(1, {**self.tasks[0], "chapter": 2})

    def test_partial_group_recovers_only_changed_members_without_repolling(self):
        self.three_member_partial()
        self.interrupt()
        self.workflow = self.new_workflow()
        result = self.run_group()
        self.assertEqual(["promote", "promote", "reject"], [r["decision"] for r in result])
        self.assertEqual([1, 2], self.workflow.journal.data["revision_chapters"])
        self.assertEqual(self.originals["chapter-03.md"], (self.root / "manuscript/chapters/chapter-03.md").read_bytes())
        self.assertEqual(9, len(self.calls))

    def test_recovery_rejects_a_new_canonical_retained_chapter_not_seen_by_reviewers(self):
        self.three_member_partial()
        self.interrupt()
        target = self.root / "manuscript/chapters/chapter-03.md"
        target.write_bytes(target.read_bytes() + b"\nNew canonical fact.\n")
        # Even a recorded update cannot make the old whole-book review current.
        self.workflow.journal.data["canonical"]["manuscript/chapters/chapter-03.md"] = groups.digest(target.read_bytes())
        self.workflow.journal.save()
        with self.assertRaisesRegex(WorkflowError, "complete reviewed manuscript is stale"):
            self.new_workflow()
        self.assertEqual(self.originals["chapter-02.md"], (self.root / "manuscript/chapters/chapter-02.md").read_bytes())

    def test_receipt_without_outcomes_rejects_a_new_canonical_retained_chapter(self):
        self.invalid = {3}
        with patch.object(groups, "save_outcomes", side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            self.run_group()
        self.assertTrue((self.root / "evaluations/promotions/revision-1-creative-group-1-3.json").exists())
        self.assertFalse((self.root / "evaluations/decisions/revision-1-creative-group-1-3-outcomes.json").exists())
        self.assertIsNone(self.workflow.journal.data["pending_mutation"])
        target = self.root / "manuscript/chapters/chapter-03.md"
        target.write_bytes(target.read_bytes() + b"\nNew canonical fact after publication.\n")
        self.workflow.journal.data["canonical"]["manuscript/chapters/chapter-03.md"] = groups.digest(target.read_bytes())
        self.workflow.journal.save()
        self.workflow = self.new_workflow()
        with self.assertRaisesRegex(WorkflowError, "complete reviewed manuscript is stale"):
            self.run_group()
        self.assertEqual(8, len(self.calls))

    def test_receipt_without_outcomes_resumes_unchanged_partial_group_without_polling(self):
        self.invalid = {3}
        with patch.object(groups, "save_outcomes", side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            self.run_group()
        self.workflow = self.new_workflow()
        result = self.run_group()
        self.assertEqual(["promote", "reject"], [r["decision"] for r in result])
        self.assertEqual(8, len(self.calls))

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
        self.check_delivery(partial=False)

    def test_whole_workflow_exports_partial_group_and_preserves_rejected_member_evidence(self):
        self.check_delivery(partial=True)

    def check_delivery(self, partial):
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
                    result["prose"] = (context["accepted_chapter"] if partial and context["task"]["chapter"] == 2
                        else context["accepted_chapter"].replace("held the stolen letter", "chose to confess"))
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
            manifest = read_json(path)
            self.assertEqual(3, manifest["schema_version"])
            self.assertEqual([1] if partial else [1, 2], [r["chapter"] for r in manifest["publications"]])
            source = root / manifest["sources"]["original/chapter-01.md"]["path"]
            source.write_bytes(source.read_bytes() + b"Changed original evidence.")
            with redirect_stdout(io.StringIO()), self.assertRaisesRegex(WorkflowError, "evidence is missing or changed"):
                BookWorkflow(root, COMMAND, **options).run()
            self.assertEqual(count, len(calls))


if __name__ == "__main__":
    unittest.main()
