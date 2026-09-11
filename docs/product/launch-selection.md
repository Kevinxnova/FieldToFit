# 首发内容与维护记录

2026-09-11 · 用户确认 P3 方案后实现。当前首发动态为 **10 条**，原 D-01～D-09 加入 D-10 DeepSeek-V4.1-Flash；完整发布内容见[新闻文件](../../backend/knowledge/content/news.json)。资源档案沿用数据库内已审核集合，新闻不是数据库草稿。

## CW1 持续关注内容更新

用户随后确认按模型、工具、Agent、Skill、Harness 展开“持续关注”。[CW1 具体内容稿](continuous-watch/README.md)已准备 27 个主体的简介、版本 / 技能表、分点解读和来源，**已获用户确认并接入网页 / MCP**，替代原先平铺资源档案作为主展示。原数据库 27 项移至折叠原文库，与本批主体不是同一集合。[本轮验收及部署状态](../validation/2026-09-11-continuous-watch.md)。

## P3 首次实现记录（CW1 前）

- 近期动态：本期速览最多 5 条一句话提要，发布与更新展示全部动态。
- 完整 FieldToFit 解读仅在对应动态中逐点展开，每点有标题、具体解释、原文位置及来源。
- 资源档案：持续维护对象材料，保留详情、原文、修订、资料包；关联条目保留编号和可读名称。
- 页内目录：桌面固定、手机展开，直达并展开具体条目，筛选与当前页数量同步。

## 内容实况与边界

DeepSeek-V4.1-Flash 官方模型卡已在本轮读到；解读围绕编码/解码分工和缓存共享。首次发布日期仍未知，展示核验日，不能自动把 2026-09-11 标成发布日。其他动态保留其来源日期，8 月内容明确为回顾。

每条 1–2 个实质解读点，根据具体材料说明值得读的内容；没有统一套话。当前动态保存中文整理、解读和一手入口，**原始文章覆盖是 link_only**，没有声称网站已存完整新闻原文或已实测外部产品。

此前 15 份资源候选中，GLM-5.3-Flash、Qwen3.8-Flash-Next、DeepSeek-V4.1-Flash 的官方模型卡作为新闻关联入口；Codex CLI、Claude Code、Gemini CLI、Deep Agents、LangGraph、OpenAI Agents SDK、Browser Use、Anthropic Skills、Ollama、vLLM、ComfyUI、Docling 为持续维护候选。候选名单不等于这些档案均已完成新一轮发布审核，本轮未批量替换数据库原有 27 项资源。

## 更新操作

1. 维护 backend/knowledge/content/news.json：稳定 D-ID，来源日期/核验日分开；逐点评价引用登记的 source ID。
2. 草稿 state=draft；经原文与文案复核后才设 published。撤回改 withdrawn，后续读取不再提供正文。
3. 运行内容校验、相关测试和网页检查，经 Git 审阅后部署；新闻随软件部署生效。公开修订仅由公开字段计算，私有备注不影响它。
4. API `/api/v1/platform/news` 与 MCP `curated_news` 同源，支持 q/id/revision；指定旧修订遇到变化返回 409，重新读当前集合。当前不提供新闻历史正文快照。
5. 当前日采集仍运行既有来源流程；将新动态接入后台 AI 整理、自动原文入库与独立新闻发布，是后续 REQ-F-04 / O-01 工作。不能把文件里的核验日期冒充每日自动核验成功。

[本轮验收](../validation/2026-09-11-reading.md) · [REQ](requirements.md)

## 持续关注维护

审核后维护 backend/knowledge/content/watch.json，保留稳定 CW-ID、表格、解读、来源及核验口径。state 为 draft / published / withdrawn；只返回 published。网页与 curated_watch / GET /api/v1/platform/watch 同源，支持 q、id、type、revision。修订变化返回 409，撤回对象返回 404，失效站内关联转为不可用说明。更新后运行相关测试、前端构建及浏览器验收再部署；不是后台自动发表。
