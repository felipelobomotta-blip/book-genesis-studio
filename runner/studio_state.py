"""Durable Studio events and cached, failure-tolerant project reads."""
import json
import re
import threading
from datetime import datetime, timezone

from runner.studio import StudioView


def safe_message(text):
    text = re.sub(r'(?i)(bearer\s+|(?:api[_-]?key|token|authorization)\s*[:=]\s*)[^\s,;]+', r'\1[redacted]', str(text))
    return re.sub(r'\bsk-[A-Za-z0-9_-]{12,}\b', '[redacted]', text)[:5000]


class JournalView(StudioView):
    def __init__(self, project):
        super().__init__()
        self.path = project / 'work/studio-events.jsonl'
        self.journal_lock = threading.Lock()

    def emit(self, kind, **payload):
        if kind == 'error':
            payload = {**payload, 'text': safe_message(payload['text'])}
        if kind in {'stage', 'error', 'result', 'score', 'header'}:
            record = {'timestamp': datetime.now(timezone.utc).isoformat(), 'kind': kind, 'payload': payload}
            try:
                with self.journal_lock:
                    self.path.parent.mkdir(parents=True, exist_ok=True)
                    with self.path.open('a', encoding='utf-8') as handle:
                        handle.write(json.dumps(record, ensure_ascii=False) + '\n')
            except OSError:
                super().emit('activity', text='Studio history could not be saved. Check project folder access.')
        super().emit(kind, **payload)


class FileCache:
    def __init__(self):
        self.entries = {}

    def read(self, path, loader):
        stat = path.stat()
        signature = (stat.st_mtime_ns, stat.st_size)
        entry = self.entries.get(path)
        if entry is None or entry[0] != signature:
            value = loader(path)
            self.entries[path] = (signature, value)
            return value
        return entry[1]

    def previous(self, path, default):
        return self.entries.get(path, (None, default))[1]
