# Gemini TTS 官方参考资料索引

核查日期：2026-09-10。检索范围：Google AI for Developers、Google Cloud Documentation、Google DeepMind、Google 官方 SDK 与 Cookbook 仓库。下面按功能去重；同一页面的语言版本、追踪参数及站点页脚不重复收录。

“全部”在这里指覆盖 Gemini TTS 使用所需的官方主干文档及相关参考入口，不宣称穷尽 Google 所有历史版本、博客、生成式 SDK 类型页或未来新增页面。论坛帖子即使位于 Google 域名，也不作为官方能力承诺。

## 先读这 5 个

| 官方链接 | 能解决的问题 | 对应项目位置 |
| --- | --- | --- |
| [Gemini API 语音生成总指南](https://ai.google.dev/gemini-api/docs/speech-generation) | 单人、双人、声音、语言、风格、标签、流式与限制 | 工作台；learning_guide.md |
| [GenerateContent 语音生成指南](https://ai.google.dev/gemini-api/docs/generate-content/speech-generation) | 兼容路径的 Python 配置结构；页面已标 Legacy | tts.py / generate_genai |
| [Google Cloud Gemini-TTS 总指南](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts) | Cloud / Vertex 的模型、区域、流式、结构化对话、编码及限制 | tts.py / generate_cloud |
| [Google Gen AI Python SDK 文档](https://googleapis.github.io/python-genai/) | Client、types、请求、响应、流式及 Batch | tts.py、batch_demo.py |
| [Google 官方 TTS Cookbook](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_TTS.ipynb) | Notebook 入门示例 | 可与 examples/quickstart.py 对照 |

## Gemini API 模型与调用

| 官方链接 | 用途 |
| --- | --- |
| [Gemini 3.1 Flash TTS Preview 模型页](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-tts-preview) | 输入输出、模型 ID、token 上限及支持/不支持能力 |
| [Gemini 2.5 Flash Preview TTS 模型页](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash-preview-tts) | Flash 模型参数与能力 |
| [Gemini 2.5 Pro Preview TTS 模型页](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-pro-preview-tts) | Pro 模型参数与能力 |
| [Gemini 模型目录](https://ai.google.dev/gemini-api/docs/models) | 从全部 Gemini 模型中定位 TTS / Live / 转写 |
| [Interactions 概览](https://ai.google.dev/gemini-api/docs/interactions-overview) | 新接口概念；与 GenerateContent 的区别 |
| [Batch API](https://ai.google.dev/gemini-api/docs/batch-api) | 创建、查询、取消和读取异步批处理结果 |
| [Python SDK 源码](https://github.com/googleapis/python-genai) | 可运行示例、安装、类型与实际行为 |
| [Python SDK 更新记录](https://github.com/googleapis/python-genai/blob/main/CHANGELOG.md) | 升级时查兼容性变化 |
| [创建 API Key](https://aistudio.google.com/apikey) | 控制台入口，需要登录 |
| [API Key 使用与迁移](https://ai.google.dev/gemini-api/docs/api-key) | 环境变量、密钥保管、Auth Key 迁移 |
| [AI Studio 语音体验](https://aistudio.google.com/generate-speech) | 官方试听工作台，需要登录 |

## Cloud Text-to-Speech / Vertex AI

以下是同一 Gemini-TTS 专题页中的章节直达链接；不是不同产品的“通用承诺”。

- [Cloud 模型列表](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts#available-models)：**3.1 与 Gemini API 同名**（`gemini-3.1-flash-tts-preview`，展示名都带 Preview）。**2.5 Flash/Pro 不同名**：Cloud/Vertex 是 `gemini-2.5-flash-tts`（GA，无 preview），Gemini API 是 `gemini-2.5-flash-preview-tts`。
- [Cloud 区域列表](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts#available-regions)：先匹配模型，再选择 endpoint/location。
- [如何选择 Cloud TTS 或 Vertex](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts#choose-the-right-api)：SDK、已有项目与编码需求。
- [Cloud TTS 调用章节](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts#use-cloud-text-to-speech-api)：单人、自由文本双人、结构化双人和流式示例。
- [SSML `<lang>` / `<voice>`](https://cloud.google.com/text-to-speech/docs/ssml)：传统 Cloud 在同一请求里换语言或换声；日文汉字不要靠 `<lang>`。
- [Chirp 3: HD SSML 子集](https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd)：没有 `<lang>`；可用 `<voice>`。同步可用，流式不可。
- [Vertex AI 调用章节](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts#use-vertex-ai-api)：google-genai、ADC、单向流式。
- [Cloud 提示词建议](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts#prompting-tips)：台词与表演提示。
- [Cloud 语言表](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts#available-languages)：不要将 Gemini API 的语言代码直接当成 Cloud locale。
- [Cloud 声音表](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts#voice-options)：核对声音可用性，以及文档中的 Male/Female 标注。这是分类标签，不是请求里的 `gender` 字段。Gemini API 声音表用风格形容词（Firm、Youthful），不提供少年/壮年/老年枚举。
- [声音类型总览](https://docs.cloud.google.com/text-to-speech/docs/voice-types)：Chirp / Studio / Neural2 / WaveNet / Standard 的官方定位；Chirp 条目写明不支持 SSML、speakingRate、pitch（与 Chirp 专题页有冲突）。
- [创建音频文件](https://cloud.google.com/text-to-speech/docs/create-audio)：`text:synthesize` 示例，含 `name` 与 `ssmlGender`。
- [AudioConfig](https://cloud.google.com/text-to-speech/docs/reference/rest/v1/AudioConfig)：speakingRate、pitch、volumeGainDb、effectsProfileId。
- [音频设备配置](https://cloud.google.com/text-to-speech/docs/audio-profiles)：effectsProfileId。本 Demo 不发送。
- [Cloud Python SDK](https://docs.cloud.google.com/python/docs/reference/texttospeech/latest)：类、字段、认证与安装说明。
- [Cloud text.synthesize REST 参考](https://docs.cloud.google.com/text-to-speech/docs/reference/rest/v1/text/synthesize)：请求/响应及编码封装。它是通用 Cloud TTS schema，某个字段存在不表示 Gemini 模型一定支持。
- [Application Default Credentials 配置](https://docs.cloud.google.com/docs/authentication/provide-credentials-adc)：本地登录、服务账户和部署身份。

## 成本、运行和服务边界

| 官方链接 | 阅读时机 |
| --- | --- |
| [Gemini API 定价](https://ai.google.dev/gemini-api/docs/pricing) | 确认所选模型、标准/Batch、免费/付费层 |
| [Gemini API 限流](https://ai.google.dev/gemini-api/docs/rate-limits) | 遇到 429；查项目的实际额度 |
| [Gemini API 可用地区](https://ai.google.dev/gemini-api/docs/available-regions) | 开通或请求被地区限制时 |
| [Gemini API 排错](https://ai.google.dev/gemini-api/docs/troubleshooting) | 根据 HTTP 状态码定位问题 |
| [Gemini API 更新记录](https://ai.google.dev/gemini-api/docs/changelog) | 判断模型升级、弃用与行为变化 |
| [Gemini API 附加服务条款](https://ai.google.dev/gemini-api/terms) | 商用、数据使用及服务条件；免费/付费服务需要区分 |
| [Cloud TTS 定价](https://cloud.google.com/text-to-speech/pricing) | Cloud 账单，不要套用 Gemini API 报价 |
| [Cloud TTS 配额与限制](https://docs.cloud.google.com/text-to-speech/quotas) | 请求频率、并发及系统限制 |
| [Cloud TTS 更新记录](https://docs.cloud.google.com/text-to-speech/docs/release-notes) | Cloud 模型发布与变更 |
| [Gemini Live API](https://ai.google.dev/gemini-api/docs/live-api) | 需要实时交谈、麦克风输入或打断时 |
| [Gemini 音频理解](https://ai.google.dev/gemini-api/docs/audio) | 需要转写、理解音频时 |
| [DeepMind 3.1 Flash Audio 模型卡](https://deepmind.google/models/model-cards/gemini-3-1-flash-audio/) | 模型评估与边界；注意区分 TTS 与 Live |
| [3.1 Flash Audio 模型卡 PDF](https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-1-Flash-Audio-Model-Card.pdf) | 可下载的评估资料 |

## 相关但不是本 Demo 的路径

这些官方页面容易和 Gemini TTS 搜到一起。**传统声音请点顶栏 Chirp 3 HD / WaveNet / Neural2 / Standard / Studio 独立页**，不要把它们当成 Gemini-TTS。

| 官方链接 | 用途 |
| --- | --- |
| [Cloud Text-to-Speech 产品总览](https://docs.cloud.google.com/text-to-speech/docs) | 产品线总览：Gemini-TTS + Chirp / WaveNet / SSML |
| [支持的声音与语言](https://cloud.google.com/text-to-speech/docs/voices) | WaveNet / Neural2 / Standard / Chirp 3 / News / Polyglot / Studio 全表 |
| [声音类型总览](https://docs.cloud.google.com/text-to-speech/docs/voice-types) | 各家族定位与可控性；Chirp 与专题页的 SSML/pitch 表述冲突 |
| [Chirp 3: HD](https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd) | 声音名格式、流式、SSML 子集 |
| [Chirp 3: Instant Custom Voice](https://docs.cloud.google.com/text-to-speech/docs/chirp3-instant-custom-voice) | 克隆音色；本 Demo 不调用 |
| [Custom Voice](https://cloud.google.com/text-to-speech/docs/custom-voice) | AutoML 定制声；本 Demo 不调用 |
| [创建音频文件](https://cloud.google.com/text-to-speech/docs/create-audio) | 同步合成示例 |
| [Long audio](https://cloud.google.com/text-to-speech/docs/create-audio-text-long-audio-synthesis) | 异步写 GCS；本 Demo 长文是应用层分段 |
| [流式合成](https://cloud.google.com/text-to-speech/docs/create-audio-text-streaming) | 单向 / 双向流式 |
| [列出声音](https://cloud.google.com/text-to-speech/docs/list-voices) | voices.list；本 Demo 用文档快照 |
| [SSML 指南](https://cloud.google.com/text-to-speech/docs/ssml) | WaveNet / Neural2 等传统声音的标记 |
| [音频设备配置](https://cloud.google.com/text-to-speech/docs/audio-profiles) | effectsProfileId |
| [Firebase AI Logic 语音生成](https://firebase.google.com/docs/ai-logic/generate-speech) | 不是本 Demo：移动/Web 客户端 SDK |

## 重要核查结论与冲突记录

1. **流式必须按入口区分。** Gemini API 的 TTS 文档明确区分 2.5 与 3.1；Cloud 文档另有 2.5 模型的流式说明。不能笼统写“Gemini TTS 不支持流式”。
2. **长度不是一个数字。** Gemini 总览仍写 32k context，而具体模型页写 8,192 输入、16,384 输出 token。本项目不把 32k 当成可提交正文长度。Cloud 又使用 UTF-8 字节与音频时长约束。
3. **Cloud 多人章节的正文与表格不一致。** 正文局部出现合计 4,000 bytes，表格则是 prompt / text 各 4,000、合计 8,000。本项目按表格校验；如果端点拒绝，请进一步缩短，不能视为所有部署均能接受 8,000。
4. **新旧 API 并存。** 当前 Gemini 主指南展示 Interactions，GenerateContent 指南标记 Legacy。本 Demo 同时提供两条路径，默认选已用安装版 SDK 类型校验的 GenerateContent，便于对照现有样例。官方页面示例本身存在不同语言段落更新不齐的问题，应同时参考 SDK。
5. **普通话代码要分清。** Gemini 语言列表标 cmn；Cloud 需要 locale（如 cmn-CN），其他语言同理。填表并不能证明账号、区域、模型组合已获支持。
6. **模型可选不等于账号可用。** 这是文档快照，不是在线模型探测结果。Preview、区域、配额、授权都会影响实际调用。
7. **声音分类不要发明 API。** Gemini-TTS 原生字段是 `voice_name`（30 个预置名）。Cloud 声音表的 Male/Female 只用于选角。Chirp 3: HD 虽然也用 Kore 这类短名，请求里却是 `cmn-CN-Chirp3-HD-Kore`，并且走 `text:synthesize`，不是 Gemini 提示词。WaveNet 的 `ssmlGender` 不要套到 Gemini-TTS 上。
8. **一段里中日英不是统一开关。** Gemini API 写明自动识别输入语言；Vertex / Gemini API 混语时把 `language_code` 留空。Cloud Gemini 仍要填主 locale。Chirp SSML 没有 `<lang>`。WaveNet 的 `<lang>` 官方不支持带汉字的日语，应改用 `<voice>` 换到日语声。
9. **选传统不是因为「旧模型过时了还能凑合」。** Gemini-TTS 不走 SSML。日期、电话、验证码、毫秒停顿、IPA 是 Cloud TTS 传统路径的契约。计费单位也不同（字符 vs token），数字以 [定价页](https://cloud.google.com/text-to-speech/pricing) 为准；Studio / Chirp 不是一律更便宜。
10. **年龄没有 API。** Gemini 靠提示词 + Leda/Gacrux 风格词。Chirp 只能换 30 个说话人，提示词无效；[声音类型总览](https://docs.cloud.google.com/text-to-speech/docs/voice-types) 写明 Chirp 不支持 AudioConfig.pitch。WaveNet/Neural2/Standard/Studio 换 `name`（如 A/B/C/D）；`pitch` 是半音，不是童声档。`ssmlGender` 只是未指定 name 时的性别偏好。
11. **Chirp 文档冲突。** 类型总览写 Chirp 不支持 SSML / speakingRate / pitch；[Chirp 3: HD 专题](https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd) 又给出同步 SSML 子集与 HD 语速控件。本 Demo 同步可勾选 SSML，流式不可；pitch 对 Chirp 不发送。以端点行为为准。

## 如何保持资料不过时

每次升级先看两份 release notes，再核对模型页、价格和配额。保留失败时的入口、模型 ID、SDK 版本、错误码和输入长度，不保存密钥。确认变更后更新 catalog.py 与测试；不要仅根据搜索摘要改代码。

本站安装与工程说明、学习练习、应用层分段和 UI 操作说明为本项目原创；Google 示例思想与能力说明均附官方出处，未逐字复制长篇文档。
