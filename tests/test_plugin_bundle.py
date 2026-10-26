from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runner.plugin_bundle import build_bundle, verify_bundle


class PluginBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def test_clean_archive_is_portable_and_byte_identical(self):
        result = build_bundle(self.root / 'build with spaces')
        plugin = Path(result['plugin'])
        self.assertTrue(verify_bundle(plugin)['ok'])
        for name in ('book-genesis', 'beta-reader', 'editorial-package', 'literary-agent-panel'):
            self.assertEqual((ROOT / 'skills' / name / 'SKILL.md').read_bytes(),
                             (plugin / 'skills' / name / 'SKILL.md').read_bytes())
        with zipfile.ZipFile(result['archive']) as archive:
            self.assertIsNone(archive.testzip())
            names = archive.namelist()
            self.assertIn('plugin.json', names)
            self.assertIn('.claude-plugin/plugin.json', names)
            self.assertFalse(any('/__pycache__/' in x or x.startswith(('books/', '.git/', 'tests/', '.host-')) for x in names))
            extracted = self.root / 'fresh extracted plugin'
            archive.extractall(extracted)
        self.assertTrue(verify_bundle(extracted)['ok'])
        check = subprocess.run([sys.executable, str(extracted / 'skills/book-genesis/scripts/export_book.py'), '--help'],
                               cwd=self.root, capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr)
        check = subprocess.run([sys.executable, str(extracted / 'plugin_entry.py'), '--help'],
                               cwd=self.root, capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr)
        # --help does not import run_attached's platform-specific lazy modules.
        # Exercise the extracted process owner, without any model or network.
        check = subprocess.run([sys.executable, '-c',
            'import sys; sys.path.insert(0, sys.argv[1]); from launcher.native import run_attached; '
            'raise SystemExit(run_attached([sys.executable, "-c", "print(123)"]))',
            str(extracted)], cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertEqual(check.returncode, 0, check.stderr)
        self.assertIn('123', check.stdout)

    def test_malformed_allowlist_is_rejected_without_traceback(self):
        source = Path(build_bundle(self.root / 'source')['plugin'])
        index = source / 'distribution/plugin-files.json'
        for entries in ([{}], [1], [None]):
            index.write_text(json.dumps(entries))
            with self.assertRaisesRegex(ValueError, 'Invalid plugin file allowlist'):
                build_bundle(self.root / 'release', repo_root=source)

    def test_existing_destination_is_never_overwritten(self):
        target = self.root / 'build'
        target.mkdir()
        (target / 'my-book.md').write_text('keep')
        with self.assertRaises(FileExistsError):
            build_bundle(target)
        self.assertEqual((target / 'my-book.md').read_text(), 'keep')

    def test_extracted_timezone_resource_and_licenses_are_available(self):
        result = build_bundle(self.root / 'build')
        root = Path(result['plugin'])
        scripts = root / 'skills/book-genesis/scripts'
        for name in ('iana-timezones.zip', 'tzdata-LICENSE', 'tzdata-licenses-LICENSE_APACHE'):
            self.assertTrue((scripts / 'data' / name).is_file(), name)
        check = subprocess.run([sys.executable, '-c',
            'import sys; sys.path.insert(0, sys.argv[1]); from provider_wait import reset_timezone; assert reset_timezone("America/Sao_Paulo") is not None',
            str(scripts)], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr)

    def test_repeat_build_has_reproducible_archive(self):
        a = build_bundle(self.root / 'a')
        b = build_bundle(self.root / 'b')
        self.assertEqual(Path(a['archive']).read_bytes(), Path(b['archive']).read_bytes())

    def test_verification_rejects_changed_missing_and_extra_files(self):
        result = build_bundle(self.root / 'build')
        root = Path(result['plugin'])
        (root / 'skills/book-genesis/SKILL.md').write_text('modified')
        (root / 'LICENSE').unlink()
        (root / 'private.md').write_text('must not ship')
        errors = '\n'.join(verify_bundle(root)['errors'])
        self.assertIn('changed: skills/book-genesis/SKILL.md', errors)
        self.assertIn('missing: LICENSE', errors)
        self.assertIn('unexpected: private.md', errors)

    def test_verification_rejects_index_path_escape(self):
        result = build_bundle(self.root / 'build')
        root = Path(result['plugin'])
        receipt = json.loads((root / 'bundle-receipt.json').read_text())
        receipt['files']['../outside'] = hashlib.sha256(b'').hexdigest()
        (root / 'bundle-receipt.json').write_text(json.dumps(receipt))
        self.assertFalse(verify_bundle(root)['ok'])

    def test_deepseek_provider_loads_all_bundled_skills(self):
        if not shutil.which('node'):
            self.skipTest('Node is not installed')
        result = build_bundle(self.root / 'build')
        check = subprocess.run(['node', str(ROOT / 'tests/plugin_provider.mjs'), result['plugin']],
                               cwd=self.root, capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_deepseek_bundle_declares_activatable_composition(self):
        package = json.loads((ROOT / 'package.json').read_text())
        patch = package.get('dsh', {}).get('bundle', {}).get('patch')
        self.assertEqual(patch, './cordis.patch.yml')
        self.assertIn('name: dsh-plugin-book-genesis', (ROOT / patch).read_text())
        self.assertIn('cordis.patch.yml', package['files'])

    def test_unlisted_private_file_inside_a_skill_does_not_ship(self):
        source = Path(build_bundle(self.root / 'source')['plugin'])
        (source / 'skills/book-genesis/private-note.md').write_text('private')
        (source / 'agents/private-review.md').write_text('private')
        result = build_bundle(self.root / 'release', repo_root=source)
        self.assertFalse((Path(result['plugin']) / 'skills/book-genesis/private-note.md').exists())
        self.assertFalse((Path(result['plugin']) / 'agents/private-review.md').exists())

    def test_reparse_points_rejected_on_python_311(self):
        from unittest.mock import patch
        from runner.plugin_bundle import _check_path
        # Python 3.10/3.11 have no Path.is_junction; lstat is the portable Windows fallback.
        import os
        real = os.lstat
        target = self.root / 'linked'
        target.mkdir()
        class Reparse:
            st_file_attributes = 0x400
        # Explicitly simulate the pre-3.12 API surface on every CI Python.
        with patch('os.path.isjunction', None, create=True), patch('os.lstat', side_effect=lambda p, **kw: Reparse() if Path(p) == target else real(p, **kw)):
            with self.assertRaisesRegex(ValueError, 'Linked'):
                _check_path(target, self.root)


if __name__ == '__main__':
    unittest.main()
