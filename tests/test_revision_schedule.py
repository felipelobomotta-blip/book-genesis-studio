"""A global typography ticket must not postpone causal story repairs."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/book-genesis/scripts'))
import correction_groups as groups


class RevisionScheduleTests(unittest.TestCase):
    def test_partition_policy_preserves_the_existing_revision_order(self):
        self.assertEqual(groups.revision_schedule(self.tasks(), version=2),
                         groups.revision_schedule(self.tasks(), version=3))

    def tasks(self):
        return [
            {'chapter': 1, 'mode': 'factual', 'revision_class': 'proofread', 'issue_ids': ['quotes']},
            {'chapter': 2, 'mode': 'factual', 'revision_class': 'continuity', 'issue_ids': ['key', 'quotes']},
            {'chapter': 3, 'mode': 'factual', 'revision_class': 'continuity', 'issue_ids': ['key']},
            {'chapter': 1, 'mode': 'creative', 'revision_class': 'structural', 'issue_ids': ['clue']},
            {'chapter': 4, 'mode': 'creative', 'revision_class': 'structural', 'issue_ids': ['clue']},
            {'chapter': 4, 'mode': 'factual', 'revision_class': 'proofread', 'issue_ids': ['quotes']},
        ]

    def test_cosmetic_instances_are_independent_and_follow_story_repairs(self):
        result = groups.revision_schedule(self.tasks(), version=2)
        self.assertEqual([('factual', [2, 3]), ('creative', [1, 4]), ('factual', [1]), ('factual', [4])],
                         [(g[0]['mode'], [t['chapter'] for t in g]) for g in result])

    def test_existing_pass_keeps_original_group_order(self):
        result = groups.revision_schedule(self.tasks(), version=1)
        self.assertEqual([('factual', [1, 2, 3, 4]), ('creative', [1, 4])],
                         [(g[0]['mode'], [t['chapter'] for t in g]) for g in result])

    def test_only_pure_proofread_class_is_deferred(self):
        tasks = [{'chapter': 1, 'mode': 'factual', 'issue_ids': ['unknown']},
                 {'chapter': 2, 'mode': 'creative', 'revision_class': 'prose', 'issue_ids': ['voice']}]
        result = groups.revision_schedule(tasks, version=2)
        self.assertEqual(['factual', 'creative'], [g[0]['mode'] for g in result])


if __name__ == '__main__':
    unittest.main()
