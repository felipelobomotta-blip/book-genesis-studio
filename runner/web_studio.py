"""Loopback-only Writing Studio. The existing runner remains the sole book writer."""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from datetime import datetime, timezone
from pathlib import Path
import queue
import secrets
import threading
import time
from urllib.parse import parse_qs, urlsplit

from runner.adapters import AdapterError
from runner.studio import StudioView
from runner.filesystem import load_state_summary, scaffold_project
from runner.studio_state import FileCache, JournalView, safe_message

ASSETS = Path(__file__).parent / "web"


class StudioModel:
    def __init__(self, library: Path, initial_project=None, setup_factory=None):
        self.library = library.resolve()
        self.library.mkdir(parents=True, exist_ok=True)
        self.project = Path(initial_project).resolve() if initial_project else None
        self.extra = [self.project] if self.project else []
        self.setup_factory = setup_factory
        self.mutex = threading.RLock()
        self.worker = None
        self.view = StudioView()
        self.status = "ready"
        self.stage = ""
        self.detail = "Your next book starts with an idea."
        self.question = None
        self.prose = ""
        self.prose_task = ""
        self.logs = deque(maxlen=100)
        self.started = None
        self.finished = None
        self.delivery = {}
        self.feedback = ""
        self.roles = {}
        self.warnings = []
        self.selected_connection = "saved"
        self.selected_model = ""
        self.probing = False
        self.closing = False
        self.probe = {"active": False, "status": "idle", "detail": "", "prose": "", "logs": []}
        self.probe_view = StudioView()
        self.last_error = None
        self.read_warning = ""
        self.cache = FileCache()
        self.api_setup = None
        from runner.roles import available_adapters
        self.connections = ["saved"] + [name for name, installed in available_adapters().items() if installed]
        if self.project:
            self.restore()

    def summary(self, project):
        path = project / "PROJECT_STATE.yaml"
        try:
            return self.cache.read(path, lambda _: load_state_summary(project))
        except (OSError, ValueError) as exc:
            self.read_warning = "Could not refresh saved book details: " + safe_message(exc) + ". Previously loaded information is shown."
            return self.cache.previous(path, {})

    def restore(self):
        """Reopen durable feedback/errors without pretending a dead worker is active."""
        summary = self.summary(self.project)
        self.status = "completed" if summary.get("status") == "completed" else "ready"
        from runner.session import PHASE_STAGE
        self.stage = "Package" if self.status == "completed" else PHASE_STAGE.get(summary.get("current_phase"), "")
        count = len(list((self.project / "manuscript/chapters").glob("chapter-*.md")))
        self.detail = f"{count} saved chapter(s). Select a chapter to read, or resume your book."
        self.last_error = None
        path = self.project / "work/studio-events.jsonl"
        try:
            with path.open(encoding="utf-8") as handle:
                records = deque(handle, maxlen=500)
            for line in records:
                try:
                    record = json.loads(line)
                    kind, payload = record["kind"], record["payload"]
                    if kind == "error":
                        self.remember_error(payload["text"])
                    elif kind == "score":
                        self.feedback = payload["text"]
                    elif kind == "result":
                        self.detail = payload["message"]
                        if payload["status"] == "completed":
                            self.last_error = None
                except (ValueError, KeyError, TypeError):
                    continue
        except OSError:
            pass

    def remember_error(self, message, *, persist=False):
        from runner.recovery import classify_error
        message = safe_message(message)
        advice = classify_error(message)
        self.last_error = {"message": message, "category": advice.category,
                           "action": advice.action, "stage": self.stage,
                           "journal": str(self.project / "work/studio-events.jsonl") if self.project else ""}
        if persist and self.project:
            record = {"timestamp": datetime.now(timezone.utc).isoformat(), "kind": "error",
                      "payload": {"text": message}}
            try:
                path = self.project / "work/studio-events.jsonl"
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            except OSError:
                pass

    def active(self):
        return self.worker is not None and self.worker.is_alive()

    def books(self):
        candidates = list(self.library.iterdir()) + self.extra
        books, seen = [], set()
        for path in candidates:
            path = path.resolve()
            if path in seen or not (path / "PROJECT_STATE.yaml").is_file():
                continue
            seen.add(path)
            try:
                summary = self.summary(path)
            except (OSError, ValueError):
                continue
            books.append({"id": self.book_id(path), "title": summary.get("title") or path.name,
                          "idea": summary.get("idea", ""), "status": summary.get("status", ""),
                          "chapters": len(list((path / "manuscript/chapters").glob("chapter-*.md")))})
        return books

    @staticmethod
    def book_id(path):
        return hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:24]

    def select(self, identifier):
        if self.active():
            raise ValueError("Pause the current book before opening another.")
        for path in list(self.library.iterdir()) + self.extra:
            if self.book_id(path) == identifier and (path / "PROJECT_STATE.yaml").is_file():
                self.project = path.resolve()
                self.view = StudioView()
                self.status, self.stage, self.detail = "ready", "", "Your saved book is ready to reopen."
                self.question, self.prose, self.delivery = None, "", {}
                self.feedback = ""
                self.started = self.finished = None
                self.logs.clear()
                self.restore()
                return
        raise ValueError("This book is not in the open library.")

    def setup(self, connection, model):
        if self.setup_factory:
            return self.setup_factory(self.project)
        from runner.app import build_setup
        from runner.roles import build_role_adapters
        if connection == "saved" and self.api_setup is not None:
            return build_role_adapters(user_config=self.api_setup)
        setup = build_setup(self.project or self.library) if connection == "saved" else build_role_adapters(available={connection: True})
        if model:
            for role in ("writer", "editor", "architect", "disruptor"):
                if setup.adapters[role].name == setup.adapters["writer"].name:
                    setup.models[role] = model
            setup.warnings.append("Writing model selected explicitly: " + model)
        return setup

    def start(self, payload, *, probe=False):
        if self.closing:
            raise ValueError("This workspace is closing. Reopen Studio to continue.")
        if self.active():
            raise ValueError("Writing is already in progress.")
        connection = payload.get("connection", "saved")
        from runner.activity import RequestBudget
        budget = RequestBudget(payload.get("request_limit", 200))
        model = str(payload.get("model", "")).strip()
        if connection not in self.connections or len(model) > 160:
            raise ValueError("Choose an available connection and model.")
        setup = None
        if not probe:
            # Resolve the selected setup before creating a new folder. A
            # missing login/key must not leave an empty book behind when the
            # first provider call would fail.
            try:
                setup = self.setup(connection, model)
            except Exception as exc:
                self.remember_error(str(exc), persist=True)
                raise
        if not probe and payload.get("new"):
            self.last_error = None
            idea, language = str(payload.get("idea", "")).strip(), str(payload.get("language", "en")).strip()
            if not idea or len(idea) > 20000 or not language or len(language) > 20:
                raise ValueError("Add a book idea and a short language code.")
            from runner.cli import _slug
            stem = _slug(idea)[:70] or "my-book"
            project = self.library / stem
            number = 2
            while project.exists():
                project = self.library / f"{stem}-{number}"
                number += 1
            scaffold_project(project, idea=idea, language=language, adapter="auto", model_name="auto")
            self.project = project
        if not probe and self.project is None:
            raise ValueError("Create or open a book first.")
        self.selected_connection, self.selected_model = connection, model
        if probe:
            self.start_probe(connection, model)
            return
        self.probing = False
        self.view = JournalView(self.project)
        self.view.budget = budget
        self.status, self.stage, self.detail = "running", "Connecting", "Connecting to your selected writing tools."
        self.question, self.prose, self.prose_task, self.delivery = None, "", "", {}
        self.feedback = ""
        self.logs.clear()
        self.started = time.monotonic()
        self.finished = None

        def work():
            try:
                from runner.session import run_session
                result = run_session(self.project, setup, self.view)
                message = result.message
                if result.status == "stopped" and "book-genesis resume" in message:
                    message = "Your progress is saved. Choose Resume writing whenever you are ready."
                self.view.emit("result", status=result.status, message=message)
            except Exception as exc:
                from runner.recovery import classify_error
                message = safe_message(exc) + " " + classify_error(str(exc)).action
                self.view.fail(message)
                self.view.emit("result", status="failed", message=message)
            finally:
                self.view.emit("idle")
        self.worker = threading.Thread(target=work, daemon=False)
        self.worker.start()

    def start_probe(self, connection, model):
        self.probing = True
        self.probe_view = StudioView()
        self.probe = {"active": True, "status": "running", "detail": "Testing your connection. Provider usage applies.", "prose": "", "logs": []}
        def work():
            from runner.activity import activity_events, complete_with_activity, WorkflowPaused
            try:
                setup = self.setup(connection, model)
                with activity_events(self.probe_view.event, prose_listener=self.probe_view.prose, cancel=self.probe_view.cancel):
                    complete_with_activity(setup.adapters["writer"],
                        "Write only a 60 to 90 word original scene about finding a lost library key. No tools or commands.",
                        model=setup.models.get("writer", ""), task="Chapter 0 writer")
                self.probe_view.emit("result", status="ready", message="Connection responded. This sample verifies the connection, not book quality.")
            except WorkflowPaused:
                self.probe_view.emit("result", status="stopped", message="Connection test stopped safely.")
            except Exception as exc:
                self.probe_view.emit("result", status="failed", message=safe_message(exc))
        self.worker = threading.Thread(target=work, daemon=False)
        self.worker.start()

    def configure_api(self, data):
        if self.active() or self.closing:
            raise ValueError("Finish or pause the current request first.")
        from runner.studio_connections import prepare_setup
        config = prepare_setup(data)
        self.probing = True
        self.probe_view = StudioView()
        self.probe = {"active": True, "status": "running", "detail": "Checking your selected writing and reader models. Up to two short requests.", "prose": "", "logs": []}
        def work():
            from runner.roles import build_adapter
            from runner.userconfig import write_user_config
            from runner.activity import activity_events, complete_with_activity, WorkflowPaused
            try:
                checked = set()
                for role in ("writer", "judge"):
                    if self.probe_view.cancel.is_set():
                        raise ValueError("Connection check stopped. No setup was saved.")
                    choice = config.roles[role]
                    if (choice.adapter,choice.model) in checked:
                        continue
                    adapter = build_adapter(choice.adapter, user_config=config)
                    adapter.timeout_seconds = 90
                    # Route setup checks through the same public activity channel as a
                    # book run. A slow API must visibly say what it is doing; private
                    # reasoning and provider logs remain excluded by activity.py.
                    with activity_events(self.probe_view.event, prose_listener=self.probe_view.prose,
                                         cancel=self.probe_view.cancel):
                        reply = complete_with_activity(
                            adapter,
                            "Reply with a brief greeting to a new author. No tools or commands.",
                            model=choice.model,
                            task=f"Connection check {role}",
                        )
                    if not reply.strip():
                        raise ValueError("The model returned no text.")
                    checked.add((choice.adapter,choice.model))
                if self.probe_view.cancel.is_set():
                    raise ValueError("Connection check stopped. No setup was saved.")
                if data.get("remember") is True:
                    write_user_config(config)
                self.api_setup = config
                self.selected_connection, self.selected_model = "saved", ""
                suffix = "Saved on this computer." if data.get("remember") is True else "Available until Studio closes."
                self.probe_view.emit("result", status="ready", message="Connection verified. " + suffix + " Select Saved connection setup for your next book. Readers use this provider too.")
            except Exception as exc:
                message = str(exc)
                secret = data.get("api_key")
                if secret:
                    message = message.replace(secret, "[redacted]")
                self.probe_view.emit("result", status="failed", message=safe_message(message))
        self.worker = threading.Thread(target=work, daemon=False)
        self.worker.start()

    def drain(self):
        while True:
            try:
                kind, payload = self.probe_view.events.get_nowait()
            except queue.Empty:
                break
            if kind == "prose":
                self.probe["prose"] += payload["text"]
            elif kind == "activity":
                self.probe.setdefault("logs", []).append(payload["text"])
            elif kind == "result":
                self.probe.update(status=payload["status"], detail=payload["message"], active=False)
                self.probing = False
        while True:
            try:
                kind, payload = self.view.events.get_nowait()
            except queue.Empty:
                break
            if kind == "prose":
                if payload["task"] != self.prose_task:
                    self.prose, self.prose_task = "", payload["task"]
                self.prose += payload["text"]
            elif kind == "question":
                self.question = payload
                self.status, self.detail = "awaiting_author", "Your turn. A simple yes or a note is enough."
            elif kind == "stage":
                self.stage, self.detail = payload["name"], payload["detail"]
                if payload["state"] == "working":
                    self.status = "running"
                if payload["state"] == "paused":
                    self.status = "stopped"
            elif kind == "activity":
                self.logs.append(payload["text"])
            elif kind == "error":
                self.logs.append(payload["text"])
                self.detail = payload["text"]
                self.remember_error(payload["text"])
            elif kind == "header":
                self.roles, self.warnings = payload.get("roles", {}), payload.get("warnings", [])
            elif kind == "delivery":
                self.delivery = payload["paths"]
            elif kind == "score":
                self.feedback = payload["text"]
            elif kind == "result":
                self.status, self.detail = payload["status"], payload["message"]
                self.question = None
                self.finished = time.monotonic()
                if self.status == "completed":
                    self.last_error = None
            elif kind == "idle" and self.status == "running":
                self.status = "stopped"

    def snapshot(self):
        with self.mutex:
            # Sample liveness before consuming events. A worker that finishes
            # during this snapshot stays active until its final events are read.
            active = self.active()
            self.drain()
            self.read_warning = ""
            chapters, summary = [], {}
            if self.project:
                summary = self.summary(self.project)
                for path in sorted((self.project / "manuscript/chapters").glob("chapter-*.md")):
                    if not path.resolve().is_relative_to(self.project):
                        continue
                    try:
                        def describe(p):
                            text = p.read_text(encoding="utf-8")
                            return {"number": int(p.stem.split("-")[-1]),
                                    "title": next((line.lstrip("# ") for line in text.splitlines() if line.strip()), p.stem),
                                    "words": len(text.split())}
                        chapters.append(self.cache.read(path, describe))
                    except (OSError, ValueError) as exc:
                        self.read_warning = "Could not refresh a saved chapter: " + safe_message(exc)
                        previous = self.cache.previous(path, None)
                        if previous:
                            chapters.append(previous)
            return {"status": self.status, "stage": self.stage, "detail": self.detail,
                    "active": active, "question": self.question, "prose": self.prose, "prose_task": self.prose_task,
                    "logs": list(self.logs), "books": self.books(), "chapters": chapters,
                    "project": ({"id": self.book_id(self.project), "title": summary.get("title") or self.project.name,
                                 "idea": summary.get("idea", ""), "path": str(self.project)} if self.project else None),
                    "elapsed": round((self.finished or time.monotonic()) - self.started) if self.started else 0,
                    "connections": self.connections, "roles": self.roles, "warnings": self.warnings,
                    "connection": self.selected_connection, "model": self.selected_model,
                    "probing": self.probing, "probe": self.probe, "closing": self.closing, "feedback": self.feedback,
                    "last_error": self.last_error, "read_warning": self.read_warning,
                    "request_limit": getattr(getattr(self.view, "budget", None), "limit", 200),
                    "requests_used": getattr(getattr(self.view, "budget", None), "used", 0),
                    "has_working_drafts": bool(self.project and any((self.project / "manuscript/chapters/history").glob("chapter-*/manifest.json")))}

    def chapter(self, number):
        if self.project is None or type(number) is not int or number < 1:
            raise ValueError("Select a saved chapter.")
        path = self.project / "manuscript/chapters" / f"chapter-{number:02d}.md"
        if not path.is_file() or not path.resolve().is_relative_to(self.project):
            raise ValueError("This chapter is not saved yet.")
        return path.read_text(encoding="utf-8")

    def action(self, route, data):
        with self.mutex:
            self.drain()
            if route == "close":
                self.closing = True
                self.view.cancel.set()
                self.probe_view.cancel.set()
                self.detail = "Closing safely. The current request will finish and your saved files will remain."
            elif route == "start":
                self.start(data)
            elif route == "probe":
                self.start(data, probe=True)
            elif route == "configure-api":
                self.configure_api(data)
            elif route == "open":
                self.select(data.get("id", ""))
            elif route == "pause":
                self.view.cancel.set()
                self.probe_view.cancel.set()
                self.detail = "Pause requested. The current call will finish safely before writing stops."
            elif route == "answer":
                text = str(data.get("text", "")).strip()
                if not self.question or not text or len(text) > 20000:
                    raise ValueError("There is no question waiting for that answer.")
                if not self.question.get("allow_notes", True) and text.lower() not in {"yes", "no", "ok", "q"}:
                    raise ValueError("Choose Yes or No for this question.")
                if not self.view.answer(text):
                    raise ValueError("That question has already been answered.")
                self.question, self.status, self.detail = None, "running", "Your answer is saved. Continuing."
            elif route == "notes":
                if self.active() or not self.project:
                    raise ValueError("Pause and open a book before adding guidance.")
                text = str(data.get("text", "")).strip()
                if not text or len(text) > 20000:
                    raise ValueError("Write the change you want first.")
                from runner.session import save_notes
                from runner.workspace_lock import project_lock
                with project_lock(self.project):
                    save_notes(self.project, text)
                self.detail = "Guidance saved. Resume when you are ready."
            else:
                raise ValueError("Unknown action.")

    def download(self, fmt):
        with self.mutex:
            if self.active() or not self.project or fmt not in {"epub", "markdown", "working-draft"}:
                raise ValueError("Pause writing before downloading a saved book.")
            from runner.export import export_project
            from runner.workspace_lock import project_lock
            with project_lock(self.project):
                if fmt == "working-draft":
                    from runner.working_draft import export_working_draft
                    path = export_working_draft(self.project)
                    return path.name, path.read_bytes()
                draft = load_state_summary(self.project).get("status") != "completed"
                extension = "epub" if fmt == "epub" else "md"
                name = ("draft" if draft else "manuscript") + "-" + str(time.time_ns()) + "." + extension
                path = export_project(self.project, fmt, self.project / "exports" / name)
                return name, path.read_bytes()


class StudioServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, model, port=0):
        self.model, self.token = model, secrets.token_urlsafe(32)
        super().__init__(("127.0.0.1", port), StudioHandler)

    def close_when_idle(self):
        def finish():
            worker = self.model.worker
            if worker:
                worker.join()
            self.shutdown()
        threading.Thread(target=finish, daemon=True).start()


class StudioHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def allowed(self, authenticated=False):
        host = f"127.0.0.1:{self.server.server_port}"
        if self.headers.get("Host") != host:
            return False
        origin = self.headers.get("Origin")
        if origin and origin != "http://" + host:
            return False
        supplied = self.headers.get("X-Studio-Token", "")
        return not authenticated or (supplied.isascii() and secrets.compare_digest(supplied, self.server.token))

    def respond(self, data, content_type="application/json", status=200, filename=None):
        if not isinstance(data, bytes):
            data = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type + ("; charset=utf-8" if content_type.startswith(("text/", "application/json")) else ""))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        route = urlsplit(self.path)
        if not self.allowed(route.path.startswith("/api/")):
            self.respond({"error": "This request is not authorized for the local Studio."}, status=403)
            return
        try:
            if route.path == "/":
                html = (ASSETS / "index.html").read_text(encoding="utf-8").replace("STUDIO_SESSION_TOKEN", self.server.token)
                self.respond(html.encode("utf-8"), "text/html")
            elif route.path in {"/studio.css", "/studio.js", "/studio_poll.js"}:
                self.respond((ASSETS / route.path[1:]).read_bytes(), "text/css" if route.path.endswith("css") else "text/javascript")
            elif route.path == "/api/state":
                self.respond(self.server.model.snapshot())
            elif route.path == "/api/chapter":
                self.respond({"text": self.server.model.chapter(int(parse_qs(route.query).get("number", ["0"])[0]))})
            elif route.path == "/api/download":
                fmt = parse_qs(route.query).get("format", ["epub"])[0]
                name, content = self.server.model.download(fmt)
                self.respond(content, "application/epub+zip" if fmt == "epub" else "text/markdown", filename=name)
            else:
                self.respond({"error": "Not found"}, status=404)
        except (OSError, ValueError, KeyError, AdapterError) as exc:
            self.respond({"error": safe_message(exc)}, status=400)

    def do_POST(self):
        # Drain bounded request bodies before rejecting headers. Closing a Windows
        # socket with unread body bytes can reset it before the error reaches UI.
        self.connection.settimeout(10)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            # Drain modest oversized forms as well, so Windows can deliver the
            # validation response instead of resetting an unread socket.
            raw = self.rfile.read(length) if 0 < length <= 1048576 else b""
        except (ValueError, OSError):
            self.respond({"error": "A bounded JSON request is required."}, status=400)
            return
        if not self.allowed(True):
            self.respond({"error": "This request is not authorized for the local Studio."}, status=403)
            return
        try:
            if not 0 < length <= 65536 or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise ValueError("A bounded JSON request is required.")
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("An object is required.")
            route = urlsplit(self.path).path
            if not route.startswith("/api/"):
                raise ValueError("Unknown action.")
            self.server.model.action(route[5:], data)
            self.respond({"ok": True})
            if route == "/api/close":
                self.server.close_when_idle()
        except (OSError, ValueError, KeyError, AdapterError) as exc:
            self.respond({"error": safe_message(exc)}, status=400)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="book-genesis studio", description="Open the local visual Writing Studio.")
    parser.add_argument("project", nargs="?", type=Path)
    parser.add_argument("--library", type=Path, default=Path.home() / "Book Genesis" / "books")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args(argv)
    if args.project and not (args.project / "PROJECT_STATE.yaml").is_file():
        parser.error("Choose an existing Book Genesis project folder.")
    model = StudioModel(args.library, args.project)
    server = StudioServer(model, args.port)
    url = f"http://127.0.0.1:{server.server_port}/"
    import sys
    if sys.stdout is not None:
        print("Writing Studio: " + url, flush=True)
    if not args.no_open:
        import webbrowser
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        model.view.cancel.set()
        model.probe_view.cancel.set()
        if sys.stdout is not None:
            print("Finishing the current request before stopping. Saved chapters remain in your project folder.", flush=True)
        if model.worker:
            model.worker.join()
    finally:
        server.server_close()
    return 0
