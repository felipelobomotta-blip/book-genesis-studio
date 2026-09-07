import json
import pytest
from runner.activity import RequestBudget, WorkflowPaused, activity_events, complete_with_activity
from runner.adapters import FakeAdapter
from runner.filesystem import scaffold_project
from runner.history import reserve_attempt, record_draft
from runner.working_draft import export_working_draft


def test_request_budget_stops_before_over_budget_provider_call():
    adapter=FakeAdapter(['first','second'])
    budget=RequestBudget(1)
    with activity_events(lambda _:None,budget=budget):
        assert complete_with_activity(adapter,'one')=='first'
        with pytest.raises(WorkflowPaused,match='Session limit reached'):
            complete_with_activity(adapter,'two')
    assert len(adapter.calls)==1 and budget.used==1
    assert complete_with_activity(adapter,'another context')=='second'


def test_recovery_export_includes_unaccepted_prose_without_promoting_it(tmp_path):
    project=tmp_path/'book';scaffold_project(project,idea='A story',language='en',adapter='auto',model_name='auto')
    attempt,_=reserve_attempt(project,1)
    draft=project/'manuscript/drafts/unfinished.md';draft.parent.mkdir(exist_ok=True,parents=True)
    draft.write_text('# Chapter 1\n\nPreserved unfinished words.',encoding='utf-8')
    record_draft(project,1,attempt,draft)
    output=export_working_draft(project)
    assert 'UNACCEPTED' in output.read_text(encoding='utf-8')
    assert 'Preserved unfinished words' in output.read_text(encoding='utf-8')
    assert not list((project/'manuscript/chapters').glob('chapter-*.md'))
    draft.write_text('changed outside runner',encoding='utf-8')
    with pytest.raises(ValueError,match='changed'):
        export_working_draft(project)


def test_recovery_export_rejects_manifest_path_escape(tmp_path):
    project=tmp_path/'book';scaffold_project(project,idea='A story',language='en',adapter='auto',model_name='auto')
    reserve_attempt(project,1)
    manifest=project/'manuscript/chapters/history/chapter-01/manifest.json'
    data=json.loads(manifest.read_text());data['attempts'][0]['draft_path']='../outside.md'
    manifest.write_text(json.dumps(data),encoding='utf-8')
    with pytest.raises(ValueError,match='leaves the project'):
        export_working_draft(project)
