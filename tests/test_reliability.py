from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from runner.distribution import install_suite, resolve_install_root, verify_install
from runner.filesystem import advance_phase, fill_outputs_for_demo, load_manifest, load_state_summary, scaffold_project


class ReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def project(self, phase_index=0):
        root = self.root / "book"
        scaffold_project(root, idea='An idea\nwith "quotes" and \\ paths', adapter="native", model_name="")
        for phase in load_manifest()[:phase_index]:
            fill_outputs_for_demo(root, phase)
            self.assertTrue(advance_phase(root)["ok"])
        return root

    def test_new_host_paths_and_opencode_precedence(self):
        for target, relative in (("opencode", ".config/opencode/skills"),
                                 ("antigravity", ".gemini/config/skills"),
                                 ("gemini", ".gemini/skills")):
            self.assertEqual((self.root / relative).resolve(), resolve_install_root(target, home=self.root, environ={}))
        xdg = self.root / "xdg"
        custom = self.root / "custom"
        self.assertEqual((xdg / "opencode/skills").resolve(), resolve_install_root("opencode", environ={"XDG_CONFIG_HOME": str(xdg)}))
        env = {"XDG_CONFIG_HOME": str(xdg), "OPENCODE_CONFIG_DIR": str(custom)}
        self.assertEqual((custom / "skills").resolve(), resolve_install_root("opencode", environ=env))
        self.assertEqual(self.root.resolve(), resolve_install_root("opencode", destination=self.root, environ=env))
        self.assertEqual((custom / ".gemini/skills").resolve(), resolve_install_root("gemini", environ={"GEMINI_CLI_HOME": str(custom)}))

    def test_installed_verification_detects_missing_reference_and_corrupt_record(self):
        root = self.root / "skills"
        self.assertFalse(verify_install("opencode", destination=root)["ok"])
        self.assertTrue(install_suite("opencode", destination=root)["ok"])
        self.assertTrue(verify_install("opencode", destination=root)["ok"])
        ref = root / "book-genesis/references/prompts/drafting.md"
        ref.unlink()
        self.assertFalse(verify_install("opencode", destination=root)["ok"])
        self.assertTrue(install_suite("opencode", destination=root, force=True)["ok"])
        (root / ".book-genesis-install.json").write_text('[]', encoding="utf-8")
        self.assertFalse(verify_install("opencode", destination=root)["ok"])

    def test_empty_heading_and_template_chapters_cannot_advance(self):
        root = self.project(3)
        chapter = root / "manuscript/chapters/chapter-01.md"
        state = (root / "PROJECT_STATE.yaml").read_bytes()
        for content in ("", "# Chapter 1\n", "<!-- BOOK_GENESIS_TEMPLATE -->\n"):
            chapter.write_text(content, encoding="utf-8")
            self.assertFalse(advance_phase(root)["ok"])
            self.assertEqual(state, (root / "PROJECT_STATE.yaml").read_bytes())

    def test_recorded_length_and_chapter_contract_blocks_incomplete_draft(self):
        root = self.project(3)
        fill_outputs_for_demo(root, load_manifest()[3])
        state = root / "PROJECT_STATE.yaml"
        state.write_text(state.read_text(encoding="utf-8").replace("target_floor_words: 0", "target_floor_words: 100").replace("chapter_count_planned: 0", "chapter_count_planned: 3"), encoding="utf-8")
        result = advance_phase(root)
        self.assertFalse(result["ok"])
        self.assertTrue(any("below recorded floor" in issue for issue in result["pending"]))
        self.assertIn("chapters: 2 of 3 planned", result["pending"])

    def test_jump_to_final_phase_cannot_skip_audit(self):
        root = self.project()
        state = root / "PROJECT_STATE.yaml"
        state.write_text(state.read_text(encoding="utf-8").replace('current_phase: "Phase 0: Intake"', 'current_phase: "Phase 6: Final Score"'), encoding="utf-8")
        fill_outputs_for_demo(root, load_manifest()[6])
        result = advance_phase(root)
        self.assertFalse(result["ok"])
        self.assertIn("prerequisite gate: adversarial_audit", result["pending"])

    def test_interrupted_state_commit_preserves_previous_snapshot(self):
        root = self.project()
        fill_outputs_for_demo(root, load_manifest()[0])
        state = root / "PROJECT_STATE.yaml"
        before = state.read_bytes()
        with patch("runner.filesystem.os.replace", side_effect=OSError("simulated write failure")):
            with self.assertRaises(OSError):
                advance_phase(root)
        self.assertEqual(before, state.read_bytes())
        self.assertTrue(advance_phase(root)["ok"])

    def test_pipeline_update_leaves_manuscript_status_untouched(self):
        root = self.project()
        state = root / "PROJECT_STATE.yaml"
        text = state.read_text(encoding="utf-8")
        # Reorder the manuscript section before pipeline: identical scalar names
        # must still update the intended section, independent of document order.
        start, end = text.index("manuscript:\n"), text.index("gates:\n")
        manuscript = text[start:end]
        text = text[:start] + text[end:]
        text = text.replace("pipeline:\n", manuscript + "pipeline:\n")
        state.write_text(text, encoding="utf-8")
        fill_outputs_for_demo(root, load_manifest()[0])
        self.assertTrue(advance_phase(root)["ok"])
        after = state.read_text(encoding="utf-8")
        self.assertIn(manuscript, after)
        self.assertIn('current_phase: "Phase 1: Foundation"', after)
        self.assertEqual("ready", load_state_summary(root)["status"])

    def test_installer_refuses_source_tree_overlap_without_writes(self):
        from runner.filesystem import REPO_ROOT
        for path in (REPO_ROOT, REPO_ROOT / "skills", REPO_ROOT / "skills/nested-test"):
            result = install_suite("opencode", destination=path, dry_run=True)
            self.assertFalse(result["ok"])
            self.assertIn("overlap", result["errors"][0])

    def test_multiline_idea_is_a_valid_escaped_scalar(self):
        root = self.project()
        text = (root / "PROJECT_STATE.yaml").read_text(encoding="utf-8")
        value = next(line.split(":", 1)[1].strip() for line in text.splitlines() if line.startswith("  idea:"))
        self.assertEqual('An idea\nwith "quotes" and \\ paths', json.loads(value))
