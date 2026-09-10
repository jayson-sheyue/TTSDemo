"""真正的 Gemini Batch API 命令行示例。不是工作台长文分段。

用法（在项目根目录，会发起真实云端任务，可能计费）：
    .venv/bin/python batch_demo.py submit examples/batch.json
    .venv/bin/python batch_demo.py status batches/返回的任务ID
    .venv/bin/python batch_demo.py download batches/返回的任务ID
    .venv/bin/python batch_demo.py cancel batches/返回的任务ID

submit 只提交一次，不轮询。download 只在任务成功后取回 inline 音频。
有 GOOGLE_CLOUD_PROJECT 时走 Vertex ADC；否则才使用 GEMINI_API_KEY。
Vertex 的大型任务通常写入 GCS，inline 小样本在 Developer API 上更常见。
大型 JSONL / 文件结果见：https://ai.google.dev/gemini-api/docs/batch-api
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from tts import extract_pcm, wav_bytes

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')


def client():
    from google import genai
    project = (os.getenv('GOOGLE_CLOUD_PROJECT') or '').strip()
    if project:
        return genai.Client(vertexai=True, project=project, location=os.getenv('GOOGLE_CLOUD_LOCATION', 'global'))
    key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not key:
        raise SystemExit('缺少 ADC 项目或 API Key。推荐：gcloud auth application-default login，并设置 GOOGLE_CLOUD_PROJECT。')
    return genai.Client(api_key=key)


def load_job(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data.get('requests'), list) or not data['requests']:
        raise SystemExit('JSON 需要非空的 requests 数组。')
    data.setdefault('model', 'gemini-3.1-flash-tts-preview')
    data.setdefault('display_name', 'tts-lab-inline-demo')
    for index, item in enumerate(data['requests'], start=1):
        if not str(item.get('text', '')).strip():
            raise SystemExit(f'第 {index} 条缺少 text。')
        item.setdefault('voice', 'Kore')
    return data


def inlined_requests(job: dict) -> list[dict]:
    result = []
    for item in job['requests']:
        result.append({
            'contents': item['text'],
            'config': {
                'response_modalities': ['AUDIO'],
                'speech_config': {
                    'voice_config': {
                        'prebuilt_voice_config': {'voice_name': item['voice']}
                    }
                },
            },
        })
    return result


def submit(path: Path) -> None:
    job = load_job(path)
    created = client().batches.create(
        model=job['model'],
        src=inlined_requests(job),
        config={'display_name': job['display_name']},
    )
    print(created.name)
    print('已提交。复制上面的任务名，稍后运行 status / download。本命令不会自动轮询。')


def status(name: str) -> None:
    job = client().batches.get(name=name)
    state = getattr(getattr(job, 'state', None), 'name', None) or job.state
    print(f'{job.name}\nstate={state}')
    if getattr(job, 'error', None):
        print(f'error={job.error}')


def download(name: str) -> None:
    job = client().batches.get(name=name)
    state = getattr(getattr(job, 'state', None), 'name', None) or str(job.state)
    if state != 'JOB_STATE_SUCCEEDED':
        raise SystemExit(f'任务尚未成功（{state}）。成功后再 download，不要循环重试计费请求。')
    dest = getattr(job, 'dest', None)
    responses = getattr(dest, 'inlined_responses', None) if dest else None
    if not responses:
        raise SystemExit('没有 inline 音频结果。若你提交的是文件/JSONL 任务，请按官方 Batch 文档读取目标文件。')
    folder = ROOT / 'outputs' / name.replace('/', '_')
    folder.mkdir(parents=True, exist_ok=True)
    written = 0
    for index, item in enumerate(responses, start=1):
        if getattr(item, 'error', None):
            print(f'{index}: 失败 {item.error}')
            continue
        response = getattr(item, 'response', None)
        pcm = b''.join(extract_pcm(response)) if response else b''
        if not pcm:
            print(f'{index}: 没有音频')
            continue
        path = folder / f'{index:02d}.wav'
        path.write_bytes(wav_bytes(pcm))
        written += 1
        print(path)
    if not written:
        raise SystemExit('没有写出任何 WAV。')
    print(f'共 {written} 个文件。请试听，不要把成功状态当成逐字完整。')


def cancel(name: str) -> None:
    client().batches.cancel(name=name)
    print(f'已请求取消 {name}')


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Gemini TTS Batch API 小规模 inline 示例')
    sub = parser.add_subparsers(dest='cmd', required=True)
    submit_p = sub.add_parser('submit', help='提交 examples/batch.json 这类 inline 任务')
    submit_p.add_argument('json_path')
    status_p = sub.add_parser('status', help='查询一次状态，不轮询')
    status_p.add_argument('name')
    download_p = sub.add_parser('download', help='仅在成功后下载 inline WAV')
    download_p.add_argument('name')
    cancel_p = sub.add_parser('cancel', help='取消尚未结束的任务')
    cancel_p.add_argument('name')
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == 'submit':
        submit(Path(args.json_path))
    elif args.cmd == 'status':
        status(args.name)
    elif args.cmd == 'download':
        download(args.name)
    else:
        cancel(args.name)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
