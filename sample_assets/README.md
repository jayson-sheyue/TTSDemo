# 场景样例

这些 JSON 是各引擎页「本页场景样例」的一键导入源。点一下会填入该页能用的字段，再点「生成语音」。

Gemini 样例在教：**声音名字决定声线，语气只导演表演。** 不要用「黑社会头目」这种默认男性身份去驱动女声。传统 Cloud 样例只出现在 Chirp / WaveNet 等对应页，不会出现在 Gemini-TTS 页。

各页的「高阶 · 中日英混语」教的是同一段里多种语言：**Gemini 留空语言码**；Chirp / WaveNet 用 SSML `<voice>` 换声。日文汉字不要用 `<lang>`。

各传统页的「独有 ·」样例教的是 **为什么选 SSML 而不选 Gemini 提示词**：验证码逐字、日期、电话、IPA、写死的停顿。Gemini 页「对照 · 验证码只能靠提示词」是同一段 IVR 的提示词版本。

「年龄怎么控」分组：Gemini 仍用提示词；Chirp 只换 Leda/Gacrux；WaveNet 换 A/B/C/D，另有一条 `pitch=+4` 证明音高不是年龄档。

「业务选型」分组：播客/品牌旁白、对话助手、英语客服、低成本通知、广播叙述。配合入门页对照表。

「功能怎么测」分组：各引擎都有长文分段。Gemini 另有流式、Cloud 结构化双人；Chirp 有流式助手（不开 SSML）；WaveNet / Neural2 / Standard 有语速或音高。不适合的场景不会出现在该页（例如 Studio 不放验证码，Chirp 不放提示词演戏）。

「多语言」按页只放该引擎能选的 locale / 声音：Gemini 可留空语言码；Chirp 换 locale 保留短名；WaveNet/Standard 换 `ko-KR` / `yue-HK` 等训练声；Studio 放英/法/德/西叙述声，不放普通话。

## 字段

| 字段 | 作用 |
| --- | --- |
| `id` / `title` / `group` | 界面分组和按钮文案 |
| `engine` | 只出现在对应顶栏页：`gemini` / `chirp3-hd` / `wavenet` / `neural2` / `standard` / `studio` |
| `note` | 导入后显示的写法说明 |
| `config` | 与该页导出配置相同的字段 |

新增样例：把 JSON 放进本目录，并在 `index.json` 的 `samples` 列表里登记文件名。
