import time
from unittest.mock import patch
import pytest
from runner.adapters import FakeAdapter, AdapterError
from runner.studio_connections import prepare_setup
from runner.web_studio import StudioModel


def payload(**overrides):
    return {'provider':'openai','api_key':'test-secret-not-real','writer_model':'chosen-model','reader_model':'reader-model',**overrides}


def test_graphical_setup_uses_explicit_models_and_preserves_other_providers():
    with patch('runner.studio_connections.load_user_config',return_value=None):
        config=prepare_setup(payload())
    assert config.roles['writer'].model=='chosen-model'
    assert config.roles['judge'].model=='reader-model'
    assert config.providers['studio_openai'].base_url=='https://api.openai.com/v1'


@pytest.mark.parametrize('data',[payload(provider='arbitrary-url'),payload(api_key='abc\nwriter:'),payload(writer_model='')])
def test_invalid_connection_inputs_do_not_start_a_provider(data):
    with pytest.raises(ValueError):prepare_setup(data)


def test_configuration_is_saved_only_after_both_models_respond(tmp_path):
    model=StudioModel(tmp_path/'library')
    with patch('runner.studio_connections.load_user_config',return_value=None), patch('runner.roles.build_adapter',return_value=FakeAdapter(['hello','reader ready'])), patch('runner.userconfig.write_user_config') as save:
        model.action('configure-api',payload(remember=True))
        model.worker.join(3)
    assert not model.active() and model.snapshot()['probe']['status']=='ready'
    save.assert_called_once()
    assert 'test-secret-not-real' not in str(model.snapshot())


def test_failed_connection_does_not_replace_or_save_setup(tmp_path):
    class Failing:
        def complete(self,*args,**kwargs):raise AdapterError('bad key test-secret-not-real')
    model=StudioModel(tmp_path/'library')
    with patch('runner.studio_connections.load_user_config',return_value=None), patch('runner.roles.build_adapter',return_value=Failing()), patch('runner.userconfig.write_user_config') as save:
        model.action('configure-api',payload(remember=True))
        model.worker.join(3)
    state=model.snapshot()
    assert state['probe']['status']=='failed' and model.api_setup is None
    assert 'test-secret-not-real' not in str(state)
    save.assert_not_called()


def test_cancelled_connection_does_not_save_or_probe_reader(tmp_path):
    model = StudioModel(tmp_path/'library')
    class CancelDuringReply:
        calls = 0
        def complete(self, *args, **kwargs):
            self.calls += 1
            model.probe_view.cancel.set()
            return 'hello'
    adapter = CancelDuringReply()
    with patch('runner.studio_connections.load_user_config', return_value=None), patch('runner.roles.build_adapter', return_value=adapter), patch('runner.userconfig.write_user_config') as save:
        model.action('configure-api', payload(remember=True))
        model.worker.join(3)
    assert adapter.calls == 1 and model.api_setup is None
    assert 'stopped' in model.snapshot()['probe']['detail']
    save.assert_not_called()
