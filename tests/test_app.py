from __future__ import annotations

import json

from catalog import EXAMPLES, VOICES


def test_home_and_static(client):
    home = client.get('/')
    assert home.status_code == 200
    assert '声音实验室' in home.text and 'id="workspaces"' in home.text
    assert 'data-page="gemini"' in home.text and 'data-page="chirp3-hd"' in home.text
    assert 'data-page="wavenet"' in home.text and 'data-page="studio"' in home.text
    assert 'id="compare-classic"' in home.text
    assert 'id="compare-why-classic"' in home.text
    assert 'id="compare-age"' in home.text and 'id="compare-fit"' in home.text
    assert 'id="api-out-of-demo"' in home.text
    css = client.get('/static/style.css')
    js = client.get('/static/app.js')
    assert css.status_code == 200 and js.status_code == 200
    assert 'sample.engine===active' in js.text
    assert '本页场景样例' in js.text
    assert 'fillLanguageSelect' in js.text
    assert '当前语言' in js.text
    assert 'AudioConfig.pitch' in js.text


def test_catalog_and_docs(client):
    catalog = client.get('/api/catalog').json()
    assert catalog['checked'] == '2026-09-10'
    assert catalog['key_configured'] is False
    assert catalog['default_provider'] == 'vertex'
    assert set(VOICES) <= set(catalog['voices'])
    assert catalog['examples'][0]['title'] == EXAMPLES[0]['title']
    assert catalog['tags']
    profiles = catalog['voice_profiles']
    assert len(profiles) == 30
    assert {item['name'] for item in profiles} == set(VOICES)
    assert sum(1 for item in profiles if item['gender'] == 'female') == 14
    assert sum(1 for item in profiles if item['gender'] == 'male') == 16
    kore = next(item for item in profiles if item['name'] == 'Kore')
    puck = next(item for item in profiles if item['name'] == 'Puck')
    leda = next(item for item in profiles if item['name'] == 'Leda')
    assert kore['gender'] == 'female' and puck['gender'] == 'male'
    assert 'Youthful' in leda['age_hint']
    assert catalog['voice_rules'][0][0] == '分类'
    assert catalog['compare_providers'][0][1] == 'Gemini API'
    assert catalog['compare_models'][0][1] == '3.1 Flash TTS'
    assert catalog['compare_classic'][0][2] == 'Chirp 3: HD'
    assert catalog['why_classic'][1][0].startswith('日期')
    assert catalog['age_control'][1][0].startswith('有没有年龄')
    assert catalog['fit_guide'][1][1] == 'Gemini-TTS（3.1 或 2.5 Pro）'
    assert any('Instant Custom Voice' in row[0] for row in catalog['api_out_of_demo'])
    gemini = next(item for item in catalog['workspaces'] if item['id'] == 'gemini')
    assert gemini['docs'] and all(item['url'].startswith('https://') for item in gemini['docs'])
    assert all(item.get('docs') and item.get('fit') and item.get('surface') for item in catalog['workspaces'])
    names = {item['name'] for item in catalog['classic_voices']}
    assert {'cmn-CN-Wavenet-A', 'cmn-CN-Wavenet-D', 'en-US-Neural2-A', 'en-US-Neural2-J', 'en-GB-Studio-C', 'de-DE-Wavenet-G', 'en-US-News-K'} <= names
    assert len(catalog['classic_voices']) >= 400
    assert len(catalog['chirp_locales']) >= 50
    assert not any(item['name'].startswith('cmn-CN-Neural2') for item in catalog['classic_voices'])
    assert any(item['name'] == 'cmn-CN-Wavenet-A' for item in catalog['classic_voices'])
    assert [item['id'] for item in catalog['workspaces']] == ['gemini', 'chirp3-hd', 'wavenet', 'neural2', 'standard', 'studio']
    assert 'Flash-Lite' in catalog['model_cards']['gemini-2.5-flash-lite-preview-tts']
    samples = catalog['samples']
    assert len(samples) >= 16
    assert samples[0]['id'] == 'welcome'
    assert any(item['id'] == 'female-fierce' for item in samples)
    assert {item['engine'] for item in samples} >= {'gemini', 'chirp3-hd', 'wavenet', 'neural2', 'standard', 'studio'}
    for name in ('readme', 'guide', 'sources'):
        body = client.get(f'/api/doc/{name}').json()['text']
        assert 'Gemini' in body
    assert client.get('/api/doc/missing').status_code == 404


def test_preview_ok_and_validation(client):
    ok = client.post('/api/preview', json={'text': '你好。', 'voice': 'Kore', 'voice2': 'Puck'})
    assert ok.status_code == 200
    payload = ok.json()
    assert payload['requests'] == 1 and 'TRANSCRIPT:' in payload['prompt']
    assert 'adult female' in payload['prompt']
    conflict = client.post('/api/preview', json={'text': '听好了。', 'voice': 'Kore', 'voice2': 'Puck', 'style': '凶狠，像是一个黑社会头目在逞凶斗狠'})
    assert any('女声读成男声' in item for item in conflict.json()['warnings'])
    bad = client.post('/api/preview', json={'mode': 'dialogue', 'text': '没有角色名', 'voice': 'Kore', 'voice2': 'Puck'})
    assert bad.status_code == 400
    assert 'Host' in bad.json()['detail']


def test_synthesize_without_adc(client):
    response = client.post('/api/synthesize', json={'text': '你好。', 'voice': 'Kore', 'voice2': 'Puck'})
    assert response.status_code == 400
    assert 'GOOGLE_CLOUD_PROJECT' in response.json()['detail']


def test_synthesize_stream_events(client, monkeypatch):
    monkeypatch.setenv('GOOGLE_CLOUD_PROJECT', 'demo-test')
    monkeypatch.setattr('tts.adc_available', lambda: True)

    def fake_chunks(_request, _text):
        yield b'\x00\x01'
        yield b'\x02\x03'

    monkeypatch.setattr('app.audio_chunks', fake_chunks)
    response = client.post('/api/synthesize', json={'text': '你好。', 'voice': 'Kore', 'voice2': 'Puck'})
    assert response.status_code == 200
    events = [json.loads(line) for line in response.text.strip().split('\n')]
    types = [event['type'] for event in events]
    assert types == ['start', 'segment', 'audio', 'audio', 'done']
    assert events[-1]['bytes'] == 4
    assert events[-1]['duration'] == round(4 / 48000, 2)


def test_synthesize_error_event(client, monkeypatch):
    monkeypatch.setenv('GOOGLE_CLOUD_PROJECT', 'demo-test')
    monkeypatch.setattr('tts.adc_available', lambda: True)

    def boom(_request, _text):
        raise RuntimeError('503 unavailable please retry with secret')
        yield b''

    monkeypatch.setattr('app.audio_chunks', boom)
    response = client.post('/api/synthesize', json={'text': '你好。', 'voice': 'Kore', 'voice2': 'Puck'})
    events = [json.loads(line) for line in response.text.strip().split('\n')]
    assert events[-1]['type'] == 'error'
    assert '503' in events[-1]['detail']
    assert events[-1]['error_type'] == 'RuntimeError'
    assert events[-1]['message']


def test_draft_without_key(client):
    response = client.post('/api/draft', json={'topic': '解释 TTS'})
    assert response.status_code == 400


def test_rejects_wrong_host_and_content_type(client):
    bad_host = client.get('/', headers={'host': 'evil.example'})
    assert bad_host.status_code == 400
    plain = client.post('/api/preview', content='text=hi', headers={'content-type': 'text/plain'})
    assert plain.status_code == 415
