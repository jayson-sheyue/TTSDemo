"""Load one-click demo samples from sample_assets/. No credentials here."""
from __future__ import annotations

import json
from pathlib import Path

from catalog import CLASSIC_INDEX, VOICES, WORKSPACES

ENGINES = {item['id'] for item in WORKSPACES}

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'sample_assets'
REQUIRED = ('id', 'title', 'group', 'note', 'engine', 'config')


def load_samples() -> list[dict]:
    index = json.loads((ASSETS / 'index.json').read_text(encoding='utf-8'))
    samples = []
    for name in index['samples']:
        path = ASSETS / name
        data = json.loads(path.read_text(encoding='utf-8'))
        missing = [key for key in REQUIRED if key not in data]
        if missing:
            raise ValueError(f'{name} 缺少字段：{missing}')
        config = data['config']
        if not config.get('text'):
            raise ValueError(f'{name} 需要 text')
        if data['engine'] not in ENGINES:
            raise ValueError(f'{name} 的 engine 必须是 {sorted(ENGINES)} 之一')
        if data['engine'] == 'gemini' and not config.get('style'):
            raise ValueError(f'{name} 需要 style')
        if config.get('voice') not in VOICES and config.get('voice') not in CLASSIC_INDEX:
            raise ValueError(f'{name} 声音不在预置名单：{config.get("voice")}')
        data['file'] = name
        samples.append(data)
    return samples
