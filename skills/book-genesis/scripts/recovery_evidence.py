"""Read-only verification of explicitly recorded stopped-run runtime repairs."""
import json
from hashlib import sha256


def verify_recoveries(root, data):
    root = root.resolve()

    def verify_file(row):
        path = (root / row['path']).resolve()
        if not path.is_relative_to(root) or not path.is_file() or sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Runtime recovery evidence is missing or changed')
        return path

    def read_record(row):
        path = verify_file(row)
        return json.loads(path.read_text(encoding='utf-8'))

    def verify_attempt_files(value):
        if isinstance(value, dict):
            if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
                verify_file(value)
            for child in value.values():
                verify_attempt_files(child)
        elif isinstance(value, list):
            for child in value:
                verify_attempt_files(child)

    previous = None
    for row in data.get('runtime_recoveries', []):
        record = read_record(row)
        if record.get('schema_version') != 1 or record.get('kind') != 'explicit_runtime_recovery':
            raise ValueError('Unsupported runtime recovery evidence')
        before = read_record(record['original_journal'])
        verify_file(record['archive_inventory'])
        old, new = record['old_contract'], record['new_contract']
        if before['contract'] != old or (previous is not None and old != previous):
            raise ValueError('Runtime recovery contract chain differs from original evidence')
        if set(old) != set(new) or any(old[k] != new[k] for k in old if k not in {'install_sha256', 'runner_sha256'}):
            raise ValueError('Runtime recovery changed the model, scoring or production contract')
        # Every old step and consumed pass remains visible. Later outcomes may
        # advance, but history cannot disappear from a recovered run.
        if not set(before['steps']).issubset(data['steps']) or len(before['passes']) > len(data['passes']):
            raise ValueError('Runtime recovery discarded original attempts or revision passes')
        for key, step in before['steps'].items():
            current = data['steps'][key]
            if current.get('request') != step.get('request') or current['attempts'][:len(step['attempts'])] != step['attempts']:
                raise ValueError('Runtime recovery altered a historical native attempt')
            # Attempt packets and responses are immutable. Canonical manuscript
            # paths may legitimately change through verified later revisions.
            verify_attempt_files(step['attempts'])
        for index, old_pass in enumerate(before['passes']):
            current = data['passes'][index]
            for field in ('number', 'reserved_at', 'sources', 'panel_failed', 'rubric_failed'):
                if current.get(field) != old_pass.get(field):
                    raise ValueError('Runtime recovery altered a consumed revision pass')
        previous = new
    if previous is not None and data['contract'] != previous:
        raise ValueError('Runtime recovery does not bind the active execution contract')
    return {'status': 'verified', 'recoveries': len(data.get('runtime_recoveries', []))}
