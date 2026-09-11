# FieldToFit 更新记录

## Unreleased · 待发布

后续计划见 [REQ list](docs/product/requirements.md)，尚未完成的计划不记为已发布变化。

## v1.0.0 持续关注 CW1 · 2026-09-11

- 27 个已确认主体按五类展示；补齐模型版本、工具 / Agent 更新、Skill 关注度与代表技能、Harness 运行机制。
- 同源 curated_watch / HTTP 读取、正文搜索与类型筛选、目录定位、JSON 下载与 AI 交接；原有原文库折叠保留。
- 草稿/撤回/私有字段隔离，来源覆盖与未知项明确；精选 MCP 共 12 项。[验收与部署状态](docs/validation/2026-09-11-continuous-watch.md)。

## v1.0.0 内容与阅读更新 · 2026-09-11

- For you 改为近期动态（速览/发布与更新）和资源档案；完整解读逐点展示，减少重复内容。
- 新增页内目录，桌面固定、手机折叠，支持阅读定位、分享展开及筛选/分页同步（REQ-Y-04）。
- 加入包含 DeepSeek-V4.1-Flash 的 10 条首发动态；新增 curated_news 与同源 API，共 11 项精选 MCP 工具。
- 新闻通过版本化文件审核发布，原文仅链接；旧资源/期次/原文接口保留。验证见[阅读验收](docs/validation/2026-09-11-reading.md)。

### 前次文件整理

- 2026-09-11：整理当前文档、归档 Metis 历史，公开品牌图片收敛为网站实际使用的 5 份。
- 文件整理阶段先记录候选内容；随后根据用户确认合并为近期动态与资源档案，本次交付范围见上文。
- FieldToFit 标签采用 `fieldtofit-vX.Y.Z`；旧 Metis 标签保留。

## v1.0.0 · FieldToFit · 2026-09-10

- 项目品牌更名为 **FieldToFit**，视觉表达为 **FIELD → FIT**；以人与 AI 共享的动态 AI 地图说明项目立意。
- 接入提供的深浅色 Logo、浏览器图标、触屏图标和分享图；关于页先展示 Field / To / Fit，再保留双端使用方式、来源与维护说明。
- 统一网页、MCP 身份、README、开发与部署文档中的项目名称；前后端运行版本均为 1.0.0。
- 兼容读取旧环境变量、浏览器收藏和 SQLite 数据；旧协议标识与历史证据保留用于升级兼容。
- fieldtofit.top 已完成 DNS 与生产绑定；品牌、健康、27 项资料及 10 项 MCP 工具通过公网实测。公开列表和资料包采用请求内批量读取，后续请求重新检查撤回，修复远程写锁超时与逐条查询延迟。
- 首批内容已扩展为 27 项、62 份材料；本地整理稿导出/导入、引文预览与审核发布已实现。公网部署及连续日运行仍单独验收。

这是品牌版本的新起点；以下旧版本编号保留历史顺序，不代表从 v1.1 降级数据。


## 附录：Metis 历史更新记录

以下保留当时日期、版本和名称，仅用于追溯。早期 beta 编号不代表 FieldToFit 当前版本；历史 Unreleased 阶段已结束，不继续作为当前待发布清单。旧 `v1.0.0` 标签指向 Metis 2026-08-30，不能用来下载当前 FieldToFit。

## Metis 转型开发记录 · 2026-09-08～10

### 公开修订历史与网页补验 · 2026-09-10

- 详情和 AI 页面增加截至所选修订的公开历史，展示首次发布、修订字段、待复核和撤回；可打开旧修订，管理员审核备注不公开（REQ-Y-03.01、AI-02.03）。
- 新增 `curated_history` 和对象历史接口，固定快照分页；JSON/Markdown 原文包包含历史，超过 20 条给出继续读取参数，当前共 19 项 MCP 工具（REQ-AI-03.01）。
- 修复从筛选列表进入详情或旧修订后丢失筛选条件的问题；补验来源、UTC 日期区间、清除、刷新恢复、AI 页面选对象及 390px 手机布局（REQ-Y-02.03/.04、Y-03.01、AI-01.03）。
- 完整测试 154 项通过、1 项跳过，官方 SDK HTTP/stdio 及真实修订 6/3 对应历史验证通过。没有新增数据表、生产部署或正式版本标签。

证据：[公开历史与网页补验](docs/validation/2026-09-10-platform-history.md)。逐材料检查、有依据的对象关系、真实日运营和用户验收仍待完成。

### 精选来源检查与日期筛选 · 2026-09-10

- 精选索引支持采集来源 ID、UTC 精选发布日期首尾筛选，筛选条件绑定稳定游标；旧无筛选游标保留兼容（REQ-Y-02.03、AI-01.03）。
- 当前精选来源提供最后尝试、最后成功、失败/部分成功/停用/逾期/未登记状态；不把记录整理时间或采集源运行冒充逐份文档复核，不公开源配置和私有错误（REQ-F-04.01/.03、AI-04.03）。
- 新发布保存来源身份；历史发布缺失字段时从对应历史记录读取，不跟随当前来源改动。原文包携带同一来源检查说明。
- 新增 `curated_sources`，共 18 项 MCP 工具。17 项新测试通过，完整测试 148 项通过、1 项跳过；官方 SDK 双传输通过。页面已接通，完整筛选交互因工具额度拦截尚待补验。

证据：[来源与筛选验收](docs/validation/2026-09-10-platform-sources.md)。不新增表，不改生产库或自动发布旧资料。应用版本仍为 beta.2，尚未正式发布。

### 多对象含原文资料包 · 2026-09-10

- For you 可手选最多 10 个对象，跨搜索/分页保留所选发布修订；详情与 For your AI 可预览、下载 JSON/Markdown 原文包（REQ-Y-03.03、AI-01.04）。
- 新增 `curated_bundle` 与 HTTP POST `/api/v1/platform/bundle`；把档案、实际所存正文、来源、许可证、未知项和缺口一起交接。默认 20 万、最大 50 万正文字符，超限保留准确续读参数（REQ-AI-02.03）。
- 撤回/缺失对象不静默丢弃，历史修订不自动替换；同一事务读取，逐份核对哈希，外部正文保持字面引用数据（REQ-AI-02.02～.04）。
- MCP 现为 17 项；官方 SDK HTTP/stdio 的完整包、限长续读和 Markdown 检查通过。本轮不新增数据表、不改生产库或自动精选旧记录。

证据与边界见[原文包验收](docs/validation/2026-09-10-platform-bundles.md)。关系/历史材料、真实日常 AI 客户端与正式运营仍待验；应用版本未递增。

### 概览期次与可靠续读 · 2026-09-09

- For you 增加人工审核的独立期次、固定修订直达与往期归档；草稿修改不覆盖公开版本，来源变化/不可用逐项提示（REQ-Y-01.02～.04、F-03.04）。
- 精选索引与归档使用固定快照，新增内容留到下一批，撤回位置脱敏保留；游标绑定查询、页大小并设 7 天期限（REQ-AI-01.03、AI-04.02）。
- 提供精选新增、修订、待复核、撤回事件及跨窗口检查点；源下架和归并进入变化记录，私有草稿及审核备注不公开（REQ-AI-04、O-01）。
- 新增 `curated_changes`、`curated_editions`、`curated_edition`，共 16 项 MCP 工具；后台增加概览草稿、原句核查、排序、并发发布及撤回（REQ-AI-03、O-01）。
- 增加三个增量表，保留已有数据；新版盘点脚本覆盖平台六张表。生产部署、连续日运营及真实用户验收仍未完成。

证据与实际边界见[期次及增量检查](docs/validation/2026-09-09-platform-updates.md)。应用版本暂不递增，仍为本地 Unreleased 工作。


### 精选平台基础与三页 · 2026-09-09

- 新增 For you、For your AI、About；主导航收敛为两项，旧入口兼容跳转（REQ-Y-01～Y-03、AI-01、AB-01、X-01.01）。
- 增加精选角色/别名/关注依据、来源引文门槛、材料清单和固定发布修订；审核与发布有并发校验和事务保护，资料变化进入复核（REQ-F-01～F-03、F-05、O-01）。
- 增加 4 项只读 curated MCP 工具和同源 HTTP 接口；原文按修订续读，中性清单可复制/下载，旧 9 项工具保留（REQ-AI-01～AI-03、X-01.03）。
- 增量三张表、只读 SQLite 盘点/一致备份；检查器覆盖 18/72 新编号及 42 历史锚点（REQ-X-01、O-03）。
- 真实 Deep Agents 官方材料仅用于隔离预览，不自动发布存量。独立概览期次、精选变化流、更多资料及正式运行验收仍待完成。

验证与升级边界见[平台检查](docs/validation/2026-09-09-platform-foundation.md)及[使用指南](docs/guides/platform.md)。应用版本未递增，未部署生产。

### 文档与产品规划 · P1 · 2026-09-08

- 重新明确平台立意：给人提供结构化精选内容，给个人 AI 提供详细、有来源的材料；网站代做比较、场景和任务方案退出新主线。
- 写明 For you、For your AI 与辅助“关于 Metis”页面方案、拟用文案及共用资料契约（REQ-Y-01～Y-03、AI-01～AI-04、AB-01）。
- 将现行需求展开为 18 个 REQ / 72 个子 REQ，逐项记录用途、方案、验收、依赖及状态；保留旧 42 项映射和调整前快照（REQ-X-01.04）。
- 同步中英文 README、导航、路线图、运营和版本维护说明；验收改为精选质量、人读理解、AI 取材及持续维护。
- 案例继续 pending，账户待开放，自动检查保持每 1 天。旧数量目标取消。

**此条仅记录 2026-09-08 的文档阶段：当时未修改功能代码或应用版本。** 后续实现见上方 2026-09-09 条目。 后续开发见 [ROADMAP](ROADMAP.md)。

---

## [v1.1.0-beta.2] — 2026-09-08 · 开发候选，尚未发布

- 收录作者仓库中的 Skill 和选定 Agent 框架，保存提交版本、原始材料和附属文件入口；不自动运行仓库代码。
- 网页、API、MCP 增加独立能力筛选；资源类型和能力条件随任务资料包与导出保留。
- 管理端增加审核事项、状态筛选与分页，展示重复候选，由维护者选择主记录并填写依据后归并。
- 记录处理批次和完整日流程，展示积压、等待天数与延迟样本；有限批次不把未完成队列报为全部成功。
- 归并、撤销、冲突解决使用事务，远程批量写入失败关闭流并回滚，不自动重放不确定的提交。
- 阅读导出包含提纲、顺序、条件比较、实验事实状态、原文入口和 BibTeX；无模型时保留基础整理。
- 公开账户和产品主案例继续暂缓。真实日周期、生产 Turso / 容器、在线模型与真实用户效果仍待验收。

详细范围、真实采集和检查结果：[本版说明](docs/archive/metis/releases/v1.1.0-beta.2.md)。

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

详细重点、升级影响与验证：[本版说明](docs/archive/metis/releases/v1.1.0-beta.1.md)。

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
| Admin 后台 | 密码保护，工具审核（approve/skip/defer/archive/unapprove）、设置 featured/fieldtofit-pick、编辑 Take、合并重复项，操作记录到 `curation_log` 表 |
| Newsletter 发送 | `issues` 表管理期刊（draft → sent），HTML 模板 + Buttondown API 分发，防重复发送 |
| Landing page | `/` 品牌主页，介绍 Metis 定位 |
| 中英文切换 | 前端 i18n，localStorage 持久化语言偏好 |
| 爬虫健康监控 | `scrape_runs` 表记录每次运行的 source、status、found/new/deduped 计数、耗时 |
| 部署架构 | Vercel（前端 + Serverless Functions）+ SQLite/Turso + Cloudflare Tunnel（Mac mini）+ MiniMax + Buttondown + Google Translate |
