from __future__ import annotations

import json
from pathlib import Path

REQUIRED_URLS = [
    'https://ai.google.dev/gemini-api/docs/speech-generation',
    'https://ai.google.dev/gemini-api/docs/generate-content/speech-generation',
    'https://docs.cloud.google.com/text-to-speech/docs/gemini-tts',
    'https://googleapis.github.io/python-genai/',
    'https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_TTS.ipynb',
    'https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-tts-preview',
    'https://ai.google.dev/gemini-api/docs/batch-api',
    'https://ai.google.dev/gemini-api/docs/pricing',
    'https://ai.google.dev/gemini-api/docs/live-api',
    'https://ai.google.dev/gemini-api/docs/audio',
    'https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd',
    'https://docs.cloud.google.com/text-to-speech/docs/voice-types',
    'https://cloud.google.com/text-to-speech/docs/create-audio',
    'https://cloud.google.com/text-to-speech/docs/ssml',
    'https://cloud.google.com/text-to-speech/docs/voices',
    'https://docs.cloud.google.com/text-to-speech/docs/chirp3-instant-custom-voice',
    'https://cloud.google.com/text-to-speech/docs/audio-profiles',
]


def test_required_docs_exist():
    root = Path(__file__).resolve().parents[1]
    for name in ('README.md', 'learning_guide.md', 'docs/official_sources.md'):
        assert (root / name).is_file()
        assert len((root / name).read_text(encoding='utf-8')) > 500


def test_official_index_covers_主干入口():
    text = (Path(__file__).resolve().parents[1] / 'docs/official_sources.md').read_text(encoding='utf-8')
    missing = [url for url in REQUIRED_URLS if url not in text]
    assert missing == []


def test_learning_guide_covers_can_and_cannot():
    text = (Path(__file__).resolve().parents[1] / 'learning_guide.md').read_text(encoding='utf-8')
    for needle in ('能干什么', '不能干什么', 'Live API', '声音克隆', 'TRANSCRIPT', 'Batch API', '30 个', '少年', '女声', 'Leda', 'Gacrux', 'AudioConfig.pitch', '换 A/B/C/D', '网页 Demo 故意没接'):
        assert needle in text
    readme = (Path(__file__).resolve().parents[1] / 'README.md').read_text(encoding='utf-8')
    assert '少年 / 壮年 / 老年' in readme
    assert '没有 gender 字段' in readme
    assert '传统声音' in readme
    assert 'sample_assets' in readme
    assert '女声也可以凶' in (Path(__file__).resolve().parents[1] / 'learning_guide.md').read_text(encoding='utf-8')


def test_batch_json_and_quickstart_exist():
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / 'examples/batch.json').read_text(encoding='utf-8'))
    assert payload['requests'] and payload['requests'][0]['voice'] in {'Kore', 'Puck'}
    assert (root / 'examples/quickstart.py').is_file()
    assert (root / 'batch_demo.py').is_file()
