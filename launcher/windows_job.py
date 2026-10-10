"""Own a native Windows process tree without changing the native CLI.

Start the process suspended, assign it to a private kill-on-close job, and
resume its one initial thread. Children inherit the job, including children
whose parent exits first. No jobs belonging to other sessions are opened.
Windows 8+ supports nesting this job inside a terminal/CI runner's job.

API contracts: https://learn.microsoft.com/windows/win32/procthread/job-objects
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes as w
import time


CREATE_SUSPENDED = 0x00000004


class _BasicLimits(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", w.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", w.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", w.DWORD),
        ("SchedulingClass", w.DWORD),
    ]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimits),
        ("IoInfo", ctypes.c_ulonglong * 6),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class _Accounting(ctypes.Structure):
    _fields_ = [
        ("TotalUserTime", ctypes.c_longlong),
        ("TotalKernelTime", ctypes.c_longlong),
        ("ThisPeriodTotalUserTime", ctypes.c_longlong),
        ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
        ("TotalPageFaultCount", w.DWORD),
        ("TotalProcesses", w.DWORD),
        ("ActiveProcesses", w.DWORD),
        ("TotalTerminatedProcesses", w.DWORD),
    ]


class _ThreadEntry(ctypes.Structure):
    _fields_ = [
        ("dwSize", w.DWORD), ("cntUsage", w.DWORD),
        ("th32ThreadID", w.DWORD), ("th32OwnerProcessID", w.DWORD),
        ("tpBasePri", w.LONG), ("tpDeltaPri", w.LONG), ("dwFlags", w.DWORD),
    ]


class WindowsJob:
    def __init__(self):
        kernel = self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateJobObjectW": ([ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
            "SetInformationJobObject": ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
            "QueryInformationJobObject": ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p], w.BOOL),
            "AssignProcessToJobObject": ([w.HANDLE, w.HANDLE], w.BOOL),
            "TerminateJobObject": ([w.HANDLE, w.UINT], w.BOOL),
            "OpenProcess": ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
            "CloseHandle": ([w.HANDLE], w.BOOL),
            "CreateToolhelp32Snapshot": ([w.DWORD, w.DWORD], w.HANDLE),
            "Thread32First": ([w.HANDLE, ctypes.POINTER(_ThreadEntry)], w.BOOL),
            "Thread32Next": ([w.HANDLE, ctypes.POINTER(_ThreadEntry)], w.BOOL),
            "OpenThread": ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
            "ResumeThread": ([w.HANDLE], w.DWORD),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(kernel, name)
            function.argtypes, function.restype = arguments, result
        self.handle = kernel.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = _ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000  # KILL_ON_JOB_CLOSE; no breakaway
        if not kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            error = ctypes.WinError(ctypes.get_last_error())
            self.close()
            raise error

    def assign(self, pid: int) -> None:
        process = self.kernel.OpenProcess(0x0101, False, pid)  # SET_QUOTA | TERMINATE
        if not process:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if not self.kernel.AssignProcessToJobObject(self.handle, process):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            self.kernel.CloseHandle(process)

    def resume(self, pid: int) -> None:
        snapshot = self.kernel.CreateToolhelp32Snapshot(4, 0)  # SNAPTHREAD
        if snapshot == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        entry = _ThreadEntry()
        entry.dwSize = ctypes.sizeof(entry)
        threads = []
        try:
            found = self.kernel.Thread32First(snapshot, ctypes.byref(entry))
            while found:
                if entry.th32OwnerProcessID == pid:
                    threads.append(entry.th32ThreadID)
                entry.dwSize = ctypes.sizeof(entry)
                found = self.kernel.Thread32Next(snapshot, ctypes.byref(entry))
            if ctypes.get_last_error() != 18:  # ERROR_NO_MORE_FILES
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            self.kernel.CloseHandle(snapshot)
        # The newly created process has not run yet. Do not guess which thread
        # to resume if its lifecycle differs from that supported contract.
        if len(threads) != 1:
            raise OSError(f"Suspended native process has {len(threads)} threads; expected its one initial thread")
        thread = self.kernel.OpenThread(2, False, threads[0])  # SUSPEND_RESUME
        if not thread:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            previous = self.kernel.ResumeThread(thread)
            if previous == 0xFFFFFFFF:
                raise ctypes.WinError(ctypes.get_last_error())
            if previous != 1:
                raise OSError(f"Unexpected native thread suspend count: {previous}")
        finally:
            self.kernel.CloseHandle(thread)

    def active_processes(self) -> int:
        accounting = _Accounting()
        if not self.kernel.QueryInformationJobObject(self.handle, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None):
            raise ctypes.WinError(ctypes.get_last_error())
        return accounting.ActiveProcesses

    def stop(self) -> bool:
        """Stop only our job and verify its active-process count, with a bound."""
        try:
            if self.active_processes() and not self.kernel.TerminateJobObject(self.handle, 130):
                return False
            deadline = time.monotonic() + 3
            while self.active_processes() and time.monotonic() < deadline:
                time.sleep(0.05)
            return self.active_processes() == 0
        except OSError:
            return False

    def close(self) -> None:
        if self.handle:
            handle, self.handle = self.handle, None
            if not self.kernel.CloseHandle(handle):
                raise ctypes.WinError(ctypes.get_last_error())
