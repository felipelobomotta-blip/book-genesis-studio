"""Tests for Book Genesis Studio end-to-end web generator (Catalyst, Runner, UI, Kit)."""
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from studio.server import create_server


def _fake_catalyst_transport(packet: str, _schema: dict) -> dict:
    assert "shower idea" in packet.lower()
    return {
        "directions": [
            {
                "id": i,
                "angle_label": f"Ângulo Comercial {i}",
                "title": f"O Acorde Secreto {i}",
                "genre": "Thriller Psicológico",
                "pitch_15s": "Um afinador descobre uma confissão gravada num piano esquecido.",
                "protagonist_and_wound": "Artur, ouvido absoluto e culpa antiga pelo sumiço da irmã.",
                "tropes_and_twist": "Fita perdida + cidade histórica, mas a mensagem foi deixada para ele.",
                "opening_10pct_hook": "Na página 3, a corda dó sustenido revela uma fita colada no tampo.",
                "shareability_peak": "O dilema final entre entregar a fita ou proteger quem ainda vive.",
                "enriched_brief": (
                    f"Versão {i}: Artur é um afinador de pianos aposentado em Ouro Preto que encontra "
                    "uma fita cassete escondida dentro do último piano tocado por uma cantora desaparecida."
                ),
            }
            for i in (1, 2, 3)
        ]
    }


class StudioServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.books = Path(self.temp.name) / "books"
        self.worker_script = Path(self.temp.name) / "fake_worker.py"
        self.worker_script.write_text(
            "import json, pathlib, sys, time\n"
            "book = pathlib.Path(sys.argv[1])\n"
            "print('Phase 0 started', flush=True)\n"
            "(book / 'manuscript/chapters').mkdir(parents=True, exist_ok=True)\n"
            "(book / 'artifacts').mkdir(parents=True, exist_ok=True)\n"
            "(book / 'manuscript/chapters/chapter-01.md').write_text('# Capítulo 1: O Piano\\n\\n— Escute — disse Artur.\\n', encoding='utf-8')\n"
            "(book / 'artifacts/12-editorial-package.md').write_text('# Pacote Editorial\\n\\nLogline comercial em PT-BR.\\n', encoding='utf-8')\n"
            "(book / 'artifacts/13-positioning.md').write_text("
            "'# Posicionamento\\n\\n## Simulated hook test\\n\\n' + json.dumps({"
            "'ranking': [2, 1, 3],"
            "'options': [{'id': 1, 'title': 'A', 'logline': 'L1', 'blurb': 'B1'}, {'id': 2, 'title': 'Campeao', 'logline': 'L2', 'blurb': 'B2'}, {'id': 3, 'title': 'C', 'logline': 'L3', 'blurb': 'B3'}],"
            "'readers': [{'reader': 'Lena', 'options': [{'id': 1, 'click': False, 'buy': False, 'keep_reading': False, 'reason': 'ok'}, {'id': 2, 'click': True, 'buy': True, 'keep_reading': True, 'reason': 'forte'}, {'id': 3, 'click': False, 'buy': False, 'keep_reading': False, 'reason': 'ok'}]}]"
            "}) + '\\n', encoding='utf-8')\n"
            "if '--hang' in sys.argv:\n"
            "    time.sleep(30)\n"
            "print('Finished cleanly', flush=True)\n",
            encoding="utf-8",
        )
        self.hang_mode = False

        def cmd_builder(book_dir: Path) -> list[str]:
            extra = ["--hang"] if self.hang_mode else []
            return [sys.executable, "-u", str(self.worker_script), str(book_dir), *extra]

        self.server = create_server(
            self.books,
            port=0,
            command_builder=cmd_builder,
            catalyst_transport=_fake_catalyst_transport,
        )
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def _get(self, path: str):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}") as resp:
            return resp.status, resp.headers.get("Content-Type", ""), resp.read()

    def _post(self, path: str, payload: dict):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def test_serves_ui_catalyzes_idea_runs_background_generator_and_exports_commercial_kit(self):
        status, ctype, html = self._get("/")
        self.assertEqual(200, status)
        self.assertIn("text/html", ctype)
        self.assertIn("shower idea", html.decode("utf-8").lower())

        status, _, body = self._get("/api/health")
        self.assertEqual(200, status)
        health = json.loads(body.decode("utf-8"))
        self.assertTrue(health["ok"])
        self.assertIn("commercial", health["presets"])

        # 1. Catalyst turns raw shower idea into 3 validated commercial directions
        status, cat = self._post("/api/catalyze", {
            "idea": "Um afinador de pianos encontra uma mensagem secreta em uma fita cassete antiga.",
            "language": "Portuguese (Brazil)",
            "host": "codex",
        })
        self.assertEqual(200, status)
        self.assertEqual(3, len(cat["directions"]))
        self.assertEqual("O Acorde Secreto 1", cat["directions"][0]["title"])

        # 2. Reject score-target leakage in creative idea
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post("/api/books", {
                "idea": "Escreva um thriller com nota 95/100 garantida.",
                "language": "Portuguese (Brazil)",
            })
        self.assertEqual(400, ctx.exception.code)

        # 3. Guided prompt mode preserved when autonomous=False
        status, guided = self._post("/api/books", {
            "idea": cat["directions"][0]["enriched_brief"],
            "title": "O Ultimo Acorde",
            "author": "Felipe Lobo",
            "language": "Portuguese (Brazil)",
            "preset": "pilot",
            "host": "codex",
            "autonomous": False,
        })
        self.assertEqual(201, status)
        self.assertIn("3 direções criativas", guided["agent_prompt"])

        # 4. 1-Click Create & Auto-Start background generation
        status, created = self._post("/api/books", {
            "idea": cat["directions"][1]["enriched_brief"],
            "title": "O Acorde Secreto",
            "author": "Felipe Lobo",
            "language": "Portuguese (Brazil)",
            "preset": "pilot",
            "host": "codex",
            "auto_start": True,
        })
        self.assertEqual(201, status)
        slug = created["slug"]
        book_dir = Path(created["path"])

        # Wait up to 5s for fast background worker to complete
        deadline = time.monotonic() + 5.0
        detail = None
        while time.monotonic() < deadline:
            _, _, raw = self._get(f"/api/books/{slug}")
            detail = json.loads(raw.decode("utf-8"))
            if not detail["runner"]["running"] and detail["chapters"]:
                break
            time.sleep(0.1)

        self.assertIsNotNone(detail)
        self.assertEqual(1, len(detail["chapters"]))
        self.assertEqual("pt-br", detail["prose_diagnostics"]["profile"])
        self.assertEqual(0, detail["prose_diagnostics"]["chapters"][0]["narration_dashes"])
        self.assertTrue(detail["has_commercial_kit"])
        self.assertEqual([2, 1, 3], detail["hook_test"]["ranking"])

        # Download Commercial & BookTok Kit
        kit_status, kit_ctype, kit_bytes = self._get(f"/api/books/{slug}/commercial-kit")
        self.assertEqual(200, kit_status)
        self.assertIn("text/markdown", kit_ctype)
        self.assertIn("Logline comercial em PT-BR", kit_bytes.decode("utf-8"))

        # Verify EPUB download & chapter reading
        deliv = book_dir / "delivery"
        deliv.mkdir(parents=True, exist_ok=True)
        (deliv / "o-acorde-secreto.epub").write_bytes(b"PK-fake-epub")
        _, _, ch_raw = self._get(f"/api/books/{slug}/chapters/chapter-01.md")
        self.assertIn("Escute", json.loads(ch_raw.decode("utf-8"))["content"])
        _, _, epub_bytes = self._get(f"/api/books/{slug}/delivery/o-acorde-secreto.epub")
        self.assertEqual(b"PK-fake-epub", epub_bytes)

        # 5. Pause / Stop active background process cleanly
        self.hang_mode = True
        _, started = self._post(f"/api/books/{slug}/run", {})
        self.assertTrue(started["runner"]["running"])
        _, stopped = self._post(f"/api/books/{slug}/stop", {})
        self.assertFalse(stopped["runner"]["running"])
        self.assertEqual("paused", stopped["runner"]["state"])

        # 6. Path traversal must be rejected
        for bad in (
            "/api/books/.catalyst-runs",
            "/api/books/..%2Fsecret",
            f"/api/books/{slug}/chapters/..%2Fproject.json",
            f"/api/books/{slug}/delivery/..%2Fproject.json",
        ):
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                self._get(bad)
            self.assertIn(ctx.exception.code, (400, 404))


if __name__ == "__main__":
    unittest.main()
