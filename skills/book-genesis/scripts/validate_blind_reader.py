"""Validate a blind-reader JSON report against the prose it was assigned.

The validator is deliberately conservative. It checks report structure and
enums, but it does not repair a report or infer what a reader meant. A report
that cannot be verified is invalid and must be retried by the host.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from prepare_rubric import build_catalog, canonical_json, catalog_digest


FLAGS = {
    "slow_start",
    "confusing",
    "flat_voice",
    "over_explained",
    "machine_prose",
    "exposition_dump",
    "stiff_dialogue",
    "no_stakes",
    "predictable",
    "emotion_missed",
    "continuity_doubt",
    "cliche",
}
TURN_PAGES = {"yes", "no", "unsure"}
CONFIDENCE = {"low", "medium", "high"}
COMPARE = {"A", "B", "same"}

REQUIRED_FIELDS = {
    "reader",
    "turn_page",
    "stopped_at",
    "why_stopped",
    "remember_tomorrow",
    "confused_by",
    "flags",
    "strongest_passage",
    "weakest_passage",
    "machine_tells",
    "felt",
    "confidence",
}
OPTIONAL_FIELDS = {"compare"}

QUOTE_FIELDS = {
    "stopped_at": "quote",
    "strongest_passage": "quote",
    "weakest_passage": "quote",
}


_INLINE_EMPHASIS = re.compile(
    r"(?<!\w)(?P<mark>\*\*|\*|__|_)(?=\S)(?P<text>[^\r\n]+?\S)(?P=mark)(?!\w)"
)


def _strip_balanced_inline_emphasis(value: str) -> str:
    """Remove balanced Markdown emphasis delimiters without changing words.

    Delimiters are removed only when they pair on the same line, surround
    non-whitespace text, and sit at Markdown-like word boundaries. Unbalanced
    or embedded marker characters remain part of the candidate and therefore
    still fail exact matching.
    """

    while True:
        value, replacements = _INLINE_EMPHASIS.subn(r"\g<text>", value)
        if replacements == 0:
            return value


def _normalise_quote(value: str) -> str:
    """Allow whitespace, typographic quotes, and balanced inline emphasis."""

    value = value.translate(
        str.maketrans(
            {
                "“": '"',
                "”": '"',
                "„": '"',
                "‟": '"',
                "‘": "'",
                "’": "'",
                "‚": "'",
                "‛": "'",
            }
        )
    )
    value = _strip_balanced_inline_emphasis(value)
    return re.sub(r"\s+", " ", value).strip()


def _strip_one_markdown_fence(text: str) -> str:
    lines = text.strip().splitlines()
    if not lines or not lines[0].lstrip().startswith("```"):
        return text.strip()
    if len(lines) < 3 or lines[-1].strip() != "```":
        return text.strip()
    opening = lines[0].strip()
    if opening not in {"```", "```json", "```JSON"}:
        return text.strip()
    return "\n".join(lines[1:-1]).strip()


def _nonempty_string(value: Any, field: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty string")
        return None
    return value.strip()


def _enum(value: Any, field: str, allowed: set[str], errors: list[str]) -> None:
    if not isinstance(value, str) or value not in allowed:
        errors.append(f"{field} must be one of: {', '.join(sorted(allowed))}")


def _is_exact_quote(quote: Any, field: str, sources: list[tuple[Path, str]], errors: list[str]) -> bool:
    if not isinstance(quote, str) or not quote.strip():
        errors.append(f"{field}.quote must be a non-empty string")
        return False
    candidate = _normalise_quote(quote)
    for path, prose in sources:
        if candidate in _normalise_quote(prose):
            return True
    errors.append(f"{field}.quote is not an exact contiguous quote from the assigned chapter(s)")
    return False


def _validate_reason_object(
    value: Any,
    field: str,
    sources: list[tuple[Path, str]],
    errors: list[str],
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object with quote and reason")
        return
    if set(value) != {"quote", "reason"}:
        errors.append(f"{field} must contain only quote and reason")
    _is_exact_quote(value.get("quote"), field, sources, errors)
    _nonempty_string(value.get("reason"), f"{field}.reason", errors)


def _validate_quote_only_object(
    value: Any,
    field: str,
    sources: list[tuple[Path, str]],
    errors: list[str],
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{field} must be null or an object with quote")
        return
    if set(value) != {"quote"}:
        errors.append(f"{field} must contain only quote")
    _is_exact_quote(value.get("quote"), field, sources, errors)


def _validate_list_of_reason_objects(
    value: Any,
    field: str,
    sources: list[tuple[Path, str]],
    errors: list[str],
) -> None:
    if not isinstance(value, list):
        errors.append(f"{field} must be an array")
        return
    for index, item in enumerate(value):
        _validate_reason_object(item, f"{field}[{index}]", sources, errors)


def _validate_report(report: Any, sources: list[tuple[Path, str]]) -> list[str]:
    errors: list[str] = []
    if not isinstance(report, dict):
        return ["report must be a JSON object"]

    missing = sorted(REQUIRED_FIELDS - set(report))
    if missing:
        errors.append("missing required fields: " + ", ".join(missing))
    unknown = sorted(set(report) - REQUIRED_FIELDS - OPTIONAL_FIELDS)
    if unknown:
        errors.append("unknown fields: " + ", ".join(unknown))

    _nonempty_string(report.get("reader"), "reader", errors)
    _enum(report.get("turn_page"), "turn_page", TURN_PAGES, errors)
    _enum(report.get("confidence"), "confidence", CONFIDENCE, errors)
    if "compare" in report:
        _enum(report["compare"], "compare", COMPARE, errors)

    stopped_at = report.get("stopped_at")
    if stopped_at is not None:
        _validate_quote_only_object(stopped_at, "stopped_at", sources, errors)
        if report.get("why_stopped") is None:
            errors.append("why_stopped must be an object when stopped_at has a quote")
    elif report.get("why_stopped") is not None:
        errors.append("why_stopped must be null when stopped_at is null")
    if stopped_at is not None and report.get("why_stopped") is not None:
        why = report["why_stopped"]
        if not isinstance(why, dict) or set(why) != {"reason"}:
            errors.append("why_stopped must contain only reason")
        elif _nonempty_string(why.get("reason"), "why_stopped.reason", errors) is None:
            pass

    _validate_list_of_reason_objects(report.get("remember_tomorrow"), "remember_tomorrow", sources, errors)
    _validate_list_of_reason_objects(report.get("confused_by"), "confused_by", sources, errors)

    flags = report.get("flags")
    if not isinstance(flags, list):
        errors.append("flags must be an array")
    else:
        for index, item in enumerate(flags):
            field = f"flags[{index}]"
            if not isinstance(item, dict) or set(item) != {"flag", "quote"}:
                errors.append(f"{field} must contain only flag and quote")
                continue
            if not isinstance(item.get("flag"), str) or item.get("flag") not in FLAGS:
                errors.append(f"{field}.flag is not an allowed flag")
            _is_exact_quote(item.get("quote"), field, sources, errors)

    _validate_reason_object(report.get("strongest_passage"), "strongest_passage", sources, errors)
    _validate_reason_object(report.get("weakest_passage"), "weakest_passage", sources, errors)

    machine_tells = report.get("machine_tells")
    if not isinstance(machine_tells, list):
        errors.append("machine_tells must be an array")
    else:
        for index, item in enumerate(machine_tells):
            field = f"machine_tells[{index}]"
            if not isinstance(item, dict) or set(item) != {"tell", "quote"}:
                errors.append(f"{field} must contain only tell and quote")
                continue
            _nonempty_string(item.get("tell"), f"{field}.tell", errors)
            _is_exact_quote(item.get("quote"), field, sources, errors)

    felt = report.get("felt")
    if not isinstance(felt, dict) or set(felt) != {"emotion", "reason"}:
        errors.append("felt must contain only emotion and reason")
    else:
        emotion = _nonempty_string(felt.get("emotion"), "felt.emotion", errors)
        _nonempty_string(felt.get("reason"), "felt.reason", errors)
        if emotion is not None and len(emotion) > 120:
            errors.append("felt.emotion must be a short emotion phrase, not copied prose")
        if emotion is not None and any(
            len(_normalise_quote(emotion)) >= 20
            and _normalise_quote(emotion) in _normalise_quote(prose)
            for _, prose in sources
        ):
            errors.append("felt.emotion appears to be copied prose, not an emotion phrase")

    return errors


def validate_blind_reader_report(
    chapter_paths: list[Path], report_path: Path, *, expected_reader: str | None = None,
    catalog_path: Path | None = None,
) -> dict[str, Any]:
    """Return a JSON-serialisable receipt; never mutates source or report."""

    errors: list[str] = []
    if expected_reader is not None and (not isinstance(expected_reader, str) or not expected_reader.strip()):
        errors.append("expected_reader must be a non-empty assigned reader name")
    source_records: list[dict[str, Any]] = []
    sources: list[tuple[Path, str]] = []
    for path in chapter_paths:
        try:
            data = path.read_bytes()
            text = data.decode("utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"chapter {path}: cannot read UTF-8 source: {exc}")
            continue
        source_records.append(
            {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
        )
        sources.append((path, text))

    parse_failed = False
    try:
        report_bytes = sys.stdin.buffer.read() if str(report_path) == "-" else report_path.read_bytes()
        raw = report_bytes.decode("utf-8-sig")
        report_text = _strip_one_markdown_fence(raw)
        report = json.loads(report_text, object_pairs_hook=_unique_object, parse_constant=_no_constant)
    except (OSError, UnicodeError) as exc:
        report_bytes = b""
        report = None
        parse_failed = True
        errors.append(f"report: cannot read UTF-8 JSON: {exc}")
    except json.JSONDecodeError as exc:
        report = None
        parse_failed = True
        errors.append(f"report: malformed JSON at line {exc.lineno} column {exc.colno}")
    except ValueError as exc:
        report = None
        parse_failed = True
        errors.append(f"report: {exc}")

    resolved: list[dict[str, Any]] = []
    catalog_hash = None
    if isinstance(report, dict) and "schema_version" in report:
        if type(report["schema_version"]) is not int or report["schema_version"] not in (2, 3):
            errors.append("unsupported reader report schema")
        else:
            report, catalog_hash, resolved = _resolve_passages(report, chapter_paths, catalog_path, errors)
    elif catalog_path is not None:
        errors.append("a catalog requires a schema 2 or 3 passage-reference report")

    if parse_failed:
        pass
    elif not isinstance(report, dict):
        errors.append("report must be a JSON object")
    elif sources:
        errors.extend(_validate_report(report, sources))
    else:
        errors.append("report: no readable assigned chapter source")

    if isinstance(report, dict) and expected_reader is not None and report.get("reader") != expected_reader:
        errors.append("report.reader does not match the assigned reader")

    for record in source_records:
        try:
            if hashlib.sha256(Path(record["path"]).read_bytes()).hexdigest() != record["sha256"]:
                errors.append("assigned source changed during validation")
        except OSError as exc:
            errors.append(f"assigned source became unreadable during validation: {exc}")

    valid = not errors
    receipt = {
        "schema_version": 1,
        "status": "passed" if valid else "invalid",
        "valid": valid,
        "source_chapters": source_records,
        "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "errors": errors,
    }
    if expected_reader is not None:
        receipt["expected_reader"] = expected_reader
    if catalog_hash is not None:
        receipt["catalog_sha256"] = catalog_hash
        receipt["resolved_evidence"] = resolved
    return receipt


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _no_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _resolve_passages(report: dict, chapter_paths: list[Path], catalog_path: Path | None,
                      errors: list[str]) -> tuple[dict, str | None, list[dict]]:
    """Create a validation view, never edit or repair the raw reader response."""
    resolved = []
    passages = {}
    digest = None
    try:
        if catalog_path is None:
            raise ValueError("passage references require a frozen --catalog")
        catalog = json.loads(catalog_path.read_text(encoding="utf-8-sig"),
                             object_pairs_hook=_unique_object, parse_constant=_no_constant)
        if report["schema_version"] == 3:
            from build_comparison import verify_comparison_catalog
            catalog = verify_comparison_catalog(catalog, chapter_paths)
            passages = {p["id"]: {"version": c["label"], "quote": p["text"]}
                        for c in catalog["sources"] for p in c["passages"]}
        else:
            if canonical_json(catalog) != canonical_json(build_catalog(chapter_paths)):
                raise ValueError("catalog differs from the complete current assigned prose; obtain a fresh read")
            passages = {p["id"]: {"chapter": c["chapter"], "quote": p["text"]}
                        for c in catalog["chapters"] for p in c["passages"]}
        digest = catalog_digest(catalog)
        if report.get("catalog_sha256") != digest:
            raise ValueError("report is bound to a different evidence catalog")
    except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
        errors.append(f"evidence catalog: {exc}")

    view = copy.deepcopy(report)
    view.pop("schema_version", None)
    view.pop("catalog_sha256", None)
    if report["schema_version"] == 2 and "compare" in view:
        errors.append("schema 2 is for current-draft reads, not A/B comparisons")
    elif report["schema_version"] == 3 and "compare" not in view:
        errors.append("schema 3 requires an anonymous comparison vote")

    def resolve(item: Any, location: str) -> None:
        if not isinstance(item, dict):
            return  # The ordinary shape validation supplies the error.
        pid = item.pop("passage_id", None)
        if "quote" in item:
            errors.append(f"{location}: use only passage_id, not a copied quote")
        if not isinstance(pid, str) or pid not in passages:
            errors.append(f"{location}: unknown passage_id")
            item["quote"] = ""
            return
        passage = passages[pid]
        item["quote"] = passage["quote"]
        resolved.append({"location": location, "passage_id": pid, **passage})

    for field in ("stopped_at", "strongest_passage", "weakest_passage"):
        if view.get(field) is not None:
            resolve(view[field], field)
    for field in ("remember_tomorrow", "confused_by", "flags", "machine_tells"):
        if isinstance(view.get(field), list):
            for index, item in enumerate(view[field]):
                resolve(item, f"{field}[{index}]")
    return view, digest, resolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapter", action="append", required=True, help="assigned chapter source; repeatable")
    parser.add_argument("--report", required=True, help="raw JSON report path, or - for stdin")
    parser.add_argument("--expected-reader", help="exact assigned identity; a mismatch is invalid, never renamed")
    parser.add_argument("--catalog", type=Path, help="Frozen complete assigned prose for current-draft or A/B passage references")
    args = parser.parse_args(argv)
    receipt = validate_blind_reader_report(
        [Path(value) for value in args.chapter], Path(args.report), expected_reader=args.expected_reader,
        catalog_path=args.catalog,
    )
    json.dump(receipt, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if receipt["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
