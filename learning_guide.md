# Gemini TTS 学习指南

这份指南是给第一次接触的人写的。你不需要先懂机器学习、HTTP 或 Google Cloud。

**目标：** 跟着做一遍之后，你能清楚回答四件事：

1. Gemini TTS 是什么
2. 它能干什么
3. 它不能干什么
4. 出问题时该打开哪份官方文档

先按 [README.md](README.md) 把 Demo 跑起来，再回到这里。没有 ADC / 项目也可以读完本页、点开工作台、载入示例并使用「预览请求」；**只有「生成语音」和「写稿」需要把文字发到 Google，并可能计费。**

资料核查日期：2026-09-10。完整入口见 [docs/official_sources.md](docs/official_sources.md)。本项目不是 Google 官方产品；能力以对应官方页面为准。

---

## 0. 先建立正确的图像（2 分钟）

### 一句话

**TTS（Text-to-Speech）= 把已经写好的文字，变成可以播放的语音。**

Gemini TTS 是 Google 提供的一类**专用语音模型**：输入只能是文字，输出只能是音频。它特别擅长按你的自然语言指示去「表演」——语气、口音、节奏、场景都可以写进提示词。

### 用导演和演员来理解

| 你在工作台里做的事 | 对应现实 | 对应 API |
| --- | --- | --- |
| 写下台词 | 剧本 / transcript | 请求里的文本 |
| 选择 Kore / Puck 等 | 选一个预置配音演员 | `voice_name` |
| 填写语气、口音、节奏、场景 | 导演阐述 | 提示词（prompt） |
| 插入 `[whispers]` | 当场喊戏 | 行内音频标签 |
| 双人模式写 `Host:` / `Guest:` | 两个演员对戏 | 最多 2 个 speaker |
| 点「生成语音」 | 开拍 | 一次（或分段多次）云端调用 |

演员会演，但**不是音频工作站**：同一句台词每次生成都可能略有差别；不保证一个字都不漏；也不能精确到毫秒地剪辑。

### 官方怎么定位它

官方语音生成指南把 Gemini TTS 和 **Live API** 区分开：

- **TTS**：适合需要尽量按稿朗读、并精细控制风格的场景，例如播客、有声书、旁白。
- **Live API**：适合实时对话、麦克风输入、随时打断，不属于本 Demo。

出处：[Gemini API 语音生成总指南](https://ai.google.dev/gemini-api/docs/speech-generation)

---

## 1. 15 分钟上手（必须做）

打开 [本地工作台](http://127.0.0.1:8001)。下面每一步只改一个变量，这样你听得懂「到底是什么在变」。

### 练习 1：先出声（3 分钟）

1. 点「第一段中文」。
2. 点「预览请求」（不收费）。看两件事：上面是导演提示，下面 `TRANSCRIPT:` 之后才是要读的台词。
3. 点「生成语音」，等待播放或点播放器。

**成功标准：** 你听到的内容大体就是编辑框里的中文。  
**失败时：** 看页面顶部是否提示未配置 ADC / 项目；再看 [README.md](README.md) 第 10 节。只有把服务入口改成 Gemini API 时才需要 API Key。

### 练习 2：只换声音（3 分钟）

台词和语气都不要动。只把主声音从 Kore（女声 · 坚定）换成 Puck（男声 · 活泼），再生成一次。右侧可用「女声 / 男声」筛选，但发出去的请求里仍然只有 `voice_name`，没有 gender 字段。

**成功标准：** 同一句话，音色明显不同。  
**记住：** 声音名称旁边的「坚定 / 活泼」只是选角提示，不是音质保证。先听，再决定。

### 练习 2b：年龄感靠提示词，不是档位（可选）

点「年轻感（提示词）」听 Leda，再点「年长感（提示词）」听 Gacrux。官方只有 Youthful / Mature 这类形容词，**没有**少年、壮年、老年 API。Gemini-TTS 页左侧「本页场景样例」也可以一键导入这两条。

**成功标准：** 你能听出提示词改变了表演；不要把它理解成官方年龄档已生效。

### 练习 3：只改语气（3 分钟）

声音改回 Kore。把「语气与表演」改成：`又累又无聊，不想解释，但还是在说。` 再生成。

**成功标准：** 同一句话，情绪不同。  
**记住：** 这是提示词引导，不是把「累」这个旋钮拧到 70%。写得越具体越好，例如口音写成「Brixton, London 的英语」通常比只写「英国口音」更有效。

### 练习 4：双人小播客（4 分钟）

1. 点「双人小播客」。
2. 确认每行是 `Host:` 或 `Guest:` 开头。
3. 给两个角色选不同声音。
4. 预览，再生成。

**成功标准：** 能听出两个人在轮流说话。  
**失败时：** 角色名必须和台词里的名字完全一致；本 Demo 只允许英文/数字角色名，如 `Host` / `Guest`。两位都必须至少有一句台词。

### 练习 5：标签与流式（可选，2 分钟）

点「情绪与标签」，确认模型是 `gemini-3.1-flash-tts-preview`，需要的话打开「边生成边播放」，再生成。

**成功标准：** 低语和笑声至少能听出变化。  
**记住：** 官方没有「哪些标签一定有效」的完整清单；非英语台词也建议继续使用英语标签，例如 `[whispers]`，不要写成 `[低语]`。

做完这 5 步，你已经用过 Gemini TTS 的主干能力。下面是完整功能地图。

---

## 2. 它能干什么：主流功能地图

这些功能都来自官方文档；工作台只是把它们收成表单。

| 功能 | 一句话 | 官方出处 | 在本 Demo 里 |
| --- | --- | --- | --- |
| 单人朗读 | 一个预置声音读完整段文字 | 语音生成指南 · Single-speaker | 模式：单人朗读 |
| 双人对话 | 最多两个说话人，名字必须和台词一致 | 同上 · Multi-speaker | 模式：双人对话 |
| 30 个预置声音 | 只能从官方名单选，不能上传自己的声音 | 语音生成指南 · Voice options | 声音下拉框 |
| 女声 / 男声筛选 | Cloud 声音表给 30 个名字标了 Male/Female；**请求里没有 gender 参数** | Cloud Gemini-TTS · Voice options | 步骤 03 的「全部 / 女声 / 男声」 |
| 少年 / 壮年 / 老年 | **官方不提供年龄档**；没有 age 枚举 | 文档只有风格形容词，如 Youthful / Mature | 选 Leda / Gacrux，把年龄写进语气 |
| 自动识别语言 | Gemini API 可不填语言代码 | 语音生成指南 · Supported languages | 语言代码可留空 |
| 一段里中日英混排 | 不是所有引擎都能「自动换语」 | Gemini：留空语言码 + 提示词；传统 Cloud：SSML `<voice>` | 各页「高阶 · 中日英混语」 |
| 指定语言代码 | Cloud 必须填 locale，如 `cmn-CN` | Cloud Gemini-TTS · Available languages | 连接与音频格式 |
| 自然语言控风格 | 用文字指定语气、口音、节奏、场景 | 语音生成指南 · Prompting guide | 步骤 02 |
| 行内音频标签 | `[whispers]` `[laughs]` 等，3.1 更适合 | 语音生成指南 · Audio tags | 表演标签按钮 |
| 先写稿再朗读 | TTS 模型不会写故事；用普通文字模型起草台词、表演标签和导演提示 | 语音生成指南 · Generate a prompt | 「让文字模型帮你起草」会同时填入步骤 02 |
| 流式播放 | 音频边生成边到达；Gemini API 仅 3.1 | 语音生成指南 · Streaming | 「边生成边播放」 |
| 非流式完整返回 | 等全部生成完再播放 | 2.5 在 Gemini API 上的路径 | 关闭流式 |
| GenerateContent | 旧路径，文档标 Legacy，SDK 样例多 | [GenerateContent 语音指南](https://ai.google.dev/gemini-api/docs/generate-content/speech-generation) | 调用方式下拉框 |
| Interactions | 新接口 | [Interactions 概览](https://ai.google.dev/gemini-api/docs/interactions-overview) | 同一下拉框 |
| Vertex AI | 用 Cloud 项目 + ADC 调同一类模型 | [Cloud Gemini-TTS](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts) | 服务入口：Vertex |
| Cloud Text-to-Speech | 可输出 WAV / MP3 / OGG，可结构化双人 | 同上 | 服务入口：Cloud TTS |
| 结构化双人台词 | Cloud TTS 独有字段：每句做成 Turn，不是自由文本。Vertex / Gemini API 没有这个字段，但仍能双人 | Cloud 文档 Multi-speaker markup | Gemini-TTS 页勾选后仅非流式、且须选 Cloud TTS 入口 |
| Batch API | 异步批量，适合不赶时间的多条短稿 | [Batch API](https://ai.google.dev/gemini-api/docs/batch-api) | 命令行 `batch_demo.py`，工作台不用 |

### 官方点名的常见标签

官方写明：没有穷尽清单，需要自己试。下面这些是文档里举例或常用的：

`[whispers]` `[shouting]` `[laughs]` `[sighs]` `[gasp]` `[excited]` `[bored]` `[tired]` `[sarcastic]` `[serious]` `[trembling]` `[crying]` `[giggles]` `[curious]` `[amazed]` `[panicked]` `[mischievously]` `[very fast]` `[very slow]`

你也可以写更具体的，例如 `[like a cartoon dog]`。**效果以试听为准，不要当成开关。**

---

## 3. 它不能干什么（比「能做」更重要）

把这一节当作防踩坑清单。很多失败不是你操作错了，而是产品边界。

### 3.1 不是同一个 Gemini 产品

| 你想做的事 | 正确产品 | 本 Demo |
| --- | --- | --- |
| 把录音转成文字 | [音频理解](https://ai.google.dev/gemini-api/docs/audio) / 转写模型 | 不做 |
| 对着麦克风实时聊天、打断、插话 | [Live API](https://ai.google.dev/gemini-api/docs/live-api) | 不做 |
| 让普通 Gemini 边说话边回答问题 | Live / Native Audio，不是 TTS 模型 | 不做 |
| 克隆某个真人的声音（声音克隆） | Gemini TTS 不提供 | 做不到 |
| 上传自己的音色文件 | 只有 30 个预置声音 | 做不到 |
| 按少年 / 壮年 / 老年档选声 | 没有 age 枚举；只有风格形容词 | 用提示词 + Leda / Gacrux 等接近的声音 |
| 一次真正的「三人对谈」 | 官方 TTS 多人上限是 **2** | 做不到 |
| 用 SSML 精确定标停顿/音高 | 那是传统 Cloud TTS（WaveNet / Chirp / Neural2），不是 Gemini 提示词 | 打开顶栏 Chirp 3 HD 或 WaveNet 页，勾选 SSML |
| 当音频编辑器使用 | 没有时间轴、交叉淡化、响度标准化 | 长文只是分段硬拼接 |

### 3.2 TTS 模型自己也不会的事

官方模型页写明 TTS 模型：

- 只接受**文本输入**，只产生**音频输出**
- **不支持**缓存、函数调用、结构化输出、代码执行、接地搜索、图像、Live API、思考模式等
- 输入 / 输出 token 上限以模型页为准：目前 3.1 / 2.5 TTS 页写的是输入 8,192、输出 16,384
- 总览里仍会出现 32k context 的说法；**不要把 32k 当成你可以粘贴的正文长度**

出处：[3.1 Flash TTS 模型页](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-tts-preview)

### 3.3 即使「成功返回」也不保证

官方 Limitations 和 3.1 说明里写过这些现象：

- 声线可能和所选声音、提示词不完全一致
- 长于几分钟的音频，质量与一致性可能漂移
- 偶发返回文本 token 而不是音频，表现为 500；可对**尚未出声**的请求重试
- 提示词太含糊时，可能被内容策略拒绝，或把导演说明也读出来
- 风格、标签、口音都是引导，不是确定性控件
- 预览模型可能变更、限额更紧，不承诺 SLA

本 Demo 因此会：把导演说明和台词用 `TRANSCRIPT:` 分开；检查空音频和异常结束原因；失败时不提供假装完整的下载。

### 3.4 本 Demo 额外不做的事

- 不把密钥发到浏览器
- 不在服务器磁盘保存你的台词或音频
- 不预测账单
- 不把长文分段伪装成官方 Batch API
- 不把本地拼接的接缝处理成专业母带
- 默认只绑定 `127.0.0.1`，不是给公网多人使用的产品

---

## 4. 三条服务入口，怎么选

这三列都在 **Gemini-TTS 页**里切换。Chirp / WaveNet / Neural2 / Standard / Studio 不在这个下拉框里，请点顶栏独立页。

你只需要先记住：**本 Demo 默认用 Vertex AI + ADC**（`gcloud auth application-default login`），不需要 API Key。Gemini API Key 是可选备用。

| | Gemini API | Vertex AI | Cloud Text-to-Speech |
| --- | --- | --- | --- |
| 身份 | 可选 API Key | ADC + Cloud 项目（本 Demo 默认） | ADC + Cloud 项目/权限 |
| Python 包 | `google-genai` | `google-genai` | `google-cloud-texttospeech` |
| 适合谁 | 个人学习、最快出声 | 已有 Vertex 项目 | 需要 MP3/OGG 或 Cloud 工作流 |
| 30 个预置声音 | 同一份名单 | 同一份名单 | 同一份名单，文档另标 Male/Female |
| 男 / 女分类 | 无独立参数；靠选 `voice_name` + 提示词 | 同左 | 声音表有 Male/Female，仍不是请求字段 |
| 少年 / 老年档 | 都不提供枚举；用提示词 | 同左 | 同左 |
| 2.5 Flash / Pro 模型 ID | `gemini-2.5-flash-preview-tts` | `gemini-2.5-flash-tts`（无 preview） | 同 Vertex |
| 3.1 模型 ID | `gemini-3.1-flash-tts-preview`（三入口同名，都带 preview） | 同左 | 同左 |
| Flash-Lite | 无 | 有，仅单人 | 有，仅单人 |
| 流式 | 仅 3.1 | 2.5/3.1 均可（需区域支持） | 官方明确展示的是单人流式 |
| 下载格式 | PCM → 本 Demo 打成 WAV | 同左 | WAV / MP3 / OGG（MP3·OGG 需非流式） |
| 语言代码 | 可空；列表如 `cmn`、`en` | 按 Vertex/Cloud 文档 | **必填 locale**，如 `cmn-CN` |
| 双人对话（最多 2 人） | 能：自由文本 + 两个 speaker | 能：同左 | 能：自由文本双人 |
| 结构化双人 markup | 无此字段 | 无此字段 | 有 `multi_speaker_markup`，仅非流式 |
| 3.1 区域 | 按 Gemini 地区文档 | Cloud 表：目前主要是 `global` | 目前主要是 `global` |

**不要把「结构化双人」读成「Vertex 不能双人」。** Vertex / Gemini API 都能做双人：台词写成 `Joe:` / `Jane:`，再配两个 speaker。Cloud TTS 多出来的是字段 `multi_speaker_markup`：把每一句做成 Turn 对象，文档说这有利于地址、日期等「按人话来读」；自由文本则尽量按字面读。三人及以上官方不提供。

**3.1 的模型 ID 在三条入口上相同**，都是 `gemini-3.1-flash-tts-preview`，展示名也叫 Preview。这和 AI Studio、Vertex / Agent Platform Studio 里看到的一致。

**不要混用的是 2.5 Flash / Pro。** Gemini API 仍是 `gemini-2.5-flash-preview-tts`；Cloud / Vertex 已是 GA 名 `gemini-2.5-flash-tts`（没有 preview）。把前者填进 Cloud，或把后者填进 Gemini API，会 404。2.5 Flash-Lite 的 `gemini-2.5-flash-lite-preview-tts` 只在 Cloud / Vertex。

Cloud 普通话示例是 `cmn-CN`（文档里台湾写作 `cmn-tw`）。Gemini API 语言表写的是 `cmn`。填错是 400 的常见原因。

### 4.1 传统 Cloud TTS 是另一条产品线

[Cloud TTS 产品总览](https://docs.cloud.google.com/text-to-speech/docs) 里还有 Chirp、WaveNet、Neural2、Standard、Studio。它们和 Gemini-TTS **共用 Cloud 项目和 ADC，但不是同一套模型**。

打开顶栏对应独立页（不要在 Gemini-TTS 页里找传统声音）：

| | Chirp 3: HD | WaveNet / Neural2 / Standard / Studio |
| --- | --- | --- |
| 声音名 | `cmn-CN-Chirp3-HD-Kore`（短名仍选 Kore） | `cmn-CN-Wavenet-A` 这类 |
| Gemini 提示词 | 不发送 | 不发送 |
| SSML | 同步可用子集；流式不可 | 支持 |
| 流式 | 能 | 不能 |
| 双人 | 本 Demo 不做 | 本 Demo 不做 |

### 什么时候选旧不选新？

Gemini-TTS 强在演戏、双人、标签。传统 Cloud 强在 **把读法写成契约**。官方 SSML 就是为停顿、日期、电话、缩写、需屏蔽的文本准备的。

| 需求 | 选 | 本 Demo |
| --- | --- | --- |
| 验证码必须逐字、日期必须像日期 | 传统 + `<say-as>` | WaveNet / Standard「独有 · 验证码与日期」 |
| 停顿必须是 400ms | 传统 + `<break time>` | 各传统页 SSML；Studio「写死的句间停顿」 |
| 某个词必须某种发音 | 传统 + `<phoneme>` / `<sub>` | Chirp「独有 · 逐字与 IPA」 |
| IVR / 通知，不要发挥 | 传统：按 text/SSML 合成 | 对照 Gemini 页「验证码只能靠提示词」 |
| 演戏、笑声、双人播客 | Gemini-TTS | 留在 Gemini 页 |
| 账单按字符、或用 WaveNet 免费额度 | 传统 Cloud 价目 | 数字以 [Cloud TTS 定价](https://cloud.google.com/text-to-speech/pricing) 为准；Studio / Chirp 是另一档，不是「一律更便宜」 |

一键对照：Gemini 页「对照 · 验证码只能靠提示词」→ WaveNet 页「独有 · 验证码与日期」→ Chirp 页「独有 · 逐字与 IPA」。出处：[声音与语言表](https://cloud.google.com/text-to-speech/docs/voices)、[Chirp 3: HD](https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd)、[SSML](https://cloud.google.com/text-to-speech/docs/ssml)、[Cloud TTS 定价](https://cloud.google.com/text-to-speech/pricing)。

### 4.2 一段里夹着中日英，怎么念才比较自然？

这不是同一个开关。**标签要包住那段字，不是加在全文后面。** 右侧下拉框仍是默认声：没被 `<voice>` / `<lang>` 包住的句子都走它。

SSML 本身是给停顿、日期、电话、缩写、发音用的标记语言，不是「混语专用」。混语只是其中一种用法：

| 做法 | 音色 | 官方含义 |
| --- | --- | --- |
| 只选一把默认声，不写标签 | 一种 | 整段按该声的语言来念，外语容易串音 |
| `<lang xml:lang="en-US">英文</lang>` | **尽量同一把声** | 同声换语，尽力而为；**日文汉字不支持**，会当中文念 |
| `<voice name="ja-JP-Wavenet-A">日文</voice>` | **换成另一把声** | 换人。WaveNet 没有「同一把 A 自动说日语」 |
| Chirp：`<voice name="en-US-Chirp3-HD-Kore">` | **同一短名、换 locale** | 官方格式就是 `locale-Chirp3-HD-Kore`，要你写明语言，不会自动识别 |
| Gemini-TTS：一把 Aoede，语言码留空 | **同一把声，自动识别** | 传统路径没有这一档 |

所以：传统 TTS **不能**像 Gemini 那样「选一个音色，混语全自动」。WaveNet 换语言 ≈ 换人；Chirp 可以用同一个 Kore 短名换 locale，但仍要在片段上写明 `en-US-…` / `ja-JP-…`。

| 你在哪一页 | 正确做法 | 不要做 |
| --- | --- | --- |
| Gemini-TTS（Vertex / Gemini API） | **语言代码留空**，让模型自动识别；用 3.1；语气写明「中文普通话、英文英语、日文日语，专有名词按原文读」 | 把整段锁成 `cmn` / `cmn-CN`，英文和日文容易被按普通话念 |
| Gemini-TTS 但入口是 Cloud TTS | Cloud **必须**填一个主 locale（如 `cmn-CN`） | 不要以为和 Vertex 一样可以留空；混语效果通常更差 |
| Chirp 3 HD | 主声音仍是 `cmn-CN-Chirp3-HD-Kore`；英文、日文用 SSML `<voice name="en-US-Chirp3-HD-Kore">` / `ja-JP-…` 换 locale。关流式 | Chirp SSML **没有** `<lang>`，乱写会被忽略；提示词不会演戏 |
| WaveNet | 用 `<voice name="en-US-Wavenet-D">`、`<voice name="ja-JP-Wavenet-A">` 换到该语言的声音 | 官方写明：`<lang>` **不支持带汉字的日语**，会按中文来念 |
| Neural2 / Studio / Standard | 同样用 `<voice>` 换到该语言存在的传统声。Neural2 的 `<voice>` 不能切到 WaveNet | 不要用一把英语声硬读汉字和假名 |

长文分段仍然是**同一把声音**多次请求，不会按语言自动换声。要换语言，请写进这一次请求的 SSML，或自己按语言拆开发两次。

出处：[Gemini 语言自动识别](https://ai.google.dev/gemini-api/docs/speech-generation#supported-languages)、[SSML `<lang>` / `<voice>`](https://cloud.google.com/text-to-speech/docs/ssml)、[Chirp 3 HD SSML 子集](https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd)。

---

## 5. 模型怎么选

| | 3.1 Flash TTS | 2.5 Flash TTS | 2.5 Pro TTS | 2.5 Flash-Lite |
| --- | --- | --- | --- | --- |
| 定位 | 新、可控、标签更好 | 快、省 | 质量、长内容 | 更省、单人 |
| 单人 | 能 | 能 | 能 | 能 |
| 双人 | 能 | 能 | 能 | **不能** |
| Gemini API 流式 | 能 | 不能 | 不能 | 无此入口 |
| Vertex / Cloud 流式 | 能（3.1 多在 global） | 能（视区域） | 能（视区域） | 能（视区域） |
| Gemini API 模型 ID | `gemini-3.1-flash-tts-preview` | `gemini-2.5-flash-preview-tts` | `gemini-2.5-pro-preview-tts` | 无 |
| Cloud / Vertex 模型 ID | 同左（3.1 仍带 preview） | `gemini-2.5-flash-tts` | `gemini-2.5-pro-tts` | `gemini-2.5-flash-lite-preview-tts` |
| 输入 / 输出 token（模型页） | 8192 / 16384 | 8192 / 16384 | 8192 / 16384 | 8192 / 16384 |

模型下拉来自 2026-09-10 的文档快照。**列表里有，不代表你的账号、地区、配额一定能调用。** Preview 会变。

---

## 6. 声音分类：官方原生支持什么？

**原生支持的是 30 个 `voice_name`，不是「男声 / 女声 / 少年 / 老年」这种档位 API。** 工作台里的女声、男声筛选，只是按 Cloud 声音表的 Male/Female 标注帮你挑名字。

| 分类 | 官方是否原生支持 | 你在 Demo 里怎么做 |
| --- | --- | --- |
| 预置声音 30 个 | 支持。请求字段是 `voice_name` | 下拉框选择 Kore / Puck 等 |
| 女声 / 男声 | **部分支持**：Cloud 声音表标注 Male/Female（当前快照约 14 女 / 16 男）；API **没有** `gender` 参数 | 用「全部 / 女声 / 男声」筛选；发出去的仍是一个声音名字 |
| 少年 / 壮年 / 老年 | **不支持**。没有 age 枚举，也没有童声档 | 选接近的风格词，把年龄写进语气 |
| 传统 TTS 的年龄 | **同样没有 age 枚举** | Chirp：换 Leda/Gacrux。WaveNet：换 A/B/C/D。pitch 是音高 |
| 自定义音色 / 克隆 | 不支持 | 做不到 |
| 行内标签 `[shouting]` | 支持，无封闭名单；3.1 更稳；建议英语标签 | 写在台词里，效果要试听 |

最接近「年龄」的官方形容词只有两个：

- **Leda**：Youthful（年轻感），**不是**「少年声」档位
- **Gacrux**：Mature（成熟感），**不是**「老年声」档位

其余声音的描述是 Bright、Firm、Upbeat 这类风格词。官方提醒：不要强迫一个低沉男声去演小女孩口吻；**反过来也一样**——选了女声，却把人设写成「黑社会头目」，模型常会按默认男角色去演，听起来就像男声。

正确写法：先锁声线，再写情绪。例如 `成年女性，保持女声音高和声线。语气凶狠，像女当家在发号施令。` 工作台已在发给模型的提示里加上「声线锁定」；冲突时，「预览请求」和语气框下方会警告。一键对照：场景样例里的「女声也可以凶」和「男声黑帮头目」。

工作台示例「女声 · 坚定」「男声 · 活泼」「年轻感（提示词）」「年长感（提示词）」就是为了让你听清：**在 Gemini 页，性别靠选声，年龄靠提示词。** 传统页见下一小节。

### 6.1 传统 TTS 怎么控年龄？（和 Gemini 不是同一套逻辑）

**三条路径都没有「少年 / 壮年 / 老年」请求字段。** 差别在于你还能动什么：

| | Gemini-TTS | Chirp 3: HD | WaveNet / Neural2 / Standard / Studio |
| --- | --- | --- | --- |
| 换说话人 | 换 30 个短名。Leda=Youthful，Gacrux=Mature（风格词） | **只能靠这个。** 同一套 30 个短名，请求是 `cmn-CN-Chirp3-HD-Leda` | 换声音名。普通话 WaveNet/Standard 官方各仅 A–D 四人 |
| 提示词演年龄 | 有效（仍不保证） | **无效**，提示词不会发送 | **无效** |
| 音高 pitch | 无此字段 | [声音类型总览](https://docs.cloud.google.com/text-to-speech/docs/voice-types) 写明不支持。本 Demo 不发送 | `AudioConfig.pitch` -20～+20 半音。更尖 ≠ 官方童声档 |
| 性别 | 选 name；无 gender 字段 | 声音表 Name+Gender | 声音表 SSML Gender；未指定 name 时可用 `ssmlGender` 作偏好 |

对照听：Gemini「年轻感 / 年长感」→ Chirp「选声 · Leda / Gacrux」→ WaveNet「女声 D」和「音高 +4」。传统页的声音下拉是官方全表快照，**按语言筛选**；Chirp 是 30 个短名 × 声音表里的全部 locale。出处：[Chirp 声音表](https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd)、[Cloud 声音全表](https://cloud.google.com/text-to-speech/docs/voices)、[AudioConfig](https://cloud.google.com/text-to-speech/docs/reference/rest/v1/AudioConfig)、[创建音频](https://cloud.google.com/text-to-speech/docs/create-audio)。

### 6.2 业务怎么选型？

入门指南页有对照表。粗规则：

- 要演戏、标签、双人 → Gemini-TTS
- 要流式高保真助手、不要发挥 → Chirp 3 HD
- 要验证码/日期/400ms → WaveNet 或 Standard + SSML
- 英语通知 + Neural 音质 → Neural2（官方无普通话 Neural2）
- 英语有声书写死停顿 → Studio（高档字符价，无普通话）

测通后，每一引擎页底部有「接入你们系统」官方链接。克隆音色、Long audio、双向流式、Studio 实验性双人组见入门页「本产品还有、网页 Demo 故意没接」。News / Polyglot / Casual 在 Neural2 页按语言筛选即可。设备补偿和音量在 WaveNet / Neural2 / Standard / Studio 第 02 步。Gemini Batch 见第 8 节与 `batch_demo.py`。Live 对话是另一个产品。

官方 Gemini API 提供 30 个预置声音。名称是希腊神话/星名，描述是选角提示：

Zephyr 明亮 · Puck 活泼 · Charon 知性 · Kore 坚定 · Fenrir 兴奋 · Leda 年轻 · Orus 坚定 · Aoede 轻快 · Callirrhoe 随和 · Autonoe 明亮 · Enceladus 气声 · Iapetus 清晰 · Umbriel 随和 · Algieba 顺滑 · Despina 顺滑 · Erinome 清晰 · Algenib 沙哑 · Rasalgethi 知性 · Laomedeia 活泼 · Achernar 柔软 · Alnilam 坚定 · Schedar 平稳 · Gacrux 成熟 · Pulcherrima 直率 · Achird 亲切 · Zubenelgenubi 随意 · Vindemiatrix 温柔 · Sadachbia 生动 · Sadaltager 博学 · Sulafat 温暖

语言：Gemini API 文档列出 70+ 种，可自动检测。入门指南页有中文、英语、日语、Filipino 对照。各引擎页「多语言」另有韩语、西班牙语、法语、粤语、德语等，**只列出该引擎能选的 locale / 声音**（例如 Studio 不放普通话，Neural2 不以普通话为主声）。列表里有某种语言，不等于该语言在所有声音、所有区域上效果都一样好。

---

## 7. 提示词：怎样「导戏」

官方把高质量提示拆成几块。你不必每次写满，但要知道它们的分工。

1. **Audio Profile**：这是谁在说话（电台 DJ、书店店员、新闻主播）
2. **Scene**：在什么环境、什么心情
3. **Director's Notes**：语气、口音、节奏、呼吸。官方认为这是最不该省的一块
4. **Transcript**：真正要读出口的字
5. **Audio tags**：只调整其中几句的演法

工作台把 1–3 收进「语气 / 口音 / 节奏 / 场景」，把 4–5 放进编辑框。后端会强制加上一句「只朗读台词、不要朗读导演说明」，并用 `TRANSCRIPT:` 切开。这是为了降低「把提示词念出来」的概率，不是官方 SDK 的必填字段。

### 写得好 vs 写得含糊

较差：`好一点`

较好：`温暖、自然，像在向一位刚认识的朋友介绍自己，不要播音腔。`

更好：把口音写成具体地点，把节奏写成「句与句之间留出思考的停顿」，让台词本身也像这个人会说的话。官方强调：**谁在说、说什么、怎么说，三者要一致。**

### 双人提示

可以分别规定两个人：`Host 好奇而轻快；Guest 耐心且亲切。` 台词里的名字必须和配置的角色名一致。

---

## 8. 流式、长文分段、Batch：三件不同的事

很多人把这三者混成「处理很多文字」。请分开记：

| | 流式 | 长文分段 | Batch API |
| --- | --- | --- | --- |
| 解决什么 | 先听到声音，少等 | 单次请求放不下的长文 | 很多独立短请求、不赶时间 |
| 谁来切 | 模型边生成边下发音频块 | **本 Demo 应用层**按标点/行切开 | 你提交一个云端任务 |
| 计费形态 | 仍然是普通生成 | 每一段都是一次普通生成 | 官方 Batch，价通常不同 |
| 工作台有没有 | 有 | 有，需勾选 | 没有；用 `batch_demo.py` |

六个引擎页各自有一条「长文 · 分段拼接」样例，点进去会勾上分段。不要到 Gemini 页去测 Chirp 的长文，也不要把 Studio 页当成验证码试验场。

长文分段的后果（官方也建议长音频自己切）：

- 会重复发送风格提示
- 接缝处可能顿一下，声线可能漂
- 本 Demo 不插入静音、不做交叉淡化
- 一次最多 20 段，是 Demo 自己的保护，不是官方字段

Cloud 还有自己的硬限制（文档表格）：prompt 与 text 各最多约 4,000 UTF-8 字节，合计约 8,000；输出音频大约最多 655 秒，超长会被截断。多人章节的正文和表格曾出现过不一致，本项目按表格校验，若端点仍拒绝就再缩短。

---

## 9. 音频格式（你下载到的是什么）

Gemini API / Vertex 这条路径，得到的是 **PCM：单声道、16-bit little-endian、24 kHz**。本 Demo 在浏览器里包成 WAV，才能双击播放。

Cloud 非流式还可以要 MP3 或 OGG Opus。本 Demo 的限制是：这两种格式**不能**和流式、长文分段一起用，因为分段拼接按 PCM 实现。

不要把原始 PCM 直接改名为 `.mp3`。那会「有文件但全是噪声」。

---

## 10. 从零到会用的知识顺序

1. 本页第 0–1 节 + 工作台 5 个练习
2. [README.md](README.md) 的启动、排错、成本
3. [语音生成总指南](https://ai.google.dev/gemini-api/docs/speech-generation)（先看 Limitations 和 Prompting）
4. 你实际在用的[模型页](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-tts-preview)
5. 需要 Cloud 时再读 [Gemini-TTS](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts)
6. 写自己的脚本时对照 [Python SDK](https://googleapis.github.io/python-genai/) 和 `examples/quickstart.py`
7. 价格与配额永远看[定价](https://ai.google.dev/gemini-api/docs/pricing)和[限流](https://ai.google.dev/gemini-api/docs/rate-limits)，不要看播放器上的秒数

命令行最小例子：

```bash
.venv/bin/python examples/quickstart.py
```

它和官方 Cookbook 是同一条 GenerateContent 路径：选模型、选声音、保存 WAV。工作台只是在前面加了校验、分段、流式播放和中文说明。

---

## 11. 验收清单（给「我是不是真会了」用）

没有 ADC 时：

- [ ] 能打开工作台，载入示例，看到字符数和 UTF-8 字节数
- [ ] 「预览请求」能显示导演说明、`TRANSCRIPT` 和分段数量
- [ ] 入门指南和官方资料页能打开，链接能点到 Google 域名

已配置 ADC 与项目时：

- [ ] 第一段中文能出声，下载的 WAV 能在系统播放器打开
- [ ] 只换声音，音色变了
- [ ] 用女声/男声筛选后，请求里仍是声音名字，没有 gender
- [ ] 年轻感 / 年长感示例能听出表演差异，并理解这不是官方年龄档
- [ ] 只改语气，表演变了
- [ ] 双人示例能听出两个角色
- [ ] 3.1 + 标签能听出低语或笑声（允许偶尔失败，再试一次）
- [ ] 故意写错对话格式（去掉 `Host:`）时，预览会用中文拒绝，而不是把请求打到云端
- [ ] 把 Gemini 2.5 打开流式时，界面会禁止或后端拒绝

你还应该能用自己的话回答：

- TTS 和 Live API 差在哪里？
- 为什么提示词可能被念出来？
- 长文分段为什么可能在接缝处「换了一个人」？
- 为什么列表里的模型不一定能在你的账号上调用？
- 女声/男声和少年/老年，哪些是官方原生支持的？

如果这四句都能答，你已经比「会点生成」更懂 Gemini TTS。

---

## 12. 常见误解

| 误解 | 更准确的说法 |
| --- | --- |
| 「Gemini 都能说话」 | 普通文本模型和 TTS 模型不同。TTS 模型不能聊天，只能读你给的稿。 |
| 「选了坚定的声音就会一直坚定」 | 声音是起点，提示词和台词会一起影响表演。 |
| 「流式更便宜」 | 流式主要改的是你何时开始听，不一定改计费方式。 |
| 「分段 = Batch」 | 分段是本 Demo 循环调用；Batch 是官方异步任务，价和配额都不同。 |
| 「返回 200 就等于读完了」 | 仍要听末句。模型可能漏字、提早结束或质量漂移。 |
| 「Cloud 和 Gemini 是同一个开关」 | 身份、模型 ID、语言代码、可用区域都不一样。 |
| 「官方有少年、壮年、老年档」 | 没有。原生只有 30 个 `voice_name`；Cloud 表另标 Male/Female，但仍不是请求字段。年龄感靠提示词。 |
| 「选了女声，语气写成黑社会头目，就一定是女声」 | 不会。人设默认是男的，模型常会改声线。先写「成年女性，保持女声线」，再写凶狠。 |
| 「填了中文就一定用普通话发音」 | 可指定语言/口音；不填时靠模型识别，仍可能串音。 |
| 「官方试听过的声音，我这边一定有」 | Preview、地区、账单、IAM、配额都会挡。 |

---

## 13. 接下来

- 继续试验：同一句台词 × 三个声音 × 两种语气，你会很快建立直觉
- 把工作台「导出本次配置」存下来，方便对照（不含密钥；相同配置也不保证相同音频）
- 要自己写代码：先跑 `examples/quickstart.py`，再读 `tts.py`
- 要批量：读 README 第 12 节，确认计费后再运行 `batch_demo.py`
- 要核对原文：打开工作台「官方资料」页，或直接读 [docs/official_sources.md](docs/official_sources.md)
