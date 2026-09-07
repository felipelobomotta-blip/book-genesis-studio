import json
import sys
import pytest
from runner.activity import activity_events, complete_with_activity, public_text_observer
from runner.adapters import AdapterError, _claude_public_delta, _claude_stream_result, _run


def event(kind, **fields):
    return json.dumps({"type": "stream_event", "event": {"type": "content_block_delta", "delta": {"type": kind, **fields}}})


def test_only_public_text_reaches_the_preview():
    received = []
    for line in (event("thinking_delta", thinking="private reasoning"), event("input_json_delta", partial_json="tool input"), '{"type":"system","text":"private setup"}', event("text_delta", text="Public prose — café.")):
        _claude_public_delta(line, received.append)
    assert received == ["Public prose — café."]


def test_partial_stream_never_substitutes_for_a_completed_response():
    partial = event("text_delta", text="The story began")
    with pytest.raises(AdapterError, match="without a completed"):
        _claude_stream_result(partial)
    with pytest.raises(AdapterError, match="could not complete"):
        _claude_stream_result(partial + '\n{"type":"result","is_error":true,"result":"quota reached"}')
    assert _claude_stream_result(partial + '\n{"type":"result","is_error":false,"result":"A complete story."}') == "A complete story."


def test_public_prose_is_shown_before_a_real_subprocess_finishes(tmp_path):
    ack = tmp_path / "observed.txt"
    line = event("text_delta", text="Already writing.")
    program = ("import time; from pathlib import Path; "
               f"print({line!r},flush=True); p=Path({str(ack)!r}); "
               "deadline=time.monotonic()+2\n"
               "while not p.exists() and time.monotonic()<deadline: time.sleep(.01)\n"
               "assert p.exists(), 'stdout was buffered until process completion'\n"
               "print('finished',flush=True)\n")
    def observe(line):
        _claude_public_delta(line, lambda text: ack.write_text(text))
    result = _run([sys.executable, "-c", program], "", timeout_seconds=4, on_stdout_line=observe)
    assert result.returncode == 0, result.stderr
    assert ack.read_text() == "Already writing."
    assert "finished" in result.stdout


def test_activity_scope_only_exposes_prose_and_resets_after_failure():
    class Provider:
        name = "fixture"
        def complete(self, prompt, *, model=""):
            observer = public_text_observer()
            if observer:
                observer("A visible line.")
            raise AdapterError("failed after preview")
    lines = []
    with activity_events(lines.append):
        with pytest.raises(AdapterError):
            complete_with_activity(Provider(), "private prompt", task="Chapter 1 writer")
        assert public_text_observer() is None
        with pytest.raises(AdapterError):
            complete_with_activity(Provider(), "private prompt", task="Reader")
    assert sum("writing now" in line for line in lines) == 1
    assert all("private prompt" not in line for line in lines)
