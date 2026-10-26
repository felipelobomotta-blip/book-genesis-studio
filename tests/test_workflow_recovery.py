"""Regressions observed in the real 12-chapter unattended acceptance run."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from workflow_roles import (PROSE_SCHEMA, TEXT, apply_corrections, enum, array, obj,
    review_schema, text_catalog, validate_prose, validate_corrections, validate_shape)
from workflow_issues import collect_issues, reconcile_issues, validate_issue_statuses
from workflow_state import Journal, encoded, freeze, read_json
from test_autonomous_workflow import COMMAND, receipt_transport, fixture_response
from autonomous_book import BookWorkflow


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_control_character_is_repaired_inside_reserved_native_attempts(self):
        journal = Journal(self.root, {"model": "exact-test-model", "effort": "high"})
        packets = []
        def produce(_id, packet, _schema, _root):
            packets.append(packet)
            return {"prose": '# One\n\n' + ('\x0022Wait.\x022' if len(packets) == 1 else '"Wait."'),
                    "continuity_delta": "Ada waits."}
        with redirect_stdout(io.StringIO()):
            response, report = journal.call("draft", b"Write the scene", PROSE_SCHEMA, COMMAND,
                lambda path: validate_prose(path, low=1, high=100), feedback=True, feedback_response=True,
                transport=receipt_transport(produce))
        self.assertTrue(report["valid"])
        self.assertEqual(2, len(journal.data["steps"]["draft"]["attempts"]))
        self.assertIn("XML-invalid", packets[1])
        self.assertIn("\\u0000", packets[1])
        self.assertNotIn("\x00", read_json(response)["prose"])
        from stage_chapter import stage_chapter
        source = self.root / "prose.md"
        source.write_text(read_json(response)["prose"], encoding="utf-8")
        self.assertEqual("staged", stage_chapter(source, self.root / "stage")["status"])

    def test_unpaired_surrogates_are_rejected_before_utf8_extraction(self):
        self.assertTrue(validate_shape("broken \ud800", TEXT))
        self.assertFalse(validate_shape("Valid — piano 🎹\n\ttext", TEXT))

    def test_coverage_schema_names_only_catalog_sources(self):
        catalog = text_catalog({"brief": "Brief.", "chapter-01.md": "# One\n\nScene."})
        schema = review_schema(catalog, passes=["Voice"])
        coverage = schema["properties"]["coverage"]
        self.assertEqual(["brief", "chapter-01.md"], coverage["items"]["enum"])
        self.assertEqual(2, coverage["minItems"])
        self.assertTrue(validate_shape(["brief", "chapter-01.md", "auditor reference"], coverage))

    def test_literal_factual_edits_preserve_every_other_byte_and_reject_ambiguity(self):
        original = "# One\n\nJune Venn arrived on Tuesday.\n\nThe piano stayed shut.\n"
        edits = [{"before": "June Venn", "after": "June Vale"}, {"before": "on Tuesday", "after": "on Thursday"}]
        self.assertEqual(original.replace("June Venn", "June Vale").replace("on Tuesday", "on Thursday"), apply_corrections(original, edits))
        unchanged = {"before": "The piano stayed shut.", "after": "The piano stayed shut."}
        self.assertEqual(apply_corrections(original, edits), apply_corrections(original, edits + [unchanged]))
        with self.assertRaises(ValueError):
            apply_corrections(original, [unchanged])
        for bad in ([{"before": " ", "after": "_"}],
                    [{"before": "June Venn", "after": "June Vale"}, {"before": "Venn", "after": "Vale"}],
                    [{"before": "# One", "after": "# Another"}]):
            with self.assertRaises(ValueError):
                apply_corrections(original, bad)
        path = self.root / "response"
        path.write_bytes(encoded({"replacements": [{"before": "Venn", "after": "Vale\x00"}]}))
        self.assertFalse(validate_corrections(path, original, low=1, high=100)["valid"])

    def test_history_omitted_by_later_audit_still_reaches_correctness_check(self):
        from types import SimpleNamespace
        journal = Journal(self.root, {})
        catalog = text_catalog({"chapter-01.md": "# One\n\nA wrong age."})
        raw = {"findings": [{"severity": "high", "kind": "continuity", "chapters": [1],
            "evidence_ids": ["s01p0002"], "problem": "Age changes.", "fix": "Keep the established age.", "preserve": "Voice."}]}
        response = self.root / "audit-response"
        freeze(response, encoded(raw))
        freeze(self.root / "work/workflow/audit-original/packet.md", ("Complete sources:\n" + json.dumps(catalog)).encode())
        journal.data["steps"]["audit-original"] = {"status": "completed", "response": "audit-response", "evidence": [journal.record_file(response)]}
        # The newer audit contains no finding, which must not close the old one.
        new = self.root / "later-response"
        freeze(new, encoded({"findings": []}))
        freeze(self.root / "work/workflow/measure-1-audit/packet.md", ("Complete sources:\n" + json.dumps(catalog)).encode())
        journal.data["steps"]["measure-1-audit"] = {"status": "completed", "response": "later-response", "evidence": [journal.record_file(new)]}
        issues = collect_issues(SimpleNamespace(root=self.root, journal=journal), 1)
        self.assertEqual(["audit-original-f001"], [issue["id"] for issue in issues])
        self.assertEqual("A wrong age.", issues[0]["original_evidence"][0]["text"])

    def test_partial_chapter_evidence_cannot_close_multichapter_defect(self):
        catalog = text_catalog({"chapter-01.md": "# One\n\nThursday.", "chapter-02.md": "# Two\n\nMonday."})
        issues = [{"id": "timeline", "finding": {"chapters": [1, 2]}}]
        ids = [p["id"] for source in catalog["sources"] for p in source["passages"]]
        schema = obj({"statuses": array(obj({"id": enum(["timeline"]), "status": enum(["open", "resolved", "not_supported"]),
            "reason": TEXT, "evidence_ids": array(enum(ids))}))})
        path = self.root / "response"
        row = {"id": "timeline", "status": "resolved", "reason": "An incomplete assertion.", "evidence_ids": ["s01p0002"]}
        path.write_bytes(encoded({"statuses": [row]}))
        self.assertFalse(validate_issue_statuses(path, schema, issues, catalog)["valid"])
        row["status"] = "open"
        path.write_bytes(encoded({"statuses": [row]}))
        self.assertTrue(validate_issue_statuses(path, schema, issues, catalog)["valid"])

    def test_status_format_retry_identifies_missing_chapter_without_disclosing_prior_judgment(self):
        from types import SimpleNamespace
        journal = Journal(self.root, {})
        texts = {"chapter-01.md": "# One\n\nThe delivery happened Thursday.",
                 "chapter-02.md": "# Two\n\nThe same delivery happened Monday."}
        snapshot = []
        for name, text in texts.items():
            path = self.root / name
            freeze(path, text.encode())
            snapshot.append(path)
        catalog = text_catalog(texts)
        response = self.root / "audit-response"
        freeze(response, encoded({"findings": [{"severity": "high", "kind": "continuity", "chapters": [1, 2],
            "evidence_ids": ["s01p0002", "s02p0002"], "problem": "The delivery date conflicts.",
            "fix": "Establish one delivery date.", "preserve": "Voice."}]}))
        freeze(self.root / "work/workflow/audit-original/packet.md", ("Complete sources:\n" + json.dumps(catalog)).encode())
        journal.data["steps"]["audit-original"] = {"status": "completed", "response": "audit-response", "evidence": [journal.record_file(response)]}
        packets = []
        def generate(call_id, packet, schema, root):
            packets.append(packet)
            if len(packets) == 1:
                return {"statuses": [{"id": "audit-original-f001", "status": "resolved",
                    "reason": "UNIQUE_REJECTED_JUDGMENT", "evidence_ids": ["s01p0002"]}]}
            self.assertIn("missing chapter-02.md", packet)
            self.assertNotIn("UNIQUE_REJECTED_JUDGMENT", packet)
            self.assertNotIn("Previous rejected producer response", packet)
            return {"statuses": [{"id": "audit-original-f001", "status": "open",
                "reason": "The current two chapters still disagree.", "evidence_ids": ["s01p0002", "s02p0002"]}]}
        def call(key, packet, schema, validator, **kwargs):
            return journal.call(key, packet.encode(), schema, COMMAND, validator,
                                transport=receipt_transport(generate), **kwargs)
        workflow = SimpleNamespace(root=self.root, journal=journal, neutral_sources=lambda _: texts, call=call)
        with redirect_stdout(io.StringIO()):
            result = reconcile_issues(workflow, 1, snapshot)
        self.assertEqual(2, len(packets))
        self.assertFalse(result["passed"])
        self.assertEqual("open", result["statuses"][0]["status"])
        self.assertTrue(journal.data["steps"]["issue-check-1"]["attempts"][-1]["feedback_evidence"])
        with redirect_stdout(io.StringIO()):
            self.assertEqual(result, reconcile_issues(workflow, 1, snapshot))
        self.assertEqual(2, len(packets))

    def test_exhausted_invalid_issue_statuses_keep_all_findings_open_with_native_evidence(self):
        from types import SimpleNamespace
        from workflow_state import WorkflowError
        journal = Journal(self.root, {})
        text = "# One\n\nThe delivery happened Thursday."
        chapter = self.root / "chapter-01.md"
        freeze(chapter, text.encode())
        snapshot = [chapter]
        catalog = text_catalog({"chapter-01.md": text})
        response = self.root / "audit-response"
        freeze(response, encoded({"findings": [{"severity": "high", "kind": "continuity", "chapters": [1],
            "evidence_ids": ["s01p0002"], "problem": "The delivery date conflicts.",
            "fix": "Establish one delivery date.", "preserve": "Voice."}]}))
        freeze(self.root / "work/workflow/audit-original/packet.md", ("Complete sources:\n" + json.dumps(catalog)).encode())
        journal.data["steps"]["audit-original"] = {"status": "completed", "response": "audit-response",
            "evidence": [journal.record_file(response)]}
        calls = []

        def generate(call_id, packet, schema, root):
            calls.append(call_id)
            return {"statuses": []}  # invalid even after the format-only retry

        def call(key, packet, schema, validator, **kwargs):
            return journal.call(key, packet.encode(), schema, COMMAND, validator,
                                transport=receipt_transport(generate), **kwargs)

        workflow = SimpleNamespace(root=self.root, journal=journal,
            neutral_sources=lambda _: {"chapter-01.md": text}, call=call)
        with redirect_stdout(io.StringIO()):
            result = reconcile_issues(workflow, 1, snapshot)
        self.assertEqual(2, len(calls))
        self.assertFalse(result["passed"])
        self.assertEqual("open", result["statuses"][0]["status"])
        self.assertEqual("controller_fail_closed_after_invalid_native_responses", result["status_source"])
        self.assertIn("not a factual determination", result["statuses"][0]["reason"])
        self.assertTrue(any(row["path"].startswith("work/host-calls/wf-issue-check-1-")
                            for row in result["evidence"]))
        self.assertTrue((self.root / "evaluations/issue-status-fallback-1.json").is_file())
        self.assertEqual("failed", journal.data["steps"]["issue-check-1"]["status"])

    def test_factual_fix_reaches_export_without_preference_votes(self):
        root = self.root
        freeze(root / ".book-genesis/project.json", encoded({"schema_version": 1, "host": "codex", "collaboration": "autonomous",
            "author_name": "QA", "model": "exact-test-model", "effort": "high", "idea": "Ada Vale returns a letter.", "language": "English",
            "autonomous_contract": {"chapters": 2, "min_words": 240, "max_words": 600, "quality_target": 8.5}}))
        freeze(root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
        calls = []
        def generate(call_id, packet, schema, book):
            calls.append(call_id)
            props = schema["properties"]
            if "corrections" in props:
                sources = json.loads(packet.rsplit("\n\n", 1)[1])["accepted_chapter"]
                passage = next(row for row in sources if "Ida Vale" in row["text"])
                return {"corrections": [{"from_passage": passage["id"], "through_passage": passage["id"],
                                        "after": passage["text"].replace("Ida Vale", "Ada Vale")}]}
            if "canon_supported" in props:
                from catalog_wire import parse_catalog
                catalog = parse_catalog(packet.split('\nCatalog wire:\n', 1)[1])
                ids = [p['id'] for s in catalog['sources'] for p in s['passages']]
                return {"verdict": "pass", "canon_supported": True, "factual_only": True, "dependencies_safe": True,
                    "evidence": [{"passage_id": next(p for p in ids if p.startswith(source)), "reason": "Name matches frozen canon."}
                                 for source in ("accepted-p", "candidate-p", "canon-1-p")], "findings": []}
            result = fixture_response(call_id, packet, schema, book)
            if "prose" in props and "draft-01" in call_id:
                result["prose"] = result["prose"].replace("The courier", "Ida Vale", 1)
            if "strategy" in props:
                result["tasks"][0].update(mode="factual", ticket="Correct Ida Vale to the established Ada Vale.", revision_class="continuity")
            if "checks" in props:
                for finding in result["findings"]:
                    finding.update(kind="continuity", problem="Ida Vale differs from the established Ada Vale.", fix="Use Ada Vale.")
            return result
        kwargs = dict(chapters=2, min_words=240, max_words=600, transport=receipt_transport(generate))
        with redirect_stdout(io.StringIO()):
            workflow = BookWorkflow(root, COMMAND, **kwargs)
            self.assertEqual(0, workflow.run())
        corrected = (root / "manuscript/chapters/chapter-01.md").read_text(encoding="utf-8")
        original = (root / "work/revisions/revision-1-c01-facts/chapter-01.md").read_text(encoding="utf-8")
        self.assertEqual(original.replace("Ida Vale", "Ada Vale"), corrected)
        decision = read_json(root / "evaluations/decisions/revision-1-c01-facts.json")
        self.assertEqual("verified_correction", decision["kind"])
        self.assertFalse(any("revision-1-c01-facts-primary" in call for call in calls))
        self.assertTrue(list((root / "delivery").glob("*.epub")))
        before = len(calls)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, BookWorkflow(root, COMMAND, **kwargs).run())
        self.assertEqual(before, len(calls))

    def test_two_invalid_optional_revisions_keep_the_accepted_chapter_and_export(self):
        root = self.root
        freeze(root / ".book-genesis/project.json", encoded({"schema_version": 1, "host": "codex", "collaboration": "autonomous",
            "author_name": "QA", "model": "exact-test-model", "effort": "high", "idea": "A letter returns.", "language": "English",
            "autonomous_contract": {"chapters": 2, "min_words": 240, "max_words": 600, "quality_target": 8.5}}))
        freeze(root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
        def generate(call_id, packet, schema, book):
            result = fixture_response(call_id, packet, schema, book)
            if "prose" in schema["properties"] and "revision-" in call_id:
                result["prose"] += "\x00"
            return result
        with redirect_stdout(io.StringIO()):
            workflow = BookWorkflow(root, COMMAND, chapters=2, min_words=240, max_words=600,
                transport=receipt_transport(generate))
            self.assertEqual(0, workflow.run())
        step = workflow.journal.data["steps"]["revision-1-c01"]
        self.assertEqual("failed", step["status"])
        self.assertEqual(2, len(step["attempts"]))
        self.assertTrue(step["rejected_evidence"])
        self.assertEqual((root / "work/snapshots/original-draft/chapter-01.md").read_bytes(),
                         (root / "manuscript/chapters/chapter-01.md").read_bytes())
        self.assertTrue(list((root / "delivery").glob("*.epub")))
        from workflow_state import verify_execution, WorkflowError
        verify_execution(root)
        (root / "work/host-calls/wf-revision-1-c01-1/response").write_text("changed")
        with self.assertRaises(WorkflowError):
            verify_execution(root)

    def test_weighted_goal_does_not_stop_at_a_passing_dimension_floor(self):
        root = self.root
        freeze(root / ".book-genesis/project.json", encoded({"host": "codex", "collaboration": "autonomous", "author_name": "QA",
            "model": "exact-test-model", "effort": "high", "idea": "A letter returns.", "language": "English"}))
        freeze(root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
        freeze(root / "artifacts/01-market-map.md", b"Unverified positioning.")
        snapshot = [root / f"snapshot/chapter-{n:02d}.md" for n in (1, 2)]
        for path in snapshot:
            freeze(path, b"# A letter\n\nAda chose to confess.\n\nJo opened the door.\n")
        with redirect_stdout(io.StringIO()):
            workflow = BookWorkflow(root, COMMAND, chapters=2, min_words=240, max_words=600, weighted_quality_target=9.0,
                transport=receipt_transport(fixture_response))
            report = workflow.rubric("measure-1-rubric", snapshot)
        self.assertEqual(8.6, report["floor"])
        self.assertEqual(8.6, report["weighted"])
        self.assertFalse(report["passed"])
        packet = (root / "work/workflow/measure-1-rubric-1/packet.md").read_text(encoding="utf-8")
        self.assertNotIn("weighted_quality_target", packet)
        self.assertNotIn("quality_target", packet)

    def test_plan_repairs_cannot_rewrite_unrelated_fields_or_change_chapter_numbers(self):
        from workflow_roles import plan_schema, plan_repair_schema, apply_plan_edits
        data = fixture_response("architecture", "", plan_schema(2), self.root)
        after = data["chapters"][0]["events"] + " The rescue physically reaches safety."
        edits = [{"path": "/chapters/0/events", "before": data["chapters"][0]["events"], "after": after}]
        repaired = apply_plan_edits(data, edits)
        native_edits = [{"path": row["path"], "after": row["after"]} for row in edits]
        self.assertEqual(repaired, apply_plan_edits(data, native_edits))
        self.assertEqual(data["chapters"][1], repaired["chapters"][1])
        self.assertEqual(data["canon"], repaired["canon"])
        self.assertEqual(data["writer_facts"], repaired["writer_facts"])
        self.assertNotEqual(data["chapters"][0]["events"], repaired["chapters"][0]["events"])
        unchanged = {"path": "/chapters/1/events", "before": data["chapters"][1]["events"], "after": data["chapters"][1]["events"]}
        self.assertEqual(repaired, apply_plan_edits(data, edits + [unchanged]))
        with self.assertRaisesRegex(ValueError, "No substantive plan edit"):
            apply_plan_edits(data, [unchanged])
        schema = plan_repair_schema(data)
        self.assertEqual("object", schema["properties"]["edits"]["type"])
        self.assertNotIn("/chapters/0/number", schema["properties"]["edits"]["properties"])
        with self.assertRaises(ValueError):
            apply_plan_edits(data, edits + edits)
        with self.assertRaises(ValueError):
            apply_plan_edits(data, [{"path": "/chapters/0/events", "before": "invented original", "after": after}])

    def test_multiple_plan_defects_are_repaired_with_a_durable_three_repair_limit(self):
        root = self.root
        freeze(root / ".book-genesis/project.json", encoded({"host": "codex", "collaboration": "autonomous", "author_name": "QA",
            "model": "exact-test-model", "effort": "high", "idea": "A letter returns.", "language": "English"}))
        freeze(root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
        calls = []
        def generate(call_id, packet, schema, book):
            calls.append(call_id)
            if "plan-check-" in call_id:
                return fixture_response("wf-plan-check-0-1", packet, schema, book)
            return fixture_response(call_id, packet, schema, book)
        with redirect_stdout(io.StringIO()):
            workflow = BookWorkflow(root, COMMAND, chapters=2, min_words=240, max_words=600, transport=receipt_transport(generate))
            from workflow_state import WorkflowError
            with self.assertRaisesRegex(WorkflowError, "three bounded plan repairs"):
                workflow.planning()
            before = len(calls)
            resumed = BookWorkflow(root, COMMAND, chapters=2, min_words=240, max_words=600, transport=receipt_transport(generate))
            with self.assertRaisesRegex(WorkflowError, "three bounded plan repairs"):
                resumed.planning()
        self.assertEqual(before, len(calls))
        self.assertEqual(3, sum("architecture-repair" in call for call in calls))
        self.assertEqual(4, sum("plan-check-" in call for call in calls))
        self.assertFalse(list((root / "manuscript/chapters").glob("*.md")))

    def test_three_pass_exhaustion_exports_honestly_without_rerating_unchanged_prose(self):
        for mode in ("below_weighted_goal", "unassessed_dimension"):
            with self.subTest(mode=mode):
                root = self.root / mode
                freeze(root / ".book-genesis/project.json", encoded({"host": "codex", "collaboration": "autonomous", "author_name": "QA",
                    "model": "exact-test-model", "effort": "high", "idea": "A letter returns.", "language": "English",
                    "autonomous_contract": {"chapters": 2, "min_words": 240, "max_words": 600, "quality_target": 8.5, "weighted_quality_target": 9.0}}))
                freeze(root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
                calls = []
                def generate(call_id, packet, schema, book):
                    calls.append(call_id)
                    result = fixture_response(call_id, packet, schema, book)
                    if mode == "unassessed_dimension" and "dimensions" in schema["properties"]:
                        result["dimensions"][-1]["score"] = None
                    return result
                kwargs = dict(chapters=2, min_words=240, max_words=600, weighted_quality_target=9.0,
                              transport=receipt_transport(generate))
                with redirect_stdout(io.StringIO()):
                    workflow = BookWorkflow(root, COMMAND, **kwargs)
                    self.assertEqual(0, workflow.run())
                self.assertEqual(3, len(workflow.journal.data["passes"]))
                result = read_json(root / "evaluations/final-measurement.json")
                self.assertFalse(result["passed"])
                self.assertEqual(1, result["number"])
                self.assertTrue(list((root / "delivery").glob("*.epub")))
                self.assertFalse(any("measure-2" in call or "measure-3" in call for call in calls))
                self.assertFalse(any("revision-2-c01-primary" in call for call in calls))
                self.assertEqual("reject", read_json(root / "evaluations/decisions/revision-2-c01.json")["decision"])
                if mode == "unassessed_dimension":
                    self.assertIsNone(result["rubric"]["weighted"])
                    self.assertIsNone(result["rubric"]["floor"])
                    self.assertIn("unassessed", (root / "artifacts/11-genesis-score.md").read_text(encoding="utf-8"))
                before = len(calls)
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(0, BookWorkflow(root, COMMAND, **kwargs).run())
                self.assertEqual(before, len(calls))


if __name__ == "__main__":
    unittest.main()
