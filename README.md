# Gemini 声音实验室

一个中文、可在本机运行的 Gemini TTS Web Demo。后端使用官方 Python SDK，前端无需 Node.js。你提供台词，选择声音和表演方式，得到可以试听、下载的语音。

**第一次接触？先运行本页的 4 步，再打开 [learning_guide.md](learning_guide.md)。**

资料核查日期：2026-09-10。完整入口见 [官方资料索引](docs/official_sources.md)。本项目不是 Google 官方产品。

## 1. 你拿到了什么

- 顶栏按引擎分页：Gemini-TTS、Chirp 3 HD、WaveNet、Neural2、Standard、Studio。每页只展示该引擎的控件和**适合该页的**场景样例（约 90 条），不适合的不会跨页硬塞。
- Gemini-TTS 页：单人/双人、30 个预置声音、语气提示、音频标签、声线锁定、UTF-8 文本导入。控制是提示词引导，不是确定性的音频编辑器。
- Vertex AI（默认）：通过 google-genai + ADC（`gcloud auth application-default login`）调用 Cloud 模型，不需要 API Key。
- Gemini API：可选备用路径，使用 GenerateContent / Interactions 与 API Key。
- Cloud TTS · Gemini-TTS：仍在 Gemini-TTS 页切换入口；通过 google-cloud-texttospeech + ADC，支持 WAV、MP3、OGG Opus 和结构化双人台词。
- 传统声音各页：Chirp 3: HD、WaveNet、Neural2、Standard、Studio。各自展开 SSML / 语速 / 语言代码。**不是** Gemini-TTS，这些页没有提示词演戏。
- 流式接收与浏览器即时播放、停止、WAV 下载；兼容不流式的模型。
- 长文按 UTF-8 字节分段、逐段生成和 PCM 拼接；预览会显示请求次数。
- 独立文字模型起草台词，检查后再调用 TTS。
- 请求预览、中文排错、耗时/大小/音频时长、配置导出。
- 真正 Batch API 的命令行示例：提交、查询、下载和取消；不是把普通请求循环称为批处理。
- README、学习指南、官方参考索引及无需密钥的自动测试。

## 2. 四步启动（macOS / Linux）

### 第一步：进入项目目录

打开终端，进入本仓库根目录（含 `README.md` 的那一层）：

```bash
git clone https://github.com/jayson-sheyue/TTSDemo.git
cd TTSDemo
```

若已有本地拷贝，直接 `cd` 到该文件夹即可。需要 Python 3.10 或更新版本；本项目在 Python 3.14.6 上验证。

### 第二步：安装依赖

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

`.venv` 是这个项目自己的 Python 环境，不会把依赖混入其他项目。下载失败时检查网络与 PyPI 访问能力。不要换成旧的 `google-generativeai` 包。

### 第三步：用 ADC 登录（不需要 API Key）

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
cp .env.example .env
```

用文本编辑器打开 `.env`，填入你的 Google Cloud 项目：

```dotenv
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
GOOGLE_CLOUD_LOCATION=global
```

命令是 `gcloud auth application-default login`（中间是连字符）。浏览器弹出 Google 账号登录后，本机才会有 ADC。项目需启用账单，并具备调用模型的权限；Gemini-TTS 指南要求 `aiplatform.endpoints.predict`，可由 `roles/aiplatform.user` 提供。

不填项目也可以打开界面、读文档、载入示例和预览请求；点击“生成语音”会提示配置。**没有假语音或本地合成替代结果。** 只有当你把服务入口改成「Gemini API」时，才需要 `GEMINI_API_KEY`。

### 第四步：运行

```bash
.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8001
```

或：`.venv/bin/python app.py`（同样默认 8001，可用环境变量 `DEMO_PORT` 覆盖）。

看到服务器启动后，在浏览器打开 [本地 Demo](http://127.0.0.1:8001)。保持终端开启。停止服务器按 `Ctrl+C`。修改 `.env` 或重新 login 后也要重启。

依次点击“第一段中文” → “预览请求” → “生成语音”。首次可能等待数秒或更长；本项目单次远程调用超时为 120 秒，不承诺具体生成时延。

## 3. Windows 启动

在项目目录打开 PowerShell：

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8001
```

使用环境内 Python 的完整路径，不需要修改 PowerShell 执行策略。

## 4. 按钮怎么用

| 你想做什么 | 操作 | 观察什么 |
| --- | --- | --- |
| 第一次出声 | 留在 Gemini-TTS 页，点「入门 · 第一段中文」→ 生成语音 | 是否能正确读完 |
| 听女声 / 男声 | 点右侧「女声」或「男声」筛选 | 只改主声音（角色 A）；双人时角色 B 仍可另选性别 |
| 女声要演凶狠 | 导入「女声也可以凶」，不要只写「黑社会头目」 | 声线仍是女声，情绪变凶 |
| 试某种语言的官方全表 | 传统页换「语言 / locale」下拉 | 下拉会列出该语言全部声音，不是抽查 |
| 传统路径换「年龄感」 | Chirp 听 Leda/Gacrux；WaveNet 听 A vs D，再听「音高 +4」 | Chirp 不能演；pitch 不是童声档 |
| 判断业务用哪一页 | 入门指南「业务怎么选型」；各页顶部「适合 / 不适合」 | 测通后看该页底部官方文档 |
| 换人朗读 | 只改主声音，再生成 | 音色差异 |
| 更有感情 | 改语气与表演，再生成 | 同一句话的情绪 |
| 做小播客 | 导入「双人播客」 | 角色名与台词是否匹配 |
| 试其他语言 | 打开当前页「多语言」分组（不要跨页硬贴） | 传统页必须换对 locale 和声音名 |
| 一段里中日英混排 | 各引擎页点「高阶 · 中日英混语」 | Gemini 留空语言码；Chirp/WaveNet 用 SSML 换声，不要拿日文汉字去套 xml:lang |
| 低语或笑声 | 导入「低语与笑声」，用 3.1 模型 | 标签是否按预期表演 |
| 试 Chirp / WaveNet | 打开顶栏对应页，导入该页样例 | 没有提示词框；SSML 能控停顿 |
| 为什么选传统不选 Gemini | WaveNet「独有 · 验证码与日期」，再对照 Gemini「验证码只能靠提示词」 | A3K9 是否逐字、日期是否像日期 |
| 更快开始听 | 开启“边生成边播放” | 首段音频耗时 |
| 处理长文 | 各引擎页都有「长文 · 分段拼接」；先预览看段数 | 请求段数、接缝是否像同一次录音 |
| 试韩语 / 粤语 / 西语法语 | 打开对应页的「多语言」样例，不要跨页硬贴 | 传统页必须换对 locale 和声音名 |
| 看实际输入 | 预览请求 | 风格指令与 TRANSCRIPT 分隔 |
| 拿走音频 | 生成完成后下载 | WAV / Cloud MP3 / Cloud OGG |
| 让 AI 写稿 | 输入主题，生成草稿 | 先检查事实再合成 |
| 保留实验条件 | 导出本次配置 | 不含密钥；相同配置不保证相同声音 |

浏览器可能限制自动播放。本 Demo 在你点击生成时启用音频上下文；若流式没有声音，等生成完成后点播放器播放。流式播放期间点击成品播放器会停止尚未播完的流式队列，避免重叠。

## 5. 选择服务入口与模型

| 入口 | 身份方式 | Python 包 | 模型 ID 示例 |
| --- | --- | --- | --- |
| Gemini API | API Key | google-genai | gemini-3.1-flash-tts-preview；gemini-2.5-flash-preview-tts；gemini-2.5-pro-preview-tts |
| Vertex AI | ADC + Cloud 项目 | google-genai | gemini-3.1-flash-tts-preview；gemini-2.5-flash-tts；gemini-2.5-pro-tts；gemini-2.5-flash-lite-preview-tts |
| Cloud TTS | ADC + Cloud 项目/权限 | google-cloud-texttospeech | 同 Cloud 列表，另含 gemini-2.5-flash-lite-preview-tts |

Flash-Lite 在此仅用于单人模式。**3.1 Flash TTS 三入口同名** `gemini-3.1-flash-tts-preview`（展示名都带 Preview）。**只有 2.5 Flash/Pro 的 ID 分叉**：Gemini API 带 `-preview-tts`，Cloud / Vertex 是无 preview 的 GA 名。不要把 2.5 的两种 ID 对调。模型下拉来自核查快照，未代替账号的模型可用性检查。[模型与入口出处](docs/official_sources.md)

三条 Gemini 路径共用同一套 30 个预置声音，但身份、格式、流式和双人能力不同。对照表在「入门指南」页。传统 Cloud（Chirp / WaveNet 等）不在 Gemini 页的服务入口里，请点顶栏独立页。

| | Gemini API | Vertex AI | Cloud Text-to-Speech |
| --- | --- | --- | --- |
| 身份 | API Key | ADC + Cloud 项目（默认） | ADC + Cloud 项目 |
| 下载格式 | PCM → Demo 打成 WAV | 同左 | WAV / MP3 / OGG（MP3·OGG 需非流式） |
| 流式 | 仅 3.1 | 2.5 / 3.1（视区域） | 2.5 / 3.1（视区域）；官方示例偏单人 |
| Flash-Lite | 无 | 有，仅单人 | 有，仅单人 |
| 双人对话（最多 2 人） | 能：自由文本 | 能：自由文本 | 能：自由文本 |
| 结构化双人 markup | 无此字段 | 无此字段 | 有，非流式 |
| 男/女分类 | 无独立参数 | 同左 | 声音表有 Male/Female，仍不是请求字段 |
| 少年/老年档 | 都不提供 | 同左 | 同左 |

四个 Gemini TTS 模型的差异（单人/双人/流式）见学习指南第 5 节；换模型时看工作台「语音模型」下方的能力说明。

## 5.1 声音分类：官方原生支持什么？

| 分类 | 官方是否原生支持 | 在本 Demo |
| --- | --- | --- |
| 30 个预置 `voice_name` | 支持 | 声音下拉框 |
| 女声 / 男声 | Cloud 声音表标注 Male/Female；**API 没有 gender 字段** | 「全部 / 女声 / 男声」筛选，发出去仍是声音名字 |
| 少年 / 壮年 / 老年 | **不支持**，没有 age 枚举 | 选 Leda（Youthful）或 Gacrux（Mature），把年龄写进语气 |
| 自定义音色 / 克隆 | 不支持 | 做不到 |

试听：载入「女声 · 坚定」「男声 · 活泼」「年轻感（提示词）」「年长感（提示词）」。性别靠选声，年龄靠提示词。

**流式矩阵：**

| 服务 | 3.1 Flash TTS | 2.5 Flash / Pro TTS |
| --- | --- | --- |
| Gemini API | 流式/非流式 | 非流式 |
| Vertex | 流式/非流式 | 流式/非流式，需区域支持 |
| Cloud TTS | 流式/非流式 | 流式/非流式，需区域支持 |

Cloud 流式示例以单人为官方文档明确展示的路径；本 Demo 的 Cloud 多人流式使用 SDK 的多人配置组合，仍需在目标服务上验证。要对照官方多人流式示例，优先用 Vertex。Cloud 结构化双人模式限定非流式。

## 6. Cloud 区域、编码与权限（进阶）

先安装 Google Cloud CLI，并在你的项目启用账单和所需 API。项目需具备调用模型的权限；Gemini-TTS 指南要求 `aiplatform.endpoints.predict`，可由 `roles/aiplatform.user` 提供。权限由项目管理员配置。

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

`.env` 示例：

```dotenv
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
GOOGLE_CLOUD_LOCATION=global
CLOUD_TTS_ENDPOINT=texttospeech.googleapis.com
```

- Vertex 使用 `GOOGLE_CLOUD_PROJECT` 和 `GOOGLE_CLOUD_LOCATION`。Cloud 文档显示 3.1 TTS 目前主要在 `global`。
- Cloud SDK 从 ADC 读取身份/配额项目；只填写项目变量不等于完成 ADC 配额配置。
- 按 [官方区域表](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts#available-regions) 调整 location / endpoint。不要把 Vertex 的 endpoint 填进 Cloud TTS endpoint。
- Cloud 在界面中填写语言代码，如 `en-US`，普通话参照语言表填写 `cmn-CN`。
- Wave 是通用路径。Cloud MP3/OGG 仅限关闭流式与分段；这是本 Demo 的拼接实现边界。

## 7. 项目结构与 API

```text
app.py                    FastAPI、静态页面、文档、流式响应及写稿路由
tts.py                    输入校验、分段、SDK 适配、PCM/WAV、错误处理
catalog.py                模型、30 声音、六页工作台、能力对照、入门示例快照
samples.py                加载 sample_assets 场景样例
sample_assets/            约 90 条按引擎过滤的 JSON（长文、多语言、业务、功能怎么测）
voice_assets/             Cloud 声音全表快照；工作台按语言筛选，不是一次铺开
static/index.html         顶栏分页壳；各引擎页由 app.js 按 catalog.workspaces 生成
static/style.css          响应式样式
static/app.js             流式播放器、下载、交互
examples/quickstart.py     最小 Python 单人合成
batch_demo.py             官方 Batch API 命令行示例
tests/                    无密钥测试与模拟 SDK 响应
README.md                 启动与工程说明
learning_guide.md          从零学习与能力边界
docs/official_sources.md   官方资料索引与冲突记录
```

开发接口文档：[FastAPI Swagger](http://127.0.0.1:8001/docs)。`POST /api/preview` 不调用 Google；`POST /api/synthesize` 返回逐行 JSON（NDJSON），事件顺序是 start → segment → audio → done，失败则 error。`audio.data` 是 base64 编码的数据；WAV 模式内部传输 raw PCM，浏览器在完成时添加 WAV 头。`POST /api/draft` 另行调用文字模型。

请求示例：

```json
{"provider":"vertex","api":"generate","model":"gemini-3.1-flash-tts-preview","mode":"single","text":"你好，世界。","voice":"Kore","style":"亲切、自然","stream":true}
```

对话须每行以英文/数字角色名加冒号开头。服务端验证两位角色确实都有台词，避免只有一个声音却误以为跑通了双人合成。

## 8. 长度、格式与错误处理策略

- 输入最多 30,000 字符，最多 20 段，单次作品接收上限 100 MB：均为 Demo 自定资源边界。
- 每段默认 1,800 UTF-8 字节，可调 300–3,000。通常一个汉字占 3 字节，字符数、字节数、token 数不相同。
- 每段完整 prompt 保守限制 8,000 字节，风格指令最多 4,000 字节。Cloud 正文另限 4,000 字节。Gemini API 的字节检查是本项目保守策略，不是官方 token 计数器。
- 按标点/行切分；普通文本可在超长句内按字符切分。对话不切断角色行：过长就要求用户拆行。
- 拼接不添加静音、不交叉淡化；不保证接缝自然，也不保证生成完整。请听末句核对。
- 原始 PCM 为单声道、16-bit little-endian、24 kHz。Cloud LINEAR16 已有 WAV 头，先解包再统一处理，不能重复添加头。
- 检查空音频、非预期编码、异常 finish reason 与缺失完成事件。失败后不提供伪装成完整结果的下载。
- 仅在尚未收到音频时对部分 500/502/503 异常自动重试一次；中途失败不回放重试，以免重复音频。429 不自动刷请求。
- “停止”中断浏览器请求和播放；同步 SDK 调用可能等超时才释放后台工作，云端也可能继续并计费。
- 一次只接受一个生成/写稿任务，避免快速连点造成并发费用。

## 9. 成本与数据

本项目不会预测你的真实账单。输入、输出、模型、服务入口、套餐、重试、Batch 都影响费用。价格看 [Gemini](https://ai.google.dev/gemini-api/docs/pricing) 或 [Cloud](https://cloud.google.com/text-to-speech/pricing) 对应页面；不能把播放器显示的时长直接当成完整费用。

凭据只在 Python 进程中使用（ADC 文件或可选的 API Key）。**不要把 `.env`、服务账户 JSON、API Key 提交进 git**；仓库已忽略 `.env`。浏览器只收到“是否已配置”的布尔值。文本和音频在当前请求/页面内存中使用，不自动保存到服务器磁盘，刷新后作品消失；主动下载/导出的文件由浏览器保存。Google 服务端的数据处理另遵循所选服务的官方条款，不能由本项目的“本地不保存”推导出“云端不保留”。Interactions 请求显式 `store=False`，不等于绕开服务条款中的其他日志或保留规则。

这是单用户本地教学 Demo：默认绑定 127.0.0.1，限制 Host 和跨站请求。不要直接改为公网监听并分享，因为没有用户登录、用户级配额和持久任务管理。

## 10. 常见问题

| 现象 | 怎么处理 |
| --- | --- |
| 生成提示没有项目或 ADC | `.env` 填写 `GOOGLE_CLOUD_PROJECT`，运行 `gcloud auth application-default login` 后重启 |
| 401 / 403 | 检查 ADC 是否过期、配额项目、API 启用、账单和 IAM；只有 Gemini API 才查 Key |
| 404 模型不存在 | 检查 Gemini / Cloud 的名字差异和区域，不是换一个 SDK 就一定能解决 |
| 400 参数错误 | 缩短文本，检查语言、模型与流式组合；Cloud 语言代码不可空 |
| 429 | 在控制台查看实际配额和账单，等待恢复；连续重试不会增加额度 |
| 500 / 503 | 本项目对首音前临时错误重试一次；仍失败则稍后尝试短句 |
| 提示词被念出 | 保留清晰“合成语音”指令与 TRANSCRIPT 分隔，减少不相关描述 |
| 有声音但漏字 | 对照原文，缩短片段；不要默认响应成功就代表完整 |
| 噪声 / 速度不对 | 确认 PCM 编码与 WAV 头，勿把 raw PCM 直接当 MP3 |
| 长文不稳定 | 缩短段落、保持同一声音和风格、人工听接缝 |
| 端口被占用 | 将启动参数改成 `--port 8765`，浏览器同步用 8765；或设置 `DEMO_PORT` |
| 停止后提示仍有任务 | 后端同步调用尚未退出，等超时或结束；不要反复重启制造重复请求 |

更多见 [官方排错指南](https://ai.google.dev/gemini-api/docs/troubleshooting)。本项目不把上游异常原文直接显示给浏览器，以免泄漏密钥或台词。

## 11. 运行测试与验证范围

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

测试不联网、不生成收费语音，覆盖文本切分、UTF-8 边界、角色/模型组合、音频头、SDK 类型构造、响应解析、空响应、重试策略、网页/API 路由和错误流。

自动测试不联网、不使用真实 Google 凭据，因此不会产生收费合成。测试通过能证明本地逻辑与模拟调用路径的行为，**不能证明你的账号可用、某个端点已部署模型或实际音质达标**。配置凭据后按学习指南的验收步骤测试。

## 12. Batch API（异步批量）

不着急立即拿到声音、又有多条短稿时才考虑 Batch。它和工作台长文分段是两种机制；工作台不自动提交 Batch。

```bash
.venv/bin/python batch_demo.py submit examples/batch.json
.venv/bin/python batch_demo.py status batches/返回的任务ID
.venv/bin/python batch_demo.py download batches/返回的任务ID
.venv/bin/python batch_demo.py cancel batches/返回的任务ID
```

submit 会产生真实云端任务，可能计费；命令只执行你指定的动作，不自动提交第二次，不无限轮询。复制完整任务名，等成功后下载。音频保存在 outputs 下的新目录。这里使用小规模 inline requests；大型 JSONL/文件结果路径见 [Batch 官方指南](https://ai.google.dev/gemini-api/docs/batch-api)。
