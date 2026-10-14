"""A temporary Windows directory reader must not break skill installation."""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import shutil
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from runner.distribution import _swap_groups


def lock_directory(path):
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.CreateFileW(str(path), 0x80000000, 3, None, 3, 0x02000000, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    return kernel, handle


@unittest.skipUnless(os.name == "nt", "Windows installation sharing semantics")
class InstallSharingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="book-genesis-sharing-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "SKILL.md").write_bytes(b"new skill")
        self.parent = self.root / "installed"
        self.target = self.parent / "book-genesis"
        self.target.mkdir(parents=True)
        (self.target / "SKILL.md").write_bytes(b"original skill")
        self.record = self.parent / "record.json"
        self.record.write_bytes(b"original record")
        self.backup = self.root / "backup"

    def swap(self):
        return _swap_groups([(self.parent, {"book-genesis": self.source}, self.backup, shutil.copytree)],
            record=(self.record, lambda: b"new record"))

    def test_temporary_real_directory_lock_recovers_without_recopying_or_losing_backup(self):
        original = Path.rename
        handles, threads, observed_errors = [], [], []

        def rename(path, target):
            if path.name == "book-genesis" and path.parent.name.startswith(".book-genesis-stage-"):
                if not handles:
                    kernel, handle = lock_directory(path)
                    handles.append((kernel, handle))
                    thread = threading.Thread(target=lambda: (time.sleep(.15), kernel.CloseHandle(handle)))
                    threads.append(thread)
                    thread.start()
                try:
                    return original(path, target)
                except PermissionError as exc:
                    observed_errors.append(exc.winerror)
                    raise
            return original(path, target)

        try:
            with patch.object(Path, "rename", rename):
                try:
                    self.swap()
                except OSError as exc:
                    self.fail(f"temporary reader prevented installation: {exc}")
        finally:
            for thread in threads:
                thread.join(timeout=2)
        self.assertTrue(observed_errors, "test never reproduced the real sharing failure")
        self.assertTrue(set(observed_errors) <= {5, 32, 33})
        self.assertEqual(b"new skill", (self.target / "SKILL.md").read_bytes())
        self.assertEqual(b"original skill", (self.backup / "book-genesis/SKILL.md.bak").read_bytes())
        self.assertEqual(b"new record", self.record.read_bytes())
        self.assertEqual(b"new skill", (self.source / "SKILL.md").read_bytes())

    def test_persistent_real_directory_lock_fails_boundedly_and_restores_old_install(self):
        original = Path.rename
        handles = []

        def rename(path, target):
            if path.name == "book-genesis" and path.parent.name.startswith(".book-genesis-stage-") and not handles:
                handles.append(lock_directory(path))
            return original(path, target)

        started = time.monotonic()
        try:
            with patch.object(Path, "rename", rename), self.assertRaises(PermissionError):
                self.swap()
        finally:
            for kernel, handle in handles:
                kernel.CloseHandle(handle)
        self.assertLess(time.monotonic() - started, 3)
        self.assertEqual(b"original skill", (self.target / "SKILL.md").read_bytes())
        self.assertEqual(b"original record", self.record.read_bytes())

    def test_external_target_appearing_after_failed_rename_is_not_deleted_by_rollback(self):
        original = Path.rename

        def rename(path, target):
            if path.name == "book-genesis" and path.parent.name.startswith(".book-genesis-stage-"):
                self.target.mkdir()
                (self.target / "SKILL.md").write_bytes(b"concurrent author file")
                exc = PermissionError("temporary Windows access denial")
                exc.winerror = 5
                raise exc
            return original(path, target)

        with patch.object(Path, "rename", rename), self.assertRaises(OSError):
            self.swap()
        self.assertEqual(b"concurrent author file", (self.target / "SKILL.md").read_bytes())
        self.assertEqual(b"original skill", (self.backup / "book-genesis/SKILL.md.bak").read_bytes())
        self.assertEqual(b"original record", self.record.read_bytes())

    def test_unrelated_rename_error_is_not_retried_and_original_install_is_preserved(self):
        original = Path.rename
        attempts = []

        def rename(path, target):
            if path.name == "book-genesis" and path.parent.name.startswith(".book-genesis-stage-"):
                attempts.append(path)
                raise OSError("disk failure")
            return original(path, target)

        with patch.object(Path, "rename", rename), self.assertRaisesRegex(OSError, "disk failure"):
            self.swap()
        self.assertEqual(1, len(attempts))
        self.assertEqual(b"original skill", (self.target / "SKILL.md").read_bytes())
        self.assertEqual(b"original record", self.record.read_bytes())


if __name__ == "__main__":
    unittest.main()
