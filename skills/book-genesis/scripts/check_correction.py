"""Freeze and check a factual correction, separately from literary preference.

The fresh reviewer decides correctness. This helper verifies its original
response, exact evidence, completed native call and unchanged input files.
It never invents votes, edits prose, closes audit tickets or calls a model.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re


class CorrectionError(ValueError):
    pass


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CorrectionError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value):
    raise CorrectionError(f"nonfinite JSON value: {value}")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=_pairs, parse_constant=_constant)


def _save(path: Path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def _record(path: Path, source: str) -> tuple[dict, str]:
    path = path.resolve()
    data = path.read_bytes()
    text = data.decode("utf-8-sig")
    if not text.strip():
        raise CorrectionError(f"empty {source} source")
    return {"source": source, "path": str(path), "sha256": sha256(data).hexdigest()}, text


def _passages(texts: dict[str, str]) -> dict:
    result = {}
    for source, text in texts.items():
        paragraphs = re.split(r"\n[ \t]*\n", text.replace("\r\n", "\n").replace("\r", "\n"))
        for index, paragraph in enumerate((p for p in paragraphs if p.strip()), 1):
            result[f"{source}-p{index:04d}"] = {"source": source, "text": paragraph}
    return result


def response_schema(passages: list[str]) -> dict:
    def obj(properties):
        return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}
    return obj({
        "verdict": {"type": "string", "enum": ["pass", "block"]},
        "canon_supported": {"type": "boolean"},
        "factual_only": {"type": "boolean"},
        "dependencies_safe": {"type": "boolean"},
        "evidence": {"type": "array", "items": obj({
            "passage_id": {"type": "string", "enum": passages},
            "reason": {"type": "string"}})},
        "findings": {"type": "array", "items": {"type": "string"}},
    })


def _packet(ticket: str, texts: dict[str, str]) -> str:
    return (
        "# Factual correction verification\n\n"
        "Use only the supplied sources. Do not read project files or previous reviews. "
        "This is a correctness check, not a preference vote. Either pass or block is valid. "
        "The accepted text can be wrong. The proposed text can also be wrong.\n\n"
        "Check every difference. Pass only if existing canon supports it, it is strictly a factual correction "
        "with no creative rewrite or unrelated change, and dependent expressions and surrounding scenes "
        "remain coherent. A new canon choice, insufficient context, an unresolved dependency, or changing "
        "an action, motivation, event order or consequence requires block and a wider editorial ticket. "
        "Do not prefer an error for its wording. Existing unrelated defects may remain; identify them without "
        "claiming this local correction closes a whole-book ticket.\n\n"
        "Return the required JSON. Cite the supplied paragraph IDs from accepted, candidate, and at least "
        "one canon source, with an explanation for each. Do not recopy or invent quotations. "
        "Include context evidence when a dependency relies on it. "
        "A pass requires all three checks true and no unresolved findings within this correction.\n\n"
        + "## Ticket\n\n" + ticket.strip() + "\n"
        + "".join(f"\n## Source {row['source']} / [{key}]\n\n{row['text']}\n"
                  for key, row in _passages(texts).items())
    )


def _check_versions(texts: dict, accepted: Path) -> int:
    chapter = re.fullmatch(r"chapter-(\d+)\.md", accepted.name)
    if not chapter or int(chapter[1]) < 1:
        raise CorrectionError("accepted source must be chapter-NN.md")
    original, proposed = texts["accepted"], texts["candidate"]
    if original == proposed:
        raise CorrectionError("candidate has no change")
    if not original.startswith("# ") or not proposed or original.splitlines()[0] != proposed.splitlines()[0]:
        raise CorrectionError("a factual correction must retain the chapter heading")
    return int(chapter[1])


def prepare(accepted: Path, candidate: Path, canon: list[Path], context: list[Path],
            ticket: str, output: Path, *, publication_target: Path | None = None) -> dict:
    if not ticket.strip() or not canon:
        raise CorrectionError("a factual ticket and at least one existing canon source are required")
    entries = [(accepted, "accepted"), (candidate, "candidate")]
    entries += [(p, f"canon-{i}") for i, p in enumerate(canon, 1)]
    entries += [(p, f"context-{i}") for i, p in enumerate(context, 1)]
    records, texts = [], {}
    for path, source in entries:
        record, text = _record(path, source)
        records.append(record)
        texts[source] = text
    if len({r["path"] for r in records}) != len(records):
        raise CorrectionError("correction sources must be distinct files")
    chapter = _check_versions(texts, accepted)
    target_record = None
    if publication_target is not None:
        publication_target = publication_target.resolve()
        if publication_target.name != accepted.name or digest(publication_target) != records[0]["sha256"]:
            raise CorrectionError("publication target must be the same chapter and match the frozen accepted bytes")
        target_record = {"path": str(publication_target), "sha256": records[0]["sha256"]}
    packet = _packet(ticket, texts)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / "review.packet.md").write_bytes(packet.encode("utf-8"))
    _save(output / "review.schema.json", response_schema(list(_passages(texts))))
    manifest = {"schema_version": 1, "kind": "factual_correction", "chapter": chapter,
                "ticket": ticket, "sources": records,
                "packet_sha256": digest(output / "review.packet.md"),
                "schema_sha256": digest(output / "review.schema.json")}
    if target_record is not None:
        manifest["publication_target"] = target_record
    for row in records:
        if digest(Path(row["path"])) != row["sha256"]:
            raise CorrectionError("source changed while preparing the correction")
    _save(output / "manifest.private.json", manifest)
    return manifest


def verify(manifest_path: Path, call_dir: Path) -> dict:
    """Recheck the original completed call; invalid or blocked is never a pass."""
    manifest_path, call_dir = manifest_path.resolve(), call_dir.resolve()
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or manifest.get("kind") != "factual_correction":
        raise CorrectionError("unsupported correction manifest")
    if not isinstance(manifest.get("sources"), list) or not manifest["sources"] or any(not isinstance(row, dict) for row in manifest["sources"]):
        raise CorrectionError("correction manifest needs source records")
    guarded = [{"path": str(manifest_path), "sha256": digest(manifest_path)}]
    texts, by_source = {}, {}
    for row in manifest["sources"]:
        source = row["source"]
        if source in texts:
            raise CorrectionError("duplicate correction source")
        path = Path(row["path"])
        if digest(path) != row["sha256"]:
            raise CorrectionError(f"correction source changed: {source}")
        texts[source] = path.read_bytes().decode("utf-8-sig")
        by_source[source] = row
        guarded.append({"path": str(path.resolve()), "sha256": row["sha256"]})
    if not {"accepted", "candidate"}.issubset(texts) or not any(k.startswith("canon-") for k in texts):
        raise CorrectionError("missing correction sources")
    if _check_versions(texts, Path(by_source["accepted"]["path"])) != manifest["chapter"]:
        raise CorrectionError("correction chapter identity changed")
    if sha256(_packet(manifest["ticket"], texts).encode("utf-8")).hexdigest() != manifest["packet_sha256"]:
        raise CorrectionError("correction packet does not match its complete sources")
    for name, key in [("review.packet.md", "packet_sha256"), ("review.schema.json", "schema_sha256")]:
        path = manifest_path.parent / name
        if digest(path) != manifest[key]:
            raise CorrectionError(f"frozen {name} changed")
        guarded.append({"path": str(path), "sha256": manifest[key]})
    receipt_path = call_dir / "receipt.json"
    receipt = read_json(receipt_path)
    if not isinstance(receipt, dict) or receipt.get("status") != "completed" or receipt.get("exit_code") != 0 or receipt.get("error") is not None:
        raise CorrectionError("correction reviewer has no successful native completion receipt")
    if receipt.get("packet_sha256") != manifest["packet_sha256"]:
        raise CorrectionError("reviewer did not receive this frozen correction packet")
    guarded.append({"path": str(receipt_path), "sha256": digest(receipt_path)})
    for name in ("packet", "response", "stdout", "stderr"):
        path = call_dir / name
        if digest(path) != receipt.get(name + "_sha256"):
            raise CorrectionError(f"original native {name} changed")
        guarded.append({"path": str(path), "sha256": receipt[name + "_sha256"]})
    if (call_dir / "response.pending").exists():
        raise CorrectionError("correction call still has a pending response")
    report = read_json(call_dir / "response")
    if not isinstance(report, dict) or set(report) != {"verdict", "canon_supported", "factual_only", "dependencies_safe", "evidence", "findings"}:
        raise CorrectionError("invalid correction report fields")
    if report["verdict"] not in {"pass", "block"} or any(type(report[key]) is not bool for key in ("canon_supported", "factual_only", "dependencies_safe")):
        raise CorrectionError("invalid correction verdict or checks")
    if not isinstance(report["findings"], list) or any(not isinstance(x, str) or not x.strip() for x in report["findings"]):
        raise CorrectionError("findings must be a list of nonempty strings")
    evidence = report["evidence"]
    if not isinstance(evidence, list):
        raise CorrectionError("correction evidence must be a list")
    cited, resolved = set(), []
    passages = _passages(texts)
    for item in evidence:
        if not isinstance(item, dict) or set(item) != {"passage_id", "reason"}:
            raise CorrectionError("invalid correction evidence entry")
        passage_id, reason = item["passage_id"], item["reason"]
        if not isinstance(passage_id, str) or passage_id not in passages:
            raise CorrectionError("correction evidence names an unknown source passage")
        if not isinstance(reason, str) or not reason.strip():
            raise CorrectionError("correction evidence needs a reason")
        passage = passages[passage_id]
        cited.add(passage["source"])
        resolved.append({"passage_id": passage_id, "source": passage["source"],
                         "quote": passage["text"], "reason": reason})
    if not {"accepted", "candidate"}.issubset(cited) or not any(s.startswith("canon-") for s in cited):
        raise CorrectionError("evidence must cover both versions and existing canon")
    passed = report["verdict"] == "pass" and all(report[k] for k in ("canon_supported", "factual_only", "dependencies_safe")) and not report["findings"]
    if not passed:
        raise CorrectionError("fresh reviewer blocked this correction: " + "; ".join(report["findings"]))
    target = manifest.get("publication_target", {"path": by_source["accepted"]["path"], "sha256": by_source["accepted"]["sha256"]})
    if (not isinstance(target, dict) or set(target) != {"path", "sha256"}
            or target["sha256"] != by_source["accepted"]["sha256"]
            or Path(target["path"]).name != Path(by_source["accepted"]["path"]).name):
        raise CorrectionError("invalid frozen publication target")
    recheck(guarded)
    return {"rule": "fresh_verified_factual_correction", "chapter": manifest["chapter"],
            "ticket": manifest["ticket"], "accepted_sha256": by_source["accepted"]["sha256"],
            "candidate_sha256": by_source["candidate"]["sha256"],
            "accepted_path": by_source["accepted"]["path"], "candidate_path": by_source["candidate"]["path"],
            "publication_target": target["path"],
            "report_sha256": receipt["response_sha256"], "resolved_evidence": resolved, "guarded_sources": guarded}


def recheck(records: list[dict], *, skip: Path | None = None):
    for row in records:
        path = Path(row["path"])
        if skip is not None and path.resolve() == skip.resolve():
            continue
        if digest(path) != row["sha256"]:
            raise CorrectionError("correction evidence changed before promotion")


def decision(manifest: Path, call_dir: Path, output: Path) -> dict:
    checked = verify(manifest, call_dir)
    result = {"schema_version": 2, "kind": "verified_correction", "decision": "promote",
              "chapter": checked["chapter"], "accepted_sha256": checked["accepted_sha256"],
              "candidate_sha256": checked["candidate_sha256"],
              "correction_manifest": str(manifest.resolve()), "correction_manifest_sha256": digest(manifest),
              "review_call_dir": str(call_dir.resolve()), "review_receipt_sha256": digest(call_dir / "receipt.json"),
              "review_report_sha256": checked["report_sha256"]}
    output.parent.mkdir(parents=True, exist_ok=True)
    _save(output, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare")
    for name in ("accepted", "candidate", "output-dir"):
        prep.add_argument("--" + name, type=Path, required=True)
    prep.add_argument("--canon", type=Path, action="append", required=True)
    prep.add_argument("--context", type=Path, action="append", default=[])
    prep.add_argument("--ticket", required=True)
    check = sub.add_parser("decide")
    check.add_argument("--manifest", type=Path, required=True)
    check.add_argument("--call-dir", type=Path, required=True)
    check.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = (prepare(args.accepted, args.candidate, args.canon, args.context, args.ticket, args.output_dir)
                  if args.action == "prepare" else decision(args.manifest, args.call_dir, args.output))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}))
        return 1
    print(json.dumps({"status": "prepared" if args.action == "prepare" else "verified", "chapter": result["chapter"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
