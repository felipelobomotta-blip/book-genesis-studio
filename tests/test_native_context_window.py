"""Explicit context requests remain scoped to the book's native command."""
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from launcher.autonomous import controlled_command
from launcher.cli import build_parser


class NativeContextTests(unittest.TestCase):
    def build(self, context=None, host="codex"):
        help_output = subprocess.CompletedProcess([], 0, "--ignore-user-config --ephemeral")
        base = {"argv": ["codex", "exec", "-m", "gpt-5.6-luna", "-o", "{output}", "-"],
                "timeout_seconds": 900}
        with patch("launcher.autonomous.subprocess.run", return_value=help_output), \
             patch("launcher.autonomous.codex_scoped_command", return_value=base):
            return controlled_command(["codex"], model="gpt-5.6-luna", effort="high",
                                      host=host, context_window=context)

    def test_default_preserves_native_capacity(self):
        self.assertFalse(any("context_window=" in arg for arg in self.build()["argv"]))

    def test_requested_context_and_compaction_are_scoped_to_exact_argv(self):
        command = self.build(400000)
        self.assertIn("model_context_window=400000", command["argv"])
        self.assertIn("model_auto_compact_token_limit=380000", command["argv"])
        self.assertIn("--ignore-user-config", command["argv"])
        self.assertIn("--ephemeral", command["argv"])
        self.assertEqual(command["argv"][-3:], ["-o", "{output}", "-"])

    def test_invalid_or_other_host_window_fails_before_native_dispatch(self):
        for value, host in ((True, "codex"), (100, "codex"), (1050001, "codex"), (400000, "claude")):
            with self.subTest(value=value, host=host), self.assertRaisesRegex(ValueError, "explicit native context"):
                self.build(value, host)

    def test_new_public_command_accepts_context_but_resume_cannot_change_it(self):
        parser = build_parser()
        args = parser.parse_args(["new", "book", "--autonomous", "--host", "codex", "--native-context-window", "400000"])
        self.assertEqual(args.native_context_window, 400000)
        self.assertNotIn("native_context_window", vars(parser.parse_args(["resume", "book"])))


if __name__ == "__main__":
    unittest.main()
