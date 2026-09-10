"""SDK adapters and pure validation helpers. Audio is PCM16 LE mono 24 kHz.

Gemini: official google-genai (GenerateContent or Interactions).
Vertex: official google-genai with ADC.
Cloud TTS: official google-cloud-texttospeech with ADC.
"""
from __future__ import annotations

import base64
import io
import os
import re
import time
import wave
import traceback
from collections.abc import Iterator
from typing import Literal

from pydantic import BaseModel, Field
from catalog import CLASSIC_INDEX, CLASSIC_PAGE_FAMILIES, CLASSIC_PACE, CHIRP_LOCALES, MODELS, VOICE_PROFILES, VOICES

RATE = 24000
VOICE_INDEX = {item['name']: item for item in VOICE_PROFILES}
MALE_ROLE = re.compile(r'黑社会|头目|大哥|汉子|老爷们|男主角|男声|男性|gangster|godfather|\bboss\b', re.I)
FEMALE_KEEP = re.compile(r'女声|女性|女当家|女|woman|female|lady', re.I)
FEMALE_ROLE = re.compile(r'小女孩|少女|女声|女性|女主角', re.I)
MALE_KEEP = re.compile(r'男声|男性|男|man|male', re.I)


class UserError(ValueError):
    pass


class Request(BaseModel):
    provider: Literal['gemini', 'vertex', 'cloud', 'classic'] = 'vertex'
    api: Literal['generate', 'interactions'] = 'generate'
    model: str = 'gemini-3.1-flash-tts-preview'
    mode: Literal['single', 'dialogue'] = 'single'
    text: str = Field(min_length=1, max_length=30000)
    style: str = Field(default='', max_length=3000)
    pace: str = Field(default='自然', max_length=80)
    accent: str = Field(default='', max_length=100)
    scene: str = Field(default='', max_length=400)
    voice: str = 'Kore'
    voice2: str = 'Puck'
    speaker: str = Field(default='Host', max_length=30)
    speaker2: str = Field(default='Guest', max_length=30)
    language: str = Field(default='', max_length=30)
    stream: bool = False
    chunk: bool = False
    chunk_bytes: int = Field(default=1800, ge=300, le=3000)
    format: Literal['wav', 'mp3', 'ogg'] = 'wav'
    structured: bool = False
    ssml: bool = False
    pitch: float = Field(default=0.0, ge=-20.0, le=20.0)


def voice_lock(name: str, who: str = 'The speaker') -> str:
    profile = VOICE_INDEX.get(name)
    if not profile:
        return ''
    if profile['gender'] == 'female':
        return (
            f'{who} is an adult female using prebuilt voice {name}. '
            'Keep a female timbre and pitch range. Performance may be fierce, cold, or angry, '
            'but must not become a male speaker. '
            f'{who}是成年女性声线（{name}）。语气可以凶狠，但不要变成男声。'
        )
    return (
        f'{who} is an adult male using prebuilt voice {name}. '
        'Keep a male timbre and pitch range. Performance may be gentle or youthful, '
        'but must not become a female speaker. '
        f'{who}是成年男性声线（{name}）。语气可以温柔，但不要变成女声。'
    )


def directions(r: Request) -> str:
    parts = ['Synthesize speech. Read only the transcript, not the directions.']
    if r.mode == 'dialogue':
        lock = voice_lock(r.voice, f'Speaker {r.speaker}')
        lock2 = voice_lock(r.voice2, f'Speaker {r.speaker2}')
        if lock: parts.append(lock)
        if lock2: parts.append(lock2)
    else:
        lock = voice_lock(r.voice)
        if lock: parts.append(lock)
    if r.style.strip(): parts.append('Performance: ' + r.style.strip())
    if r.pace.strip(): parts.append('Pacing: ' + r.pace)
    if r.accent.strip(): parts.append('Accent: ' + r.accent.strip())
    if r.scene.strip(): parts.append('Scene: ' + r.scene.strip())
    return '\n'.join(parts)


def gender_conflict_warnings(r: Request) -> list[str]:
    notes = f'{r.style}\n{r.scene}'
    warnings = []
    profile = VOICE_INDEX.get(r.voice)
    if profile and profile['gender'] == 'female' and MALE_ROLE.search(notes) and not FEMALE_KEEP.search(notes):
        warnings.append(
            '语气里的角色偏男性（如「黑社会头目」），模型常会把女声读成男声。'
            '请改成「成年女性，保持女声线，语气凶狠」，或改选男声。可一键导入样例「女声也可以凶」。'
        )
    if profile and profile['gender'] == 'male' and FEMALE_ROLE.search(notes) and not MALE_KEEP.search(notes):
        warnings.append(
            '语气里的角色偏女性，模型可能把男声读成女声。请在语气里写明「成年男性，保持男声线」，或改选女声。'
        )
    if r.mode == 'dialogue':
        other = VOICE_INDEX.get(r.voice2)
        if other and other['gender'] == 'female' and MALE_ROLE.search(notes) and not FEMALE_KEEP.search(notes):
            warnings.append(f'角色 B 当前是女声 {r.voice2}，请避免用默认男性身份去描写她。')
    return warnings


def classic_voice_name(r: Request) -> str:
    if r.model == 'chirp3-hd':
        if r.voice not in VOICES:
            raise UserError('Chirp 3: HD 使用与 Gemini 相同的 30 个短名，例如 Kore / Puck。')
        if not r.language.strip():
            raise UserError('Chirp 3: HD 需要语言代码，例如 cmn-CN 或 en-US。')
        return f'{r.language.strip()}-Chirp3-HD-{r.voice}'
    profile = CLASSIC_INDEX.get(r.voice)
    allowed = CLASSIC_PAGE_FAMILIES.get(r.model, (r.model,))
    if not profile or profile['family'] not in allowed:
        raise UserError('请选择当前页声音家族里的传统 Cloud 声音。换语言后下拉会列出该 locale 的全表。')
    return r.voice


def ensure_ssml(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith('<speak'):
        return stripped
    return f'<speak>{stripped}</speak>'


def classic_uses_ssml(r: Request, text: str) -> bool:
    return bool(r.ssml or text.lstrip().startswith('<speak'))


def prompt(r: Request, text: str) -> str:
    if r.provider == 'classic':
        name = classic_voice_name(r)
        kind = 'SSML' if classic_uses_ssml(r, text) else 'text'
        return (
            f'Cloud TTS 传统合成（不是 Gemini-TTS）。\n'
            f'family={r.model} voice={name} language={r.language} input={kind}\n'
            f'Gemini 提示词不会发送。节奏由 speaking_rate / SSML 控制'
            + (f'；pitch={r.pitch}' if r.model != 'chirp3-hd' and r.pitch else '')
            + '。\n\nINPUT:\n'
            + (ensure_ssml(text) if classic_uses_ssml(r, text) else text)
        )
    return directions(r) + '\n\nTRANSCRIPT:\n' + text


def dialogue_lines(r: Request, text: str) -> list[tuple[str, str]]:
    result = []
    for line in text.splitlines():
        if not line.strip(): continue
        match = re.fullmatch(r'([^:：]+)[:：]\s*(.+)', line.strip())
        if not match or match[1] not in (r.speaker, r.speaker2) or not match[2].strip():
            raise UserError(f'对话每行须以 {r.speaker}: 或 {r.speaker2}: 开头，后面写台词。')
        result.append((match[1], match[2]))
    return result


def split_text(text: str, limit: int, dialogue: bool = False) -> list[str]:
    """Preserve text exactly; prefer punctuation. Never break a speaker turn."""
    units = text.splitlines(keepends=True) if dialogue else re.findall(r'.*?[。！？.!?\n]+|.+$', text, re.S)
    chunks, current = [], ''
    for unit in units:
        if len(unit.encode()) > limit:
            if dialogue:
                raise UserError('一行对话超过分段上限，请把该角色台词拆成多行，每行保留角色名。')
            if current: chunks.append(current); current = ''
            for char in unit:
                if len((current + char).encode()) > limit:
                    chunks.append(current); current = ''
                current += char
        else:
            if len((current + unit).encode()) > limit:
                chunks.append(current); current = ''
            current += unit
    if current: chunks.append(current)
    return chunks


def plan(r: Request) -> dict:
    if not r.text.strip(): raise UserError('请先输入需要朗读的文字。')
    if r.model not in MODELS[r.provider]: raise UserError('模型与服务入口不匹配，请重新选择模型。')
    if r.provider != 'gemini' and r.api != 'generate': raise UserError('Interactions 仅供 Gemini API 使用。')
    if r.provider == 'classic':
        classic_voice_name(r)
        if r.mode == 'dialogue': raise UserError('传统 Cloud TTS 本 Demo 只做单人。双人请改用 Gemini-TTS。')
        if r.structured: raise UserError('结构化双人仅用于 Cloud Gemini-TTS，不是 WaveNet / Chirp。')
        if not r.language.strip(): raise UserError('传统 Cloud TTS 需要语言代码，例如 cmn-CN 或 en-US。')
        if r.ssml and r.stream: raise UserError('Chirp 3: HD 的 SSML 仅支持非流式；请关闭流式或取消 SSML。')
        if r.stream and r.model != 'chirp3-hd': raise UserError('WaveNet / Neural2 / Standard / Studio 不能流式；请关闭流式或改用 Chirp 3: HD。')
        if r.format != 'wav' and (r.stream or r.chunk): raise UserError('MP3 / OGG 仅支持非流式、非分段的 Cloud TTS。')
        if r.model == 'chirp3-hd':
            codes = {item['code'] for item in CHIRP_LOCALES}
            if r.language.strip() not in codes:
                raise UserError(f'Chirp 3 HD 当前快照没有 locale {r.language}。请用语言下拉选择声音表中的语言。')
        elif CLASSIC_INDEX[r.voice]['language'] != r.language:
            raise UserError(f'声音 {r.voice} 的语言是 {CLASSIC_INDEX[r.voice]["language"]}，请把语言代码改成一致。')
    else:
        if r.voice not in VOICES or r.voice2 not in VOICES: raise UserError('请选择列表中的预置声音。')
        if r.mode == 'dialogue':
            if 'lite' in r.model: raise UserError('Flash-Lite TTS 仅支持单人朗读。')
            if r.speaker == r.speaker2 or not all(re.fullmatch('[A-Za-z0-9]+', x) for x in (r.speaker, r.speaker2)):
                raise UserError('两个角色名须不同，并仅使用英文字母和数字，如 Host / Guest。')
            turns = dialogue_lines(r, r.text)
            if {name for name, _ in turns} != {r.speaker, r.speaker2}: raise UserError('双人模式需要两位角色各有至少一句台词。')
        if r.provider == 'gemini' and r.stream and '3.1' not in r.model:
            raise UserError('Gemini API 的 2.5 TTS 不支持流式；请改用 3.1 或关闭流式。')
        if r.structured and (r.provider != 'cloud' or r.mode != 'dialogue' or r.stream):
            raise UserError('结构化对话仅支持 Cloud TTS 双人非流式合成。')
        if r.format != 'wav' and (r.provider != 'cloud' or r.stream or r.chunk):
            raise UserError('MP3 / OGG 仅支持 Cloud TTS 的非流式、非分段请求。')
        if r.provider == 'cloud' and not r.language.strip(): raise UserError('Cloud TTS 需要语言代码，例如 cmn-CN 或 en-US。')
    if r.language and not re.fullmatch('[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*', r.language):
        raise UserError('语言代码格式不正确，例如 cmn-CN、en-US、ja-JP。')
    chunks = split_text(r.text, r.chunk_bytes, r.mode == 'dialogue') if r.chunk else [r.text]
    if len(chunks) > 20: raise UserError('本 Demo 一次最多 20 段，请减少文本或增大分段上限。')
    for text in chunks:
        if r.provider != 'classic' and len(directions(r).encode()) > 4000: raise UserError('风格与导演提示合计超过本 Demo 的 4000 字节上限。')
        if r.provider in {'cloud', 'classic'} and len(text.encode()) > 4000: raise UserError('Cloud 每段文字不能超过 4000 UTF-8 字节，请启用长文分段。')
        if r.provider != 'classic' and len(prompt(r, text).encode()) > 8000: raise UserError('每段文字及提示超过本 Demo 的 8000 UTF-8 字节保守上限，请启用分段。')
    warnings = ['每次生成都可能有变化；下载后请核对是否漏字、读错或提前结束。']
    if r.provider != 'classic':
        warnings.extend(gender_conflict_warnings(r))
    else:
        warnings.append('这是传统 Cloud TTS，不是 Gemini-TTS。提示词不会被当成导演阐述；请用 SSML 或 speaking_rate。')
        if r.model == 'chirp3-hd':
            warnings.append(f'将请求声音 {classic_voice_name(r)}。Chirp 3: HD 与 Gemini 共用短名，但合成路径不同。')
        if r.pace.startswith('逐渐'):
            warnings.append('传统 TTS 不能做「逐渐加快」这种曲线，只会用一个固定语速。')
        if r.pitch and r.model == 'chirp3-hd':
            warnings.append('声音类型总览写明 Chirp 3: HD 不支持 AudioConfig.pitch；本 Demo 不会发送音高。换年轻/成熟请改选 Leda / Gacrux。')
        elif r.pitch:
            warnings.append(f'将发送 AudioConfig.pitch={r.pitch} 半音。这是音高，不是官方年龄档。')
    if r.chunk: warnings.append('长文分段是应用层逐段调用，会重复发送风格提示；接缝和声线可能变化，不等同于 Batch API。')
    if r.stream: warnings.append('收到音频后立即播放；停止会中断接收，但已提交的云端请求仍可能计费。')
    if '3.1' in r.model and r.provider not in {'gemini', 'classic'}:
        warnings.append('Cloud 文档显示 3.1 TTS 目前主要在 global 区域；请核对 GOOGLE_CLOUD_LOCATION / CLOUD_TTS_ENDPOINT。')
    if r.provider == 'gemini' and r.language.count('-'):
        warnings.append('Gemini API 语言表多用短码（如 cmn、en）；带地区的 locale（如 cmn-CN）是 Cloud 的写法。')
    if r.provider in {'cloud', 'classic'} and r.language in {'cmn', 'en', 'ja'}:
        warnings.append('Cloud TTS 需要完整 locale，例如 cmn-CN、en-US、ja-JP。')
    return {'chunks': chunks, 'requests': len(chunks), 'text_bytes': len(r.text.encode()), 'prompt': prompt(r, chunks[0]), 'warnings': warnings}


def wav_bytes(pcm: bytes) -> bytes:
    if not pcm or len(pcm) % 2: raise UserError('音频为空或 PCM 数据不完整，请重新生成。')
    out = io.BytesIO()
    with wave.open(out, 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(RATE); f.writeframes(pcm)
    return out.getvalue()


def extract_pcm(response) -> Iterator[bytes]:
    for candidate in getattr(response, 'candidates', None) or []:
        reason = str(getattr(candidate, 'finish_reason', '') or '')
        if reason and not reason.endswith(('STOP', 'UNSPECIFIED')):
            raise UserError('生成未正常结束（' + reason + '），请缩短文字或检查内容；不会将部分音频当作完整结果。')
        for part in getattr(getattr(candidate, 'content', None), 'parts', None) or []:
            inline = getattr(part, 'inline_data', None)
            if inline and inline.data:
                mime = (inline.mime_type or '').lower()
                if not (mime.startswith('audio/l16') or mime.startswith('audio/pcm')):
                    raise UserError('收到未预期的音频编码：' + (inline.mime_type or ''))
                rate = re.search(r'rate=(\d+)', mime)
                if rate and int(rate[1]) != RATE: raise UserError('收到非 24kHz 音频，不能按当前格式播放。')
                yield inline.data


def adc_available() -> bool:
    try:
        import google.auth
        credentials, _project = google.auth.default()
        return credentials is not None
    except Exception:
        return False


def require_provider_auth(provider: str) -> None:
    if provider == 'gemini':
        if not (os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')):
            raise UserError('Gemini API 需要 GEMINI_API_KEY。本 Demo 默认走 Vertex + ADC，请改回 Vertex，或运行 gcloud auth application-default login。')
        return
    if not (os.getenv('GOOGLE_CLOUD_PROJECT') or '').strip():
        raise UserError('请在 .env 填写 GOOGLE_CLOUD_PROJECT，并运行：gcloud auth application-default login。预览无需凭据。')
    if not adc_available():
        raise UserError('未检测到 Application Default Credentials。请运行：gcloud auth application-default login，然后 gcloud auth application-default set-quota-project 你的项目ID，并重启服务。')


def genai_client(provider: str):
    from google import genai
    from google.genai import types
    options = types.HttpOptions(timeout=120000, retry_options=types.HttpRetryOptions(attempts=1))
    if provider == 'vertex':
        require_provider_auth('vertex')
        return genai.Client(vertexai=True, project=os.getenv('GOOGLE_CLOUD_PROJECT'), location=os.getenv('GOOGLE_CLOUD_LOCATION', 'global'), http_options=options)
    require_provider_auth('gemini')
    return genai.Client(vertexai=False, api_key=os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'), http_options=options)


def genai_config(r: Request):
    from google.genai import types as t
    def voice(name): return t.VoiceConfig(prebuilt_voice_config=t.PrebuiltVoiceConfig(voice_name=name))
    kwargs = {'language_code': r.language} if r.language else {}
    if r.mode == 'single': kwargs['voice_config'] = voice(r.voice)
    else:
        kwargs['multi_speaker_voice_config'] = t.MultiSpeakerVoiceConfig(speaker_voice_configs=[
            t.SpeakerVoiceConfig(speaker=r.speaker, voice_config=voice(r.voice)),
            t.SpeakerVoiceConfig(speaker=r.speaker2, voice_config=voice(r.voice2))])
    return t.GenerateContentConfig(response_modalities=['AUDIO'], speech_config=t.SpeechConfig(**kwargs))


def generate_genai(r: Request, text: str) -> Iterator[bytes]:
    with genai_client(r.provider) as client:
        if r.api == 'interactions':
            voices = [{'voice': r.voice}]
            if r.mode == 'dialogue': voices = [{'speaker': r.speaker, 'voice': r.voice}, {'speaker': r.speaker2, 'voice': r.voice2}]
            if r.language:
                for v in voices: v['language'] = r.language
            result = client.interactions.create(model=r.model, input=prompt(r, text), response_format={'type': 'audio'}, generation_config={'speech_config': voices}, stream=r.stream, store=False)
            if r.stream:
                try:
                    for event in result:
                        if event.event_type in ('error', 'interaction.failed'): raise UserError('Interactions 流式请求失败，请检查模型和输入。')
                        if event.event_type == 'step.delta' and getattr(event.delta, 'type', '') == 'audio':
                            yield base64.b64decode(event.delta.data)
                finally:
                    if hasattr(result, 'close'): result.close()
            else:
                audio = result.output_audio
                if audio: yield base64.b64decode(audio.data)
        else:
            kwargs = dict(model=r.model, contents=prompt(r, text), config=genai_config(r))
            if r.stream:
                stream = client.models.generate_content_stream(**kwargs)
                try:
                    for response in stream: yield from extract_pcm(response)
                finally:
                    if hasattr(stream, 'close'): stream.close()
            else: yield from extract_pcm(client.models.generate_content(**kwargs))


def cloud_args(r: Request, text: str):
    from google.cloud import texttospeech as t
    voice = dict(language_code=r.language, model_name=r.model)
    if r.mode == 'single': voice['name'] = r.voice
    else:
        voice['multi_speaker_voice_config'] = t.MultiSpeakerVoiceConfig(speaker_voice_configs=[
            t.MultispeakerPrebuiltVoice(speaker_alias=r.speaker, speaker_id=r.voice),
            t.MultispeakerPrebuiltVoice(speaker_alias=r.speaker2, speaker_id=r.voice2)])
    data = dict(prompt=directions(r))
    if r.structured:
        data['multi_speaker_markup'] = t.MultiSpeakerMarkup(turns=[t.MultiSpeakerMarkup.Turn(speaker=s, text=line) for s, line in dialogue_lines(r, text)])
    else: data['text'] = text
    return t.VoiceSelectionParams(**voice), data


def generate_classic(r: Request, text: str) -> Iterator[bytes]:
    from google.cloud import texttospeech as t
    client = t.TextToSpeechClient(client_options={'api_endpoint': os.getenv('CLOUD_TTS_ENDPOINT', 'texttospeech.googleapis.com')})
    try:
        name = classic_voice_name(r)
        voice = t.VoiceSelectionParams(language_code=r.language, name=name)
        rate = CLASSIC_PACE.get(r.pace, 1.0)
        if r.stream:
            config = t.StreamingSynthesizeConfig(
                voice=voice,
                streaming_audio_config=t.StreamingAudioConfig(audio_encoding=t.AudioEncoding.PCM, sample_rate_hertz=RATE),
            )
            requests = iter([
                t.StreamingSynthesizeRequest(streaming_config=config),
                t.StreamingSynthesizeRequest(input=t.StreamingSynthesisInput(text=text)),
            ])
            stream = client.streaming_synthesize(requests=requests, timeout=120, retry=None)
            try:
                for response in stream:
                    if response.audio_content: yield response.audio_content
            finally:
                if hasattr(stream, 'cancel'): stream.cancel()
        else:
            payload = dict(ssml=ensure_ssml(text)) if classic_uses_ssml(r, text) else dict(text=text)
            encoding = {'wav': t.AudioEncoding.LINEAR16, 'mp3': t.AudioEncoding.MP3, 'ogg': t.AudioEncoding.OGG_OPUS}[r.format]
            audio = dict(audio_encoding=encoding, sample_rate_hertz=RATE, speaking_rate=rate)
            if r.model != 'chirp3-hd' and r.pitch:
                audio['pitch'] = r.pitch
            response = client.synthesize_speech(
                input=t.SynthesisInput(**payload),
                voice=voice,
                audio_config=t.AudioConfig(**audio),
                timeout=120, retry=None,
            )
            if r.format == 'wav':
                with wave.open(io.BytesIO(response.audio_content), 'rb') as f:
                    if (f.getnchannels(), f.getsampwidth(), f.getframerate()) != (1, 2, RATE):
                        raise UserError('Cloud 返回的 WAV 格式不符合预期。')
                    yield f.readframes(f.getnframes())
            else:
                yield response.audio_content
    finally:
        client.transport.close()


def generate_cloud(r: Request, text: str) -> Iterator[bytes]:
    from google.cloud import texttospeech as t
    client = t.TextToSpeechClient(client_options={'api_endpoint': os.getenv('CLOUD_TTS_ENDPOINT', 'texttospeech.googleapis.com')})
    try:
        voice, data = cloud_args(r, text)
        if r.stream:
            config = t.StreamingSynthesizeConfig(voice=voice, streaming_audio_config=t.StreamingAudioConfig(audio_encoding=t.AudioEncoding.PCM, sample_rate_hertz=RATE))
            requests = iter([t.StreamingSynthesizeRequest(streaming_config=config), t.StreamingSynthesizeRequest(input=t.StreamingSynthesisInput(**data))])
            stream = client.streaming_synthesize(requests=requests, timeout=120, retry=None)
            try:
                for response in stream:
                    if response.audio_content: yield response.audio_content
            finally:
                if hasattr(stream, 'cancel'): stream.cancel()
        else:
            encoding = {'wav': t.AudioEncoding.LINEAR16, 'mp3': t.AudioEncoding.MP3, 'ogg': t.AudioEncoding.OGG_OPUS}[r.format]
            response = client.synthesize_speech(input=t.SynthesisInput(**data), voice=voice, audio_config=t.AudioConfig(audio_encoding=encoding, sample_rate_hertz=RATE), timeout=120, retry=None)
            if r.format == 'wav':
                with wave.open(io.BytesIO(response.audio_content), 'rb') as f:
                    if (f.getnchannels(), f.getsampwidth(), f.getframerate()) != (1, 2, RATE): raise UserError('Cloud 返回的 WAV 格式不符合预期。')
                    yield f.readframes(f.getnframes())
            else: yield response.audio_content
    finally:
        client.transport.close()


_SECRET = re.compile(r'(?i)((?:api[_-]?key|token|bearer|authorization|ya29\.|AIza)[=:\s]+)[^\s,;\'"]+')


def redact(text: str) -> str:
    return _SECRET.sub(r'\1***', text)


def error_payload(error: Exception) -> dict:
    """Friendly summary plus original traceback for the on-page log box."""
    raw = redact(''.join(traceback.format_exception(type(error), error, error.__traceback__)))
    return {
        'message': error_message(error),
        'detail': raw.strip() or type(error).__name__,
        'error_type': type(error).__name__,
    }


def error_message(error: Exception) -> str:
    if isinstance(error, UserError): return str(error)
    # Never return raw provider errors: they can contain text or credentials.
    msg = str(error).lower()
    if any(x in msg for x in ('429', 'resource_exhausted', 'quota')): return '请求过于频繁或额度不足（429）。请检查配额/账单，稍后再试。'
    if any(x in msg for x in ('401', '403', 'permission', 'credential', 'api key', 'adc', 'reauth')): return '身份验证或权限失败。Vertex / Cloud 请检查 ADC、GOOGLE_CLOUD_PROJECT、已启用 API、账单和 IAM；Gemini API 才使用 API Key。'
    if '404' in msg or 'not_found' in msg: return '模型或区域不可用（404）。请核对服务入口、模型名称与区域。'
    if '400' in msg or 'invalid_argument' in msg: return '参数不被服务接受（400）。请检查语言代码、模型能力、文本长度和 SDK 版本。'
    if any(x in msg for x in ('timeout', 'deadline', 'connect', 'resolve')): return '连接超时或网络不可达。请检查网络；已发出的请求仍可能计费。'
    return '生成失败，可能为服务端暂时异常或内容被拒绝。请缩短文字后重试，并参阅排错指南。'


def audio_chunks(r: Request, text: str) -> Iterator[bytes]:
    """Retry only transient failures BEFORE audio is emitted. Never replay a partial stream."""
    for attempt in range(2):
        emitted = False
        try:
            source = generate_classic(r, text) if r.provider == 'classic' else generate_cloud(r, text) if r.provider == 'cloud' else generate_genai(r, text)
            for data in source:
                if data: emitted = True; yield data
            if not emitted: raise UserError('服务没有返回音频。请明确写“朗读以下台词”，缩短输入并重试。')
            return
        except Exception as error:
            transient = any(x in str(error).lower() for x in ('500', '502', '503', 'unavailable', 'internal'))
            if emitted or attempt or not transient: raise
            time.sleep(1)
