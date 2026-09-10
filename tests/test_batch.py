from __future__ import annotations

from pathlib import Path

from batch_demo import inlined_requests, load_job


def test_load_inline_batch_json():
    job = load_job(Path(__file__).resolve().parents[1] / 'examples/batch.json')
    assert job['model'].endswith('tts-preview')
    requests = inlined_requests(job)
    assert len(requests) == 2
    assert requests[0]['config']['response_modalities'] == ['AUDIO']
    assert requests[0]['config']['speech_config']['voice_config']['prebuilt_voice_config']['voice_name'] == 'Kore'
    assert 'TRANSCRIPT:' in requests[1]['contents']
