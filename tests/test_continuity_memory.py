import json
import pytest

from runner.adapters import FakeAdapter
from runner.continuity import extract, memory_before, parse_record, evidence
from runner.filesystem import scaffold_project, update_state_value


def book(tmp_path):
    root = tmp_path / "book"
    scaffold_project(root, idea="A record mystery", language="en", adapter="fake", model_name="")
    return root


def payload(quote="The key is brass.", conflicts=None):
    return json.dumps({"facts": [{"kind": "identity", "statement": quote, "quote": quote}], "conflicts": conflicts or []})


def test_source_evidence_cache_and_changed_context(tmp_path):
    root = book(tmp_path)
    adapter = FakeAdapter([payload(), payload()])
    first = extract(root, "The key is brass.", "chapter 1", [], adapter)
    assert extract(root, "The key is brass.", "chapter 1", [], adapter) == first
    assert len(adapter.calls) == 1
    extract(root, "The key is brass. It opens the archive.", "chapter 1", [], adapter)
    assert len(adapter.calls) == 2


def test_accepted_extraction_is_reused_without_another_provider_call(tmp_path):
    from runner.continuity import verify_candidate, remember_accepted
    root = book(tmp_path)
    for path in (root / "artifacts").glob("*.md"):
        path.unlink()
    draft = "# Chapter 1\n\nThe key is brass.\n"
    adapter = FakeAdapter([payload()])
    assert verify_candidate(root, 1, draft, [], adapter) == []
    (root / "manuscript/chapters/chapter-01.md").write_text(draft, encoding="utf-8")
    assert remember_accepted(root, 1, draft, [], adapter)
    facts = memory_before(root, 2, adapter)
    assert facts[0]["quote"] == "The key is brass." and len(adapter.calls) == 1


@pytest.mark.parametrize("raw", ["broken", "[]", '{"facts": [], "conflicts": null}', payload("Invented quotation."),
    payload(conflicts=[{"previous_id": "invented", "quote": "The key is brass.", "reason": "Wrong metal"}])])
def test_unsupported_or_malformed_extraction_is_not_cached(tmp_path, raw):
    root = book(tmp_path)
    with pytest.raises(ValueError):
        extract(root, "The key is brass.", "chapter 1", [], FakeAdapter([raw, raw]))
    assert not list((root / "work/book-memory/records").glob("*.json"))


def test_removed_and_changed_chapters_cannot_leave_stale_memory(tmp_path):
    root = book(tmp_path)
    # Isolate sources from the scaffold's unfilled planning templates.
    for path in (root / "artifacts").glob("*.md"):
        path.unlink()
    chapter = root / "manuscript/chapters/chapter-01.md"
    chapter.write_text("The key is brass.", encoding="utf-8")
    adapter = FakeAdapter([payload(), payload("The key is silver.")])
    assert "brass" in memory_before(root, 2, adapter)[0]["statement"]
    chapter.write_text("The key is silver.", encoding="utf-8")
    assert "silver" in memory_before(root, 2, adapter)[0]["statement"]
    chapter.unlink()
    assert memory_before(root, 2, adapter) == []


def test_supported_conflict_requires_existing_fact_and_exact_quote():
    previous = evidence(json.loads(payload()), "The key is brass.", "chapter 1")
    conflict = {"previous_id": previous[0]["id"], "quote": "The key is silver.", "reason": "Same key has a conflicting metal."}
    assert parse_record(payload("The key is silver.", [conflict]), "The key is silver.", previous)["conflicts"] == [conflict]


def test_source_ids_copy_actual_markdown_instead_of_trusting_reconstructed_quotes():
    source = "| Name | **Nora Vale** |\n| Key | brass |"
    raw = json.dumps({"facts": [{"kind": "identity", "statement": "The name is Nora Vale", "source_id": "s1"}], "conflicts": []})
    record = parse_record(raw, source, [])
    assert record["facts"][0]["quote"] == "| Name | **Nora Vale** |"
    with pytest.raises(ValueError, match="nonexistent source"):
        parse_record(raw.replace('"s1"', '"s999"'), source, [])


def test_invalid_evidence_gets_one_informed_correction_without_losing_valid_source(tmp_path):
    root = book(tmp_path)
    adapter = FakeAdapter([payload("Invented quote."), payload()])
    record = extract(root, "The key is brass.", "chapter 1", [], adapter)
    assert record["facts"][0]["quote"] == "The key is brass."
    assert len(adapter.calls) == 2
    assert "CORRECT THE INVALID EXTRACTION" in adapter.calls[1].prompt
    assert "Invented quote." in adapter.calls[1].prompt
    assert len(list((root / "work/book-memory/rejected").glob("*.json"))) == 1


def test_blind_reader_never_receives_memory_and_failed_repair_preserves_canonical(tmp_path, monkeypatch):
    from runner.chapter import run_chapter
    root = book(tmp_path)
    update_state_value(root / "PROJECT_STATE.yaml", "genre", "nonfiction")
    (root / "artifacts/05-outline.md").write_text("## Chapter 1: The key", encoding="utf-8")
    canonical = root / "manuscript/chapters/chapter-01.md"
    canonical.write_text("# Chapter 1: The key\n\nThe key is brass.\n", encoding="utf-8")
    original = canonical.read_bytes()
    facts = [{"id": "evidence", "statement": "PRIVATE-MEMORY-SENTINEL", "source": "chapter 0"}]
    monkeypatch.setattr("runner.continuity.memory_before", lambda *a: facts)
    conflict = [{"previous_id": "evidence", "quote": "The key is silver.", "reason": "Metal changed"}]
    monkeypatch.setattr("runner.continuity.verify_candidate", lambda *a: conflict)
    yes = "```yaml\nturn_page: yes\nstopped_at: none\nremember: []\nflags: []\nvs_previous: better\n```"
    reader = FakeAdapter([yes, yes])
    result = run_chapter(root, 1, {"writer": FakeAdapter(["# Chapter 1: The key\n\nThe key is silver."]),
        "editor": FakeAdapter(["# Chapter 1: The key\n\nThe key is silver."]), "judge": reader, "continuity": FakeAdapter([])})
    assert not result.accepted
    assert canonical.read_bytes() == original
    assert all("PRIVATE-MEMORY-SENTINEL" not in call.prompt for call in reader.calls)


def test_successful_continuity_repair_is_rejudged_and_published(tmp_path, monkeypatch):
    from runner.chapter import run_chapter
    root = book(tmp_path)
    update_state_value(root / "PROJECT_STATE.yaml", "genre", "nonfiction")
    (root / "artifacts/05-outline.md").write_text("## Chapter 1: The key", encoding="utf-8")
    monkeypatch.setattr("runner.continuity.memory_before", lambda *a: [])
    checks = iter([[{"reason": "Wrong date"}], []])
    monkeypatch.setattr("runner.continuity.verify_candidate", lambda *a: next(checks))
    yes = "```yaml\nturn_page: yes\nstopped_at: none\nremember: []\nflags: []\nvs_previous: better\n```"
    reader = FakeAdapter([yes, yes])
    result = run_chapter(root, 1, {"writer": FakeAdapter(["# Chapter 1: The key\n\n2005."]),
        "editor": FakeAdapter(["# Chapter 1: The key\n\n2006."]), "judge": reader, "continuity": FakeAdapter([])})
    assert result.accepted and len(reader.calls) == 2
    assert "2006" in result.draft_path.read_text(encoding="utf-8")
