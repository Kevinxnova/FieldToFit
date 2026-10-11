# 全站英文与双语内容维护

REQ-23 全站英文于 v1.8.26 完成，v1.8.27 补齐语言切换等待与失败保护。所有者确认开发验证，选择继续本地逐项翻译，并明确授权“更新并部署”；当前正式交付及实际检查范围见[验收记录](../validation/2026-10-11-complete-english.md)。译文已由开发助手逐项复核，所有者英文全文最终审读仍待执行。

## 阅读、分享与 AI

中文沿用既有地址；英文使用 `/en/for-you`、`/en/for-your-ai`、`/en/news/<id>`、`/en/watch/<id>`、`/en/maps/<slug>` 等地址。地址决定语言，直接打开英文链接也得到英文服务端正文和分享信息。切换保留查询、锚点、组件内筛选及未保存输入。新语言响应到达前只显示加载状态，失败显示错误，不能显示、复制或下载上一语言数据。正文返回后恢复锚点或滚动位置；读者开始新的点击、滚动或键盘操作时取消待恢复位置。后台源稿保持原语言且不重置未保存输入。账户与应用案例范围保持。

公开 HTTP 请求用 `lang=en`，MCP 工具在 `arguments` 中加入 `"lang":"en"`。省略参数沿用中文默认，不新增 MCP 地址或读取权限。

```json
{"name":"curated_watch","arguments":{"id":"CW-T16","lang":"en"}}
```

网页、复制、下载、资料包与 MCP 使用相同公开修订的译文。正文缺译或失效时返回明确错误，不能回退中文或隐藏条目冒充完成。用户输入、真实名称、代码、URL、原始材料、原帖、引文、许可证与定位偏移保留原值；原文显示明确标识。本站图文说明提供英文，上游图片保留证据原貌。

## 新内容和实质修订

1. 按[内容管理](management.md)整理并保存中文源稿。原文字段保持输入语言。
2. 在“英文正文审核”展开逐项对照，填写全部英文，核对事实、数字、单位、版本、日期、出处和限制条件。
3. 写审核说明，勾选逐项核对，确认英文审核。保存英文草稿本身不代表审核完成或发布。
4. 生成双端预览，分别检查中文与 English preview 中 For you 的真实展示和 For your AI 的公开字段。
5. 核对公开范围和材料依据，填写变更原因后明确发布。

译文由服务器绑定源文指纹和草稿版本。源文变化后变为待更新；并发编辑、失效预览、缺译、未确认或已撤回修订会阻止发布。审核备注保持私密。重新确认相同译文不会刷新公开“内容更新”日期；真正改变已审英文会产生相应公开修订。合并、旧材料库发布、采集转正式材料、公开更正及维护说明也要求核对最终中英文。

## 本批存量与后续回归

`backend/knowledge/content/locale/en.json` 和 `frontend/src/locale/en.json` 维护同一份已复核文本；`baseline.json` 仅保存本批存量源稿的指纹，包括可访问历史，不能给新的任意内容自动授权。每个对象的新译文由服务器保存于自己的内容修订，历史读取使用当时译文。源稿变化不能仅靠共享词条继续沿用旧审核。

本地译稿工具只生成候选，不审核、不发布；无需 MiniMax 或其他外部服务。`local-drafts.swift` 可用已安装的 macOS Translation 生成初稿，`prepare-local.py` 保护字面事实，但仍需逐项阅读和纠正。批量词条录入工具也不授予审核状态。

维护时对生产备份的隔离副本执行以下流程，禁止把含私密草稿的数据库或 output 提交到仓库：

```bash
node scripts/locale/extract-ui.mjs > output/operations/req23-english/ui-inventory.json
python scripts/locale/inventory.py --snapshot /private/path/copy.sqlite3 --output output/operations/req23-english
python scripts/locale/check.py --inventory output/operations/req23-english/inventory.json --catalog backend/knowledge/content/locale/en.json --output output/operations/req23-english/facts.json
python scripts/locale/audit.py --snapshot /private/path/copy.sqlite3 --output output/operations/req23-english/public-audit.json
```

检查覆盖完整公开清单、可访问历史、缺译与汉字、数值、固定标识和 Markdown 链接；它不能证明自然语言含义完全一致。审读后再维护存量指纹，不能将清单工具生成的 baseline 直接当作人工确认。还须执行相关回归、`cd frontend && npm run test:locale`、前端构建及实际浏览器检查。补充文本、图文与文档提交遵循[发布规则](releasing.md)。
