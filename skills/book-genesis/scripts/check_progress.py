"""Read-only reconciliation for a Book Genesis schema-6 progress snapshot.

This intentionally parses only the small YAML subset used by
``references/pipeline/project-state.yaml``.  It is not a general YAML parser:
required fields with unsupported, duplicate, or ambiguous syntax fail closed.
The same deterministic chapter and prose count is used by the complete export
preflight, while the CLI can be used by a host before resuming a run.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any, Iterable


class ProgressError(ValueError):
    """Raised for unsupported or ambiguous progress-state syntax."""


_INTEGER_RE = re.compile(r"^[+-]?\d+$")
_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
_WORD_COUNT_METHOD = "whitespace_split_prose_v1"
_PHASE_RE = re.compile(r"^Phase ([0-7]): .+$")
_INCOMPLETE_STATUSES = {
    "",
    "pending",
    "not_started",
    "not-started",
    "in_progress",
    "in-progress",
    "running",
    "unfinished",
    "unknown",
    "not_run",
    "not-run",
    "skipped",
    "never_run",
    "never-run",
}
_REQUIRED_GATES = (
    "intake",
    "foundation",
    "architecture",
    "drafting",
    "adversarial_audit",
    "revision_loop",
    "final_score",
)
_ALL_GATES = _REQUIRED_GATES + ("editorial_package",)
_REQUIRED_TOP_LEVEL = {"schema_version", "pipeline", "manuscript", "gates"}
_REQUIRED_CHILDREN = {
    "pipeline": {"current_phase", "status"},
    "manuscript": {"chapter_count_planned", "completed_chapters", "word_count_actual", "status"},
    "gates": set(_ALL_GATES),
}


@dataclass(frozen=True)
class _ListMarker:
    """Placeholder for a block list whose first item has not been read."""


def _json_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProgressError(f"duplicate key in PROJECT_STATE.yaml: {key}")
        result[key] = value
    return result


def _strip_comment(value: str) -> str:
    quote: str | None = None
    escaped = False
    for index, character in enumerate(value):
        if quote == '"' and escaped:
            escaped = False
            continue
        if quote == '"' and character == "\\":
            escaped = True
            continue
        if character in {'"', "'"}:
            if quote is None:
                quote = character
            elif quote == character:
                quote = None
            continue
        if character == "#" and quote is None and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip()
    return value.rstrip()


def _split_inline_list(value: str) -> list[str]:
    body = value[1:-1].strip()
    if not body:
        return []
    items: list[str] = []
    start = 0
    quote: str | None = None
    escaped = False
    for index, character in enumerate(body):
        if quote == '"' and escaped:
            escaped = False
            continue
        if quote == '"' and character == "\\":
            escaped = True
            continue
        if character in {'"', "'"}:
            if quote is None:
                quote = character
            elif quote == character:
                quote = None
        elif character == "," and quote is None:
            item = body[start:index].strip()
            if not item:
                raise ProgressError("ambiguous empty item in inline list")
            items.append(item)
            start = index + 1
    if quote is not None:
        raise ProgressError("unterminated quote in inline list")
    item = body[start:].strip()
    if not item:
        raise ProgressError("ambiguous trailing comma in inline list")
    items.append(item)
    return items


def _parse_scalar(value: str) -> Any:
    value = _strip_comment(value).strip()
    if not value:
        raise ProgressError("empty scalar where a value is required")
    if value.startswith("["):
        if not value.endswith("]"):
            raise ProgressError("unsupported or unterminated inline list syntax")
        return [_parse_scalar(item) for item in _split_inline_list(value)]
    if value.startswith("{") or value.endswith("}"):
        raise ProgressError("inline mappings are unsupported in required progress fields")
    if value[0] in {'"', "'"}:
        if len(value) < 2 or value[-1] != value[0]:
            raise ProgressError("unterminated quoted scalar")
        if value[0] == '"':
            try:
                return json.loads(value)
            except json.JSONDecodeError as exc:
                raise ProgressError(f"invalid JSON quoted scalar: {exc.msg}") from exc
        return value[1:-1].replace("''", "'")
    if _INTEGER_RE.fullmatch(value):
        try:
            return int(value)
        except ValueError as exc:
            raise ProgressError("invalid integer scalar") from exc
    lowered = value.casefold()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "~"}:
        return None
    if ":" in value:
        raise ProgressError(f"unsupported mapping-like scalar syntax: {value!r}")
    return value


def _parse_yaml_subset(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    # (indent, path, container, parent, key) where parent/key allow a pending
    # mapping value to be replaced by a block list on its first ``-`` item.
    stack: list[tuple[int, tuple[str, ...], Any, dict[str, Any] | None, str | None]] = []
    seen: set[tuple[str, ...]] = set()
    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    for line_number, raw in enumerate(lines, 1):
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise ProgressError(f"unsupported tab indentation at line {line_number}")
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped in {"---", "..."}:
            raise ProgressError("multiple or explicitly delimited YAML documents are unsupported")
        indent = len(raw) - len(raw.lstrip(" "))
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if stripped.startswith("-"):
            if not stack or not stripped.startswith("- "):
                raise ProgressError(f"unsupported block-list syntax at line {line_number}")
            marker = stack[-1]
            container = marker[2]
            parent = marker[3]
            key = marker[4]
            if parent is None or key is None:
                raise ProgressError(f"block list has no mapping owner at line {line_number}")
            if isinstance(container, dict):
                if container:
                    raise ProgressError(f"ambiguous mapping/list syntax at line {line_number}")
                values = parent[key]
                if isinstance(values, _ListMarker):
                    parent[key] = []
                    container = parent[key]
                    stack[-1] = (marker[0], marker[1], container, parent, key)
            if not isinstance(container, list):
                raise ProgressError(f"block list owner is not a list at line {line_number}")
            value = stripped[2:].strip()
            if not value:
                raise ProgressError(f"empty block-list item at line {line_number}")
            if ":" in value and not value.startswith(('"', "'")):
                item_key, item_value = value.split(":", 1)
                item_key = item_key.strip()
                if not _KEY_RE.fullmatch(item_key):
                    raise ProgressError(f"unsupported block-list mapping key at line {line_number}: {item_key!r}")
                item: dict[str, Any] = {}
                container.append(item)
                item_value = _strip_comment(item_value).strip()
                item[item_key] = _parse_scalar(item_value) if item_value else _ListMarker()
                stack.append((indent, marker[1] + ("[]", str(len(container) - 1)), item, container, None))
            else:
                container.append(_parse_scalar(value))
            continue
        if ":" not in stripped:
            raise ProgressError(f"unsupported mapping syntax at line {line_number}")
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        if not _KEY_RE.fullmatch(key):
            raise ProgressError(f"unsupported mapping key at line {line_number}: {key!r}")
        parent: dict[str, Any]
        if stack:
            if not isinstance(stack[-1][2], dict):
                raise ProgressError(f"mapping follows a list at line {line_number}")
            parent = stack[-1][2]
            pending_parent = stack[-1][3]
            pending_key = stack[-1][4]
            if pending_parent is not None and pending_key is not None and isinstance(pending_parent.get(pending_key), _ListMarker):
                pending_parent[pending_key] = parent
        else:
            parent = root
        path = (stack[-1][1] if stack else ()) + (key,)
        if path in seen:
            raise ProgressError("duplicate key in PROJECT_STATE.yaml: " + ".".join(path))
        seen.add(path)
        raw_value = _strip_comment(raw_value).strip()
        if not raw_value:
            parent[key] = _ListMarker()
            child: dict[str, Any] = {}
            stack.append((indent, path, child, parent, key))
        else:
            parent[key] = _parse_scalar(raw_value)
    # The template uses ``completed_chapters: []``.  Accept its empty block
    # spelling as well, while rejecting empty required scalar fields later.
    manuscript = root.get("manuscript")
    if isinstance(manuscript, dict) and isinstance(manuscript.get("completed_chapters"), _ListMarker):
        manuscript["completed_chapters"] = []
    return root


def _required_yaml_text(text: str) -> str:
    """Keep required sections while ignoring arbitrary project prose safely."""

    retained: list[str] = []
    active_top: str | None = None
    skipped_child_indent: int | None = None
    for line_number, raw in enumerate(text.replace("\r\n", "\n").replace("\r", "\n").splitlines(), 1):
        stripped = raw.strip()
        if stripped in {"---", "..."}:
            raise ProgressError(f"multiple or explicitly delimited YAML documents are unsupported at line {line_number}")
        if not stripped or stripped.startswith("#"):
            if skipped_child_indent is None and active_top is not None:
                retained.append(raw)
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if "\t" in raw[:indent]:
            raise ProgressError(f"unsupported tab indentation at line {line_number}")
        if indent == 0:
            if ":" not in stripped:
                active_top = None
                skipped_child_indent = None
                continue
            key = stripped.split(":", 1)[0].strip()
            active_top = key if key in _REQUIRED_TOP_LEVEL else None
            skipped_child_indent = None
            if active_top is not None:
                retained.append(raw)
            continue
        if active_top is None:
            continue
        if skipped_child_indent is not None:
            if indent > skipped_child_indent:
                continue
            skipped_child_indent = None
        children = _REQUIRED_CHILDREN.get(active_top)
        if children is not None and not stripped.startswith("-") and ":" in stripped:
            key = stripped.split(":", 1)[0].strip()
            if key not in children:
                skipped_child_indent = indent
                continue
        retained.append(raw)
    return "\n".join(retained) + ("\n" if retained else "")


def parse_project_state(path: str | Path) -> dict[str, Any]:
    """Parse schema-6 state using JSON or the documented narrow YAML subset."""

    state_path = Path(path)
    try:
        text = state_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise ProgressError(f"cannot read PROJECT_STATE.yaml: {exc}") from exc
    if not text.strip():
        raise ProgressError("PROJECT_STATE.yaml is empty")
    if text.lstrip().startswith("{"):
        try:
            parsed = json.loads(text, object_pairs_hook=_json_pairs)
        except (json.JSONDecodeError, ProgressError) as exc:
            raise ProgressError(f"invalid JSON/YAML state: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ProgressError("PROJECT_STATE.yaml root must be a mapping")
        return parsed
    return _parse_yaml_subset(_required_yaml_text(text))


def _mapping(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProgressError(f"required state field {path} must be a mapping")
    return value


def _required(state: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = state
    for key in path:
        if not isinstance(current, dict) or key not in current:
            raise ProgressError("missing required state field: " + ".".join(path))
        current = current[key]
    return current


def _integer(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ProgressError(f"required state field {path} must be an integer")
    if value < 0:
        raise ProgressError(f"required state field {path} must be non-negative")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProgressError(f"required state field {path} must be a non-empty string")
    return value.strip()


def _normalise_required_state(state: dict[str, Any]) -> dict[str, Any]:
    schema_version = _integer(_required(state, ("schema_version",)), "schema_version")
    pipeline = _mapping(_required(state, ("pipeline",)), "pipeline")
    manuscript = _mapping(_required(state, ("manuscript",)), "manuscript")
    gates = _mapping(_required(state, ("gates",)), "gates")
    current_phase = _string(pipeline.get("current_phase"), "pipeline.current_phase")
    pipeline_status = _string(pipeline.get("status"), "pipeline.status")
    manuscript_status = _string(manuscript.get("status"), "manuscript.status")
    completed = manuscript.get("completed_chapters")
    if not isinstance(completed, list):
        raise ProgressError("required state field manuscript.completed_chapters must be an integer list")
    completed_numbers: list[int] = []
    for index, item in enumerate(completed):
        completed_numbers.append(_integer(item, f"manuscript.completed_chapters[{index}]"))
    if len(set(completed_numbers)) != len(completed_numbers):
        raise ProgressError("manuscript.completed_chapters contains duplicate chapter numbers")
    if completed_numbers != sorted(completed_numbers):
        raise ProgressError("manuscript.completed_chapters must be in ascending order")
    gate_values = {name: _string(gates.get(name), f"gates.{name}") for name in _ALL_GATES}
    return {
        "schema_version": schema_version,
        "current_phase": current_phase,
        "pipeline_status": pipeline_status,
        "manuscript_status": manuscript_status,
        "chapter_count_planned": _integer(manuscript.get("chapter_count_planned"), "manuscript.chapter_count_planned"),
        "completed_chapters": completed_numbers,
        "word_count_actual": _integer(manuscript.get("word_count_actual"), "manuscript.word_count_actual"),
        "gates": gate_values,
    }


def _canonical_chapters(book_root: Path) -> tuple[list[int], int, list[str]]:
    """Use the exporter's canonical reader and word counter verbatim.

    The import is intentionally local: ``export_book`` imports this module for
    its complete-pipeline preflight, while the CLI imports the exporter only
    when it needs to inspect a real chapter set.
    """
    chapter_root = book_root / "manuscript" / "chapters"
    if not chapter_root.is_dir():
        return [], 0, []
    # A directory containing only the writer lock is a valid empty new book.
    if not any(path.is_file() and path.suffix.casefold() == ".md" for path in chapter_root.iterdir()):
        return [], 0, []
    try:
        from export_book import ExportError, count_prose_words, discover_chapters

        chapters = discover_chapters(chapter_root)
        return [chapter.number for chapter in chapters], sum(count_prose_words(chapter) for chapter in chapters), []
    except (ExportError, OSError, UnicodeError) as exc:
        return [], 0, [str(exc)]


def _mismatch(mismatches: list[dict[str, str]], field: str, message: str, recovery: str) -> None:
    mismatches.append({"field": field, "message": message, "recovery": recovery})


def reconcile_book(
    book_dir: str | Path,
    *,
    complete: bool = False,
    expected_chapters: int | None = None,
    min_words: int | None = None,
    max_words: int | None = None,
) -> dict[str, Any]:
    """Return a read-only reconciliation report for startup or complete export."""

    book_root = Path(book_dir).resolve()
    state_path = book_root / "PROJECT_STATE.yaml"
    chapter_numbers, actual_words, chapter_errors = _canonical_chapters(book_root)
    mismatches: list[dict[str, str]] = []
    recovery_steps: list[str] = []
    if not state_path.exists() and not chapter_numbers and not chapter_errors:
        if complete:
            _mismatch(mismatches, "PROJECT_STATE.yaml", "complete export requires a schema-6 progress state", "initialize the state and complete the pipeline before exporting")
        else:
            return {
                "schema_version": 1,
                "book_dir": str(book_root),
                "mode": "complete" if complete else "resume",
                "status": "empty",
                "ok": True,
                "canonical": {"chapter_numbers": [], "chapter_count": 0, "word_count": 0, "word_count_method": _WORD_COUNT_METHOD},
                "mismatches": [],
                "recovery_steps": ["initialize PROJECT_STATE.yaml from the schema-6 template before drafting"],
            }
    if chapter_errors:
        for error in chapter_errors:
            _mismatch(mismatches, "manuscript/chapters", error, "repair the canonical chapter set, then rerun this read-only check")
    if not state_path.is_file():
        _mismatch(mismatches, "PROJECT_STATE.yaml", "progress state is missing", "restore or initialize a schema-6 PROJECT_STATE.yaml")
        return {
            "schema_version": 1,
            "book_dir": str(book_root),
            "mode": "complete" if complete else "resume",
            "status": "mismatch",
            "ok": False,
            "canonical": {"chapter_numbers": chapter_numbers, "chapter_count": len(chapter_numbers), "word_count": actual_words, "word_count_method": _WORD_COUNT_METHOD},
            "mismatches": mismatches,
            "recovery_steps": [item["recovery"] for item in mismatches],
        }
    try:
        state = _normalise_required_state(parse_project_state(state_path))
    except ProgressError as exc:
        _mismatch(mismatches, "PROJECT_STATE.yaml", str(exc), "repair the state using the documented schema-6 fields; this tool never auto-corrects it")
        return {
            "schema_version": 1,
            "book_dir": str(book_root),
            "mode": "complete" if complete else "resume",
            "status": "invalid",
            "ok": False,
            "canonical": {"chapter_numbers": chapter_numbers, "chapter_count": len(chapter_numbers), "word_count": actual_words, "word_count_method": _WORD_COUNT_METHOD},
            "mismatches": mismatches,
            "recovery_steps": [item["recovery"] for item in mismatches],
        }
    if state["schema_version"] != 6:
        _mismatch(mismatches, "schema_version", f"expected schema_version 6, found {state['schema_version']}", "migrate the state to the schema-6 template before resuming")
    if not _PHASE_RE.fullmatch(state["current_phase"]):
        _mismatch(mismatches, "pipeline.current_phase", f"unsupported phase label: {state['current_phase']!r}", "set current_phase to one documented Phase 0 through Phase 7 label")
    actual_numbers = chapter_numbers
    if state["completed_chapters"] != actual_numbers:
        _mismatch(mismatches, "manuscript.completed_chapters", f"state lists {state['completed_chapters']} but canonical chapters are {actual_numbers}", "reconcile the state after verified chapter saves; do not manually claim a chapter")
    if state["word_count_actual"] != actual_words:
        _mismatch(mismatches, "manuscript.word_count_actual", f"state records {state['word_count_actual']} words but canonical prose counts {actual_words}", "recount canonical prose with this helper and update state after a verified save")
    if complete and state["chapter_count_planned"] != len(actual_numbers):
        _mismatch(mismatches, "manuscript.chapter_count_planned", f"complete export plans {state['chapter_count_planned']} chapters but canonical count is {len(actual_numbers)}", "finish the approved chapter set and reconcile the planned count before export")
    elif state["chapter_count_planned"] < len(actual_numbers) and actual_numbers:
        _mismatch(mismatches, "manuscript.chapter_count_planned", f"planned chapter count {state['chapter_count_planned']} is below canonical count {len(actual_numbers)}", "repair the approved chapter contract or canonical set before continuing")
    if expected_chapters is not None:
        if expected_chapters < 1:
            _mismatch(mismatches, "expected_chapters", "expected chapter count must be positive", "pass the approved positive chapter count")
        elif state["chapter_count_planned"] != expected_chapters:
            _mismatch(mismatches, "manuscript.chapter_count_planned", f"state plans {state['chapter_count_planned']} chapters but complete export requires {expected_chapters}", "use the approved intake/outline chapter count consistently")
        elif len(actual_numbers) != expected_chapters:
            _mismatch(mismatches, "canonical chapter count", f"complete export requires {expected_chapters} chapters but found {len(actual_numbers)}", "finish or repair the canonical chapter set before export")
    if min_words is not None and actual_words < min_words:
        _mismatch(mismatches, "word_count", f"canonical prose count {actual_words} is below min_words {min_words}", "finish the approved manuscript or revise the contract before complete export")
    if max_words is not None and actual_words > max_words:
        _mismatch(mismatches, "word_count", f"canonical prose count {actual_words} is above max_words {max_words}", "compress the approved manuscript or revise the contract before complete export")
    if complete:
        if not actual_numbers:
            _mismatch(mismatches, "manuscript/chapters", "complete export has no canonical chapters", "finish and verify the canonical chapter set before export")
        if not state["current_phase"].startswith("Phase 7:"):
            _mismatch(mismatches, "pipeline.current_phase", f"complete export requires Phase 7; found {state['current_phase']!r}", "advance through the earlier phases and checkpoint them before Phase 7 export")
        if state["pipeline_status"].casefold() in _INCOMPLETE_STATUSES - {"in_progress"}:
            _mismatch(mismatches, "pipeline.status", f"pipeline status is unfinished: {state['pipeline_status']!r}", "finish or truthfully record the earlier pipeline work before export")
        if state["manuscript_status"].casefold() in _INCOMPLETE_STATUSES:
            _mismatch(mismatches, "manuscript.status", f"manuscript status is unfinished: {state['manuscript_status']!r}", "finish the canonical manuscript and update its status before export")
        for gate in _REQUIRED_GATES:
            status = state["gates"][gate]
            if status.casefold() in _INCOMPLETE_STATUSES:
                _mismatch(mismatches, f"gates.{gate}", f"required earlier gate is unfinished: {status!r}", "record the gate outcome, including a truthful failed or warning result, before export")
        editorial_status = state["gates"]["editorial_package"]
        if editorial_status.casefold() in _INCOMPLETE_STATUSES - {"in_progress"}:
            _mismatch(mismatches, "gates.editorial_package", f"editorial package gate is unfinished: {editorial_status!r}", "start Phase 7 packaging or record its finished outcome before export")
    status = "ok" if not mismatches else "mismatch"
    if not chapter_numbers and not complete and not mismatches:
        status = "empty"
    recovery_steps = list(dict.fromkeys(item["recovery"] for item in mismatches))
    return {
        "schema_version": 1,
        "book_dir": str(book_root),
        "mode": "complete" if complete else "resume",
        "status": status,
        "ok": not mismatches,
        "state": state,
        "canonical": {"chapter_numbers": actual_numbers, "chapter_count": len(actual_numbers), "word_count": actual_words, "word_count_method": _WORD_COUNT_METHOD},
        "mismatches": mismatches,
        "recovery_steps": recovery_steps,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Book Genesis progress reconciliation.")
    parser.add_argument("--book-dir", default=".")
    parser.add_argument("--complete", action="store_true", help="apply the stricter Phase 7 complete-export checks")
    parser.add_argument("--expected-chapters", type=int)
    parser.add_argument("--min-words", type=int)
    parser.add_argument("--max-words", type=int)
    args = parser.parse_args(argv)
    report = reconcile_book(
        args.book_dir,
        complete=args.complete,
        expected_chapters=args.expected_chapters,
        min_words=args.min_words,
        max_words=args.max_words,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
