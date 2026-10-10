from contextlib import redirect_stdout, redirect_stderr
import _thread
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from launcher import cli, native
from runner.distribution import verify_install


# A stand-in for the native CLI: a real child process, so lifecycle tests see
# real exit codes, real PIDs and a real descendant tree.
NATIVE_FIXTURE = r'''
import json, os, subprocess, sys, time
mode, workdir = sys.argv[1], sys.argv[2]
if mode == "exit":
    sys.exit(int(sys.argv[3]))
if mode == "check-lock":
    lock = json.load(open(os.path.join(workdir, ".book-genesis", "launcher.lock"), encoding="utf-8"))
    sys.exit(0 if lock.get("native_pid") == os.getpid() else 17)
if mode == "check-effort":
    expected = sys.argv[3]
    sys.exit(0 if os.environ.get("CLAUDE_CODE_EFFORT_LEVEL") == expected and os.environ.get("BOOK_GENESIS_TEST_AUTH_BOUNDARY") == "inherited" else 18)
if mode in {"tree", "orphan"}:
    grandchild = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
    with open(sys.argv[3] + ".tmp", "w", encoding="utf-8") as handle:
        json.dump({"child": os.getpid(), "grandchild": grandchild.pid}, handle)
    os.replace(sys.argv[3] + ".tmp", sys.argv[3])
    if mode == "orphan":
        sys.exit(int(sys.argv[4]))
    time.sleep(120)
'''


def pid_running(pid):
    if os.name == "nt":
        import ctypes
        kernel = ctypes.windll.kernel32
        handle = kernel.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = ctypes.c_ulong()
        try:
            kernel.GetExitCodeProcess(handle, ctypes.byref(code))
        finally:
            kernel.CloseHandle(handle)
        return code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def wait_until_gone(pid, seconds=5.0):
    deadline = time.monotonic() + seconds
    while pid_running(pid) and time.monotonic() < deadline:
        time.sleep(0.05)
    return not pid_running(pid)


def interrupt_when_file_exists(path, seconds=20.0):
    def watch():
        deadline = time.monotonic() + seconds
        while not path.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        _thread.interrupt_main()
    thread = threading.Thread(target=watch, daemon=True)
    thread.start()
    return thread


class NativeAdapterTests(unittest.TestCase):
    def test_codex_auth_uses_native_status_and_does_not_expose_pii(self):
        commands = []

        def run(argv, **kwargs):
            commands.append(argv)
            return subprocess.CompletedProcess(argv, 0, "0.156.1" if argv[-1] == "--version" else "", "" if argv[-1] == "--version" else "Logged in using ChatGPT\n")

        with patch.object(native, "find_native", return_value=["native-codex"]), patch.object(native.subprocess, "run", side_effect=run):
            result = native.inspect_native("codex")
        self.assertEqual("signed_in", result["status"])
        self.assertEqual("ChatGPT plan", result["account"])
        self.assertEqual([["native-codex", "--version"], ["native-codex", "login", "status"]], commands)

    def test_status_failure_is_an_error_not_signed_out(self):
        responses = [subprocess.CompletedProcess([], 0, "1.0", ""), subprocess.CompletedProcess([], 1, "", "Permission denied")]
        with patch.object(native, "find_native", return_value=["codex"]), patch.object(native.subprocess, "run", side_effect=responses):
            result = native.inspect_native("codex")
        self.assertEqual("error", result["status"])
        self.assertNotIn("account", result)

    def test_codex_signed_out_requires_the_native_signed_out_line(self):
        responses = [subprocess.CompletedProcess([], 0, "1.0", ""), subprocess.CompletedProcess([], 1, "Not logged in\n", "")]
        with patch.object(native, "find_native", return_value=["codex"]), patch.object(native.subprocess, "run", side_effect=responses):
            self.assertEqual("signed_out", native.inspect_native("codex")["status"])

    def test_claude_account_status_is_reduced_to_billing_category(self):
        raw = {"loggedIn": True, "authMethod": "claude.ai", "email": "private@example.com", "orgId": "private-org", "accessToken": "do-not-save"}
        responses = [subprocess.CompletedProcess([], 0, "2.1.300", ""), subprocess.CompletedProcess([], 0, json.dumps(raw), "")]
        with patch.object(native, "find_native", return_value=["claude"]), patch.object(native.subprocess, "run", side_effect=responses):
            result = native.inspect_native("claude")
        self.assertEqual("Claude plan", result["account"])
        serialized = json.dumps(result)
        for secret in ("private@example.com", "private-org", "do-not-save"):
            self.assertNotIn(secret, serialized)

    def test_claude_invalid_status_is_an_error_not_an_empty_account(self):
        responses = [subprocess.CompletedProcess([], 0, "2.1", ""), subprocess.CompletedProcess([], 0, "not-json", "")]
        with patch.object(native, "find_native", return_value=["claude"]), patch.object(native.subprocess, "run", side_effect=responses):
            self.assertEqual("error", native.inspect_native("claude")["status"])

    def test_native_argv_preserves_model_effort_and_real_permissions(self):
        root = Path("book folder").resolve()
        prompt = "Read the real skill; $(do-not-run) & quoted text"
        with patch.object(native, "find_native", return_value=["native"]):
            codex = native.session_argv("codex", root, prompt, model="gpt-5.6-luna", effort="high")
            claude = native.session_argv("claude", root, prompt, model="opus", effort="medium")
        self.assertEqual(["--", prompt], codex[-2:])
        self.assertEqual(["--", prompt], claude[-2:])
        self.assertIn('model_reasoning_effort="high"', codex)
        self.assertEqual("workspace-write", codex[codex.index("-s") + 1])
        self.assertEqual("on-request", codex[codex.index("-a") + 1])
        self.assertEqual("opus", claude[claude.index("--model") + 1])
        self.assertEqual("medium", claude[claude.index("--effort") + 1])
        self.assertEqual({"env": {"CLAUDE_CODE_EFFORT_LEVEL": "medium"}}, json.loads(claude[claude.index("--settings") + 1]))
        for flag in ("--bare", "--print", "--dangerously-skip-permissions", "--fallback-model", "--permission-mode"):
            self.assertNotIn(flag, claude)
        for flag in ("danger-full-access", "--dangerously-bypass-approvals-and-sandbox", "--approve-for-me", "never", "exec"):
            self.assertNotIn(flag, codex[:-1])

    def test_omitted_model_does_not_create_a_hidden_model_override(self):
        with patch.object(native, "find_native", return_value=["native"]):
            argv = native.session_argv("codex", Path("."), "start", model=None, effort=None)
            claude = native.session_argv("claude", Path("."), "start", model=None, effort=None)
        self.assertNotIn("-m", argv)
        self.assertNotIn("-c", argv)
        self.assertEqual(["native", "--", "start"], claude)

    def test_native_login_is_a_direct_official_command(self):
        with patch.object(native, "find_native", return_value=["native"]):
            self.assertEqual(["native", "login"], native.login_argv("codex"))
            self.assertEqual(["native", "auth", "login"], native.login_argv("claude"))

    def test_missing_native_cli_is_reported_without_a_shell_fallback(self):
        empty = Path(tempfile.mkdtemp(prefix="bg-empty-path-"))
        try:
            with patch.dict("os.environ", {"PATH": str(empty)}):
                with self.assertRaisesRegex(ValueError, "not on PATH"):
                    native.find_native("claude")
                self.assertEqual("unavailable", native.inspect_native("codex")["status"])
        finally:
            shutil.rmtree(empty, ignore_errors=True)

    def test_attached_process_reuses_core_shutdown_and_preserves_environment(self):
        code = "import os; assert os.environ.get('BOOK_GENESIS_TEST_AUTH_BOUNDARY') == 'inherited'; print('native fixture done')"
        with patch.dict("os.environ", {"BOOK_GENESIS_TEST_AUTH_BOUNDARY": "inherited"}):
            self.assertEqual(0, native.run_attached([sys.executable, "-c", code]))

    def test_interrupt_stops_the_whole_native_tree_while_it_runs(self):
        temp = Path(tempfile.mkdtemp(prefix="bg-tree-"))
        try:
            fixture = temp / "native.py"
            fixture.write_text(NATIVE_FIXTURE, encoding="utf-8")
            pids = temp / "pids.json"
            interrupt_when_file_exists(pids)
            started = time.monotonic()
            with self.assertRaises(KeyboardInterrupt):
                native.run_attached([sys.executable, str(fixture), "tree", str(temp), str(pids)])
            self.assertLess(time.monotonic() - started, 30)
            tree = json.loads(pids.read_text(encoding="utf-8"))
            self.assertTrue(wait_until_gone(tree["child"]), "native child survived interruption")
            self.assertTrue(wait_until_gone(tree["grandchild"]), "native descendant survived interruption")
        finally:
            shutil.rmtree(temp, ignore_errors=True)


class LauncherProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="book-genesis-launcher-"))
        self.project = self.temp / "book with spaces"
        self.fixture = self.temp / "native fixture.py"
        self.fixture.write_text(NATIVE_FIXTURE, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(cli._install_path(self.temp), ignore_errors=True)

    def prepare(self, **kwargs):
        project = kwargs.pop("project", self.project)
        return cli.prepare_project(project, host=kwargs.pop("host", "codex"), idea="A clock keeps the names of trains that never arrived.", **kwargs)

    def launch(self, config, argv, *, project=None, host="codex", effort=None):
        """Run launch_project against a real child process standing in for the native CLI."""
        with patch.object(cli, "_has_terminal", return_value=True), patch.object(cli, "session_argv", return_value=argv):
            with redirect_stdout(io.StringIO()):
                return cli.launch_project(project or self.project, config, host=host, model=None, effort=effort, resumed=False)

    def receipts(self, project=None):
        folder = cli._install_path((project or self.project) / ".book-genesis/launches")
        return [json.loads(path.read_text(encoding="utf-8")) for path in folder.glob("*.json")]

    def test_preparation_reuses_and_verifies_the_existing_core(self):
        self.prepare()
        self.assertTrue(verify_install("codex", destination=self.project / cli.SKILLS)["ok"])
        source = REPO_ROOT / "skills/book-genesis/references/pipeline/manifest.yaml"
        installed = self.project / cli.SKILLS / "book-genesis/references/pipeline/manifest.yaml"
        self.assertEqual(source.read_bytes(), installed.read_bytes())
        self.assertFalse((self.project / "PROJECT_STATE.yaml").exists())
        self.assertFalse((self.project / "manuscript").exists())

    def test_new_refuses_to_overwrite_an_existing_manuscript(self):
        self.project.mkdir()
        manuscript = self.project / "manuscript.md"
        manuscript.write_text("Keep this book.", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "must be empty"):
            self.prepare()
        self.assertEqual("Keep this book.", manuscript.read_text(encoding="utf-8"))
        self.assertFalse((self.project / ".book-genesis").exists())

    def test_new_refuses_a_prepared_project_and_keeps_its_record(self):
        self.prepare()
        record = (self.project / cli.CONFIG).read_bytes()
        with self.assertRaisesRegex(ValueError, "must be empty"):
            self.prepare(host="claude")
        self.assertEqual(record, (self.project / cli.CONFIG).read_bytes())

    def test_failed_preparation_leaves_no_half_prepared_project(self):
        failure = {"ok": False, "errors": ["simulated verification failure"]}
        with patch.object(cli, "verify_install", return_value=failure):
            with self.assertRaisesRegex(ValueError, "simulated"):
                self.prepare(host="claude")
        self.assertFalse(self.project.exists())
        self.project.mkdir()
        with patch.object(cli, "verify_install", return_value=failure):
            with self.assertRaisesRegex(ValueError, "simulated"):
                self.prepare(host="claude")
        self.assertEqual([], list(self.project.iterdir()))
        self.prepare(host="claude")
        self.assertEqual("claude", cli.read_project(self.project)["host"])

    def test_preparation_claim_rejects_another_preparer_before_any_copy(self):
        actual_install = cli.install_suite
        outcomes = []

        def overlapping_install(*args, **kwargs):
            # A second process can arrive after the first empty-folder check,
            # before any installer has written files. It must not overwrite
            # the first attempt or make its rollback delete the other one.
            with patch.object(cli, "install_suite") as second_install:
                with self.assertRaisesRegex(ValueError, "must be empty|already owns"):
                    self.prepare(host="claude")
                second_install.assert_not_called()
            outcomes.append("second preparation refused")
            return actual_install(*args, **kwargs)

        with patch.object(cli, "install_suite", side_effect=overlapping_install):
            self.prepare()
        self.assertEqual(["second preparation refused"], outcomes)
        self.assertEqual("codex", cli.read_project(self.project)["host"])

    def test_failed_codex_preparation_preserves_unrelated_new_files(self):
        external = self.project / ".claude" / "author-note.txt"

        def fail_verification(*args, **kwargs):
            external.parent.mkdir()
            external.write_text("This was added by another session.", encoding="utf-8")
            return {"ok": False, "errors": ["verification failed"]}

        with patch.object(cli, "verify_install", side_effect=fail_verification):
            with self.assertRaisesRegex(ValueError, "verification failed"):
                self.prepare()
        self.assertEqual("This was added by another session.", external.read_text(encoding="utf-8"))
        self.assertFalse((self.project / ".book-genesis").exists())

    def test_resume_rejects_tampered_skill_without_reinstalling(self):
        self.prepare()
        skill = self.project / cli.SKILLS / "book-genesis/SKILL.md"
        skill.write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "no automatic upgrade"):
            cli.read_project(self.project)
        self.assertEqual("changed", skill.read_text(encoding="utf-8"))

    def test_resume_rejects_a_changed_claude_agent(self):
        self.prepare(host="claude")
        agent = self.project / ".claude/agents/book-genesis-blind-reader.md"
        agent.write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "no automatic upgrade"):
            cli.read_project(self.project)
        self.assertEqual("changed", agent.read_text(encoding="utf-8"))

    def test_copied_claude_project_is_not_verified_against_the_original_agents(self):
        self.prepare(host="claude")
        copy = self.temp / "copied book"
        shutil.copytree(self.project, copy)
        self.assertEqual("claude", cli.read_project(self.project)["host"])
        with self.assertRaisesRegex(ValueError, "another folder"):
            cli.read_project(copy)

    def test_resuming_does_not_reset_pending_author_checkpoint(self):
        config = self.prepare(autonomous=True)
        state = self.project / "PROJECT_STATE.yaml"
        saved = "collaboration:\n  waiting_for_author: true\n  pending_checkpoint: opening\n"
        state.write_text(saved, encoding="utf-8")
        cli.read_project(self.project)
        prompt = cli.start_prompt(config, resumed=True, model="exact-model", effort="high")
        self.assertIn("do not auto-accept", prompt)
        self.assertIn("existing PROJECT_STATE.yaml remains authoritative", prompt)
        self.assertIn('"model": "exact-model"', prompt)
        self.assertEqual(0, self.launch(config, [sys.executable, str(self.fixture), "exit", str(self.project), "0"]))
        self.assertEqual(saved, state.read_text(encoding="utf-8"))

    def test_claude_project_has_generated_agents_and_verified_skill(self):
        self.prepare(host="claude")
        self.assertTrue(verify_install("claude", destination=self.project / cli.SKILLS)["ok"])
        self.assertTrue((self.project / ".claude/agents/book-genesis-blind-reader.md").is_file())

    def test_claude_explicit_effort_overrides_only_the_child_environment(self):
        config = self.prepare(host="claude")
        with patch.dict(os.environ, {"CLAUDE_CODE_EFFORT_LEVEL": "max", "BOOK_GENESIS_TEST_AUTH_BOUNDARY": "inherited"}):
            argv = [sys.executable, str(self.fixture), "check-effort", str(self.project), "medium"]
            self.assertEqual(0, self.launch(config, argv, host="claude", effort="medium"))
            self.assertEqual("max", os.environ["CLAUDE_CODE_EFFORT_LEVEL"])
        [record] = self.receipts()
        self.assertEqual("medium", record["effort"])
        self.assertEqual("not_assessed", record["book_completion"])

    def test_omitted_claude_effort_and_codex_preserve_the_native_environment(self):
        for host, effort in (("claude", None), ("codex", "high")):
            with self.subTest(host=host):
                config = self.prepare(host=host, project=self.temp / host)
                with patch.dict(os.environ, {"CLAUDE_CODE_EFFORT_LEVEL": "max", "BOOK_GENESIS_TEST_AUTH_BOUNDARY": "inherited"}):
                    argv = [sys.executable, str(self.fixture), "check-effort", str(self.temp / host), "max"]
                    self.assertEqual(0, self.launch(config, argv, project=self.temp / host, host=host, effort=effort))
                    self.assertEqual("max", os.environ["CLAUDE_CODE_EFFORT_LEVEL"])

    def test_resume_refuses_to_switch_the_verified_host(self):
        self.prepare()
        with patch.object(cli, "find_native", return_value=["native"]), redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(2, cli.main(["resume", str(self.project), "--host", "claude", "--prepare-only"]))
        self.assertIn("prepared and verified for Codex", errors.getvalue())
        self.assertFalse((self.project / ".claude").exists())

    def test_resume_of_a_folder_that_is_not_a_project_is_explained(self):
        self.project.mkdir()
        with redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(2, cli.main(["resume", str(self.project), "--prepare-only"]))
        self.assertIn("not a Book Genesis launcher project", errors.getvalue())

    def test_existing_launcher_lock_is_never_cleared(self):
        config = self.prepare()
        lock = self.project / cli.LOCK
        lock.write_text('{"launcher_pid": 999999}', encoding="utf-8")
        with patch.object(cli, "_has_terminal", return_value=True), patch.object(cli, "session_argv", return_value=["native"]), patch.object(cli, "run_attached") as dispatch:
            with self.assertRaisesRegex(ValueError, "already owns"):
                cli.launch_project(self.project, config, host="codex", model=None, effort=None, resumed=False)
        self.assertEqual('{"launcher_pid": 999999}', lock.read_text(encoding="utf-8"))
        dispatch.assert_not_called()

    def test_lock_names_the_running_native_process(self):
        config = self.prepare()
        self.assertEqual(0, self.launch(config, [sys.executable, str(self.fixture), "check-lock", str(self.project)]))
        self.assertFalse((self.project / cli.LOCK).exists())

    def test_exit_zero_is_recorded_as_native_exit_never_book_completion(self):
        config = self.prepare()
        self.assertEqual(0, self.launch(config, [sys.executable, str(self.fixture), "exit", str(self.project), "0", "--"]))
        [record] = self.receipts()
        self.assertEqual("not_assessed", record["book_completion"])
        self.assertEqual("native_session_exited", record["status"])
        self.assertEqual(0, record["native_exit_code"])
        self.assertIsInstance(record["native_pid"], int)
        self.assertEqual([sys.executable, str(self.fixture), "exit", str(self.project), "0"], record["native_command"])
        self.assertFalse((self.project / cli.LOCK).exists())

    def test_nonzero_native_exit_is_returned_and_recorded(self):
        config = self.prepare()
        # A native CLI rejecting a flag exits nonzero in the same way.
        self.assertEqual(3, self.launch(config, [sys.executable, str(self.fixture), "exit", str(self.project), "3"]))
        [record] = self.receipts()
        self.assertEqual(("native_session_exited", 3, "not_assessed"), (record["status"], record["native_exit_code"], record["book_completion"]))
        self.assertFalse((self.project / cli.LOCK).exists())

    def test_startup_failure_is_recorded_and_releases_the_lock(self):
        config = self.prepare()
        with self.assertRaises(OSError):
            self.launch(config, [str(self.temp / "missing native.exe"), "--"])
        [record] = self.receipts()
        self.assertEqual("launch_failed", record["status"])
        self.assertIsNone(record["native_exit_code"])
        self.assertNotIn("native_pid", record)
        self.assertFalse((self.project / cli.LOCK).exists())

    def test_interrupted_session_stops_its_tree_before_releasing_the_lock(self):
        config = self.prepare()
        pids = self.temp / "pids.json"
        interrupt_when_file_exists(pids)
        with self.assertRaises(KeyboardInterrupt):
            self.launch(config, [sys.executable, str(self.fixture), "tree", str(self.project), str(pids)])
        tree = json.loads(pids.read_text(encoding="utf-8"))
        self.assertTrue(wait_until_gone(tree["child"]))
        self.assertTrue(wait_until_gone(tree["grandchild"]))
        [record] = self.receipts()
        self.assertEqual("interrupted", record["status"])
        self.assertEqual(tree["child"], record["native_pid"])
        self.assertFalse((self.project / cli.LOCK).exists())

    @unittest.skipUnless(os.name == "nt", "Windows job ownership")
    def test_native_exit_stops_surviving_descendants_before_releasing_lock(self):
        config = self.prepare()
        for code in (0, 7):
            with self.subTest(native_exit=code):
                pids = self.temp / f"exit-{code}-pids.json"
                returned = self.launch(config, [sys.executable, str(self.fixture), "orphan", str(self.project), str(pids), str(code)])
                tree = json.loads(pids.read_text(encoding="utf-8"))
                self.assertEqual(code, returned)
                self.assertTrue(wait_until_gone(tree["grandchild"]), "descendant outlived a completed launch")
                self.assertFalse((self.project / cli.LOCK).exists())
                record = max(self.receipts(), key=lambda item: item["started_at"])
                self.assertEqual(code, record["native_exit_code"])
                self.assertEqual("not_assessed", record["book_completion"])

    @unittest.skipUnless(os.name == "nt", "Windows kill-on-close job")
    def test_abrupt_launcher_exit_stops_owned_tree_without_touching_other_processes(self):
        self.prepare()
        pids = self.temp / "hard-stop-pids.json"
        driver = self.temp / "abrupt launcher.py"
        driver.write_text(
            "import sys\n"
            f"sys.path.insert(0, {str(REPO_ROOT)!r})\n"
            "from pathlib import Path\n"
            "from launcher import cli\n"
            "cli._has_terminal = lambda: True\n"
            f"root = Path({str(self.project)!r})\n"
            f"cli.session_argv = lambda *a, **k: [sys.executable, {str(self.fixture)!r}, 'tree', str(root), {str(pids)!r}]\n"
            "cli.launch_project(root, cli.read_project(root), host='codex', model=None, effort=None, resumed=True)\n",
            encoding="utf-8",
        )
        unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        launcher = subprocess.Popen([sys.executable, str(driver)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        tree = None
        try:
            deadline = time.monotonic() + 15
            while not pids.exists() and launcher.poll() is None and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertTrue(pids.exists(), "fixture never reached a registered running tree")
            tree = json.loads(pids.read_text(encoding="utf-8"))
            launcher.kill()  # only the owned parent handle, without tree termination
            launcher.wait(timeout=5)
            self.assertTrue(wait_until_gone(tree["child"]), "native child outlived the launcher crash")
            self.assertTrue(wait_until_gone(tree["grandchild"]), "descendant outlived the launcher crash")
            self.assertIsNone(unrelated.poll(), "another session's process was stopped")
            self.assertTrue((self.project / cli.LOCK).exists(), "a crash must not clear the ownership record")
        finally:
            if launcher.poll() is None:
                launcher.kill()
                launcher.wait(timeout=5)
            unrelated.terminate()
            unrelated.wait(timeout=5)
            if tree is not None:
                # Protect the test machine if the regression is reintroduced.
                for pid in (tree["child"], tree["grandchild"]):
                    if pid_running(pid):
                        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, timeout=5, shell=False)

    def test_unverified_process_shutdown_keeps_lock_and_failure_receipt(self):
        config = self.prepare()
        real_guard = native._load_guard()

        def unverified(process):
            real_guard._terminate_and_reap_owned(process)  # do not leak the fixture
            return False

        pids = self.temp / "pids.json"
        interrupt_when_file_exists(pids)
        with patch.object(native, "_load_guard", return_value=types.SimpleNamespace(_terminate_and_reap_owned=unverified)):
            with self.assertRaisesRegex(native.NativeShutdownUnverified, "lock was kept"):
                self.launch(config, [sys.executable, str(self.fixture), "tree", str(self.project), str(pids)])
        lock = json.loads((self.project / cli.LOCK).read_text(encoding="utf-8"))
        tree = json.loads(pids.read_text(encoding="utf-8"))
        self.assertEqual(tree["child"], lock["native_pid"])
        [record] = self.receipts()
        self.assertEqual("shutdown_unverified", record["status"])
        # The kept lock blocks the next launch until someone checks the PIDs.
        with patch.object(cli, "_has_terminal", return_value=True), patch.object(cli, "session_argv", return_value=["native"]), patch.object(cli, "run_attached") as dispatch:
            with self.assertRaisesRegex(ValueError, "already owns"):
                cli.launch_project(self.project, config, host="codex", model=None, effort=None, resumed=True)
        dispatch.assert_not_called()
        wait_until_gone(tree["grandchild"])

    def test_long_windows_path_prepares_verifies_and_launches(self):
        # Make the book folder itself valid (< 248 characters) while installed
        # skill files and installer staging paths exceed the 260-character MAX_PATH.
        budget = 225 - len(str(self.temp)) - len("\\book with spaces")
        if budget < 40:
            self.skipTest("temporary directory path is too long to construct this case")
        parent = self.temp
        while budget > 0:
            segment = ("deep folder " * 5)[: min(50, budget - 1)].strip() or "d"
            parent = parent / segment
            budget -= len(segment) + 1
        project = parent / "book with spaces"
        config = self.prepare(project=project, host="claude")
        root = cli._install_path(project)
        longest = max(len(str(path)) - (len(str(root)) - len(str(project.resolve()))) for path in root.rglob("*"))
        self.assertGreater(longest, 260)
        self.assertLess(len(str(project.resolve())), 248)
        self.assertTrue(verify_install("claude", destination=cli._install_path(project / cli.SKILLS))["ok"])
        self.assertEqual("claude", cli.read_project(project)["host"])
        self.assertEqual(0, self.launch(config, [sys.executable, str(self.fixture), "exit", str(project), "0"], project=project, host="claude"))
        [record] = self.receipts(project)
        self.assertEqual("native_session_exited", record["status"])
        self.assertFalse(cli._install_path(project / cli.LOCK).exists())

    def test_prepare_only_cli_calls_no_model(self):
        with patch.object(cli, "find_native", return_value=["native"]), patch.object(cli, "launch_project") as launch:
            with redirect_stdout(io.StringIO()) as output:
                result = cli.main(["new", str(self.project), "--host", "codex", "--idea", "An unlisted station.", "--prepare-only"])
        self.assertEqual(0, result)
        launch.assert_not_called()
        self.assertIn("book_genesis.py resume", output.getvalue())
        self.assertEqual("codex", cli.read_project(self.project)["host"])

    def test_interactive_new_collects_author_before_opening_native_session(self):
        for answer, expected in (("Nora Reed", "Nora Reed"), ("", "Anonymous")):
            with self.subTest(answer=answer):
                project = self.temp / expected
                with patch.object(cli, "_has_terminal", return_value=True), patch.object(cli, "find_native", return_value=["native"]), patch.object(cli, "launch_project", return_value=0) as launch, patch("builtins.input", return_value=answer) as ask:
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(0, cli.main(["new", str(project), "--host", "codex", "--idea", "An unlisted station."]))
                ask.assert_called_once_with("Name on the title page [Anonymous]: ")
                self.assertEqual(expected, cli.read_project(project)["author_name"])
                self.assertEqual(expected, launch.call_args.kwargs["author_name"])

    def test_explicit_author_in_prepare_only_is_saved_without_a_prompt(self):
        with patch.object(cli, "find_native", return_value=["native"]), patch("builtins.input", side_effect=AssertionError("unexpected author prompt")), redirect_stdout(io.StringIO()):
            self.assertEqual(0, cli.main(["new", str(self.project), "--host", "codex", "--idea", "An unlisted station.", "--author", "Ada Bell", "--prepare-only"]))
        self.assertEqual("Ada Bell", cli.read_project(self.project)["author_name"])

    def test_resume_author_override_preserves_the_original_record(self):
        config = self.prepare(author_name="Original Pen Name")
        original = (self.project / cli.CONFIG).read_bytes()
        with patch.object(cli, "_has_terminal", return_value=True), patch.object(cli, "find_native", return_value=["native"]), patch.object(cli, "launch_project", return_value=0) as launch, redirect_stdout(io.StringIO()):
            self.assertEqual(0, cli.main(["resume", str(self.project), "--author", "New Pen Name"]))
        self.assertEqual("New Pen Name", launch.call_args.kwargs["author_name"])
        self.assertEqual(original, (self.project / cli.CONFIG).read_bytes())
        prompt = cli.start_prompt(config, resumed=True, author_name="New Pen Name")
        self.assertIn('"New Pen Name"', prompt)

    @unittest.skipUnless(os.name == "nt", "PowerShell command quoting")
    def test_resume_plan_preserves_overrides_as_literal_powershell_arguments(self):
        self.prepare()
        credit = "Pat's $(do-not-run) Book"
        with patch.object(cli, "find_native", return_value=["native"]), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(0, cli.main(["resume", str(self.project), "--author", credit, "--model", "exact-model", "--effort", "high", "--prepare-only"]))
        command = output.getvalue().split("When ready, run in PowerShell: ", 1)[1].strip()
        self.assertIn("--model 'exact-model'", command)
        self.assertIn("--effort 'high'", command)
        self.assertIn("--author 'Pat''s $(do-not-run) Book'", command)
        self.assertIsNone(cli.read_project(self.project)["author_name"])

    def test_new_without_a_terminal_refuses_before_creating_the_project(self):
        with patch.object(cli, "_has_terminal", return_value=False), patch.object(cli, "find_native", return_value=["native"]):
            with redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(2, cli.main(["new", str(self.project), "--host", "codex", "--idea", "An unlisted station."]))
        self.assertIn("--prepare-only", errors.getvalue())
        self.assertFalse(self.project.exists())

    def test_invalid_model_and_effort_do_not_create_a_project(self):
        for options in ({"model": "--unsafe-option"}, {"host": "claude", "effort": "minimal"}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.prepare(**options)
        self.assertFalse(self.project.exists())

    def test_noninteractive_launch_gives_a_concrete_resume_path(self):
        config = self.prepare()
        with patch.object(cli, "_has_terminal", return_value=False):
            with self.assertRaisesRegex(ValueError, "book_genesis.py resume"):
                cli.launch_project(self.project, config, host="codex", model=None, effort=None, resumed=False)
        self.assertFalse((self.project / cli.LOCK).exists())

    def test_status_reports_launcher_records_without_claiming_progress(self):
        config = self.prepare()
        self.launch(config, [sys.executable, str(self.fixture), "exit", str(self.project), "0"])
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(1, cli.main(["status", str(self.project)]))
        text = output.getvalue()
        self.assertIn("Launches: 1 | last: native_session_exited | native exit: 0 | book completion: not_assessed", text)
        self.assertIn("No pipeline state", text)

    def test_status_supplies_saved_review_index_and_preserves_verifier_failure(self):
        self.prepare()
        (self.project / "PROJECT_STATE.yaml").write_text("saved state\n", encoding="utf-8")
        index = self.project / "evaluations/review-index.json"
        index.parent.mkdir()
        original = b'{"schema_version": 1, "scopes": []}\n'
        index.write_bytes(original)
        for verification_exit, expected in ((0, 0), (1, 1)):
            with self.subTest(verification_exit=verification_exit):
                results = [subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], verification_exit)]
                with patch.object(cli.subprocess, "run", side_effect=results) as run, redirect_stdout(io.StringIO()):
                    self.assertEqual(expected, cli.main(["status", str(self.project)]))
                command = run.call_args_list[1].args[0]
                self.assertEqual(str(index), command[command.index("--review-index") + 1])
                self.assertNotIn("--check", command, "keep the core's default delivery AND review checks")
                self.assertFalse(run.call_args_list[1].kwargs["shell"])
                self.assertEqual(original, index.read_bytes(), "status must not regenerate reader evidence")

    def test_status_with_no_review_index_does_not_skip_required_review_check(self):
        self.prepare()
        (self.project / "PROJECT_STATE.yaml").write_text("saved state\n", encoding="utf-8")
        results = [subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 1)]
        with patch.object(cli.subprocess, "run", side_effect=results) as run, redirect_stdout(io.StringIO()):
            self.assertEqual(1, cli.main(["status", str(self.project)]))
        command = run.call_args_list[1].args[0]
        self.assertNotIn("--review-index", command)
        self.assertNotIn("--check", command, "missing readers must not become a delivery-only pass")
        self.assertFalse((self.project / "evaluations/review-index.json").exists())


if __name__ == "__main__":
    unittest.main()
