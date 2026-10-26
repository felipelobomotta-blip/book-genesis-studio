import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/book-genesis/scripts'))
from editorial_context import continuity_view, method_section
from workflow_roles import plan_schema, render_plan
from workflow_state import digest

SKILL = Path(__file__).resolve().parents[1] / 'skills/book-genesis'


class EditorialContextTests(unittest.TestCase):
    def test_exact_handoff_and_all_accepted_sources_survive(self):
        sources = {'chapter-01.md': '# One\n\nAda keeps a brass key.',
                   'chapter-02.md': '# Two\n\nJo waits.\n\nAda opens the door.'}
        summaries = [{'chapter': 1, 'facts': 'An unverified inference.'}]
        before = copy.deepcopy(summaries)
        view = continuity_view(sources, through=2, provisional=summaries)
        self.assertEqual(2, len(view['source_index']))
        self.assertEqual(digest(sources['chapter-01.md'].encode()), view['source_index'][0]['sha256'])
        self.assertEqual('Ada opens the door.', view['handoff']['text'])
        self.assertIn('provisional', view['summary_status'])
        self.assertEqual(before, summaries)
        self.assertNotIn('verified_facts', view)

    def test_future_missing_and_aliased_chapters_are_rejected(self):
        for sources, through in (({'chapter-02.md': 'future'}, 1),
                                 ({'chapter-02.md': 'gap'}, 2),
                                 ({'../chapter-01.md': 'escape'}, 1)):
            with self.subTest(sources=sources), self.assertRaises(ValueError):
                continuity_view(sources, through=through, provisional=[])

    def test_empty_opening_context_does_not_invent_facts(self):
        view = continuity_view({}, through=0, provisional=[])
        self.assertEqual([], view['source_index'])
        self.assertIsNone(view['handoff'])

    def test_plan_requires_causal_scene_work_and_knowledge_boundaries(self):
        fields = plan_schema(2)['properties']['chapters']['items']['properties']
        for field in ('scene_contract', 'knowledge_boundary', 'arc_change'):
            self.assertIn(field, fields)
            self.assertEqual('string', fields[field]['type'])

    def test_role_views_are_distinct_and_do_not_expose_quality_targets(self):
        draft = method_section(SKILL, 'Drafting')
        planning = method_section(SKILL, 'Planning')
        revision = method_section(SKILL, 'Revision')
        self.assertIn('goal', planning)
        self.assertIn('knowledge', draft)
        self.assertIn('dependency', revision)
        self.assertNotIn('## Revision', draft)
        self.assertNotIn('90/100', draft + planning + revision)
        with self.assertRaises(ValueError):
            method_section(SKILL, 'Invented')
