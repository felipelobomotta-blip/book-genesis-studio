from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.distribution import (  # noqa: E402
    BACKUP_DIRECTORY,
    INSTALL_RECORD,
    _file_digest,
    _tree_digest,
    install_suite,
    resolve_install_root,
    selected_skills,
    supported_targets,
    validate_suite,
    verify_install,
)
from runner.filesystem import load_manifest  # noqa: E402

INSTALLER = [sys.executable, str(REPO_ROOT / "runner" / "installer.py")]
BLIND_READER = "book-genesis-blind-reader.md"
AUDITOR = "book-genesis-auditor.md"


class SuiteContractTests(unittest.TestCase):
    def test_checkout_passes_the_suite_check(self) -> None:
        result = validate_suite()
        self.assertTrue(result["ok"], msg="\n".join(result["errors"]))

    def test_suite_ships_the_core_and_three_standalone_skills(self) -> None:
        self.assertEqual(
            ["book-genesis", "beta-reader", "editorial-package", "literary-agent-panel"],
            selected_skills(),
        )

    def test_pipeline_runs_the_eight_phases_in_order(self) -> None:
        self.assertEqual(
            [
                "Phase 0: Intake",
                "Phase 1: Foundation",
                "Phase 2: Architecture",
                "Phase 3: Drafting",
                "Phase 4: Adversarial Audit",
                "Phase 5: Revision Loop",
                "Phase 6: Final Score",
                "Phase 7: Editorial Package",
            ],
            [phase.label for phase in load_manifest()],
        )

    def test_supported_targets_are_the_documented_sixteen(self) -> None:
        self.assertEqual(
            {
                "antigravity", "antigravity-cli", "claude", "codex", "copilot", "cursor",
                "deepseek", "gemini", "hermes", "kimi", "openclaw", "opencode", "pi",
                "qwen", "shared", "windsurf",
            },
            set(supported_targets()),
        )

    def test_cli_verifies_suite(self) -> None:
        result = subprocess.run(INSTALLER + ["verify-suite"], capture_output=True, text=True, check=False)
        self.assertEqual(0, result.returncode, msg=result.stdout + result.stderr)
        self.assertIn("Suite check ok", result.stdout)

    def test_targets_command_lists_every_target(self) -> None:
        result = subprocess.run(INSTALLER + ["targets"], capture_output=True, text=True, check=False)
        self.assertEqual(0, result.returncode, msg=result.stderr)
        self.assertEqual(list(supported_targets()), result.stdout.split())


class InstallPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="book-genesis-distribution-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_default_paths_are_resolved_without_writing(self) -> None:
        home = self.tempdir / "home"
        expected = {
            "claude": ".claude/skills", "codex": ".codex/skills", "kimi": ".kimi-code/skills",
            "shared": ".agents/skills", "openclaw": ".openclaw/skills", "hermes": ".hermes/skills",
            "opencode": ".config/opencode/skills", "antigravity": ".gemini/config/skills",
            "antigravity-cli": ".gemini/antigravity-cli/skills", "gemini": ".gemini/skills",
            "deepseek": ".dsh/skills", "cursor": ".cursor/skills", "copilot": ".copilot/skills",
            "qwen": ".qwen/skills", "pi": ".pi/agent/skills", "windsurf": ".codeium/windsurf/skills",
        }
        for target, relative in expected.items():
            with self.subTest(target=target):
                self.assertEqual((home / relative).resolve(), resolve_install_root(target, home=home, environ={}))
        self.assertFalse(home.exists())

    def test_home_variables_and_explicit_destination(self) -> None:
        home = self.tempdir / "home"
        for target, variable, subdir in (
            ("claude", "CLAUDE_CONFIG_DIR", ""),
            ("codex", "CODEX_HOME", ""),
            ("kimi", "KIMI_CODE_HOME", ""),
            ("openclaw", "OPENCLAW_STATE_DIR", ""),
            ("hermes", "HERMES_HOME", ""),
            ("deepseek", "DSH_HOME", ""),
            ("pi", "PI_CODING_AGENT_DIR", ""),
            ("gemini", "GEMINI_CLI_HOME", ".gemini"),
        ):
            with self.subTest(target=target):
                custom = self.tempdir / f"custom {target}"
                self.assertEqual(
                    (custom / subdir / "skills").resolve(),
                    resolve_install_root(target, home=home, environ={variable: str(custom)}),
                )
                explicit = self.tempdir / "workspace skills"
                self.assertEqual(
                    explicit.resolve(),
                    resolve_install_root(target, destination=explicit, environ={variable: str(custom)}),
                )

    def test_opencode_prefers_its_own_variable_over_xdg(self) -> None:
        xdg = self.tempdir / "xdg"
        custom = self.tempdir / "custom"
        self.assertEqual((xdg / "opencode/skills").resolve(),
                         resolve_install_root("opencode", environ={"XDG_CONFIG_HOME": str(xdg)}))
        self.assertEqual((custom / "skills").resolve(), resolve_install_root(
            "opencode", environ={"XDG_CONFIG_HOME": str(xdg), "OPENCODE_CONFIG_DIR": str(custom)}))

    def test_copilot_search_paths_are_not_a_home_directory(self) -> None:
        home = self.tempdir / "home"
        self.assertEqual((home / ".copilot/skills").resolve(), resolve_install_root(
            "copilot", home=home, environ={"COPILOT_SKILLS_DIRS": "one,two"}))


class InstallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="book-genesis-install-"))
        self.home = self.tempdir / "home"

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def claude_install(self, **options):
        return install_suite("claude", home=self.home, environ={}, **options)

    def test_every_target_installs_through_the_cli_byte_for_byte(self) -> None:
        for target in supported_targets():
            with self.subTest(target=target):
                destination = self.tempdir / target / "skills with spaces"
                command = INSTALLER + ["install", target, "--dest", str(destination)]
                preview = subprocess.run(command + ["--dry-run"], capture_output=True, text=True)
                self.assertEqual(0, preview.returncode, preview.stdout + preview.stderr)
                self.assertFalse(destination.exists())
                installed = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(0, installed.returncode, installed.stdout + installed.stderr)
                verified = verify_install(target, destination=destination)
                self.assertTrue(verified["ok"], msg=str(verified["errors"]))
                for name in selected_skills():
                    source_root = REPO_ROOT / "skills" / name
                    for source in source_root.rglob("*"):
                        if source.is_file():
                            copied = destination / name / source.relative_to(source_root)
                            self.assertEqual(source.read_bytes(), copied.read_bytes(), str(copied))
                again = install_suite(target, destination=destination)
                self.assertTrue(again["ok"])
                self.assertEqual({"unchanged"}, {item["action"] for item in again["actions"]})

    def test_install_writes_exactly_the_shipped_skills(self) -> None:
        destination = self.tempdir / "skills"
        result = install_suite("codex", destination=destination)
        self.assertTrue(result["ok"], msg=str(result["errors"]))
        installed = {path.name for path in destination.iterdir() if path.is_dir() and not path.name.startswith(".")}
        self.assertEqual(set(selected_skills()), installed)
        self.assertTrue((destination / INSTALL_RECORD).is_file())

    def test_dry_run_does_not_create_destination(self) -> None:
        destination = self.tempdir / "dry-run-skills"
        result = install_suite("codex", destination=destination, dry_run=True)
        self.assertTrue(result["ok"])
        self.assertFalse(destination.exists())
        self.assertIn("install", {item["action"] for item in result["actions"]})

    def test_destination_file_fails_even_in_dry_run(self) -> None:
        destination = self.tempdir / "not-a-directory"
        destination.write_text("occupied\n", encoding="utf-8")
        result = install_suite("codex", destination=destination, dry_run=True)
        self.assertFalse(result["ok"])
        self.assertEqual(["installation destination exists and is not a directory"], result["errors"])

    def test_installer_refuses_to_overlap_the_source_tree(self) -> None:
        for path in (REPO_ROOT, REPO_ROOT / "skills", REPO_ROOT / "skills" / "nested-test"):
            with self.subTest(path=path):
                result = install_suite("opencode", destination=path, dry_run=True)
                self.assertFalse(result["ok"])
                self.assertEqual(
                    ["installation destination cannot overlap repository source skills directory"],
                    result["errors"],
                )

    def test_conflict_requires_force_and_force_backs_up_where_no_host_loads_it(self) -> None:
        destination = self.tempdir / "skills"
        install_suite("kimi", destination=destination)
        skill_file = destination / "book-genesis" / "SKILL.md"
        skill_file.write_text(skill_file.read_text(encoding="utf-8") + "\nlocal change\n", encoding="utf-8")

        blocked = install_suite("kimi", destination=destination)
        self.assertFalse(blocked["ok"])
        self.assertEqual(["book-genesis"], blocked["conflicts"])
        self.assertIn("local change", skill_file.read_text(encoding="utf-8"))

        replaced = install_suite("kimi", destination=destination, force=True)
        self.assertTrue(replaced["ok"], msg=str(replaced["errors"]))
        self.assertNotIn("local change", skill_file.read_text(encoding="utf-8"))
        backups = list((destination / BACKUP_DIRECTORY).glob("*/book-genesis/SKILL.md.bak"))
        self.assertEqual(1, len(backups))
        self.assertIn("local change", backups[0].read_text(encoding="utf-8"))
        self.assertEqual([], list((destination / BACKUP_DIRECTORY).rglob("SKILL.md")))

    def test_verify_install_catches_a_missing_reference_and_a_corrupt_record(self) -> None:
        root = self.tempdir / "skills"
        self.assertFalse(verify_install("opencode", destination=root)["ok"])
        self.assertTrue(install_suite("opencode", destination=root)["ok"])
        self.assertTrue(verify_install("opencode", destination=root)["ok"])
        (root / "book-genesis/references/prompts/drafting.md").unlink()
        self.assertIn(
            "book-genesis was changed after it was installed; compare it with this checkout before reinstalling",
            verify_install("opencode", destination=root)["errors"],
        )
        self.assertTrue(install_suite("opencode", destination=root, force=True)["ok"])
        (root / INSTALL_RECORD).write_text("[]", encoding="utf-8")
        self.assertEqual(["install record is invalid"], verify_install("opencode", destination=root)["errors"])

    def test_claude_install_puts_generated_subagents_in_the_claude_home(self) -> None:
        result = self.claude_install()
        self.assertTrue(result["ok"], msg=str(result["errors"]))
        agents = self.home / ".claude" / "agents"
        for name in (BLIND_READER, AUDITOR):
            self.assertEqual((REPO_ROOT / "agents" / name).read_bytes(), (agents / name).read_bytes())
        self.assertTrue(verify_install("claude", home=self.home, environ={})["ok"])

    def test_other_targets_get_no_subagents(self) -> None:
        result = install_suite("codex", home=self.home, environ={})
        self.assertTrue(result["ok"], msg=str(result["errors"]))
        self.assertEqual([], result["agent_actions"])
        self.assertFalse((self.home / ".codex" / "agents").exists())

    def test_custom_dest_installs_subagents_only_with_agents_dest(self) -> None:
        skills = self.tempdir / "project" / "skills"
        without = install_suite("claude", destination=skills)
        self.assertTrue(without["ok"], msg=str(without["errors"]))
        self.assertEqual([], without["agent_actions"])
        self.assertEqual(
            ["Claude Code subagents were not installed; add --agents-dest to install them next to a custom --dest"],
            without["notes"],
        )
        self.assertFalse((skills.parent / "agents").exists())

        agents = self.tempdir / "project" / "agents"
        with_agents = install_suite("claude", destination=skills, agents_destination=agents)
        self.assertTrue(with_agents["ok"], msg=str(with_agents["errors"]))
        self.assertTrue((agents / BLIND_READER).is_file())

    def test_verify_install_reports_a_deleted_subagent(self) -> None:
        self.claude_install()
        missing = self.home / ".claude" / "agents" / AUDITOR
        missing.unlink()
        self.assertEqual([f"missing agent: {missing.resolve()}"],
                         verify_install("claude", home=self.home, environ={})["errors"])

    def test_changed_subagent_blocks_install_and_force_backs_it_up(self) -> None:
        self.claude_install()
        agent = self.home / ".claude" / "agents" / BLIND_READER
        agent.write_text(agent.read_text(encoding="utf-8") + "\nmy tweak\n", encoding="utf-8")

        blocked = self.claude_install()
        self.assertFalse(blocked["ok"])
        self.assertEqual([f"agents/{BLIND_READER}"], blocked["conflicts"])

        replaced = self.claude_install(force=True)
        self.assertTrue(replaced["ok"], msg=str(replaced["errors"]))
        self.assertNotIn("my tweak", agent.read_text(encoding="utf-8"))
        backups = list((agent.parent / BACKUP_DIRECTORY).glob(f"*/{BLIND_READER}.bak"))
        self.assertEqual(1, len(backups))
        self.assertIn("my tweak", backups[0].read_text(encoding="utf-8"))

    SHIPPED_IN_5X = ("book-genesis", "beta-reader", "editorial-package", "literary-agent-panel")

    def fake_5x_install(self) -> Path:
        """Lay out what the 5.x installer left in a Claude home, with its v1 record.

        5.x shipped the same four skill names as 6.0 (with older content), plus
        skills 6.0 retires, plus V4 agents next to the skills folder.
        """
        skills = self.home / ".claude" / "skills"
        for name in self.SHIPPED_IN_5X + ("humanizer", "book-bestseller-studio"):
            folder = skills / name
            folder.mkdir(parents=True)
            (folder / "SKILL.md").write_text(f"---\nname: {name}\ndescription: 5.x text\n---\n", encoding="utf-8")
        orchestrator = self.home / ".claude" / "agents" / "book-orchestrator.md"
        orchestrator.parent.mkdir(parents=True)
        orchestrator.write_text("---\nname: book-orchestrator\ndescription: V4 for the book pipeline\n---\n", encoding="utf-8")
        recorded = {name: _tree_digest(skills / name) for name in self.SHIPPED_IN_5X + ("humanizer",)}
        recorded["book-bestseller-studio"] = "digest-before-the-author-edited-it"
        record = {
            "schema_version": 1,
            "skills": recorded,
            "legacy_claude_files": {"agents/book-orchestrator.md": _file_digest(orchestrator)},
        }
        (skills / INSTALL_RECORD).write_text(json.dumps(record), encoding="utf-8")
        return skills

    def test_upgrade_from_5x_needs_no_force_and_retires_only_unchanged_files(self) -> None:
        skills = self.fake_5x_install()

        result = self.claude_install()

        self.assertTrue(result["ok"], msg=str(result["errors"]))
        self.assertEqual(
            {name: "update" for name in self.SHIPPED_IN_5X},
            {item["skill"]: item["action"] for item in result["actions"]},
        )
        self.assertEqual(
            [("skill", "humanizer"), ("file", "agents/book-orchestrator.md")],
            [(item["kind"], item["name"]) for item in result["retirements"]],
        )
        self.assertFalse((skills / "humanizer").exists())
        self.assertFalse((self.home / ".claude" / "agents" / "book-orchestrator.md").exists())
        backup = Path(result["backups"][0])
        self.assertTrue((backup / "book-genesis" / "SKILL.md.bak").is_file())
        self.assertTrue((backup / "retired" / "humanizer" / "SKILL.md.bak").is_file())
        self.assertTrue((backup / "retired" / "agents" / "book-orchestrator.md.bak").is_file())
        self.assertTrue((skills / "book-bestseller-studio" / "SKILL.md").is_file())
        self.assertEqual(1, len(result["warnings"]))
        self.assertIn(str((skills / "book-bestseller-studio").resolve()), result["warnings"][0])
        self.assertTrue(verify_install("claude", home=self.home, environ={})["ok"])

    def test_edited_5x_skill_still_needs_force(self) -> None:
        skills = self.fake_5x_install()
        edited = skills / "editorial-package" / "SKILL.md"
        edited.write_text(edited.read_text(encoding="utf-8") + "\nmy notes\n", encoding="utf-8")

        result = self.claude_install()

        self.assertFalse(result["ok"])
        self.assertEqual(["editorial-package"], result["conflicts"])
        self.assertIn("my notes", edited.read_text(encoding="utf-8"))
        self.assertTrue((skills / "humanizer").exists(), "nothing moves when the install is refused")

    def test_dry_run_upgrade_says_what_would_be_retired_and_moves_nothing(self) -> None:
        skills = self.fake_5x_install()
        env = dict(os.environ, CLAUDE_CONFIG_DIR=str(self.home / ".claude"))

        result = subprocess.run(INSTALLER + ["install", "claude", "--dry-run"], capture_output=True, text=True, env=env)

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("would retire: humanizer", result.stdout)
        self.assertNotIn("retired:", result.stdout)
        self.assertTrue((skills / "humanizer" / "SKILL.md").is_file())

    def make_link(self, link: Path, target: Path) -> None:
        target.mkdir(parents=True, exist_ok=True)
        link.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.symlink(target, link, target_is_directory=True)
        except OSError:
            try:
                import _winapi
                _winapi.CreateJunction(str(target), str(link))
            except (ImportError, OSError) as exc:
                self.skipTest(f"cannot create a directory link here: {exc}")

    def test_a_link_in_place_of_a_skill_is_never_followed_or_replaced(self) -> None:
        skills = self.tempdir / "skills"
        outside = self.tempdir / "someone-elses-fork" / "book-genesis"
        (outside / "SKILL.md").parent.mkdir(parents=True)
        (outside / "SKILL.md").write_text("---\nname: book-genesis\ndescription: fork\n---\n", encoding="utf-8")
        self.make_link(skills / "book-genesis", outside)

        for force in (False, True):
            with self.subTest(force=force):
                result = install_suite("codex", destination=skills, force=force)
                self.assertFalse(result["ok"])
                self.assertIn(
                    f"{(skills / 'book-genesis')} is a link; the installer never replaces links, move it aside yourself",
                    result["errors"],
                )
                self.assertTrue((outside / "SKILL.md").is_file())
                self.assertEqual([], list(outside.glob("*.bak")))

    def test_failure_before_any_swap_leaves_the_previous_install_untouched(self) -> None:
        skills = self.tempdir / "project" / "skills"
        agents = self.tempdir / "project" / "agents"
        self.assertTrue(install_suite("claude", destination=skills, agents_destination=agents)["ok"])
        edited = skills / "editorial-package" / "SKILL.md"
        edited.write_text(edited.read_text(encoding="utf-8") + "\nmy notes\n", encoding="utf-8")
        blocker = self.tempdir / "blocker"
        blocker.write_text("a file where a folder should be\n", encoding="utf-8")

        with self.assertRaises(OSError):
            install_suite("claude", destination=skills, agents_destination=blocker / "agents", force=True)

        self.assertIn("my notes", edited.read_text(encoding="utf-8"))
        self.assertFalse((skills / BACKUP_DIRECTORY).exists())
        self.assertEqual([], list(skills.glob(".book-genesis-stage-*")))

    def test_a_users_own_skill_md_bak_survives_a_forced_replace(self) -> None:
        skills = self.tempdir / "skills"
        install_suite("codex", destination=skills)
        folder = skills / "beta-reader"
        (folder / "SKILL.md.bak").write_text("the author's own backup\n", encoding="utf-8")
        (folder / "SKILL.md").write_text((folder / "SKILL.md").read_text(encoding="utf-8") + "\nedit\n", encoding="utf-8")

        result = install_suite("codex", destination=skills, force=True)

        self.assertTrue(result["ok"], msg=str(result["errors"]))
        backup = Path(result["backups"][0]) / "beta-reader"
        self.assertEqual("the author's own backup\n", (backup / "SKILL.md.bak").read_text(encoding="utf-8"))
        self.assertIn("\nedit\n", (backup / "SKILL.md.bak.1").read_text(encoding="utf-8"))
        self.assertFalse((backup / "SKILL.md").exists())
        self.assertTrue((skills / "beta-reader" / "SKILL.md").is_file())

    def test_reported_backup_folders_exist(self) -> None:
        self.claude_install()
        agent = self.home / ".claude" / "agents" / AUDITOR
        agent.write_text(agent.read_text(encoding="utf-8") + "\ntweak\n", encoding="utf-8")

        result = self.claude_install(force=True)

        self.assertTrue(result["ok"], msg=str(result["errors"]))
        self.assertEqual(1, len(result["backups"]))
        self.assertTrue(Path(result["backups"][0]).is_dir())
        self.assertTrue((Path(result["backups"][0]) / f"{AUDITOR}.bak").is_file())

    def test_record_with_null_sections_is_reported_not_a_crash(self) -> None:
        skills = self.tempdir / "skills"
        install_suite("codex", destination=skills)
        (skills / INSTALL_RECORD).write_text(
            json.dumps({"schema_version": 2, "skills": {}, "agents": None}), encoding="utf-8"
        )

        self.assertIn("install record is invalid", verify_install("codex", destination=skills)["errors"])
        cli = subprocess.run(INSTALLER + ["verify-install", "codex", "--dest", str(skills)], capture_output=True, text=True)
        self.assertEqual(1, cli.returncode)
        self.assertNotIn("Traceback", cli.stdout + cli.stderr)

    def test_verify_tells_an_outdated_install_from_a_local_edit(self) -> None:
        skills = self.tempdir / "skills"
        install_suite("codex", destination=skills)
        record_path = skills / INSTALL_RECORD
        skill_file = skills / "literary-agent-panel" / "SKILL.md"
        skill_file.write_text(skill_file.read_text(encoding="utf-8") + "\nolder release\n", encoding="utf-8")
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["skills"]["literary-agent-panel"] = _tree_digest(skills / "literary-agent-panel")
        record_path.write_text(json.dumps(record), encoding="utf-8")

        self.assertEqual(
            ["installed copy of literary-agent-panel is from another version of this checkout; run install to update it"],
            verify_install("codex", destination=skills)["errors"],
        )

        skill_file.write_text(skill_file.read_text(encoding="utf-8") + "\nmy own edit\n", encoding="utf-8")
        self.assertEqual(
            ["literary-agent-panel was changed after it was installed; compare it with this checkout before reinstalling"],
            verify_install("codex", destination=skills)["errors"],
        )

    def test_agents_dest_is_noted_when_the_target_has_no_subagents(self) -> None:
        result = install_suite("codex", destination=self.tempdir / "skills", agents_destination=self.tempdir / "agents")

        self.assertTrue(result["ok"], msg=str(result["errors"]))
        self.assertEqual(["--agents-dest is only used for claude; ignored for codex"], result["notes"])
        self.assertFalse((self.tempdir / "agents").exists())

    def test_unrecorded_old_agent_is_left_in_place_with_a_warning(self) -> None:
        writer = self.home / ".claude" / "agents" / "book-writer.md"
        writer.parent.mkdir(parents=True)
        writer.write_text("---\nname: book-writer\n---\n", encoding="utf-8")

        result = self.claude_install()

        self.assertTrue(result["ok"], msg=str(result["errors"]))
        self.assertTrue(writer.is_file())
        self.assertEqual([], result["retirements"])
        self.assertEqual(1, len(result["warnings"]))
        self.assertIn(str(writer.resolve()), result["warnings"][0])

    def test_cli_failure_prints_a_message_not_a_traceback(self) -> None:
        blocker = self.tempdir / "blocker"
        blocker.write_text("a file where a folder should be\n", encoding="utf-8")

        result = subprocess.run(INSTALLER + ["install", "codex", "--dest", str(blocker / "skills")],
                                capture_output=True, text=True)

        self.assertEqual(1, result.returncode)
        self.assertIn("install failed:", result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_cli_rejects_a_relative_home_variable_by_name(self) -> None:
        env = dict(os.environ, CLAUDE_CONFIG_DIR="relative/claude")

        result = subprocess.run(INSTALLER + ["install", "claude", "--dry-run"],
                                capture_output=True, text=True, env=env)

        self.assertEqual(1, result.returncode)
        self.assertIn("CLAUDE_CONFIG_DIR must be an absolute path", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
