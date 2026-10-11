"""Native envelope, subscription isolation and full-controller regressions.

Subprocess fixtures are synthetic; they make no external model calls.
"""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/book-genesis/scripts"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS))
from launcher import cli
from launcher.autonomous import controlled_command
from autonomous_book import BookWorkflow
from workflow_state import encoded, freeze, read_json, verify_execution
from verify_book import verify_book
from test_autonomous_workflow import COMMAND, fixture_response, receipt_transport


class NativeClaudeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.native = self.root / "fake_claude.py"
        self.native.write_text('''import json, os, sys
from pathlib import Path
root = Path(__file__).parent
settings = json.loads((root / "fixture.json").read_text())
args = sys.argv[1:]
if args[-2:] == ["auth", "status"]:
    print(json.dumps({"loggedIn": True, "authMethod": settings.get("auth", "claude.ai"), "apiProvider": "firstParty"}))
    raise SystemExit(0)
assert "--restricted" in args and "--strict-mcp-config" in args
assert args[args.index("--tools") + 1] == ""
assert "--bare" not in args and "--dangerously-skip-permissions" not in args
assert "--fallback-model" not in args and "--disable-slash-commands" in args
assert "--no-session-persistence" in args and args[args.index("--setting-sources") + 1] == ""
packet = sys.stdin.buffer.read().decode("utf-8")
(root / "received.json").write_text(json.dumps({"argv": args, "packet": packet, "effort_env": os.environ.get("CLAUDE_CODE_EFFORT_LEVEL"), "tz": os.environ.get("TZ")}), encoding="utf-8")
model = settings.get("model", args[args.index("--model") + 1])
payload = settings.get("payload", '{"text":"café — 星"}')
reply = {"type":"result", "subtype":"success", "is_error": settings.get("is_error", False), "result":payload, "modelUsage":{model:{"inputTokens":1,"outputTokens":1}}}
reply.update(settings.get("envelope", {}))
if "structured_output" in settings:
    reply["structured_output"] = settings["structured_output"]
sys.stdout.buffer.write(json.dumps(reply, ensure_ascii=False).encode("utf-8"))
sys.stdout.buffer.flush()
raise SystemExit(settings.get("exit", 0))
''', encoding="utf-8")
        self.prefix = [sys.executable, str(self.native)]
        self.settings = self.root / "fixture.json"
        self.settings.write_text("{}", encoding="utf-8")
        self.schema = self.root / "schema.json"
        self.schema.write_text(json.dumps({"type": "object", "description": "large " * 12000,
            "properties": {"text": {"type": "string"}}, "required": ["text"], "additionalProperties": False}), encoding="utf-8")
        self.output = self.root / "response"

    def run_bridge(self, env_overrides=None, **settings):
        self.settings.write_text(json.dumps(settings), encoding="utf-8")
        command = [sys.executable, str(SCRIPTS / "native_claude.py"), "--native-command-json", json.dumps(self.prefix),
            "--model", "claude-opus-exact-test", "--effort", "medium", "--output-schema", str(self.schema),
            "-o", str(self.output), "-"]
        env = {**os.environ, "PYTHONIOENCODING": "cp1252", "CLAUDE_CODE_EFFORT_LEVEL": "max"}
        for key in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY"):
            env.pop(key, None)
        env.update(env_overrides or {})
        return subprocess.run(command, input="Scoped café 星 packet".encode("utf-8"), capture_output=True,
            env=env, cwd=self.root, timeout=15)

    def test_large_schema_unicode_and_original_envelope_survive_real_subprocess_transport(self):
        result = self.run_bridge()
        self.assertEqual(0, result.returncode, result.stderr.decode("utf-8"))
        self.assertEqual('{"text":"café — 星"}'.encode("utf-8"), self.output.read_bytes())
        envelope = json.loads(result.stdout)
        self.assertEqual({"claude-opus-exact-test"}, set(envelope["modelUsage"]))
        received = read_json(self.root / "received.json")
        self.assertTrue(received["packet"].startswith("Scoped café 星 packet"))
        self.assertGreater(len(received["packet"]), 32768)
        self.assertLess(sum(map(len, received["argv"])), 2000)
        native_schema = json.loads(received["argv"][received["argv"].index("--json-schema") + 1])
        self.assertNotIn("description", native_schema)
        self.assertEqual(["text"], native_schema["required"])
        self.assertEqual("medium", received["effort_env"])
        self.assertEqual(os.environ.get("TZ"), received["tz"])
        self.assertIn(b"model: claude-opus-exact-test\nreasoning effort: medium\n", result.stderr)

    def test_api_auth_is_rejected_before_model_dispatch(self):
        result = self.run_bridge(auth="apiKey")
        self.assertNotEqual(0, result.returncode)
        self.assertFalse((self.root / "received.json").exists())
        self.assertFalse(self.output.exists())
        self.assertIn(b"no API or provider fallback", result.stderr)

    def test_single_native_json_fence_preserves_exact_document_and_original_envelope(self):
        document = '{\r\n  "verdict": "block", "text": "café — 星", "findings": ["A real unresolved defect."]\r\n}'
        payload = "```json\r\n" + document + "\r\n```"
        result = self.run_bridge(payload=payload)
        self.assertEqual(0, result.returncode, result.stderr.decode("utf-8"))
        self.assertEqual(document.encode("utf-8"), self.output.read_bytes())
        self.assertEqual(payload, json.loads(result.stdout)["result"])
        self.assertEqual("block", json.loads(self.output.read_bytes())["verdict"])
        self.assertIn(b"response presentation: single_json_fence", result.stderr)

    def test_ambiguous_or_non_json_fences_are_not_salvaged(self):
        for payload in ('```json\n{"text":"one"}\n```\n```json\n{"text":"two"}\n```',
                        '```json\n{"text":"one"}\n```\nAn extra explanation.',
                        '```json\n["not an object"]\n```',
                        '```json\n{"text":"unfinished"\n```'):
            with self.subTest(payload=payload):
                result = self.run_bridge(payload=payload)
                self.assertNotEqual(0, result.returncode)
                self.assertFalse(self.output.exists())
                self.assertEqual(payload, json.loads(result.stdout)["result"])

    def test_fences_inside_story_strings_are_preserved_as_content(self):
        content = {"prose": "# A sign\n\nThe sign read ```json and café.\n\nShe said, ‘No.’", "continuity_delta": "She refuses."}
        document = json.dumps(content, ensure_ascii=False, indent=2)
        result = self.run_bridge(payload="```json\n" + document + "\n```")
        self.assertEqual(0, result.returncode, result.stderr.decode("utf-8"))
        self.assertEqual(document.encode("utf-8"), self.output.read_bytes())
        self.assertEqual(content, json.loads(self.output.read_bytes()))

    def test_decoding_presentation_does_not_bypass_response_shape_validation(self):
        from workflow_roles import validate_json
        result = self.run_bridge(payload='```json\n{"verdict":"pass","invented_field":"not an approval"}\n```')
        self.assertEqual(0, result.returncode)
        self.assertFalse(validate_json(self.output, read_json(self.schema))["valid"])

    def test_explicit_api_environment_cannot_silently_override_subscription_auth(self):
        result = self.run_bridge(env_overrides={"ANTHROPIC_API_KEY": "synthetic-not-a-credential"})
        self.assertNotEqual(0, result.returncode)
        self.assertFalse((self.root / "received.json").exists())
        self.assertFalse(self.output.exists())
        self.assertIn(b"made no model call", result.stderr)

    def test_wrong_native_model_is_not_accepted_even_with_valid_response_text(self):
        result = self.run_bridge(model="some-other-model")
        self.assertNotEqual(0, result.returncode)
        self.assertFalse(self.output.exists())
        self.assertIn("some-other-model", json.loads(result.stdout)["modelUsage"])

    def test_failed_native_envelope_preserves_original_and_cannot_publish(self):
        result = self.run_bridge(is_error=True, exit=1)
        self.assertNotEqual(0, result.returncode)
        self.assertTrue(json.loads(result.stdout)["is_error"])
        self.assertFalse(self.output.exists())

    def test_existing_output_is_preserved_without_dispatch(self):
        self.output.write_bytes(b"original")
        result = self.run_bridge()
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(b"original", self.output.read_bytes())
        self.assertFalse((self.root / "received.json").exists())

    def test_zero_usage_provider_error_reports_actual_reason_before_identity_check(self):
        result = self.run_bridge(envelope={"is_error": True, "modelUsage": {}, "api_error_status": 429,
            "result": "You've hit your session limit · resets 7:30am (America/Sao_Paulo)"})
        self.assertEqual(1, result.returncode)
        self.assertIn(b"session limit", result.stderr)
        self.assertNotIn(b"did not verify the exact selected model", result.stderr)
        self.assertFalse(self.output.exists())

    def test_success_without_usage_is_still_rejected(self):
        result = self.run_bridge(envelope={"is_error": False, "modelUsage": {}})
        self.assertEqual(1, result.returncode)
        self.assertIn(b"did not verify the exact selected model", result.stderr)
        self.assertFalse(self.output.exists())

    def test_proven_utc_quota_has_distinct_exit_and_preserves_original_refusal(self):
        from datetime import datetime, timedelta, timezone
        from provider_wait import MARKER, WAIT_EXIT
        reset = datetime.now(timezone.utc) + timedelta(hours=1)
        clock = f"{reset.hour % 12 or 12}:{reset.minute:02d}{'am' if reset.hour < 12 else 'pm'}"
        envelope = {"is_error": True, "modelUsage": {}, "api_error_status": 429,
            "usage": {key: 0 for key in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")},
            "result": f"You've hit your session limit · resets {clock} (UTC)"}
        result = self.run_bridge(envelope=envelope)
        self.assertEqual(WAIT_EXIT, result.returncode, result.stderr.decode("utf-8"))
        self.assertIn(MARKER.encode(), result.stderr)
        self.assertEqual(envelope["result"], json.loads(result.stdout)["result"])
        self.assertNotIn(b"model evidence: native modelUsage", result.stderr)
        self.assertFalse(self.output.exists())

    def test_capability_check_and_changing_alias_block_unsafe_dispatch(self):
        flags = "--restricted --tools --strict-mcp-config --disable-slash-commands --no-session-persistence --setting-sources --model --effort --output-format --json-schema --print"
        with patch("launcher.autonomous.subprocess.run", return_value=subprocess.CompletedProcess([], 0, flags, "")):
            command = controlled_command(self.prefix, model="claude-opus-exact-test", effort="medium", host="claude", bridge=SCRIPTS / "native_claude.py")
            self.assertEqual(["-o", "{output}", "-"], command["argv"][-3:])
            self.assertNotIn("--bare", command["argv"])
            with self.assertRaisesRegex(ValueError, "exact model"):
                controlled_command(self.prefix, model="opus", effort="medium", host="claude", bridge=SCRIPTS / "native_claude.py")
        with patch("launcher.autonomous.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "old CLI", "")):
            with self.assertRaisesRegex(ValueError, "restricted mode"):
                controlled_command(self.prefix, model="claude-opus-exact-test", effort="medium", host="claude", bridge=SCRIPTS / "native_claude.py")

    def test_headless_new_claude_records_a_controlled_contract(self):
        project = self.root / "book"
        with patch.object(cli, "_has_terminal", return_value=False), patch.object(cli, "find_native", return_value=self.prefix), redirect_stdout(io.StringIO()):
            code = cli.main(["new", str(project), "--host", "claude", "--model", "claude-opus-exact-test", "--effort", "medium",
                             "--author", "QA", "--idea", "A stolen letter returned.", "--autonomous", "--prepare-only"])
        self.assertEqual(0, code)
        config = cli.read_project(project)
        self.assertEqual("claude", config["host"])
        self.assertEqual(12, config["autonomous_contract"]["chapters"])

    def test_claude_contract_completes_same_pipeline_exports_and_no_call_resume(self):
        root = self.root / "controller"
        freeze(root / ".book-genesis/project.json", encoded({"host": "claude", "collaboration": "autonomous",
            "author_name": "QA", "model": "exact-test-model", "effort": "high", "idea": "A stolen letter returned.", "language": "English",
            "autonomous_contract": {"chapters": 2, "min_words": 240, "max_words": 600, "quality_target": 8.5}}))
        freeze(root / ".book-genesis/skills/.book-genesis-install.json", b'{}')
        calls = []
        def respond(*args):
            calls.append(args[0])
            return fixture_response(*args)
        kwargs = dict(chapters=2, min_words=240, max_words=600, transport=receipt_transport(respond))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, BookWorkflow(root, COMMAND, **kwargs).run())
            call_count = len(calls)
            self.assertEqual(0, BookWorkflow(root, COMMAND, **kwargs).run())
        self.assertEqual(call_count, len(calls))
        self.assertEqual(8, verify_execution(root, required_phase=8)["phase"])
        self.assertEqual("delivered", verify_book(root, "evaluations/final-reader-index.json")["delivery"]["status"])

    def test_native_structured_object_preserves_values_and_original_envelope(self):
        value = {"verdict": "block", "findings": ["A real unresolved defect."], "text": "café — 星", "score": 6.3}
        result = self.run_bridge(structured_output=value, payload="A human-readable summary, not the role document.")
        self.assertEqual(0, result.returncode, result.stderr.decode("utf-8"))
        self.assertEqual(value, json.loads(self.output.read_bytes()))
        self.assertEqual(value, json.loads(result.stdout)["structured_output"])
        self.assertIn(b"response presentation: native_structured_output", result.stderr)

    def test_invalid_structured_object_cannot_fall_back_to_a_positive_text_result(self):
        result = self.run_bridge(structured_output=None, payload='{"verdict":"pass"}')
        self.assertNotEqual(0, result.returncode)
        self.assertFalse(self.output.exists())
        self.assertIn("structured_output", json.loads(result.stdout))

    def test_compact_schema_keeps_real_field_names_and_requires_host_source_validation(self):
        from native_claude import compact_native_schema
        from workflow_roles import validate_json
        original = {"type": "object", "description": "Long annotation " * 1000,
            "properties": {"description": {"type": "string", "description": "Field guidance"},
                           "passage_id": {"type": "string", "enum": [f"c01p{n:04d}" for n in range(1, 300)]}},
            "required": ["description", "passage_id"], "additionalProperties": False}
        reduced = compact_native_schema(original)
        self.assertIn("description", reduced["properties"])
        self.assertNotIn("enum", reduced["properties"]["passage_id"])
        self.assertEqual(original["required"], reduced["required"])
        self.schema.write_text(json.dumps(original), encoding="utf-8")
        result = self.run_bridge(structured_output={"description": "Unsupported citation", "passage_id": "invented"})
        self.assertEqual(0, result.returncode)
        self.assertFalse(validate_json(self.output, original)["valid"])

    def test_still_oversized_structural_schema_blocks_before_model_dispatch(self):
        properties = {("field" + str(n) + "x" * 250): {"type": "string"} for n in range(80)}
        self.schema.write_text(json.dumps({"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}), encoding="utf-8")
        result = self.run_bridge()
        self.assertNotEqual(0, result.returncode)
        self.assertFalse((self.root / "received.json").exists())
        self.assertFalse(self.output.exists())
        self.assertIn(b"bounded command size", result.stderr)


if __name__ == "__main__":
    unittest.main()
