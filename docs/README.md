# FieldToFit 文档导航

[本轮公开历史与网页补验](validation/2026-09-10-platform-history.md)

[来源与筛选验收](validation/2026-09-10-platform-sources.md)

[原文包验收](validation/2026-09-10-platform-bundles.md)

[期次与增量验收](validation/2026-09-09-platform-updates.md)

[精选平台实际使用](guides/platform.md)

**P1 产品基线；2026-09-10 Unreleased 实现。** For you、For your AI、About 的基础页面和精选发布/读取已可本地使用，版本仍为 1.1.0-beta.2。案例 pending，账户待开放，每 1 天检查。先看[平台使用指南](guides/platform.md)和[本次验证](validation/2026-09-09-platform-foundation.md)。

## 先了解项目与需求

| 想了解什么 | 文档 |
| --- | --- |
| 项目是什么、现在到哪里 | [中文 README](../README.md) · [English](../README.en.md) |
| 立意、用户、平台职责与范围 | [项目目标](product/goals.md) |
| 三个页面具体怎么做 | [页面结构及 About 文案](product/pages.md) |
| 全部 REQ、子 REQ 与现有基础 | [18 项需求总表、72 子项及旧 42 项映射](product/requirements.md) |
| 共享资料如何组织 | [资料模型与 AI 读取契约草案](product/data-contract.md) |
| 怎么判断完成、何时能正式发布 | [平台验收标准](product/acceptance.md) |
| 下一步及持续运营 | [路线图](../ROADMAP.md) |

## REQ 详细方案

[共享资料基础](product/requirements/foundation.md) · [For you](product/requirements/for-you.md) · [For your AI](product/requirements/for-ai.md) · [About](product/requirements/about.md) · [维护与运营](product/requirements/operations.md) · [迁移](product/requirements/migration.md)

每个子项包含用途、具体方案、验收及状态；不以文档写完代替功能完成。

## 使用当前代码

| 想做什么 | 入口 |
| --- | --- |
| 本地启动、导入样本 | [本地指南](guides/local-development.md) |
| 部署、日调度、备份 | [部署指南](guides/deployment.md) |
| 管理与审核当前资料 | [管理指南](guides/management.md) |
| 使用当前 API/MCP | [接入指南](guides/ai-access.md) |
| 内容维护 | [现有操作与目标流程](guides/content.md) |
| 理解代码和兼容边界 | [架构](architecture/README.md) |

这些指南标明 beta.2 实际能力；新 REQ 中拟定的字段、页面和接口不应被当作已经可用。

## 版本和历史

[CHANGELOG](../CHANGELOG.md) · [版本维护](releases/README.md) · [验证索引](validation/README.md) · [历史归档](archive/README.md)

现行状态只维护在需求总表和其子项方案中。逐版记录描述实际交付；验证记录只证明指定提交/环境/输入；旧计划是历史，不继续指导实施。
