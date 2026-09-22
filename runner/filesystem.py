"""Repository paths and the canonical pipeline manifest.

Book Genesis runs inside the author's host agent. This module only reads the
manifest that the installer validates; it never creates or advances a book.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, List


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "book-genesis"
MANIFEST_PATH = SKILL_ROOT / "references" / "pipeline" / "manifest.yaml"


@dataclass(frozen=True)
class Phase:
    key: str
    label: str
    prompt: str
    references: List[str]
    gate: str
    outputs: List[str]
    next: str


def load_manifest(path: Path = MANIFEST_PATH) -> List[Phase]:
    entries = _load_simple_yaml_map(path)
    return [
        Phase(
            key=key,
            label=str(entry.get("label", "")),
            prompt=str(entry.get("prompt", "")),
            references=list(entry.get("references", [])),
            gate=str(entry.get("gate", "")),
            outputs=list(entry.get("outputs", [])),
            next=str(entry.get("next", "")),
        )
        for key, entry in entries.items()
    ]


def _load_simple_yaml_map(path: Path) -> Dict[str, Dict[str, object]]:
    """Read the two-level mapping used by manifest.yaml (keys, scalars, lists)."""
    entries: Dict[str, Dict[str, object]] = {}
    current_key = ""
    current_list_key = ""

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" "):
            current_key = line.split(":", 1)[0].strip()
            entries[current_key] = {}
            current_list_key = ""
            continue
        if not current_key:
            raise ValueError(f"Value before top-level key in {path}: {line}")
        stripped = line.strip()
        if stripped.startswith("- "):
            if not current_list_key:
                raise ValueError(f"List item without list key in {path}: {line}")
            entries[current_key].setdefault(current_list_key, [])
            entries[current_key][current_list_key].append(_unquote(stripped[2:].strip()))  # type: ignore[union-attr]
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            entries[current_key][key] = []
            current_list_key = key
        else:
            entries[current_key][key] = _unquote(value)
            current_list_key = ""

    return entries


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return json.loads(value)
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value
