"""Regressions for Frente 1 quality-elevation upgrades.

Verifies language-aware machine-prose tells (including PT-BR travessão
protection), deterministic prose telemetry, full foundation/opening context in
writer and editor packets, bounded Chapter 1 opening checkpoint revision,
score-blind craft-risk prioritization, and book-specific reader lenses.
"""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/book-genesis"
sys.path.insert(0, str(SKILL / "scripts"))

from autonomous_book import BookWorkflow, _chapter_emotional_curve_view
from craft_context import language_tells, tells_language_code
from prose_diagnostics import analyze_chapter, analyze_manuscript
from workflow_state import encoded, freeze, read_json
from test_autonomous_workflow import COMMAND, fixture_response, receipt_transport


class ProseDiagnosticsTests(unittest.TestCase):
    def test_pt_br_dialogue_travessoes_are_excluded_from_narration_dash_count(self):
        chapter = (
            "# Capítulo 1: A Carta\n\n"
            "— Você chegou cedo — disse Marta, fechando a janela. — Entra.\n\n"
            "— Não vim ficar — respondeu Lucas. — Só devolvo o envelope.\n\n"
            "A chuva batia no vidro da varanda. Ele pôs o papel seco em cima da mesa.\n"
        )
        metrics = analyze_chapter("chapter-01.md", chapter, "Português (Brasil)")
        self.assertTrue(metrics["supported"])
        self.assertEqual("pt-br", metrics["language_profile"])
        self.assertEqual(0, metrics["narration_dashes"])
        self.assertGreater(metrics["dialogue_words"], 0)
        self.assertNotIn("narration_dashes", metrics["candidates_above_default_ceiling"])

    def test_pt_br_detects_narration_tells_and_moralizing_ending(self):
        chapter = (
            "# Capítulo 2\n\n"
            "A sala estava quieta — quieta demais — e o relógio — parado desde maio — marcava seis.\n\n"
            "Não era medo; era cansaço. Não houve resposta. Não houve eco.\n\n"
            "Ele sentiu uma onda de tristeza ao olhar o retrato, andando, olhando, pensando no passado.\n\n"
            "Afinal, talvez fosse isso: algumas portas só se abrem por dentro.\n"
        )
        metrics = analyze_chapter("chapter-02.md", chapter, "pt-BR")
        self.assertGreater(metrics["narration_dashes"], 2)
        self.assertEqual(1, metrics["paragraphs_over_2_narration_dashes"])
        self.assertEqual(1, metrics["corrective_negation_semicolon"])
        self.assertEqual(2, metrics["nao_houve_count"])
        self.assertEqual(1, metrics["emotion_label_candidates"])
        self.assertEqual(1, metrics["gerund_chain_sentences"])
        self.assertTrue(metrics["ending_moral_candidate"])
        self.assertIn("narration_dashes", metrics["candidates_above_default_ceiling"])
        self.assertIn("corrective_negation", metrics["candidates_above_default_ceiling"])
        self.assertIn("nao_houve", metrics["candidates_above_default_ceiling"])
        self.assertIn("moral_at_the_door_candidate", metrics["candidates_above_default_ceiling"])

    def test_unsupported_language_never_inherits_english_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            ch = Path(tmp) / "chapter-01.md"
            ch.write_text("# Capítulo 1\n\n— Hola — dijo Ana.\n", encoding="utf-8")
            report = analyze_manuscript([ch], "Español")
            self.assertFalse(report["supported"])
            self.assertIsNone(report["profile"])
            self.assertIn("Do not apply English", report["interpretation"])


class QualityElevationWorkflowTests(unittest.TestCase):
    def test_pt_br_workflow_routes_pt_br_tells_and_book_specific_lenses_and_full_craft_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze(root / ".book-genesis/project.json", encoded({
                "host": "codex", "collaboration": "autonomous", "author_name": "QA",
                "model": "exact-test-model", "effort": "high",
                "idea": "Uma carta desaparecida muda o destino de duas irmãs em Minas.",
                "language": "Brazilian Portuguese",
                "autonomous_contract": {"chapters": 2, "min_words": 240, "max_words": 600, "quality_target": 8.5},
            }))
            freeze(root / ".book-genesis/skills/.book-genesis-install.json", b"{}")
            packets = {}

            def generate(call_id, packet, schema, book):
                packets[call_id] = packet
                data = fixture_response(call_id, packet, schema, book)
                if call_id.startswith("wf-intake") and "files" in data:
                    data["files"]["artifacts/01-market-map.md"] = (
                        "# Mapa de Mercado\n\n## Reader lenses\n"
                        "- Primary: Leitora fiel de drama familiar brasileiro que busca voz autêntica.\n"
                        "- Hostile: Crítico cético que abandona clichês melodramáticos na página 2.\n"
                        "- Adjacent: Leitor de mistério psicológico curioso por segredos domésticos.\n"
                    )
                if call_id.startswith("wf-measure-0-rubric") and "dimensions" in data:
                    # Make Voice and Emotion clearly the lowest dimensions so ordering is testable.
                    for dim in data["dimensions"]:
                        if dim["name"] == "Voice":
                            dim["score"] = 7.2
                        elif dim["name"] == "Emotion":
                            dim["score"] = 7.6
                        else:
                            dim["score"] = 9.0
                return data

            workflow = BookWorkflow(root, COMMAND, chapters=2, min_words=240, max_words=600,
                                    transport=receipt_transport(generate))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, workflow.run())

            # 1. PT-BR tells routed to panel, audit and rubric (never hardcoded EN tells)
            self.assertEqual("pt-br", tells_language_code("Brazilian Portuguese"))
            self.assertEqual("patterns/ai-tells-pt-br.md", language_tells("Brazilian Portuguese"))
            for key in ("wf-draft-check-01-primary-1", "wf-audit-original-1", "wf-measure-0-rubric-1-1"):
                self.assertIn("Brazilian Portuguese", packets[key])
                self.assertIn("travessão", packets[key])
                self.assertNotIn("Machine-prose tells: English", packets[key])

            # 2. Book-specific reader lenses reach the blind panel and comparison packets
            self.assertIn("Leitora fiel de drama familiar brasileiro", packets["wf-draft-check-01-primary-1"])
            self.assertIn("Crítico cético que abandona clichês melodramáticos", packets["wf-draft-check-01-hostile-1"])
            self.assertIn("Leitor de mistério psicológico", packets["wf-draft-check-01-adjacent-1"])

            # 3. Writer receives theme, emotional curve and (for chapter 1) opening strategy
            ch1_writer = json.loads(packets["wf-draft-01-1"].split("\n\n", 1)[1])
            self.assertIn("theme", ch1_writer)
            self.assertIn("emotional_curve", ch1_writer)
            self.assertIn("opening_strategy", ch1_writer)
            ch2_writer = json.loads(packets["wf-draft-02-1"].split("\n\n", 1)[1])
            self.assertIn("theme", ch2_writer)
            self.assertIn("emotional_curve", ch2_writer)
            self.assertNotIn("opening_strategy", ch2_writer)

            # 4. Audit receives deterministic prose diagnostics
            self.assertIn("controller/prose-diagnostics.json", packets["wf-audit-original-1"])
            self.assertIn("artifacts/06-emotional-curve.md", packets["wf-audit-original-1"])

            # 5. Revision planner receives score-blind priority ordering with Voice/Emotion first and no numeric scores
            plan_context = json.loads(packets["wf-revision-plan-1-1"].rsplit("\n\n", 1)[1])
            obs = plan_context["craft_observations"]
            self.assertEqual("Voice", obs[0]["dimension"])
            self.assertEqual("highest_craft_risk", obs[0]["priority"])
            self.assertNotIn("7.2", json.dumps(obs))
            self.assertNotIn("quality_target", packets["wf-revision-plan-1-1"])

            # 6. Creative revision editor receives theme, emotional curve and opening strategy for chapter 1
            editor_ctx = json.loads(packets["wf-revision-1-c01-1"].rsplit("\n\n", 1)[1])
            self.assertIn("theme", editor_ctx)
            self.assertIn("emotional_curve", editor_ctx)
            self.assertIn("opening_strategy", editor_ctx)

            # 7. Phase 7 package and simulated Hook Test use book language and book-specific reader lenses
            self.assertIn("Write editorial_package, positioning and all three options in Brazilian Portuguese.", packets["wf-editorial-package-1"])
            self.assertIn("Leitora fiel de drama familiar brasileiro", packets["wf-hook-primary-1"])
            self.assertIn("written in Brazilian Portuguese", packets["wf-hook-primary-1"])

    def test_chapter_emotional_curve_view_hides_future_chapters_before_ending(self):
        curve = (
            "# Emotional curve\n\n"
            "| Ch | Dominant | Anchor |\n"
            "|---|---|---|\n"
            "| 1 | Curiosity | Ring in soap |\n"
            "| 2 | Dread | Cold file room |\n"
            "| 3 | Break | Secret killer revealed |\n\n"
            "High-impact beats: Ch 3 twist.\n"
            "Residue: Haunting silence.\n"
        )
        ch1_view = _chapter_emotional_curve_view(curve, 1, 3)
        self.assertIn("Ring in soap", ch1_view)
        self.assertNotIn("Cold file room", ch1_view)
        self.assertNotIn("Secret killer revealed", ch1_view)
        self.assertNotIn("Ch 3 twist", ch1_view)
        full_view = _chapter_emotional_curve_view(curve, 3, 3)
        self.assertIn("Secret killer revealed", full_view)
        self.assertIn("Residue: Haunting silence.", full_view)

    def test_failed_chapter_1_opening_checkpoint_runs_bounded_revision_and_promotes_before_chapter_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            freeze(root / ".book-genesis/project.json", encoded({
                "host": "codex", "collaboration": "autonomous", "author_name": "QA",
                "model": "exact-test-model", "effort": "high",
                "idea": "A piano tuner finds a coded recording.", "language": "English",
                "autonomous_contract": {"chapters": 2, "min_words": 240, "max_words": 600, "quality_target": 8.5},
            }))
            freeze(root / ".book-genesis/skills/.book-genesis-install.json", b"{}")
            seen_calls = []

            def generate(call_id, packet, schema, book):
                seen_calls.append(call_id)
                # Comparison readers prefer the revised chapter 1 (handle before fixture_response,
                # whose hardcoded comparison lookup expects work/comparisons/revision-1-c01/).
                if call_id.startswith("wf-opening-revision-c01-") and "compare" in schema["properties"]:
                    manifest = read_json(book / "work/comparisons/opening-revision-c01/manifest.private.json")
                    reader = schema["properties"]["reader"]["enum"][0]
                    assignment = next(row for row in manifest["readers"] if row["reader"] == reader)
                    ids = schema["$defs"]["passageId"]["enum"]
                    ev = {"passage_id": ids[0], "reason": "Stronger immediate hook."}
                    return {
                        "schema_version": 3,
                        "catalog_sha256": schema["properties"]["catalog_sha256"]["enum"][0],
                        "reader": reader,
                        "turn_page": "yes",
                        "stopped_at": None,
                        "why_stopped": None,
                        "remember_tomorrow": [ev],
                        "confused_by": [],
                        "flags": [],
                        "strongest_passage": ev,
                        "weakest_passage": ev,
                        "machine_tells": [],
                        "felt": {"emotion": "intrigue", "reason": "Hook lands immediately."},
                        "confidence": "medium",
                        "compare": next(label for label, identity in assignment["mapping"].items() if identity == "candidate"),
                    }
                data = fixture_response(call_id, packet, schema, book)
                # Force initial chapter 1 opening panel to fail (0/4 turn_page)
                if call_id.startswith("wf-draft-check-01-") and "revised" not in call_id and "turn_page" in schema["properties"]:
                    ids = schema["$defs"]["passageId"]["enum"]
                    data["turn_page"] = "no"
                    data["stopped_at"] = {"passage_id": ids[0]}
                    data["why_stopped"] = {"reason": "Opening paragraph delays the concrete hook."}
                    data["flags"] = [{"flag": "slow_start", "passage_id": ids[0]}]
                # Opening revision produces distinct improved prose
                if call_id.startswith("wf-opening-revision-c01") and "prose" in data:
                    data["prose"] = (
                        "# Chapter 1\n\n"
                        + "The piano wire snapped before the tape finished playing. " * 18
                        + "\n\n" + "Ada pressed rewind and heard her father's voice. " * 16
                    )
                return data

            workflow = BookWorkflow(root, COMMAND, chapters=2, min_words=240, max_words=600,
                                    transport=receipt_transport(generate))
            with redirect_stdout(io.StringIO()):
                workflow.planning()
                workflow.draft()

            # Verify opening revision ran, promoted chapter 1, refreshed panel, and chapter 2 saw the revised chapter 1!
            self.assertTrue(any(c.startswith("wf-opening-revision-c01") for c in seen_calls))
            self.assertTrue(any(c.startswith("wf-draft-check-01-revised-") for c in seen_calls))
            ch1_text = (root / "manuscript/chapters/chapter-01.md").read_text(encoding="utf-8")
            self.assertIn("piano wire snapped", ch1_text)
            outcome = read_json(root / "evaluations/decisions/opening-revision-c01-outcome.json")
            self.assertEqual("promote", outcome["decision"])


if __name__ == "__main__":
    unittest.main()
