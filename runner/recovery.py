"""Conservative, actionable recovery. Never change providers or permissions silently."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Recovery:
    category: str
    retryable: bool
    action: str


def classify_error(message: str) -> Recovery:
    text = message.lower()
    if any(word in text for word in ("quota", "insufficient", "billing", "credit balance", "hit your session limit", "usage limit", "weekly limit", "limit reached", "out of extra usage")):
        return Recovery("quota", False, "Check your provider allowance or choose another connection. Your work is saved.")
    if any(word in text for word in ("permission", "not permitted", "access denied", "headless")):
        return Recovery("permission", False, "This connection requested an unavailable operation. Choose a text-compatible connection; your work is saved.")
    if re.search(r"\b(?:401|403)\b", text) or any(word in text for word in ("not logged", "login", "log in", "api key", "authentication", "unauthorized")):
        return Recovery("authentication", False, "Reconnect your provider in connection setup, then resume your saved book.")
    if any(word in text for word in ("not found", "not installed", "unknown model", "nonexistent", "invalid model", "model name is required")):
        return Recovery("configuration", False, "Select an installed connection and an available model, then resume.")
    if re.search(r"\b429\b", text) or "rate limit" in text:
        return Recovery("rate_limit", True, "The provider is busy. Wait briefly, then retry the saved step.")
    if re.search(r"\b(?:500|502|503|504)\b", text) or any(word in text for word in ("timed out", "timeout", "could not reach", "connection failed", "connection reset")):
        return Recovery("temporary", True, "The connection was interrupted. You can retry the saved step.")
    return Recovery("output", True, "The response could not be used. Retry the saved step; existing chapters are safe.")


def capabilities(adapter) -> dict:
    from runner.adapters import ClaudeCliAdapter, CodexCliAdapter, OpenAICompatibleAdapter, AnthropicAdapter
    return {"connection": adapter.name,
            "public_prose_streaming": isinstance(adapter, ClaudeCliAdapter),
            "tool_mode": ("disabled" if isinstance(adapter, (ClaudeCliAdapter, OpenAICompatibleAdapter, AnthropicAdapter))
                          else "read-only sandbox" if isinstance(adapter, CodexCliAdapter) else "provider-declared; verify"),
            "timeout_seconds": getattr(adapter, "timeout_seconds", None)}
