"""Explicit runtime repair preserves the stopped run and frozen quality policy."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'skills/book-genesis/scripts'))
from launcher.cli import prepare_project, read_project
from autonomous_book import BookWorkflow
from workflow_state import encoded, read_json, digest, atomic
from test_autonomous_workflow import COMMAND


class RuntimeRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.book, self.archive = self.base / 'book', self.base / 'original'
        prepare_project(self.book, host='codex', idea='A missing letter.', model='exact-test-model',
            effort='high', autonomous=True, author_name='QA', autonomous_contract={
                'chapters': 1, 'min_words': 100, 'max_words': 400, 'quality_target': 9.0,
                'weighted_quality_target': 9.0})
        workflow = BookWorkflow(self.book, COMMAND, chapters=1, min_words=100, max_words=400,
                                quality_target=9.0, weighted_quality_target=9.0)
        self.journal = workflow.journal
        original = self.book / 'fixture/chapter-01.md'
        original.parent.mkdir()
        original.write_text('# Letter\n\n' + 'The letter was still sealed. ' * 30, encoding='utf-8')
        self.journal.publish(original, self.book / 'manuscript/chapters/chapter-01.md')
        self.journal.data.update(phase=5, status='blocked')
        self.journal.reserve_pass(1, panel_failed=True, rubric_failed=True)
        packet = self.book / 'work/blocked-packet.md'
        packet.parent.mkdir(exist_ok=True)
        packet.write_text('An undispatched preserved packet.', encoding='utf-8')
        self.journal.data['steps']['review'] = {'status': 'blocked_input_size', 'attempts': [
            {'status': 'input_too_large', 'native_dispatched': False,
             'input_evidence': [self.journal.record_file(packet)]}]}
        atomic(self.book / '.book-genesis/native-command.json', encoded(COMMAND))
        self.journal.save()
        self.before = copy.deepcopy(self.journal.data)
        self.prose = (self.book / 'manuscript/chapters/chapter-01.md').read_bytes()

    def recover(self):
        from launcher.recovery import recover_runtime
        return recover_runtime(self.book, self.archive)

    def test_recovery_preserves_prose_attempts_passes_and_quality_contract(self):
        report = self.recover()
        self.assertEqual('recovered', report['status'])
        after = read_json(self.book / '.book-genesis/workflow.json')
        self.assertEqual(self.before['steps'], after['steps'])
        self.assertEqual(self.before['passes'], after['passes'])
        self.assertEqual(self.prose, (self.book / 'manuscript/chapters/chapter-01.md').read_bytes())
        self.assertEqual(self.before, read_json(self.archive / '.book-genesis/workflow.json'))
        for key in self.before['contract']:
            if key not in {'install_sha256', 'runner_sha256'}:
                self.assertEqual(self.before['contract'][key], after['contract'][key])
        read_project(self.book)
        resumed = BookWorkflow(self.book, COMMAND, chapters=1, min_words=100, max_words=400,
                               quality_target=9.0, weighted_quality_target=9.0)
        self.assertEqual(1, len(resumed.journal.data['passes']))

    def test_changed_manuscript_is_rejected_before_creating_archive(self):
        (self.book / 'manuscript/chapters/chapter-01.md').write_text('Changed.', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'manuscript|Canonical'):
            self.recover()
        self.assertFalse(self.archive.exists())

    def test_changed_old_evidence_is_rejected(self):
        (self.book / 'work/blocked-packet.md').write_text('Changed.', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'evidence|changed'):
            self.recover()
        self.assertFalse(self.archive.exists())

    def test_active_native_lock_is_not_removed(self):
        lock = self.book / 'work/host-calls/.active.lock'
        lock.parent.mkdir(parents=True)
        lock.write_text('owned', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'active|lock'):
            self.recover()
        self.assertTrue(lock.exists())

    def test_recovery_receipt_tampering_blocks_future_resume(self):
        self.recover()
        state = read_json(self.book / '.book-genesis/workflow.json')
        receipt = self.book / state['runtime_recoveries'][-1]['path']
        receipt.write_text('{}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'recovery|Recovery'):
            BookWorkflow(self.book, COMMAND, chapters=1, min_words=100, max_words=400,
                         quality_target=9.0, weighted_quality_target=9.0)

    def test_lowered_project_target_cannot_be_adopted_during_recovery(self):
        config_path = self.book / '.book-genesis/project.json'
        config = read_json(config_path)
        config['autonomous_contract']['quality_target'] = 8.0
        atomic(config_path, encoded(config))
        self.journal.data['contract']['project_sha256'] = digest(config_path.read_bytes())
        self.journal.save()
        with self.assertRaisesRegex(ValueError, 'quality|production'):
            self.recover()
        self.assertFalse(self.archive.exists())

    def test_original_blocked_packet_tampering_after_recovery_blocks_resume(self):
        self.recover()
        (self.book / 'work/blocked-packet.md').write_text('Changed after recovery.', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'recovery|Recovery'):
            BookWorkflow(self.book, COMMAND, chapters=1, min_words=100, max_words=400,
                         quality_target=9.0, weighted_quality_target=9.0)

    def test_later_journal_publication_does_not_invalidate_preserved_attempts(self):
        self.recover()
        resumed = BookWorkflow(self.book, COMMAND, chapters=1, min_words=100, max_words=400,
                               quality_target=9.0, weighted_quality_target=9.0)
        candidate = self.book / 'fixture/later.md'
        candidate.write_bytes(self.prose + b'\nShe opened the letter.\n')
        target = self.book / 'manuscript/chapters/chapter-01.md'
        # The real promotion guard is covered by correction-group tests. This
        # unit isolates recovery evidence from a later authorized publication.
        resumed.journal.publish(candidate, target, promote=lambda: atomic(target, candidate.read_bytes()))
        read_project(self.book)
        self.assertEqual(self.prose, (self.archive / 'manuscript/chapters/chapter-01.md').read_bytes())

    def test_consumed_pass_cannot_be_refunded_after_recovery(self):
        self.recover()
        path = self.book / '.book-genesis/workflow.json'
        data = read_json(path)
        data['passes'][0]['panel_failed'] = False
        atomic(path, encoded(data))
        with self.assertRaisesRegex(ValueError, 'consumed revision pass'):
            read_project(self.book)

    def test_second_explicit_recovery_keeps_both_receipts_and_original_archive(self):
        self.recover()
        first = read_json(self.book / '.book-genesis/workflow.json')
        from launcher.recovery import recover_runtime
        recover_runtime(self.book, self.base / 'second-original')
        after = read_json(self.book / '.book-genesis/workflow.json')
        self.assertEqual(2, len(after['runtime_recoveries']))
        self.assertEqual(first['runtime_recoveries'][0], after['runtime_recoveries'][0])
        self.assertEqual(self.before, read_json(self.archive / '.book-genesis/workflow.json'))
        self.assertEqual(first, read_json(self.base / 'second-original/.book-genesis/workflow.json'))
        read_project(self.book)

    def test_symlinked_ancestor_recovers_and_a_leaf_link_is_refused(self):
        from launcher.recovery import recover_runtime
        linked = self.base / 'via-ancestor'
        try:
            linked.symlink_to(self.base, target_is_directory=True)
        except OSError as exc:
            self.skipTest('cannot create a directory link here: ' + str(exc))
        book_via = linked / 'book'
        self.assertNotEqual(book_via.resolve(), book_via)
        report = recover_runtime(book_via, linked / 'original')
        self.assertEqual('recovered', report['status'])
        self.assertEqual(self.prose, (self.book / 'manuscript/chapters/chapter-01.md').read_bytes())
        self.assertEqual(self.before, read_json(self.archive / '.book-genesis/workflow.json'))
        leaf = self.base / 'book-link'
        leaf.symlink_to(self.book, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'unlinked'):
            recover_runtime(leaf, self.base / 'another-archive')
        self.assertFalse((self.base / 'another-archive').exists())

    def test_archive_inventory_reads_long_nested_runtime_paths(self):
        from launcher.recovery import _inventory
        from launcher.cli import _install_path
        archive = self.base / 'archive'
        def cleanup_long_archive():
            import shutil
            if not archive.resolve().is_relative_to(self.base.resolve()):
                raise ValueError('Test archive escaped its temporary workspace')
            if archive.exists():
                shutil.rmtree(_install_path(archive))
        self.addCleanup(cleanup_long_archive)
        relative = '/'.join(['previous-runtime-evidence'] * 12) + '/proof.txt'
        target = _install_path(archive / relative)
        target.parent.mkdir(parents=True)
        target.write_bytes(b'Preserved long-path evidence.')
        self.assertEqual({relative: digest(target.read_bytes())}, _inventory(archive))


if __name__ == '__main__':
    unittest.main()
