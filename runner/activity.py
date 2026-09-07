"""Visible provider activity without exposing internal reasoning or raw provider logs."""
from contextlib import contextmanager
from contextvars import ContextVar
import threading
import time
import json
from datetime import datetime, timezone

_listener = ContextVar("book_genesis_activity", default=None)
_public_text = ContextVar("book_genesis_public_text", default=None)
_project = ContextVar("book_genesis_activity_project", default=None)
_prose_listener = ContextVar("book_genesis_prose_listener", default=None)
_cancel = ContextVar("book_genesis_cancel", default=None)
_budget = ContextVar("book_genesis_call_budget", default=None)
HEARTBEAT_SECONDS = 5


class WorkflowPaused(Exception):
    """Cooperative pause between provider calls; in-flight text is never discarded."""


class RequestBudget:
    """Count attempted model requests, not dollars or estimated token charges."""
    def __init__(self, limit):
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError("Choose a session request limit between 1 and 1000.")
        self.limit, self.used = limit, 0
        self.lock = threading.Lock()

    def reserve(self):
        with self.lock:
            if self.used >= self.limit:
                raise WorkflowPaused(f"Session limit reached ({self.limit} model requests). Saved work is preserved. Resume to authorize another session allowance.")
            self.used += 1


def public_text_observer():
    """Optional callback for generated prose, never provider reasoning or logs."""
    return _public_text.get()


@contextmanager
def activity_events(listener, *, project=None, prose_listener=None, cancel=None, budget=None):
    token = _listener.set(listener)
    tokens = [(_project, _project.set(project)), (_prose_listener, _prose_listener.set(prose_listener)),
              (_cancel, _cancel.set(cancel)), (_budget, _budget.set(budget))]
    try:
        yield
    finally:
        _listener.reset(token)
        for variable, value in reversed(tokens):
            variable.reset(value)


def complete_with_activity(adapter, prompt, *, model="", task="Model"):
    if _cancel.get() is not None and _cancel.get().is_set():
        raise WorkflowPaused("Paused at a safe boundary. Resume to continue the saved book.")
    if _budget.get() is not None:
        _budget.get().reserve()
    say = _listener.get() or (lambda _line: None)
    prose_listener = _prose_listener.get()
    # Adapters are intentionally duck-typed so integrations and tests can supply
    # a tiny object with only ``complete``. Fall back to its class name instead of
    # failing before the provider is called just because it omitted a display name.
    adapter_name = getattr(adapter, "name", adapter.__class__.__name__)
    label = f"{task} | {adapter_name} {model}".strip()
    started = time.monotonic()
    stopped = threading.Event()
    preview = ""
    last_preview = 0.0
    received_at = 0.0
    first_text_at = None
    say(f"{label}: request started")

    def text_delta(text):
        nonlocal preview, last_preview, received_at, first_text_at
        if stopped.is_set():
            return
        received_at = time.monotonic()
        if first_text_at is None:
            first_text_at = received_at - started
        if prose_listener:
            prose_listener(task, text)
        preview = (preview + text)[-800:]
        if received_at - last_preview >= 1:
            say(f"{label}: writing now | " + " ".join(preview.split())[-240:])
            last_preview = received_at

    def heartbeat():
        while not stopped.wait(HEARTBEAT_SECONDS):
            elapsed = int(time.monotonic() - started)
            state = "receiving prose" if received_at and time.monotonic() - received_at < HEARTBEAT_SECONDS else "waiting for provider response"
            say(f"{label}: {state} | {elapsed}s elapsed")

    worker = threading.Thread(target=heartbeat, daemon=True)
    worker.start()
    is_prose = task.startswith("Chapter ") and task.endswith(("writer", "editor", "reviser")) and "precision" not in task
    token = _public_text.set(text_delta if is_prose else None)
    outcome, words = "error", 0
    error_category = "unknown"
    try:
        result = adapter.complete(prompt, model=model)
        words = len(result.split())
        outcome = "success"
        if is_prose and prose_listener and first_text_at is None:
            prose_listener(task, result)
    except Exception as exc:
        from runner.recovery import classify_error
        error_category = classify_error(str(exc)).category
        raise
    finally:
        stopped.set()
        worker.join()
        _public_text.reset(token)
        project = _project.get()
        if project is not None:
            record = {"timestamp": datetime.now(timezone.utc).isoformat(), "task": task,
                      "provider": adapter.name, "model": model, "prompt_chars": len(prompt),
                      "elapsed_seconds": round(time.monotonic() - started, 3),
                      "first_text_seconds": first_text_at, "output_words": words,
                      "outcome": outcome, "error_category": error_category if outcome == "error" else None}
            try:
                path = project / "work" / "metrics.jsonl"
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            except OSError:
                say("Performance measurements could not be saved; the provider result is preserved.")
    say(f"{label}: received {len(result.split())} words in {time.monotonic() - started:.1f}s")
    return result
