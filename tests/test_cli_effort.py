import pytest
from runner.adapters import ClaudeCliAdapter, CodexCliAdapter


def test_explicit_provider_efforts_reach_cli():
    claude = ClaudeCliAdapter(effort="medium").build_command("claude-opus-5")
    assert claude[claude.index("--effort") + 1] == "medium"
    codex = CodexCliAdapter(effort="high").build_command("gpt-5.6-luna")
    assert 'model_reasoning_effort="high"' in codex
    assert "--ignore-user-config" in codex


@pytest.mark.parametrize("adapter", [ClaudeCliAdapter, CodexCliAdapter])
def test_invalid_effort_fails_before_call(adapter):
    with pytest.raises(ValueError):
        adapter(effort="invented")
