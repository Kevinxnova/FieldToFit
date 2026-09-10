# FieldToFit

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="frontend/public/brand/logo-on-dark.svg">
  <img src="frontend/public/brand/logo-on-light.svg" alt="FieldToFit" width="600">
</picture>

**FIELD → FIT**

- **Field**：动态、论文、模型、工具、开源项目和开发资料组成的 AI 全景。
- **To**：持续跟踪、整理、比较、验证和筛选。
- **Fit**：结合用户的任务、条件与限制，判断什么真正适用。

**FieldToFit 是人与 AI 共享的动态 AI 地图：看清已有方案，判断是否适配，选择正确的采用与构建路线。**

**给你看，也给你的 AI 用。**

把值得关注的 AI 对象与变化整理给人看，把充分、有来源的材料提供给用户自己的 AI。

[English](README.en.md) · [项目立意](docs/product/goals.md) · [REQ list](docs/product/requirements.md) · [文档](docs/README.md) · [更新记录](CHANGELOG.md) · [路线图](ROADMAP.md)

[![CI](https://github.com/Kevinxnova/FieldToFit/actions/workflows/ci.yml/badge.svg)](https://github.com/Kevinxnova/FieldToFit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

FieldToFit 面向研究者、工程师、研究生、学生，以及他们使用的个人 AI / Agent。人需要清楚的重点、结构化介绍和可核查的出处；AI 需要详细材料、版本、限制和可继续读取的原文。两种阅读方式共用同一套对象与证据。

平台负责资料的发现、整理、维护和提供。用户的 AI 基于这些材料，结合用户自己的需求继续比较、选择、设计或执行。

## 产品方向

**三个页面的基础实现已可本地使用；完整目标与剩余工作逐项记录在 REQ list。**

| 页面 | 为谁做、能得到什么 |
| --- | --- |
| **For you · 给你看** | 本期概览和精选资料流；看懂受到关注的模型、工具、Agent、Skill、Harness 与重要研究，查看公开能力、限制、变化及来源，然后交给自己的 AI |
| **For your AI · 给 AI 用** | 连接 MCP/API，查看同一精选集合的材料覆盖，按需读取原文、导出 JSON/Markdown、获取版本变化 |
| **关于 FieldToFit · About FieldToFit** | 说明项目立意、两种使用方法、资料来源与维护原则、项目状态和参与方式；放在页脚及辅助菜单 |

主导航保留两个工作入口，取消旧领域分类墙。先维护少量高质量对象，不按每日条数凑内容。资料每 **1 天**检查；关注度、公开声明和实际观察分开，缺失/过期明确显示。页面与拟用文案见[完整方案](docs/product/pages.md)。

## 当前实现到哪里

当前运行版本为 **v1.0.0**，作为 FieldToFit 品牌的首个版本。现有精选资料、For you、For your AI、About 和 MCP 已可本地使用；生产部署和持续日验收按 REQ list 独立记录，版本更名不替代验收。

| 已有基础 | 仍需完成的新目标 |
| --- | --- |
| 精选对象、Harness/别名、事实引文、材料清单及内容哈希 | 首批已有 27 项审核内容；关系、多版本材料与长期运营继续完善 |
| 单对象审核发布、并发冲突保护、变更复核、撤回；原每日流程保留 | AI 整理稿交接已接通；连续真实日运营与生产验收待完成 |
| 19 项只读 MCP 工具（10 项精选读取）、HTTP/stdio、原文续读与多对象原文包 | 对象关系、逐材料复核、日常 AI 客户端验收 |
| For you、For your AI、About，双主导航、旧入口兼容迁移 | 新详情收藏、真实用户理解与取材验证 |

现行 [18 个 REQ / 72 个子 REQ](docs/product/requirements.md) 逐项写明方案、现有基础、缺口及验收。旧 42 项保留历史映射，不代表新目标已完成。

公开注册、登录和同步暂不开放，账户标注“待开放”。AI 应用案例继续 **pending**；旧 PDF 技术样例仅用于回归。网站代做任务比较/方案/学习路线退出新主线，已有代码和接口暂保留兼容。

<details>
<summary>查看历史 beta.2 界面（不代表当前新页面）</summary>

![beta.2 信息工作台](docs/assets/workspace-information.png)

*信息截图使用六条显式导入的本地样本；不代表全网覆盖或当前精选质量。*

![beta.2 应用与资源](docs/assets/workspace-resources.png)

*资源截图展示 beta.2 的 Skill 收录与筛选。新三页基础已实现，以下历史截图未更新。*

</details>

## 最近更新与下一步

| 记录 | 状态 / 日期 | 重点 |
| --- | --- | --- |
| [公开历史与网页补验](docs/validation/2026-09-10-platform-history.md) | Unreleased · 2026-09-10 | 固定修订历史、资料包历史及续读、筛选返回修复、网页与手机补验 |
| [来源与筛选检查](docs/validation/2026-09-10-platform-sources.md) | Unreleased · 2026-09-10 | 精选来源状态、历史来源绑定、UTC 发布日期与来源筛选；完整网页交互待验 |
| [原文资料包检查](docs/validation/2026-09-10-platform-bundles.md) | Unreleased · 2026-09-10 | 手选多个对象、固定修订、含原文 JSON/Markdown、覆盖及续读说明 |
| [期次与增量检查](docs/validation/2026-09-09-platform-updates.md) | Unreleased · 2026-09-09 | 人工概览期次/归档、固定快照分页、精选变化续读、新增 3 项 MCP 工具 |
| [平台实现检查](docs/validation/2026-09-09-platform-foundation.md) | Unreleased · 2026-09-09 | 精选发布、三页基础、同源 API/MCP、真实原文续读和兼容迁移 |
| [平台文档 P1](docs/product/goals.md) | 文档调整 · 2026-09-08 | 新立意、两主页面及 About、18 REQ/72 子项、旧需求映射、验收和运营方案；无功能发布 |
| [v1.0.0](docs/releases/v1.0.0.md) | FieldToFit 首个品牌版本 · 2026-09-10 | 品牌、关于页、README、运行版本及兼容迁移 |
| [v1.1.0-beta.2](docs/releases/v1.1.0-beta.2.md) | 开发候选 · 2026-09-08 | Skill / Agent 版本材料、能力筛选、审核分页、日积压监控、事务回滚及研究导出 |
| [v1.1.0-beta.1](docs/releases/v1.1.0-beta.1.md) | 开发候选 · 2026-09-07 | 知识工作台、事实和版本材料、只读 MCP、代码与文档整理 |
| v1.0.0 | 历史基线 · 2026-08-30 | 首个正式开源版本，工具发现、人工策展与 Newsletter |

下一步完善“首批资料维护与完整交接 → 日常客户端、真实运营和发布验收”，见 [ROADMAP](ROADMAP.md)。软件发版记录更新重点、对应 REQ/子项、验证和升级影响；每日内容变化单独维护，不冒充软件发版。

## 快速开始

需要 Python 3.12/3.13 和 Node.js 20+。以下取得当前开发候选分支；使用 v1.0.0 标签会看到旧版工作流。

```bash
git clone --branch codex/fieldtofit-knowledge-workspace https://github.com/Kevinxnova/FieldToFit.git
cd fieldtofit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
cd frontend
npm ci
cd ..
```

按需在 `.env` 设置管理员和定时任务凭证。已有 `.env` 请保留原文件。默认本地 SQLite；浏览与基础检索无需模型密钥。

分别在两个终端启动：

```bash
# 仓库根目录：后端
./scripts/start-backend.sh
```

```bash
# 仓库根目录：前端
cd frontend
npm run dev
```

打开 [http://localhost:5173](http://localhost:5173)。新数据库没有资料时，可在已激活环境的根目录显式导入六条短引用与整理样本：

```bash
python -m examples.editorial.load
```

默认进入 `/for-you`。以上样本属于旧记录，不会自动进入精选；真实材料隔离预览与审核发布见[平台使用指南](docs/guides/platform.md)。完整配置、隔离数据和检查办法见 [本地指南](docs/guides/local-development.md)。

## 当前 MCP 与 API

当前后端 MCP 地址为 `http://127.0.0.1:8000/api/mcp`，网页 `/for-your-ai` 可检查连接。HTTP API 位于 `/api/v1`。基础资料读取无需生成模型密钥；公网服务是否需要读令牌由部署者配置。

```bash
.venv/bin/python -m backend.mcp_stdio
```

stdio 客户端工作目录设为仓库根目录，通过 `FIELDTOFIT_MCP_URL` 和可选 `FIELDTOFIT_READ_TOKEN` 配置连接。新精选入口使用 `curated_search`、`curated_object`、`curated_material`、`curated_export`；另有 `curated_changes`、`curated_editions`、`curated_edition`。旧 9 项工具保留兼容。当前接口用法见[接入指南](docs/guides/ai-access.md)，未来目标另见[资料契约草案](docs/product/data-contract.md)。

## 维护与参与

[内容维护](docs/guides/content.md) · [管理后台](docs/guides/management.md) · [部署](DEPLOY.md) · [验证记录](docs/validation/README.md) · [架构](docs/architecture/README.md) · [贡献](CONTRIBUTING.md) · [安全报告](SECURITY.md)

欢迎反馈资料错误、缺少的原文、希望持续跟进的对象，以及个人 AI 取材过程中遇到的问题。旧策展与 Newsletter 仍由 `/admin/curation` 保留。源码采用 [MIT License](LICENSE)；第三方材料保留各自来源和适用许可。
