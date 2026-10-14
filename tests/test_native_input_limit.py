"""Do not send an oversized native turn, including bounded format retries."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/book-genesis/scripts'))
from workflow_state import Journal, WorkflowError, read_json
from workflow_roles import PROSE_SCHEMA, validate_prose
from test_autonomous_workflow import COMMAND, receipt_transport

CODEX = {**COMMAND, 'argv': ['fake-native', 'exec', '--ignore-user-config', '-o', '{output}', '-']}


class NativeInputLimitTests(unittest.TestCase):
    def test_large_rejected_producer_response_blocks_before_second_native_dispatch_and_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            journal = Journal(root, {'model': 'exact-test-model', 'effort': 'high'})
            calls = []
            def generate(call_id, packet, schema, book):
                calls.append(call_id)
                self.assertLessEqual(len(packet), 1048576, 'Oversized retry reached the native transport')
                return {'prose': '# One\n\n' + 'x' * 250000, 'continuity_delta': 'Invalid one-word body.'}
            transport = receipt_transport(generate)
            with redirect_stdout(io.StringIO()), self.assertRaisesRegex(WorkflowError, 'native character limit'):
                journal.call('revision', b'Context. ' + b'a' * 849000, PROSE_SCHEMA, CODEX,
                    lambda path: validate_prose(path, low=100, high=1000),
                    feedback=True, feedback_response=True, transport=transport)
            self.assertEqual(1, len(calls))
            step = journal.data['steps']['revision']
            blocked = step['attempts'][-1]
            self.assertEqual('input_too_large', blocked['status'])
            self.assertIs(False, blocked['native_dispatched'])
            self.assertEqual(2, len(step['attempts']))
            self.assertFalse((root / 'work/host-calls' / blocked['call_id']).exists())
            self.assertTrue(blocked['input_evidence'])
            self.assertTrue(blocked['feedback_evidence'])
            journal.verify_files(blocked['input_evidence'])
            first = root / 'work/host-calls' / step['attempts'][0]['call_id']
            self.assertEqual(len('# One\n\n') + 250000, len(read_json(first / 'response')['prose']))
            second = Journal(root, {'model': 'exact-test-model', 'effort': 'high'})
            with redirect_stdout(io.StringIO()), self.assertRaisesRegex(WorkflowError, 'native character limit'):
                second.call('revision', b'Context. ' + b'a' * 849000, PROSE_SCHEMA, CODEX,
                    lambda path: validate_prose(path, low=100, high=1000),
                    feedback=True, feedback_response=True, transport=transport)
            self.assertEqual(1, len(calls))
            self.assertEqual(2, len(second.data['steps']['revision']['attempts']))

    def test_initial_oversized_codex_input_never_calls_transport_or_creates_fake_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            journal = Journal(root, {})
            calls = []
            def forbidden(*args):
                calls.append(args)
                self.fail('Oversized initial input reached the native transport')
            with redirect_stdout(io.StringIO()), self.assertRaisesRegex(WorkflowError, 'native character limit'):
                journal.call('initial', b'x' * 1048577, None, CODEX, lambda p: {'valid': True},
                    transport=forbidden)
            self.assertEqual([], calls)
            step = journal.data['steps']['initial']
            self.assertEqual('input_too_large', step['attempts'][0]['status'])
            self.assertEqual([], list((root / 'work/host-calls').glob('*/receipt.json')))

    def test_character_count_uses_unicode_characters_rather_than_utf8_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            journal = Journal(root, {'model': 'exact-test-model', 'effort': 'high'})
            calls = []
            def generate(call_id, packet, schema, book):
                calls.append(call_id)
                return {'prose': '# One\n\nA complete short scene.', 'continuity_delta': 'No new fact.'}
            with redirect_stdout(io.StringIO()):
                journal.call('unicode', ('é' * 600000).encode('utf-8'), PROSE_SCHEMA, CODEX,
                    lambda p: validate_prose(p, low=1, high=100), transport=receipt_transport(generate))
            self.assertEqual(1, len(calls))

    def test_other_explicit_transports_do_not_inherit_the_codex_character_cap(self):
        with tempfile.TemporaryDirectory() as temporary:
            journal = Journal(Path(temporary), {'model': 'exact-test-model', 'effort': 'high'})
            calls = []
            def generate(call_id, packet, schema, book):
                calls.append(call_id)
                return {'prose': '# One\n\nA complete short scene.', 'continuity_delta': 'No new fact.'}
            with redirect_stdout(io.StringIO()):
                journal.call('other-transport', b'x' * 1048577, PROSE_SCHEMA, COMMAND,
                    lambda p: validate_prose(p, low=1, high=100), transport=receipt_transport(generate))
            self.assertEqual(1, len(calls))


if __name__ == '__main__':
    unittest.main()
