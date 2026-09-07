import json
import unittest
from runner.adapters import FakeAdapter
from runner.chapter import _select_length_cuts
from runner.chapter import clean_chapter


class PrecisionLengthTests(unittest.TestCase):
    def test_plain_or_bold_chapter_title_becomes_a_markdown_heading(self):
        for title in ("Chapter 3: The Moved Fourth", "**Chapter 3: The Moved Fourth**"):
            self.assertEqual("# Chapter 3: The Moved Fourth\n\nThe story.\n", clean_chapter(title + "\n\nThe story."))

    def setUp(self):
        self.parts = ["# Chapter 1: Keep", "Opening words stay here.", "An expendable description of the surrounding room.", "The key clue must remain.", "Some more redundant description that can safely go.", "The ending stays here."]
        self.draft = "\n\n".join(self.parts) + "\n"

    def test_model_selected_cuts_are_measured_and_keep_original_order(self):
        adapter = FakeAdapter([json.dumps({"remove_order": [2, 4]})])
        words = len(self.draft.split())
        result = _select_length_cuts(self.draft, words - 10, words - 5, adapter, "", 1)
        self.assertEqual("\n\n".join(self.parts[:2] + self.parts[3:]) + "\n", result)
        self.assertIn("The key clue", result)
        self.assertEqual(self.draft, "\n\n".join(self.parts) + "\n")

    def test_invalid_impossible_or_protected_cuts_leave_draft_intact(self):
        for payload in ({"remove_order": [0, 1, 5]}, {"remove_order": [999]}, {"remove_order": [True]}, {"remove_order": "2"}, {}, "invalid JSON"):
            with self.subTest(payload=payload):
                raw = payload if isinstance(payload, str) else json.dumps(payload)
                self.assertEqual(self.draft, _select_length_cuts(self.draft, 5, 10, FakeAdapter([raw]), "", 1))

    def test_duplicate_ids_are_never_counted_twice(self):
        self.assertEqual(self.draft, _select_length_cuts(self.draft, 5, 10, FakeAdapter(['{"remove_order":[2,2,2,2,2]}']), "", 1))

    def test_single_paragraph_is_never_truncated(self):
        adapter = FakeAdapter()
        draft = "# Chapter 1\n\nA long continuous passage. " * 2
        self.assertEqual(draft, _select_length_cuts(draft, 1, 3, adapter, "", 1))
        self.assertEqual([], adapter.calls)
