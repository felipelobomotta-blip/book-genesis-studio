import json
from runner.continuity import atomic_json, io_path


def test_deep_evidence_file_can_be_written_read_and_enumerated(tmp_path):
    folder = tmp_path / ('project-' + 'a'*60) / 'work' / 'repair-campaigns' / ('b'*64)
    path = folder / ('c'*64 + '.json')
    assert len(str(path)) > 260
    atomic_json(path, {'saved': True})
    assert json.loads(io_path(path).read_text()) == {'saved': True}
    assert len(list(io_path(folder).glob('*.json'))) == 1
