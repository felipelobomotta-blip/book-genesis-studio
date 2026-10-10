"""The product, not a model, selects Codex's headless transport syntax."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from launcher import cli, native
from run_host_call import command_from_launch


class ScopedCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.book = Path(self.temp.name)
        self.launches = self.book / ".book-genesis/launches"
        self.launches.mkdir(parents=True)
        self.packet = self.book / "packet.txt"
        self.packet.write_text("Read this packet only.", encoding="utf-8")
        self.fixture = self.book / "fake_native.py"
        self.fixture.write_text(
            "import sys, json\nfrom pathlib import Path\n"
            "args = sys.argv[1:]\n"
            "assert 'exec' in args, 'interactive mode cannot read piped input'\n"
            "assert args.index('-a') < args.index('exec'), 'approval flag belongs to parent parser'\n"
            "assert '--no-alt-screen' not in args and '--ignore-user-config' not in args\n"
            "assert '--skip-git-repo-check' in args\n"
            "assert args[args.index('--sandbox')+1] == 'read-only'\n"
            "assert sys.stdin.read() == 'Read this packet only.'\n"
            "schema = json.loads(Path(args[args.index('--output-schema')+1]).read_text()) if '--output-schema' in args else None\n"
            "Path(args[args.index('-o')+1]).write_text(json.dumps({'model':args[args.index('-m')+1], 'schema':schema}), encoding='utf-8')\n",
            encoding="utf-8")
        self.prefix = [sys.executable, str(self.fixture)]
        self.recipe = native.codex_scoped_command(self.prefix, model="test-model", effort="high")
        self.record = {"host":"codex", "model":"test-model", "effort":"high", "scoped_command":self.recipe}
        self.receipt_path = self.launches / "launch.json"
        self.save_record()

    def save_record(self):
        self.receipt_path.write_text(json.dumps(self.record), encoding="utf-8")

    def run_guard(self, *extra):
        return subprocess.run([sys.executable, str(ROOT / "skills/book-genesis/scripts/run_host_call.py"),
                               "--book-dir", str(self.book), "--call-id", "test-role", "--packet", str(self.packet),
                               "--launch-receipt", str(self.receipt_path), *extra],
                              capture_output=True, text=True, encoding="utf-8")

    def test_actual_child_uses_headless_mode_and_captures_output_without_tty(self):
        run = self.run_guard("--timeout-seconds", "10")
        self.assertEqual(0, run.returncode, run.stdout + run.stderr)
        response = json.loads((self.book / "work/host-calls/test-role/response").read_text())
        self.assertEqual({"model":"test-model", "schema":None}, response)

    def test_actual_child_receives_schema_without_mutating_saved_recipe(self):
        schema = self.book / "schema.json"
        schema.write_text('{"type":"object"}', encoding="utf-8")
        before = self.receipt_path.read_bytes()
        run = self.run_guard("--output-schema", str(schema), "--timeout-seconds", "10")
        self.assertEqual(0, run.returncode, run.stdout + run.stderr)
        response = json.loads((self.book / "work/host-calls/test-role/response").read_text())
        self.assertEqual({"type":"object"}, response["schema"])
        self.assertEqual(before, self.receipt_path.read_bytes())

    def test_old_or_interactive_recipe_and_invalid_schema_are_rejected_before_spawn(self):
        for record in ({"host":"codex"}, {"host":"claude", "scoped_command":self.recipe},
                       {"host":"codex", "scoped_command":{"argv":self.prefix+["--no-alt-screen"]}}):
            self.record = record
            self.save_record()
            with self.assertRaises(ValueError):
                command_from_launch(self.book, self.receipt_path)
        self.record = {"host":"codex", "scoped_command":self.recipe}
        self.save_record()
        for content in ("[]", "invalid json"):
            schema = self.book / "bad.json"
            schema.write_text(content)
            with self.assertRaises(ValueError):
                command_from_launch(self.book, self.receipt_path, output_schema=schema)
        with self.assertRaises(ValueError):
            command_from_launch(self.book, self.receipt_path, output_schema=self.book.parent / "outside.json")
        with self.assertRaises(ValueError):
            command_from_launch(self.book, self.book / "not-a-launch.json")
        self.assertFalse((self.book / "work/host-calls").exists())

    def test_omitted_selection_preserves_native_defaults_and_timeout_validation(self):
        recipe = native.codex_scoped_command(self.prefix, model=None, effort=None)
        self.assertNotIn("-m", recipe["argv"])
        self.assertNotIn("-c", recipe["argv"])
        for timeout in (0, -1, float("inf"), float("nan")):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                command_from_launch(self.book, self.receipt_path, timeout_seconds=timeout)

    def test_launcher_records_same_resolved_prefix_and_explicit_model_effort(self):
        config = {"host":"codex", "language":"English", "author_name":"QA", "collaboration":"autonomous"}
        captured = []

        def run(argv, *, cwd, on_start, env):
            on_start(543210)
            paths = [p for p in self.launches.glob("*.json") if p != self.receipt_path]
            self.assertEqual(1, len(paths))
            captured.append(json.loads(paths[0].read_text()))
            return 0

        with patch.object(cli, "_has_terminal", return_value=True), patch.object(native, "find_native", return_value=self.prefix), \
             patch.object(cli, "run_attached", side_effect=run), redirect_stdout(io.StringIO()):
            self.assertEqual(0, cli.launch_project(self.book, config, host="codex", model="selected", effort="high", resumed=True))
        record = captured[0]
        scoped = record["scoped_command"]["argv"]
        self.assertEqual(self.prefix, scoped[:2])
        self.assertEqual("selected", scoped[scoped.index("-m")+1])
        self.assertEqual('model_reasoning_effort="high"', scoped[scoped.index("-c")+1])
        self.assertIn("exec", scoped)
        self.assertNotIn("exec", record["native_command"])
