"""Dated edition facts stay bounded, source-bound and stable across resume."""
from contextlib import redirect_stdout
from copy import deepcopy
from datetime import date
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/book-genesis"
sys.path.insert(0, str(SKILL / "scripts"))
from autonomous_book import BookWorkflow
from research_context import REFERENCE, frozen_reference_metadata, reference_metadata
from workflow_state import WorkflowError, digest, encoded, freeze, read_json
from test_autonomous_workflow import COMMAND, fixture_response, receipt_transport


class ResearchContextTests(unittest.TestCase):
    def test_shipped_metadata_is_seven_named_editions_not_prose_or_live_market_data(self):
        view = reference_metadata(SKILL, "English", today=date(2026, 10, 11))
        self.assertEqual("dated_publisher_metadata_snapshot", view["status"])
        self.assertEqual(7, len(view["entries"]))
        self.assertEqual(digest((SKILL / "references" / REFERENCE).read_bytes()), view["reference_sha256"])
        self.assertEqual(0, view["days_since_checked"])
        woods = next(row for row in view["entries"] if row["title"] == "The God of the Woods")
        self.assertEqual(("Paperback", "2025-10-28", "9780593418925", 576),
                         (woods["format"], woods["edition_publication_date"], woods["isbn13"], woods["pages"]))
        self.assertIn("not a live market survey", view["scope"])
        self.assertIn("do not establish prose word counts", view["limitations"])
        self.assertTrue(all("prose" not in row and "sales" not in row and "demand" not in row for row in view["entries"]))

    def test_other_languages_do_not_load_or_claim_english_market_facts(self):
        for language in ("Portuguese", "pt-BR", "Spanish", "German"):
            with self.subTest(language=language):
                view = reference_metadata(Path("missing-skill"), language, today=date(2026, 10, 11))
                self.assertEqual("not_available_for_language", view["status"])
                self.assertEqual([], view["entries"])
                self.assertNotIn("reference_sha256", view)
        for language in ("English", "en", "en-US", "en_GB"):
            self.assertEqual(7, len(reference_metadata(SKILL, language, today=date(2026, 10, 11))["entries"]))

    def test_snapshot_age_is_explicit_and_future_dated_facts_are_unavailable(self):
        older = reference_metadata(SKILL, "English", today=date(2027, 10, 11))
        self.assertEqual(365, older["days_since_checked"])
        self.assertEqual("2026-10-11", older["checked_date"])
        future = reference_metadata(SKILL, "English", today=date(2026, 10, 10))
        self.assertEqual("future_dated_snapshot_unavailable", future["status"])
        self.assertEqual([], future["entries"])
        self.assertNotIn("checked_date", future)

    def test_invalid_catalogs_fail_before_any_host_call_or_network_request(self):
        original = read_json(SKILL / "references" / REFERENCE)
        variants = []
        for key, value in (("schema_version", 2), ("language", "Portuguese"),
                           ("checked_date", "not-a-date"), ("scope", ""), ("entries", [])):
            changed = deepcopy(original); changed[key] = value; variants.append(changed)
        for key, value in (("url", "http://example.com"), ("url", "https://user:secret@example.com"),
                           ("edition_publication_date", "invalid"), ("pages", True), ("pages", 0),
                           ("title", ""), ("isbn13", "9780593418924")):
            changed = deepcopy(original); changed["entries"][0][key] = value; variants.append(changed)
        changed = deepcopy(original); changed["entries"].append(changed["entries"][0]); variants.append(changed)
        changed = deepcopy(original); del changed["limitations"]; variants.append(changed)
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp); path = skill / "references" / REFERENCE
            path.parent.mkdir(parents=True)
            for index, changed in enumerate(variants):
                with self.subTest(index=index):
                    path.write_bytes(encoded(changed))
                    with self.assertRaises(WorkflowError):
                        reference_metadata(skill, "English", today=date(2026, 10, 11))

    def test_frozen_intake_reuses_observation_date_and_rejects_changed_facts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reference-metadata.json"
            with patch("research_context.date", wraps=date) as clock:
                clock.today.return_value = date(2026, 10, 11)
                first = frozen_reference_metadata(SKILL, "English", path)
                clock.today.return_value = date(2027, 10, 11)
                self.assertEqual(first, frozen_reference_metadata(SKILL, "English", path))
            changed = read_json(path); changed["entries"][0]["pages"] = 1
            path.write_bytes(encoded(changed))
            with self.assertRaisesRegex(WorkflowError, "Immutable evidence changed"):
                frozen_reference_metadata(SKILL, "English", path)
            self.assertEqual(changed, read_json(path))

    def test_completed_intake_binds_snapshot_and_tampering_blocks_resume_before_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze(root / ".book-genesis/project.json", encoded({"host": "codex", "collaboration": "autonomous",
                "author_name": "QA", "model": "exact-test-model", "effort": "high", "idea": "A letter returns.",
                "language": "English", "autonomous_contract": {"chapters": 2, "min_words": 240, "max_words": 600}}))
            freeze(root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
            kwargs = dict(chapters=2, min_words=240, max_words=600, transport=receipt_transport(fixture_response))
            workflow = BookWorkflow(root, COMMAND, **kwargs)
            finish = workflow.finish
            def stop_after_intake(phase, evidence, **options):
                finish(phase, evidence, **options)
                if phase == 0:
                    raise KeyboardInterrupt()
            with redirect_stdout(io.StringIO()), patch.object(workflow, "finish", side_effect=stop_after_intake):
                with self.assertRaises(KeyboardInterrupt):
                    workflow.run()
            self.assertEqual(1, workflow.journal.data["phase"])
            path = root / "work/research/reference-metadata.json"
            packet = (root / "work/workflow/intake/packet.md").read_text(encoding="utf-8")
            self.assertIn('"reference_metadata"', packet)
            self.assertIn(read_json(path)["reference_sha256"], packet)
            evidence = workflow.journal.data["phase_evidence"]["0"]["files"]
            self.assertEqual(digest(path.read_bytes()), next(row["sha256"] for row in evidence
                             if row["path"] == "work/research/reference-metadata.json"))
            calls = len(list((root / "work/host-calls").iterdir()))
            path.write_bytes(b'{}')
            with redirect_stdout(io.StringIO()), self.assertRaisesRegex(WorkflowError, "Saved evidence is missing or changed"):
                BookWorkflow(root, COMMAND, **kwargs).run()
            self.assertEqual(calls, len(list((root / "work/host-calls").iterdir())))
            self.assertEqual(b'{}', path.read_bytes())


if __name__ == "__main__":
    unittest.main()
