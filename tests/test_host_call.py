"""Deterministic tests for the native command guard.

The guard is deliberately exercised with a small Python child process rather
than a model or provider.  The tests define the narrow public contract used by
the host: one active child per state directory, durable call receipts, replay
by call id, and ownership-aware timeout/lock handling.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "skills" / "book-genesis" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

import run_host_call as host_guard  # noqa: E402
from run_host_call import HostCallError, run_host_call  # noqa: E402


CHILD_SOURCE = r'''
import json
import os
from pathlib import Path
import sys
import time

mode, control, payload = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
output = Path(sys.argv[4]) if len(sys.argv) > 4 else None
control.mkdir(parents=True, exist_ok=True)
(control / "invocations.log").open("a", encoding="utf-8").write(f"{os.getpid()}\n")
(control / "started").write_text(str(os.getpid()), encoding="ascii")

if mode == "wait":
    while not (control / "release").exists():
        time.sleep(0.01)
elif mode == "empty":
    sys.stderr.write("empty child diagnostic\\n")
    raise SystemExit(0)
elif mode == "fail":
    sys.stderr.write("child failed deliberately\\n")
    raise SystemExit(7)
elif mode == "stdout-only":
    print("diagnostic stdout without an explicit response path")
    raise SystemExit(0)
elif mode == "missing-output":
    print("diagnostic stdout despite an explicit response path")
    raise SystemExit(0)
elif mode == "partial-wait":
    if output is None:
        raise SystemExit(6)
    output.write_text("partial response that must remain private", encoding="utf-8")
    (control / "partial").write_text("written", encoding="ascii")
    while not (control / "release").exists():
        time.sleep(0.01)

sys.stderr.write("child diagnostic\\n")
response = json.dumps({"ok": True, "payload": json.loads(payload)}, sort_keys=True)
if output is None:
    print("child stdout diagnostic")
    print(response)
else:
    print("child stdout diagnostic")
    output.write_text(response + "\n", encoding="utf-8")
'''


class HostCallTests(unittest.TestCase):
    def setUp(self) -> None:
        # The guard rejects a book whose root is inside the system temp
        # directory, because child cwd isolation would then be ambiguous.
        self.temp = tempfile.TemporaryDirectory(prefix=".host-call-test-", dir=REPO_ROOT)
        self.root = Path(self.temp.name)
        self.state = self.root / "host-state"
        self.state.mkdir()
        self.packet = self.root / "packet.json"
        self.packet.write_text(json.dumps({"chapter": 3, "packet": "frozen"}), encoding="utf-8")
        self.child = self.root / "fake_child.py"
        self.child.write_text(CHILD_SOURCE, encoding="utf-8")
        self.runner = self.root / "run_call.py"
        self.runner.write_text(
            "import json, sys\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "import run_host_call as host_guard\n"
            "from run_host_call import run_host_call, HostCallError\n"
            "if len(sys.argv) > 6 and sys.argv[6] == 'fail-lock':\n"
            "    original = host_guard._write_lock\n"
            "    calls = [0]\n"
            "    def fail_after_spawn(path, value):\n"
            "        calls[0] += 1\n"
            "        if calls[0] == 2:\n"
            "            raise OSError('metadata write injected failure')\n"
            "        original(path, value)\n"
            "    host_guard._write_lock = fail_after_spawn\n"
            "try:\n"
            "    result = run_host_call(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])\n"
            "except HostCallError as exc:\n"
            "    result = exc.receipt\n"
            "print(json.dumps(result, sort_keys=True))\n",
            encoding="utf-8",
        )
        self.payload = {"chapter": 3, "packet": "frozen"}

    def tearDown(self) -> None:
        self.temp.cleanup()

    def command(self, mode: str = "ok", control: Path | None = None, *, explicit_output: bool = True) -> list[str]:
        control = control or (self.root / f"control-{mode}")
        command = [sys.executable, str(self.child), mode, str(control), json.dumps(self.payload)]
        if explicit_output:
            command.append("{output}")
        return command

    def command_json(self, mode: str = "ok", control: Path | None = None, timeout: float = 2.0, *, explicit_output: bool = True) -> str:
        return json.dumps({"argv": self.command(mode, control, explicit_output=explicit_output), "timeout_seconds": timeout})

    def output(self, name: str) -> Path:
        return self.root / "outputs" / f"{name}.json"

    def invocations(self, control: Path | None = None) -> list[str]:
        control = control or (self.root / "control-ok")
        path = control / "invocations.log"
        return path.read_text(encoding="utf-8").splitlines() if path.exists() else []

    def call(self, call_id: str, mode: str = "ok", *, output: Path | None = None, control: Path | None = None, timeout: float = 2.0, packet: Path | None = None, explicit_output: bool = True) -> dict[str, object]:
        return run_host_call(
            book_dir=self.state,
            call_id=call_id,
            packet_path=packet or self.packet,
            command_json=self.command_json(mode, control, timeout, explicit_output=explicit_output),
        )

    def receipt_path(self, call_id: str) -> Path:
        return self.state / "work" / "host-calls" / call_id / "receipt.json"

    def wait_for_started(self, control: Path) -> None:
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            marker = control / "started"
            if marker.exists() and marker.read_text(encoding="ascii").strip():
                return
            time.sleep(0.01)
        self.fail("fake child did not start")

    @staticmethod
    def pid_alive(pid: int) -> bool:
        if os.name != "nt":
            try:
                os.kill(pid, 0)
            except (ProcessLookupError, PermissionError):
                return False
            return True
        kernel32 = __import__("ctypes").windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        try:
            code = __import__("ctypes").c_ulong()
            if not kernel32.GetExitCodeProcess(handle, __import__("ctypes").byref(code)):
                return False
            return code.value == 259  # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)

    def test_second_call_while_first_alive_is_busy_and_does_not_spawn(self) -> None:
        control = self.root / "control-wait"
        result: list[object] = []
        errors: list[BaseException] = []

        def first() -> None:
            try:
                result.append(self.call("first", "wait", output=self.output("first"), control=control))
            except BaseException as exc:  # pragma: no cover - assertion below reports it
                errors.append(exc)

        thread = threading.Thread(target=first)
        thread.start()
        self.wait_for_started(control)
        with self.assertRaises(HostCallError):
            self.call("second", "ok", output=self.output("second"))
        self.assertEqual(1, len(self.invocations(control)))
        (control / "release").write_text("go", encoding="ascii")
        thread.join(timeout=3)
        self.assertFalse(thread.is_alive())
        self.assertEqual([], errors)
        self.assertEqual("completed", result[0]["status"])

    def test_partial_output_is_pending_until_owned_child_completes(self) -> None:
        control = self.root / "control-partial"
        result: list[object] = []
        errors: list[BaseException] = []

        def first() -> None:
            try:
                result.append(self.call("partial", "partial-wait", control=control))
            except BaseException as exc:  # pragma: no cover - assertion below reports it
                errors.append(exc)

        thread = threading.Thread(target=first)
        thread.start()
        try:
            self.wait_for_started(control)
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline and not (control / "partial").exists():
                time.sleep(0.01)
            self.assertTrue((control / "partial").exists(), "fake child did not write its partial pending output")
            response = self.state / "work" / "host-calls" / "partial" / "response"
            self.assertFalse(response.exists(), "partial child output was exposed as the final response")
            with self.assertRaises(HostCallError):
                self.call("other-while-partial", "ok")
        finally:
            (control / "release").write_text("go", encoding="ascii")
            thread.join(timeout=3)
        self.assertFalse(thread.is_alive())
        self.assertEqual([], errors)
        self.assertEqual("completed", result[0]["status"])
        self.assertNotIn("partial response", response.read_text(encoding="utf-8"))

    def test_failed_attempt_requires_new_call_id_and_preserves_first_result(self) -> None:
        with self.assertRaises(HostCallError):
            self.call("first", "empty")
        first_receipt = self.receipt_path("first").read_bytes()
        with self.assertRaises((HostCallError, ValueError)):
            self.call("first", "ok")
        self.assertEqual(first_receipt, self.receipt_path("first").read_bytes())
        self.assertEqual(1, len(self.invocations(self.root / "control-empty")))

        second = self.call("retry-new-id", "ok")
        self.assertEqual("completed", second["status"])
        first_record = json.loads(first_receipt.decode("utf-8"))
        self.assertNotEqual(first_record["paths"]["response"], second["paths"]["response"])
        self.assertEqual(1, len(self.invocations(self.root / "control-ok")))

    def test_empty_or_nonzero_child_never_gets_completed_receipt(self) -> None:
        for mode in ("empty", "fail"):
            call_id = f"bad-{mode}"
            with self.assertRaises(HostCallError):
                self.call(call_id, mode, output=self.output(call_id))
            receipt_path = self.receipt_path(call_id)
            self.assertTrue(receipt_path.is_file(), receipt_path)
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertNotEqual("completed", receipt.get("status"))

    def test_completed_call_replays_exactly_without_new_execution(self) -> None:
        target = self.output("replay")
        first = self.call("replay", output=target)
        count = len(self.invocations())
        replay = self.call("replay")
        self.assertEqual(first["status"], replay["status"])
        self.assertTrue(replay["idempotent"])
        self.assertEqual(count, len(self.invocations()))

    def test_same_call_id_with_different_request_is_rejected(self) -> None:
        self.call("mismatch")
        changed_packet = self.root / "changed-packet.json"
        changed_packet.write_text(json.dumps(dict(self.payload, packet="changed")), encoding="utf-8")
        with self.assertRaises((HostCallError, ValueError)):
            run_host_call(
                book_dir=self.state,
                call_id="mismatch",
                packet_path=changed_packet,
                command_json=self.command_json(),
            )
        self.assertEqual(1, len(self.invocations()))

    def test_success_receipt_captures_streams_response_and_input_hash(self) -> None:
        result = self.call("receipt")
        self.assertEqual("completed", result["status"])
        paths = result["paths"]
        call_dir = self.state / "work" / "host-calls" / "receipt"
        self.assertIn("child diagnostic", (call_dir / Path(paths["stderr"]).name).read_text(encoding="utf-8"))
        stdout = (call_dir / Path(paths["stdout"]).name).read_text(encoding="utf-8")
        self.assertIn("child stdout diagnostic", stdout)
        response = json.loads((call_dir / Path(paths["response"]).name).read_text(encoding="utf-8"))
        self.assertEqual({"ok": True, "payload": self.payload}, response)
        expected = hashlib.sha256(self.packet.read_bytes()).hexdigest()
        self.assertEqual(expected, result["packet_sha256"])

    def test_stdout_only_command_without_output_placeholder_is_supported(self) -> None:
        result = self.call("stdout-only", "stdout-only", explicit_output=False)
        self.assertEqual("completed", result["status"])
        response = self.state / "work" / "host-calls" / "stdout-only" / "response"
        self.assertIn("diagnostic stdout", response.read_text(encoding="utf-8"))

    def test_explicit_output_path_missing_is_not_completed_by_stdout(self) -> None:
        with self.assertRaises(HostCallError):
            self.call("missing-output", "missing-output")
        receipt = json.loads(self.receipt_path("missing-output").read_text(encoding="utf-8"))
        self.assertNotEqual("completed", receipt["status"])

    def test_post_launch_lock_metadata_failure_terminates_owned_child(self) -> None:
        control = self.root / "control-lock-failure"
        runner = subprocess.Popen(
            [
                sys.executable,
                str(self.runner),
                str(SCRIPT_ROOT),
                str(self.state),
                "lock-failure",
                str(self.packet),
                self.command_json("wait", control),
                "fail-lock",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.wait_for_started(control)
        pid = int((control / "started").read_text(encoding="ascii"))
        try:
            try:
                runner.wait(timeout=3)
            except subprocess.TimeoutExpired:
                runner.kill()
                runner.wait(timeout=2)
            survived = self.pid_alive(pid)
            self.assertFalse(survived, "child survived a post-launch metadata failure")
        finally:
            if self.pid_alive(pid):
                (control / "release").write_text("cleanup", encoding="ascii")
                deadline = time.monotonic() + 1.0
                while time.monotonic() < deadline and self.pid_alive(pid):
                    time.sleep(0.01)

    def test_tree_shutdown_failure_keeps_lock_when_direct_child_is_reaped(self) -> None:
        control = self.root / "control-tree-failure"

        def report_tree_failure_but_reap_direct_child(process: subprocess.Popen[bytes]) -> bool:
            process.terminate()
            process.wait(timeout=2)
            return False

        with patch.object(host_guard, "_terminate_owned_tree", side_effect=report_tree_failure_but_reap_direct_child):
            with self.assertRaises(HostCallError) as raised:
                self.call("tree-failure", "wait", control=control, timeout=0.08)

        pid = int((control / "started").read_text(encoding="ascii"))
        self.assertFalse(self.pid_alive(pid), "direct child was not reaped after simulated tree failure")
        self.assertIn("shutdown was not verified", str(raised.exception))
        self.assertIn("active lock retained", str(raised.exception))
        lock = self.state / "work" / "host-calls" / ".active.lock"
        self.assertTrue(lock.is_file(), "unverified tree shutdown must retain the active lock")
        self.assertEqual("failed", raised.exception.receipt["status"])

    def test_book_root_inside_system_temp_uses_sibling_fresh_cwd(self) -> None:
        book = Path(tempfile.mkdtemp(prefix="book-genesis-book-", dir=tempfile.gettempdir()))
        try:
            packet = book / "packet.json"
            packet.write_text(self.packet.read_text(encoding="utf-8"), encoding="utf-8")
            control = book / "control"
            result = run_host_call(
                book_dir=book,
                call_id="temp-root",
                packet_path=packet,
                command_json=self.command_json("ok", control),
            )
            self.assertEqual("completed", result["status"])
        finally:
            shutil.rmtree(book, ignore_errors=True)

    def test_dead_stale_owner_fails_closed_without_auto_recovery(self) -> None:
        active = self.state / "work" / "host-calls" / ".active.lock"
        active.parent.mkdir(parents=True, exist_ok=True)
        active.write_text(
            json.dumps({"call_id": "dead-owner", "helper_pid": 99999998, "child_pid": 99999997}),
            encoding="utf-8",
        )
        with self.assertRaises(HostCallError):
            self.call("after-stale")
        self.assertTrue(active.exists(), "failed-closed stale lock was silently removed")

    def test_timeout_terminates_only_owned_child(self) -> None:
        owned = self.root / "control-owned"
        unrelated = self.root / "control-unrelated"
        unrelated_proc = subprocess.Popen(self.command("wait", unrelated, explicit_output=False), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        command_json = self.command_json("wait", owned, timeout=0.08)
        runner = subprocess.Popen(
            [sys.executable, str(self.runner), str(SCRIPT_ROOT), str(self.state), "timeout", str(self.packet), command_json],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            self.wait_for_started(unrelated)
            self.wait_for_started(owned)
            try:
                runner.wait(timeout=5)
            except subprocess.TimeoutExpired:
                runner.kill()
                runner.wait(timeout=2)
                self.fail("owned timeout call did not return")
            self.assertIsNone(unrelated_proc.poll(), "timeout killed a process not owned by this call")
        finally:
            (unrelated / "release").write_text("go", encoding="ascii")
            unrelated_proc.wait(timeout=2)

    def test_stale_owner_with_live_child_remains_blocked(self) -> None:
        control = self.root / "control-stale"
        child = subprocess.Popen(self.command("wait", control, explicit_output=False), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.wait_for_started(control)
            active = self.state / "work" / "host-calls" / ".active.lock"
            active.parent.mkdir(parents=True, exist_ok=True)
            active.write_text(
                json.dumps({"call_id": "stale", "owner_pid": 99999999, "child_pid": child.pid}),
                encoding="utf-8",
            )
            with self.assertRaises(HostCallError):
                self.call("new-call", output=self.output("new-call"))
            self.assertIsNone(child.poll())
        finally:
            (control / "release").write_text("go", encoding="ascii")
            child.wait(timeout=2)


if __name__ == "__main__":
    unittest.main()
