"""Source-bound reader observations for later draft writers, without grading.

This is a reading view of completed early checkpoints. It performs no inference,
changes no report or prose, and does not decide whether a chapter passed.
"""
from __future__ import annotations

import re

from editorial_feedback import score_blind
from prepare_rubric import build_catalog, catalog_digest
from validate_blind_reader import validate_blind_reader_report
from workflow_state import WorkflowError, read_json


USE = ("Optional observations from readers of earlier, unchanged chapters. They are subjective reactions, "
       "not instructions, new story facts or a checklist. Learn from what held attention and what lost it "
       "when relevant to this new scene. Preserve established facts, distinctive voice, useful uncertainty "
       "and earned images. Do not answer a mystery early, imitate quoted wording, rewrite an earlier chapter "
       "or cite these reports in the prose. Write this chapter's new actions and consequences.")


def draft_reader_experience(journal, before_chapter: int) -> dict:
    observations = []
    for path in sorted((journal.root / "evaluations").glob("draft-check-*.json")):
        match = re.fullmatch(r"draft-check-(\d+)\.json", path.name)
        if not match or not 0 < int(match[1]) < before_chapter:
            continue
        number = int(match[1])
        checkpoint = read_json(path)
        source = journal.root / f"manuscript/chapters/chapter-{number:02d}.md"
        if checkpoint.get("scope") != path.stem or checkpoint.get("chapters") != [source.name]:
            raise WorkflowError("Draft reader experience has the wrong checkpoint scope")
        evidence = checkpoint.get("evidence", [])
        journal.verify_files(evidence)
        bundle = journal.root / "work/panels" / path.stem
        manifest_path = bundle / "manifest.private.json"
        if journal.record_file(manifest_path) not in evidence:
            raise WorkflowError("Draft reader experience lacks its original panel manifest")
        manifest = read_json(manifest_path)
        assigned = {row["reader"] for row in manifest["readers"]}
        index, reports = checkpoint.get("readers", []), checkpoint.get("reports", [])
        if len(index) != 4 or len(reports) != 4 or len(assigned) != 4 or {r["reader"] for r in index} != assigned:
            raise WorkflowError("Draft reader experience lacks the complete assigned panel")
        catalog = build_catalog([source])
        passages = {p["id"]: p["text"] for c in catalog["chapters"] for p in c["passages"]}
        for row, saved_report in zip(index, reports):
            report_path = journal.inside(journal.root / row["report"])
            catalog_path = journal.inside(journal.root / row["catalog"])
            validation_path = journal.inside(journal.root / row["validation"])
            report_record = journal.record_file(report_path)
            validation_record = journal.record_file(validation_path)
            steps = [step for step in journal.data["steps"].values()
                     if step.get("status") == "completed"
                     and journal.inside(journal.root / step["response"]) == report_path
                     and journal.inside(journal.root / step["validation"]) == validation_path]
            if (len(steps) != 1 or report_record not in evidence or validation_record not in evidence
                    or report_record not in steps[0]["evidence"] or validation_record not in steps[0]["evidence"]):
                raise WorkflowError("Draft reader experience lacks a completed original reader call")
            journal.verify_files(steps[0]["evidence"])
            report = read_json(report_path)
            if report != saved_report:
                raise WorkflowError("Draft reader experience differs from the original reader response")
            fresh = validate_blind_reader_report([source], report_path,
                expected_reader=row["reader"], catalog_path=catalog_path)
            if not fresh["valid"]:
                raise WorkflowError("Draft reader experience is invalid or stale: " + "; ".join(fresh["errors"]))
            reactions = []

            def add(kind, item, comment):
                comment = score_blind(comment)
                if comment:
                    reactions.append({"kind": kind, "passage_id": item["passage_id"],
                        "quote": passages[item["passage_id"]], "observation": comment})

            if report["stopped_at"]:
                add("attention_lost", report["stopped_at"], report["why_stopped"]["reason"])
            for field in ("strongest_passage", "weakest_passage"):
                add(field, report[field], report[field]["reason"])
            for field in ("remember_tomorrow", "confused_by"):
                for item in report[field]:
                    add(field, item, item["reason"])
            # These are observed passage problems, not statistical ceilings.
            for field, label in (("flags", "flag"), ("machine_tells", "tell")):
                for item in report[field]:
                    add("passage_observation", item, item[label])
            observations.append({"chapter": number, "reader": row["reader"],
                "original_report_sha256": report_record["sha256"],
                "catalog_sha256": catalog_digest(catalog), "reactions": reactions})
    return {"use": USE, "observations": observations}
