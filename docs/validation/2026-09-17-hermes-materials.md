# Hermes：只用 FieldToFit MCP 的原文取材对照

日期：2026-09-17（北京时间）。关联 REQ-4-1、REQ-4-2、REQ-9-3。应用仍为 v1.5.1；这是内容验证，不是新版本发布。

## 结论及网站状态

- 真实问题存在：生产 CW-A08 的项目介绍、版本表、FieldToFit 解读可读，但 README、发布记录、LICENSE、文档入口四项均为 `link_only`，正文 0 字符。
- 现有 `curated_material` 和 `curated_bundle` 能提供原文，不需要再新建 MCP 工具。问题在这项内容没有保存正文，不能用接口验收通过代表所有对象材料齐全。
- 在临时 SQLite 中补入 5 份允许收录的完整固定版本文件和一份发布摘录后，真实 AI 得到了原简介不能支持的迁移、记忆、技能机制答案；新增事实与实际读取段落逐项核对通过。
- **“所有材料完整正文齐备”未通过**：GitHub 发布说明的完整转载许可尚未核实，本次只保留 17 个英文词的两条标题摘录。其他文档页面、迁移实现和运行效果没有覆盖。
- **补充内容未发布网站**，未修改线上数据库、后端或前端代码，也未提交、推送或部署。本地候选已保存，生产 Hermes 仍是原来四个来源链接。此状态与已完成的 MCP 取材测试分开登记。

## 方法与证据边界

使用 Codex CLI `0.154.0-alpha.6.2` 的两个独立临时会话。两次复用完全相同的提示词，忽略用户配置，在空目录运行；关闭 shell、unified exec、apps 和 web search，项目文档读取上限为 0。只配置 FieldToFit MCP，并复核所有实际工具事件。配置含义依据 [Codex 官方配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)。

前测连接 `https://fieldtofit.top/api/mcp/curated`；后测连接本机隔离的实际 FieldToFit 应用，显式禁用 Turso，数据只写临时 SQLite。代码相同；补充前的整个 watch 发布修订与生产一致，Hermes 的编辑内容及材料清单一致。生产多出独立维护状态，不影响正文版本。两次未指定模型覆盖，事件未提供确切模型 ID，因此本记录不是控制所有变量的模型能力对比；结论来自正文返回值及答案与原文的对应关系。

两轮均先遇到 Codex 模型连接的 WebSocket 超时，自动回退 HTTP 后完成；这不是 FieldToFit MCP 工具报错。

| 检查 | 生产前测 | 隔离补充后测 |
| --- | --- | --- |
| 已完成工具调用 | 8 次，全部 FieldToFit MCP | 11 次，全部 FieldToFit MCP |
| 实際返回来源正文 | 0 字符 | 57,739 字符 |
| 原文读取 | 逐项尝试 4 项，均为空 | 6 项均读到正文；README 跨两段读完；memory 读至 20,000、skills 读至 10,000，覆盖问题所需段落 |
| README 迁移选择 | 无法从简介确认 | 读出 `user-data`、`dry-run`、记忆条目及技能导入目录；没有声称两参数组合或逐文件迁移已实测 |
| 记忆机制 | 缺文件、容量与生效条件 | 两文件、字符限额、会话快照和下一会话生效均有原文依据 |
| 技能读取 | 只知道项目有技能功能 | 读出目录→完整技能→附属文件三层读取，按需载入 |
| 许可证与文档首页 | 只有链接 | 读取 LICENSE 及固定版本 MDX 首页；明确首页不等于全部链接页面 |
| 发布记录 | 仅有编辑摘要 | 原文仅两条修复标题摘录；明确不能当完整发布说明 |

另外使用 HTTP MCP 完成 32 次协议调用，以 4,096 字符分段重建全部 6 项材料：共 104,699 字符，所有正文与来源文件 SHA256 一致；资料包包含同样的 104,699 字符。此项是协议检查，不能混计为真实 AI 的 11 次调用。

## 补充候选的具体范围

版本：Hermes Agent v0.21.3 / v2026.9.14；固定提交 `345cd2b057a452236de401d3534b8502a7465e8d`。

| material_id | 来源文件 / 材料 | 候选覆盖 | 字符数 |
| --- | --- | --- | ---: |
| source-1 | README.md | 完整文件 | 17,574 |
| source-2 | GitHub 发布说明中的两条修复标题 | 摘录，17 个英文词 | 129 |
| source-3 | LICENSE | 完整文件 | 1,070 |
| source-4 | website/docs/index.mdx | 完整 MDX 源文件，不是实时官网或整站文档 | 8,966 |
| memory | website/docs/user-guide/features/memory.md | 完整文件 | 24,648 |
| skills | website/docs/user-guide/features/skills.md | 完整文件 | 52,312 |

README、许可证和三个仓库文档保留完整 MIT 版权／许可通知；正文、来源 URL、固定提交、实际获取时间和内容哈希一起保存。官网入口继续保留在来源列表，原文清单指向对应固定提交的首页源文件。未把 GitHub 网页导航、图片或其他链接页面算作已收录正文。

GitHub 发布说明正文没有找到独立的全文许可依据，不能从仓库 MIT 自动推定。因此只引用两条短标题并明确缺口，不把编辑概述补写成原文。完整发布说明仍是后续处理项。

## 新答案的原文依据与限制

1. README 的 `Migrating from OpenClaw` 说明不迁移 secrets 的预设、预览选项，以及技能导入 `~/.hermes/skills/openclaw-imports/`。memory 文档另说明存储目录；客户端正确区分存储位置与未经核实的迁移映射。
2. memory 文档说明 MEMORY.md 为 2,200 字符、USER.md 为 1,375 字符；会话内更新落盘而系统提示保持会话开始快照。客户端没有把字符当 token，也未认为用户配置必然等于文档默认值。
3. skills 文档的 `Progressive Disclosure` 说明 `skills_list()`、`skill_view(name)`、`skill_view(name, path)` 分层。所读正文支持按需加载的结论。
4. 客户端还发现 README／首页提到 LLM 摘要，而 memory 专页说明当前会话检索不做 LLM 摘要。这一差异在对应原文中确实存在；本次没有凭空替来源消除矛盾，也未运行源码判断实际行为。

固定来源：[README](https://github.com/NousResearch/hermes-agent/blob/345cd2b057a452236de401d3534b8502a7465e8d/README.md)、[Memory](https://github.com/NousResearch/hermes-agent/blob/345cd2b057a452236de401d3534b8502a7465e8d/website/docs/user-guide/features/memory.md)、[Skills](https://github.com/NousResearch/hermes-agent/blob/345cd2b057a452236de401d3534b8502a7465e8d/website/docs/user-guide/features/skills.md)、[文档首页源文件](https://github.com/NousResearch/hermes-agent/blob/345cd2b057a452236de401d3534b8502a7465e8d/website/docs/index.mdx)、[LICENSE](https://github.com/NousResearch/hermes-agent/blob/345cd2b057a452236de401d3534b8502a7465e8d/LICENSE)、[发布说明](https://github.com/NousResearch/hermes-agent/releases/tag/v2026.9.14)。

## 复核与保存

[结构化证据](2026-09-17-hermes-materials.json) 包含完整提示词、提示词哈希、配置、实际调用序列、读取偏移、修订和正文哈希。两个独立会话的原始事件及答案、补充候选、来源审计清单保存在本机 `output/operations/2026-09-17-hermes-mcp/`，该目录不纳入公开源码。

独立审核已逐项核对答案与实际读取段落，未发现假装读过正文或把链接当原文的情况。后续可将这种 MCP-only 内容验收用于已确认对象；不因本次有效就自动抓取整个仓库或为所有对象新增专题页面。
