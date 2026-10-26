"""Native failures: numerical score leakage and distant correction evidence."""
from contextlib import redirect_stdout
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from autonomous_book import BookWorkflow
from editorial_feedback import score_blind
from workflow_state import encoded, freeze, read_json
from test_autonomous_workflow import COMMAND, fixture_response, receipt_transport


class EditorialScoreBoundaryTests(unittest.TestCase):
    def test_actual_cap_sentence_is_removed_without_removing_the_defect(self):
        original = ("The contrast-by-negation tell repeats in chapters 3, 4 and 5. "
                    "That is more than a quarter of the chapters, so the Prose cap of 7.5 applies. "
                    "Repeated stock images accumulate.")
        self.assertEqual("The contrast-by-negation tell repeats in chapters 3, 4 and 5. "
                         "Repeated stock images accumulate.", score_blind(original))
        self.assertIn("7.5", original)

    def test_ratings_are_withheld_but_observed_counts_and_story_numbers_survive(self):
        for text in ("Prose: 7.5/10.", "Raise the score to 9.1.", "Rated 90 out of 100.",
                     "A nota foi 7,5.", "The calibrated floor is 6.3."):
            with self.subTest(text=text):
                self.assertEqual("", score_blind(text))
        facts = "Chapter 12 repeats the line 3 times. Nell paid $2,400 on September 18. The tempo is 90."
        self.assertEqual(facts, score_blind(facts))

    def test_nested_feedback_keeps_ids_and_does_not_mutate_the_raw_report(self):
        value = {"evidence": [{"passage_id": "c04p0105", "reason": "Score: 7.5. The gesture repeats."}],
                 "issue_ids": ["measure-0-proof-f005"], "chapter": 4}
        original = copy.deepcopy(value)
        clean = score_blind(value)
        self.assertEqual("The gesture repeats.", clean["evidence"][0]["reason"])
        self.assertEqual(value, original)
        self.assertEqual(value["issue_ids"], clean["issue_ids"])
        self.assertEqual({"text": "The score was 9.1."}, score_blind({"text": "The score was 9.1."}))

    def test_actual_workflow_keeps_raw_scores_and_excludes_them_from_editor_packets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze(root / ".book-genesis/project.json", encoded({
                "host": "codex", "collaboration": "autonomous", "author_name": "QA",
                "model": "exact-test-model", "effort": "high", "idea": "A letter returns.", "language": "English",
                "autonomous_contract": {"chapters": 2, "min_words": 240, "max_words": 600, "quality_target": 8.5}}))
            freeze(root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
            packets = {}
            def generate(call_id, packet, schema, book):
                packets[call_id] = packet
                data = fixture_response(call_id, packet, schema, book)
                if "dimensions" in data:
                    data["dimensions"][0]["reason"] = "The gesture repeats in chapter 1. The Prose cap of 7.5 applies."
                    data["dimensions"][0]["evidence"][0]["reason"] = "Score: 7.5. The gesture repeats."
                if "strategy" in data:
                    data["strategy"] += " Raise the score to 9.1."
                return data
            workflow = BookWorkflow(root, COMMAND, chapters=2, min_words=240, max_words=600,
                                    transport=receipt_transport(generate))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, workflow.run())
            planner = packets["wf-revision-plan-1-1"]
            writer = packets["wf-revision-1-c01-1"]
            self.assertNotIn("Prose cap of 7.5", planner, "Numeric cap reached the revision planner")
            self.assertNotIn("Raise the score to 9.1", writer, "A planner's generated score reached the prose editor")
            self.assertIn("The gesture repeats", planner)
            original = read_json(root / "work/host-calls/wf-measure-0-rubric-1-1/response")
            self.assertIn("7.5", original["dimensions"][0]["reason"])
            self.assertEqual(8.8, original["dimensions"][0]["score"])


class DistantCorrectionEvidenceTests(unittest.TestCase):
    def test_editor_and_checker_receive_distant_current_prose_with_original_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze(root / ".book-genesis/project.json", encoded({
                "host": "codex", "collaboration": "autonomous", "author_name": "QA",
                "model": "exact-test-model", "effort": "high", "idea": "The gate repair.", "language": "English"}))
            freeze(root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
            packets = {}
            marker = "The gate is galvanised mesh at eleven dollars a length."
            def generate(call_id, packet, schema, book):
                packets[call_id] = packet
                if "corrections" in schema["properties"]:
                    context = json.loads(packet.rsplit("\n\n", 1)[1])
                    passage = next(p for p in context["accepted_chapter"] if "plastic gate" in p["text"])
                    return {"corrections": [{"from_passage": passage["id"], "through_passage": passage["id"],
                        "after": passage["text"].replace("plastic gate", "galvanised mesh gate")}]}
                from catalog_wire import parse_catalog
                catalog = parse_catalog(packet.split('\nCatalog wire:\n', 1)[1])
                ids = [p['id'] for s in catalog['sources'] for p in s['passages']]
                # The synthetic checker exercises the real source/receipt gate,
                # not a claim of model quality. Remote source evidence is required.
                self.assertIn(marker, packet)
                return {"verdict": "pass", "canon_supported": True, "factual_only": True,
                    "dependencies_safe": True, "findings": [], "evidence": [
                        {"passage_id": next(i for i in ids if i == prefix + "-p0002"), "reason": "Verified source fact."}
                        for prefix in ("accepted", "candidate", "canon-1", "canon-4")]}
            workflow = BookWorkflow(root, COMMAND, chapters=5, min_words=500, max_words=2000,
                                    transport=receipt_transport(generate))
            originals = {}
            for n in range(1, 6):
                sentence = marker if n in (1, 5) else "She repaired the plastic gate." if n == 3 else "She crossed the street."
                data = (f"# Gate {n}\n\n{sentence}\n\n" + "She carried the letter down the lane. " * 20 + "\n").encode("utf-8")
                source = root / "fixture" / f"chapter-{n:02d}.md"
                freeze(source, data)
                workflow.journal.publish(source, root / "manuscript/chapters" / source.name)
                originals[source.name] = data
            for name in ("00-brief.md", "03-characters.md", "05-voice.md", "07-outline.md", "09-continuity-ledger.md"):
                freeze(root / "artifacts" / name, b"# Notes\n\nShe repairs a gate. Material and price were omitted.\n")
            task = {"chapter": 3, "mode": "factual", "ticket": "Use the established mesh material from chapters 1 and 5.",
                    "preserve": "Every action.", "revision_class": "continuity", "issue_ids": []}
            with redirect_stdout(io.StringIO()):
                outcome = workflow.revise_chapter(1, task, "Match the demonstrated fact.")
            self.assertEqual("promote", outcome["decision"])
            packet = json.loads(packets["wf-revision-1-c03-facts-1"].rsplit("\n\n", 1)[1])
            self.assertIsNone(packet["craft_knowledge"], "A strictly factual editor must not get stylistic rewrite material")
            self.assertNotIn(marker, " ".join(packet["adjacent_context"]))
            for name, text in packet["other_current_chapters"].items():
                self.assertEqual(originals[name], text.encode("utf-8"))
            self.assertEqual(4, len(packet["other_current_chapters"]))
            manifest = read_json(root / "work/corrections/revision-1-c03-facts/manifest.private.json")
            full_chapters = [row for row in manifest["sources"] if "source-book" in row["path"]]
            self.assertEqual(4, len(full_chapters))
            for row in full_chapters:
                path = Path(row["path"])
                self.assertEqual(originals[path.name], path.read_bytes())
            count = len(packets)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(outcome, workflow.revise_chapter(1, task, "Match the demonstrated fact."))
            self.assertEqual(count, len(packets))


if __name__ == "__main__":
    unittest.main()
