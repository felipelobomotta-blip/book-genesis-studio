"""Model adapters: the only place the runner talks to a model.

Every adapter exposes ``complete(prompt, model=...) -> str``. The runner owns file
I/O. Claude is started in safe mode with its tool list disabled. Codex versions supported by this
runner have no equivalent no-tools flag, so it is isolated with its ephemeral,
read-only sandbox and without user/project configuration; this constrains writes but
is not a promise that it cannot read a permitted workspace. Generic CLIs follow their
own declared capability model. The manual adapter writes the prompt to disk and waits
for a person to paste the reply (ADR 0002).
"""

from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from typing import Callable, Dict, List, Optional, Protocol, Sequence, Tuple, Union
import urllib.error
import urllib.request

DEFAULT_MAX_TOKENS = 16000
CLEANUP_WAIT_SECONDS = 1
Transport = Callable[[str, Dict[str, str], bytes, int], Tuple[int, bytes]]

REPO_ROOT = Path(__file__).resolve().parents[1]


def command_template_argv(command_template: str, model: str = "") -> List[str]:
    """Parse a configured command once and keep model text in one argv element."""
    try:
        tokens = shlex.split(command_template, posix=True)
    except ValueError as exc:
        raise AdapterError(f"invalid adapter command template: {exc}") from exc
    return [token.replace("{model}", model) for token in tokens if token.replace("{model}", model)]


def resolve_repo_relative_argv(tokens: Sequence[str]) -> List[str]:
    """Resolve repository files without splitting paths that contain spaces."""
    rewritten: List[str] = []
    for token in tokens:
        candidate = Path(token)
        if not candidate.is_absolute():
            repo_candidate = REPO_ROOT / candidate
            if repo_candidate.exists():
                rewritten.append(str(repo_candidate))
                continue
        rewritten.append(token)
    return rewritten


def resolve_repo_relative_tokens(command: str) -> str:
    """Compatibility helper for callers that still expect a rendered string.

    Declared command templates such as ``python runner/bridge_gemini.py {model}``
    use repo-relative paths, but execution uses ``resolve_repo_relative_argv``
    so spaces survive unchanged.
    """
    return shlex.join(resolve_repo_relative_argv(command_template_argv(command)))


class AdapterError(RuntimeError):
    """A model call failed or returned nothing usable."""


class AwaitingManual(RuntimeError):
    """Manual adapter: the prompt is on disk; a person has to paste the model's reply."""

    def __init__(self, prompt_path: Path, response_path: Path, role: str) -> None:
        super().__init__(
            f"[{role}] prompt written to {prompt_path}. Send it to your model, paste the full reply "
            f"into {response_path}, then run the same command again."
        )
        self.prompt_path = prompt_path
        self.response_path = response_path
        self.role = role


@dataclass(frozen=True)
class Call:
    prompt: str
    model: str


class Adapter(Protocol):
    name: str

    def complete(self, prompt: str, *, model: str = "") -> str: ...


class FakeAdapter:
    """Scripted responses for tests. Records every prompt it was sent."""

    name = "fake"

    def __init__(self, responses: Sequence[str] = ()) -> None:
        self._responses: List[str] = list(responses)
        self.calls: List[Call] = []

    def complete(self, prompt: str, *, model: str = "") -> str:
        self.calls.append(Call(prompt=prompt, model=model))
        if not self._responses:
            raise AdapterError("FakeAdapter ran out of scripted responses")
        return self._responses.pop(0)


class ClaudeCliAdapter:
    """``claude -p`` with the prompt on stdin and plain text on stdout."""

    name = "claude"

    def __init__(self, executable: str = "claude", timeout_seconds: int = 1800, *, effort: str = "") -> None:
        if effort not in ("", "low", "medium", "high", "xhigh", "max"):
            raise ValueError("Unsupported Claude effort level")
        self.executable = executable
        self.timeout_seconds = timeout_seconds
        self.effort = effort

    def build_command(self, model: str = "", *, streaming: bool = False) -> List[str]:
        command = _resolve(self.executable) + [
            "-p",
            "--output-format",
            "stream-json" if streaming else "text",
            "--no-session-persistence",
            "--safe-mode",
            "--disable-slash-commands",
            "--tools",
            "",
        ]
        if model:
            command += ["--model", model]
        if self.effort:
            command += ["--effort", self.effort]
        if streaming:
            command += ["--verbose", "--include-partial-messages"]
        return command

    def complete(self, prompt: str, *, model: str = "") -> str:
        # The CLI must not inherit the project's working directory, where
        # instructions or files could become ambient context. Claude safe mode
        # retains OAuth while disabling project customizations and tools.
        from runner.activity import public_text_observer
        observer = public_text_observer()
        try:
            with _temporary_workdir("book-genesis-claude-") as workdir:
                if observer is None:
                    result = _run(self.build_command(model), prompt, timeout_seconds=self.timeout_seconds, cwd=workdir)
                else:
                    result = _run(self.build_command(model, streaming=True), prompt,
                                  timeout_seconds=self.timeout_seconds, cwd=workdir,
                                  on_stdout_line=lambda line: _claude_public_delta(line, observer))
        except subprocess.TimeoutExpired as exc:
            raise AdapterError(f"claude timed out after {self.timeout_seconds} seconds") from exc
        if result.returncode != 0:
            reason = _claude_failure(result.stdout) if observer is not None else result.stdout.strip()[:800]
            reason = reason or result.stderr.strip()[:800] or "The provider process stopped without an error message. Check the connection and retry."
            raise AdapterError(f"claude exited {result.returncode}: {reason}")
        text = result.stdout.strip()
        if observer is not None:
            text = _claude_stream_result(text)
        if not text:
            raise AdapterError("claude returned empty output")
        _warn_if_undecodable(text, "claude")
        return text


def _claude_public_delta(line, observer):
    """Allowlist only the public text delta; thinking/tool/system events stay out."""
    try:
        event = json.loads(line)
        if event.get("type") != "stream_event":
            return
        delta = event.get("event", {}).get("delta", {})
        if delta.get("type") == "text_delta" and isinstance(delta.get("text"), str):
            observer(delta["text"])
    except (ValueError, AttributeError, TypeError):
        return


def _claude_failure(stream):
    """Read declared result errors, never partial prose or private stream events."""
    for line in reversed(stream.splitlines()):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("type") == "result" and event.get("is_error"):
            errors = event.get("errors")
            detail = event.get("result") or ("; ".join(str(e) for e in errors) if isinstance(errors, list) else errors)
            return str(detail or event.get("subtype") or "Provider reported an unsuccessful response")[:800]
    return ""


def _claude_stream_result(stream):
    for line in reversed(stream.splitlines()):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("type") == "result":
            if event.get("is_error"):
                raise AdapterError("claude could not complete the streamed response: " + _claude_failure(line))
            result = event.get("result")
            if isinstance(result, str) and result.strip():
                return result.strip()
    raise AdapterError("claude stream ended without a completed response; partial prose was not accepted")


class CodexCliAdapter:
    """``codex exec`` with the prompt on stdin; the reply is read from --output-last-message."""

    name = "codex"

    def __init__(self, executable: str = "codex", timeout_seconds: int = 1800, *, effort: str = "") -> None:
        if effort not in ("", "minimal", "low", "medium", "high", "xhigh"):
            raise ValueError("Unsupported Codex effort level")
        self.executable = executable
        self.timeout_seconds = timeout_seconds
        self.effort = effort
        self._auth_checked = False

    def _ensure_logged_in(self) -> None:
        """Fail before a long generation call when CLI authentication is unavailable."""
        if self._auth_checked:
            return
        status = codex_login_status(self.executable, timeout_seconds=min(self.timeout_seconds, 10))
        if status is None:
            raise AdapterError(
                "could not check Codex authentication in this environment. "
                "This does not mean you are logged out. Check `codex login status` in the same terminal and retry."
            )
        if not status:
            raise AdapterError("Codex CLI is not logged in. Run `codex login` and try again.")
        self._auth_checked = True

    def preflight(self) -> None:
        """Check authentication before the runner reserves a chapter attempt."""
        self._ensure_logged_in()

    def build_command(
        self,
        model: str = "",
        last_message_file: Path | None = None,
        workdir: Path | None = None,
    ) -> List[str]:
        # Current Codex exposes no no-tools switch. Keep the agent ephemeral and
        # read-only without loading its user configuration. We do not pass an
        # ignore-rules flag; exec-policy behavior remains the CLI's own contract.
        command = _resolve(self.executable) + [
            "exec",
            "--skip-git-repo-check",
            "--ignore-user-config",
            "--ephemeral",
            "-s",
            "read-only",
        ]
        if workdir is not None:
            command += ["-C", str(workdir)]
        if last_message_file is not None:
            command += ["-o", str(last_message_file)]
        if model:
            command += ["-m", model]
        if self.effort:
            command += ["-c", 'model_reasoning_effort="' + self.effort + '"']
        return command

    def complete(self, prompt: str, *, model: str = "") -> str:
        self._ensure_logged_in()
        try:
            with _temporary_workdir("book-genesis-codex-") as tmp:
                last_message = Path(tmp) / "last-message.md"
                result = _run(
                    self.build_command(model, last_message, Path(tmp)),
                    prompt,
                    timeout_seconds=self.timeout_seconds,
                    cwd=tmp,
                )
                if result.returncode != 0:
                    raise AdapterError(f"codex exited {result.returncode}: {result.stderr.strip()[:800]}")
                if not last_message.exists():
                    raise AdapterError("codex did not write the last-message file")
                text = last_message.read_text(encoding="utf-8", errors="replace").strip()
        except subprocess.TimeoutExpired as exc:
            raise AdapterError(f"codex timed out after {self.timeout_seconds} seconds") from exc
        if not text:
            raise AdapterError("codex returned empty output")
        _warn_if_undecodable(text, "codex")
        return text


class GenericCliAdapter:
    """Any command-line model tool: prompt on stdin, reply on stdout.

    The command is a template from runner/config/adapters.yaml; ``{model}`` is replaced
    by the role's model name, which may be empty.
    """

    def __init__(self, name: str, command_template: str, timeout_seconds: int = 1800) -> None:
        self.name = name
        self.command_template = command_template
        self.timeout_seconds = timeout_seconds

    def render_command(self, model: str = "") -> str:
        return shlex.join(command_template_argv(self.command_template, model))

    def build_command(self, model: str = "") -> List[str]:
        command = resolve_repo_relative_argv(command_template_argv(self.command_template, model))
        if not command:
            raise AdapterError(f"adapter {self.name} has an empty command template")
        head = command[0]
        resolved = shutil.which(head)
        if resolved is None and Path(head).is_file():
            resolved = head
        if resolved is None:
            raise AdapterError(f"{head!r} (adapter {self.name}) was not found on PATH")
        if resolved.lower().endswith((".cmd", ".bat")):
            return ["cmd", "/c", resolved, *command[1:]]
        return [resolved, *command[1:]]

    def complete(self, prompt: str, *, model: str = "") -> str:
        command = self.build_command(model)
        try:
            with _temporary_workdir("book-genesis-generic-") as workdir:
                result = _run(command, prompt, timeout_seconds=self.timeout_seconds, cwd=workdir)
        except subprocess.TimeoutExpired as exc:
            raise AdapterError(f"{self.name} timed out after {self.timeout_seconds} seconds") from exc
        if result.returncode != 0:
            raise AdapterError(f"{self.name} exited {result.returncode}: {result.stderr.strip()[:800]}")
        text = result.stdout.strip()
        if not text:
            raise AdapterError(f"{self.name} returned empty output")
        _warn_if_undecodable(text, self.name)
        return text


class ManualAdapter:
    """For people with a chat window and no CLI: the prompt becomes a file, the reply too.

    File names are derived from a hash of the prompt, and the runner's prompts are
    deterministic, so re-running the same command finds the pasted reply.
    """

    name = "manual"

    def __init__(self, directory: Path, role: str) -> None:
        self.directory = Path(directory)
        self.role = role

    def paths_for(self, prompt: str) -> Tuple[Path, Path]:
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:10]
        stem = f"{digest}-{self.role}"
        return self.directory / f"{stem}.prompt.md", self.directory / f"{stem}.response.md"

    def complete(self, prompt: str, *, model: str = "") -> str:
        prompt_path, response_path = self.paths_for(prompt)
        if response_path.exists():
            text = response_path.read_text(encoding="utf-8").strip()
            if text:
                return text
        self.directory.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt, encoding="utf-8")
        raise AwaitingManual(prompt_path, response_path, self.role)


class OpenAICompatibleAdapter:
    """Any ``/chat/completions`` endpoint: OpenRouter, DeepSeek, OpenAI, Groq, Together, local servers.

    Stdlib only. The key travels in the Authorization header and nowhere else; error messages
    have it masked. ``transport`` is injectable so tests never touch the network.
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        *,
        timeout_seconds: int = 1800,
        transport: Optional[Transport] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.transport: Transport = transport or _http_post
        self.extra_headers = dict(extra_headers or {})

    def complete(self, prompt: str, *, model: str = "") -> str:
        if not model:
            raise AdapterError(f"{self.name}: a model name is required for this provider (set it with `book-genesis setup`)")
        if not self.api_key:
            raise AdapterError(f"{self.name}: no API key; run `book-genesis setup` or set the provider's environment variable")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            **self.extra_headers,
        }
        body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
        status, raw = self.transport(f"{self.base_url}/chat/completions", headers, body, self.timeout_seconds)
        if status != 200:
            raise AdapterError(f"{self.name} returned HTTP {status}: {_safe_excerpt(raw, self.api_key)}")
        try:
            data = json.loads(raw.decode("utf-8"))
            text = data["choices"][0]["message"]["content"]
            if data["choices"][0].get("finish_reason") in {"length", "content_filter"}:
                raise AdapterError(f"{self.name}: provider stopped before completing the response; retry or choose another model")
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise AdapterError(f"{self.name}: unexpected response shape: {_safe_excerpt(raw, self.api_key)}") from exc
        if text is not None and not isinstance(text, str):
            raise AdapterError(f"{self.name}: expected a text response, received another content type")
        text = (text or "").strip()
        if not text:
            raise AdapterError(f"{self.name} returned empty output")
        _warn_if_undecodable(text, self.name)
        return text


class AnthropicAdapter:
    """The Anthropic Messages API, stdlib only."""

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        *,
        timeout_seconds: int = 1800,
        transport: Optional[Transport] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.transport: Transport = transport or _http_post
        self.max_tokens = max_tokens

    def complete(self, prompt: str, *, model: str = "") -> str:
        if not model:
            raise AdapterError(f"{self.name}: a model name is required for this provider (set it with `book-genesis setup`)")
        if not self.api_key:
            raise AdapterError(f"{self.name}: no API key; run `book-genesis setup` or set ANTHROPIC_API_KEY")
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        body = json.dumps(
            {"model": model, "max_tokens": self.max_tokens, "messages": [{"role": "user", "content": prompt}]}
        ).encode("utf-8")
        status, raw = self.transport(f"{self.base_url}/v1/messages", headers, body, self.timeout_seconds)
        if status != 200:
            raise AdapterError(f"{self.name} returned HTTP {status}: {_safe_excerpt(raw, self.api_key)}")
        try:
            data = json.loads(raw.decode("utf-8"))
            if data.get("stop_reason") in {"max_tokens", "refusal"}:
                raise AdapterError(f"{self.name}: provider stopped before completing the response; retry or choose another model")
            text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
        except (ValueError, AttributeError, TypeError) as exc:
            raise AdapterError(f"{self.name}: unexpected response shape: {_safe_excerpt(raw, self.api_key)}") from exc
        text = text.strip()
        if not text:
            raise AdapterError(f"{self.name} returned empty output")
        _warn_if_undecodable(text, self.name)
        return text


def _http_post(url: str, headers: Dict[str, str], body: bytes, timeout_seconds: int) -> Tuple[int, bytes]:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()
    except urllib.error.URLError as error:
        raise AdapterError(f"could not reach {url}: {error.reason}") from error
    except (TimeoutError, ConnectionError) as error:
        raise AdapterError(f"provider connection failed or timed out after {timeout_seconds} seconds") from error


def _safe_excerpt(raw: bytes, secret: str) -> str:
    text = raw.decode("utf-8", errors="replace")
    if secret:
        text = text.replace(secret, "***")
    return " ".join(text.split())[:300]


def _resolve(executable: str) -> List[str]:
    path = shutil.which(executable)
    if not path:
        raise AdapterError(f"{executable!r} was not found on PATH")
    if path.lower().endswith((".cmd", ".bat")):
        return ["cmd", "/c", path]
    return [path]


def codex_login_status(executable: str = "codex", *, timeout_seconds: int = 10) -> Optional[bool]:
    """Return Codex authentication state without starting a generation request.

    ``None`` means the status command itself could not be verified. This is kept
    separate from ``False`` so the CLI can tell a missing login from a broken install.
    """
    try:
        result = _run(
            _resolve(executable) + ["login", "status"],
            "", timeout_seconds=timeout_seconds,
        )
    except (AdapterError, OSError, subprocess.TimeoutExpired):
        return None
    status = f"{result.stdout}\n{result.stderr}".lower()
    if "not logged in" in status or "not authenticated" in status:
        return False
    if result.returncode == 0 and "logged in" in status:
        return True
    return None


@contextmanager
def _temporary_workdir(prefix: str):
    """A briefly locked Windows temp folder must not replace a provider result."""
    directory = tempfile.TemporaryDirectory(prefix=prefix)
    try:
        yield directory.name
    finally:
        for delay in (0, 0.1, 0.2):
            if delay:
                time.sleep(delay)
            try:
                directory.cleanup()
                break
            except OSError:
                if delay == 0.2:
                    sys.stderr.write("warning: Windows could not remove a temporary provider folder because it is still in use.\n")


def _run(
    command: Union[str, Sequence[str]],
    prompt: str,
    *,
    timeout_seconds: int,
    cwd: Optional[Union[str, Path]] = None,
    on_stdout_line: Optional[Callable[[str], None]] = None,
) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)  # allow `claude -p` to run from inside a Claude Code session
    env["PYTHONIOENCODING"] = "utf-8"
    popen_args: Union[str, List[str]]
    if isinstance(command, str):
        popen_args = command if os.name == "nt" else shlex.split(command)
    else:
        popen_args = list(command)
    process = subprocess.Popen(
        popen_args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=str(cwd) if cwd is not None else None,
    )
    captured = []
    reader = None
    if on_stdout_line is not None:
        stream = process.stdout
        # communicate still owns stdin, stderr, timeout and cancellation. A
        # dedicated reader drains stdout as it arrives, then closes its handle.
        process.stdout = None
        def read_output():
            try:
                for line in iter(stream.readline, ""):
                    captured.append(line)
                    try:
                        on_stdout_line(line)
                    except Exception:
                        pass  # a display failure must not block the provider pipe
            finally:
                stream.close()
        reader = threading.Thread(target=read_output, daemon=True)
        reader.start()
    try:
        stdout, stderr = process.communicate(input=prompt, timeout=timeout_seconds)
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
        try:
            _terminate_timed_out_process(process)
            try:
                process.communicate(timeout=CLEANUP_WAIT_SECONDS)
            except subprocess.TimeoutExpired:
                # This is still only the process we created, never a name/global kill.
                try:
                    process.kill()
                    process.communicate(timeout=CLEANUP_WAIT_SECONDS)
                except (OSError, subprocess.TimeoutExpired):
                    pass
        except OSError:
            # Cleanup cannot replace the timeout that triggered it.
            pass
        raise exc
    finally:
        if reader is not None:
            reader.join(timeout=CLEANUP_WAIT_SECONDS)
    if reader is not None:
        if reader.is_alive():
            raise AdapterError("provider stdout did not close after completion")
        stdout = "".join(captured)
    return subprocess.CompletedProcess(popen_args, process.returncode, stdout, stderr)


def _terminate_timed_out_process(process: subprocess.Popen) -> None:
    """Bounded Windows-only cleanup for a timed-out wrapper and its own children."""
    if os.name != "nt" or process.poll() is not None:
        return
    try:
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=CLEANUP_WAIT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        # The direct `process.kill()` fallback in `_run` still targets only this PID.
        pass


def _warn_if_undecodable(text: str, adapter_name: str) -> None:
    """Long `claude -p` replies on Windows occasionally carry a byte pair that is not UTF-8
    (measured: 2 in ~30k bytes on one 3-minute reply; short replies are clean). The runner
    keeps the text and says so, because a silent U+FFFD in prose would reach the judge."""
    count = text.count("�")
    if count:
        sys.stderr.write(f"warning: {count} undecodable character(s) in {adapter_name} output; search for �\n")
