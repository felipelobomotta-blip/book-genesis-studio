"""Large native editor packets retain full source evidence without duplication."""
from contextlib import redirect_stdout
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/book-genesis/scripts'))
from autonomous_book import BookWorkflow
from workflow_state import encoded, freeze
from test_autonomous_workflow import COMMAND, receipt_transport


def context_fixture():
    original = '# One\r\n\r\nAda has the key.\r\n\r\nShe waits beside the gate.\r\n'
    proposed = original.replace('Ada has the key.', 'Jo has the key.\r\nShe hides it in her coat.')
    return {'task': {'chapter': 2, 'ticket': 'Respect the proposed handoff.'},
        'unaccepted_companion_proposals': {'chapter-01.md': proposed},
        'other_current_chapters': {'chapter-01.md': original},
        'adjacent_context': [original], 'accepted_chapter': '# Two\n\nAda waits.\n',
        'contract': 'Unchanged distant fact: the doctor is a woman.',
        'craft_knowledge': {'rule': 'Preserve the actual voice.'}}


class RevisionContextTests(unittest.TestCase):
    def test_large_actual_revision_preserves_every_source_and_proposal_under_native_cap(self):
        self.run_large_revision(invalid_first=False)

    def test_large_format_retry_preserves_complete_context_and_original_attempt_budget(self):
        self.run_large_revision(invalid_first=True)

    def run_large_revision(self, *, invalid_first):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            freeze(root / '.book-genesis/project.json', encoded({'host': 'codex', 'collaboration': 'autonomous',
                'author_name': 'QA', 'model': 'exact-test-model', 'effort': 'high',
                'idea': 'A letter reaches its recipient.', 'language': 'English'}))
            freeze(root / '.book-genesis/skills/.book-genesis-install.json', b'{}')
            originals = {n: f'# Chapter {n}\n\nAda has the brass key.\n\n' + ''.join(
                f'Paragraph {i}: Ada carries the sealed letter past the courtyard wall and counts the lit windows.\n\n'
                for i in range({1: 4200, 2: 20, 3: 1800}[n])) for n in (1, 2, 3)}
            proposed = originals[1].replace('Ada has the brass key.', 'Jo has the brass key. She keeps it in her coat.')
            calls = []
            def generate(call_id, packet, schema, book):
                calls.append(call_id)
                self.assertLessEqual(len(packet), 1048576, 'Native editor input exceeds its real character cap')
                from revision_context import decode_context
                context, _ = json.JSONDecoder().raw_decode('{"task":' + packet.split('\n\n{"task":', 1)[1])
                decoded = decode_context(context)
                self.assertEqual(originals[2], decoded['accepted_chapter'])
                self.assertEqual(originals[1], decoded['other_current_chapters']['chapter-01.md'])
                self.assertEqual(originals[3], decoded['other_current_chapters']['chapter-03.md'])
                self.assertEqual(proposed, decoded['unaccepted_companion_proposals']['chapter-01.md'])
                self.assertEqual([originals[1], originals[3]], decoded['adjacent_context'])
                self.assertIn('references', decoded['craft_knowledge'])
                self.assertNotIn('quality_target', decoded)
                if invalid_first and len(calls) == 1:
                    return {'prose': '# Too short\n\nNo complete scene.', 'continuity_delta': 'Invalid fixture response.'}
                if invalid_first:
                    self.assertIn('Deterministic output validation rejected', packet)
                    self.assertIn('Previous rejected producer response', packet)
                return {'prose': originals[2].replace('Ada has the brass key.', 'Jo holds the brass key.'),
                        'continuity_delta': 'Jo is the proposed holder; originals have not changed.'}
            workflow = BookWorkflow(root, COMMAND, chapters=3, min_words=400, max_words=300000,
                transport=receipt_transport(generate))
            for n, text in originals.items():
                source = root / f'fixture/chapter-{n:02d}.md'
                freeze(source, text.encode())
                workflow.journal.publish(source, root / f'manuscript/chapters/chapter-{n:02d}.md')
            for name in ('00-brief.md', '03-characters.md', '05-voice.md', '09-continuity-ledger.md'):
                freeze(root / 'artifacts' / name, b'# Contract\n\nThe doctor is a woman.\n')
            task = {'chapter': 2, 'mode': 'creative', 'ticket': 'Coordinate the key handoff.',
                'preserve': 'Letter and courtyard.', 'revision_class': 'continuity', 'issue_ids': ['key']}
            with redirect_stdout(io.StringIO()):
                staged = workflow.revise_chapter(1, task, 'Make the key handoff consistent.', stage_only=True,
                    companion_tasks=[{**task, 'chapter': 1}], staged_companions={'chapter-01.md': proposed})
            self.assertIn('candidate', staged)
            expected_calls = 2 if invalid_first else 1
            self.assertEqual(expected_calls, len(calls))
            for n, text in originals.items():
                self.assertEqual(text.encode(), (root / f'manuscript/chapters/chapter-{n:02d}.md').read_bytes())
            with redirect_stdout(io.StringIO()):
                workflow.revise_chapter(1, task, 'Make the key handoff consistent.', stage_only=True,
                    companion_tasks=[{**task, 'chapter': 1}], staged_companions={'chapter-01.md': proposed})
            self.assertEqual(expected_calls, len(calls))

    def test_small_existing_context_stays_byte_identical(self):
        from revision_context import render_context, decode_context
        context = context_fixture()
        self.assertEqual(json.dumps(context, ensure_ascii=False), render_context(context))
        self.assertEqual(context, decode_context(context))

    def test_compact_view_reconstructs_unicode_line_endings_and_all_metadata(self):
        from revision_context import compact_context, decode_context
        context = context_fixture()
        context['other_current_chapters']['chapter-01.md'] += '\r\n' + 'Unique untouched line.\r\n' * 100
        context['unaccepted_companion_proposals']['chapter-01.md'] += '\r\n' + 'Unique untouched line.\r\n' * 100
        context['adjacent_context'] = [context['other_current_chapters']['chapter-01.md']]
        context['unaccepted_companion_proposals']['chapter-01.md'] += '\r\nCafé — música.\n'
        before = encoded(context)
        view = compact_context(context)
        self.assertLess(len(encoded(view)), len(before))
        self.assertEqual(before, encoded(decode_context(view)))
        self.assertEqual(before, encoded(context))
        self.assertIn('not accepted canon', view['_lossless_context']['instructions'])

    def test_replacements_insertions_deletions_and_final_newline_round_trip(self):
        from revision_context import compact_context, decode_context
        for before, after in [('a\nb\nc\n', 'a\nnew\nc\n'), ('a\nb', 'prefix\na\nb\nlast'),
                              ('a\nb\nc\n', 'a\nc\n'), ('a\r\nb\r\n', 'a\r\nb'), ('a\n', 'a\n')]:
            context = context_fixture()
            # Make the lossless representation smaller without changing the edit mechanism.
            tail = ''.join(f'Unchanged distinct line {n}.\n' for n in range(100))
            context['other_current_chapters']['chapter-01.md'] = tail + before
            context['unaccepted_companion_proposals']['chapter-01.md'] = tail + after
            context['adjacent_context'] = []
            self.assertEqual(context, decode_context(compact_context(context)))

    def test_stale_source_changed_after_text_and_invalid_line_ranges_are_rejected(self):
        from revision_context import compact_context, decode_context
        context = context_fixture()
        tail = ''.join(f'Unchanged distinct line {n}.\n' for n in range(100))
        for name in ('other_current_chapters', 'unaccepted_companion_proposals'):
            context[name]['chapter-01.md'] += tail
        context['adjacent_context'] = []
        view = compact_context(context)
        candidate = view['unaccepted_companion_proposals']['chapter-01.md']
        self.assertIsInstance(candidate, dict)
        for change in ('source', 'before', 'after', 'range', 'hash'):
            edited = copy.deepcopy(view)
            row = edited['unaccepted_companion_proposals']['chapter-01.md']
            if change == 'source':
                edited['other_current_chapters']['chapter-01.md'] += 'Changed.'
            elif change in ('before', 'after'):
                row['edits'][0][change] += 'Changed.'
            elif change == 'range':
                row['edits'][0]['lines'] = [True, 1]
            else:
                edited['_lossless_context']['original_context_sha256'] = '0' * 64
            with self.subTest(change=change), self.assertRaises(ValueError):
                decode_context(edited)

    def test_still_oversized_unique_context_is_never_truncated(self):
        from revision_context import render_context
        context = context_fixture()
        context['craft_knowledge'] = 'x' * 1050000
        before = encoded(context)
        with self.assertRaisesRegex(ValueError, 'native input|native character|too large'):
            render_context(context)
        self.assertEqual(before, encoded(context))


if __name__ == '__main__':
    unittest.main()
