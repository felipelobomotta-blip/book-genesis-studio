import json
import pytest

from runner.acceptance import inspect, performance
from runner.continuity import arithmetic_findings, select_facts
from runner.filesystem import scaffold_project, update_state_value


def test_arithmetic_calculates_exact_decimal_sum_from_source():
    source = "Of 25 copies, 5 stayed and 21 went out."
    data = {"arithmetic": [{"quote": source, "total": "25", "parts": ["5", "21"]}]}
    assert "26" in arithmetic_findings(data, source)[0]["reason"]
    source = "The total is 0.3 from 0.1 and 0.2."
    assert arithmetic_findings({"arithmetic": [{"quote": source, "total": "0.3", "parts": ["0.1", "0.2"]}]}, source) == []


@pytest.mark.parametrize("parts", [["4", "21"], ["__import__('os')", "21"], ["5"], ["5", "NaN"], [5, 21]])
def test_arithmetic_rejects_unsupported_inputs(parts):
    source = "Of 25 copies, 5 stayed and 21 went out."
    with pytest.raises(ValueError):
        arithmetic_findings({"arithmetic": [{"quote": source, "total": "25", "parts": parts}]}, source)


def test_retrieval_is_bounded_and_preserves_relevant_old_fact():
    facts = [{"kind": "quantity", "statement": f"Unrelated detail {n}", "id": str(n)} for n in range(200)]
    facts[0]["statement"] = "Nora owns the brass archive key"
    selected = select_facts(facts, "Nora looks for the archive key", limit=10)
    assert len(selected) == 10 and facts[0] in selected
    assert len(facts) == 200


def test_release_gate_cannot_turn_a_draft_into_production_ready(tmp_path):
    project = tmp_path / "book"
    scaffold_project(project, idea="A mystery", language="en", adapter="fake", model_name="")
    (project / "artifacts/05-outline.md").write_text("## Chapter 1: Start", encoding="utf-8")
    (project / "manuscript/chapters/chapter-01.md").write_text("# Chapter 1: Start\n\nThe story.", encoding="utf-8")
    report = inspect(project, 50000)
    assert not report["mechanical_acceptance"] and not report["release_ready"]
    assert any(c["check"] == "requested_scale" and not c["passed"] for c in report["checks"])
    assert any(c["check"] == "chapter-01_accepted_source" and not c["passed"] for c in report["checks"])


def test_metrics_report_partial_records_as_a_gap(tmp_path):
    (tmp_path / "work").mkdir()
    (tmp_path / "work/metrics.jsonl").write_text('{"elapsed_seconds": 2, "outcome": "success"}\n{"partial"', encoding="utf-8")
    report = performance(tmp_path)
    assert report["calls"] == 1 and report["invalid_metric_records"] == 1
