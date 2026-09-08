# Changelog

格式参考 [Keep a Changelog](https://keepachangelog.com/)，语义化版本。

---

## Unreleased

后续已合入、尚未归入版本的变化记在这里。主案例及产品价值验证保持 pending，下一步重点见 [ROADMAP](ROADMAP.md)。

---

## [v1.1.0-beta.2] — 2026-09-08 · 开发候选，尚未发布

- 收录作者仓库中的 Skill 和选定 Agent 框架，保存提交版本、原始材料和附属文件入口；不自动运行仓库代码。
- 网页、API、MCP 增加独立能力筛选；资源类型和能力条件随任务资料包与导出保留。
- 管理端增加审核事项、状态筛选与分页，展示重复候选，由维护者选择主记录并填写依据后归并。
- 记录处理批次和完整日流程，展示积压、等待天数与延迟样本；有限批次不把未完成队列报为全部成功。
- 归并、撤销、冲突解决使用事务，远程批量写入失败关闭流并回滚，不自动重放不确定的提交。
- 阅读导出包含提纲、顺序、条件比较、实验事实状态、原文入口和 BibTeX；无模型时保留基础整理。
- 公开账户和产品主案例继续暂缓。真实日周期、生产 Turso / 容器、在线模型与真实用户效果仍待验收。

详细范围、真实采集和检查结果：[本版说明](docs/releases/v1.1.0-beta.2.md)。

## [v1.1.0-beta.1] — 2026-09-07 · 开发候选，尚未发布

本版将 Metis 从旧工具发现/策展流程扩展为有来源的 AI 知识工作台，并整理代码、文档与版本展示。版本号对应当前源码候选，不代表已创建公开 Release 或完成生产验收。

### Added

- 信息、论文、应用资源档案，共用事实、证据、版本、关系和历史（D-05～D-08、I-01、A-01）。
- 每日知识库流程、原文分段、双语整理与简报、任务条件和材料、研究引用、本地关注以及 9 项只读 MCP 工具（AI-01～AI-05、M-01）。
- 当前目标、唯一的 42 项 REQ 状态表、使用指南、架构说明、验证索引、ROADMAP 和逐版说明模板。
- 仓库检查脚本，核对前后端版本、文档链接、相对导入与 REQ ID；纳入 CI。

### Changed

- README 改为中文首页与独立英文版，展示当前真实页面和明确的开发状态。
- 旧策展的 9 个文件移入 frontend/src/legacy；10 个未引用的旧页面及组件移除；/admin/curation 与旧路由兼容保留。
- 7 个脚本按安装、运行、历史维护分类，原路径保留兼容包装；后端依赖入口统一引用根清单。
- 旧设计、阶段计划和交付快照归档；现行状态集中到 docs/product/requirements.md。
- 前后端源码版本同步为 1.1.0-beta.1，健康检查读取统一后端版本。
- 隔离启动显式禁用 dotenv 时，兼容启动脚本也不再载入实际 .env。

### Known limitations

- **A-05 / AI-03 / V-01 主案例 pending**。旧 PDF 样例作为技术回归保留，不再作为产品价值案例；本版没有开发替代案例。
- 公开注册、登录和同步保持关闭（H-03）。资料建设、研究/学习流程、部分管理功能及任务条件订阅仍不完整。
- 容器、生产 Turso、连续日周期、真实在线模型服务切换和用户效果待验收；远程多步事务与完整运行隔离仍有缺口。

详细重点、升级影响与验证：[本版说明](docs/releases/v1.1.0-beta.1.md)。

---

## [v1.0.0] — 2026-08-30

Metis 首个正式开源版本。此版本将完整的数据发现、AI 增强、人工策展、
双语展示和 Newsletter 工作流作为稳定基线发布。

### Added
- 使用 MIT License 正式开源，并发布首个稳定版本
- 新增中英文 README、项目截图、Quick Start、部署、安全和贡献指南
- 新增 GitHub Actions CI、Dependabot 和 GitHub 密钥扫描保护
- 支持 GPT、Claude、MiniMax、GLM、DeepSeek 等 AI 模型的扩展方向；
  当前参考实现默认使用 MiniMax

### Security
- 管理、通讯、翻译、生成和监控接口现在统一要求管理员鉴权
- 未配置 `CRON_SECRET` 时定时任务接口默认拒绝访问
- 移除临时数据库和 MiniMax 诊断接口
- 通讯 HTML 对不可信字段进行转义
- Community 页面明确提示昵称、留言内容和日期会公开展示
- 清理公开文档中的本机绝对路径和旧 GitHub 仓库链接
- 移除存在供应链安全公告的 `deep-translator`；翻译改为显式配置的
  LibreTranslate 兼容端点，默认不外发文本

### Changed
- 启动脚本改为仓库相对路径，不再包含本机绝对路径
- 启动脚本恢复可执行权限，Quick Start 已在干净环境完成安装和启动验证
- Flask 后端统一使用 Gunicorn，并更新部署说明
- README 新增项目截图和完整中文版
- 新增 CI、贡献指南、安全报告流程和隔离的集成测试

---

## [v0.4.0] — 2026-04-13

### Added

| 功能 | 说明 |
|------|------|
| RSS 新闻爬虫 | 新增第 4 个数据源 `RSSNewsScraper`，抓取 8 个 AI 新闻 RSS 源（The Verge AI / TechCrunch AI / Ars Technica / MIT Technology Review / VentureBeat AI / Wired AI / OpenAI Blog / Google AI Blog），仅保留最近 48 小时文章，httpx + feedparser 解析 |
| AI 每日新闻 | `generate_daily_news()` 从当日 AI 相关条目中筛选最多 80 条，调用 MiniMax 生成结构化日报：3-5 条 headlines（含标签：模型发布/融资/开源/产品/政策/研究/工具）、3-6 条 quick_bites、编辑视角分析，中英双语 |
| DailyNews 前端页面 | `/daily-news` 路由，含 12 月年历概览（可点击已发布日期）、日期导航（跳转到相邻已发布期）、带彩色标签的 headlines、Quick Bites、Editor's Take 渐变卡片 |
| 暗色/亮色主题 | CSS 变量驱动的全局主题系统，`theme.ts` 管理状态，localStorage 持久化偏好，所有页面和组件适配 |
| Cron 任务拆分 | 原单一 `/api/cron` 拆分为 4 个独立 Vercel Serverless Function：`cron_scrape`（600s）、`cron_daily_news`（300s）、`cron_classify`（600s）、`cron_digest`（300s），各自独立调度互不阻塞 |
| Cron 执行日志 | 新增 `cron_logs` 表，记录每次定时任务的 run_date、task_name、status、各步骤详情（JSON）、耗时、错误信息；`GET /api/cron-logs` 端点支持按 task 过滤查询 |
| 每日新闻二次生成 | 每日 06:00 UTC 再次触发 `/api/cron/daily-news`，用更多后续素材补充日报内容 |
| `feedparser` 依赖 | `requirements.txt` 新增 `feedparser>=6.0.0` 用于 RSS 解析 |

### Changed

| 变更项 | 变更内容 |
|--------|----------|
| Cron 调度时间 | 调整为北京时间白天执行：爬虫 08:00 → 日报 08:30 → 分类 09:00 → 摘要 09:30 → 日报补充 14:00 |
| 分类流水线优先级 | `task_classify()` 重排优先级：先跑 discovery_category + short_summary（依赖 MiniMax），再跑 content_type/domain（本地规则）+ 翻译 |
| MiniMax API 超时 | 从 300s 降为 120s，减少长时间挂起风险 |
| 发现模块布局 | 本周发现从 3 列网格改为全宽堆叠布局 |
| week_tools 查询 | 修复 N+1 查询，改为单次查询返回 `discovery_category` + `short_summary` 字段 |

### Fixed

| 问题 | 修复方式 |
|------|----------|
| MiniMax API 错误静默吞没 | 错误信息现在正确传播到 `cron_logs`，便于排查 |
| 分类空转死循环 | 无新内容可处理时 `task_classify()` 提前 break，不再空耗 550s 时间预算 |
| Turso 浮点参数编码 | 修复 `duration_seconds` REAL 类型参数在 Turso 上的编码问题 |
| MiniMax 400 错误 | 修复批量分类时 prompt 过长导致的请求拒绝 |
| 爬虫跳过逻辑 | 修复已存在内容的 source 合并逻辑 |

---

## [v0.3.0] — 2026-04-05

### Added

| 功能 | 说明 |
|------|------|
| 三模块分区 | 本周发现按 `discovery_category` 拆分为三区：📰 AI 动态（`news`）/ 🔧 AI 工具（`ai_tool`）/ 🌐 其他（`other`） |
| AI 智能摘要 | MiniMax 为每条内容生成 `short_summary`（英文 ≤60 字符）和 `short_summary_zh`（中文 ≤20 字符），格式「名称 — 一句话功能描述」，批量处理每批 20 条 |
| 自动分类触发 | 爬虫发现新内容后自动调用 MiniMax 完成 discovery_category 分类（50 条/批）和摘要生成 |
| `discovery_category` 列 | `tools` 表新增字段，由 MiniMax 分类，取值 news / ai_tool / other |
| `short_summary` / `short_summary_zh` 列 | `tools` 表新增字段，AI 生成的一句话摘要 |

### Changed

| 变更项 | 变更内容 |
|--------|----------|
| AI 推荐运行方式 | 从手动触发改为每日自动运行，爬虫完成后自动生成 |

---

## [v0.2.0] — 2026-03

### Added

| 功能 | 说明 |
|------|------|
| 社区页 | `/community` 路由，用户留言入口，支持可选昵称，数据存入 `user_messages` 表 |
| 本周发现 | `GET /api/discover/week` 返回最近 7 天内容，按热度指标降序排列 |
| Daily Digest | MiniMax 每日从发现中选出 3 个工具推荐 + 2 条热点新闻，附中英文一句话摘要，结果缓存在 `daily_digest` 表 |
| AI 推荐 TOP 5 | MiniMax 分析当日最多 50 条内容，选出 TOP 5 并输出中英文推荐理由（2-3 句）、适用场景（2-3 个）、评分 1-10，结果存入 `ai_recommendations` 表 |
| Carousel 组件 | 优选榜和 AI 推荐支持平滑滚动 + 方向箭头导航 |
| AI 推荐速览 | 推荐列表上方展示「名称 — 一行理由」快速预览条 |

---

## [v0.1.0] — 2026-02 ~ 2026-03

### Added

| 功能 | 说明 |
|------|------|
| GitHub Trending 爬虫 | 解析 `github.com/trending/{lang}` 页面（Python / TypeScript / JavaScript / Rust / Go / 全部），httpx + 正则提取，GitHub REST API 获取精确 star 数 |
| Hacker News 爬虫 | Firebase API 抓取 `showstories` + `topstories`，每端点前 50 条，过滤 `points < 10`，Show HN 自动清理标题前缀 |
| Product Hunt 爬虫 | GraphQL API 按投票数取前 30 个产品，Bearer Token 认证 |
| URL 去重 | 两级 `dedup_key` 策略：GitHub URL → `github:{owner}/{repo}`，其他 → `url:{normalized}`（去 query/fragment/www/尾部斜杠） |
| 规则分类器 | 零 API 开销，正则关键词匹配评分：`content_type`（tool/library/model/api/article/other）× `domain`（ai/web/devops/data/security/design/general） |
| 中英翻译 | `deep-translator` 调用 Google Translate，标题+描述 → 中文；Take → 英文反向翻译 |
| Discover 页 | `/discover` 四板块：优选榜（`is_featured`）、Metis 推荐（`is_metis_pick`）、AI 推荐（`ai_recommendations`）、今日发现 |
| Admin 后台 | 密码保护，工具审核（approve/skip/defer/archive/unapprove）、设置 featured/metis-pick、编辑 Take、合并重复项，操作记录到 `curation_log` 表 |
| Newsletter 发送 | `issues` 表管理期刊（draft → sent），HTML 模板 + Buttondown API 分发，防重复发送 |
| Landing page | `/` 品牌主页，介绍 Metis 定位 |
| 中英文切换 | 前端 i18n，localStorage 持久化语言偏好 |
| 爬虫健康监控 | `scrape_runs` 表记录每次运行的 source、status、found/new/deduped 计数、耗时 |
| 部署架构 | Vercel（前端 + Serverless Functions）+ SQLite/Turso + Cloudflare Tunnel（Mac mini）+ MiniMax + Buttondown + Google Translate |
