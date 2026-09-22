"""Claude Code subagents generated from the core skill's role files.

The role files under skills/book-genesis/references/roles/ are the single
source of truth. Every host reads them directly; Claude Code additionally gets
subagent files with tool limits, generated here so they can never drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from runner.filesystem import REPO_ROOT


ROLES_RELATIVE = Path("skills") / "book-genesis" / "references" / "roles"
AGENTS_RELATIVE = Path("agents")


@dataclass(frozen=True)
class AgentSpec:
    name: str
    role_file: str
    tools: str
    description: str

    @property
    def agent_file(self) -> str:
        return f"{self.name}.md"


AGENT_SPECS: tuple[AgentSpec, ...] = (
    AgentSpec(
        name="book-genesis-blind-reader",
        role_file="blind-reader.md",
        tools="Read",
        description=(
            "Blind reader for the book-genesis skill. Reads only the prose it is handed and reports "
            "where a reader would stop, what they would remember, and what sounds machine-made. "
            "It never sees outlines, targets or earlier scores. Only for use by book-genesis."
        ),
    ),
    AgentSpec(
        name="book-genesis-auditor",
        role_file="auditor.md",
        tools="Read, Grep, Glob",
        description=(
            "Read-only structural auditor for the book-genesis skill. Audits a full manuscript "
            "against its outline and continuity ledger, cites exact passages, and never edits files. "
            "Only for use by book-genesis."
        ),
    ),
)


def render_agents(roles_dir: Path) -> dict[str, str]:
    """Return {agent file name: file content} for every spec."""
    rendered: dict[str, str] = {}
    for spec in AGENT_SPECS:
        body = (roles_dir / spec.role_file).read_text(encoding="utf-8").strip()
        source = (ROLES_RELATIVE / spec.role_file).as_posix()
        rendered[spec.agent_file] = (
            "---\n"
            f"name: {spec.name}\n"
            f"description: {spec.description}\n"
            f"tools: {spec.tools}\n"
            "model: inherit\n"
            "---\n\n"
            f"<!-- Generated from {source}. Edit that file, then run: "
            "python runner/installer.py generate-agents -->\n\n"
            f"{body}\n"
        )
    return rendered


def generate_agents(repo_root: Path = REPO_ROOT) -> list[Path]:
    """Write the generated agents; return the files written."""
    agents_dir = repo_root / AGENTS_RELATIVE
    agents_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, text in render_agents(repo_root / ROLES_RELATIVE).items():
        path = agents_dir / name
        path.write_text(text, encoding="utf-8", newline="\n")
        written.append(path)
    return written


def agent_drift(repo_root: Path = REPO_ROOT) -> list[str]:
    """List committed agent files that differ from what the role files generate."""
    agents_dir = repo_root / AGENTS_RELATIVE
    expected = render_agents(repo_root / ROLES_RELATIVE)
    problems: list[str] = []
    for name, text in expected.items():
        path = agents_dir / name
        committed = path.read_text(encoding="utf-8") if path.is_file() else None
        if committed != text:
            problems.append(
                f"agents/{name} is out of date; run: python runner/installer.py generate-agents"
            )
    if agents_dir.is_dir():
        for path in sorted(agents_dir.glob("*.md")):
            if path.name not in expected:
                problems.append(
                    f"agents/{path.name} is not generated from a role file; remove it or add a role"
                )
    return problems
