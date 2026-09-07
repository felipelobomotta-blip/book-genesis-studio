"""Real Windows timeout cleanup, scoped to a child tree created by this test."""
import csv
import os
from pathlib import Path
import subprocess
import sys
import time
import pytest
from runner.adapters import _run


@pytest.mark.skipif(os.name != "nt", reason="Windows process-tree behavior")
@pytest.mark.parametrize("streaming", [False, True])
def test_timeout_reaps_the_wrapper_and_its_child(tmp_path, streaming):
    marker = tmp_path / "child-pid.txt"
    child = "import time; time.sleep(30)"
    wrapper = ("import subprocess,sys,time; from pathlib import Path; "
               f"p=subprocess.Popen([sys.executable,'-c',{child!r}]); "
               f"Path({str(marker)!r}).write_text(str(p.pid)); time.sleep(30)")
    started = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired):
        _run([sys.executable, "-c", wrapper], "", timeout_seconds=3, cwd=tmp_path,
             on_stdout_line=(lambda line: None) if streaming else None)
    assert time.monotonic() - started < 10
    assert marker.is_file(), "The test child must start before measuring cleanup"
    pid = int(marker.read_text())
    result = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True, timeout=5)
    alive = any(len(row) > 1 and row[1] == str(pid) for row in csv.reader(result.stdout.splitlines()))
    if alive:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, timeout=5)
    assert not alive, "The timed-out provider left its test child running"
