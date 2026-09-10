"""Local web demo. Run: python -m uvicorn app:app --host 127.0.0.1 --port 8001."""
import base64
import json
import os
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

from catalog import AGE_CONTROL, API_OUT_OF_DEMO, CHIRP_LOCALES, CLASSIC_PAGE_FAMILIES, CLASSIC_VOICES, COMPARE_CLASSIC, COMPARE_MODELS, COMPARE_PROVIDERS, EXAMPLES, FIT_GUIDE, MODEL_CARDS, MODELS, SSML_TAGS, TAGS, VOICE_PROFILES, VOICE_RULES, VOICES, WHY_CLASSIC, WORKSPACES
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
            'api_out_of_demo': API_OUT_OF_DEMO,
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


class Draft(BaseModel):
    topic: str = Field(min_length=1, max_length=1000)
    model: str = Field(default='gemini-2.5-flash', max_length=100)
    dialogue: bool = False
    speaker: str = Field(default='Host', pattern='^[A-Za-z0-9]{1,30}$')
    speaker2: str = Field(default='Guest', pattern='^[A-Za-z0-9]{1,30}$')


@app.post('/api/draft')
def draft(r: Draft):
    if not r.topic.strip(): raise HTTPException(400, '请输入写稿主题。')
    if not generation_lock.acquire(blocking=False): raise HTTPException(409, '请先等待当前生成任务完成。')
    try:
        layout = f'每行以 {r.speaker}: 或 {r.speaker2}: 开头，两人均须发言。' if r.dialogue else '单人旁白。'
        provider = 'vertex' if os.getenv('GOOGLE_CLOUD_PROJECT') else 'gemini'
        with genai_client(provider) as client:
            result = client.models.generate_content(model=r.model, contents=f'写一段约150字的中文朗读稿，只返回台词，不要标题和Markdown。{layout}\n主题：{r.topic}')
            if not result.text: raise UserError('写稿模型没有返回文字，请换一个可用的文本模型。')
            return {'text': result.text}
    except UserError as error: raise HTTPException(400, str(error)) from None
    except Exception as error: raise HTTPException(400, error_payload(error)) from None
    finally: generation_lock.release()


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app:app', host='127.0.0.1', port=int(os.getenv('DEMO_PORT', '8001')), reload=False)
