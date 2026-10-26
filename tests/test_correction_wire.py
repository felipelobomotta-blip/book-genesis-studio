"""Full-book correction packets stay lossless without an enormous wire enum."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/book-genesis/scripts'))
import check_correction as correction
from catalog_wire import parse_catalog
import test_correction_gate


class CorrectionWireTests(unittest.TestCase):
    def test_new_packet_is_lossless_and_wire_schema_size_does_not_grow_with_book(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            accepted, candidate, canon = [root / n for n in ('chapter-01.md', 'candidate.md', 'canon.md')]
            accepted.write_text('# Door\n\nJonah Vale.\n', encoding='utf-8')
            candidate.write_text('# Door\n\nJonah Mercer.\n', encoding='utf-8')
            prose = '\n\n'.join(f'Paragraph {i}. The door opened.\nS spoofed header é.' for i in range(10000))
            canon.write_text(prose, encoding='utf-8')
            bundle = root / 'bundle'
            manifest = correction.prepare(accepted, candidate, [canon], [], 'Correct surname.', bundle)
            self.assertEqual(2, manifest['schema_version'])
            packet = (bundle / 'review.packet.md').read_text(encoding='utf-8')
            catalog = parse_catalog(packet.split('\nCatalog wire:\n', 1)[1])
            actual = {p['id']: {'source': s['source'], 'text': p['text']} for s in catalog['sources'] for p in s['passages']}
            self.assertEqual(correction._passages({'accepted': accepted.read_text(encoding='utf-8'), 'candidate': candidate.read_text(encoding='utf-8'), 'canon-1': prose}), actual)
            wire = json.loads((bundle / 'review.schema.json').read_text())
            self.assertLess(len(json.dumps(wire)), 3000)
            strict = correction.validation_schema(bundle / 'manifest.private.json')
            self.assertIn('canon-1-p9999', strict['properties']['evidence']['items']['properties']['passage_id']['enum'])
            report = {'verdict': 'pass', 'canon_supported': True, 'factual_only': True, 'dependencies_safe': True,
                      'findings': [], 'evidence': [{'passage_id': p, 'reason': 'Evidence.'} for p in
                          ('accepted-p0002', 'candidate-p0002', 'canon-1-p99999')]}
            response = root / 'response.json'
            response.write_text(json.dumps(report))
            self.assertFalse(correction.validate_report(response, strict)['valid'])


class CorrectionLegacyWireTests(test_correction_gate.CorrectionGateTests):
    """Run the unchanged promotion/tamper suite against a frozen v1 fixture too."""
    def setUp(self):
        super().setUp()
        manifest = correction.read_json(self.manifest)
        texts = {r['source']: Path(r['path']).read_bytes().decode('utf-8-sig') for r in manifest['sources']}
        (self.bundle / 'review.packet.md').write_bytes(correction._packet(manifest['ticket'], texts, version=1).encode())
        (self.bundle / 'review.schema.json').write_text(json.dumps(correction.response_schema(list(correction._passages(texts)))))
        manifest['schema_version'] = 1
        for name, key in [('review.packet.md', 'packet_sha256'), ('review.schema.json', 'schema_sha256')]:
            manifest[key] = correction.digest(self.bundle / name)
        self.manifest.write_text(json.dumps(manifest))
        self.write_call()


if __name__ == '__main__':
    unittest.main()
