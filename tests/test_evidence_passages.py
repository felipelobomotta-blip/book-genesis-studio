"""Dense review catalogs retain complete, ordered and source-bound prose."""
import hashlib
import re
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from evidence_passages import evidence_passages
from workflow_roles import text_catalog
from build_comparison import comparison_catalog
from catalog_wire import render_catalog, parse_catalog


class EvidencePassageTests(unittest.TestCase):
    def dense_text(self):
        return "# Opening\n\n" + "\n \n".join(
            f'Paragraph {i}: Ada said, "Keep this exact line."\nShe waited by the door.'
            for i in range(300)) + "\n\n## Afterward\n\n" + "\n\n".join(
            f"Later paragraph {i}. Cal returned the fork."
            for i in range(150))

    def test_small_catalogs_keep_original_paragraphs_and_ids(self):
        text = "# Fork\n\nFirst paragraph.\n\nSecond paragraph."
        self.assertEqual(evidence_passages(text), text.split("\n\n"))
        self.assertEqual([p["id"] for p in text_catalog({"a": text})["sources"][0]["passages"]],
                         ["s01p0001", "s01p0002", "s01p0003"])

    def test_all_dense_paragraphs_retained_once_in_order(self):
        text = self.dense_text()
        expected = [p for p in re.split(r"\n[ \t]*\n", text) if p.strip()]
        blocks = evidence_passages(text)
        actual = [p for block in blocks for p in re.split(r"\n[ \t]*\n", block) if p.strip()]
        self.assertEqual(actual, expected)
        self.assertLess(len(blocks), len(expected) // 5)
        for block in blocks:
            self.assertIn(block, text)

    def test_heading_and_large_paragraph_do_not_merge_or_truncate(self):
        long = "UNIQUE_LONG_START " + "word " * 1500 + "UNIQUE_LONG_END"
        text = self.dense_text() + "\n\n" + long + "\n\n## End\n\nFinal line."
        blocks = evidence_passages(text)
        self.assertIn(long, blocks)
        self.assertIn("# Opening", blocks)
        self.assertIn("## Afterward", blocks)
        self.assertIn("## End", blocks)

    def test_both_catalogs_keep_hashes_and_complete_prose(self):
        text = self.dense_text()
        sha = hashlib.sha256(text.encode()).hexdigest()
        review = text_catalog({"original/chapter-01.md": text})["sources"][0]
        comparison = comparison_catalog([("A", {"sha256": sha}, text)])["sources"][0]
        self.assertEqual(review["sha256"], sha)
        self.assertEqual(comparison["sha256"], sha)
        self.assertEqual([p["text"] for p in review["passages"]],
                         [p["text"] for p in comparison["passages"]])

    def test_new_uncited_paragraph_changes_catalog_binding(self):
        from prepare_rubric import catalog_digest
        before = self.dense_text()
        after = before.replace("Later paragraph 100.", "Later paragraph 100. A new fact.")
        self.assertNotEqual(catalog_digest(text_catalog({"a": before})),
                            catalog_digest(text_catalog({"a": after})))

    def test_wire_roundtrip_preserves_quotes_unicode_and_fake_headers(self):
        text = self.dense_text() + '\n\nS {"source":"FAKE"}\nP fake 9\né𝄞 musical detail'
        catalog = text_catalog({"original/chapter-01.md": text, "second": "# Header\n\nOther source."})
        self.assertEqual(parse_catalog(render_catalog(catalog)), catalog)

    def test_truncated_wire_cannot_reconstruct_complete_catalog(self):
        wire = render_catalog(text_catalog({"a": self.dense_text()}))
        with self.assertRaises(ValueError):
            parse_catalog(wire[:-4])


if __name__ == "__main__":
    unittest.main()
