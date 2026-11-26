"""Local web studio for Book Genesis (pure Python stdlib, localhost-only).

End-to-end "Shower Idea -> Potential Bestseller" studio:
1. Catalyzes raw shower ideas into 3 high-concept commercial directions (`POST /api/catalyze`).
2. Prepares verified Book Genesis workspaces and launches/resumes/pauses the
   official 8-phase controlled workflow in the background (`POST /api/books`,
   `POST /api/books/<slug>/run`, `POST /api/books/<slug>/stop`).
3. Streams live phase/chapter/reader progress, renders book-typography chapters
   and planning artifacts, runs deterministic EN/PT-BR prose diagnostics, displays
   calibrated 3-reading literary rubrics + simulated Hook Test winners, and serves
   validated EPUB, Markdown, and complete Commercial/Viral Launch Kits.

Never edits canonical chapters or controller workflow state directly.
"""
from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
import sys
from typing import Callable
import urllib.parse
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/book-genesis/scripts"
for path in (ROOT, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from launcher.cli import prepare_project
from launcher.native import inspect_native
from launcher.status import collect_status
from plugin_entry import validate_creative_idea
from prose_diagnostics import analyze_manuscript
from studio.catalyst import catalyze_idea
from studio.runner_manager import StudioRunnerManager


FORMAT_PRESETS = {
    "pilot": {
        "label_pt": "Piloto Completo Ágil (6 capítulos · ~12 mil palavras)",
        "label_en": "Quick Complete Pilot (6 chapters · ~12k words)",
        "chapters": 6,
        "min_words": 9000,
        "max_words": 16000,
    },
    "novella": {
        "label_pt": "Novela Comercial (12 capítulos · ~35 mil palavras)",
        "label_en": "Commercial Novella (12 chapters · ~35k words)",
        "chapters": 12,
        "min_words": 28000,
        "max_words": 40000,
    },
    "commercial": {
        "label_pt": "Romance Best-Seller Padrão (24 capítulos · ~75 mil palavras)",
        "label_en": "Standard Commercial Novel (24 chapters · ~75k words)",
        "chapters": 24,
        "min_words": 65000,
        "max_words": 88000,
    },
    "epic": {
        "label_pt": "Romance Longo / Épico (32 capítulos · ~105 mil palavras)",
        "label_en": "Full-Length Epic (32 chapters · ~105k words)",
        "chapters": 32,
        "min_words": 95000,
        "max_words": 120000,
    },
}

DEFAULT_MODELS = {
    "codex": "gpt-5.6-luna",
    "claude": "claude-sonnet-4-6",
}


def slugify(text: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return (clean[:48] or "my-book").strip("-")


def _safe_book_dir(books_root: Path, slug: str) -> Path:
    if not slug or slug.startswith(".") or "/" in slug or "\\" in slug or slug in (".", "..") or not re.fullmatch(r"[A-Za-z0-9._-]+", slug):
        raise ValueError("Invalid book identifier")
    target = (books_root / slug).resolve()
    root = books_root.resolve()
    if target == root or not target.is_relative_to(root):
        raise ValueError("Book path escapes books directory")
    return target


def _safe_child(book_dir: Path, relative: str) -> Path:
    candidate = (book_dir / relative).resolve()
    root = book_dir.resolve()
    if not candidate.is_relative_to(root) or candidate == root:
        raise ValueError("Requested file escapes book folder")
    return candidate


def _read_json_optional(path: Path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _read_text_optional(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _claude_api_env_blocked() -> bool:
    return (
        any(os.environ.get(k) for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL"))
        or any(os.environ.get(k, "").lower() in {"1", "true", "yes"} for k in (
            "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY"))
    )


def detect_hosts() -> dict:
    result = {}
    for host in ("codex", "claude"):
        try:
            info = inspect_native(host)
            installed = bool(info.get("executable")) and info.get("status") not in {"missing", "unavailable"}
            signed_in = info.get("status") == "signed_in"
            account = info.get("account")
            if host == "claude":
                autonomous_ready = signed_in and account == "Claude plan" and not _claude_api_env_blocked()
                note = (
                    "Claude subscription ready"
                    if autonomous_ready
                    else "Unattended mode requires a claude.ai subscription login without ANTHROPIC_API_KEY/BASE_URL env vars"
                )
            else:
                autonomous_ready = signed_in
                note = "Ready for 1-click full-book generation" if autonomous_ready else "Sign in via CLI (`codex login`)"
            result[host] = {
                "installed": installed,
                "signed_in": signed_in,
                "autonomous_ready": autonomous_ready,
                "status": info.get("status"),
                "version": info.get("version"),
                "account": account,
                "note": note,
                "default_model": DEFAULT_MODELS[host],
            }
        except Exception as exc:
            result[host] = {
                "installed": False,
                "signed_in": False,
                "autonomous_ready": False,
                "error": str(exc),
                "default_model": DEFAULT_MODELS[host],
            }
    return result


def _display_title(book_dir: Path, config: dict, meta: dict) -> str:
    if meta.get("title"):
        return str(meta["title"])
    if config.get("title"):
        return str(config["title"])
    brief = _read_text_optional(book_dir / "artifacts/00-brief.md")
    if brief:
        first = next((line.lstrip("#").strip() for line in brief.splitlines() if line.strip()), "")
        if ":" in first:
            candidate = first.split(":", 1)[1].strip()
            if candidate:
                return candidate
    return book_dir.name.replace("-", " ").title()


def _extract_hook_test(positioning_md: str | None) -> dict | None:
    if not positioning_md or "## Simulated hook test" not in positioning_md:
        return None
    tail = positioning_md.split("## Simulated hook test", 1)[1]
    start = tail.find("{")
    end = tail.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(tail[start:end + 1])
        return parsed if isinstance(parsed, dict) else None
    except ValueError:
        return None


def _collect_panels(evaluations_dir: Path) -> list[dict]:
    if not evaluations_dir.is_dir():
        return []
    panels = []
    for path in sorted(evaluations_dir.glob("draft-check-*.json")):
        data = _read_json_optional(path)
        if isinstance(data, dict) and "reports" in data:
            panels.append(data)
    return panels


def list_books(books_root: Path, runner: StudioRunnerManager) -> list[dict]:
    if not books_root.is_dir():
        return []
    rows = []
    for entry in sorted(books_root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        project_file = entry / ".book-genesis/project.json"
        state_file = entry / "PROJECT_STATE.yaml"
        if not project_file.is_file() and not state_file.is_file():
            continue
        config = _read_json_optional(project_file) or {}
        meta = _read_json_optional(entry / "work/book-metadata.json") or {}
        chapters_dir = entry / "manuscript/chapters"
        chapter_files = sorted(chapters_dir.glob("chapter-*.md")) if chapters_dir.is_dir() else []
        journal = _read_json_optional(entry / ".book-genesis/workflow.json") or {}
        state_doc = _read_json_optional(state_file) or {}
        final_meas = _read_json_optional(entry / "evaluations/final-measurement.json")
        delivery_dir = entry / "delivery"
        has_epub = bool(delivery_dir.is_dir() and list(delivery_dir.glob("*.epub")))
        run_info = runner.inspect(entry.name, entry)
        planned = (config.get("autonomous_contract") or {}).get("chapters") or (state_doc.get("manuscript") or {}).get("chapter_count_planned")
        rows.append({
            "slug": entry.name,
            "title": _display_title(entry, config, meta),
            "genre": meta.get("genre") or (state_doc.get("project") or {}).get("genre") or "",
            "author": config.get("author_name") or "Anonymous",
            "language": config.get("language") or (state_doc.get("project") or {}).get("language") or "Portuguese (Brazil)",
            "idea": config.get("idea") or (state_doc.get("project") or {}).get("idea") or "",
            "host": config.get("host") or "",
            "collaboration": config.get("collaboration") or "autonomous",
            "chapters_saved": len(chapter_files),
            "chapters_planned": planned,
            "phase": journal.get("phase", 0),
            "journal_status": journal.get("status", "prepared"),
            "running": run_info["running"],
            "runner_state": run_info["state"],
            "has_epub": has_epub,
            "rubric_weighted": (final_meas.get("rubric") or {}).get("weighted") if isinstance(final_meas, dict) else None,
            "rubric_floor": (final_meas.get("rubric") or {}).get("floor") if isinstance(final_meas, dict) else None,
            "gates_passed": bool(final_meas.get("passed")) if isinstance(final_meas, dict) else None,
        })
    return rows


def book_detail(books_root: Path, slug: str, runner: StudioRunnerManager) -> dict:
    book_dir = _safe_book_dir(books_root, slug)
    if not book_dir.is_dir():
        raise FileNotFoundError(f"Book not found: {slug}")
    config = _read_json_optional(book_dir / ".book-genesis/project.json") or {}
    meta = _read_json_optional(book_dir / "work/book-metadata.json") or {}
    status = collect_status(book_dir, SCRIPTS)
    chapters_dir = book_dir / "manuscript/chapters"
    chapter_paths = sorted(chapters_dir.glob("chapter-*.md")) if chapters_dir.is_dir() else []
    chapters = []
    for path in chapter_paths:
        text = path.read_text(encoding="utf-8")
        first_line = next((line.lstrip("#").strip() for line in text.splitlines() if line.strip()), path.stem)
        words = len(re.findall(r"\S+", re.sub(r"<!--.*?-->", "", text, flags=re.S)))
        chapters.append({"file": path.name, "title": first_line, "words": words})
    language = config.get("language") or "Portuguese (Brazil)"
    diagnostics = analyze_manuscript(chapter_paths, language) if chapter_paths else None
    artifacts_dir = book_dir / "artifacts"
    artifacts = {}
    if artifacts_dir.is_dir():
        for path in sorted(artifacts_dir.glob("*.md")):
            artifacts[path.name] = path.read_text(encoding="utf-8")
    evaluations_dir = book_dir / "evaluations"
    final_measurement = _read_json_optional(evaluations_dir / "final-measurement.json")
    panels = _collect_panels(evaluations_dir)
    opening_panel = _read_json_optional(evaluations_dir / "draft-check-01-revised.json") or _read_json_optional(evaluations_dir / "draft-check-01.json")
    journal = _read_json_optional(book_dir / ".book-genesis/workflow.json") or {}
    revision_passes = journal.get("passes") or []
    hook_test = _extract_hook_test(artifacts.get("13-positioning.md"))

    delivery_dir = book_dir / "delivery"
    deliverables = []
    if delivery_dir.is_dir():
        for path in sorted(delivery_dir.iterdir()):
            if path.is_file() and path.suffix.lower() in {".epub", ".md", ".pdf", ".docx"}:
                deliverables.append({"name": path.name, "size": path.stat().st_size, "ext": path.suffix.lower()})

    prompt = build_agent_prompt(config.get("idea") or "", language, config.get("collaboration") == "autonomous")
    return {
        "slug": slug,
        "title": _display_title(book_dir, config, meta),
        "path": str(book_dir),
        "config": config,
        "metadata": meta,
        "status": status,
        "runner": runner.inspect(slug, book_dir),
        "chapters": chapters,
        "prose_diagnostics": diagnostics,
        "artifacts": artifacts,
        "panels": panels,
        "opening_panel": opening_panel,
        "revision_passes": revision_passes,
        "final_measurement": final_measurement,
        "hook_test": hook_test,
        "deliverables": deliverables,
        "has_commercial_kit": bool(artifacts.get("12-editorial-package.md") or artifacts.get("13-positioning.md")),
        "agent_prompt": prompt,
    }


def build_commercial_kit_markdown(detail: dict) -> str:
    title = detail.get("title") or detail["slug"]
    author = (detail.get("config") or {}).get("author_name") or "Anonymous"
    arts = detail.get("artifacts") or {}
    parts = [
        f"# Commercial, Discovery & Launch Kit — {title}",
        f"**Author:** {author}",
        "",
        "> Transparency note: Hooks, shelf positioning, BookTok angles, and simulated click/buy tests below are creative hypotheses and simulated readings on the finished manuscript — never a sales forecast or bestseller guarantee.",
        "",
    ]
    if arts.get("12-editorial-package.md"):
        parts.extend(["---", "", arts["12-editorial-package.md"].strip(), ""])
    if arts.get("13-positioning.md"):
        parts.extend(["---", "", arts["13-positioning.md"].strip(), ""])
    if arts.get("11-genesis-score.md"):
        parts.extend(["---", "", arts["11-genesis-score.md"].strip(), ""])
    return "\n".join(parts).strip() + "\n"


def build_agent_prompt(idea: str, language: str, autonomous: bool) -> str:
    is_pt = language.casefold().startswith(("pt", "portug", "brazil"))
    if is_pt:
        mode = (
            "Tome boas decisões criativas e vá até o final sem pausar capítulo por capítulo, revisando e exportando Markdown e EPUB."
            if autonomous
            else "Comece pela Fase 0 me mostrando 3 direções criativas de alto conceito para a minha ideia antes de travar o planejamento."
        )
        return f"Use Book Genesis. Minha ideia de livro: {idea.strip()} Escreva o livro completo em Português (Brasil). {mode}"
    mode = (
        "Make strong creative decisions and continue to the end without chapter-by-chapter approval, revising and exporting Markdown and EPUB."
        if autonomous
        else "Start with Phase 0 by showing me 3 distinct high-concept directions for my idea before locking the plan."
    )
    return f"Use Book Genesis. My book idea: {idea.strip()} Write the complete book in {language}. {mode}"


def create_book(books_root: Path, payload: dict, runner: StudioRunnerManager) -> dict:
    idea = str(payload.get("idea") or "").strip()
    if len(idea) < 12:
        raise ValueError("Please share a bit more about your idea (at least 12 characters).")
    validate_creative_idea(idea)
    title_hint = str(payload.get("title") or "").strip()
    base_slug = slugify(title_hint or " ".join(idea.split()[:6]))
    books_root.mkdir(parents=True, exist_ok=True)
    slug = base_slug
    counter = 2
    while (books_root / slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    host = str(payload.get("host") or "codex").strip().lower()
    if host not in {"codex", "claude"}:
        raise ValueError("Supported engines: codex or claude")
    language = str(payload.get("language") or "English").strip()
    author = str(payload.get("author") or "Anonymous").strip() or "Anonymous"
    preset_key = str(payload.get("preset") or "commercial").strip().lower()
    preset = FORMAT_PRESETS.get(preset_key, FORMAT_PRESETS["commercial"])
    autonomous = bool(payload.get("autonomous", True))
    auto_start = bool(payload.get("auto_start", False))
    if auto_start:
        autonomous = True
    model = str(payload.get("model") or DEFAULT_MODELS[host]).strip()
    effort = str(payload.get("effort") or "high").strip()
    raw_qt = payload.get("quality_target", 8.5)
    quality_target = max(7.0, min(9.0, float(raw_qt))) if raw_qt is not None else 8.5
    contract = {
        "chapters": int(payload.get("chapters") or preset["chapters"]),
        "min_words": int(payload.get("min_words") or preset["min_words"]),
        "max_words": int(payload.get("max_words") or preset["max_words"]),
        "quality_target": quality_target,
    } if autonomous else None
    target = books_root / slug
    config = prepare_project(
        target,
        host=host,
        idea=idea,
        language=language,
        model=model,
        effort=effort,
        autonomous=autonomous,
        author_name=author,
        autonomous_contract=contract,
    )
    if title_hint:
        # Store optional working title hint in project.json for clean display before Phase 0 finishes
        proj_path = target / ".book-genesis/project.json"
        saved = json.loads(proj_path.read_text(encoding="utf-8"))
        saved["title"] = title_hint
        proj_path.write_text(json.dumps(saved, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        config = saved

    run_state = None
    start_error = None
    if auto_start and contract is not None:
        try:
            run_state = runner.start_or_resume(slug, target.resolve(), default_contract=contract, default_models=DEFAULT_MODELS)
        except Exception as exc:
            start_error = str(exc)

    return {
        "slug": slug,
        "path": str(target.resolve()),
        "config": config,
        "runner": run_state,
        "start_error": start_error,
        "agent_prompt": build_agent_prompt(idea, language, autonomous),
        "cli_command": f'python book_genesis.py resume "{target.resolve()}"',
    }


class StudioHTTPServer(ThreadingHTTPServer):
    runner: StudioRunnerManager

    def server_close(self) -> None:
        if hasattr(self, "runner") and self.runner is not None:
            self.runner.shutdown_all()
        super().server_close()


def make_handler(
    books_root: Path,
    runner: StudioRunnerManager,
    *,
    catalyst_transport: Callable[[str, dict], dict] | None = None,
):
    app_html_path = Path(__file__).resolve().parent / "app.html"

    class StudioHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):  # noqa: A002
            return

        def _send(self, code: int, body: bytes, content_type: str, extra_headers: dict | None = None):
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            for k, v in (extra_headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, data: object):
            self._send(code, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def _read_body_json(self) -> dict:
            length = int(self.headers.get("Content-Length") or "0")
            if length == 0:
                return {}
            if length < 0 or length > 250_000:
                raise ValueError("Invalid request payload size")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("Expected JSON object")
            return payload

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            try:
                if path in {"/", "/index.html"}:
                    return self._send(HTTPStatus.OK, app_html_path.read_bytes(), "text/html; charset=utf-8")
                if path == "/api/health":
                    return self._json(HTTPStatus.OK, {
                        "ok": True,
                        "books_root": str(books_root.resolve()),
                        "hosts": detect_hosts(),
                        "presets": FORMAT_PRESETS,
                    })
                if path == "/api/books":
                    return self._json(HTTPStatus.OK, {"books": list_books(books_root, runner)})
                match = re.fullmatch(r"/api/books/([^/]+)", path)
                if match:
                    return self._json(HTTPStatus.OK, book_detail(books_root, urllib.parse.unquote(match[1]), runner))
                match = re.fullmatch(r"/api/books/([^/]+)/commercial-kit", path)
                if match:
                    slug = urllib.parse.unquote(match[1])
                    detail = book_detail(books_root, slug, runner)
                    if not detail["has_commercial_kit"]:
                        return self._json(HTTPStatus.NOT_FOUND, {"error": "Kit comercial ainda não gerado (disponível na Fase 7)."})
                    kit_md = build_commercial_kit_markdown(detail).encode("utf-8")
                    return self._send(
                        HTTPStatus.OK,
                        kit_md,
                        "text/markdown; charset=utf-8",
                        {"Content-Disposition": f'attachment; filename="kit-comercial-{slug}.md"'},
                    )
                match = re.fullmatch(r"/api/books/([^/]+)/chapters/([^/]+)", path)
                if match:
                    book_dir = _safe_book_dir(books_root, urllib.parse.unquote(match[1]))
                    filename = urllib.parse.unquote(match[2])
                    if not re.fullmatch(r"chapter-\d+\.md", filename):
                        return self._json(HTTPStatus.BAD_REQUEST, {"error": "Invalid chapter filename"})
                    chapter_path = _safe_child(book_dir, f"manuscript/chapters/{filename}")
                    if not chapter_path.is_file():
                        return self._json(HTTPStatus.NOT_FOUND, {"error": "Chapter not found"})
                    return self._json(HTTPStatus.OK, {"file": filename, "content": chapter_path.read_text(encoding="utf-8")})
                match = re.fullmatch(r"/api/books/([^/]+)/delivery/([^/]+)", path)
                if match:
                    book_dir = _safe_book_dir(books_root, urllib.parse.unquote(match[1]))
                    filename = urllib.parse.unquote(match[2])
                    if "/" in filename or "\\" in filename or filename in (".", ".."):
                        return self._json(HTTPStatus.BAD_REQUEST, {"error": "Invalid deliverable filename"})
                    file_path = _safe_child(book_dir, f"delivery/{filename}")
                    if not file_path.is_file():
                        return self._json(HTTPStatus.NOT_FOUND, {"error": "Deliverable not found"})
                    ctype = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
                    return self._send(
                        HTTPStatus.OK,
                        file_path.read_bytes(),
                        ctype,
                        {"Content-Disposition": f'attachment; filename="{file_path.name}"'},
                    )
                return self._json(HTTPStatus.NOT_FOUND, {"error": "Route not found"})
            except FileNotFoundError as exc:
                return self._json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
            except ValueError as exc:
                return self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            except Exception as exc:
                return self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

        def do_POST(self):
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            try:
                payload = self._read_body_json()
                if path == "/api/catalyze":
                    result = catalyze_idea(
                        books_root,
                        idea=str(payload.get("idea") or ""),
                        language=str(payload.get("language") or "Portuguese (Brazil)"),
                        host=str(payload.get("host") or "codex"),
                        model=payload.get("model"),
                        default_models=DEFAULT_MODELS,
                        transport=catalyst_transport,
                    )
                    return self._json(HTTPStatus.OK, result)
                if path == "/api/books":
                    created = create_book(books_root, payload, runner)
                    return self._json(HTTPStatus.CREATED, created)
                match = re.fullmatch(r"/api/books/([^/]+)/run", path)
                if match:
                    slug = urllib.parse.unquote(match[1])
                    book_dir = _safe_book_dir(books_root, slug)
                    if not book_dir.is_dir():
                        return self._json(HTTPStatus.NOT_FOUND, {"error": "Book not found"})
                    preset = FORMAT_PRESETS["commercial"]
                    default_contract = {
                        "chapters": preset["chapters"],
                        "min_words": preset["min_words"],
                        "max_words": preset["max_words"],
                        "quality_target": 8.5,
                    }
                    state = runner.start_or_resume(
                        slug,
                        book_dir,
                        default_contract=default_contract,
                        default_models=DEFAULT_MODELS,
                        recover_stale_lock=bool(payload.get("recover_stale_lock", False)),
                    )
                    return self._json(HTTPStatus.OK, {"ok": True, "runner": state})
                match = re.fullmatch(r"/api/books/([^/]+)/stop", path)
                if match:
                    slug = urllib.parse.unquote(match[1])
                    book_dir = _safe_book_dir(books_root, slug)
                    if not book_dir.is_dir():
                        return self._json(HTTPStatus.NOT_FOUND, {"error": "Book not found"})
                    state = runner.stop(slug, book_dir)
                    return self._json(HTTPStatus.OK, {"ok": True, "runner": state})
                return self._json(HTTPStatus.NOT_FOUND, {"error": "Route not found"})
            except FileNotFoundError as exc:
                return self._json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
            except ValueError as exc:
                code = HTTPStatus.CONFLICT if str(exc).startswith("STALE_LOCK:") else HTTPStatus.BAD_REQUEST
                return self._json(code, {"error": str(exc)})
            except RuntimeError as exc:
                return self._json(HTTPStatus.BAD_GATEWAY, {"error": str(exc)})
            except Exception as exc:
                return self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

    return StudioHandler


def create_server(
    books_root: Path,
    host: str = "127.0.0.1",
    port: int = 4173,
    *,
    command_builder: Callable[[Path], list[str]] | None = None,
    catalyst_transport: Callable[[str, dict], dict] | None = None,
) -> StudioHTTPServer:
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("Book Genesis Studio binds to localhost only for safety")
    runner = StudioRunnerManager(books_root, command_builder=command_builder)
    server = StudioHTTPServer((host, port), make_handler(books_root, runner, catalyst_transport=catalyst_transport))
    server.runner = runner
    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Start the Book Genesis Studio local web app.")
    parser.add_argument("--books-dir", type=Path, default=ROOT / "books", help="Directory where book folders live.")
    parser.add_argument("--port", type=int, default=4173, help="Local TCP port (default: 4173).")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the browser automatically.")
    args = parser.parse_args(argv)
    server = create_server(args.books_dir, port=args.port)
    url = f"http://127.0.0.1:{server.server_address[1]}"
    print(f"Book Genesis Studio running at {url}", flush=True)
    print(f"Books workspace: {args.books_dir.resolve()}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBook Genesis Studio stopped.", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
