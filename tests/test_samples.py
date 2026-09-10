from __future__ import annotations

from catalog import CLASSIC_INDEX, MODELS, VOICES, WORKSPACES
from samples import load_samples


def test_sample_assets_cover_scenes():
    samples = load_samples()
    ids = [item['id'] for item in samples]
    assert ids[0] == 'welcome'
    for needed in (
        'female-fierce', 'male-fierce', 'youthful', 'mature', 'podcast', 'tags', 'longform',
        'chirp3-hd', 'wavenet-ssml', 'gemini-mixed', 'wavenet-mixed', 'wavenet-ivr', 'chirp-precise',
        'gemini-ivr-prompt', 'chirp-leda', 'chirp-gacrux', 'wavenet-pitch', 'neural2-cs', 'standard-notice',
        'chirp-longform', 'wavenet-longform', 'neural2-longform', 'standard-longform', 'studio-longform',
        'gemini-stream', 'chirp-stream', 'gemini-structured', 'wavenet-korean', 'standard-cantonese',
        'neural2-news', 'studio-french',
    ):
        assert needed in ids
    groups = {item['group'] for item in samples}
    assert {'入门对照', '声线怎么写', '应用场景', '情绪与对话', '多语言', '传统 Cloud TTS', '业务选型', '年龄怎么控', '功能怎么测'} <= groups
    mixed = next(item for item in samples if item['id'] == 'gemini-mixed')
    assert mixed['config']['language'] == ''
    assert '3.1' in mixed['config']['model']
    assert '按原文语言' in mixed['config']['style']
    wavenet_mixed = next(item for item in samples if item['id'] == 'wavenet-mixed')
    assert wavenet_mixed['config']['ssml'] is True
    assert 'ja-JP-Wavenet-A' in wavenet_mixed['config']['text']
    fierce = next(item for item in samples if item['id'] == 'female-fierce')
    assert fierce['config']['voice'] == 'Kore'
    assert '成年女性' in fierce['config']['style'] and '不要变成男声' in fierce['config']['style']
    assert '黑社会头目' not in fierce['config']['style']
    engines = {item['id'] for item in WORKSPACES}
    assert {item['engine'] for item in samples} == engines
    for item in samples:
        config = item['config']
        assert item['engine'] in engines
        assert config['voice'] in VOICES or config['voice'] in CLASSIC_INDEX
        other = config.get('voice2', 'Puck')
        assert other in VOICES or other in CLASSIC_INDEX
        if config.get('model'):
            assert any(config['model'] in names for names in MODELS.values())
        assert item['note']
    by_engine = {}
    for item in samples:
        by_engine.setdefault(item['engine'], []).append(item)
    for engine in engines:
        assert len(by_engine[engine]) >= 8, engine
        assert any(item['config'].get('chunk') for item in by_engine[engine]), engine
    assert any(item['config'].get('stream') for item in by_engine['chirp3-hd'])
    assert any(item['config'].get('structured') for item in by_engine['gemini'])
    assert any(item['config'].get('language') == 'yue-HK' for item in by_engine['standard'])
    assert not any('验证码' in item['title'] and item['engine'] == 'studio' for item in samples)
