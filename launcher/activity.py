"""Read-only observations of the journal, never an assertion of process liveness."""
from datetime import datetime, timezone
import json
import re


def request_label(key):
    match = re.fullmatch(r'draft-(\d+)', key)
    if match:
        return f'Drafting chapter {int(match[1])}'
    match = re.match(r'revision-\d+-c(\d+)', key)
    if match:
        return f'Revising chapter {int(match[1])}'
    if key.startswith('continuity-'):
        return 'Checking continuity across accepted chapters'
    if 'check' in key or 'audit' in key or 'measure' in key:
        return 'Reviewing saved manuscript evidence'
    return {'foundation': 'Developing characters and voice', 'architecture': 'Planning scenes and dependencies',
            'intake': 'Shaping the book idea'}.get(key, key)


def collect_activity(root, *, now=None):
    result = {'journal_status': 'unavailable', 'process_liveness': 'not_checked', 'requests': [],
              'diagnostic': None}
    path = root / '.book-genesis/workflow.json'
    if not path.is_file():
        return result
    try:
        journal = json.loads(path.read_bytes())
        if not isinstance(journal, dict) or not isinstance(journal.get('steps'), dict):
            raise ValueError('Invalid workflow journal shape')
        result.update(journal_status=journal.get('status', 'unknown'), phase=journal.get('phase'))
        now = now or datetime.now(timezone.utc)
        for key, step in journal['steps'].items():
            if not isinstance(step, dict):
                raise ValueError('Invalid workflow step shape')
            if step.get('status') == 'completed':
                continue
            attempts = step.get('attempts', [])
            if not isinstance(attempts, list) or any(not isinstance(a, dict) for a in attempts):
                raise ValueError('Invalid workflow attempt shape')
            attempt = attempts[-1] if attempts else {}
            elapsed = None
            if attempt.get('reserved_at') and attempt.get('status') == 'reserved':
                try:
                    start = datetime.fromisoformat(attempt['reserved_at'])
                    if start.tzinfo is not None:
                        elapsed = max(0, int((now - start).total_seconds()))
                except (ValueError, TypeError):
                    pass
            result['requests'].append({'step': key, 'label': request_label(key),
                'status': step.get('status', 'unknown'), 'attempt_status': attempt.get('status'),
                'seconds_since_reserved': elapsed,
                'detail': attempt.get('error') or step.get('error') or
                          (attempt.get('provider_wait') or {}).get('reason')})
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        result.update(journal_status='unavailable', requests=[], diagnostic=str(exc))
    return result
