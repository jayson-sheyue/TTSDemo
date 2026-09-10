"""最小可运行的 Gemini TTS 示例（Vertex AI + ADC）。

用法（在项目根目录）：
    .venv/bin/python examples/quickstart.py

需要：
    gcloud auth application-default login
    gcloud auth application-default set-quota-project YOUR_PROJECT_ID
    .env 里的 GOOGLE_CLOUD_PROJECT

这会发起一次真实的付费/配额调用。
对照：https://docs.cloud.google.com/text-to-speech/docs/gemini-tts#use-vertex-ai-api
"""
from __future__ import annotations

import os
import sys
import wave
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')

OUT = ROOT / 'outputs' / 'quickstart.wav'
MODEL = 'gemini-3.1-flash-tts-preview'
VOICE = 'Kore'
TEXT = 'Say warmly in Mandarin: 你好，欢迎来到声音实验室。'


def save_wav(path: Path, pcm: bytes, rate: int = 24000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(pcm)


def main() -> int:
    project = (os.getenv('GOOGLE_CLOUD_PROJECT') or '').strip()
    if not project:
        print('缺少 GOOGLE_CLOUD_PROJECT。请复制 .env.example 为 .env，并先运行 gcloud auth application-default login。', file=sys.stderr)
        return 1

    client = genai.Client(
        vertexai=True,
        project=project,
        location=os.getenv('GOOGLE_CLOUD_LOCATION', 'global'),
    )
    response = client.models.generate_content(
        model=MODEL,
        contents=TEXT,
        config=types.GenerateContentConfig(
            response_modalities=['AUDIO'],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE)
                )
            ),
        ),
    )
    data = response.candidates[0].content.parts[0].inline_data.data
    if not data:
        print('模型没有返回音频。请缩短文本或换一个可用模型。', file=sys.stderr)
        return 1
    save_wav(OUT, data)
    print(f'已写入 {OUT} （{VOICE} · {MODEL} · Vertex/{project}）')
    print('用系统播放器打开这个 WAV。工作台默认是同一条 ADC 路径。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
