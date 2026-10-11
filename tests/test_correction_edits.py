"""Regressions for native correction attempts that miscopied baseline text."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from correction_edits import apply_passage_corrections, correction_schema, source_passages
from check_correction import prepare, CorrectionError
from workflow_roles import validate_shape


class CorrectionEditTests(unittest.TestCase):
    def test_explicit_group_retention_keeps_every_original_byte_without_weakening_default(self):
        original = '# One\r\n\r\n  The gate is mesh.  \r\n'
        self.assertTrue(validate_shape({"corrections": []}, correction_schema(original)))
        with self.assertRaisesRegex(ValueError, "No substantive correction"):
            apply_passage_corrections(original, [])
        self.assertFalse(validate_shape({"corrections": []}, correction_schema(original, allow_unchanged=True)))
        self.assertEqual(original, apply_passage_corrections(original, [], allow_unchanged=True))
        with self.assertRaisesRegex(ValueError, "outside the frozen chapter"):
            apply_passage_corrections(original, [{"from_passage": "p9999", "through_passage": "p9999", "after": "X"}], allow_unchanged=True)

    def test_repeated_passage_is_addressable_and_every_other_byte_is_preserved(self):
        original = '# One\r\n\r\n  —Wait.  \r\n \r\n—Wait.\r\n\r\nThe door stayed shut.\r\n'
        rows = source_passages(original)
        self.assertEqual(["# One", "—Wait.", "—Wait.", "The door stayed shut."], [r["text"] for r in rows])
        target = rows[2]
        correction = {"from_passage": target["id"], "through_passage": target["id"], "after": '“Wait.”'}
        self.assertEqual(original[:target["start"]] + '“Wait.”' + original[target["end"]:],
                         apply_passage_corrections(original, [correction]))
        self.assertFalse(validate_shape({"corrections": [correction]}, correction_schema(original)))

    def test_inclusive_range_can_fix_dialogue_without_returning_any_before_text(self):
        original = '# One\n\n—Wait.\n\n—Why?\n\nThe door stayed shut.\n'
        row = {"from_passage": "p0002", "through_passage": "p0003", "after": '“Wait.”\n\n“Why?”'}
        self.assertEqual('# One\n\n“Wait.”\n\n“Why?”\n\nThe door stayed shut.\n', apply_passage_corrections(original, [row]))

    def test_bad_ranges_noops_title_changes_and_control_characters_are_rejected(self):
        original = '# One\n\nA key.\n\nA door.\n'
        valid = {"from_passage": "p0002", "through_passage": "p0002", "after": "The key."}
        for edits in ([{**valid, "from_passage": "p9999"}],
                      [{**valid, "from_passage": "p0003"}], [valid, valid],
                      [{**valid, "after": "A key."}], [{**valid, "after": ""}],
                      [{"from_passage": "p0001", "through_passage": "p0001", "after": "# Different story"}]):
            with self.subTest(edits=edits), self.assertRaises(ValueError):
                apply_passage_corrections(original, edits)
        noop = {"from_passage": "p0003", "through_passage": "p0003", "after": "A door."}
        self.assertEqual(apply_passage_corrections(original, [valid]), apply_passage_corrections(original, [valid, noop]))
        self.assertTrue(validate_shape({"corrections": [{**valid, "after": "The\x00key."}]}, correction_schema(original)))

    def test_heading_presentation_reaches_the_independent_gate_but_retitling_cannot(self):
        original = '# Chapter Six: Blue Under Water\n\nThe key stayed with Ada.\n'
        row = {"from_passage": "p0001", "through_passage": "p0001", "after": "# Blue Under Water"}
        corrected = apply_passage_corrections(original, [row])
        self.assertEqual(original.replace('# Chapter Six: ', '# ', 1), corrected)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            accepted, candidate, canon = root / 'chapter-06.md', root / 'candidate.md', root / 'canon.md'
            accepted.write_text(original, encoding='utf-8')
            candidate.write_text(corrected, encoding='utf-8')
            canon.write_text('# Outline\n\nChapter six: Blue Under Water.\n', encoding='utf-8')
            result = prepare(accepted, candidate, [canon], [], 'Standardize the heading presentation.', root / 'review')
            self.assertTrue((root / 'review/manifest.private.json').exists())
            self.assertIsInstance(result, dict)
            candidate.write_text('# An Entirely Different Title\n\nThe key stayed with Ada.\n', encoding='utf-8')
            with self.assertRaises(CorrectionError):
                prepare(accepted, candidate, [canon], [], 'Retitle the chapter.', root / 'invalid')


if __name__ == '__main__':
    unittest.main()
