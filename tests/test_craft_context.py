"""Actual tool-free role packets must contain their permitted skill knowledge."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/book-genesis"
sys.path.insert(0, str(SKILL / "scripts"))
from autonomous_book import BookWorkflow
from build_comparison import reader_schema
from craft_context import draft_knowledge, revision_knowledge, language_tells
from native_claude import compact_native_schema
from validate_blind_reader import MAX_EMOTION_LENGTH
from workflow_state import encoded, freeze
from test_autonomous_workflow import COMMAND, fixture_response, receipt_transport


class CraftContextTests(unittest.TestCase):
    def test_draft_receives_only_the_existing_sections_allowed_while_writing(self):
        data = draft_knowledge(SKILL)
        text = data["specialists/prose-craft.md#sections-1-5"]
        source = (SKILL / "references/specialists/prose-craft.md").read_text(encoding="utf-8")
        self.assertEqual(source[source.index("## 1. Openings"):source.index("## 6. Revision moves")].strip(), text)
        self.assertIn("### Real speech is messy", text)
        self.assertNotIn("### The eight moves", text)
        self.assertNotIn("Simile surgery", text)
        self.assertNotIn("scoring/rubric", text)
        self.assertIn("not a quota", data["use"])

    def test_revision_gets_actual_move_definitions_and_patterns_without_tools_or_rubric(self):
        source = SKILL / "references/specialists/prose-craft.md"
        before = source.read_bytes()
        data = revision_knowledge(SKILL, "English")
        text = "\n".join(data["references"].values())
        self.assertIn("### The eight moves", text)
        self.assertIn("A competent chapter can be well built, consistent in voice, coherent in theme and still predictable.", text)
        self.assertIn("Simile surgery", text)
        self.assertIn("patterns/ai-tells-en.md", data["references"])
        self.assertNotIn("scoring/rubric", text)
        self.assertNotIn("the rubric still penalizes", text)
        self.assertNotIn('grep -o', text)
        self.assertEqual(before, source.read_bytes())

    def test_language_specific_tells_are_not_silently_english_for_every_book(self):
        for language in ("Português", "Portuguese", "pt-BR", "pt_br", "Brazilian Portuguese"):
            self.assertEqual("patterns/ai-tells-pt-br.md", language_tells(language))
            refs = revision_knowledge(SKILL, language)["references"]
            self.assertIn("patterns/ai-tells-pt-br.md", refs)
            self.assertNotIn("patterns/ai-tells-en.md", refs)
        self.assertIsNone(language_tells("Español"))
        self.assertFalse(any("ai-tells" in p for p in revision_knowledge(SKILL, "Español")["references"]))

    def test_actual_full_workflow_carries_craft_to_writers_and_keeps_readers_blind(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze(root / ".book-genesis/project.json", encoded({"host": "codex", "collaboration": "autonomous",
                "author_name": "QA", "model": "exact-test-model", "effort": "high", "idea": "A letter returns.",
                "language": "English", "autonomous_contract": {"chapters": 2, "min_words": 240, "max_words": 600, "quality_target": 8.5}}))
            freeze(root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
            packets, readers = {}, []
            def generate(call_id, packet, schema, book):
                packets[call_id] = packet
                if "turn_page" in schema["properties"]:
                    readers.append(packet)
                return fixture_response(call_id, packet, schema, book)
            options = dict(chapters=2, min_words=240, max_words=600, transport=receipt_transport(generate))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, BookWorkflow(root, COMMAND, **options).run())
            draft = json.loads(packets["wf-draft-01-1"].split("\n\n", 1)[1])
            self.assertEqual(draft_knowledge(SKILL), draft["craft_knowledge"])
            self.assertNotIn("### The eight moves", packets["wf-draft-01-1"])
            self.assertNotIn("quality_target", packets["wf-draft-01-1"])
            for key in ("wf-revision-plan-1-1", "wf-revision-1-c01-1"):
                context = json.loads(packets[key].rsplit("\n\n", 1)[1])
                self.assertEqual(revision_knowledge(SKILL, "English"), context["craft_knowledge"])
            self.assertTrue(readers)
            for packet in readers:
                self.assertNotIn("### The eight moves", packet)
                self.assertNotIn("craft_knowledge", packet)
            count = len(packets)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, BookWorkflow(root, COMMAND, **options).run())
            self.assertEqual(count, len(packets))


class ReaderEmotionContractTests(unittest.TestCase):
    def test_reader_and_comparison_schemas_expose_the_existing_validator_limit(self):
        for catalog in (None, {"chapters": [{"number": 1, "passages": [{"id": "c01p0001"}]}]},
                        {"kind": "anonymous_comparison", "sources": [{"passages": [{"id": "Ap0001"}]}]}):
            schema = reader_schema("Priya", catalog=catalog)
            fields = schema["properties"]["felt"]["properties"]
            self.assertEqual(MAX_EMOTION_LENGTH, fields["emotion"]["maxLength"])
            self.assertEqual(1, fields["emotion"]["minLength"])
            self.assertIn("felt.reason", fields["emotion"]["description"])
            self.assertNotIn("maxLength", fields["reason"])

    def test_native_claude_compaction_retains_the_emotion_constraint(self):
        compact = compact_native_schema(reader_schema("Priya"))
        emotion = compact["properties"]["felt"]["properties"]["emotion"]
        self.assertEqual(MAX_EMOTION_LENGTH, emotion["maxLength"])
        self.assertNotIn("description", emotion)


if __name__ == "__main__":
    unittest.main()
