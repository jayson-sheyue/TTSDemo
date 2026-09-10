# Cloud TTS 声音全表快照

`cloud_voices.json` 来自官方 [Supported voices and languages](https://cloud.google.com/text-to-speech/docs/voices)（核查日期写在 JSON 的 `checked` 字段）。

- WaveNet / Neural2 / Standard / Studio / News / Polyglot / Casual / 旧版 Chirp HD：逐条收录，工作台按**语言**筛选后下拉。
- Chirp 3: HD：不把 `locale × 30 短名` 展开成一千多条。短名仍是 30 个，locale 在 `chirp_locales`。
- 不含 Instant Custom Voice / Custom Voice（需要克隆密钥或 AutoML 模型）。
- 本 Demo **不调用** `voices.list`；账号里实际可用的声音仍以该 API 与区域为准。
