from __future__ import annotations

from types import SimpleNamespace

import pytest

from catalog import MODELS, TAGS, VOICE_PROFILES, VOICES
from tts import (
    Request,
    UserError,
    audio_chunks,
    classic_voice_name,
    cloud_args,
    directions,
    ensure_ssml,
    error_message,
    extract_pcm,
    gender_conflict_warnings,
    genai_config,
    plan,
    prompt,
    require_provider_auth,
    split_text,
    wav_bytes,
)


def req(**kwargs) -> Request:
    data = dict(text='你好，世界。', voice='Kore', voice2='Puck')
    data.update(kwargs)
    return Request(**data)


def test_catalog_snapshot():
    assert len(VOICES) == 30
    assert 'Kore' in VOICES and 'Puck' in VOICES
    assert len(VOICE_PROFILES) == 30
    assert sum(1 for item in VOICE_PROFILES if item['gender'] == 'female') == 14
    assert sum(1 for item in VOICE_PROFILES if item['gender'] == 'male') == 16
    assert next(item for item in VOICE_PROFILES if item['name'] == 'Kore')['gender'] == 'female'
    assert next(item for item in VOICE_PROFILES if item['name'] == 'Puck')['gender'] == 'male'
    assert 'gemini-3.1-flash-tts-preview' in MODELS['gemini']
    assert 'gemini-2.5-flash-preview-tts' in MODELS['gemini']
    assert 'gemini-2.5-flash-tts' in MODELS['cloud']
    assert 'gemini-2.5-flash-lite-preview-tts' in MODELS['vertex']
    assert 'chirp3-hd' in MODELS['classic'] and 'wavenet' in MODELS['classic']
    assert TAGS[0][0].startswith('[')


def test_split_prefers_punctuation_and_utf8_boundary():
    chunks = split_text('第一句。第二句！第三句？', 12)
    assert chunks == ['第一句。', '第二句！', '第三句？']
    pieces = split_text('你好世界', 4)
    assert pieces == ['你', '好', '世', '界']
    assert all(len(part.encode()) <= 4 for part in pieces)


def test_split_dialogue_never_breaks_a_turn():
    text = 'Host: 短。\nGuest: 也短。'
    assert split_text(text, 40, dialogue=True) == ['Host: 短。\nGuest: 也短。']
    with pytest.raises(UserError, match='拆成多行'):
        split_text('Host: ' + '啊' * 20, 10, dialogue=True)


def test_plan_single_and_dialogue():
    preview = plan(req())
    assert preview['requests'] == 1
    assert 'TRANSCRIPT:' in preview['prompt']
    assert 'Synthesize speech' in directions(req())
    dialogue = req(
        mode='dialogue',
        text='Host: 你好。\nGuest: 你好。',
        speaker='Host',
        speaker2='Guest',
    )
    assert plan(dialogue)['requests'] == 1


def test_plan_rejects_invalid_combinations():
    with pytest.raises(UserError, match='朗读的文字'):
        plan(req(text='   '))
    with pytest.raises(UserError, match='模型与服务入口'):
        plan(req(provider='gemini', model='gemini-2.5-flash-tts'))
    with pytest.raises(UserError, match='预置声音'):
        plan(req(voice='NotAVoice'))
    with pytest.raises(UserError, match='仅供 Gemini'):
        plan(req(provider='vertex', api='interactions', model='gemini-2.5-flash-tts'))
    with pytest.raises(UserError, match='仅支持单人'):
        plan(req(
            provider='cloud', model='gemini-2.5-flash-lite-preview-tts',
            mode='dialogue', language='cmn-CN', text='Host: a\nGuest: b',
        ))
    with pytest.raises(UserError, match='两位角色'):
        plan(req(mode='dialogue', text='Host: 只有我在说。'))
    with pytest.raises(UserError, match='不支持流式'):
        plan(req(provider='gemini', model='gemini-2.5-flash-preview-tts', stream=True))
    with pytest.raises(UserError, match='结构化对话'):
        plan(req(structured=True, mode='dialogue', text='Host: a\nGuest: b'))
    with pytest.raises(UserError, match='MP3'):
        plan(req(format='mp3'))
    with pytest.raises(UserError, match='语言代码'):
        plan(req(provider='cloud', model='gemini-2.5-flash-tts'))
    with pytest.raises(UserError, match='只做单人'):
        plan(req(provider='classic', model='chirp3-hd', language='cmn-CN', mode='dialogue', text='Host: a\nGuest: b'))
    with pytest.raises(UserError, match='不能流式'):
        plan(req(provider='classic', model='wavenet', voice='cmn-CN-Wavenet-A', language='cmn-CN', stream=True))
    with pytest.raises(UserError, match='最多 20 段'):
        plan(req(text=('字' * 90 + '。') * 21, chunk=True, chunk_bytes=300))


def test_plan_language_and_region_warnings():
    gemini = plan(req(provider='gemini', model='gemini-3.1-flash-tts-preview', language='cmn-CN'))
    assert any('短码' in item for item in gemini['warnings'])
    cloud = plan(req(provider='cloud', model='gemini-2.5-flash-tts', language='cmn'))
    assert any('locale' in item for item in cloud['warnings'])
    vertex = plan(req(provider='vertex', model='gemini-3.1-flash-tts-preview'))
    assert any('global' in item for item in vertex['warnings'])


def test_chunked_plan_counts_requests():
    preview = plan(req(text=('甲' * 90 + '。') + ('乙' * 90 + '。') + ('丙' * 90 + '。'), chunk=True, chunk_bytes=300))
    assert preview['requests'] == 3
    assert preview['chunks'][0].endswith('。')


def test_wav_header_is_pcm16_mono_24k():
    pcm = b'\x00\x00\xff\x7f'
    blob = wav_bytes(pcm)
    assert blob[:4] == b'RIFF' and blob[8:12] == b'WAVE'
    assert blob[22:24] == b'\x01\x00'
    assert blob[24:28] == (24000).to_bytes(4, 'little')
    assert blob[34:36] == b'\x10\x00'
    with pytest.raises(UserError, match='不完整'):
        wav_bytes(b'\x00')
    with pytest.raises(UserError, match='为空'):
        wav_bytes(b'')


def _part(data=b'\x00\x00', mime='audio/L16;rate=24000', reason='STOP'):
    return SimpleNamespace(
        finish_reason=reason,
        content=SimpleNamespace(parts=[SimpleNamespace(inline_data=SimpleNamespace(data=data, mime_type=mime))]),
    )


def test_extract_pcm_and_finish_reasons():
    ok = SimpleNamespace(candidates=[_part()])
    assert list(extract_pcm(ok)) == [b'\x00\x00']
    empty = SimpleNamespace(candidates=[])
    assert list(extract_pcm(empty)) == []
    with pytest.raises(UserError, match='未正常结束'):
        list(extract_pcm(SimpleNamespace(candidates=[_part(reason='SAFETY')])))
    with pytest.raises(UserError, match='未预期'):
        list(extract_pcm(SimpleNamespace(candidates=[_part(mime='audio/mpeg')])))
    ok_lower = SimpleNamespace(candidates=[_part(mime='audio/l16; rate=24000; channels=1')])
    assert list(extract_pcm(ok_lower)) == [b'\x00\x00']
    with pytest.raises(UserError, match='24kHz'):
        list(extract_pcm(SimpleNamespace(candidates=[_part(mime='audio/L16;rate=16000')])))


def test_error_payload_keeps_original_text():
    from tts import error_payload
    payload = error_payload(RuntimeError('503 unavailable model not found'))
    assert '503 unavailable model not found' in payload['detail']
    assert payload['error_type'] == 'RuntimeError'
    assert '404' in payload['message'] or '503' in payload['message'] or '生成失败' in payload['message']
    secret = UserError('请先输入需要朗读的文字。')
    assert error_message(secret) == str(secret)
    assert 'sk-' not in error_message(Exception('401 invalid api key sk-secret'))
    assert '429' in error_message(Exception('429 RESOURCE_EXHAUSTED quota'))
    assert '404' in error_message(Exception('NOT_FOUND 404'))
    assert '400' in error_message(Exception('INVALID_ARGUMENT 400'))
    assert '超时' in error_message(Exception('deadline exceeded timeout'))
    generic = error_message(Exception('PROMPT leaked transcript hello'))
    assert 'hello' not in generic
    assert '生成失败' in generic


def test_retry_only_before_audio_and_only_transient(monkeypatch):
    calls = {'n': 0}

    def flaky(_request, _text):
        calls['n'] += 1
        if calls['n'] == 1:
            raise RuntimeError('503 unavailable')
        yield b'\x01\x02'

    monkeypatch.setattr('tts.generate_genai', flaky)
    assert b''.join(audio_chunks(req(), '你好')) == b'\x01\x02'
    assert calls['n'] == 2

    def after_audio(_request, _text):
        yield b'\x03\x04'
        raise RuntimeError('503 unavailable')

    monkeypatch.setattr('tts.generate_genai', after_audio)
    gen = audio_chunks(req(), '你好')
    assert next(gen) == b'\x03\x04'
    with pytest.raises(RuntimeError, match='503'):
        next(gen)

    def quota(_request, _text):
        raise RuntimeError('429 RESOURCE_EXHAUSTED')

    monkeypatch.setattr('tts.generate_genai', quota)
    with pytest.raises(RuntimeError, match='429'):
        list(audio_chunks(req(), '你好'))

    def silent(_request, _text):
        if False:
            yield b''

    monkeypatch.setattr('tts.generate_genai', silent)
    with pytest.raises(UserError, match='没有返回音频'):
        list(audio_chunks(req(), '你好'))


def test_sdk_type_construction():
    single = genai_config(req(language='cmn'))
    assert single.response_modalities == ['AUDIO']
    assert single.speech_config.voice_config.prebuilt_voice_config.voice_name == 'Kore'
    assert single.speech_config.language_code == 'cmn'
    two = genai_config(req(mode='dialogue', text='Host: a\nGuest: b'))
    names = [item.speaker for item in two.speech_config.multi_speaker_voice_config.speaker_voice_configs]
    assert names == ['Host', 'Guest']
    voice, data = cloud_args(req(provider='cloud', model='gemini-2.5-flash-tts', language='cmn-CN'), '你好')
    assert voice.language_code == 'cmn-CN' and voice.name == 'Kore'
    assert data['text'] == '你好' and 'prompt' in data
    _, structured = cloud_args(
        req(
            provider='cloud', model='gemini-2.5-flash-tts', language='cmn-CN',
            mode='dialogue', structured=True, text='Host: 甲\nGuest: 乙',
        ),
        'Host: 甲\nGuest: 乙',
    )
    assert 'multi_speaker_markup' in structured and 'text' not in structured


def test_prompt_keeps_transcript_separate():
    text = prompt(req(style='温柔'), '请朗读。')
    assert text.index('TRANSCRIPT:') < text.index('请朗读。')
    assert '温柔' in text


def test_classic_voice_name_and_ssml_preview():
    assert classic_voice_name(req(provider='classic', model='chirp3-hd', language='cmn-CN', voice='Kore')) == 'cmn-CN-Chirp3-HD-Kore'
    assert ensure_ssml('你好').startswith('<speak>')
    preview = plan(req(provider='classic', model='chirp3-hd', language='en-US', voice='Puck'))
    assert 'en-US-Chirp3-HD-Puck' in preview['prompt']
    assert '不是 Gemini-TTS' in preview['prompt']
    ssml = plan(req(
        provider='classic', model='wavenet', voice='cmn-CN-Wavenet-A',
        language='cmn-CN', ssml=True, text='<speak>停一下。</speak>',
    ))
    assert 'SSML' in ssml['prompt']
    with pytest.raises(UserError, match='SSML'):
        plan(req(provider='classic', model='chirp3-hd', language='cmn-CN', ssml=True, stream=True))
    pitched = plan(req(
        provider='classic', model='wavenet', voice='cmn-CN-Wavenet-A',
        language='cmn-CN', pitch=4, text='你好。',
    ))
    assert any('pitch=4' in item for item in pitched['warnings'])
    assert 'pitch=4' in pitched['prompt']
    chirp_pitch = plan(req(
        provider='classic', model='chirp3-hd', language='cmn-CN', voice='Leda', pitch=4, text='你好。',
    ))
    assert any('不支持 AudioConfig.pitch' in item for item in chirp_pitch['warnings'])
    assert 'pitch=4' not in chirp_pitch['prompt']
    profiled = plan(req(
        provider='classic', model='wavenet', voice='cmn-CN-Wavenet-A',
        language='cmn-CN', effects_profile='headphone-class-device', volume_gain_db=3, text='你好。',
    ))
    assert any('headphone-class-device' in item for item in profiled['warnings'])
    assert 'effectsProfileId=headphone-class-device' in profiled['prompt']
    assert 'volumeGainDb=3' in profiled['prompt']
    assert classic_voice_name(req(
        provider='classic', model='neural2', voice='en-US-News-K', language='en-US',
    )) == 'en-US-News-K'
    with pytest.raises(UserError, match='locale'):
        plan(req(provider='classic', model='chirp3-hd', language='xx-YY', voice='Kore', text='你好。'))


def test_voice_lock_keeps_female_when_style_is_fierce():
    text = directions(req(voice='Kore', style='凶狠，像是一个黑社会头目在逞凶斗狠'))
    assert 'adult female' in text and 'Kore' in text
    assert '不要变成男声' in text
    assert '黑社会头目' in text
    assert gender_conflict_warnings(req(voice='Kore', style='凶狠，像是一个黑社会头目在逞凶斗狠'))
    assert not gender_conflict_warnings(req(
        voice='Kore',
        style='成年女性，保持女声线，语气凶狠，像女当家在发号施令',
    ))
    male = directions(req(voice='Puck', style='温柔'))
    assert 'adult male' in male and '不要变成女声' in male


def test_require_provider_auth(monkeypatch):
    monkeypatch.delenv('GOOGLE_CLOUD_PROJECT', raising=False)
    with pytest.raises(UserError, match='GOOGLE_CLOUD_PROJECT'):
        require_provider_auth('vertex')
    monkeypatch.setenv('GOOGLE_CLOUD_PROJECT', 'demo-test')
    monkeypatch.setattr('tts.adc_available', lambda: False)
    with pytest.raises(UserError, match='application-default'):
        require_provider_auth('cloud')
    monkeypatch.setattr('tts.adc_available', lambda: True)
    require_provider_auth('vertex')
    with pytest.raises(UserError, match='GEMINI_API_KEY'):
        require_provider_auth('gemini')
