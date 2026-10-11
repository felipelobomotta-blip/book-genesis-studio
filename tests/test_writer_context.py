"""Regressions for lost character history and facts outside a closing excerpt."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from autonomous_book import BookWorkflow
from workflow_roles import character_context
from workflow_state import encoded, freeze
from test_autonomous_workflow import COMMAND, fixture_response, receipt_transport


CARDS = ("# Characters\n\n"
         "## Ada Vale, courier\n\nWound: Jo publicly blamed Ada for the lost letter.\n\n"
         "## Jo Vale — recipient\n\nDesire: Admit that she hid the envelope.\n\n"
         "## Will Hart, later visitor\n\nWill secretly arrives after the confession.\n")


class WriterContextTests(unittest.TestCase):
    def test_local_cards_keep_the_approved_motive_and_exclude_an_absent_character(self):
        selected = character_context(CARDS, "Ada and Jo will carry the letter. Ada's viewpoint.")
        self.assertIn("Jo publicly blamed Ada", selected)
        self.assertIn("Admit that she hid the envelope", selected)
        self.assertNotIn("Will Hart", selected)
        self.assertNotIn("secretly arrives", selected)

    def test_legacy_character_format_cannot_silently_erase_all_motivation(self):
        legacy = "# Cast\n\nAda: she wants to confess but fears her mother's judgment.\n"
        self.assertEqual(legacy, character_context(legacy, "Ada returns."))

    def test_actual_draft_handoff_retains_early_identity_outside_the_last_300_words(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze(root / ".book-genesis/project.json", encoded({
                "host": "codex", "collaboration": "autonomous", "author_name": "QA",
                "model": "exact-test-model", "effort": "high", "idea": "A letter returns.", "language": "English",
                "autonomous_contract": {"chapters": 2, "min_words": 800, "max_words": 1800, "quality_target": 8.5}}))
            freeze(root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
            packets = {}
            marker = "Denise Hall is a woman. She handed the brass key to Ada."

            def generate(call_id, packet, schema, book):
                packets[call_id] = packet
                data = fixture_response(call_id, packet, schema, book)
                if "files" in data and "artifacts/03-characters.md" in data["files"]:
                    data["files"]["artifacts/03-characters.md"] = CARDS
                if "canon" in data:
                    for chapter in data["chapters"]:
                        chapter.update(characters="Ada and Jo will carry the letter.", point_of_view="Ada")
                if "prose" in data:
                    number = 2 if "draft-02" in call_id else 1
                    data["prose"] = f"# Chapter {number}\n\n{marker}\n\n" + "Ada carried the letter down the lane. " * 60
                    # Deliberately incomplete summary: identities/custody must
                    # remain available from the actual preceding prose.
                    data["continuity_delta"] = "Ada carried the letter."
                return data

            workflow = BookWorkflow(root, COMMAND, chapters=2, min_words=800, max_words=1800,
                                    transport=receipt_transport(generate))
            with redirect_stdout(io.StringIO()):
                workflow.planning()
                workflow.draft()
            previous = (root / "manuscript/chapters/chapter-01.md").read_text(encoding="utf-8")
            self.assertNotIn(marker, " ".join(previous.split()[-300:]))
            context = json.loads(packets["wf-draft-02-1"].split("\n\n", 1)[1])
            self.assertEqual(previous, context["previous_chapter"])
            self.assertIn(marker, context["previous_chapter"])
            self.assertIn("Jo publicly blamed Ada", context["characters"])
            self.assertNotIn("Will Hart", context["characters"])
            self.assertNotIn("FUTURE_ONLY_RESOLUTION", packets["wf-draft-02-1"])
            self.assertNotIn("quality_target", context)

    def test_later_chapter_receives_original_history_when_every_summary_omits_a_fact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze(root / ".book-genesis/project.json", encoded({
                "host": "codex", "collaboration": "autonomous", "author_name": "QA",
                "model": "exact-test-model", "effort": "high", "idea": "A letter returns.", "language": "English",
                "autonomous_contract": {"chapters": 4, "min_words": 1600, "max_words": 3600, "quality_target": 8.5}}))
            freeze(root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
            packets = {}
            marker = "Old Dombrowski received the wire transfer in September."
            def generate(call_id, packet, schema, book):
                packets[call_id] = packet
                data = fixture_response(call_id, packet, schema, book)
                if "canon" in data:
                    template = data["chapters"][0]
                    data["chapters"] = [{**template, "number": n, "title": f"Chapter {n}"} for n in range(1, 5)]
                    data["chapters"][3]["events"] += " ONLY_FOURTH_CHAPTER_PLAN."
                if "prose" in data:
                    number = int(re.search(r"draft-(\d+)", call_id)[1])
                    fact = marker if number == 1 else "Ada remembered the letter."
                    data["prose"] = f"# Chapter {number}\n\n{fact}\n\n" + "Ada carried the letter down the lane. " * 60
                    data["continuity_delta"] = "Ada carried the letter."
                return data
            workflow = BookWorkflow(root, COMMAND, chapters=4, min_words=1600, max_words=3600,
                                    transport=receipt_transport(generate))
            with redirect_stdout(io.StringIO()):
                workflow.planning()
                workflow.draft()
            context = json.loads(packets["wf-draft-04-1"].split("\n\n", 1)[1])
            self.assertNotIn(marker, context["previous_chapter"])
            self.assertNotIn(marker, json.dumps(context["demonstrated_facts"]))
            self.assertEqual(["chapter-01.md", "chapter-02.md"], list(context["earlier_chapters"]))
            for name, prose in context["earlier_chapters"].items():
                self.assertEqual((root / "manuscript/chapters" / name).read_bytes(), prose.encode("utf-8"))
            self.assertIn(marker, context["earlier_chapters"]["chapter-01.md"])
            third = json.loads(packets["wf-draft-03-1"].split("\n\n", 1)[1])
            self.assertEqual(["chapter-01.md"], list(third["earlier_chapters"]))
            self.assertNotIn("ONLY_FOURTH_CHAPTER_PLAN", packets["wf-draft-03-1"])
            for number in range(1, 5):
                self.assertNotIn("quality_target", packets[f"wf-draft-{number:02d}-1"])
                self.assertNotIn("FUTURE_ONLY_RESOLUTION", packets[f"wf-draft-{number:02d}-1"])


if __name__ == "__main__":
    unittest.main()
