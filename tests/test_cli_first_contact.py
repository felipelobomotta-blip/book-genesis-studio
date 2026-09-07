"""The first thirty seconds, from a usability session on 2026-09-07.

An agent from a third model family, told only that a tool on this machine turns an
idea into a book and forbidden from reading the source, worked through the CLI cold.
Three findings from that session are pinned here.

`--version` was the very first thing tried and it crashed with an argparse usage
error. The help identified `new` as the entry point but never showed that the idea
is passed as `--idea "..."`, so the first real command came from the README rather
than the tool. And `--idea` and `--language` — the two flags every newcomer needs —
were the only flags on `new` with no description at all.
"""

import io
import contextlib

import pytest

from runner.app import main


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = main(argv)
    return code, out.getvalue()


@pytest.mark.parametrize("flag", ["--version", "-V"])
def test_asking_for_the_version_answers_instead_of_crashing(flag):
    code, text = run([flag])
    assert code == 0
    assert "5.1" in text


def test_the_help_shows_how_an_idea_is_actually_passed():
    """`new  give it an idea` does not tell anyone what to type."""
    _, text = run(["--help"])
    assert '--idea "' in text


def test_the_step_commands_are_not_presented_as_a_second_tool():
    """Twelve bare command names under the eight real ones doubled the apparent
    surface of the CLI and read as a separate interface."""
    _, text = run(["--help"])
    assert "One step at a time: brief, chapter" not in text


def test_the_two_flags_a_newcomer_needs_are_documented():
    """`--idea` and `--language` were the only flags on `new` with no description.

    Two modules define a `new` parser and only one of them is reachable, so this
    asserts on the help a person actually gets rather than on a parser object.
    """
    out = io.StringIO()
    with contextlib.redirect_stdout(out), pytest.raises(SystemExit):
        main(["new", "--help"])
    for line in out.getvalue().splitlines():
        if line.strip().startswith(("--idea", "--language")):
            assert len(line.split()) > 2, f"no description: {line!r}"
