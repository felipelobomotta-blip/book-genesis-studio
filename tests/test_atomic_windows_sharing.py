"""Real Windows read handles must not abort single-writer state publication."""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/book-genesis/scripts"))
from workflow_state import atomic, WorkflowError, REPLACE_RETRY_DELAYS


def read_handle_without_delete_share(path):
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                                  wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    # A legitimate status reader permits reads/writes, but not rename/delete.
    handle = kernel.CreateFileW(str(path), 0x80000000, 1 | 2, None, 3, 0x80, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    return kernel, handle


class AtomicStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "workflow.json"
        self.path.write_bytes(b'{"state":"original"}')

    def test_unrelated_filesystem_error_is_not_retried_or_relabelled(self):
        with patch("workflow_state.os.replace", side_effect=OSError("disk error")) as replace, \
             self.assertRaisesRegex(OSError, "disk error"):
            atomic(self.path, b"new")
        self.assertEqual(1, replace.call_count)
        self.assertEqual(b'{"state":"original"}', self.path.read_bytes())
        self.assertFalse(list(self.root.glob("*.tmp")))

    def test_an_edit_during_retry_is_preserved_instead_of_overwritten(self):
        error = PermissionError("synthetic Windows sharing error")
        error.winerror = 5
        def external_edit(_delay):
            self.path.write_bytes(b"the author's external change")
        with patch("workflow_state.os.replace", side_effect=error) as replace, \
             patch("workflow_state.time.sleep", side_effect=external_edit), \
             self.assertRaisesRegex(WorkflowError, "target changed during"):
            atomic(self.path, b"would overwrite")
        self.assertEqual(1, replace.call_count)
        self.assertEqual(b"the author's external change", self.path.read_bytes())
        self.assertFalse(list(self.root.glob("*.tmp")))

    def test_new_file_created_during_retry_is_not_overwritten(self):
        self.path.unlink()
        error = PermissionError("synthetic Windows sharing error")
        error.winerror = 32
        with patch("workflow_state.os.replace", side_effect=error), \
             patch("workflow_state.time.sleep", side_effect=lambda _delay: self.path.write_bytes(b"new external file")), \
             self.assertRaisesRegex(WorkflowError, "target changed during"):
            atomic(self.path, b"would overwrite")
        self.assertEqual(b"new external file", self.path.read_bytes())

    @unittest.skipUnless(os.name == "nt", "Requires real Windows file-sharing semantics")
    def test_real_reader_lock_reproduces_error_then_releases_for_atomic_publication(self):
        kernel, handle = read_handle_without_delete_share(self.path)
        raw = self.root / "raw.tmp"
        raw.write_bytes(b"prepared")
        try:
            with self.assertRaises(PermissionError) as caught:
                os.replace(raw, self.path)
            self.assertIn(caught.exception.winerror, (5, 32, 33))
            reader_closed = threading.Event()
            def release():
                time.sleep(.08)
                kernel.CloseHandle(handle)
                reader_closed.set()
            thread = threading.Thread(target=release)
            thread.start()
            try:
                atomic(self.path, b'{"state":"committed"}')
            finally:
                thread.join(timeout=2)
            self.assertTrue(reader_closed.is_set())
            self.assertEqual(b'{"state":"committed"}', self.path.read_bytes())
            self.assertEqual(b"prepared", raw.read_bytes())
        finally:
            if 'reader_closed' not in locals() or not reader_closed.is_set():
                kernel.CloseHandle(handle)

    @unittest.skipUnless(os.name == "nt", "Requires real Windows file-sharing semantics")
    def test_persistent_real_lock_fails_boundedly_without_deleting_the_target(self):
        kernel, handle = read_handle_without_delete_share(self.path)
        start = time.monotonic()
        try:
            with self.assertRaises(PermissionError):
                atomic(self.path, b"not published")
        finally:
            kernel.CloseHandle(handle)
        self.assertLess(time.monotonic() - start, sum(REPLACE_RETRY_DELAYS) + 1.0)
        self.assertEqual(b'{"state":"original"}', self.path.read_bytes())
        self.assertFalse(list(self.root.glob("workflow.json.*.tmp")))


if __name__ == "__main__":
    unittest.main()
