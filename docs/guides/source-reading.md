# 原文阅读与审核

对应 [REQ-26-7／8](../../FieldToFit-PM.md#req-26-7)。v1.20.0原文阅读功能已于2026-11-10部署；生产正文必须按具体提案批准后，沿用保存、双语预览、提交复核、明确发布流程。

## 中文

OpenAI与Anthropic采用相同规则：标题直接说官方宣布的事实，摘要使用准确官方导语或摘译，不写泛化设问；正文使用署名短摘录，中文译文与原语分开标识。不要把旧「FieldToFit解读」复制进原文字段，或只换栏目标题。完整长文链接原始材料；摘录须保留必要上下文，不能删掉条件而扩大适用范围。

在既有动态中开启「原文阅读」，编辑标题、摘要和原文段落。每段填写来源编号、作者、原文位置、核对日期、逐字原文、中文译文与使用依据。按原文章节顺序排列；来源先登记在本条sources。现阶段文字支持英文或中文原语；英文有中文译文，中文原文在英文页明确标为中文。英文标题／摘要仍使用既有英文审核。原文、译文及图注都进入审核指纹；改动必须重新预览复核。

图注保留原文与中文译文。没有确认复用许可时，选择「链接原图」，保留真实HTTPS图片地址。嵌入使用既有 `backend/knowledge/content/report-figures.json` 资源登记：PNG地址、`kind: original`、`original_url`、`source_urls`、`license`、`rights_url`；图片随源码交付到 `frontend/public/report-figures/`。核对真实原图及授权后才能登记；旧重绘图没有original身份，不能冒用。编辑器填相同资源地址、复用依据和替代文字；不自动抓图或上传。图片加载失败时保留原图链接和文字说明。

原文模式的当前公开修订不再输出旧解读、补充评论、热点卡、旧配图或人工路线图；报告可以只保存稳定slug、报告日期与来源，正文复用本条source_reading。历史修订保留原样，可从修订记录展开。切换模式不删除旧数据库历史。新闻、报告、HTML、API、MCP及交接数据共享同一份公开投影，编号、原日期和URL保持。变更英文审核、来源或草稿版本使旧预览失效。新字段是可选兼容扩展，旧条目不自动迁移或发布。

## English

OpenAI and Anthropic use the same reading policy: concrete announcement titles, official leads or faithful translations, and attributed short excerpts instead of editorial questions or commentary. Keep necessary context and link the complete source. Never relabel existing editorial notes as quotations.

Enable source reading on the existing news record. Each block records its source ID, author, locator, check date, exact text and Chinese translation. English and Chinese source languages are supported; Chinese originals remain explicitly labelled on English pages. Titles and summaries continue through the existing English review. Quote, translation and figure-caption changes invalidate the reviewed source fingerprint.

Use original-image links when reuse permission is unverified. Embedded PNGs must be registered in the existing report-figure manifest with `kind: original`, `original_url`, `source_urls`, `license` and `rights_url`, with the asset shipped under the existing public figure directory. Legacy redraws cannot pass as original figures. The editor does not fetch or upload images. Image failure retains the original link and caption.

Current source-mode publications omit legacy editorial notes, cards, images and graph interpretations. Reports can retain only their stable slug and source/date records while sharing the news item's source-reading blocks. Historical revisions remain accessible. Web, HTML, API, MCP and handoff data use the same reviewed projection. IDs, event dates and links remain stable; existing records are not automatically migrated. Source reading was deployed on 2026-11-10; each content revision still requires specific approval and the existing publication workflow.
