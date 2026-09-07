import pytest
from runner.adapters import FakeAdapter
from runner.judge import judge_chapter

PAST = "This sentence belongs only to the previous chapter."
CURRENT = "# Chapter 2\n\nThe visitor opened the gate and found her missing letter."
WRONG = f'```yaml\nturn_page: no\nstopped_at: "{PAST}"\nremember: []\nflags: [exposition]\n```'
RIGHT = '```yaml\nturn_page: yes\nstopped_at: none\nremember: [the letter]\nflags: []\n```'


def test_judge_retries_a_verdict_quoting_the_previous_chapter():
    adapter = FakeAdapter([WRONG, RIGHT])
    verdict = judge_chapter(CURRENT, PAST, "mystery", adapter)
    assert verdict.turn_page
    assert len(adapter.calls) == 2
    assert "came from context" in adapter.calls[1].prompt


def test_repeated_wrong_source_is_not_accepted_as_a_valid_reader_verdict():
    with pytest.raises(ValueError, match="verdict not accepted"):
        judge_chapter(CURRENT, PAST, "mystery", FakeAdapter([WRONG, WRONG]))


def test_quotation_repeated_in_current_chapter_is_valid():
    adapter = FakeAdapter([WRONG])
    assert not judge_chapter(CURRENT + "\n\n" + PAST, PAST, "mystery", adapter).turn_page
    assert len(adapter.calls) == 1
