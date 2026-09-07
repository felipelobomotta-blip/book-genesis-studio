from runner.brief import extract_chapter_section
from runner.book import outline_chapters
from runner.adapters import FakeAdapter
from runner.filesystem import scaffold_project, load_state_summary
from runner.phases import run_phase
from test_phases import INTAKE_RESPONSE, FOUNDATION_RESPONSE


def test_nested_markdown_heading_from_live_opus_is_readable():
    outline = '## Chapter outline\n\n### ## Chapter 1: Scope\nFIRST BODY\n\n### ## Chapter 2: Print\nSECOND BODY\n'
    assert outline_chapters(outline) == [1, 2]
    assert 'FIRST BODY' in extract_chapter_section(outline, 1)
    assert 'SECOND BODY' not in extract_chapter_section(outline, 1)


def test_outline_without_chapters_cannot_advance_to_drafting(tmp_path):
    scaffold_project(tmp_path, idea='A short guide', language='en', adapter='fake', model_name='')
    adapter = FakeAdapter([INTAKE_RESPONSE, FOUNDATION_RESPONSE,
        '=== FILE: artifacts/05-outline.md ===\n# Outline\nA paragraph without chapters.\n'])
    for _ in range(2):
        assert run_phase(tmp_path, {'architect': adapter}, {}).ok
    previous = (tmp_path/'artifacts/05-outline.md').read_bytes()
    result = run_phase(tmp_path, {'architect': adapter}, {})
    assert not result.ok
    assert (tmp_path/'artifacts/05-outline.md').read_bytes() == previous
    assert 'Architecture' in load_state_summary(tmp_path)['current_phase']
