"""Read-only verification of delivery and reader coverage for the current text.

Saved passes are not transferable to changed chapters. This helper checks the
original validation receipts as well as the raw reports; it never regenerates
a receipt to make an old read look current, calls a model, or approves a book.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from export_book import (
    BookMetadata, ExportError, assemble_manuscript, discover_chapters,
    validate_docx, validate_epub, validate_pdf, word_count_receipt,
)
from validate_blind_reader import validate_blind_reader_report


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=_pairs)
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path.name}")
    return value


def _inside(root: Path, relative: Any) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError("file reference must be a nonempty relative path")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"file reference must stay inside its folder: {relative}")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"file reference escapes its folder: {relative}")
    if not resolved.is_file():
        raise ValueError(f"missing file: {relative}")
    return resolved


def verify_delivery(book_root: Path, chapters: list[Any]) -> dict[str, Any]:
    delivery = book_root / "delivery"
    receipt_path = delivery / "export-receipt.json"
    if not receipt_path.exists():
        return {"status": "pending", "formats": [], "errors": ["no export receipt"]}
    errors: list[str] = []
    formats: list[str] = []
    try:
        receipt_path = _inside(book_root, "delivery/export-receipt.json")
        receipt = _json(receipt_path)
        if receipt.get("schema_version") != 1:
            raise ValueError("unsupported export receipt schema")
        expected_sources = [
            {"number": item.number, "path": item.path.name, "title": item.title, "sha256": item.sha256}
            for item in chapters
        ]
        if receipt.get("source_chapters") != expected_sources:
            errors.append("export source chapters differ from the current manuscript")
        if receipt.get("chapter_count") != len(chapters) or not chapters:
            errors.append("export chapter count differs from the current manuscript")
        saved_count = receipt.get("word_count")
        current_count = word_count_receipt(chapters)
        if (
            not isinstance(saved_count, dict)
            or saved_count.get("method") not in {"whitespace_split_prose_v1", "whitespace_split_prose_v2"}
            or saved_count.get("total") != current_count["total"]
            or saved_count.get("chapters") != current_count["chapters"]
        ):
            errors.append("export prose counts differ from the current manuscript")
        outputs = receipt.get("outputs")
        if not isinstance(outputs, dict) or "manuscript.md" not in outputs:
            raise ValueError("export receipt is missing manuscript.md")
        epub_name = f"{receipt.get('slug')}.epub"
        if epub_name not in outputs:
            raise ValueError("export receipt is missing its EPUB")
        validation = receipt.get("validation")
        if not isinstance(validation, dict) or validation.get("status") != "passed":
            errors.append("export receipt does not record successful format validation")
        for name, record in outputs.items():
            path = _inside(delivery, name)
            if not isinstance(record, dict) or record.get("sha256") != _digest(path):
                errors.append(f"export output hash differs: {name}")
                continue
            suffix = path.suffix.lower()
            if name == "manuscript.md":
                metadata = BookMetadata(receipt["title"], receipt["author"], receipt["language"], receipt["slug"])
                if path.read_text(encoding="utf-8") != assemble_manuscript(chapters, metadata):
                    errors.append("assembled manuscript differs from the current canonical text")
            elif suffix == ".epub":
                validate_epub(path, len(chapters))
            elif suffix == ".docx":
                validate_docx(path, chapters)
            elif suffix == ".pdf":
                validate_pdf(path, chapters)
            else:
                raise ValueError(f"unsupported deliverable in receipt: {name}")
            formats.append(suffix.lstrip("."))
        return {
            "status": "stale" if errors else "delivered",
            "scope": receipt.get("delivery_scope", "legacy_unspecified"),
            "formats": sorted(formats),
            "receipt_sha256": _digest(receipt_path),
            "errors": errors,
        }
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, ExportError) as exc:
        return {"status": "invalid", "formats": sorted(formats), "errors": errors + [str(exc)]}


def verify_reviews(book_root: Path, chapters: list[Any], index_path: Path | None) -> dict[str, Any]:
    if index_path is None:
        return {"status": "not_run", "scopes": [], "errors": ["no current-text review index supplied"]}
    try:
        if not index_path.resolve().is_relative_to(book_root):
            raise ValueError("review index must be inside the book folder")
        index = _json(index_path)
        if index.get("schema_version") != 1:
            raise ValueError("unsupported review index schema")
        scopes = index.get("scopes")
        if not isinstance(scopes, list) or not scopes:
            raise ValueError("review index must declare nonempty scopes")
        canonical = {item.path.name: item for item in chapters}
        seen_scopes: set[str] = set()
        results: list[dict[str, Any]] = []
        for scope in scopes:
            if not isinstance(scope, dict):
                raise ValueError("each review scope must be an object")
            name = scope.get("scope")
            if not isinstance(name, str) or not name.strip() or name in seen_scopes:
                raise ValueError("review scopes must have unique nonempty names")
            seen_scopes.add(name)
            names = scope.get("chapters")
            if not isinstance(names, list) or not names or len(set(names)) != len(names):
                raise ValueError(f"{name}: declare a nonempty unique chapter list")
            if any(item not in canonical for item in names):
                raise ValueError(f"{name}: scope references a noncanonical chapter")
            readers = scope.get("readers")
            if not isinstance(readers, list) or len(readers) != 4:
                raise ValueError(f"{name}: a panel requires exactly four declared readers")
            valid: list[dict[str, str]] = []
            issues: list[str] = []
            seen_readers: set[str] = set()
            seen_reports: set[Path] = set()
            for row in readers:
                try:
                    if not isinstance(row, dict):
                        raise ValueError("reader entry must be an object")
                    reader = row.get("reader")
                    if not isinstance(reader, str) or not reader.strip() or reader in seen_readers:
                        raise ValueError("duplicate or empty reader identity")
                    seen_readers.add(reader)
                    report_path = _inside(book_root, row.get("report"))
                    if report_path in seen_reports:
                        raise ValueError("one raw report cannot count as two readers")
                    seen_reports.add(report_path)
                    receipt_path = _inside(book_root, row.get("validation"))
                    original = _json(receipt_path)
                    if original.get("schema_version") != 1 or original.get("valid") is not True or original.get("status") != "passed":
                        raise ValueError("original reader validation did not pass")
                    fresh = validate_blind_reader_report([canonical[item].path for item in names], report_path)
                    if not fresh["valid"]:
                        raise ValueError("raw report is invalid: " + "; ".join(fresh["errors"]))
                    if original.get("report_sha256") != fresh["report_sha256"]:
                        raise ValueError("raw report hash differs from its original receipt")
                    old_sources = original.get("source_chapters")
                    if not isinstance(old_sources, list):
                        raise ValueError("original receipt has no source bindings")
                    bindings = [(Path(item["path"]).name, item["sha256"], item["bytes"]) for item in old_sources]
                    current = [(Path(item["path"]).name, item["sha256"], item["bytes"]) for item in fresh["source_chapters"]]
                    if bindings != current:
                        raise ValueError("reader evidence is stale or covers different chapters")
                    raw = report_path.read_text(encoding="utf-8-sig").strip()
                    if raw.startswith("```"):
                        raw = "\n".join(raw.splitlines()[1:-1])
                    report = json.loads(raw, object_pairs_hook=_pairs)
                    if report.get("reader") != reader:
                        raise ValueError("raw report identity differs from declared reader")
                    if "compare" in report:
                        raise ValueError("a comparison vote is not a current-draft panel read")
                    valid.append({"reader": reader, "turn_page": report["turn_page"]})
                except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
                    issues.append(f"{row.get('reader', 'unknown') if isinstance(row, dict) else 'unknown'}: {exc}")
            complete = len(valid) == 4 and not issues
            results.append({
                "scope": name, "chapters": names, "status": "current" if complete else "incomplete",
                "valid_readers": valid, "errors": issues,
                "majority_turn_page": complete and sum(row["turn_page"] == "yes" for row in valid) >= 3,
            })
        return {"status": "current" if all(item["status"] == "current" for item in results) else "incomplete", "scopes": results, "errors": []}
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        return {"status": "invalid", "scopes": [], "errors": [str(exc)]}


def verify_book(book_dir: str | Path, review_index: str | Path | None = None) -> dict[str, Any]:
    root = Path(book_dir).resolve()
    chapter_root = root / "manuscript/chapters"
    try:
        if not chapter_root.resolve().is_relative_to(root):
            raise ValueError("chapter directory escapes the book folder")
        chapters = discover_chapters(chapter_root)
        if any(not item.path.resolve().is_relative_to(chapter_root.resolve()) for item in chapters):
            raise ValueError("canonical chapter escapes the chapter folder")
    except (OSError, UnicodeError, ValueError, ExportError) as exc:
        return {"schema_version": 1, "book_dir": str(root), "delivery": {"status": "invalid", "errors": [str(exc)]}, "reviews": {"status": "not_run"}, "publication_approval": "not_assessed"}
    index = Path(review_index) if review_index is not None else None
    if index is not None:
        index = (root / index).resolve() if not index.is_absolute() else index.resolve()
    result = {
        "schema_version": 1, "book_dir": str(root),
        "canonical": {"chapter_count": len(chapters), "word_count": word_count_receipt(chapters)},
        "delivery": verify_delivery(root, chapters),
        "reviews": verify_reviews(root, chapters, index),
        "literary_quality": "not_assessed_by_this_tool", "publication_approval": "not_assessed",
    }
    try:
        current = discover_chapters(chapter_root)
        initial_signature = [(item.path.name, item.sha256) for item in chapters]
        if [(item.path.name, item.sha256) for item in current] != initial_signature:
            raise ValueError("canonical manuscript changed during verification; rerun on a stable snapshot")
    except (OSError, UnicodeError, ValueError, ExportError) as exc:
        result["delivery"]["status"] = "stale"
        result["delivery"].setdefault("errors", []).append(str(exc))
        result["reviews"]["status"] = "stale"
        result["reviews"].setdefault("errors", []).append(str(exc))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--book-dir", required=True)
    parser.add_argument("--review-index")
    parser.add_argument("--check", choices=("delivery", "reviews", "all"), default="all")
    args = parser.parse_args(argv)
    result = verify_book(args.book_dir, args.review_index)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    delivered = result["delivery"]["status"] == "delivered"
    reviewed = result["reviews"]["status"] == "current"
    return 0 if (delivered if args.check == "delivery" else reviewed if args.check == "reviews" else delivered and reviewed) else 1


if __name__ == "__main__":
    raise SystemExit(main())
