# 2026-09-17 · Gemini Live 内容与原文取材验收

用户确认本批 Gemini 3.8 Live 上站；应用交付版本 v1.5.2。Diagram Design 本轮只核对并解释，不发布。Hermes 原文候选保持隔离，关注更新只登记方案。

## 内容范围

- 新动态 D-16：2026-09-15 官方发布，2026-09-17 核验补录；异步工具、Extended Thinking 和具体接入资料逐点说明。
- 更新 CW-M03：补充两款 Live 分支，保留原 Flash 表格、来源和 2026-09-11 核验边界。
- Live API overview、Develop with agents 两份 Google 文档保存完整文章正文的 Markdown 快照，保留代码和绝对来源链接；CC BY 4.0 正文、Apache 2.0 代码示例及转换说明随材料提供。页面更新日分别为 2026-09-15 与 2026-09-01，抓取日期单独记录；不将旧 Skill 文档当作此次新发布。
- 博客、模型卡、示例仓库仅链接，未取得或未核定的正文不冒充全文。未安装 Skill、未调用模型，不宣称验证了账户开放、延迟或任务成功率。公告与文档语言数量不同，因此编辑文案不提供统一确定数字。

## 发布与验证

以下结果在实际操作后补齐，草稿或本地版本不代表生产已部署。发布前私密集合备份、草稿与预览保存在忽略目录 output/operations/v1.5.2-release/；不提交提案附件或管理备份。

| 检查 | 结果 |
| --- | --- |
| 管理预览 | D-16、CW-M03 的 For you / For your AI 预览通过；桌面 1440×1000、手机 390×844 无全页横向溢出和页面错误 |
| 草稿校验 | 首轮 CW-M03 的相对新闻锚点不符合既有白名单，改为正式站 HTTPS 链接后通过；未修改应用校验规则 |
| 内容发布 | 逐项复核并发布，日报 A 提案回写 published；原 15 条动态不变，持续关注仅 CW-M03 变化，Hermes 候选未发布 |
| 人读页面 | D-16、CW-M03 锚点、Live 版本表、桌面／手机和复制交接通过；For your AI 搜索命中 Gemini 新动态 |
| 公开 MCP | 两集合与 HTTP 结果一致；统一搜索命中 D-16 / CW-M03。两对象各有两份正文，分别分两段重建，与已审核原文及 content_hash 一致；资料包包含全部已存正文，变化流可读取本批事件 |
| 文本范围 | 两份独立文档分别 6,248、5,981 字符；在动态及关注对象均可读取，不把两个对象中的相同快照计算为四份独立文档 |
| 回归与构建 | 81 passed；内容管理、新闻、持续关注、统一检索、资料包、编辑流程相关测试。TypeScript / Vite 构建、版本一致性和仓库检查通过 |
| 生产版本 | /api/health 返回 v1.5.2，MCP initialize 返回 1.5.2；Vercel 既有 FieldToFit 项目部署，正式域名 fieldtofit.top |

验证脚本首次分别误用 sha256 / full_text_materials 字段，按服务既有 content_hash / readable_materials 字段修正后完整验收通过；不是应用接口故障。详细原始结果见忽略目录 public-verification.json、preview-browser.json、browser-public.json、final-runtime.json；源码仅导出公开集合，不含管理备份、私密批次及凭据。

## 实际客户端的第二日观察

此项发生在本批 Gemini 发布前，不能写成 Gemini 的自主客户端问答实测。真实 Codex 客户端只调用 FieldToFit MCP，共 8 次：昨日动态修订已变化，旧修订请求产生预期冲突，随后按当前修订读取 D-14 / D-15；CW-S04 固定材料从 offset=12000 继续读取 2313 字符末段。没有 shell、网页或其他 MCP 调用。原始证据位于 output/briefings/2026-09-17-evidence/client-index.json、client-events.jsonl 和 client-answer.md。

第二日采集记录：北京时间 07:07–07:10，55 项中 41 成功、9 未完成、1 错误、4 延期；GLM 触及预算上限，MiniMax / xAI / Qwen / MiMo 延期。scheduler_header 不能单独证明平台定时日志；三日连续成功、08:00 准时日报和 9 月 22 日周维护仍未通过。
