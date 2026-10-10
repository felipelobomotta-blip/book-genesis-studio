"""Mechanical presentation repair must never rewrite narrative prose."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from export_book import discover_chapters, word_count_receipt
from stage_chapter import stage_chapter


class StageChapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "extracted.md"

    def test_all_heading_levels_preserve_exact_title_body_encoding_and_line_endings(self):
        for level in range(1, 7):
            for newline in (b"\n", b"\r\n", b"\r"):
                for bom in (b"", b"\xef\xbb\xbf"):
                    with self.subTest(level=level, newline=newline, bom=bom):
                        body = newline + "Mara kept the café key.  \n\n## A scene\nShe left.".encode()
                        raw = bom + b"#" * level + b" Chapter: The Key" + newline + body
                        self.source.write_bytes(raw)
                        out = self.root / f"attempt-{level}-{newline.hex()}-{len(bom)}"
                        result = stage_chapter(self.source, out)
                        expected = bom + b"# Chapter: The Key" + newline + body
                        self.assertEqual(expected, (out / "chapter.md").read_bytes())
                        self.assertEqual(raw, self.source.read_bytes())
                        self.assertEqual(raw, (out / "source.md").read_bytes())
                        self.assertEqual(hashlib.sha256(body).hexdigest(), result["body_sha256"])
                        self.assertEqual(hashlib.sha256(expected).hexdigest(), result["staged_sha256"])
                        self.assertEqual("none" if level == 1 else "initial_markdown_heading_to_h1", result["transform"])

    def test_ambiguous_or_invalid_inputs_fail_without_output(self):
        for i, raw in enumerate((b"Prose without a heading.", b"\n## Late title\nProse.", b"## \nProse.",
                                 b"####### Too deep\nProse.", b"##\tTabbed\nProse.", b"## Title\n\n",
                                 b"## Title\n\n<!-- Only hidden text. -->", b"## Title\n# Another chapter\nProse.",
                                 b"## Title\nBroken\x00body.", b"## Title\n\xff")):
            with self.subTest(raw=raw):
                self.source.write_bytes(raw)
                out = self.root / f"bad-{i}"
                with self.assertRaises((ValueError, UnicodeError)):
                    stage_chapter(self.source, out)
                self.assertFalse(out.exists())
                self.assertEqual(raw, self.source.read_bytes())

    def test_existing_attempt_is_never_overwritten(self):
        self.source.write_bytes(b"## First\n\nOriginal prose.\n")
        out = self.root / "attempt"
        stage_chapter(self.source, out)
        saved = {p.name: p.read_bytes() for p in out.iterdir()}
        self.source.write_bytes(b"## Second\n\nDifferent prose.\n")
        with self.assertRaises(FileExistsError):
            stage_chapter(self.source, out)
        self.assertEqual(saved, {p.name: p.read_bytes() for p in out.iterdir()})

    def test_actual_export_parser_accepts_staged_structure_and_same_visible_word_count(self):
        self.source.write_text("## Chapter\n\nMara kept the key.\n\n<!-- A private note -->\n\nShe left.\n", encoding="utf-8")
        result = stage_chapter(self.source, self.root / "attempt")
        canonical = self.root / "chapters"
        canonical.mkdir()
        (canonical / "chapter-01.md").write_bytes((self.root / "attempt/chapter.md").read_bytes())
        chapters = discover_chapters(canonical)
        self.assertEqual(6, word_count_receipt(chapters)["total"])
        self.assertEqual(6, result["visible_prose_words"])
        self.assertEqual("format_only_not_editorial_acceptance", result["scope"])

    def test_cli_exposes_transformation_and_original_source_hash(self):
        self.source.write_bytes(b"## Chapter\n\nMara kept the key.\n")
        run = subprocess.run([sys.executable, str(ROOT / "skills/book-genesis/scripts/stage_chapter.py"),
                              "--source", str(self.source), "--output-dir", str(self.root / "attempt")],
                             capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(0, run.returncode, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), result["source_sha256"])
        self.assertNotEqual(result["source_sha256"], result["staged_sha256"])
        self.assertTrue(result["body_unchanged"])
