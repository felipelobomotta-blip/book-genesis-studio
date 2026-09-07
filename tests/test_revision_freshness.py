from runner.adapters import FakeAdapter
from runner.chapter import run_chapter
from runner.filesystem import scaffold_project, update_state_value, load_state_summary

YES = "```yaml\nturn_page: yes\nstopped_at: none\nremember: []\nflags: []\n```"


def test_editing_a_completed_book_requires_a_new_audit(tmp_path):
    project = tmp_path / "book"
    scaffold_project(project, idea="A story", adapter="fake", model_name="fake", language="en")
    path = project / "manuscript/chapters/chapter-01.md"
    path.write_text("Chapter 1: Title\n\nThe story.\n", encoding="utf-8")
    update_state_value(project / "PROJECT_STATE.yaml", "status", "completed")
    update_state_value(project / "PROJECT_STATE.yaml", "current_phase", "Phase 6: Editorial Package")
    result = run_chapter(project, 1, {"judge": FakeAdapter([YES])}, seed_draft=path.read_text(encoding="utf-8"))
    assert result.accepted
    assert path.read_text(encoding="utf-8").startswith("# Chapter 1")
    state = load_state_summary(project)
    assert state["current_phase"] == "Phase 4: Adversarial Audit"
    assert state["status"] == "in_progress"
