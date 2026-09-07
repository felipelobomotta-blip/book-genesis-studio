"""Graphical connection setup using existing adapters and configuration contracts."""
from runner.setup import BY_KEY
from runner.constants import ROLES
from runner.userconfig import UserConfig, load_user_config

PROVIDERS = ('openrouter', 'deepseek', 'anthropic', 'openai', 'gemini-api', 'groq', 'together', 'ollama', 'lmstudio')


def provider_options():
    return [{'id':key, 'label':key.replace('-api','').title(), 'url':BY_KEY[key].base_url,
             'needs_key':BY_KEY[key].needs_key} for key in PROVIDERS]


def prepare_setup(data):
    key = data.get('provider')
    if key not in PROVIDERS:
        raise ValueError('Choose a listed provider.')
    preset = BY_KEY[key]
    secret, writer = data.get('api_key',''), data.get('writer_model','')
    reader = data.get('reader_model','') or writer
    for value in (secret, writer, reader):
        if not isinstance(value,str) or len(value)>4096 or any(ord(c)<32 for c in value):
            raise ValueError('Use a single-line key and model names.')
    if not writer.strip() or len(writer)>160 or len(reader)>160:
        raise ValueError('Enter the model names available in your provider account.')
    if preset.needs_key and not secret.strip():
        raise ValueError('Enter your provider key. It is never returned to the browser or included in logs.')
    name='studio_'+key.replace('-','_')
    cfg=UserConfig.from_choices(providers={name:{'type':preset.type,'base_url':preset.base_url,
        'api_key':secret.strip() or 'local'}},roles={role:(name,reader.strip() if role=='judge' else writer.strip()) for role in ROLES})
    previous=load_user_config()
    if previous:
        cfg.providers={**previous.providers,**cfg.providers}
    return cfg
