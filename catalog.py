"""Official model/voice snapshot, checked 2026-09-10. No credentials here.

Gender is the Cloud Gemini-TTS voice table (Male/Female), not an API field.
Age bands (child/adult/elder) are NOT official enums.
Gemini: style adjectives + prompt. Chirp: pick another speaker. WaveNet: pick another named voice; pitch is semitones, not age.
"""
from __future__ import annotations

import json
from pathlib import Path


def _voice(name, style_zh, style_en, gender, age_hint=''):
    return {
        'name': name, 'style_zh': style_zh, 'style_en': style_en,
        'gender': gender, 'gender_zh': '女声' if gender == 'female' else '男声',
        'age_hint': age_hint,
    }


VOICE_PROFILES = [
    _voice('Zephyr', '明亮', 'Bright', 'female'),
    _voice('Puck', '活泼', 'Upbeat', 'male'),
    _voice('Charon', '知性', 'Informative', 'male'),
    _voice('Kore', '坚定', 'Firm', 'female'),
    _voice('Fenrir', '兴奋', 'Excitable', 'male'),
    _voice('Leda', '年轻', 'Youthful', 'female', '官方形容词是 Youthful（年轻感），不是「少年声」档位。'),
    _voice('Orus', '坚定', 'Firm', 'male'),
    _voice('Aoede', '轻快', 'Breezy', 'female'),
    _voice('Callirrhoe', '随和', 'Easy-going', 'female'),
    _voice('Autonoe', '明亮', 'Bright', 'female'),
    _voice('Enceladus', '气声', 'Breathy', 'male'),
    _voice('Iapetus', '清晰', 'Clear', 'male'),
    _voice('Umbriel', '随和', 'Easy-going', 'male'),
    _voice('Algieba', '顺滑', 'Smooth', 'male'),
    _voice('Despina', '顺滑', 'Smooth', 'female'),
    _voice('Erinome', '清晰', 'Clear', 'female'),
    _voice('Algenib', '沙哑', 'Gravelly', 'male'),
    _voice('Rasalgethi', '知性', 'Informative', 'male'),
    _voice('Laomedeia', '活泼', 'Upbeat', 'female'),
    _voice('Achernar', '柔软', 'Soft', 'female'),
    _voice('Alnilam', '坚定', 'Firm', 'male'),
    _voice('Schedar', '平稳', 'Even', 'male'),
    _voice('Gacrux', '成熟', 'Mature', 'female', '官方形容词是 Mature（成熟感），不是「老年声」档位。'),
    _voice('Pulcherrima', '直率', 'Forward', 'female'),
    _voice('Achird', '亲切', 'Friendly', 'male'),
    _voice('Zubenelgenubi', '随意', 'Casual', 'male'),
    _voice('Vindemiatrix', '温柔', 'Gentle', 'female'),
    _voice('Sadachbia', '生动', 'Lively', 'male'),
    _voice('Sadaltager', '博学', 'Knowledgeable', 'male'),
    _voice('Sulafat', '温暖', 'Warm', 'female'),
]
VOICES = {item['name']: item['style_zh'] for item in VOICE_PROFILES}

TAGS = [
    ('[whispers]', '轻声低语'), ('[laughs]', '笑声'), ('[sighs]', '叹气'), ('[gasp]', '倒吸气'),
    ('[shouting]', '喊叫'), ('[excited]', '兴奋'), ('[tired]', '疲惫'), ('[very slow]', '很慢'),
]
MODELS = {
    'gemini': ['gemini-3.1-flash-tts-preview', 'gemini-2.5-flash-preview-tts', 'gemini-2.5-pro-preview-tts'],
    'vertex': ['gemini-3.1-flash-tts-preview', 'gemini-2.5-flash-tts', 'gemini-2.5-pro-tts', 'gemini-2.5-flash-lite-preview-tts'],
    'cloud': ['gemini-3.1-flash-tts-preview', 'gemini-2.5-flash-tts', 'gemini-2.5-pro-tts', 'gemini-2.5-flash-lite-preview-tts'],
    'classic': ['chirp3-hd', 'wavenet', 'neural2', 'standard', 'studio'],
}
MODEL_CARDS = {
    'gemini-3.1-flash-tts-preview': '3.1 Flash TTS Preview：标签、自然度、多语言更好；三入口都可流式（Cloud 3.1 主要在 global）。单人+双人。',
    'gemini-2.5-flash-preview-tts': '2.5 Flash Preview TTS（仅 Gemini API 名）：偏快、偏省。Gemini API 不能流式。单人+双人。',
    'gemini-2.5-pro-preview-tts': '2.5 Pro Preview TTS（仅 Gemini API 名）：偏质量，适合播客/有声书。Gemini API 不能流式。单人+双人。',
    'gemini-2.5-flash-tts': '2.5 Flash TTS（Cloud / Vertex 名）：可流式（视区域）。单人+双人。不要把带 preview 的 Gemini API 名填到这里。',
    'gemini-2.5-pro-tts': '2.5 Pro TTS（Cloud / Vertex 名）：偏质量。可流式（视区域）。单人+双人。',
    'gemini-2.5-flash-lite-preview-tts': '2.5 Flash-Lite Preview：只要单人。仅 Cloud / Vertex。',
    'chirp3-hd': 'Chirp 3: HD：传统 Cloud TTS，不是 Gemini-TTS。声音名是 locale-Chirp3-HD-Kore。可流式；SSML 仅非流式且标签是子集。',
    'wavenet': 'WaveNet：传统 Cloud TTS。用 SSML 控停顿/语速/读法，不是 Gemini 提示词。不能流式。',
    'neural2': 'Neural2：传统 Cloud TTS，支持 SSML。不能流式。',
    'standard': 'Standard：传统 Cloud TTS 基础声音，支持 SSML。不能流式。',
    'studio': 'Studio：传统 Cloud TTS，偏有声书；本 Demo 收录英语 Studio。支持 SSML。不能流式。',
}
COMPARE_PROVIDERS = [
    ['', 'Gemini API', 'Vertex AI', 'Cloud Text-to-Speech'],
    ['身份', 'API Key', 'ADC + Cloud 项目（本 Demo 默认）', 'ADC + Cloud 项目'],
    ['Python 包', 'google-genai', 'google-genai', 'google-cloud-texttospeech'],
    ['30 预置声音', '相同名单', '相同名单', '相同名单，另标 Male/Female'],
    ['男/女分类', '无独立参数；靠选声+提示词', '同左', '文档声音表有 Male/Female，仍不是请求字段'],
    ['少年/老年档', '都不提供枚举；用提示词', '同左', '同左'],
    ['音频标签', '3.1 更适合；自定义英语标签可试', '同左', '同左'],
    ['流式', '仅 3.1', '2.5 / 3.1（视区域）', '2.5 / 3.1（视区域）；官方示例偏单人'],
    ['下载格式', 'PCM → 本 Demo 打成 WAV', '同左', 'WAV / MP3 / OGG（MP3·OGG 需非流式）'],
    ['语言代码', '可空；短码如 cmn、en', '按 Cloud/Vertex 文档', '必填 locale，如 cmn-CN'],
    ['2.5 Flash / Pro 模型 ID', 'gemini-2.5-flash-preview-tts', 'gemini-2.5-flash-tts（无 preview）', '同 Vertex'],
    ['3.1 模型 ID', 'gemini-3.1-flash-tts-preview（三入口同名）', '同左', '同左'],
    ['Flash-Lite', '无', '有，仅单人', '有，仅单人'],
    ['双人对话（最多 2 人）', '能：自由文本 + 两个 speaker', '能：同左', '能：自由文本双人'],
    ['结构化双人 markup', '无此字段', '无此字段', '有 multi_speaker_markup，仅非流式'],
]
COMPARE_CLASSIC = [
    ['', 'Gemini-TTS', 'Chirp 3: HD', 'WaveNet / Neural2 / Standard / Studio'],
    ['它是什么', '专用语音模型，按提示词表演', 'Cloud TTS 传统高保真声', 'Cloud TTS 传统合成声'],
    ['调用', 'google-genai 或 Cloud Gemini 模型', 'text:synthesize，声音名带 Chirp3-HD', 'text:synthesize，Wavenet / Neural2 等'],
    ['声音名', 'Kore / Puck（30 个）', 'cmn-CN-Chirp3-HD-Kore（同一批名字）', 'cmn-CN-Wavenet-A 这类'],
    ['自然语言提示词', '支持，且影响表演', '不按 Gemini 提示词演戏', '不支持；用 SSML'],
    ['SSML', '不走 SSML', '同步请求有标签子集；流式不能 SSML', '支持（官方 SSML 指南）'],
    ['日期 / 电话 / 验证码', '写进提示词，不保证读法', 'say-as（同步）', 'say-as'],
    ['毫秒级停顿', '标签或「停一下」，不保证时长', 'break time（同步）', 'break time'],
    ['指定发音', '提示词', 'phoneme / sub（同步）', 'phoneme / sub'],
    ['按字面朗读', '会演戏，可能发挥或漏字', '读 text / SSML', '读 text / SSML'],
    ['计费单位', 'Gemini-TTS 按 token（输入+音频）', 'Cloud TTS 按字符', '同左；Standard/WaveNet 有免费额度'],
    ['年龄档', '无枚举；提示词 + 换 Leda/Gacrux', '无枚举；只能换说话人，提示词无效', '无枚举；换 A/B/C/D 等训练声。pitch 是音高不是年龄'],
    ['ssmlGender', '无此请求字段', '一般靠声音名', '可选；本 Demo 仍以声音名为准'],
    ['双人', '最多两个 speaker', '单人（SSML <voice> 可换声，本 Demo 不做）', '单人'],
    ['流式', '视模型和入口', '能', '不能'],
    ['本 Demo 入口', 'Gemini-TTS 独立页（Vertex / Cloud Gemini / Gemini API）', 'Chirp 3 HD 独立页', 'WaveNet / Neural2 / Standard / Studio 各自一页'],
]
COMPARE_MODELS = [
    ['', '3.1 Flash TTS', '2.5 Flash TTS', '2.5 Pro TTS', '2.5 Flash-Lite'],
    ['定位', '新、可控、标签', '快、省', '质量、长内容', '更省、单人'],
    ['单人', '能', '能', '能', '能'],
    ['双人', '能', '能', '能', '不能'],
    ['Gemini API 流式', '能', '不能', '不能', '无此入口'],
    ['Vertex / Cloud 流式', '能（3.1 多在 global）', '能（视区域）', '能（视区域）', '能（视区域）'],
    ['输入/输出 token（模型页）', '8192 / 16384', '8192 / 16384', '8192 / 16384', '8192 / 16384'],
]
WHY_CLASSIC = [
    ['你会选传统，如果…', 'Gemini-TTS', 'Chirp / WaveNet / Neural2 / Standard / Studio'],
    ['日期、电话、验证码必须读对', '只能写进提示词，每次可能不一样', 'SSML <say-as>，读法写在标记里'],
    ['停顿必须是 400 毫秒', '[pause] 或「停一下」，不保证时长', '<break time="400ms"/>'],
    ['某个词必须某种发音', '提示词碰运气', '<phoneme> / <sub alias>'],
    ['IVR、通知、无障碍：不要演戏', '模型会表演，可能漏字或发挥', '按 text / SSML 合成，提示词不会发送'],
    ['账单要按字符、或要用 WaveNet 免费额度', 'Gemini-TTS 按 token 另计价，官方表无这项免费额度', 'Cloud TTS 字符价目；Standard/WaveNet 有免费额度。Studio/Chirp 是另一档，以定价页为准'],
    ['只要某语言的专用声，而不是 30 个跨语言短名', 'Kore / Puck 一套名字跨语言', 'cmn-CN-Wavenet-A 这类按语言训练的声（Chirp 仍是短名+locale）'],
    ['Chirp 要流式高保真，又不走 Gemini 3.1', '视入口和模型', 'Chirp 可流式；SSML 与流式不能同时开'],
]
VOICE_RULES = [
    ['分类', '官方是否原生支持', '你在 Demo 里怎么做'],
    ['预置声音 30 个', '支持。请求字段是 voice_name', '下拉框选择 Kore / Puck 等'],
    ['女声 / 男声', '部分支持：Cloud 声音表标注 Male/Female；API 没有 gender 参数', '用筛选看女声/男声；仍是选一个名字'],
    ['少年 / 壮年 / 老年', '不支持。没有 age 枚举', '选接近的风格（Leda 年轻感、Gacrux 成熟感），把年龄写进语气'],
    ['提示词与声线冲突', '不保证。官方要求人设和声音协调', '女声要凶，写成「成年女性，保持女声线」；不要只写「黑社会头目」'],
    ['自定义音色 / 克隆', '不支持', '做不到'],
    ['行内标签 [shouting]', '支持，无封闭名单；3.1 更稳；建议英语标签', '写在台词里，效果要试听'],
    ['Chirp / WaveNet / SSML', '那是传统 Cloud TTS，不是 Gemini-TTS', '打开对应独立页，不要留在 Gemini-TTS 页'],
]
AGE_CONTROL = [
    ['', 'Gemini-TTS', 'Chirp 3: HD', 'WaveNet / Neural2 / Standard / Studio'],
    ['有没有年龄 API', '没有 age 枚举', '没有', '没有。官方声音表只有 Language / Voice name / SSML Gender'],
    ['年轻 / 年长怎么来', '1）换声：Leda=Youthful，Gacrux=Mature（风格词，不是少年/老年档）2）把年龄写进提示词', '只能换说话人。同一套 30 个短名。提示词不会演戏，写「听起来像长者」无效', '换声音名。cmn-CN-Wavenet-A/B/C/D 是四个训练好的说话人，不是年龄旋钮'],
    ['性别怎么来', '选 voice_name；Cloud 表有 Male/Female，请求无 gender 字段', '声音表 Name+Gender；请求用 locale-Chirp3-HD-短名', '声音表 SSML Gender。未指定 name 时可用 ssmlGender 作偏好'],
    ['AudioConfig.pitch', '无此字段', '声音类型总览写明不支持 pitch / speakingRate。本 Demo 不发送音高', '可选 -20～+20 半音。提高音高可能「听起来更尖」，官方不当作童声档'],
    ['SSML prosody pitch', '不走 SSML', 'Chirp 专题页有子集（同步）；与类型总览「不支持 SSML」有冲突，以试听和端点为准', '支持 <prosody pitch>，仍是音高不是年龄'],
]
FIT_GUIDE = [
    ['你的业务更像…', '优先试', '不要先试', '听哪条样例'],
    ['播客、有声书、广告口播、要笑声/低语/双人', 'Gemini-TTS（3.1 或 2.5 Pro）', 'Standard / 纯 IVR 声', 'Gemini：有声书、品牌广告、双人小播客'],
    ['智能客服、对话式助手、要流式高保真、不要演戏', 'Chirp 3 HD（可流式）', 'Gemini 提示词（会发挥）', 'Chirp：对话助手；对照 Gemini 客服电话'],
    ['IVR、验证码、日期电话必须读死、400ms 停顿', 'WaveNet 或 Standard + SSML', 'Gemini（只能写进提示词）', 'WaveNet「独有 · 验证码与日期」'],
    ['英语通知 / 客服留言，要 Neural 音质 + SSML', 'Neural2', '普通话 Neural2（官方表无 cmn-CN Neural2）', 'Neural2「行业 · 英语客服」'],
    ['成本敏感的通知、有免费额度', 'Standard + SSML', 'Studio / Chirp / Gemini token 价', 'Standard「行业 · 低成本通知」'],
    ['英语有声书、广播腔、写死句间停顿', 'Studio + SSML break', '用 Gemini 提示词「停 400ms」', 'Studio「写死的句间停顿」'],
]
API_OUT_OF_DEMO = [
    ['能力', '业务价值', '为什么网页 Demo 不做', '客户接入文档'],
    [
        'Chirp 3 Instant Custom Voice（克隆音色）',
        '用几秒参考音做出「听起来像某个人」的助手声：品牌代言、对内培训角色、熟人声线',
        '要上传参考录音并拿到 cloning key。不能用预置 30 个短名冒充。教学不便采集客户声纹。',
        'Chirp 3 Instant Custom Voice\nhttps://docs.cloud.google.com/text-to-speech/docs/chirp3-instant-custom-voice',
    ],
    [
        'Custom Voice（AutoML 定制声）',
        '用你们自己的播音员语料训练一把专属声，客服/有声书品牌声线长期复用',
        '要先在 Cloud 训练模型，请求里填 customVoice 资源名。没有现成模型可当场点。',
        'Custom Voice\nhttps://cloud.google.com/text-to-speech/docs/custom-voice',
    ],
    [
        'Long audio（异步写 GCS）',
        '有声书整章、超长通知一次合成，结果进云存储，不必浏览器下载大文件',
        '要 GCS 桶并轮询长时间操作。本页长文是应用层分段后多次 synthesize，方便当场试听。',
        'Long audio synthesis\nhttps://cloud.google.com/text-to-speech/docs/create-audio-text-long-audio-synthesis',
    ],
    [
        '双向流式 Bidirectional streaming',
        '边生成稿边往外推字，先听到开头；适合助手一边想一边说',
        '浏览器一次提交整段。Chirp 页已做单向流式（整段文字 → 边收边播）。双向要保持发送文本块的长连接。',
        '流式合成\nhttps://cloud.google.com/text-to-speech/docs/create-audio-text-streaming',
    ],
    [
        'Studio 实验性双人组',
        '有声书里两个叙述者共用 Studio 音质，比 Gemini 双人更「播音」',
        '官方仍是 Preview。本页 Studio 只接单人叙述声。要演戏双人请用 Gemini-TTS 页。',
        '声音类型 · Studio\nhttps://docs.cloud.google.com/text-to-speech/docs/voice-types',
    ],
    [
        'voices.list 在线拉全表',
        '生产环境按账号和区域探测此刻能用的声音，避免文档快照过期',
        '工作台用 2026-09-10 文档快照，保证离线对照稳定。上线请以 voices.list 为准。',
        '列出声音\nhttps://cloud.google.com/text-to-speech/docs/list-voices',
    ],
]


def _doc(title, url, why):
    return {'title': title, 'url': url, 'why': why}


DOC_VOICES = _doc('支持的声音与语言（全表）', 'https://cloud.google.com/text-to-speech/docs/voices', '本 Demo 用该表 2026-09-10 快照。WaveNet/Neural2/Standard/Studio 按语言筛选全表；Chirp 是 30 短名 × 全部 locale。')
DOC_SYNTH = _doc('text.synthesize REST', 'https://docs.cloud.google.com/text-to-speech/docs/reference/rest/v1/text/synthesize', '接入系统：input、voice、audioConfig。')
DOC_CREATE = _doc('创建音频（官方示例）', 'https://cloud.google.com/text-to-speech/docs/create-audio', '含按 name 或 ssmlGender 选声。')
DOC_PYTHON_TTS = _doc('Cloud TTS Python 客户端', 'https://docs.cloud.google.com/python/docs/reference/texttospeech/latest', 'google-cloud-texttospeech。')
DOC_SSML = _doc('SSML 指南', 'https://cloud.google.com/text-to-speech/docs/ssml', 'break / say-as / phoneme / prosody / voice / lang。')
DOC_AUDIOCFG = _doc('AudioConfig', 'https://cloud.google.com/text-to-speech/docs/reference/rest/v1/AudioConfig', 'speakingRate、pitch、编码、effectsProfileId。')
DOC_PRICING_CLOUD = _doc('Cloud TTS 定价', 'https://cloud.google.com/text-to-speech/pricing', '按字符。Standard/WaveNet 有免费额度；Studio/Chirp 另档。')
DOC_QUOTAS = _doc('Cloud TTS 配额', 'https://docs.cloud.google.com/text-to-speech/quotas', '频率、并发、系统限制。')
CLASSIC_DOCS = [DOC_SYNTH, DOC_CREATE, DOC_PYTHON_TTS, DOC_SSML, DOC_AUDIOCFG, DOC_VOICES, DOC_PRICING_CLOUD, DOC_QUOTAS]



def _classic(name, family, language, gender, style_zh, language_label='', tier='Premium'):
    return {
        'name': name, 'family': family, 'language': language, 'gender': gender,
        'gender_zh': '女声' if gender == 'female' else ('男声' if gender == 'male' else '中性'),
        'style_zh': style_zh, 'style_en': family,
        'language_label': language_label or language, 'tier': tier,
    }


def _load_cloud_voices():
    path = Path(__file__).resolve().parent / 'voice_assets' / 'cloud_voices.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    voices = []
    for item in data['voices']:
        voices.append(_classic(
            item['name'], item['family'], item['language'], item['gender'],
            item.get('style_zh') or item.get('language_label') or item['language'],
            item.get('language_label') or item['language'], item.get('tier') or 'Premium',
        ))
    return voices, data.get('chirp_locales') or [], data.get('checked') or '2026-09-10'


CLASSIC_VOICES, CHIRP_LOCALES, VOICES_CHECKED = _load_cloud_voices()
CLASSIC_INDEX = {item['name']: item for item in CLASSIC_VOICES}
CLASSIC_PAGE_FAMILIES = {
    'wavenet': ('wavenet',),
    'neural2': ('neural2', 'news', 'polyglot', 'casual', 'chirp-hd'),
    'standard': ('standard',),
    'studio': ('studio',),
}
CLASSIC_PACE = {
    '自然': 1.0,
    '缓慢，留出思考的停顿': 0.8,
    '轻快，保持吐字清晰': 1.15,
    '逐渐加快，最后放慢': 1.0,
}
AUDIO_PROFILES = [
    ('', '不指定 · 默认扬声器'),
    ('headphone-class-device', '耳机'),
    ('handset-class-device', '手机听筒'),
    ('telephony-class-application', '电话 / IVR'),
    ('small-bluetooth-speaker-class-device', '小型蓝牙音箱'),
    ('medium-bluetooth-speaker-class-device', '中型蓝牙音箱'),
    ('large-home-entertainment-class-device', '客厅音箱'),
    ('large-automotive-class-device', '车载'),
    ('wearable-class-device', '可穿戴'),
]
SSML_TAGS = {
    'chirp3-hd': [
        ('<break time="400ms"/>', '停顿 0.4s'),
        ('<say-as interpret-as="characters">', '逐字读'),
        ('<sub alias="World Wide Web">WWW</sub>', '替换读法'),
        ('<phoneme alphabet="ipa" ph="ˌmænɪˈtoʊbə">manitoba</phoneme>', 'IPA 发音'),
        ('<prosody rate="slow">', '变慢'),
        ('<voice name="en-US-Chirp3-HD-Kore">', '换英语 Chirp'),
        ('<voice name="ja-JP-Chirp3-HD-Kore">', '换日语 Chirp'),
    ],
    'wavenet': [
        ('<break time="400ms"/>', '停顿 0.4s'),
        ('<say-as interpret-as="characters">', '逐字读'),
        ('<say-as interpret-as="date" format="ymd">', '读日期'),
        ('<say-as interpret-as="telephone">', '读电话'),
        ('<phoneme alphabet="ipa" ph="həˈləʊ">', 'IPA 发音'),
        ('<prosody rate="slow">', '变慢'),
        ('<emphasis level="strong">', '强调'),
        ('<lang xml:lang="en-US">', '同声换英语（尽力）'),
        ('<voice name="en-US-Wavenet-D">', '换英语 WaveNet'),
        ('<voice name="ja-JP-Wavenet-A">', '换日语 WaveNet'),
    ],
    'neural2': [
        ('<break time="400ms"/>', '停顿 0.4s'),
        ('<say-as interpret-as="date" format="ymd">', '读日期'),
        ('<say-as interpret-as="telephone">', '读电话'),
        ('<say-as interpret-as="characters">', '逐字读'),
        ('<prosody rate="slow">', '变慢'),
        ('<voice name="cmn-CN-Standard-A">', '换普通话 Standard'),
        ('<voice name="ja-JP-Standard-A">', '换日语 Standard'),
    ],
    'standard': [
        ('<break time="400ms"/>', '停顿 0.4s'),
        ('<say-as interpret-as="characters">', '逐字读'),
        ('<say-as interpret-as="date" format="ymd">', '读日期'),
        ('<say-as interpret-as="telephone">', '读电话'),
        ('<prosody rate="slow">', '变慢'),
        ('<voice name="en-US-Standard-C">', '换英语 Standard'),
        ('<voice name="ja-JP-Standard-A">', '换日语 Standard'),
    ],
    'studio': [
        ('<break time="400ms"/>', '停顿 0.4s'),
        ('<break time="800ms"/>', '停顿 0.8s'),
        ('<prosody rate="slow">', '变慢'),
        ('<say-as interpret-as="date" format="ymd">', '读日期'),
        ('<voice name="cmn-CN-Standard-A">', '换普通话 Standard'),
        ('<voice name="ja-JP-Standard-A">', '换日语 Standard'),
    ],
    'ssml': [
        ('<break time="400ms"/>', '停顿 0.4s'),
        ('<say-as interpret-as="characters">', '逐字读'),
        ('<prosody rate="slow">', '变慢'),
        ('<emphasis level="strong">', '强调'),
        ('<sub alias="替代读法">', '替换读法'),
    ],
}
WORKSPACES = [
    {
        'id': 'gemini', 'nav': 'Gemini-TTS', 'family': 'gemini',
        'eyebrow': 'GEMINI TTS', 'title': '用提示词，给声音演戏。',
        'lead': '自然语言提示、音频标签、双人对话。要毫秒停顿、日期电话读死，请到传统 Cloud 各页。',
        'provider': 'vertex', 'model': 'gemini-3.1-flash-tts-preview',
        'features': ['dialogue', 'style', 'tags', 'draft', 'stream', 'chunk', 'structured', 'voice_lock'],
        'advantages': ['提示词演戏、音频标签、双人对话是这一页的独有能力。日期/电话/400ms 停顿请到 WaveNet 或 Chirp 页用 SSML。'],
        'age_note': '年龄靠提示词，外加换声：Leda=Youthful，Gacrux=Mature。没有少年/壮年/老年档。',
        'fit': [
            {'title': '适合', 'body': '播客、有声书、广告口播、教育讲解、要笑声/低语、最多两人对话。'},
            {'title': '不适合', 'body': '验证码必须逐字、日期电话读死、400ms 停顿。那些去 WaveNet。'},
        ],
        'coverage': '音色：官方 30 个预置短名，本页全部可下拉。另有 3.1 / 2.5 Flash / 2.5 Pro（Gemini API 名带 preview）；Flash-Lite 仅 Vertex/Cloud 且仅单人。',
        'surface': [
            '单人 / 双人（最多 2）', 'voice_name × 30', '提示词控风格', '行内音频标签', '语言可空（Vertex/Gemini API）',
            '流式（Gemini API 仅 3.1）', 'Cloud 结构化 dual markup', 'WAV；Cloud 非流式可 MP3/OGG',
        ],
        'docs': [
            _doc('Gemini API 语音生成总指南', 'https://ai.google.dev/gemini-api/docs/speech-generation', '测通后接入：单人、双人、声音、标签、流式。'),
            _doc('GenerateContent 语音指南', 'https://ai.google.dev/gemini-api/docs/generate-content/speech-generation', 'Legacy 路径的 speech_config。'),
            _doc('3.1 Flash TTS 模型页', 'https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-tts-preview', '模型 ID 三入口同名，都带 preview。'),
            _doc('Cloud / Vertex Gemini-TTS', 'https://docs.cloud.google.com/text-to-speech/docs/gemini-tts', '企业 ADC、区域、结构化双人、编码。'),
            _doc('Gen AI Python SDK', 'https://googleapis.github.io/python-genai/', 'google-genai。本 Demo 默认 Vertex+ADC。'),
            _doc('官方 TTS Cookbook', 'https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_TTS.ipynb', '可运行 notebook。'),
            _doc('Gemini API 定价', 'https://ai.google.dev/gemini-api/docs/pricing', '按 token。不要套 Cloud 字符价。'),
            _doc('Cloud Gemini 声音表', 'https://docs.cloud.google.com/text-to-speech/docs/gemini-tts#voice-options', '30 名、Male/Female、Youthful/Mature 等风格词。'),
        ],
    },
    {
        'id': 'chirp3-hd', 'nav': 'Chirp 3 HD', 'family': 'classic',
        'eyebrow': 'CLOUD TTS · CHIRP 3 HD', 'title': '高保真，还能把读法写死。',
        'lead': '相对 Gemini：同步 SSML 可逐字、替换读法、IPA；可流式（不要同时开 SSML）。提示词不会发送。年龄只能换说话人，不能演。',
        'provider': 'classic', 'model': 'chirp3-hd',
        'features': ['ssml', 'stream', 'chunk', 'rate', 'language'],
        'advantages': [
            'SSML 子集把验证码、缩写、IPA 写成标记，Gemini 只能写进提示词。',
            '可流式高保真，不必走 Gemini 3.1。SSML 与流式不能同时开。',
            '按字面合成，适合播报；不会把导演阐述念出来。',
        ],
        'age_note': 'Chirp 没有年龄 API，提示词也不会演戏。年轻/成熟 = 换短名（Leda / Gacrux）。声音类型总览写明不支持 AudioConfig.pitch。',
        'fit': [
            {'title': '适合', 'body': '对话式助手、虚拟客服、要流式低延迟高保真、不要模型发挥。官方定位 Conversational Agents。'},
            {'title': '不适合', 'body': '靠提示词改变年龄或情绪；完整 SSML 日期电话（子集，且不能与流式同开）。'},
        ],
        'coverage': '音色：与 Gemini 相同的 30 个短名 × 声音表里全部 Chirp 3 HD locale（当前快照 52 种）。换语言下拉即可测。Instant Custom Voice 不调用。',
        'surface': [
            '单人 text:synthesize', '30 短名 × locale', '同步 SSML 子集', '单向流式 PCM', '自定义发音 IPA/X-SAMPA（专题页）',
            '不发送 pitch（类型总览）', '不计 Gemini 提示词',
        ],
        'docs': [
            _doc('Chirp 3: HD', 'https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd', '声音名格式、流式、SSML 子集、HD 语速/停顿/发音控件。'),
            _doc('声音类型总览', 'https://docs.cloud.google.com/text-to-speech/docs/voice-types', '定位对话式代理；写明不支持 SSML / pitch / speakingRate（与专题页有冲突，接入前以端点为准）。'),
            _doc('Chirp 3 Instant Custom Voice', 'https://docs.cloud.google.com/text-to-speech/docs/chirp3-instant-custom-voice', '克隆音色。本 Demo 不调用。'),
        ] + CLASSIC_DOCS,
    },
    {
        'id': 'wavenet', 'nav': 'WaveNet', 'family': 'classic',
        'eyebrow': 'CLOUD TTS · WAVENET', 'title': '日期和验证码，SSML 说了算。',
        'lead': '相对 Gemini：<say-as> 读日期/电话/逐字，<break> 可写 400ms。年龄靠换 A/B/C/D，音高 pitch 不是年龄档。',
        'provider': 'classic', 'model': 'wavenet',
        'features': ['ssml', 'chunk', 'rate', 'language', 'format', 'pitch', 'audio_profile'],
        'advantages': [
            '官方 SSML：日期、电话、逐字、IPA、强调。Gemini-TTS 不走 SSML。',
            'speaking_rate / pitch 是请求数字，不是「读慢一点」「听起来年轻」这种提示词。',
            '按语言训练的专用声。本页是声音全表快照，用语言下拉筛选，不是只放中英日。',
        ],
        'age_note': '没有年龄档。换 cmn-CN-Wavenet-A 与 D 是换两个女训练声。pitch 只改变半音，官方不当作童声/老人声。',
        'fit': [
            {'title': '适合', 'body': 'IVR、通知、无障碍朗读、验证码/日期/电话必须稳定。官方定位 general purpose。'},
            {'title': '不适合', 'body': '演戏、双人、音频标签；也不要指望把 A 提示成儿童。'},
        ],
        'coverage': 'WaveNet 官方表当前快照全部可测，按语言筛选。普通话仍是 A–D 四人。',
        'surface': [
            '单人 text:synthesize', 'SSML 全指南标签（视声音）', 'speakingRate', 'pitch ±20 半音', 'effectsProfileId', 'volumeGainDb', 'WAV/MP3/OGG',
            '不可流式', 'ssmlGender 可选（本 Demo 用 name）',
        ],
        'docs': CLASSIC_DOCS,
    },
    {
        'id': 'neural2', 'nav': 'Neural2', 'family': 'classic',
        'eyebrow': 'CLOUD TTS · NEURAL2', 'title': '英语通知：电话和日期可读死。',
        'lead': '相对 Gemini：英语 Neural2 + SSML say-as。官方普通话表没有 Neural2。年龄同样只能换说话人。',
        'provider': 'classic', 'model': 'neural2',
        'features': ['ssml', 'chunk', 'rate', 'language', 'format', 'pitch', 'audio_profile'],
        'advantages': [
            '英语日期、电话、拼写可用 <say-as> 写成契约，不用提示词碰运气。',
            'en-US Neural2 官方全套可下拉；其他 locale 换语言即可。News / Polyglot / Casual / 旧版 Chirp HD 也放在本页。',
        ],
        'age_note': '无年龄 API。换 Neural2-C 与 H 是换女声说话人。pitch 是音高。',
        'fit': [
            {'title': '适合', 'body': '英语客服留言、系统通知、要 Neural 音质 + SSML。官方定位 general purpose。'},
            {'title': '不适合', 'body': '普通话（请用 WaveNet/Chirp/Gemini）；演戏与双人。'},
        ],
        'coverage': 'Neural2 全表按语言筛选。官方无 cmn-CN Neural2。同页还可测 News、Polyglot、Casual、旧版 Chirp HD。',
        'surface': [
            '单人 text:synthesize', 'SSML', 'speakingRate / pitch', 'effectsProfileId / volumeGainDb', 'WAV/MP3/OGG', '不可流式',
        ],
        'docs': CLASSIC_DOCS,
    },
    {
        'id': 'standard', 'nav': 'Standard', 'family': 'classic',
        'eyebrow': 'CLOUD TTS · STANDARD', 'title': '基础声 + SSML，适合对照成本。',
        'lead': '相对 Gemini：同样能 SSML 逐字/日期；官方价目里 Standard 是字符计费且有免费额度。换声控年龄，不能演。',
        'provider': 'classic', 'model': 'standard',
        'features': ['ssml', 'chunk', 'rate', 'language', 'format', 'pitch', 'audio_profile'],
        'advantages': [
            'IVR 验证码、日期可用 SSML 读死。',
            '普通话官方 Standard-A–D 都在；其他语言换下拉。字符计费 + 官方免费额度。',
        ],
        'age_note': '无年龄 API。A/D 是两把普通话女声。pitch 可试，仍不是童声档。',
        'fit': [
            {'title': '适合', 'body': '成本敏感的通知、IVR 对照、有免费额度的试点。官方定位 cost efficient。'},
            {'title': '不适合', 'body': '品牌口播、有声书质感（请 Studio/Gemini）；不要把它当「便宜的 Chirp」。'},
        ],
        'coverage': 'Standard 官方表当前快照全部可测，按语言筛选。',
        'surface': [
            '单人 text:synthesize', 'SSML', 'speakingRate / pitch', 'effectsProfileId / volumeGainDb', 'WAV/MP3/OGG', '不可流式', '价目有免费额度',
        ],
        'docs': CLASSIC_DOCS,
    },
    {
        'id': 'studio', 'nav': 'Studio', 'family': 'classic',
        'eyebrow': 'CLOUD TTS · STUDIO', 'title': '有声书节奏，用 break 写死。',
        'lead': '相对 Gemini：句间停顿可写成 400ms/800ms。Studio 是高档字符价。无普通话 Studio。',
        'provider': 'classic', 'model': 'studio',
        'features': ['ssml', 'chunk', 'rate', 'language', 'format', 'pitch', 'audio_profile'],
        'advantages': [
            'SSML break / prosody 把章节停顿写成标记，而不是「稍微停一下」。',
            '声音全表中的 Studio 单人叙述声全部可下拉，按语言筛选。无普通话 Studio。',
        ],
        'age_note': '无年龄 API。换 Studio-O / Q 是换说话人。提示词无效。',
        'fit': [
            {'title': '适合', 'body': '英语等有声书、广播叙述、要写死句间停顿。官方定位 Media: Narration。'},
            {'title': '不适合', 'body': '普通话；便宜 IVR（Studio 价高）；实验性 Studio 双人组本页不合成。'},
        ],
        'coverage': 'Studio 单人声全表可测。无 cmn-CN Studio。实验性 two-speaker Studio 未接入。',
        'surface': [
            '单人 text:synthesize', 'SSML（部分标签官方排除）', 'speakingRate / pitch', 'effectsProfileId / volumeGainDb', 'WAV/MP3/OGG', '不可流式',
        ],
        'docs': CLASSIC_DOCS + [
            _doc('声音类型 · Studio', 'https://docs.cloud.google.com/text-to-speech/docs/voice-types', '叙述 / 实验性双人组说明。'),
        ],
    },
]
EXAMPLES = [
    {'title': '第一段中文', 'mode': 'single', 'voice': 'Kore', 'text': '你好，欢迎来到声音实验室。把文字交给 Gemini，让你的想法被听见。', 'style': '温暖、自然，像在向一位新朋友介绍自己。'},
    {'title': '女声 · 坚定', 'mode': 'single', 'voice': 'Kore', 'text': '请把这份通知宣读清楚：会议改到周五上午九点，不要迟到。', 'style': '坚定、口齿清楚的成年女性播报，不要撒娇，也不要老人腔。'},
    {'title': '男声 · 活泼', 'mode': 'single', 'voice': 'Puck', 'text': '嘿，别走神。TTS 不是变声器，它只是把你写好的字读出来。', 'style': '活泼的成年男性，像朋友聊天，不要童声。'},
    {'title': '年轻感（提示词）', 'mode': 'single', 'voice': 'Leda', 'text': '我刚刚学会用这个声音实验室，有点紧张，但还是想试着讲完。', 'style': '听起来像二十出头的年轻人，气息轻、语速偏快，但仍然是成年声线，不要做成儿童配音。'},
    {'title': '年长感（提示词）', 'mode': 'single', 'voice': 'Gacrux', 'text': '孩子，有些道理不必急着懂。你把字写清楚，声音自然会跟着来。', 'style': '听起来像沉稳的长者，语速偏慢，留出停顿。这是提示词，不是官方老年档。'},
    {'title': '双人小播客', 'mode': 'dialogue', 'voice': 'Kore', 'voice2': 'Puck', 'text': 'Host: TTS 到底是什么？\nGuest: 就是把文字变成可以听的语音。\nHost: 那我能让它讲得更有感情吗？\nGuest: 可以！写清楚语气，再选择合适的声音。', 'style': 'Host 好奇而轻快；Guest 耐心且亲切。两位朋友自然交谈。'},
    {'title': '情绪与标签', 'mode': 'single', 'voice': 'Kore', 'text': '[whispers] 我告诉你一个秘密。\n[laughs] 原来，你也知道！', 'style': '先神秘地低语，再轻松地笑着说。'},
    {'title': 'English · Story', 'mode': 'single', 'voice': 'Vindemiatrix', 'text': 'The rain stopped just as she reached the old bookshop. Behind the window, a small light was still on.', 'style': 'A gentle storyteller. British English accent, unhurried pacing.'},
    {'title': '日本語 · 案内', 'mode': 'single', 'voice': 'Aoede', 'text': 'こんにちは。音声ラボへようこそ。今日は、言葉を声に変えてみましょう。', 'style': 'Friendly and clear Japanese narration.'},
    {'title': 'Filipino · 欢迎', 'mode': 'single', 'voice': 'Sulafat', 'text': 'Magandang araw! Maligayang pagdating sa aming munting kuwento. Sama-sama tayong matuto.', 'style': 'Warm and welcoming Filipino narration.'},
]
