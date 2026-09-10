from __future__ import annotations

from collections import Counter

from catalog import CHIRP_LOCALES, CLASSIC_INDEX, CLASSIC_PAGE_FAMILIES, CLASSIC_VOICES, VOICES


def test_classic_snapshot_is_the_official_table():
    families = Counter(item['family'] for item in CLASSIC_VOICES)
    assert families['wavenet'] >= 150
    assert families['neural2'] >= 50
    assert families['standard'] >= 170
    assert families['studio'] >= 10
    assert families['news'] >= 10
    assert families['polyglot'] >= 5
    assert 'en-US-News-K' in CLASSIC_INDEX
    assert 'en-US-Polyglot-1' in CLASSIC_INDEX
    assert 'en-US-Casual-K' in CLASSIC_INDEX
    assert len({item['language'] for item in CLASSIC_VOICES if item['family'] == 'wavenet'}) >= 40
    assert not any(item['family'] == 'chirp3-hd' for item in CLASSIC_VOICES)
    assert len(CHIRP_LOCALES) >= 50
    assert {item['code'] for item in CHIRP_LOCALES} >= {'cmn-CN', 'en-US', 'ja-JP', 'yue-HK'}
    assert CLASSIC_INDEX['cmn-CN-Wavenet-A']['gender'] == 'female'
    assert not any(item['name'].startswith('cmn-CN-Neural2') for item in CLASSIC_VOICES)
    assert 'neural2' in CLASSIC_PAGE_FAMILIES['neural2'] and 'news' in CLASSIC_PAGE_FAMILIES['neural2']
    assert 'Kore' in VOICES
