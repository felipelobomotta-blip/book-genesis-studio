"""Execute the existing skill with read-only native roles and code-owned state.

One process owns the book. Native roles only return responses; they never edit
the workspace or operate another orchestrator. All creative prompts, phase
routing, readers, comparison, calibration and export come from this skill.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
from statistics import median
import sys

from build_comparison import build_comparison, READERS
from check_progress import _parse_yaml_subset, parse_project_state, reconcile_book
from check_correction import (prepare as prepare_correction, decision as correction_decision,
                              validate_report as validate_correction_report)
from correction_edits import apply_passage_corrections, correction_schema, source_passages
from decide_comparison import decide
from export_book import discover_chapters, export_book, word_count_receipt
from prepare_readers import prepare_readers
from prepare_rubric import build_catalog, catalog_digest
from promote_chapter import promote_chapter
from stage_chapter import stage_chapter
from validate_blind_reader import validate_blind_reader_report
from validate_rubric import validate_rubric, rubric_schema
from verify_book import verify_book
from workflow_roles import (AUDIT_PASSES, PLAN_PASSES, PROOF_PASSES, PROSE_SCHEMA, TEXT,
    INTEGER, array, artifact_schema, enum, obj, text_catalog, review_schema,
    validate_json, validate_prose, validate_prose_text, validate_review, neutral_contract_schema,
    plan_schema, validate_neutral, render_plan,
    plan_repair_schema, apply_plan_edits, validate_shape, character_context, production_facts)
from workflow_issues import reconcile_issues
from workflow_state import Journal, WorkflowError, atomic, digest, encoded, freeze, read_json


def production_allowance(chapters, remaining, used, min_words, max_words):
    """Reserve room for every remaining chapter without imposing equal lengths.

    Local bounds allow an ordinary long or short chapter. The feasibility bounds
    reserve the remaining chapters' minimum and maximum capacity, so every
    accepted chapter leaves a route to the unchanged whole-book contract.
    """
    if not 1 <= remaining <= chapters or used < 0:
        raise WorkflowError("Invalid remaining production scope")
    local_min = max(100, math.floor(min_words / chapters * .8))
    local_max = math.ceil(max_words / chapters * 1.25)
    low = max(local_min, min_words - used - (remaining - 1) * local_max)
    high = min(local_max, max_words - used - (remaining - 1) * local_min)
    if high < low:
        raise WorkflowError("No feasible chapter allowance within the frozen book length")
    target = min(high, max(low, round(((min_words + max_words) / 2 - used) / remaining)))
    return low, high, target


def score_text(value):
    return "unassessed" if value is None else f"{value:.2f}"


class BookWorkflow:
    def __init__(self, root: Path, command: dict, *, chapters: int, min_words: int, max_words: int,
                 quality_target: float = 8.5, weighted_quality_target: float | None = None, transport=None):
        self.root = root.resolve()
        self.skill = Path(__file__).resolve().parents[1]
        self.config = read_json(self.root / ".book-genesis/project.json")
        if self.config["host"] not in {"codex", "claude"} or self.config["collaboration"] != "autonomous":
            raise WorkflowError("The controlled autonomous runner supports native Codex and Claude autonomous projects")
        if not self.config.get("author_name"):
            raise WorkflowError("An explicit title-page author is required before unattended execution")
        if not 1 <= chapters <= 100 or min_words < chapters * 100 or max_words < min_words or not 0 <= quality_target <= 9.2:
            raise WorkflowError("Invalid chapter, production length or quality contract")
        if weighted_quality_target is not None and not 0 <= weighted_quality_target < 9.2:
            raise WorkflowError("Weighted target must be below the calibrated maximum 9.2")
        self.manifest = list(_parse_yaml_subset(self.ref("pipeline/manifest.yaml")).values())
        self.command = command
        self.transport = transport
        self.contract = {"chapters": chapters, "min_words": min_words, "max_words": max_words,
            "quality_target": quality_target, "model": self.config.get("model"), "effort": self.config.get("effort"),
            "project_sha256": digest((self.root / ".book-genesis/project.json").read_bytes()),
            "install_sha256": digest((self.root / ".book-genesis/skills/.book-genesis-install.json").read_bytes()),
            "runner_sha256": digest(Path(__file__).read_bytes()), "command": command}
        if weighted_quality_target is not None:
            self.contract["weighted_quality_target"] = weighted_quality_target
        self.journal = Journal(self.root, self.contract)
        self.state_path = self.root / "PROJECT_STATE.yaml"
        if not self.state_path.exists():
            self.state = _parse_yaml_subset(self.ref("pipeline/project-state.yaml"))
            self.state["project"].update(id=self.root.name, idea=self.config["idea"], language=self.config["language"],
                target_floor_words=min_words, target_ceiling_words=max_words, target_range_words=f"{min_words}-{max_words}",
                quality_target=quality_target)
            self.state["collaboration"].update(mode="autonomous", waiting_for_author=False)
            self.state["independence"].update(level="Fresh native CLI contexts", grade="B", writer_model=self.config["model"],
                reader_model=self.config["model"], isolation_check="not_needed",
                notes="Sequential official CLI sessions in empty temporary directories; same model family; simulated readers.")
            self.state["manuscript"].update(chapter_count_planned=chapters, average_words_per_chapter_planned=(min_words + max_words) // (2 * chapters))
        else:
            self.state = parse_project_state(self.state_path)
        self.sync()

    def ref(self, name):
        return (self.skill / "references" / name).read_text(encoding="utf-8")

    def log(self, text):
        print(text, flush=True)
        with (self.root / "RUN_REPORT.md").open("a", encoding="utf-8") as handle:
            handle.write(f"\n- {Journal.now()} {text}\n")

    def sync(self):
        paths = list((self.root / "manuscript/chapters").glob("*.md"))
        chapters = discover_chapters(self.root / "manuscript/chapters") if paths else []
        words = word_count_receipt(chapters)["total"]
        self.state["manuscript"].update(completed_chapters=[c.number for c in chapters], word_count_actual=words,
            length_gate="PASS" if self.contract["min_words"] <= words <= self.contract["max_words"] else "pending",
            status="complete" if len(chapters) == self.contract["chapters"] else "in_progress")
        phase = min(self.journal.data["phase"], 7)
        self.state["pipeline"].update(current_phase=self.manifest[phase]["label"], status="in_progress" if self.journal.data["status"] == "running" else self.journal.data["status"],
            panel_passes=sum(row["panel_failed"] for row in self.journal.data["passes"]),
            rubric_passes=sum(row["rubric_failed"] for row in self.journal.data["passes"]))
        for number, record in self.journal.data["phase_evidence"].items():
            self.state["gates"][self.manifest[int(number)]["gate"]] = record["outcome"]
        atomic(self.state_path, encoded(self.state))  # JSON is a strict YAML subset.
        report = reconcile_book(self.root)
        if not report["ok"]:
            raise WorkflowError("Program-owned progress does not reconcile: " + json.dumps(report["mismatches"]))

    def call(self, key, packet, schema, validator=None, *, feedback=False, feedback_response=False):
        self.journal.check_canonical()
        kwargs = {"transport": self.transport} if self.transport is not None else {}
        result = self.journal.call(key, packet if isinstance(packet, bytes) else packet.encode("utf-8"), schema,
            self.command, validator or (lambda p: validate_json(p, schema)),
            feedback=feedback, feedback_response=feedback_response, **kwargs)
        self.journal.check_canonical()
        return result

    def finish(self, phase, evidence, outcome="completed"):
        self.journal.finish_phase(phase, evidence, outcome=outcome)
        self.sync()
        self.log(f"{self.manifest[phase]['label']} | {outcome}")

    def files(self, names):
        return {name: (self.root / name).read_text(encoding="utf-8") for name in names}

    def artifact_paths(self, phase):
        return [name for name in self.manifest[phase]["outputs"] if name.endswith(".md")]

    def publish_artifacts(self, data):
        for name, text in data["files"].items():
            freeze(self.root / name, text.encode("utf-8"))

    def phase_packet(self, phase, inputs):
        row = self.manifest[phase]
        instructions = (self.skill / row["prompt"]).read_text(encoding="utf-8")
        # Only these planning specialists see their allowed planning references.
        refs = "\n\n".join((self.skill / p).read_text(encoding="utf-8") for p in row["references"])
        return ("You are a scoped book planning specialist, not a host orchestrator. Use only this packet. "
            "Do not run tools, write files, request user input or start other agents. Return the requested JSON artifacts. "
            "Do not claim research was verified on the web. Mark unverified market/comparison hypotheses honestly. "
            "Do not invent process records or review results. The program handles them.\n\n"
            + instructions + "\n\n" + refs + "\n\nAuthor contract and allowed material:\n" + json.dumps(inputs, ensure_ascii=False))

    def planning(self):
        if self.journal.data["phase"] == 0:
            schema = artifact_schema([p for p in self.artifact_paths(0) if p != "artifacts/00-brief.md"], metadata=True)
            schema["properties"]["contract"] = neutral_contract_schema()
            schema["required"].append("contract")
            packet = self.phase_packet(0, {"idea": self.config["idea"], "language": self.config["language"],
                "chapters": self.contract["chapters"], "min_words": self.contract["min_words"], "max_words": self.contract["max_words"],
                "author": self.config["author_name"], "collaboration": "autonomous; make reasonable creative assumptions and record them"})
            packet += "\nReturn the neutral story contract separately; the program renders the brief from it and the author's exact idea/length. "
            packet += "Keep the market map under 700 words and story engine under 800. No process verdicts, gate outcomes or quality scores in story fields."
            def validate_intake(path):
                report = validate_json(path, schema)
                if report["valid"]:
                    report["errors"] += validate_neutral(read_json(path)["contract"])
                    report["valid"] = not report["errors"]
                return report
            response, _ = self.call("intake", packet, schema, validate_intake, feedback=True)
            data = read_json(response)
            brief = ["# Book brief", "", "## Author's idea", self.config["idea"], "", "## Production scope",
                f"{self.contract['chapters']} chapters; {self.contract['min_words']}-{self.contract['max_words']} prose words; {self.config['language']}.", ""]
            brief += [f"## {key.replace('_', ' ').title()}\n\n{value}\n" for key, value in data["contract"].items()]
            data["files"]["artifacts/00-brief.md"] = "\n".join(brief)
            self.publish_artifacts(data)
            self.state["project"].update(data["book"])
            freeze(self.root / "work/book-metadata.json", encoded(data["book"]))
            self.finish(0, [self.root / name for name in self.artifact_paths(0)] + [self.root / "work/book-metadata.json"])
        if self.journal.data["phase"] == 1:
            schema = artifact_schema(self.artifact_paths(1))
            response, _ = self.call("foundation", self.phase_packet(1, self.files(self.artifact_paths(0)))
                + "\nKeep each artifact under 800 words; retain concrete character, voice and story facts. Do not include process claims.", schema, feedback=True)
            self.publish_artifacts(read_json(response))
            self.finish(1, [self.root / name for name in self.artifact_paths(1)])
        if self.journal.data["phase"] == 2:
            schema = plan_schema(self.contract["chapters"])
            inputs = self.files(self.artifact_paths(0) + self.artifact_paths(1))
            packet = self.phase_packet(2, inputs) + (
                f"\nPlan exactly {self.contract['chapters']} chapters numbered in order. The chapters array is the writer's compact packet: "
                "give only each chapter's relevant character/voice cards, current knowledge/custody facts and scene work. "
                "Do not expose future reveals in early packets. Ledger facts must distinguish planned from demonstrated events. "
                "The program supplies exact per-chapter word allowances. Return only the neutral structured fields: "
                "chapters, canon, writer_facts, promises and opening_strategy. The promises array maps each indispensable "
                "part of the author's idea to an on-page setup action and a concrete causal resolution, with chapter numbers. "
                "Specify who physically does what, by what available route or means, and the resulting state; 'enables rescue' "
                "or 'truth permits resolution' alone is not a rescue or resolution. Do not replace literal requested events "
                "with thematic equivalents. Include emotional consequences without letting them substitute for physical outcomes. "
                "This global promise map is for plan verification only. Put each chapter's actual on-page actions and any "
                "payoff earned in that chapter into that chapter's events and ending fields. Writers receive those local "
                "fields, never the combined resolution of a promise that spans future chapters. "
                "writer_facts is the stable baseline supplied to EVERY writer: "
                "canonical full names and ages (explicitly unstated when unknown), relationships, setting rules and an unambiguous "
                "calendar anchor mapping story days to weekdays and dated deadlines. Keep it under 600 words. "
                "Exclude future revelations, secret identities, planned rescues and character arc outcomes from that baseline; "
                "those belong only in their relevant chapter entries and the full canon. Ensure chapter POV and time windows "
                "agree with this baseline and the author contract. Keep each chapter entry below 300 words, the full canon below 1500, "
                "and the opening strategy below 600. The program renders the outline and ledger from those facts. "
                "Do not include verification claims, process verdicts, a brief-check register, repair history or references to findings. "
                "An independent verifier and the program supply the separate process record.")
            def validate_plan(path):
                report = validate_json(path, schema)
                if report["valid"] and [c["number"] for c in read_json(path)["chapters"]] != list(range(1, self.contract["chapters"] + 1)):
                    report.update(valid=False, errors=["Plan must contain every approved chapter in order"])
                if report["valid"]:
                    for promise in read_json(path)["promises"]:
                        if any(not 1 <= n <= self.contract["chapters"] for n in promise["setup_chapters"] + promise["payoff_chapters"]):
                            report["errors"].append("Story promise names a chapter outside the approved plan")
                    report["errors"] += validate_neutral(read_json(path))
                    report["valid"] = not report["errors"]
                return report
            response, _ = self.call("architecture", packet, schema, validate_plan, feedback=True)
            data = read_json(response)
            # Three bounded, substantive repairs. Each edits named plan fields;
            # no unchanged plan is rerated in search of a favorable verdict.
            for attempt in range(4):
                freeze(self.root / f"work/plan-candidates/plan-{attempt}.json", encoded(data))
                rendered = render_plan(data)
                review = self.review(f"plan-check-{attempt}", {"approved-brief": inputs["artifacts/00-brief.md"],
                    "outline": rendered["artifacts/07-outline.md"], "ledger": rendered["artifacts/09-continuity-ledger.md"]}, PLAN_PASSES,
                    "Verify the plan against the neutral approved brief. Examine every chapter and every timeline/world-rule entry. "
                    "A contradiction of an exact constraint blocks drafting. Use revise for any such contradiction. "
                    "Treat ordinary approximate durations as approximate. Do not invent exact requirements. "
                    "Return concise evidence-bound findings, not a new outline. ending_resolved means the planned resolution is causal and complete.")
                if review["data"]["verdict"] == "pass" and review["data"]["ending_resolved"]:
                    break
                if attempt == 3:
                    raise WorkflowError("Independent architecture verification still blocks drafting after three bounded plan repairs")
                repair_schema = plan_repair_schema(data)
                repair = packet + "\n\nReturn ONLY named text-field edits in the repair schema, not a replacement whole plan. "
                repair += "Give each allowed field path and its complete new after value. The program retains the exact original "
                repair += "from this frozen plan; do not repeat it. Change all necessary dependent fields, "
                repair += "including promise setup/resolution text and ledger facts. Preserve every unrelated event, detail and physical outcome; "
                repair += "do not shorten unaffected scenes. The chapter count, numbering and promise chapter assignments are fixed. "
                repair += "Replacement fields contain ONLY current story facts, never what was fixed, who reviewed it, pass/fail or process history."
                repair += "\nProposed plan:\n" + json.dumps(data, ensure_ascii=False, sort_keys=True)
                repair += "\nSupported defects:\n" + json.dumps(review["data"]["findings"], ensure_ascii=False, sort_keys=True)
                def validate_repair(path):
                    report = validate_json(path, repair_schema)
                    if report["valid"]:
                        try:
                            proposed = apply_plan_edits(data, read_json(path)["edits"])
                            report["errors"] += validate_shape(proposed, schema) + validate_neutral(proposed)
                            report["plan_base_sha256"] = digest(encoded(data))
                            report["plan_sha256"] = digest(encoded(proposed))
                        except ValueError as exc:
                            report["errors"].append(str(exc))
                        report["valid"] = not report["errors"]
                    return report
                response, _ = self.call(f"architecture-repair-{attempt + 1}", repair, repair_schema, validate_repair, feedback=True)
                proposed = apply_plan_edits(data, read_json(response)["edits"])
                from workflow_roles import plan_text_fields
                original_fields = plan_text_fields(data)
                freeze(self.root / f"work/plan-candidates/changes-{attempt + 1}.json", encoded({
                    "base_sha256": digest(encoded(data)), "result_sha256": digest(encoded(proposed)),
                    "response": self.journal.record_file(response),
                    "edits": [{"path": edit["path"], "before": original_fields[edit["path"]], "after": edit["after"]}
                              for edit in read_json(response)["edits"]]}))
                data = proposed
            data["files"] = render_plan(data)
            self.publish_artifacts(data)
            freeze(self.root / "work/approved-plan.json", encoded(data))
            freeze(self.root / "evaluations/plan-verification.json", encoded(review))
            self.finish(2, [self.root / name for name in self.artifact_paths(2)] + [self.root / "work/approved-plan.json", self.root / "evaluations/plan-verification.json"])
        self.metadata = read_json(self.root / "work/book-metadata.json")
        self.plan = read_json(self.root / "work/approved-plan.json")

    def review(self, key, sources, passes, instructions):
        catalog = text_catalog(sources)
        schema = review_schema(catalog, passes=passes)
        packet = ("Read-only independent review. Use only this packet; do not use tools or seek prior reports. "
            "Report evidence by the supplied passage IDs. Read ALL supplied sources in order. "
            "coverage lists ONLY names from the Complete sources catalog exactly once; do not list the reference guides as sources. "
            "checks lists every required check exactly once. "
            "No findings is valid only when the checks support it. A negative verdict is valid.\n\n"
            + instructions + "\n\nRequired checks: " + json.dumps(passes) + "\n\nComplete sources:\n" + json.dumps(catalog, ensure_ascii=False))
        response, validation = self.call(key, packet, schema,
            lambda p: validate_review(p, schema, catalog, passes, max_chapter=self.contract["chapters"]))
        return {"report": str(response.relative_to(self.root)), "validation": validation, "data": read_json(response)}

    def snapshot(self, key):
        folder = self.root / "work/snapshots" / key
        existing = folder / "snapshot.json"
        if existing.exists():
            record = read_json(existing)
            self.journal.verify_files(record["files"])
            return [self.root / row["path"] for row in record["files"]]
        paths = []
        for source in sorted((self.root / "manuscript/chapters").glob("chapter-*.md")):
            target = folder / source.name
            freeze(target, source.read_bytes())
            paths.append(target)
        freeze(existing, encoded({"files": [self.journal.record_file(path) for path in paths]}))
        return paths

    def draft(self):
        if self.journal.data["phase"] != 3:
            return
        count = self.contract["chapters"]
        checkpoints = {1, max(1, round(count * .25)), max(1, round(count * .5)), max(1, round(count * .8))}
        all_evidence = []
        for entry in self.plan["chapters"]:
            number = entry["number"]
            key = f"draft-{number:02d}"
            target = self.root / f"manuscript/chapters/chapter-{number:02d}.md"
            if not target.exists():
                used = self.state["manuscript"]["word_count_actual"]
                remaining = count - number + 1
                low, high, target_words = production_allowance(count, remaining, used,
                    self.contract["min_words"], self.contract["max_words"])
                previous = ""
                if number > 1:
                    previous = (self.root / f"manuscript/chapters/chapter-{number-1:02d}.md").read_text(encoding="utf-8")
                characters = character_context((self.root / "artifacts/03-characters.md").read_text(encoding="utf-8"),
                                               entry["characters"] + "\n" + entry["point_of_view"])
                packet = ("Write one complete, engrossing chapter. Use only this packet; no tools, files or other agents. "
                    "Return JSON with prose (one leading Markdown heading, then the entire chapter, no commentary) "
                    "and continuity_delta (only facts actually demonstrated here: who learned what, when, place and object custody). "
                    "Dramatize consequential choices and pressure rather than explaining the theme. Trust voice and scene. "
                    "Honor the approved character cards and stable identities. The previous chapter records actual actions; "
                    "writer-reported summaries are provisional and must not override its object custody or locations. "
                    "Continue from those actions without replaying an exchange already completed. "
                    "A character arc is direction, not permission to perform a later chapter's resolution now. "
                    "No outline, summary, placeholder or word-count claim in the prose. "
                    f"Aim for approximately {target_words} prose words; the accepted interval is {low} to {high}. "
                    "Plan the chapter's scene work for that target; finish at its earned ending without repeating the same beat to add length.\n\n"
                    + json.dumps({"brief": self.files(["artifacts/00-brief.md"]), "chapter": entry,
                        "stable_story_facts": self.plan["writer_facts"],
                        "characters": characters,
                        "voice": (self.root / "artifacts/05-voice.md").read_text(encoding="utf-8"),
                        "previous_chapter": previous, "demonstrated_facts": self.demonstrated(number - 1),
                        "production": {"chapter_words_min": low, "chapter_words_max": high, "chapter_words_target": target_words,
                            "book_words_min": self.contract["min_words"], "book_words_max": self.contract["max_words"],
                            "remaining_chapters_including_this": remaining}}, ensure_ascii=False))
                response, validation = self.call(key, packet, PROSE_SCHEMA,
                    lambda p: validate_prose(p, low=low, high=high), feedback=True, feedback_response=True)
                staged = self.stage_response(key, response)
                self.journal.publish(staged, target)
                self.sync()
                self.log(f"Chapter {number}/{count} saved | {validation['words']} words | manuscript {self.state['manuscript']['word_count_actual']} words")
            all_evidence += [self.root / self.journal.data["steps"][key]["validation"]]
            if number in checkpoints:
                self.panel(f"draft-check-{number:02d}", [target])
            if number % 5 == 0 or number == count:
                snap = self.snapshot(f"continuity-{number:02d}")
                record = self.review(f"continuity-{number:02d}", self.neutral_sources(snap),
                    ["Facts", "Timeline", "Knowledge", "Object custody"], self.ref("specialists/continuity.md")
                    + "\nOnly check the supplied completed chapters; future planned chapters are not missing draft content. "
                    "Preserve open findings for the full audit. Do not claim projected events occurred.")
                path = self.root / f"evaluations/continuity-{number:02d}.json"
                freeze(path, encoded(record))
                all_evidence.append(path)
        if self.state["manuscript"]["length_gate"] != "PASS":
            raise WorkflowError("The complete draft is outside its frozen length contract")
        snapshot = self.snapshot("original-draft")
        all_evidence += [self.root / "work/snapshots/original-draft/snapshot.json"]
        self.finish(3, all_evidence)

    def demonstrated(self, through):
        rows = []
        for number in range(1, through + 1):
            step = self.journal.data["steps"].get(f"draft-{number:02d}")
            if step and step["status"] == "completed":
                rows.append({"chapter": number, "facts": read_json(self.root / step["response"])["continuity_delta"]})
        return rows

    def stage_response(self, key, response, *, corrected_prose=None):
        folder = self.root / "work/attempts" / key
        source = folder / "extracted.md"
        prose = corrected_prose if corrected_prose is not None else read_json(response)["prose"]
        freeze(source, prose.encode("utf-8"))
        stage = folder / "stage"
        if not (stage / "receipt.json").exists():
            stage_chapter(source, stage)
        receipt = read_json(stage / "receipt.json")
        if receipt["source_sha256"] != digest(source.read_bytes()) or receipt["staged_sha256"] != digest((stage / "chapter.md").read_bytes()):
            raise WorkflowError("Staged chapter changed")
        freeze(folder / "extraction.json", encoded({"response": self.journal.record_file(response), "extracted": self.journal.record_file(source),
            "stage": self.journal.record_file(stage / "chapter.md"),
            "extraction": "verified_literal_replacements" if corrected_prose is not None else "json_prose_field"}))
        return stage / "chapter.md"

    def neutral_sources(self, chapters):
        names = ["artifacts/00-brief.md", "artifacts/02-story-engine.md", "artifacts/03-characters.md", "artifacts/04-theme.md",
                 "artifacts/05-voice.md", "artifacts/07-outline.md", "artifacts/08-opening-strategy.md", "artifacts/09-continuity-ledger.md"]
        return {**self.files(names),
                "controller/production-counts.json": json.dumps(production_facts(chapters, self.contract), ensure_ascii=False, indent=2),
                **{path.name: path.read_text(encoding="utf-8") for path in chapters}}

    def panel(self, key, paths):
        bundle = self.root / "work/panels" / key
        first = min(paths, key=lambda path: int(re.fullmatch(r"chapter-(\d+)\.md", path.name)[1]))
        first_number = int(re.fullmatch(r"chapter-(\d+)\.md", first.name)[1])
        context = None
        if first_number > 1:
            previous = first.parent / f"chapter-{first_number - 1:02d}.md"
            if not previous.is_file():
                raise WorkflowError("Blind reader is missing the preceding chapter context")
            # Keep the original context immutable even after a later accepted
            # revision changes the canonical preceding chapter. The packet
            # builder exposes only its final 300 visible words, not the plan.
            context = self.root / "work/panel-context" / key / previous.name
            freeze(context, previous.read_bytes())
        if not (bundle / "manifest.private.json").exists():
            prepare_readers(paths, bundle, audience=self.metadata["genre"] + "; " + self.metadata["audience"], context_chapter=context)
        manifest = read_json(bundle / "manifest.private.json")
        if [(p.resolve().as_posix(), digest(p.read_bytes())) for p in paths] != [(Path(r['path']).as_posix(), r['sha256']) for r in manifest['chapters']]:
            raise WorkflowError("Panel sources changed; existing reads cannot be reused")
        expected_context = (str(context.resolve()), digest(context.read_bytes())) if context else None
        recorded_context = (manifest["context"]["path"], manifest["context"]["sha256"]) if manifest.get("context") else None
        if recorded_context != expected_context:
            raise WorkflowError("Reader context changed; existing reads cannot be rebound")
        reports, index, evidence, reused = [], [], [self.journal.record_file(bundle / "manifest.private.json")], 0
        if context:
            evidence.append(self.journal.record_file(context))
        for row in manifest["readers"]:
            step_key = key + "-" + row["persona"]
            packet = (bundle / row["packet"]).read_bytes()
            schema = read_json(bundle / row["response_schema"])
            validator = lambda p, row=row: validate_blind_reader_report(paths, p,
                expected_reader=row["reader"], catalog_path=bundle / "catalog.json")
            previous = self.journal.matching_completed_read(packet, schema, self.command)
            if previous:
                original_key, response, validation = previous
                fresh = validator(response)
                if not fresh["valid"]:
                    raise WorkflowError("Saved reader evidence no longer validates against the current sources")
                reused += original_key != step_key
                step_key = original_key
            else:
                response, validation = self.call(step_key, packet, schema, validator)
            reports.append(read_json(response))
            evidence += self.journal.data["steps"][step_key]["evidence"]
            index.append({"reader": row["reader"], "report": str(response.relative_to(self.root)),
                "validation": self.journal.data["steps"][step_key]["validation"],
                "catalog": str((bundle / "catalog.json").relative_to(self.root))})
        stops = Counter(r["stopped_at"]["passage_id"] for r in reports if r["stopped_at"])
        flags = Counter(flag["flag"] for r in reports for flag in {f["flag"]: f for f in r["flags"]}.values())
        result = {"scope": key, "chapters": [p.name for p in paths], "readers": index,
            "yes": sum(r["turn_page"] == "yes" for r in reports), "shared_stop": any(n >= 2 for n in stops.values()),
            "shared_flags": [f for f, n in flags.items() if n >= 2], "reports": reports,
            "evidence": evidence, "reused_readings": reused}
        result["passed"] = result["yes"] >= 3 and not result["shared_stop"]
        freeze(self.root / f"evaluations/{key}.json", encoded(result))
        if key == "draft-check-01":
            freeze(self.root / "evaluations/panel-chapter-01.md", ("# Opening checkpoint\n\n" + json.dumps(result, ensure_ascii=False, indent=2)).encode("utf-8"))
        self.log(f"Readers | {key} | {result['yes']}/4 would keep reading | shared stop: {result['shared_stop']} | {reused}/4 original reads reused")
        return result

    def audit(self, key, snapshot):
        standards = "\n\n".join(self.ref(name) for name in ("roles/auditor.md", "patterns/prose.md",
            "patterns/structure-and-emotion.md", "patterns/ai-tells-en.md", "specialists/continuity.md"))
        return self.review(key, self.neutral_sources(snapshot), AUDIT_PASSES, standards
            + "\nUse passage IDs in place of copied quotations; the host resolves them without changing your report. "
            "Judge the current prose, not planned events as if they had happened. Mark ending_resolved false for an unfulfilled central promise.")

    def initial_audit(self):
        if self.journal.data["phase"] != 4:
            return
        audit = self.audit("audit-original", self.snapshot("original-draft"))
        path = self.root / "artifacts/10-adversarial-audit.md"
        freeze(path, ("# Independent manuscript audit\n\n" + json.dumps(audit, ensure_ascii=False, indent=2)
                      + "\n\naudit_status: " + audit["data"]["verdict"] + "\n").encode("utf-8"))
        self.finish(4, [path], audit["data"]["verdict"])

    def rubric(self, key, snapshot):
        folder = self.root / "work/rubric" / key
        catalog = build_catalog(snapshot)
        freeze(folder / "catalog.json", encoded(catalog))
        packet = ("You are an independent read-only literary evaluator. Use only this packet. No tools. "
            "Read the complete manuscript; do not seek previous evaluations. Return the required JSON with genuine evidence.\n\n"
            + self.ref("scoring/rubric-criteria.md") + "\n\n" + self.ref("patterns/prose.md")
            + "\n\n" + self.ref("patterns/structure-and-emotion.md") + "\n\n" + self.ref("patterns/ai-tells-en.md")
            + "\n\nMarket context (unverified positioning hypotheses):\n" + (self.root / "artifacts/01-market-map.md").read_text(encoding="utf-8")
            + "\n\nComplete frozen manuscript:\n" + json.dumps(catalog, ensure_ascii=False)
            + "\ncatalog_sha256: " + catalog_digest(catalog))
        rows = []
        for number in (1, 2):
            response, validation = self.call(f"{key}-{number}", packet, rubric_schema(catalog),
                lambda p: validate_rubric(snapshot, p, expected_chapters=self.contract["chapters"], catalog_path=folder / "catalog.json"))
            rows.append({"report": str(response.relative_to(self.root)), "validation": validation, "data": read_json(response)})
        dimensions = []
        weights = {}
        # Read the weights from the canonical rubric; no second rubric definition.
        for match in re.finditer(r"^\|\s*\d+\s*\|\s*(\w+)\s*\|\s*([\d.]+)\s*\|", self.ref("scoring/rubric-criteria.md"), re.M):
            weights[match[1]] = float(match[2])
        if len(weights) != 10:
            raise WorkflowError("Canonical rubric weights are missing or ambiguous")
        for name, weight in weights.items():
            scores = [next(d["score"] for d in row["data"]["dimensions"] if d["name"] == name) for row in rows]
            if any(score is None for score in scores):
                dimensions.append({"name": name, "raw_median": None, "calibrated": None,
                                   "weight": weight, "disagreement": True})
                continue
            raw = median(scores)
            dimensions.append({"name": name, "raw_median": raw, "calibrated": round(max(0, raw - .8), 3),
                               "weight": weight, "disagreement": max(scores) - min(scores) >= 1.5})
        complete = all(d["calibrated"] is not None for d in dimensions)
        floor = min(d["calibrated"] for d in dimensions) if complete else None
        weighted = round(sum(d["calibrated"] * d["weight"] for d in dimensions) / sum(weights.values()), 3) if complete else None
        weighted_target = self.contract.get("weighted_quality_target")
        return {"readings": rows, "dimensions": dimensions, "floor": floor,
            "weighted": weighted,
            "confidence": "low" if any(d["disagreement"] for d in dimensions) else "medium",
            "passed": complete and floor >= self.contract["quality_target"] and (weighted_target is None or weighted > weighted_target),
            "unassessed": [d["name"] for d in dimensions if d["calibrated"] is None], "calibration": -0.8}

    def measure(self, number):
        key = f"measure-{number}"
        result_path = self.root / f"evaluations/{key}.json"
        if result_path.exists():
            result = read_json(result_path)
            self.journal.verify_files(result["evidence"])
            return result
        snapshot = self.snapshot(key)
        sample = {1, max(1, round(self.contract["chapters"] / 2)), max(1, self.contract["chapters"] - 1), self.contract["chapters"]}
        sample.update(self.journal.data.get("revision_chapters", []))
        panels = [self.panel(f"{key}-c{n:02d}", [snapshot[n - 1]]) for n in sorted(sample)]
        audit = self.audit(f"{key}-audit", snapshot)
        rubric = self.rubric(f"{key}-rubric", snapshot)
        proof = self.review(f"{key}-proof", {p.name: p.read_text(encoding="utf-8") for p in snapshot}, PROOF_PASSES,
            self.ref("specialists/production.md").split("## Part 2")[0] + "\nTechnical proofreading only, no stylistic rewrite. "
            "List actionable corrections with source evidence; do not invent defects to fill the form.")
        issues = reconcile_issues(self, number, snapshot)
        panel_passed = (all(panel["passed"] for panel in panels)
            and not any(f["severity"] == "high" for f in audit["data"]["findings"]) and issues["passed"])
        result = {"number": number, "sources": {p.name: digest(p.read_bytes()) for p in snapshot}, "panels": panels,
            "audit": audit, "rubric": rubric, "proofread": proof, "issue_ledger": issues, "panel_passed": panel_passed,
            "passed": panel_passed and rubric["passed"] and audit["data"]["verdict"] == "pass"
                      and audit["data"]["ending_resolved"] and not proof["data"]["findings"]}
        prefix = key + "-"
        result["evidence"] = [row for name, step in self.journal.data["steps"].items() if name.startswith(prefix)
                              for row in step.get("evidence", [])]
        result["evidence"].append(self.journal.record_file(self.root / f"work/snapshots/{key}/snapshot.json"))
        result["evidence"] += [row for panel in panels for row in panel["evidence"]]
        result["evidence"] += issues["evidence"] + ([issues["ledger"]] if "ledger" in issues else [])
        freeze(result_path, encoded(result))
        self.log(f"Review {number} | panel {'passed' if panel_passed else 'needs work'} | audit {audit['data']['verdict']} | calibrated craft floor {score_text(rubric['floor'])}/10")
        return result

    def revision_plan(self, number, measurement):
        open_issues = measurement["issue_ledger"]["open"]
        issue_ids = [issue["id"] for issue in open_issues]
        schema = obj({"strategy": TEXT, "deferred": array(TEXT), "tasks": array(obj({"chapter": INTEGER, "ticket": TEXT,
            "preserve": TEXT, "mode": enum(("factual", "creative")),
            "issue_ids": array(enum(issue_ids)) if issue_ids else {**array(TEXT), "maxItems": 0},
            "revision_class": enum(("continuity", "structural", "character", "voice", "prose", "proofread"))}))})
        # Evaluators keep their scores. Editors get observations, never numbers.
        reasons = [{"dimension": d["name"], "reason": d["reason"], "evidence": d["evidence"]}
                   for reading in measurement["rubric"]["readings"] for d in reading["data"]["dimensions"]]
        reports = [report for panel in measurement["panels"] for report in panel["reports"]]
        packet = ("Create one bounded, coherent revision plan. Use only this packet; no tools. "
            "Fix supported high-severity audit defects first, then shared reader stops, then the weakest craft risks. "
            "Address setup AND consequences; do not substitute more explanation for a missing scene. "
            "Give at most one factual task and one creative task per affected chapter. First separate strictly factual "
            "corrections supported by existing canon (names, established ages/dates, typos) from creative changes. "
            "Factual typography may remove a redundant Chapter N: prefix while retaining the exact title. "
            "Do not mix stylistic edits into a factual task. New canon choices, viewpoint, actions, event order, motivation "
            "or a missing scene require creative mode. All factual tasks run before any creative task. "
            "Each task must name the historical issue IDs it addresses. Every required unresolved issue must have a task. "
            "Join dependent fixes coherently and preserve remembered strengths. "
            "Do not change the approved premise, POV, time window, chapter count or production length. "
            "A later pass must learn from failed earlier strategies rather than repeat them. "
            "A harmless taste difference is not a mandate to rewrite. Defer low-priority suggestions explicitly.\n\n"
            + self.ref("specialists/revision-editor.md") + "\n\n" + json.dumps({
                "current_sources": self.neutral_sources(self.snapshot(f"measure-{measurement['number']}")),
                "audit_findings": measurement["audit"]["data"]["findings"],
                "proofread_findings": measurement["proofread"]["data"]["findings"],
                "unresolved_findings": open_issues,
                "reader_experience": reports, "craft_observations": reasons,
                "earlier_revision_outcomes": [row.get("outcomes", []) for row in self.journal.data["passes"][:number - 1]],
                "earlier_strategies": self.journal.data.get("strategies", [])[:number - 1]}, ensure_ascii=False, sort_keys=True))
        def validate(path):
            report = validate_json(path, schema)
            if report["valid"]:
                tasks = read_json(path)["tasks"]
                identities = [(t["chapter"], t["mode"]) for t in tasks]
                if len(identities) != len(set(identities)) or any(not 1 <= n <= self.contract["chapters"] for n, _ in identities):
                    report["errors"].append("Revision tasks require unique chapter/mode pairs within the planned chapters")
                addressed = {identifier for task in tasks for identifier in task["issue_ids"]}
                required = {issue["id"] for issue in open_issues if issue["requires_resolution"]}
                if not required.issubset(addressed):
                    report["errors"].append("Revision plan omits unresolved required issues: " + ", ".join(sorted(required - addressed)))
                report["valid"] = not report["errors"]
            return report
        response, _ = self.call(f"revision-plan-{number}", packet, schema, validate, feedback=True)
        return read_json(response)

    def revise_chapter(self, number, task, strategy):
        n = task["chapter"]
        factual = task["mode"] == "factual"
        key = f"revision-{number}-c{n:02d}" + ("-facts" if factual else "")
        decision_path = self.root / f"evaluations/decisions/{key}.json"
        outcome_path = self.root / f"evaluations/decisions/{key}-outcome.json"
        if outcome_path.exists():
            return read_json(outcome_path)
        target = self.root / f"manuscript/chapters/chapter-{n:02d}.md"
        accepted = self.root / f"work/revisions/{key}/chapter-{n:02d}.md"
        # This copy is immutable, including across a crash after promotion.
        if not accepted.exists():
            freeze(accepted, target.read_bytes())
        current_words = word_count_receipt(discover_chapters(self.root / "manuscript/chapters"))["total"]
        from export_book import Chapter, count_prose_words
        original_text = accepted.read_bytes().decode("utf-8")
        original_words = count_prose_words(Chapter(n, accepted, original_text.splitlines()[0][2:], "\n".join(original_text.splitlines()[1:]), digest(accepted.read_bytes())))
        low = max(100, self.contract["min_words"] - (current_words - original_words))
        high = self.contract["max_words"] - (current_words - original_words)
        context = []
        for adjacent in (n - 1, n + 1):
            if 1 <= adjacent <= self.contract["chapters"]:
                source = self.root / f"manuscript/chapters/chapter-{adjacent:02d}.md"
                saved = accepted.parent / f"context-{adjacent:02d}.md"
                if not saved.exists():
                    freeze(saved, source.read_bytes())
                context.append(saved)
        packet_path = self.root / f"work/workflow/{key}/packet.md"
        if packet_path.exists():
            packet = packet_path.read_bytes()
            # The original allowance was frozen before dispatch; reuse it on resume.
            allowance = read_json(accepted.parent / "allowance.json")
            low, high = allowance["low"], allowance["high"]
        else:
            freeze(accepted.parent / "allowance.json", encoded({"low": low, "high": high}))
            output_instruction = ("The accepted chapter is supplied as original passages with stable IDs. Return only corrections "
                "naming from_passage and through_passage (inclusive) and the complete new after text for that range. "
                "Use the same ID for both ends when changing one passage. Do not transcribe a before value or put IDs in after. "
                "Ranges cannot overlap. The program retains all original text and whitespace outside the named ranges. "
                "Correct only demonstrable facts or typos supported by existing canon, not style, actions, motivation "
                "or event order. A redundant Chapter N: prefix may be removed, preserving the actual title exactly. "
                "A fresh correctness checker will inspect every difference. "
                if factual else "Return the full chapter, including unchanged passages, in prose, with its existing heading, "
                "and an accurate continuity_delta. Preserve strengths, voice and asymmetry. ")
            packet = ("Address ONLY the named tickets and their required consequences. Use only this packet; no tools. "
                + output_instruction +
                "Do not add new canon to erase a factual problem; honor the supplied existing contract. "
                "The revision must remain a real scene, not explanatory compliance.\n\n" + self.ref("specialists/revision-editor.md")
                + "\n\n" + json.dumps({"task": task, "shared_revision_strategy": strategy,
                    "accepted_chapter": [{"id": p["id"], "text": p["text"]} for p in source_passages(original_text)] if factual else original_text,
                    "adjacent_context": [p.read_text(encoding="utf-8") for p in context],
                    "brief": (self.root / "artifacts/00-brief.md").read_text(encoding="utf-8"),
                    "characters": (self.root / "artifacts/03-characters.md").read_text(encoding="utf-8"),
                    "existing_canon": (self.root / "artifacts/09-continuity-ledger.md").read_text(encoding="utf-8"),
                    "voice": (self.root / "artifacts/05-voice.md").read_text(encoding="utf-8"),
                    "production_words": {"min": low, "max": high}}, ensure_ascii=False))
        schema = correction_schema(original_text) if factual else PROSE_SCHEMA
        def validate_factual(path):
            report = validate_json(path, schema)
            if report["valid"]:
                try:
                    proposed = apply_passage_corrections(original_text, read_json(path)["corrections"])
                    report = validate_prose_text(proposed, path, low=low, high=high, report=report)
                except ValueError as exc:
                    report.update(valid=False, errors=[str(exc)])
            return report
        validator = validate_factual if factual else (lambda p: validate_prose(p, low=low, high=high))
        try:
            response, _ = self.call(key, packet, schema, validator, feedback=True, feedback_response=True)
        except WorkflowError:
            # A malformed optional revision cannot destroy the accepted book or
            # stop delivery. Auth, transport, tampering and unverified work still
            # block. A failed draft has no accepted chapter and never uses this.
            evidence = self.rejected_validation_evidence(key)
            if evidence is None:
                raise
            step = self.journal.data["steps"][key]
            outcome = {"chapter": n, "mode": task["mode"], "decision": "reject", "reason": "Both bounded revision attempts failed output validation; accepted text retained.",
                       "validation_errors": [row["validation_errors"] for row in step["attempts"]], "evidence": evidence}
            freeze(outcome_path, encoded(outcome))
            self.log(f"Revision pass {number}, chapter {n} | rejected invalid proposals; accepted chapter retained")
            return outcome
        corrected = apply_passage_corrections(original_text, read_json(response)["corrections"]) if factual else None
        candidate = self.stage_response(key, response, corrected_prose=corrected)
        if candidate.read_bytes() == accepted.read_bytes():
            decision = {"decision": "reject", "reason": "Proposal is identical to the accepted chapter; no new preference panel is needed."}
            freeze(decision_path, encoded(decision))
            outcome = {"chapter": n, "mode": task["mode"], **decision,
                "candidate": self.journal.record_file(candidate), "evidence": self.journal.record_file(decision_path)}
            freeze(outcome_path, encoded(outcome))
            self.log(f"Revision pass {number}, chapter {n} | unchanged proposal; accepted text retained")
            return outcome
        if factual:
            decision = self.check_factual_revision(key, task, accepted, candidate, context, decision_path)
        else:
            decision = self.compare_revision(key, n, accepted, candidate, context, decision_path)
        if decision["decision"] == "promote":
            receipt = self.root / f"evaluations/promotions/{key}.json"
            self.journal.publish(candidate, target, receipt=receipt, promote=lambda: promote_chapter(target, candidate, decision_path, receipt))
            self.journal.data.setdefault("revision_chapters", [])
            if n not in self.journal.data["revision_chapters"]:
                self.journal.data["revision_chapters"].append(n)
            self.journal.save()
            self.sync()
        outcome = {"chapter": n, "mode": task["mode"], "decision": decision["decision"],
                   "reason": decision.get("reason", "Fresh evidence-bound factual verification"),
                   "candidate": self.journal.record_file(candidate), "evidence": self.journal.record_file(decision_path)}
        freeze(outcome_path, encoded(outcome))
        detail = "factual correctness check" if factual else f"{decision['revision_votes']}/4 preferred the candidate"
        self.log(f"Revision pass {number}, chapter {n} | {decision['decision']} | {detail}")
        return outcome

    def rejected_validation_evidence(self, key):
        """Retain verified malformed optional work; never mask transport failure."""
        step = self.journal.data["steps"].get(key, {})
        attempts = step.get("attempts", [])
        if step.get("status") != "failed" or not attempts or not all(row.get("validation_errors") for row in attempts):
            return None
        evidence = []
        for attempt in attempts:
            folder = self.root / "work/host-calls" / attempt["call_id"]
            receipt = read_json(folder / "receipt.json")
            for name in ("packet", "response", "stdout", "stderr"):
                if digest((folder / name).read_bytes()) != receipt[name + "_sha256"]:
                    raise WorkflowError("Rejected revision evidence changed")
                evidence.append(self.journal.record_file(folder / name))
            evidence.append(self.journal.record_file(folder / "receipt.json"))
        step["rejected_evidence"] = evidence
        self.journal.save()
        return evidence

    def check_factual_revision(self, key, task, accepted, candidate, context, decision_path):
        bundle = self.root / f"work/corrections/{key}"
        manifest = bundle / "manifest.private.json"
        if not manifest.exists():
            prepare_correction(accepted, candidate,
                [self.root / f"artifacts/{name}" for name in ("00-brief.md", "03-characters.md", "07-outline.md", "09-continuity-ledger.md")],
                context, task["ticket"], bundle, publication_target=self.root / f"manuscript/chapters/chapter-{task['chapter']:02d}.md")
        schema = read_json(bundle / "review.schema.json")
        try:
            response, _ = self.call(key + "-check", (bundle / "review.packet.md").read_bytes(), schema,
                                   lambda p: validate_correction_report(p, schema))
        except WorkflowError:
            evidence = self.rejected_validation_evidence(key + "-check")
            if evidence is None:
                raise
            decision = {"decision": "reject", "reason": "Factual checker exhausted bounded output-validation attempts; accepted text retained.",
                        "evidence": evidence, "manifest": self.journal.record_file(manifest)}
            freeze(decision_path, encoded(decision))
            return decision
        report = read_json(response)
        if report["verdict"] == "pass" and all(report[k] for k in ("canon_supported", "factual_only", "dependencies_safe")) and not report["findings"]:
            # This verifies the original native receipt, complete sources and all
            # cited evidence again. A model's pass alone never publishes prose.
            if decision_path.exists():
                from check_correction import verify
                verify(manifest, response.parent)
                return read_json(decision_path)
            return correction_decision(manifest, response.parent, decision_path)
        decision = {"decision": "reject", "reason": "Factual checker blocked: " + "; ".join(report["findings"]),
                    "report": self.journal.record_file(response), "manifest": self.journal.record_file(manifest)}
        freeze(decision_path, encoded(decision))
        return decision

    def compare_revision(self, key, n, accepted, candidate, context, decision_path):
        bundle = self.root / f"work/comparisons/{key}"
        if not (bundle / "manifest.private.json").exists():
            build_comparison(accepted, candidate, bundle, context)
        manifest = read_json(bundle / "manifest.private.json")
        index = {}
        paths = [accepted, candidate, *context]
        for row in manifest["readers"]:
            call_key = key + "-" + row["persona"]
            report, _ = self.call(call_key, (bundle / row["packet"]).read_bytes(), read_json(bundle / row["response_schema"]),
                lambda p, row=row: validate_blind_reader_report(paths, p, expected_reader=row["reader"], catalog_path=bundle / row["catalog"]))
            index[row["persona"]] = {"report": str(report), "validation": str(self.root / self.journal.data["steps"][call_key]["validation"])}
        freeze(bundle / "index.json", encoded(index))
        decision = decide(bundle / "manifest.private.json", bundle / "index.json", n)
        freeze(decision_path, encoded(decision))
        return decision

    def revision(self):
        if self.journal.data["phase"] != 5:
            return
        measurement = self.measure(0)
        for number in range(1, 4):
            if measurement["passed"]:
                break
            row = self.journal.reserve_pass(number, panel_failed=not measurement["panel_passed"], rubric_failed=not measurement["rubric"]["passed"])
            self.sync()
            if row["status"] == "completed":
                self.journal.verify_files([row["measurement"]])
                measurement = read_json(self.root / row["measurement"]["path"])
                self.journal.verify_files(measurement["evidence"])
                continue
            plan = self.revision_plan(number, measurement)
            plans = self.journal.data.setdefault("strategies", [])
            if len(plans) < number:
                plans.append(plan)
                self.journal.save()
            outcomes = [self.revise_chapter(number, task, plan["strategy"]) for task in sorted(plan["tasks"], key=lambda t: (t["mode"] != "factual", t["chapter"]))]
            row.update(status="revisions_saved", outcomes=outcomes)
            self.journal.save()
            current = {p.name: digest(p.read_bytes()) for p in (self.root / "manuscript/chapters").glob("*.md")}
            if current != measurement["sources"]:
                measurement = self.measure(number)
            else:
                self.log(f"Revision pass {number} | manuscript unchanged; retaining current reviews and scores without rerating")
            row.update(status="completed", measurement=self.journal.record_file(self.root / f"evaluations/measure-{measurement['number']}.json"))
            self.journal.save()
        result_path = self.root / "evaluations/final-measurement.json"
        freeze(result_path, encoded(measurement))
        freeze(self.root / "evaluations/revision-plan.md", ("# Revision strategies\n\n" + json.dumps(self.journal.data.get("strategies", []), ensure_ascii=False, indent=2)).encode("utf-8"))
        freeze(self.root / "evaluations/revision-loop.md", ("# Bounded revision record\n\n" + json.dumps(self.journal.data["passes"], ensure_ascii=False, indent=2)
            + "\n\n" + ("PASSED" if measurement["passed"] else "STOPPED: the bounded quality gates remain unmet; deliver the complete draft honestly.")).encode("utf-8"))
        freeze(self.root / "evaluations/proofread.md", ("# Current manuscript technical proofreading\n\n" + json.dumps(measurement["proofread"], ensure_ascii=False, indent=2)).encode("utf-8"))
        index = {"schema_version": 1, "scopes": [{k: p[k] for k in ("scope", "chapters", "readers")} for p in measurement["panels"]]}
        freeze(self.root / "evaluations/final-reader-index.json", encoded(index))
        self.finish(5, [result_path, self.root / "evaluations/revision-loop.md", self.root / "evaluations/revision-plan.md",
                       self.root / "evaluations/proofread.md", self.root / "evaluations/final-reader-index.json"],
                    "passed" if measurement["passed"] else "gates_not_met")

    def final_score(self):
        if self.journal.data["phase"] != 6:
            return
        result = read_json(self.root / "evaluations/final-measurement.json")
        canonical = {p.name: digest(p.read_bytes()) for p in (self.root / "manuscript/chapters").glob("*.md")}
        if canonical != result["sources"]:
            raise WorkflowError("Final measurement is stale; scoring is blocked")
        self.journal.verify_files(result["evidence"])
        check = verify_book(self.root, "evaluations/final-reader-index.json")
        if check["reviews"]["status"] != "current":
            raise WorkflowError("Final reader evidence is invalid: " + json.dumps(check["reviews"]))
        lines = [f"# {self.metadata['title']}: Genesis report", "", "A complete draft, assessed by simulated readers in fresh contexts.",
            f"{self.contract['chapters']} chapters; {self.state['manuscript']['word_count_actual']} prose words; approved range {self.contract['min_words']}-{self.contract['max_words']}.",
            "", "Gates met." if result["passed"] else "Gates not met. Completion and export do not imply literary approval.", "",
            "| Dimension | Raw median | Calibrated |", "|---|---:|---:|"]
        for d in result["rubric"]["dimensions"]:
            lines.append(f"| {d['name']} | {score_text(d['raw_median'])} | {score_text(d['calibrated'])} |")
        lines += ["", f"Calibrated floor: {score_text(result['rubric']['floor'])}/10. Weighted score: {score_text(result['rubric']['weighted'])}/10. Target: {self.contract['quality_target']:.2f}/10.",
            f"Audit: {result['audit']['data']['verdict']}. Central ending resolved: {result['audit']['data']['ending_resolved']}.",
            f"Panel: {'passed' if result['panel_passed'] else 'not met'}. Proofread findings remaining: {len(result['proofread']['data']['findings'])}.",
            f"Independence B: fresh native {self.config['model']} contexts, effort {self.config['effort']}, one model family. Confidence: {result['rubric']['confidence']}.",
            "No outside human validation, market test or publication approval. No prediction of sales.", "",
            "## Remaining findings", json.dumps(result["audit"]["data"]["findings"] + result["proofread"]["data"]["findings"], ensure_ascii=False, indent=2),
            "## Unresolved historical findings", json.dumps(result["issue_ledger"]["open"], ensure_ascii=False, indent=2)]
        path = self.root / "artifacts/11-genesis-score.md"
        freeze(path, ("\n".join(lines) + "\n").encode("utf-8"))
        self.finish(6, [path], "passed" if result["passed"] else "gates_not_met")

    def package(self):
        if self.journal.data["phase"] != 7:
            return
        schema = obj({"editorial_package": TEXT, "positioning": TEXT,
            "options": array(obj({"id": INTEGER, "title": TEXT, "logline": TEXT, "blurb": TEXT}))})
        snapshot = self.snapshot("delivery")
        packet = ("Prepare the book's editorial package. Use only this packet, no tools. Return JSON. "
            "editorial_package includes logline, blurb, full ending-inclusive synopsis, query letter, cover brief and format notes. "
            "Give exactly three distinct marketing-angle options. Do not change the manuscript or invent author credentials, reviews, awards or verified research. "
            "positioning must distinguish hypotheses from measured results; the host will run a simulated hook test.\n\n"
            + json.dumps({"book": self.metadata, "author": self.config["author_name"],
                         "manuscript": {p.name: p.read_text(encoding="utf-8") for p in snapshot},
                         "market_hypotheses": (self.root / "artifacts/01-market-map.md").read_text(encoding="utf-8")}, ensure_ascii=False))
        def validate(path):
            report = validate_json(path, schema)
            if report["valid"] and sorted(row["id"] for row in read_json(path)["options"]) != [1, 2, 3]:
                report.update(valid=False, errors=["Provide three package options numbered 1, 2, 3"])
            return report
        response, _ = self.call("editorial-package", packet, schema, validate)
        package = read_json(response)
        hooks = []
        hook_schema = obj({"reader": TEXT, "options": array(obj({"id": INTEGER, "click": {"type": "boolean"},
            "buy": {"type": "boolean"}, "keep_reading": {"type": "boolean"}, "reason": TEXT}))})
        first = " ".join(snapshot[0].read_text(encoding="utf-8").split()[2:252])
        for persona, (reader, lens) in READERS.items():
            def validate_hook(path, reader=reader):
                report = validate_json(path, hook_schema)
                if report["valid"]:
                    data = read_json(path)
                    if data["reader"] != reader or sorted(r["id"] for r in data["options"]) != [1, 2, 3]:
                        report.update(valid=False, errors=["Hook reader identity or option coverage differs"])
                return report
            report, _ = self.call("hook-" + persona, f"You are {reader}, {lens}. Use only this packet, no tools. "
                "For each package, would you click, buy, and keep reading? Give honest reasons. This is a simulated preference, not a sale.\n"
                + json.dumps({"packages": package["options"], "opening_250_words": first}, ensure_ascii=False), hook_schema, validate_hook)
            hooks.append(read_json(report))
        ranking = sorted(range(1, 4), key=lambda n: (sum(sum(r[k] for k in ("click", "buy", "keep_reading"))
            for h in hooks for r in h["options"] if r["id"] == n),
            sum(r[k] for r in hooks[0]["options"] if r["id"] == n for k in ("click", "buy", "keep_reading"))), reverse=True)
        freeze(self.root / "artifacts/12-editorial-package.md", package["editorial_package"].encode("utf-8"))
        freeze(self.root / "artifacts/13-positioning.md", (package["positioning"] + "\n\n## Simulated hook test\n\n"
            + json.dumps({"ranking": ranking, "options": package["options"], "readers": hooks}, ensure_ascii=False, indent=2)
            + "\n\nThe ranking is simulated. No human purchase, conversion or sales result has been measured.\n").encode("utf-8"))
        self.state["gates"]["editorial_package"] = "in_progress"
        self.sync()
        receipt = self.root / "delivery/export-receipt.json"
        if not receipt.exists():
            export_book(self.root, "delivery", title=self.metadata["title"], author=self.config["author_name"], language=self.config["language"],
                require_complete_pipeline=True, expected_chapters=self.contract["chapters"], min_words=self.contract["min_words"], max_words=self.contract["max_words"])
        verified = verify_book(self.root, "evaluations/final-reader-index.json")
        if verified["delivery"]["status"] != "delivered" or verified["reviews"]["status"] != "current":
            raise WorkflowError("Export verification failed: " + json.dumps(verified))
        freeze(self.root / "evaluations/delivery-verification.json", encoded(verified))
        self.finish(7, [self.root / "artifacts/12-editorial-package.md", self.root / "artifacts/13-positioning.md",
            receipt, self.root / "evaluations/delivery-verification.json"])
        self.journal.data.update(status="completed", finished_at=Journal.now())
        self.journal.save()
        self.state["delivery"].update(status="exported", scope="complete_pipeline", receipt="delivery/export-receipt.json")
        self.sync()
        self.log(f"Finished | {self.metadata['title']} | complete manuscript and validated EPUB saved in delivery/")

    def run(self):
        try:
            if self.journal.data["phase"] == 8:
                verified = verify_book(self.root, "evaluations/final-reader-index.json")
                if verified["delivery"]["status"] != "delivered" or verified["reviews"]["status"] != "current":
                    raise WorkflowError("Previously completed delivery is missing or stale")
                self.log("Completed book verified again; no model call needed")
                return 0
            self.journal.data["status"] = "running"
            self.journal.save()
            self.sync()
            self.log("Controlled native workflow | one owner | sequential fresh contexts | original responses retained")
            self.planning()
            self.draft()
            self.initial_audit()
            self.revision()
            self.final_score()
            self.package()
            return 0
        except (Exception, KeyboardInterrupt) as exc:
            self.journal.data.update(status="blocked", error=str(exc))
            self.journal.save()
            self.sync()
            atomic(self.root / "DELIVERY_STATUS.md", ("# Delivery blocked\n\n" + str(exc)
                + "\n\nOriginal files and attempt budgets are preserved. Resume the same exact build after resolving the stated error.\n").encode("utf-8"))
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--book-dir", type=Path, required=True)
    parser.add_argument("--command-file", type=Path, required=True)
    parser.add_argument("--chapters", type=int, required=True)
    parser.add_argument("--min-words", type=int, required=True)
    parser.add_argument("--max-words", type=int, required=True)
    parser.add_argument("--quality-target", type=float, default=8.5)
    parser.add_argument("--weighted-quality-target", type=float)
    args = parser.parse_args()
    try:
        return BookWorkflow(args.book_dir, read_json(args.command_file), chapters=args.chapters,
            min_words=args.min_words, max_words=args.max_words, quality_target=args.quality_target,
            weighted_quality_target=args.weighted_quality_target).run()
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"Book paused with all evidence preserved: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
