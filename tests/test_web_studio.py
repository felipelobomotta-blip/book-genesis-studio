"""HTTP integration evidence; these tests do not claim browser or visual QA."""
import http.client
import json
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from runner.adapters import FakeAdapter, _claude_failure, _claude_stream_result, AdapterError
from runner.filesystem import scaffold_project
from runner.roles import build_role_adapters
from runner.web_studio import ASSETS, StudioModel, StudioServer
from test_session import INTAKE, FOUNDATION, ARCHITECTURE, CHAPTER_ONE, CHAPTER_TWO, AUDIT, SCORE, PACKAGE, SEPARATOR


@pytest.fixture
def studio(tmp_path):
    responses = tmp_path / 'responses.txt'
    responses.write_text(SEPARATOR.join([INTAKE, FOUNDATION, ARCHITECTURE, *CHAPTER_ONE, *CHAPTER_TWO, AUDIT, SCORE, PACKAGE]), encoding='utf-8')
    setup = build_role_adapters(fake_responses_path=responses)
    model = StudioModel(tmp_path / 'library', setup_factory=lambda _: setup)
    server = StudioServer(model)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    model.view.cancel.set()
    if model.worker:
        model.worker.join(5)
    if thread.is_alive():
        server.shutdown()
    server.server_close()
    thread.join(3)


def request(server, path='/api/state', body=None, **extra):
    headers = {'X-Studio-Token': server.token, **extra}
    if body is not None:
        headers['Content-Type'] = 'application/json'
    conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
    conn.request('GET' if body is None else 'POST', path, None if body is None else json.dumps(body), headers)
    response = conn.getresponse()
    data = response.read()
    result = (response.status, dict(response.getheaders()), data)
    conn.close()
    return result


def snapshot(server):
    status, _, data = request(server)
    assert status == 200, data
    return json.loads(data)


def until(server, predicate):
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        state = snapshot(server)
        if predicate(state):
            return state
        time.sleep(.025)
    pytest.fail('Studio did not reach expected state: ' + str(state))


def test_http_full_journey_pause_resume_checkpoints_and_exports(studio):
    assert request(studio, '/api/start', {'new': True, 'idea': 'An analyst finds a hidden clock.', 'language': 'en'})[0] == 200
    state = until(studio, lambda s: s['question'])
    assert state['question']['title'] == 'The brief'
    assert 'BRIEF-SENTINEL' in state['question']['body']
    assert request(studio, '/api/start', {})[0] == 400
    assert request(studio, '/api/answer', {'text': 'no'})[0] == 200
    until(studio, lambda s: not s['active'])
    assert request(studio, '/api/start', {})[0] == 200
    titles = []
    for _ in range(5):
        state = until(studio, lambda s: s['question'] or not s['active'])
        if not state['active']:
            break
        titles.append(state['question']['title'])
        assert request(studio, '/api/answer', {'text': 'yes'})[0] == 200
    state = until(studio, lambda s: not s['active'])
    assert state['status'] == 'completed', state['logs']
    assert len(state['chapters']) == 2
    assert 'The outline' in titles and 'Chapter 1, read blind' in titles
    assert state['feedback'] and state['prose']
    assert request(studio, '/api/answer', {'text': 'yes'})[0] == 400
    status, _, prose = request(studio, '/api/chapter?number=1')
    assert status == 200 and 'DISRUPTED-SENTINEL' in json.loads(prose)['text']
    for fmt in ('markdown', 'epub'):
        status, headers, data = request(studio, '/api/download?format=' + fmt)
        assert status == 200 and data
        assert 'attachment;' in headers['Content-Disposition']
        if fmt == 'epub':
            assert data.startswith(b'PK')
    original = Path(state['project']['path']) / 'manuscript/chapters/chapter-01.md'
    before = original.read_bytes()
    assert request(studio, '/api/notes', {'text': 'Keep the narrator calm.'})[0] == 200
    assert original.read_bytes() == before


@pytest.mark.parametrize('headers', [{'X-Studio-Token': ''}, {'X-Studio-Token': 'wrong'}, {'X-Studio-Token': 'é'}, {'Host': 'attacker.example'}, {'Origin': 'https://attacker.example'}])
def test_rejects_external_or_unauthenticated_access(studio, headers):
    assert request(studio, **headers)[0] == 403
    assert request(studio, '/api/start', {'new': True, 'idea': 'x'}, **headers)[0] == 403
    assert not studio.model.books()


def test_static_assets_and_invalid_routes(studio):
    status, headers, html = request(studio, '/')
    assert status == 200 and studio.token.encode() in html
    assert "frame-ancestors 'none'" in headers['Content-Security-Policy']
    for name in ('studio.js', 'studio.css'):
        assert request(studio, '/' + name)[0] == 200
    assert request(studio, '/../PROJECT_STATE.yaml')[0] == 404
    assert request(studio, '/api/chapter?number=../../x')[0] == 400
    assert request(studio, '/api/open', {'id': 'C:/private'})[0] == 400
    assert request(studio, '/api/start', {'new': True, 'idea': 'x', 'connection': 'unknown'})[0] == 400
    assert request(studio, '/api/start', {'new': True, 'idea': 'x' * 70000})[0] == 400


def test_probe_exposes_real_returned_sample_without_creating_book(studio):
    studio.model.setup_factory = lambda _: SimpleNamespace(adapters={'writer': FakeAdapter(['Actual returned sample.'])}, models={})
    assert request(studio, '/api/probe', {})[0] == 200
    state = until(studio, lambda s: not s['active'])
    assert not state['probing'] and state['probe']['status'] == 'ready'
    assert state['probe']['prose'] == 'Actual returned sample.'
    assert not state['books'] and state['project'] is None


def test_api_configuration_reports_public_activity_while_checking_models(studio):
    """A slow setup check must show safe progress instead of looking frozen."""
    class Adapter:
        name = 'fake-api'
        timeout_seconds = 90

        def complete(self, prompt, *, model=''):
            time.sleep(0.03)
            return 'Welcome, author.'

    config = SimpleNamespace(
        roles={
            'writer': SimpleNamespace(adapter='fake-api', model='writer-model'),
            'judge': SimpleNamespace(adapter='fake-api', model='reader-model'),
        },
        providers={},
    )
    with patch('runner.studio_connections.prepare_setup', return_value=config), \
         patch('runner.roles.build_adapter', return_value=Adapter()), \
         patch('runner.userconfig.write_user_config', return_value=None):
        assert request(studio, '/api/configure-api', {
            'provider': 'openai', 'api_key': 'secret',
            'writer_model': 'writer-model', 'reader_model': 'reader-model',
            'remember': False,
        })[0] == 200
        state = until(studio, lambda s: not s['probing'])
    assert state['probe']['status'] == 'ready'
    assert any('Connection check writer' in line for line in state['probe']['logs'])


def test_provider_failure_does_not_create_an_empty_book(studio):
    """The first-run error must be actionable without leaving an orphan folder."""
    def unavailable(_):
        raise AdapterError('Codex CLI is not logged in. Run `codex login` and try again.')

    studio.model.setup_factory = unavailable
    status, _, data = request(studio, '/api/start', {
        'new': True, 'idea': 'A story that cannot start yet', 'language': 'en'
    })
    assert status == 400
    assert 'not logged in' in json.loads(data)['error']
    assert not studio.model.books()


def test_close_cancels_waiting_checkpoint_and_releases_server(studio):
    assert request(studio, '/api/start', {'new': True, 'idea': 'A small mystery'})[0] == 200
    until(studio, lambda s: s['question'])
    assert request(studio, '/api/close', {})[0] == 200
    studio.model.worker.join(3)
    assert not studio.model.active() and studio.model.closing
    assert (studio.model.project / 'PROJECT_STATE.yaml').exists()


def test_claude_error_uses_declared_failure_and_never_private_events():
    stream = json.dumps({'type': 'stream_event', 'thinking': 'PRIVATE'}) + '\n' + json.dumps({'type': 'result', 'is_error': True, 'errors': ['quota exhausted']})
    assert _claude_failure(stream) == 'quota exhausted'
    with pytest.raises(AdapterError, match='quota exhausted'):
        _claude_stream_result(stream)
    assert _claude_failure(json.dumps({'type': 'assistant', 'text': 'private prose'})) == ''


def test_probe_preserves_completed_session_state(studio):
    model = studio.model
    model.status, model.stage, model.feedback = 'completed', 'Package', 'Saved feedback'
    model.delivery = {'markdown': 'saved.md'}
    model.detail = 'Finished book'
    model.setup_factory = lambda _: SimpleNamespace(adapters={'writer': FakeAdapter(['Sample only'])}, models={})
    request(studio, '/api/probe', {})
    state = until(studio, lambda s: not s['active'])
    assert (state['status'], state['stage'], state['feedback']) == ('completed', 'Package', 'Saved feedback')
    assert model.delivery == {'markdown': 'saved.md'} and state['detail'] == 'Finished book'
    assert state['probe']['prose'] == 'Sample only' and not state['prose']


def test_error_survives_generic_result_restart_and_new_attempt(studio):
    def unavailable(_):
        raise AdapterError('HTTP 401 invalid api_key=SECRET_VALUE')
    project = studio.model.library / 'existing-book'
    scaffold_project(project, idea='A tiny story', adapter='auto', model_name='auto', language='en')
    studio.model.project = project
    studio.model.restore()
    studio.model.setup_factory = unavailable
    request(studio, '/api/start', {})
    state = until(studio, lambda s: not s['active'])
    assert state['last_error']['category'] == 'authentication'
    assert 'SECRET_VALUE' not in str(state['last_error'])
    history = (project / 'work/studio-events.jsonl').read_text(encoding='utf-8')
    assert 'SECRET_VALUE' not in history
    restored = StudioModel(studio.model.library, project)
    assert restored.snapshot()['last_error']['category'] == 'authentication'
    studio.model.view.emit('result', status='failed', message='Generic result')
    assert snapshot(studio)['last_error']['category'] == 'authentication'


def test_cached_summary_returns_previous_value_on_transient_read_error(studio):
    request(studio, '/api/start', {'new': True, 'idea': 'A small mystery'})
    until(studio, lambda s: s['question'])
    previous = snapshot(studio)['project']['title']
    with patch.object(studio.model.cache, 'read', side_effect=PermissionError('File temporarily busy')):
        state = snapshot(studio)
    assert state['project']['title'] == previous
    assert 'File temporarily busy' in state['read_warning']
    assert request(studio, '/api/pause', {})[0] == 200
    until(studio, lambda s: not s['active'])
