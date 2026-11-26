"""Interactive Shower-Idea Catalyst for Book Genesis Studio (pure Python stdlib).

Transforms a raw, unstructured shower idea into three distinct, jargon-free
high-concept commercial book directions using an isolated read-only native CLI
call (`run_host_call`). Never modifies any book workspace, never promises sales
or virality, and ensures `enriched_brief` remains free of operational/score
directives so it passes `validate_creative_idea`.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Callable
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/book-genesis/scripts"
for _p in (ROOT, SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from launcher.autonomous import controlled_command
from launcher.native import find_native
from plugin_entry import validate_creative_idea
from run_host_call import HostCallError, run_host_call
from workflow_roles import TEXT, array, obj, validate_json


DIRECTION_ITEM_SCHEMA = obj({
    "id": {"type": "integer", "enum": [1, 2, 3]},
    "angle_label": TEXT,
    "title": TEXT,
    "genre": TEXT,
    "pitch_15s": TEXT,
    "protagonist_and_wound": TEXT,
    "tropes_and_twist": TEXT,
    "opening_10pct_hook": TEXT,
    "shareability_peak": TEXT,
    "enriched_brief": TEXT,
})

CATALYST_SCHEMA = obj({
    "directions": {
        **array(DIRECTION_ITEM_SCHEMA),
        "minItems": 3,
        "maxItems": 3,
    },
})


def build_catalyst_packet(idea: str, language: str) -> str:
    specialist = (ROOT / "skills/book-genesis/references/specialists/shower-idea-catalyst.md").read_text(encoding="utf-8")
    return (
        "You are a high-concept developmental book editor helping a creative author turn a raw shower idea "
        "into three distinct, magnetic commercial book directions. Use only this packet; do not use tools, "
        "browse the web, or invent sales forecasts or bestseller guarantees.\n\n"
        f"Write every field in {language} using vivid, accessible, zero-jargon language.\n"
        "Preserve 100% of the author's core spark in all three options while varying the narrative angle, "
        "emotional temperature, and fresh subversion.\n"
        "Rules for `enriched_brief`: 4 to 7 rich sentences capturing the original idea, protagonist, emotional wound, "
        "central conflict, stakes, tone, and fresh twist so a full-book pipeline can build from it. "
        "CRITICAL: `enriched_brief` must contain ONLY pure creative story content — NEVER mention numeric scores, "
        "ratings (like 9/10 or 90/100), quality targets, prompts, AI instructions, or sales promises.\n\n"
        + specialist
        + "\n\nAuthor's raw shower idea and requested language:\n"
        + json.dumps({"idea": idea.strip(), "language": language.strip()}, ensure_ascii=False)
    )


def validate_catalyst_data(data: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict) or not isinstance(data.get("directions"), list):
        return ["Response must contain a directions array"]
    directions = data["directions"]
    if sorted(item.get("id") for item in directions if isinstance(item, dict)) != [1, 2, 3]:
        errors.append("Directions must contain exact IDs 1, 2, and 3")
    for item in directions:
        if not isinstance(item, dict):
            errors.append("Direction entry must be an object")
            continue
        try:
            validate_creative_idea(str(item.get("enriched_brief") or ""))
        except ValueError as exc:
            errors.append(f"Direction {item.get('id')} enriched_brief invalid: {exc}")
    return errors


def _inject_output_schema(command: dict, schema_path: Path, timeout_seconds: int = 240) -> str:
    argv = list(command["argv"])
    if argv[-3:] != ["-o", "{output}", "-"]:
        raise ValueError("Unexpected headless native command layout")
    argv[-3:-3] = ["--output-schema", str(schema_path)]
    return json.dumps({"argv": argv, "timeout_seconds": timeout_seconds})


def catalyze_idea(
    books_root: Path,
    *,
    idea: str,
    language: str = "English",
    host: str = "codex",
    model: str | None = None,
    effort: str = "medium",
    default_models: dict[str, str] | None = None,
    transport: Callable[[str, dict], dict] | None = None,
) -> dict:
    clean_idea = str(idea or "").strip()
    if len(clean_idea) < 12:
        raise ValueError("Please share a bit more about your idea (at least 12 characters).")
    validate_creative_idea(clean_idea)
    host = str(host or "codex").strip().lower()
    if host not in {"codex", "claude"}:
        raise ValueError("Supported engines: codex or claude")
    models = default_models or {"codex": "gpt-5.6-luna", "claude": "claude-sonnet-4-6"}
    chosen_model = str(model or models[host]).strip()
    chosen_effort = effort if effort in {"low", "medium", "high"} else "medium"
    packet_text = build_catalyst_packet(clean_idea, language)

    if transport is not None:
        raw = transport(packet_text, CATALYST_SCHEMA)
        tmp_root = books_root / ".catalyst-runs" / ("test-" + uuid4().hex[:10])
        tmp_root.mkdir(parents=True, exist_ok=True)
        resp_path = tmp_root / "response.json"
        resp_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
        check = validate_json(resp_path, CATALYST_SCHEMA)
        extra = validate_catalyst_data(raw) if check["valid"] else []
        if not check["valid"] or extra:
            raise ValueError("Catalyst response failed validation: " + "; ".join(check["errors"] + extra))
        return {"idea": clean_idea, "language": language, "host": host, "model": chosen_model, "directions": raw["directions"]}

    scratch = (books_root / ".catalyst-runs" / ("cat-" + uuid4().hex[:12])).resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    schema_path = scratch / "catalyst.schema.json"
    packet_path = scratch / "catalyst.packet.md"
    schema_path.write_text(json.dumps(CATALYST_SCHEMA, ensure_ascii=False, indent=2), encoding="utf-8")
    packet_path.write_text(packet_text, encoding="utf-8")

    bridge = ROOT / "skills/book-genesis/scripts/native_claude.py" if host == "claude" else None
    cmd = controlled_command(find_native(host), model=chosen_model, effort=chosen_effort, host=host, bridge=bridge)
    cmd_json = _inject_output_schema(cmd, schema_path, timeout_seconds=240)
    call_id = "catalyst-" + uuid4().hex[:10]
    try:
        receipt = run_host_call(scratch, call_id, packet_path, cmd_json)
    except HostCallError as exc:
        stderr_hint = ""
        try:
            stderr_path = scratch / receipt_rel if (receipt_rel := (exc.receipt.get("paths") or {}).get("stderr")) else None
            if stderr_path and stderr_path.is_file():
                stderr_hint = " " + " ".join(stderr_path.read_text(encoding="utf-8", errors="replace").splitlines()[-3:])[:280]
        except OSError:
            pass
        raise RuntimeError(f"Failed to shape the idea with {host}: {exc}.{stderr_hint}".strip()) from exc

    response_path = scratch / receipt["paths"]["response"]
    check = validate_json(response_path, CATALYST_SCHEMA)
    if not check["valid"]:
        raise RuntimeError("Catalyst response failed JSON schema validation: " + "; ".join(check["errors"]))
    parsed = json.loads(response_path.read_text(encoding="utf-8-sig"))
    extra = validate_catalyst_data(parsed)
    if extra:
        raise RuntimeError("Catalyst response failed safety check: " + "; ".join(extra))
    return {
        "idea": clean_idea,
        "language": language,
        "host": host,
        "model": chosen_model,
        "directions": parsed["directions"],
    }
