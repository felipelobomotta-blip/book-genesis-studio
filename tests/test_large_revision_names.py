"""Real-size revision groups must fit the executor's stable-name contract."""
import re
import unittest
from unittest.mock import patch

import test_creative_groups as creative_fixture
from test_autonomous_workflow import COMMAND, receipt_transport
from autonomous_book import BookWorkflow
from workflow_state import freeze
import correction_groups


class LargeRevisionGroupTests(unittest.TestCase):
    def test_twenty_one_member_partial_group_reaches_every_reader_and_replays(self):
        fixture = creative_fixture.CreativeGroupTests(methodName="runTest")
        self.addCleanup(fixture.doCleanups)
        def large_workflow(case):
            return BookWorkflow(case.root, COMMAND, chapters=24, min_words=2400, max_words=12000,
                transport=receipt_transport(case.generate))
        with patch.object(creative_fixture.CreativeGroupTests, "new_workflow", large_workflow):
            fixture.setUp()
        for n in range(4, 25):
            text = fixture.originals["chapter-01.md"].replace(b"# Gate 1\n", f"# Gate {n}\n".encode())
            source = fixture.root / f"original/chapter-{n:02d}.md"
            freeze(source, text)
            fixture.workflow.journal.publish(source, fixture.root / "manuscript/chapters" / source.name)
            fixture.originals[source.name] = text
        members = (1, 2, 3, 4, 5, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24)
        fixture.tasks = [{**fixture.tasks[0], "chapter": n} for n in members]
        fixture.invalid = {20}
        result = fixture.run_group()
        self.assertEqual(20, sum(r["decision"] == "promote" for r in result))
        self.assertEqual([20], [r["chapter"] for r in result if r["decision"] == "reject"])
        self.assertEqual(27, len(fixture.calls))
        self.assertTrue(all(re.fullmatch(r"[a-z0-9-]{1,100}", key)
            for key in fixture.workflow.journal.data["steps"]))
        self.assertEqual(result, fixture.run_group())
        self.assertEqual(27, len(fixture.calls))
        self.assertEqual(fixture.originals["chapter-20.md"],
            (fixture.root / "manuscript/chapters/chapter-20.md").read_bytes())

    def test_group_names_cover_maximum_book_size_without_changing_short_legacy_names(self):
        tasks = [{"chapter": n} for n in range(1, 101)]
        for kind in ("creative", "facts"):
            key = correction_groups.group_key(kind, 3, tasks)
            for suffix in ("-check", "-preference-primary", "-preference-adjacent", "-preference-casual"):
                self.assertRegex(key + suffix, r"^[a-z0-9-]{1,100}$")
            self.assertNotEqual(key, correction_groups.group_key(kind, 3, tasks[:50] + tasks[51:]))
            self.assertEqual(f"revision-1-{kind}-group-1-3",
                correction_groups.group_key(kind, 1, [{"chapter": 1}, {"chapter": 3}]))


if __name__ == "__main__":
    unittest.main()
