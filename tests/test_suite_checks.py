"""Checks that keep the shipped skills self-contained and the installer honest.

These tests build tiny fixture folders, so they do not depend on the current
content of skills/.
"""

from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.agents import AGENT_SPECS, agent_drift, render_agents  # noqa: E402
from runner.distribution import (  # noqa: E402
    find_skill_problems,
    load_distribution_manifest,
    read_frontmatter,
    resolve_install_root,
    supported_targets,
)


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


SKILL_HEAD = "---\nname: core\ndescription: Use when testing.\n---\n\n"


class SkillProblemTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="bg-checks-"))
        self.skill = self.root / "core"

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_missing_reference_path_is_reported_with_its_file(self) -> None:
        write(self.skill / "references/present.md", "# Present\n")
        write(self.skill / "SKILL.md", SKILL_HEAD + "Read `references/present.md` then `references/absent.md`.\n")

        problems = find_skill_problems(self.skill, retired_names=[])

        self.assertEqual(["core/SKILL.md: missing file references/absent.md"], problems)

    def test_reference_files_are_checked_too(self) -> None:
        write(self.skill / "SKILL.md", SKILL_HEAD + "Load `references/a.md`.\n")
        write(self.skill / "references/a.md", "See references/b.yaml for the schema.\n")

        problems = find_skill_problems(self.skill, retired_names=[])

        self.assertEqual(["core/references/a.md: missing file references/b.yaml"], problems)

    def test_reference_at_the_end_of_a_sentence_is_still_checked(self) -> None:
        write(self.skill / "SKILL.md", SKILL_HEAD + "The last step reads references/gone.md.\n")

        self.assertEqual(
            ["core/SKILL.md: missing file references/gone.md"],
            find_skill_problems(self.skill, retired_names=[]),
        )

    def test_retired_skill_names_used_as_skills_are_reported(self) -> None:
        write(self.skill / "SKILL.md", SKILL_HEAD + "Use `humanizer` after drafting, or run /book-genesis-full.\n")

        problems = find_skill_problems(self.skill, retired_names=["humanizer", "book-genesis-full"])

        self.assertEqual(
            [
                "core/SKILL.md: names retired skill humanizer",
                "core/SKILL.md: names retired skill book-genesis-full",
            ],
            problems,
        )

    def test_codex_dollar_mention_of_a_retired_skill_is_reported(self) -> None:
        write(self.skill / "SKILL.md", SKILL_HEAD + "Then use $humanizer on the draft.\n")

        self.assertEqual(
            ["core/SKILL.md: names retired skill humanizer"],
            find_skill_problems(self.skill, retired_names=["humanizer"]),
        )

    def test_reference_file_named_like_a_retired_skill_is_not_a_skill_call(self) -> None:
        write(self.skill / "references/specialists/prose-craft.md", "# Prose craft\n")
        write(self.skill / "SKILL.md", SKILL_HEAD + "Load `references/specialists/prose-craft.md`.\n")

        self.assertEqual([], find_skill_problems(self.skill, retired_names=["prose-craft"]))

    def test_paths_outside_the_skill_are_reported(self) -> None:
        write(
            self.skill / "SKILL.md",
            SKILL_HEAD
            + "Read skills/book-editor/SKILL.md and knowledge/bestseller-dna.md.\n"
            + "Run python ~/Desktop/books/prose-audit.py and python runner/cli.py.\n",
        )

        problems = find_skill_problems(self.skill, retired_names=[])

        self.assertEqual(
            [
                "core/SKILL.md: path outside the skill: skills/book-editor/",
                "core/SKILL.md: path outside the skill: knowledge/bestseller-dna.md",
                "core/SKILL.md: path outside the skill: ~/Desktop",
                "core/SKILL.md: path outside the skill: runner/cli.py",
            ],
            problems,
        )

    def test_home_and_parent_paths_outside_the_skill_are_reported(self) -> None:
        write(
            self.skill / "SKILL.md",
            SKILL_HEAD
            + "Read ~/.claude/knowledge/bestseller-dna.md, then ../book-genesis/SKILL.md,\n"
            + "then ~/.claude/skills/humanizer/SKILL.md.\n",
        )

        problems = find_skill_problems(self.skill, retired_names=["humanizer"])

        self.assertEqual(
            [
                "core/SKILL.md: names retired skill humanizer",
                "core/SKILL.md: path outside the skill: skills/humanizer/",
                "core/SKILL.md: path outside the skill: knowledge/bestseller-dna.md",
                "core/SKILL.md: path outside the skill: ../",
            ],
            problems,
        )

    def test_urls_templates_and_plain_words_are_not_flagged(self) -> None:
        write(
            self.skill / "SKILL.md",
            SKILL_HEAD
            + "See https://example.com/docs/references/api.json and `references/chapter.md.tmpl`.\n"
            + "Trust genre knowledge/intuition less than comps.\n",
        )

        self.assertEqual([], find_skill_problems(self.skill, retired_names=["humanizer"]))


class FrontmatterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="bg-frontmatter-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_plain_wrapped_description_is_joined(self) -> None:
        path = write(
            self.root / "SKILL.md",
            "---\nname: wrapped\ndescription:\n  Use when the text is long so the\n  author wrapped it.\n---\nBody\n",
        )

        self.assertEqual(
            {"name": "wrapped", "description": "Use when the text is long so the author wrapped it."},
            read_frontmatter(path),
        )

    def test_plain_scalar_continued_on_the_next_line_is_joined(self) -> None:
        path = write(
            self.root / "SKILL.md",
            "---\nname: long\ndescription: Use when the first line is long\n  and the rest wraps here.\n---\n",
        )

        self.assertEqual(
            "Use when the first line is long and the rest wraps here.",
            read_frontmatter(path)["description"],
        )

    def test_block_scalar_description_is_joined(self) -> None:
        path = write(self.root / "SKILL.md", "---\nname: block\ndescription: |\n  First line.\n  Second line.\n---\n")

        self.assertEqual("First line. Second line.", read_frontmatter(path)["description"])

    def test_blank_line_inside_a_block_scalar_keeps_the_block(self) -> None:
        path = write(
            self.root / "SKILL.md",
            "---\nname: block\ndescription: |\n  First paragraph.\n\n  Second paragraph.\n---\n",
        )

        self.assertEqual("First paragraph. Second paragraph.", read_frontmatter(path)["description"])

    def test_byte_order_mark_is_ignored(self) -> None:
        path = self.root / "SKILL.md"
        path.write_bytes("\ufeff---\nname: bom\ndescription: Use when saved by Notepad.\n---\n".encode("utf-8"))

        self.assertEqual("bom", read_frontmatter(path)["name"])

    def test_unquoted_colon_in_a_value_is_rejected_because_yaml_hosts_reject_it(self) -> None:
        path = write(self.root / "SKILL.md", "---\nname: colon\ndescription: Use when: writing a book\n---\n")

        with self.assertRaisesRegex(ValueError, "quote the value of description"):
            read_frontmatter(path)

    def test_quoted_colon_is_accepted(self) -> None:
        path = write(self.root / "SKILL.md", '---\nname: colon\ndescription: "Use when: writing a book"\n---\n')

        self.assertEqual("Use when: writing a book", read_frontmatter(path)["description"])

    def test_unterminated_frontmatter_raises_a_named_error(self) -> None:
        path = write(self.root / "SKILL.md", "---\nname: open\ndescription: never closed\n")

        with self.assertRaisesRegex(ValueError, "frontmatter is not closed"):
            read_frontmatter(path)


class HomeVariableTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="bg-home-")) / "home"

    def tearDown(self) -> None:
        shutil.rmtree(self.home.parent, ignore_errors=True)

    def targets_with_home_variable(self) -> dict[str, str]:
        targets = load_distribution_manifest()["targets"]
        return {name: spec["home_env"] for name, spec in targets.items() if spec.get("home_env")}

    def test_blank_home_variable_falls_back_to_the_default_for_every_target(self) -> None:
        variables = self.targets_with_home_variable()
        self.assertIn("claude", variables)
        for target, variable in variables.items():
            with self.subTest(target=target):
                expected = resolve_install_root(target, home=self.home, environ={})
                for blank in ("", "   ", "\t"):
                    self.assertEqual(
                        expected,
                        resolve_install_root(target, home=self.home, environ={variable: blank}),
                    )

    def test_relative_home_variable_is_rejected_by_name(self) -> None:
        for target, variable in self.targets_with_home_variable().items():
            with self.subTest(target=target):
                with self.assertRaisesRegex(ValueError, variable):
                    resolve_install_root(target, home=self.home, environ={variable: "relative/dir"})

    def test_every_target_resolves_inside_the_given_home(self) -> None:
        for target in supported_targets():
            with self.subTest(target=target):
                root = resolve_install_root(target, home=self.home, environ={})
                self.assertTrue(root.is_relative_to(self.home.resolve()), root)


class GeneratedAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Path(tempfile.mkdtemp(prefix="bg-agents-"))
        self.roles = self.repo / "skills/book-genesis/references/roles"
        for spec in AGENT_SPECS:
            write(self.roles / spec.role_file, f"# {spec.name}\n\nRole body for {spec.name}.\n")

    def tearDown(self) -> None:
        shutil.rmtree(self.repo, ignore_errors=True)

    def test_each_agent_carries_its_role_file_and_tool_limits(self) -> None:
        rendered = render_agents(self.roles)

        self.assertEqual({spec.agent_file for spec in AGENT_SPECS}, set(rendered))
        for spec in AGENT_SPECS:
            text = rendered[spec.agent_file]
            self.assertTrue(text.startswith(f"---\nname: {spec.name}\n"), text[:80])
            self.assertIn(f"\ntools: {spec.tools}\n", text)
            self.assertIn(f"Role body for {spec.name}.", text)
            self.assertIn(f"references/roles/{spec.role_file}", text)

    def test_committed_agents_must_match_their_role_files(self) -> None:
        agents_dir = self.repo / "agents"
        for name, text in render_agents(self.roles).items():
            write(agents_dir / name, text)
        self.assertEqual([], agent_drift(self.repo))

        stale = AGENT_SPECS[0]
        write(self.roles / stale.role_file, "# Changed\n\nNew instructions.\n")

        self.assertEqual(
            [f"agents/{stale.agent_file} is out of date; run: python runner/installer.py generate-agents"],
            agent_drift(self.repo),
        )

    def test_unknown_agent_files_are_reported(self) -> None:
        agents_dir = self.repo / "agents"
        for name, text in render_agents(self.roles).items():
            write(agents_dir / name, text)
        write(agents_dir / "book-orchestrator.md", "---\nname: book-orchestrator\n---\n")

        self.assertEqual(
            ["agents/book-orchestrator.md is not generated from a role file; remove it or add a role"],
            agent_drift(self.repo),
        )


if __name__ == "__main__":
    unittest.main()
