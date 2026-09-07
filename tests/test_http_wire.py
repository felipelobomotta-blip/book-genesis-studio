"""Real localhost HTTP transport, with simulated provider replies (no API accounts)."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import time
import unittest

from runner.adapters import AdapterError, AnthropicAdapter, OpenAICompatibleAdapter


@contextmanager
def endpoint(status, payload, delay=0):
    requests = []
    raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            requests.append((self.path, dict(self.headers), json.loads(body)))
            time.sleep(delay)
            try:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(raw)
            except ConnectionError:
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


class HttpWireTests(unittest.TestCase):
    def test_openai_wire_preserves_long_unicode_prompt_and_uses_auth_header(self):
        prompt = "An idea: café, 東京, —.\n" * 4000
        with endpoint(200, {"choices": [{"message": {"content": "A whole reply — café."}, "finish_reason": "stop"}]}) as (url, requests):
            adapter = OpenAICompatibleAdapter("local-qa", url + "/v1", "test-secret")
            self.assertEqual("A whole reply — café.", adapter.complete(prompt, model="test-model"))
        path, headers, body = requests[0]
        self.assertEqual("/v1/chat/completions", path)
        self.assertEqual("Bearer test-secret", headers["Authorization"])
        self.assertEqual(prompt, body["messages"][0]["content"])
        self.assertNotIn("test-secret", json.dumps(body))

    def test_anthropic_wire_reads_only_text_blocks(self):
        with endpoint(200, {"content": [{"type": "thinking", "thinking": "private"}, {"type": "text", "text": "Public prose."}], "stop_reason": "end_turn"}) as (url, requests):
            adapter = AnthropicAdapter("local-qa", url, "test-secret")
            self.assertEqual("Public prose.", adapter.complete("Write.", model="test-model"))
        self.assertEqual("/v1/messages", requests[0][0])
        self.assertEqual("test-secret", requests[0][1]["X-Api-Key"])

    def test_auth_rate_limit_and_service_errors_are_bounded_and_redacted(self):
        for cls in (OpenAICompatibleAdapter, AnthropicAdapter):
            for status in (401, 403, 429, 500, 503):
                with self.subTest(adapter=cls.__name__, status=status), endpoint(status, {"error": "bad test-secret"}) as (url, requests):
                    with self.assertRaises(AdapterError) as error:
                        cls("local-qa", url, "test-secret").complete("Write.", model="test-model")
                    self.assertIn(str(status), str(error.exception))
                    self.assertNotIn("test-secret", str(error.exception))
                    self.assertEqual(1, len(requests))

    def test_malformed_and_empty_responses_are_adapter_errors(self):
        for payload in (b"not JSON", {}, [], {"choices": []}, {"choices": [{"message": {"content": []}}]}, {"choices": [{"message": {"content": " "}}]}):
            with self.subTest(payload=payload), endpoint(200, payload) as (url, _):
                with self.assertRaises(AdapterError):
                    OpenAICompatibleAdapter("local-qa", url, "test-secret").complete("Write.", model="test-model")

    def test_truncated_responses_never_become_finished_prose(self):
        cases = [
            (OpenAICompatibleAdapter, {"choices": [{"message": {"content": "A sentence that"}, "finish_reason": "length"}]}),
            (AnthropicAdapter, {"content": [{"type": "text", "text": "A sentence that"}], "stop_reason": "max_tokens"}),
        ]
        for cls, payload in cases:
            with self.subTest(adapter=cls.__name__), endpoint(200, payload) as (url, _):
                with self.assertRaisesRegex(AdapterError, "stopped before completing"):
                    cls("local-qa", url, "test-secret").complete("Write.", model="test-model")

    def test_real_socket_timeout_is_a_recoverable_adapter_error(self):
        with endpoint(200, {}, delay=0.3) as (url, _):
            with self.assertRaisesRegex(AdapterError, "timed out"):
                OpenAICompatibleAdapter("local-qa", url, "test-secret", timeout_seconds=0.05).complete("Write.", model="test-model")


if __name__ == "__main__":
    unittest.main()
