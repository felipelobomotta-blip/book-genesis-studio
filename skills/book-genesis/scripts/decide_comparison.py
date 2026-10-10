"""Translate validated anonymous votes without model-written tally code.

Only a complete, decisive three-of-four majority authorizes promotion here.
An ambiguous tie stays rejected pending separate defect evidence; the number
of complaints made by a voter is not a per-version defect measurement.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from prepare_rubric import catalog_digest
from validate_blind_reader import validate_blind_reader_report, _unique_object, _no_constant, _strip_one_markdown_fence


def _read(path: Path, *, fenced: bool = False):
    text = path.read_text(encoding="utf-8-sig")
    return json.loads(_strip_one_markdown_fence(text) if fenced else text,
                      object_pairs_hook=_unique_object, parse_constant=_no_constant)


def _hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _resolve(base: Path, value) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("evidence paths must be nonempty strings")
    return (base / value).resolve()


def decide(manifest_path: Path, index_path: Path, chapter: int) -> dict:
    if type(chapter) is not int or chapter < 1:
        raise ValueError("chapter must be a positive integer")
    manifest_path, index_path = manifest_path.resolve(), index_path.resolve()
    manifest, index = _read(manifest_path), _read(index_path)
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or not isinstance(index, dict):
        raise ValueError("comparison needs its original private manifest and a report index")
    rows = manifest.get("readers")
    if not isinstance(rows, list) or len(rows) != 4 or any(not isinstance(row, dict) for row in rows):
        raise ValueError("comparison needs four assigned readers")
    if len({row["reader"] for row in rows}) != 4 or len({row["persona"] for row in rows}) != 4 or set(index) != {row["persona"] for row in rows}:
        raise ValueError("reader identities and report index must match all four assignments")
    sources = [manifest["accepted"], manifest["candidate"], *manifest.get("context", [])]
    paths = [Path(row["path"]) for row in sources]
    guards = [(manifest_path, _hash(manifest_path)), (index_path, _hash(index_path))]
    for record, path in zip(sources, paths):
        if _hash(path) != record["sha256"]:
            raise ValueError("comparison source changed; obtain a fresh comparison")
        guards.append((path, record["sha256"]))
    votes, reports, validations, candidate_first = [], set(), set(), 0
    for row in rows:
        if not row.get("catalog") or not row.get("catalog_sha256"):
            raise ValueError("automatic tally requires a paragraph-bound comparison bundle; preserve legacy votes separately")
        mapping = row["mapping"]
        if not isinstance(mapping, dict) or set(mapping) != {"A", "B"} or set(mapping.values()) != {"accepted", "candidate"}:
            raise ValueError("invalid private version mapping")
        candidate_first += mapping["A"] == "candidate"
        catalog_path = _resolve(manifest_path.parent, row["catalog"])
        if catalog_path.parent != manifest_path.parent:
            raise ValueError("comparison catalog must be in its frozen bundle")
        catalog = _read(catalog_path)
        if catalog_digest(catalog) != row["catalog_sha256"]:
            raise ValueError("comparison catalog digest changed")
        for source in catalog["sources"][:2]:
            if source["sha256"] != manifest[mapping[source["label"]]]["sha256"]:
                raise ValueError("private mapping disagrees with anonymous source evidence")
        for field, hash_field in (("packet", "packet_sha256"), ("response_schema", "response_schema_sha256")):
            frozen = _resolve(manifest_path.parent, row[field])
            if frozen.parent != manifest_path.parent or _hash(frozen) != row[hash_field]:
                raise ValueError("frozen comparison packet or schema changed")
            guards.append((frozen, row[hash_field]))
        assignment = index[row["persona"]]
        report_path = _resolve(index_path.parent, assignment["report"])
        validation_path = _resolve(index_path.parent, assignment["validation"])
        if report_path in reports or validation_path in validations:
            raise ValueError("one report or validation cannot count as two readers")
        reports.add(report_path)
        validations.add(validation_path)
        original = _read(validation_path)
        fresh = validate_blind_reader_report(paths, report_path, expected_reader=row["reader"], catalog_path=catalog_path)
        if not isinstance(original, dict) or original.get("valid") is not True or original.get("status") != "passed" or not fresh["valid"]:
            raise ValueError("all four original and current report validations must pass")
        for key in ("report_sha256", "expected_reader", "catalog_sha256", "resolved_evidence"):
            if original.get(key) != fresh.get(key):
                raise ValueError(f"original reader evidence changed: {key}")
        old_bindings = sorted((s["sha256"], s["bytes"]) for s in original["source_chapters"])
        new_bindings = sorted((s["sha256"], s["bytes"]) for s in fresh["source_chapters"])
        if old_bindings != new_bindings:
            raise ValueError("reader's original source scope differs from the comparison")
        report = _read(report_path, fenced=True)
        raw_vote = report["compare"]
        preference = "same" if raw_vote == "same" else "revision" if mapping[raw_vote] == "candidate" else "accepted"
        votes.append({"reader": row["reader"], "prefers": preference, "turn_page": report["turn_page"],
                      "compare": raw_vote, "report": str(report_path), "report_sha256": fresh["report_sha256"],
                      "validation": str(validation_path), "validation_sha256": _hash(validation_path)})
        guards.extend([(report_path, fresh["report_sha256"]), (validation_path, _hash(validation_path)),
                       (catalog_path, _hash(catalog_path))])
    if candidate_first != 2:
        raise ValueError("comparison order must be counterbalanced two and two")
    for path, digest in guards:
        if _hash(path) != digest:
            raise ValueError("comparison evidence changed during decision")
    revision = sum(v["prefers"] == "revision" for v in votes)
    accepted = sum(v["prefers"] == "accepted" for v in votes)
    neutral = sum(v["prefers"] == "same" for v in votes)
    decisive = neutral == 0 and all(v["turn_page"] in {"yes", "no"} for v in votes)
    promote = decisive and revision >= 3
    reason = ("at_least_3_of_4_revision" if promote else
              "tie_requires_separate_per_version_defect_evidence" if revision == accepted == 2 else
              "nondecisive_panel" if not decisive else "panel_did_not_prefer_revision")
    return {"schema_version": 1, "chapter": chapter, "decision": "promote" if promote else "reject",
            "accepted_sha256": manifest["accepted"]["sha256"], "candidate_sha256": manifest["candidate"]["sha256"],
            "votes": votes, "revision_votes": revision, "accepted_votes": accepted, "neutral_votes": neutral,
            "reason": reason, "manifest_sha256": _hash(manifest_path), "index_sha256": _hash(index_path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--index", type=Path, required=True,
                        help='JSON: {"primary":{"report":"path","validation":"path"}, ...}, paths relative to index')
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = decide(args.manifest, args.index, args.chapter)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}))
        return 1
    print(json.dumps({"status": "recorded", "decision": result["decision"], "reason": result["reason"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
