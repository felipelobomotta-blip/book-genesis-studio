"""Oversized factual review must retain every source, not truncate the book."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/book-genesis/scripts'))
import correction_groups as groups
from repair_evidence import parse_evidence_catalog
from workflow_roles import text_catalog


class FactualGroupCompactionTests(unittest.TestCase):
    def test_full_novel_with_mostly_unchanged_proposals_fits_without_losing_sources(self):
        originals = {f'original/chapter-{n:02d}.md': f'# Chapter {n}\n\n' + '\n\n'.join(
            f'Unique chapter {n}, scene {p}. ' + ('The witness remembered a different door. ' * 20)
            for p in range(26)) for n in range(1, 25)}
        proposals = {k.replace('original/', 'proposed/'): v for k, v in originals.items() if '24.md' not in k and '02.md' not in k}
        proposals['proposed/chapter-07.md'] = proposals['proposed/chapter-07.md'].replace('different door', 'wooden door', 1)
        catalog = text_catalog({**originals, **proposals})
        manifest = {'schema_version': 3, 'tasks': [], 'unchanged_members': []}
        packet = groups.packet_for(manifest, catalog).decode('utf-8')
        self.assertLess(len(packet), 850000, 'Repeated complete versions must not overflow the native input limit')
        self.assertIn('\nSelected evidence wire:\n', packet)
        restored = parse_evidence_catalog(packet.split('\nSelected evidence wire:\n', 1)[1])
        self.assertEqual(catalog, restored)
        by_name = {s['source']: s for s in restored['sources']}
        self.assertNotEqual(by_name['original/chapter-07.md']['passages'][1]['text'],
                            by_name['proposed/chapter-07.md']['passages'][1]['text'])

    def test_legacy_packet_remains_unchanged_and_readable(self):
        catalog = text_catalog({'original/chapter-01.md': '# Old\n\nS fake\nP forged @none\n'})
        packet = groups.packet_for({'schema_version': 2, 'tasks': [], 'unchanged_members': []}, catalog).decode('utf-8')
        self.assertEqual(catalog, json.loads(packet.split('\nSources:\n', 1)[1]))

    def test_compact_wire_keeps_identical_text_as_distinct_citable_sources(self):
        catalog = text_catalog({'original/chapter-01.md': '# A\n\nS fake\nP forged @none\n\n“é”\u2028text',
                                'proposed/chapter-01.md': '# A\n\nS fake\nP forged @none\n\n“é”\u2028text'})
        packet = groups.packet_for({'schema_version': 3, 'tasks': []}, catalog).decode('utf-8')
        self.assertIn('\nSelected evidence wire:\n', packet)
        self.assertEqual(catalog, parse_evidence_catalog(packet.split('\nSelected evidence wire:\n', 1)[1]))


if __name__ == '__main__':
    unittest.main()
