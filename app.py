"""Local web demo. Run: python -m uvicorn app:app --host 127.0.0.1 --port 8001."""
import base64
import json
import os
import re
import threading
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request as WebRequest
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from catalog import AGE_CONTROL, API_OUT_OF_DEMO, AUDIO_PROFILES, CHIRP_LOCALES, CLASSIC_PAGE_FAMILIES, CLASSIC_VOICES, COMPARE_CLASSIC, COMPARE_MODELS, COMPARE_PROVIDERS, EXAMPLES, FIT_GUIDE, MODEL_CARDS, MODELS, SSML_TAGS, TAGS, VOICE_PROFILES, VOICE_RULES, VOICES, WHY_CLASSIC, WORKSPACES
from samples import load_samples
from tts import Request, UserError, adc_available, audio_chunks, error_payload, genai_client, require_provider_auth, plan

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
SAMPLES = load_samples()
app = FastAPI(title='Gemini 声音实验室', description='Python SDK · 本地教学 Demo')
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['localhost', '127.0.0.1', '[::1]', 'testserver'])
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')
generation_lock = threading.Lock()


@app.middleware('http')
async def local_only(request: WebRequest, call_next):
    if request.method == 'POST':
        origin = request.headers.get('origin')
        if origin and origin != str(request.base_url).rstrip('/'):
            return JSONResponse({'detail': '请从本地 Demo 页面发起请求。'}, status_code=403)
        if request.headers.get('content-type', '').split(';')[0] != 'application/json':
            return JSONResponse({'detail': '需要 JSON 请求。'}, status_code=415)
        body = await request.body()
        if len(body) > 200000: return JSONResponse({'detail': '请求过大。'}, status_code=413)
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@app.exception_handler(RequestValidationError)
async def invalid_request(request, exc):
    return JSONResponse({'detail': '输入格式或长度不正确，请检查文本、角色及分段设置。'}, status_code=422)


@app.get('/')
def home(): return FileResponse(ROOT / 'static' / 'index.html')


@app.get('/api/catalog')
def catalog():
    return {'voices': VOICES, 'voice_profiles': VOICE_PROFILES, 'models': MODELS, 'model_cards': MODEL_CARDS,
            'examples': EXAMPLES, 'samples': SAMPLES, 'tags': TAGS, 'voice_rules': VOICE_RULES,
            'compare_providers': COMPARE_PROVIDERS, 'compare_models': COMPARE_MODELS, 'compare_classic': COMPARE_CLASSIC,
            'why_classic': WHY_CLASSIC, 'age_control': AGE_CONTROL, 'fit_guide': FIT_GUIDE,
            'api_out_of_demo': API_OUT_OF_DEMO, 'audio_profiles': AUDIO_PROFILES,
            'classic_voices': CLASSIC_VOICES, 'chirp_locales': CHIRP_LOCALES,
            'classic_page_families': CLASSIC_PAGE_FAMILIES,
            'workspaces': WORKSPACES, 'ssml_tags': SSML_TAGS,
            'checked': '2026-09-10',
            'default_provider': 'vertex',
            'key_configured': bool(os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')),
            'project_configured': bool(os.getenv('GOOGLE_CLOUD_PROJECT')),
            'adc_configured': adc_available(),
            'text_model': os.getenv('TEXT_MODEL', 'gemini-2.5-flash')}


@app.get('/api/doc/{name}')
def document(name: str):
    files = {'readme': 'README.md', 'guide': 'learning_guide.md', 'sources': 'docs/official_sources.md'}
    if name not in files: raise HTTPException(404)
    path = ROOT / files[name]
    if not path.is_file(): raise HTTPException(404)
    return {'text': path.read_text(encoding='utf-8')}


@app.post('/api/preview')
def preview(r: Request):
    try: return plan(r)
    except UserError as error: raise HTTPException(400, str(error)) from None


def event(data): return json.dumps(data, ensure_ascii=False) + '\n'


@app.post('/api/synthesize')
def synthesize(r: Request):
    try:
        p = plan(r)
        require_provider_auth(r.provider)
    except UserError as error: raise HTTPException(400, str(error)) from None

    def generate():
        if not generation_lock.acquire(blocking=False):
            yield event({'type': 'error', 'message': '已有生成任务运行中，请完成或停止后再试。'})
            return
        started = time.monotonic()
        first = None
        total = 0
        try:
            yield event({'type': 'start', 'segments': len(p['chunks']), 'format': r.format, 'rate': 24000, 'warnings': p.get('warnings') or []})
            for index, text in enumerate(p['chunks']):
                yield event({'type': 'segment', 'index': index + 1, 'total': len(p['chunks'])})
                for data in audio_chunks(r, text):
                    if first is None: first = time.monotonic() - started
                    total += len(data)
                    if total > 100_000_000: raise UserError('本 Demo 音频累计超过 100 MB，请缩短输入。')
                    yield event({'type': 'audio', 'data': base64.b64encode(data).decode()})
            if r.format == 'wav' and total % 2: raise UserError('PCM 数据不完整，请重新生成。')
            yield event({'type': 'done', 'seconds': round(time.monotonic() - started, 2), 'first_audio': round(first or 0, 2), 'duration': round(total / 48000, 2) if r.format == 'wav' else None, 'bytes': total})
        except Exception as error:
            payload = error_payload(error)
            print(f'[synthesize] {payload["error_type"]}: {error}', flush=True)
            yield event({'type': 'error', **payload})
        finally:
            generation_lock.release()
    return StreamingResponse(generate(), media_type='application/x-ndjson', headers={'X-Accel-Buffering': 'no'})


DRAFT_PACES = (
    '自然',
    '缓慢，留出思考的停顿',
    '轻快，保持吐字清晰',
    '逐渐加快，最后放慢',
)


class Draft(BaseModel):
    topic: str = Field(min_length=1, max_length=1000)
    model: str = Field(default='gemini-2.5-flash', max_length=100)
    dialogue: bool = False
    speaker: str = Field(default='Host', pattern='^[A-Za-z0-9]{1,30}$')
    speaker2: str = Field(default='Guest', pattern='^[A-Za-z0-9]{1,30}$')
    voice: str = Field(default='Kore', max_length=40)
    voice2: str = Field(default='Puck', max_length=40)


def _voice_brief(name: str) -> str:
    profile = next((item for item in VOICE_PROFILES if item['name'] == name), None)
    if not profile:
        return name
    return f"{profile['name']}（{profile['gender_zh']} · {profile['style_zh']}）"


def _voice_lock_phrase(name: str) -> str:
    profile = next((item for item in VOICE_PROFILES if item['name'] == name), None)
    if not profile:
        return '先写明说话人的成年声线，再写情绪'
    if profile['gender'] == 'female':
        return '成年女性，保持女声音高和声线'
    return '成年男性，保持男声音高和声线'


def draft_prompt(r: Draft) -> str:
    tags = '、'.join(tag for tag, _label in TAGS)
    paces = ' / '.join(DRAFT_PACES)
    if r.dialogue:
        layout = (
            f'text 必须是对话，每行以 {r.speaker}: 或 {r.speaker2}: 开头，两人均须至少一句。'
            f'角色 A 声音是 {_voice_brief(r.voice)}，角色 B 是 {_voice_brief(r.voice2)}。'
            f'style 里分别规定两人，并各自锁声线：{_voice_lock_phrase(r.voice)}；{_voice_lock_phrase(r.voice2)}。'
        )
    else:
        layout = (
            f'text 是单人旁白。当前预置声音是 {_voice_brief(r.voice)}。'
            f'style 必须先写「{_voice_lock_phrase(r.voice)}」，再写符合主题的情绪、对象和表演方式。'
        )
    return (
        '你在为 Google Gemini TTS 起草朗读稿。TTS 只朗读 text 里的台词；'
        '语气、口音、节奏、场景必须分开写到 style / pace / accent / scene，不要写进台词。\n'
        f'台词里必须使用英语方括号表演标签，从这些里选用：{tags}。'
        '至少使用 2 个不同标签，放在需要改演法的那一句开头，例如「[whispers] 我告诉你一个秘密。」'
        '不要写中文标签如 [低语]，不要把导演说明念出来。\n'
        f'{layout}\n'
        f'pace 必须恰好是下列之一：{paces}。\n'
        'accent 写成具体口音，中文主题用「标准普通话」。\n'
        'scene 写谁在什么环境对谁说话，要和主题一致。\n'
        '约 120–180 字。只返回 JSON 对象，不要标题、不要 Markdown。字段：text, style, pace, accent, scene。\n'
        f'主题：{r.topic.strip()}'
    )


def parse_draft(raw: str) -> dict:
    text = (raw or '').strip()
    if not text:
        raise UserError('写稿模型没有返回文字，请换一个可用的文本模型。')
    fence = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    blob = fence.group(1) if fence else text
    start, end = blob.find('{'), blob.rfind('}')
    if start == -1 or end <= start:
        raise UserError('写稿没有返回可解析的 JSON。请再试一次。')
    try:
        data = json.loads(blob[start:end + 1])
    except json.JSONDecodeError as error:
        raise UserError('写稿 JSON 无法解析，请再试一次。') from error
    if not isinstance(data, dict):
        raise UserError('写稿 JSON 格式不正确，请再试一次。')
    script = str(data.get('text') or '').strip()
    if not script:
        raise UserError('写稿没有台词。请再试一次。')
    pace = str(data.get('pace') or '自然').strip()
    if pace not in DRAFT_PACES:
        pace = next((item for item in DRAFT_PACES if item in pace or pace in item), '自然')
    return {
        'text': script,
        'style': str(data.get('style') or '').strip(),
        'pace': pace,
        'accent': str(data.get('accent') or '').strip(),
        'scene': str(data.get('scene') or '').strip(),
    }


@app.post('/api/draft')
def draft(r: Draft):
    if not r.topic.strip(): raise HTTPException(400, '请输入写稿主题。')
    if not generation_lock.acquire(blocking=False): raise HTTPException(409, '请先等待当前生成任务完成。')
    try:
        provider = 'vertex' if os.getenv('GOOGLE_CLOUD_PROJECT') else 'gemini'
        with genai_client(provider) as client:
            from google.genai import types
            result = client.models.generate_content(
                model=r.model,
                contents=draft_prompt(r),
                config=types.GenerateContentConfig(response_mime_type='application/json'),
            )
            return parse_draft(getattr(result, 'text', None) or '')
    except UserError as error: raise HTTPException(400, str(error)) from None
    except Exception as error: raise HTTPException(400, error_payload(error)) from None
    finally: generation_lock.release()


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app:app', host='127.0.0.1', port=int(os.getenv('DEMO_PORT', '8001')), reload=False)
