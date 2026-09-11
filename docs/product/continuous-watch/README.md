# 持续关注：首批内容审阅稿

2026-09-11 · CW1 · **用户已确认，网页与 MCP 实现完成**。原稿保留内容核对口径；实际发布数据以 [watch.json](../../../backend/knowledge/content/watch.json) 为准，[验收与部署状态](../../validation/2026-09-11-continuous-watch.md)单独记录。

页面名称：**持续关注**。副标题：**跟踪重要模型与项目，看清能力、版本和演进。**

首批 27 个跟踪主体，分为五组。一个模型族可以有多个版本，一个 Skill 仓库可以展开多个技能；它们不额外计为主体。这里的 27 项与线上数据库原有 27 项并非同一集合。

## 首批展示清单

| 模块与完整文案 | 数量 | 具体收录对象 | 用户能直接看到什么 |
| --- | --- | --- | --- |
| [模型](models.md) | 9 | GPT、Claude、Gemini、Kimi、GLM、DeepSeek、Qwen、MiniMax、Seed / Doubao | 模型族简介、重要版本与并行分支、具体变化、获取入口、逐点解读 |
| [工具](tools.md) | 4 | ComfyUI、Ollama、vLLM、Docling | 处理什么、输入与产物、运行方式、重要更新、项目资料 |
| [Agent](agents.md) | 7 | Codex、Claude Code、Gemini CLI、OpenHands、Browser Use、OpenClaw、Pi | 工作入口、执行范围、扩展方式、版本变化与底层组件关系 |
| [Skill](skills.md) | 3 | Superpowers、Anthropic Skills、Vercel Agent Skills | 仓库关注度快照、具体代表技能、技能内容、宿主与许可说明 |
| [Harness](harnesses.md) | 4 | DeepSeek Harness、Deep Agents、Claude Agent SDK、OpenHands Software Agent SDK | Agent 如何运行、状态如何保存、怎样扩展、当前发布状态与重要变化 |

## 实际页面文案与阅读顺序

五组目录依次为：**模型 · 工具 · Agent · Skill · Harness**。每组先展示本稿各对象的“一句话介绍”，点击对象展开其具体表格与 FieldToFit 解读。模型按“族 → 分支/版本”展开；Skill 按“仓库 → 代表技能”展开。第一屏不同时摊开所有版本表。

每个对象的内容顺序固定为：名称和简介 → 本次值得看的 1–2 点 → 版本或内容表 → 官方材料 → 关联对象。详情中的“主要变化”是材料事实；“FieldToFit 解读”是基于材料的编辑判断，均分点表述。页面目录显示五组及各组对象数，不做质量总排名。

“近期动态”承担某次发布的解读；“持续关注”保留对象的长期入口、版本关系和资料。动态通过关联编号指向对象，避免重复刊登整篇文章。CW-M01 / T01 / A01 / S01 / H01 是本稿内容编号，**不是 REQ 编号；现已作为 curated_watch 的内容 ID**。D-01 等沿用[当前动态记录](../launch-selection.md)。

## 给人的内容与给 AI 的材料

本稿已写出中文事实摘要、编辑解读、版本关系、原始链接和核验边界。后续接入 For your AI 时，这些内容应来自同一份审核材料，保留：对象及别名、类型、具体版本、来源网址与标题、事实与解读的区分、核验时间、发布日期及其精度、与其他对象的关系。

内容研究只阅读一手材料，**没有保存完整原文快照、安装或实测这些项目**。后续实现已新增 curated_watch，提供同源整理数据。链接应标记为 link_only；未知日期保留空值及说明。不能把官网能力描述写成 FieldToFit 的实测结果。

## 数据口径与还需补齐的材料

- 核验日统一为 2026-09-11。日期列明确区分：正式发布日、版本更新月份、文档快照日期、未知。不能把模型名中的数字或 GitHub 文件更新时间推断成首发日期。
- 版本表是重要节点摘选，不声称穷尽历史。不同分支并行展示，不写成全部版本彼此替代。
- Skill Star 为本次检索到的 GitHub 页面近似值；仓库 Star 不属于单个技能。没有连续快照，近 7 天增长不展示。
- 首发日期尚未核实的模型包括 GPT 本稿分支、Kimi K3/K2.7-Code、GLM 本稿分支、DeepSeek 本稿分支、Qwen3.8-27B、Seed2.1。正文可展示已核实内容及“发布日期待核”，不靠填日期凑完整。
- Gemini 的月份来自模型页面“Latest update”；Kimi K2.5 的 1 月 29 日是模板修订日；OpenClaw 的标签日期与发布记录日期不同，正文已拆开。
- Claude Agent SDK 与 OpenHands SDK 本轮采用文档快照，未确认包版本；不把当前能力伪装为本次新增。Skill 尚未固定 commit，正式入库时须补实际修订号，并刷新关注度快照。
- API 可用性、开源权重、产品订阅是分别记录的事实。本稿没有核实的价格、地区权限、硬件下限不填写。

## 本稿与当前项目的关系

本稿完成后，用户已授权更新网站。现在已实现五类网页、目录、资料导出与 curated_watch；原有数据库不变。具体版本及发布证据见[验收记录](../../validation/2026-09-11-continuous-watch.md)，REQ 以[总表](../requirements.md)为准；运行维护与日常客户端验收没有因此关闭。
