"""Local writing workspace. Tk stays on its UI thread; the existing runner owns books."""
from __future__ import annotations

import argparse
from pathlib import Path
import queue
import threading


class StudioView:
    """Thread-safe bridge; no widget is ever accessed by a provider or runner thread."""
    interactive = True

    def __init__(self):
        self.events = queue.Queue()
        self.answers = queue.Queue()
        self.cancel = threading.Event()
        self.waiting = threading.Event()

    def emit(self, kind, **payload):
        self.events.put((kind, payload))

    def header(self, **kwargs):
        self.emit("header", **kwargs)

    def stage_start(self, name, detail=""):
        self.emit("stage", name=name, detail=detail, state="working")

    def stage_update(self, name, detail):
        self.stage_start(name, detail)

    def stage_done(self, name, summary=""):
        self.emit("stage", name=name, detail=summary, state="saved")

    def stage_fail(self, name, message):
        self.emit("stage", name=name, detail=message, state="needs attention")

    def stage_stop(self, name, message):
        self.emit("stage", name=name, detail=message, state="paused")

    def event(self, line):
        self.emit("activity", text=line)

    def prose(self, task, text):
        self.emit("prose", task=task, text=text)

    def ask(self, prompt, default=""):
        return self.checkpoint(prompt, "", "Choose Yes to continue or No to keep your work and stop.", default=default, allow_notes=False)

    def checkpoint(self, title, body, hint, default="", allow_notes=True):
        self.waiting.set()
        self.emit("question", title=title, body=body, hint=hint, default=default, allow_notes=allow_notes)
        try:
            while not self.cancel.is_set():
                try:
                    return self.answers.get(timeout=0.1)
                except queue.Empty:
                    continue
            return "q"
        finally:
            self.waiting.clear()

    def answer(self, text):
        if self.waiting.is_set() and self.answers.empty():
            self.answers.put(text)
            return True
        return False

    def score(self, card):
        self.emit("score", text=card.markdown())

    def finish(self, paths):
        self.emit("delivery", paths={label: str(path) for label, path in paths.items()})

    def fail(self, message):
        self.emit("error", text=message)


class Studio:
    def __init__(self, root, project=None):
        import tkinter as tk
        from tkinter import ttk
        self.root, self.tk, self.ttk = root, tk, ttk
        self.project = Path(project).resolve() if project else None
        self.view = StudioView()
        self.worker = None
        self.last_task = ""
        self.chapter_paths = []
        self.chapter_signature = None
        root.title("Book Genesis — Writing Studio")
        root.geometry("1180x800")
        root.minsize(900, 650)
        root.configure(background="#f4f1eb")
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background="#f4f1eb")
        style.configure("TLabel", background="#f4f1eb", foreground="#253936", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 24, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=7)
        outer = ttk.Frame(root, padding=20)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Your idea. A book taking shape.", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Draft, read, revise. Your creativity leads; your work stays in your project folder.").pack(anchor="w", pady=(3, 12))
        form = ttk.Frame(outer)
        form.pack(fill="x")
        self.idea = tk.StringVar()
        ttk.Label(form, text="Book idea").grid(row=0, column=0, sticky="w")
        self.idea_entry = ttk.Entry(form, textvariable=self.idea)
        self.idea_entry.grid(row=1, column=0, sticky="ew", padx=(0, 12))
        self.language = tk.StringVar(value="en")
        ttk.Label(form, text="Language").grid(row=0, column=1, sticky="w")
        ttk.Entry(form, textvariable=self.language, width=7).grid(row=1, column=1, padx=(0, 12))
        self.connection = tk.StringVar(value="Saved connection setup")
        ttk.Label(form, text="Connection").grid(row=0, column=2, sticky="w")
        from runner.roles import available_adapters
        choices = ["Saved connection setup"] + [name for name, ok in available_adapters().items() if ok]
        self.connection_box = ttk.Combobox(form, textvariable=self.connection, values=choices, state="readonly", width=26)
        self.connection_box.grid(row=1, column=2, sticky="ew")
        self.writing_model = tk.StringVar()
        ttk.Label(form, text="Writing model (optional)").grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(form, textvariable=self.writing_model, width=28).grid(row=3, column=0, sticky="w")
        form.columnconfigure(0, weight=1)
        toolbar = ttk.Frame(outer)
        toolbar.pack(fill="x", pady=12)
        self.start_button = ttk.Button(toolbar, text="Start writing", command=self.start)
        self.start_button.pack(side="left")
        self.open_button = ttk.Button(toolbar, text="Open a book", command=self.open_project)
        self.open_button.pack(side="left", padx=6)
        self.test_button = ttk.Button(toolbar, text="Test connection", command=self.test_connection)
        self.test_button.pack(side="left")
        self.pause_button = ttk.Button(toolbar, text="Pause safely", command=self.pause, state="disabled")
        self.pause_button.pack(side="left", padx=6)
        self.export_button = ttk.Button(toolbar, text="Save EPUB", command=self.export)
        self.export_button.pack(side="right")
        self.status = tk.StringVar(value="Ready. Add an idea or open a saved book.")
        ttk.Label(outer, textvariable=self.status, wraplength=1080).pack(anchor="w")
        self.progress = ttk.Progressbar(outer, mode="indeterminate")
        self.progress.pack(fill="x", pady=(6, 10))
        self.stages = tk.StringVar(value="Intake  /  Foundation  /  Architecture  /  Drafting  /  Audit  /  Score  /  Package")
        ttk.Label(outer, textvariable=self.stages, wraplength=1080).pack(anchor="w", pady=(0, 10))
        panes = ttk.Panedwindow(outer, orient="horizontal")
        panes.pack(fill="both", expand=True)
        sidebar = ttk.Frame(panes, padding=(0, 0, 12, 0))
        ttk.Label(sidebar, text="SAVED CHAPTERS").pack(anchor="w")
        self.chapter_list = tk.Listbox(sidebar, width=25, relief="flat", font=("Segoe UI", 11), background="#e8e6df", foreground="#253936")
        self.chapter_list.pack(fill="both", expand=True, pady=8)
        self.chapter_list.bind("<<ListboxSelect>>", self.read_chapter)
        panes.add(sidebar, weight=1)
        tabs = ttk.Notebook(panes)
        self.tabs = tabs
        self.reading = self.text_tab(tabs, "Read & approve")
        self.live = self.text_tab(tabs, "Live writing")
        self.log = self.text_tab(tabs, "Activity")
        panes.add(tabs, weight=5)
        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(12, 0))
        self.yes_button = ttk.Button(actions, text="Yes / Continue", command=lambda: self.answer("yes"), state="disabled")
        self.yes_button.pack(side="left")
        self.no_button = ttk.Button(actions, text="No / Pause", command=lambda: self.answer("no"), state="disabled")
        self.no_button.pack(side="left", padx=6)
        self.notes = tk.StringVar()
        ttk.Entry(actions, textvariable=self.notes).pack(side="left", fill="x", expand=True, padx=6)
        self.note_button = ttk.Button(actions, text="Save guidance / request change", command=lambda: self.answer(self.notes.get().strip()), state="normal" if self.project else "disabled")
        self.note_button.pack(side="left")
        ttk.Label(outer, text="Feedback and scores come from models. They do not establish publication readiness or predict sales.").pack(anchor="w", pady=(9, 0))
        root.protocol("WM_DELETE_WINDOW", self.close)
        if self.project:
            from runner.filesystem import load_state_summary
            summary = load_state_summary(self.project)
            self.idea.set(summary.get("idea", ""))
            self.language.set(summary.get("language", "en"))
        self.refresh_chapters()
        root.after(100, self.poll)

    def text_tab(self, tabs, label):
        from tkinter.scrolledtext import ScrolledText
        panel = self.ttk.Frame(tabs)
        widget = ScrolledText(panel, wrap="word", font=("Georgia", 12), background="#fffdf8", foreground="#253936", relief="flat", padx=18, pady=16, state="disabled")
        widget.pack(fill="both", expand=True)
        tabs.add(panel, text=label)
        return widget

    def write(self, widget, text, replace=False):
        widget.configure(state="normal")
        if replace:
            widget.delete("1.0", "end")
        widget.insert("end", text)
        widget.see("end")
        widget.configure(state="disabled")

    def active(self):
        return self.worker is not None and self.worker.is_alive()

    def setup(self, selection, writing_model=""):
        from runner.app import build_setup
        from runner.roles import build_role_adapters
        if selection == "Saved connection setup":
            setup = build_setup(self.project or Path.cwd())
        else:
            setup = build_role_adapters(available={selection: True})
        if writing_model:
            # Apply the explicit model only to writing roles on the writer's provider.
            for role in ("writer", "editor", "architect", "disruptor"):
                if setup.adapters[role].name == setup.adapters["writer"].name:
                    setup.models[role] = writing_model
            setup.warnings.append("Writing model explicitly selected: " + writing_model + ". Model availability and usage depend on your connection.")
        return setup

    def launch(self, operation):
        if self.active():
            return
        self.view = StudioView()
        self.last_task = ""
        for button in (self.start_button, self.open_button, self.test_button):
            button.configure(state="disabled")
        self.note_button.configure(state="disabled")
        self.connection_box.configure(state="disabled")
        self.pause_button.configure(state="normal")
        self.progress.start(15)
        self.worker = threading.Thread(target=operation, daemon=False)
        self.worker.start()

    def start(self):
        if self.active():
            return
        idea, language, selection = self.idea.get().strip(), self.language.get().strip(), self.connection.get()
        writing_model = self.writing_model.get().strip()
        if self.project is None:
            if not idea or not language:
                self.status.set("Add a book idea and language first.")
                return
            from tkinter import filedialog
            parent = filedialog.askdirectory(title="Choose where your new book folder will be saved")
            if not parent:
                return
            from runner.cli import _slug
            self.project = Path(parent) / _slug(idea)
            if self.project.exists():
                self.status.set("That folder already exists. Use Open a book to resume it, or choose a different idea/folder.")
                self.project = None
                return
            from runner.filesystem import scaffold_project
            try:
                scaffold_project(self.project, idea=idea, language=language, adapter="auto", model_name="auto")
            except (OSError, ValueError) as exc:
                self.status.set(str(exc))
                self.project = None
                return
        self.status.set("Connecting. The book is saved locally; model requests use your selected connection and its allowance.")

        def work():
            from runner.session import run_session
            try:
                result = run_session(self.project, self.setup(selection, writing_model), self.view)
                self.view.emit("result", status=result.status, message=result.message)
            except Exception as exc:
                from runner.recovery import classify_error
                self.view.fail(str(exc) + "\n" + classify_error(str(exc)).action)
            finally:
                self.view.emit("idle")
        self.launch(work)

    def open_project(self):
        if self.active():
            return
        from tkinter import filedialog
        value = filedialog.askdirectory(title="Open a Book Genesis project")
        if not value:
            return
        project = Path(value)
        if not (project / "PROJECT_STATE.yaml").is_file():
            self.status.set("Choose the book folder containing PROJECT_STATE.yaml.")
            return
        self.project = project
        from runner.filesystem import load_state_summary
        summary = load_state_summary(project)
        self.idea.set(summary.get("idea", ""))
        self.language.set(summary.get("language", "en"))
        self.start_button.configure(text="Resume writing")
        self.status.set("Book opened. Read saved chapters or resume writing.")
        self.note_button.configure(state="normal")
        self.chapter_signature = None
        self.refresh_chapters()

    def test_connection(self):
        selection = self.connection.get()
        writing_model = self.writing_model.get().strip()
        self.status.set("Testing a short writing request. This uses your selected provider's allowance.")
        def work():
            from runner.activity import activity_events, complete_with_activity
            from runner.recovery import capabilities
            try:
                setup = self.setup(selection, writing_model)
                with activity_events(self.view.event, prose_listener=self.view.prose, cancel=self.view.cancel):
                    prose = complete_with_activity(setup.adapters["writer"],
                        "Return only an original 60 to 90 word scene in English about a lost library key. No tools, commands, or preamble.",
                        model=setup.models.get("writer", ""), task="Chapter 0 writer")
                if not prose.strip():
                    raise ValueError("The writing probe returned no text.")
                self.view.event("Text received. This probe does not establish book quality. Capabilities: " + str(capabilities(setup.adapters["writer"])))
                self.view.emit("result", status="connection responded", message="Inspect the sample in Live writing.")
            except Exception as exc:
                self.view.fail(str(exc))
            finally:
                self.view.emit("idle")
        self.launch(work)

    def pause(self):
        self.view.cancel.set()
        self.status.set("Pause requested. Waiting for the current call to finish safely; its configured timeout still applies.")

    def answer(self, text):
        if text and not self.active() and self.project:
            from runner.session import save_notes
            from runner.workspace_lock import project_lock
            try:
                with project_lock(self.project):
                    save_notes(self.project, text)
                self.status.set("Guidance saved. Resume writing to apply it to the remaining work or repair plan.")
                self.notes.set("")
            except (OSError, ValueError) as exc:
                self.status.set(str(exc))
            return
        if text and self.view.answer(text):
            for button in (self.yes_button, self.no_button, self.note_button):
                button.configure(state="disabled")
            self.notes.set("")
            self.status.set("Answer received. Continuing the saved workflow.")
            self.progress.start(15)

    def refresh_chapters(self):
        paths = sorted((self.project / "manuscript/chapters").glob("chapter-*.md")) if self.project else []
        signature = [(str(p), p.stat().st_mtime_ns) for p in paths]
        if signature != self.chapter_signature:
            self.chapter_signature, self.chapter_paths = signature, paths
            self.chapter_list.delete(0, "end")
            for path in paths:
                self.chapter_list.insert("end", path.stem.replace("-", " ").title())
        if self.project:
            self.start_button.configure(text="Resume writing")

    def read_chapter(self, _event=None):
        selection = self.chapter_list.curselection()
        if selection:
            try:
                self.write(self.reading, self.chapter_paths[selection[0]].read_text(encoding="utf-8"), replace=True)
                self.tabs.select(0)
            except OSError as exc:
                self.status.set(str(exc))

    def export(self):
        if self.project is None:
            self.status.set("Open or create a book first.")
            return
        if self.active():
            self.status.set("Pause writing before exporting a consistent snapshot.")
            return
        from tkinter import filedialog
        from runner.export import export_project
        from runner.filesystem import load_state_summary
        draft = load_state_summary(self.project).get("status") != "completed"
        destination = filedialog.asksaveasfilename(title="Save draft EPUB" if draft else "Save EPUB", defaultextension=".epub", initialfile="draft.epub" if draft else "manuscript.epub", filetypes=[("EPUB book", "*.epub")])
        if destination:
            try:
                from runner.workspace_lock import project_lock
                with project_lock(self.project):
                    path = export_project(self.project, "epub", Path(destination), overwrite=True)
                self.status.set(("Draft saved; editorial review remains unfinished: " if draft else "EPUB saved: ") + str(path))
            except (OSError, ValueError) as exc:
                self.status.set(str(exc))

    def poll(self):
        for _ in range(250):
            try:
                kind, payload = self.view.events.get_nowait()
            except queue.Empty:
                break
            if kind == "prose":
                task = payload["task"]
                if task != self.last_task:
                    self.write(self.live, "\n\n" + task + "\n" + "─" * 30 + "\n")
                    self.last_task = task
                self.write(self.live, payload["text"])
            elif kind == "question":
                self.progress.stop()
                self.status.set("Waiting for you: " + payload["title"])
                self.write(self.reading, payload["title"] + "\n\n" + payload["body"] + "\n\n" + payload["hint"], replace=True)
                self.tabs.select(0)
                for button in (self.yes_button, self.no_button, self.note_button):
                    button.configure(state="normal")
                if not payload.get("allow_notes", True):
                    self.note_button.configure(state="disabled")
            elif kind == "stage":
                self.status.set(payload["name"] + " — " + payload["state"] + ": " + payload["detail"])
                self.refresh_chapters()
            elif kind in {"activity", "error", "score"}:
                self.write(self.log, payload["text"] + "\n")
                if kind == "error":
                    self.status.set(payload["text"])
                    self.tabs.select(2)
            elif kind == "header":
                self.write(self.log, "Connections: " + str(payload.get("roles", {})) + "\n" + "\n".join(payload.get("warnings", [])) + "\n")
            elif kind == "delivery":
                self.write(self.log, "\n".join(label + ": " + path for label, path in payload["paths"].items()) + "\n")
            elif kind == "result":
                self.status.set(payload["status"] + ": " + payload["message"])
            elif kind == "idle":
                self.progress.stop()
                for button in (self.start_button, self.open_button, self.test_button):
                    button.configure(state="normal")
                self.connection_box.configure(state="readonly")
                for button in (self.pause_button, self.yes_button, self.no_button, self.note_button):
                    button.configure(state="disabled")
                self.note_button.configure(state="normal" if self.project else "disabled")
                self.refresh_chapters()
        self.root.after(100, self.poll)

    def close(self):
        if self.active():
            self.pause()
            self.status.set("Pausing safely. Keep this window open until the current call finishes, then close it.")
            return
        self.root.destroy()


def native_main(argv=None):
    parser = argparse.ArgumentParser(prog="book-genesis studio", description="Open the local visual writing workspace.")
    parser.add_argument("project", nargs="?")
    args = parser.parse_args(argv)
    if args.project and not (Path(args.project) / "PROJECT_STATE.yaml").is_file():
        parser.error("Choose an existing Book Genesis project folder, or omit the path to create one.")
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        Studio(root, args.project)
        root.after(150, root.deiconify)
        root.mainloop()
    except ImportError:
        print("The visual workspace needs Python's Tk support. Install Python with Tcl/Tk, or use book-genesis new.")
        return 1
    return 0


def main(argv=None):
    import sys
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--native" in argv:
        argv.remove("--native")
        return native_main(argv)
    from runner.web_studio import main as web_main
    return web_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
