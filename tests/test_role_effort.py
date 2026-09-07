"""Reasoning effort per role, from the config file to the command line.

The adapters always accepted an effort level and ``test_cli_effort`` proved the
flag reaches the CLI — but nothing built an adapter with one. A run described as
"writer on Luna high, judge on Opus medium" could be written down and never
configured. These tests cover the path that was missing.
"""

from pathlib import Path

import pytest

from runner.adapters import ClaudeCliAdapter, CodexCliAdapter
from runner.constants import PanelSpec, RoleModel
from runner.roles import build_adapter, build_role_adapters
from runner.userconfig import UserConfig, load_user_config, write_user_config

LUNA_HIGH = "writer:\n  adapter: codex\n  model: gpt-5.6-luna\n  effort: high\n"
OPUS_MEDIUM = "judge:\n  adapter: claude\n  model: claude-opus-5\n  effort: medium\n"


def test_build_adapter_passes_effort_to_each_cli():
    assert build_adapter("codex", effort="high").effort == "high"
    assert build_adapter("claude", effort="medium").effort == "medium"


def test_build_adapter_without_effort_keeps_the_cli_default():
    assert build_adapter("codex").effort == ""
    assert build_adapter("claude").effort == ""


def test_effort_survives_a_config_round_trip(tmp_path: Path):
    target = tmp_path / "config.yaml"
    target.write_text(LUNA_HIGH + "\n" + OPUS_MEDIUM, encoding="utf-8")
    config = load_user_config(target)
    assert config.roles["writer"] == RoleModel("codex", "gpt-5.6-luna", "high")
    assert config.roles["judge"] == RoleModel("claude", "claude-opus-5", "medium")

    rewritten = tmp_path / "again.yaml"
    write_user_config(config, rewritten)
    again = load_user_config(rewritten)
    assert again.roles["writer"].effort == "high"
    assert again.roles["judge"].effort == "medium"


def test_absent_effort_is_not_written(tmp_path: Path):
    """An empty key reads back as the CLI default anyway; blanks hide real choices."""
    target = tmp_path / "config.yaml"
    write_user_config(
        UserConfig(roles={"writer": RoleModel("codex", "gpt-5.5")}, panel=[]), target
    )
    assert "effort" not in target.read_text(encoding="utf-8")


def test_two_roles_on_one_cli_get_separate_adapters(tmp_path: Path):
    """The cache is keyed by (adapter, effort): sharing one instance would give
    both roles whichever level happened to be built first."""
    target = tmp_path / "config.yaml"
    target.write_text(
        "writer:\n  adapter: codex\n  model: gpt-5.6-luna\n  effort: high\n\n"
        "judge:\n  adapter: codex\n  model: gpt-5.5\n  effort: low\n",
        encoding="utf-8",
    )
    config = load_user_config(target)
    setup = build_role_adapters(available={"codex": True}, user_config=config)
    assert setup.adapters["writer"].effort == "high"
    assert setup.adapters["judge"].effort == "low"
    assert setup.adapters["writer"] is not setup.adapters["judge"]


def test_same_role_shape_reuses_one_adapter(tmp_path: Path):
    target = tmp_path / "config.yaml"
    target.write_text(
        "writer:\n  adapter: codex\n  model: gpt-5.5\n  effort: high\n\n"
        "editor:\n  adapter: codex\n  model: gpt-5.5\n  effort: high\n",
        encoding="utf-8",
    )
    config = load_user_config(target)
    setup = build_role_adapters(available={"codex": True}, user_config=config)
    assert setup.adapters["writer"] is setup.adapters["editor"]


def test_panel_seat_keeps_its_effort_after_persona_dedup(tmp_path: Path):
    """Renaming a duplicate persona must not drop the seat's reasoning level."""
    target = tmp_path / "config.yaml"
    same = "  adapter: claude\n  model: claude-opus-5\n  persona: the same reader\n  effort: medium\n"
    target.write_text(f"panel_1:\n{same}\npanel_2:\n{same}", encoding="utf-8")
    config = load_user_config(target)
    assert [seat.effort for seat in config.panel] == ["medium", "medium"]
    setup = build_role_adapters(available={"claude": True}, user_config=config)
    assert all(member.adapter.effort == "medium" for member in setup.panel.members)


@pytest.mark.parametrize(
    "adapter_class,bad",
    [(ClaudeCliAdapter, "minimal"), (CodexCliAdapter, "max")],
)
def test_each_cli_rejects_a_level_it_does_not_support(adapter_class, bad):
    """The two CLIs do not accept the same set, and the error must come before the call."""
    with pytest.raises(ValueError):
        adapter_class(effort=bad)


def test_panel_spec_defaults_to_no_effort():
    assert PanelSpec("claude", "opus", "a reader").effort == ""
