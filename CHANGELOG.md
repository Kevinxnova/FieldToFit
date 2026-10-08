# FieldToFit 更新记录

## Unreleased · 待发布

后续计划见 [REQ list](FieldToFit-PM.md)，尚未完成的计划不记为已发布变化。

<a id="v1.8.10"></a>
## v1.8.10 · 模型图表任意公司多选 · 2026-10-08

### 更新重点

<!-- release-summary:zh:start -->
- AA与Arena支持任意公司组合，包含“其他”；按钮独立选中／取消，取消最后一家恢复全部，保留全部公司和各家旗舰快捷入口。
- 多选随网址保存、刷新和来源切换保留；旧单公司／旗舰链接兼容，搜索、数值表及缺项清单同步筛选，固定坐标与来源快照保持。
- 放大窗口提供同一套公司多选、搜索与重置控件；完善REQ-7-6方案，44项回归、生产构建及本地／正式各14组浏览器验收通过，已部署v1.8.10。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- AA and Arena support arbitrary company combinations, including Other. Toggle companies independently, restore all after removing the last, and retain All companies and Company flagships shortcuts.
- Preserve selections in URLs, across reloads and source switches, with legacy company/flagship links supported. Search, values and coverage tables follow the selection while coordinates and reviewed snapshots stay consistent.
- Add shared company, search and reset controls to enlarged charts. Complete the REQ-7-6 design; 44 regression tests, the production build and 14 browser check groups in both local and production environments pass. Version 1.8.10 is deployed.
<!-- release-summary:en:end -->

对应[REQ-7-6](FieldToFit-PM.md#req-7-6)。使用重复的`company`网址参数保存公司集合，保留旧单值及`company=flagship`入口；无数据库迁移或公开接口变化。AA161／Arena94及原配置、来源、数值、单位、日期和旗舰名单保持。实际构建、回归与浏览器结果见[本批验收](docs/validation/2026-10-08-chart-selection.md)。已部署v1.8.10，正式health／三MCP、原公开内容保持、资源及同范围14组生产浏览器验收通过；源码与发布状态收尾属于同一已验批次。

<a id="v1.8.9"></a>
## v1.8.9 · 两张模型图表任意公司多选需求登记 · 2026-10-08
<!-- release-tag:unpublished -->

### 更新重点

<!-- release-summary:zh:start -->
- 新增REQ-7-6：Artificial Analysis 2026与Arena 2026均须支持任意公司组合多选，包含“其他”，保留全部公司与各家旗舰快捷入口。
- 明确独立选中／取消、最后一家取消后恢复全部、搜索与放大图及表格联动、切换来源及URL保存／旧链接兼容的验收条件。
- 核对当前源码仅支持全部／旗舰／单家公司；本批登记需求并同步版本文档，多选仍待开发、验证与上线，正式站最近已验为v1.8.8。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Add REQ-7-6 for arbitrary company combinations in Artificial Analysis 2026 and Arena 2026, including Other, while retaining All companies and Company flagships shortcuts.
- Define independent selection/removal, restoring all after removing the last company, linked search/charts/tables, and selection persistence across sources and URLs with legacy-link compatibility.
- Confirm that current source code supports all companies, flagships or one company. This batch records requirements and synchronizes release documentation; multiselect remains unbuilt, unverified and undeployed, with v1.8.8 the last verified production version.
<!-- release-summary:en:end -->

对应[REQ-7-6](FieldToFit-PM.md#req-7-6)。总计22项主REQ、140项子REQ。仅交付需求及版本文档，无图表功能、快照、数据库或公开接口变更；未部署、未推送发布标签。实际源码核对、文档与版本检查见[登记与核对](FieldToFit-PM.md#req-7-6-review)，多选交互验收待实现后执行。

<a id="v1.8.8"></a>
## v1.8.8 · 10月8日内容与双来源模型图表刷新 · 2026-10-08

### 更新重点

<!-- release-summary:zh:start -->
- 新增GPT-6 Intelligent UI、Haiku 5.5与Claude SDK浏览器／电脑工具集三条动态，同步速览；更新GPT、Claude及Claude Code v2.1.293档案，保留历史版本。
- Sonnet旧动态保留9月28日发布价格，追加10月7日缓存读取降价及Haiku已发布说明；官方正文仅链接，MCP可读本站解读与材料范围。
- 完整复核AA与Arena快照：分别161／94个可绘制配置；Arena数据截止10月2日，本站核对10月8日。保留缺值、估计分、配置和两个来源各自单位。
- Arena新增Gemini 4 Argon与Sonnet 5.5配置；官方发布日期与榜单日期分别记录，支持Google和Anthropic两个明确发布域名，不扩大评分或价格来源。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Add GPT-6 Intelligent UI, Haiku 5.5 and Claude SDK browser/computer toolsets; refresh the overview and the GPT, Claude and Claude Code v2.1.293 profiles while preserving version history.
- Keep Sonnet's September 28 launch prices and append the October 7 cache-read reduction and Haiku release. Original pages remain linked; MCP exposes our commentary and explicit material coverage.
- Review complete AA and Arena snapshots with 161 and 94 plottable configurations. Arena's data cutoff is October 2, separately from the October 8 review; missing values, estimates, configurations and independent units remain explicit.
- Add Gemini 4 Argon and Sonnet 5.5 configurations to Arena, retaining official launch dates separately and accepting two exact Google/Anthropic launch domains without expanding score or price sources.
<!-- release-summary:en:end -->

对应REQ-4/5/6/8/9/11。用户明确批准10月8日日报A–D及AA／Arena完整刷新；正式93条动态、49项持续关注。不发布未核验线索，不宣称上游性能复测，不把网页可达等同全对象语义核验。无数据库迁移或公开接口变更。112项相关回归、双端正式页面、19次MCP调用与v1.8.8部署通过，见[本批证据](docs/validation/2026-10-08-editorial.md)。

<a id="v1.8.7"></a>
## v1.8.7 · 近期报告驱动的技术演化地图 · 2026-10-07

### 更新重点

<!-- release-summary:zh:start -->
- 近期动态增加按技术问题维护的演化地图、稳定详情入口与历史索引；首张采用已对齐的DeepSeek-V4.1报告，逐节点展示机制、条件、结果、局限和原文位置。
- 网页、关联模型档案与AI共用已审图结构；支持类型明确的关系、分享、公开修订前后对照与后台双端预览，草稿和私密检查保持隔离。
- 接入近30日研究与潜在修订队列、每日10份报告的检查交接及每周整理清单；日期和版本核对后给出具体提案，主人确认再进入草稿与发布。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Extend recent developments with question-based technical maps, stable detail links and a historical index; the aligned DeepSeek-V4.1 case exposes mechanisms, conditions, results, limitations and report locations.
- Share the reviewed graph across the website, related model dossiers and AI, with typed relationships, sharing, public revision comparisons and paired editorial previews; drafts and private checks remain isolated.
- Add a 30-day research and potential-revision queue, daily handoff capped at ten reports and weekly consolidation lists; verified dates and versions feed concrete proposals before owner-approved drafting and publication.
<!-- release-summary:en:end -->

用户2026-10-07认可近期技术报告方向、放置与维护机制后明确批准开发验证，登记REQ-22。作为现有news内容、阅读页面和审核流程的扩展，本批递增patch，不新增第四内容库或改变既有只读协议。新增两张私密检查表、一个幂等研究来源和curated_maps；原精选17工具增至18，兼容26工具增至27，Codex专用工具仍为一项。

2026-10-08用户明确更新并发布，本批v1.8.7及上一批名称追源／十二公告入口已正式部署。完整私密备份与幂等升级保留原数据；D-90经正式双端预览后显式发布，报告日期仍为2026-09-17，地图首次发表为北京时间2026-10-08 01:08。既有07:30／08:00任务已接入新流程，真实连续自然日及首次周整理效果仍待验。发布状态收尾纳入同一版本，未改变应用代码；见[生产验收](docs/validation/2026-10-08-maps-production.md)。

全量520项通过、1项既有可选跳过；最终地图与工作区38项通过。原始报告HTTP读取、五处锚点、公开检查不制造更新、三屏宽浏览器与构建已验。具体结果、范围及剩余项见[验收证据](docs/validation/2026-10-07-technical-maps.md)，运行机制见[维护指南](docs/guides/technical-maps.md)。

<a id="v1.8.6"></a>
## v1.8.6 · 私密名称追源与服务公告接入 · 2026-10-07

<!-- release-tag:unpublished -->

### 更新重点

<!-- release-summary:zh:start -->
- 近期候选、已选与热门线索按名称及版本建立私密组，保留原文位置；本地AI回传同名划分、官方正文、变化及推荐理由，支持核验历史和撤销。
- 增加豆包iOS／Mac、火山方舟、百炼与MiMo API共12个客户端／服务公告入口，按条目保存日期、型号、地域、停用安排与正文更正；首次历史基线保留原日期。
- HN补扫高讨论线索，再核对AI相关性；每日追源10组、每组3次检索／5份材料，每源5条，失败和积压保留续跑，不自动改公开身份、草稿或发布。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Group recent, selected and hot leads privately by name and version with exact source positions; accept local AI identity partitions, official text, changes and reasons, with review history and reopening.
- Add 12 Doubao iOS/macOS, Volcano Ark, Bailian and MiMo API announcement sources with entry dates, model IDs, regions, deprecation schedules and body corrections; preserve original dates for historical baselines.
- Scan hot HN stories before checking AI relevance; cap investigations at 10 groups, three searches and five materials per group, and five announcements per source, retaining failures and backlogs without public identity or publication writes.
<!-- release-summary:en:end -->

用户2026-10-07批准REQ-2-1／REQ-3-1与REQ-1-1具体方案后开发验证。沿用既有发现、后台及本地AI审阅流程，增加四张私密名称表及幂等来源注册；管理员原启停设置保留，公开API及已发布内容兼容。升级前需备份并执行既有维护升级；本地交接操作见[发现指南](docs/guides/discovery.md)。新增beautifulsoup4用于官方HTML表格与公开嵌入数据解析，不执行来源脚本。

本批2026-10-07本地源码交付；2026-10-08随v1.8.7正式部署，十二入口完成真实首轮采集，晨间交接已接入，见[生产证据](docs/validation/2026-10-08-maps-production.md)。Jev真实官方正文、十二入口实际读取、隔离回归及后台三宽度已验，实际结果和剩余缺口见[验收记录](docs/validation/2026-10-07-discovery-names-sources.md)。连续三个真实自然日、正式新增日流程与豆包Android／Windows／网页日志仍待验或未确认。AI演化地图仅为用户要求的交互case，不新增网站内容或已批准REQ。

<a id="v1.8.5"></a>
## v1.8.5 · 对象核对、原文定位、纠错与公开修订对照 · 2026-10-07

### 更新重点

<!-- release-summary:zh:start -->
- 增加全部已发布CW的每日私密核对台账，冻结清单与官方入口、对照已审档案，保留差异、失败和重试，汇总覆盖并准备更新提案。
- 已审材料支持固定修订的章节、段落及PDF文件页码读取和引用；图像、扫描与公式缺口明确标注，旧字符续读兼容。
- 纠错绑定具体字段或原文位置，后台记录受理至实际发布修复；公开更正说明保留依据，报告、联系与内部备注私密。
- CW详情增加公开修订前后对照、固定链接与下载；网页、API及新增四项只读MCP能力同源，当前撤回权限优先。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Add a private daily ledger for all published CW profiles, freezing official entry plans, comparing approved dossiers, retaining findings and retry failures, and preparing update proposals.
- Read and cite revision-bound sections, paragraphs and physical PDF pages, with explicit image, scan and formula gaps and compatible character-offset reads.
- Bind corrections to specific fields or source positions and track verified publication repairs; expose reviewed receipts while keeping reports, contacts and internal notes private.
- Compare public CW dossier revisions through share links and downloads, with matching API and four new read-only MCP tools and current withdrawal permissions.
<!-- release-summary:en:end -->

对应REQ-19-1／2／3／4、REQ-4-2／8-6、REQ-10-4／8、REQ-14-2与新REQ-21-1至4。2026-10-07用户要求先完善总览方案并开发验证。保留原公开契约，增加五张私密台账／纠错表与一个索引；已有环境需先备份并执行幂等维护升级。精选MCP由13增至17项，兼容端点由22增至26项，Codex专题专用工具仍一项。PDF使用已有pypdf，Flask最低版本提升至3.1以单独限制上传大小。

用户随后明确更新并部署：本批已完成生产70表私密备份、五表幂等升级与v1.8.5正式部署；health／三MCP、新增工具对等、旧读取兼容及原公开集合／草稿／图表／历史保护通过。今日台账建立49项未完成清单，不冒充已核对；核对与提案不自动创建网站草稿或发布。正式49对象必要入口逐项核实、08:00实际交付及连续三日全覆盖待验；公共检查日期、OCR／公式解析与D动态修订对照为后续范围。实际测试、浏览器与迁移证据见[本批验收](docs/validation/2026-10-07-reviewed-maintenance.md)。

<a id="v1.8.4"></a>
## v1.8.4 · 官方每日小结与有序日志 · 2026-10-07

### 更新重点

<!-- release-summary:zh:start -->
- 在10月7日日历Day 3详情前加入Tibo官方Day 2小结，按2.1–2.4关联现有四条日志，复用真实头像与完整原帖／译文。
- 当日详情按2.2、2.3、2.4排列；2.1保留10月6日真实日期并标明已发布，API两项保持其他OpenAI分组，小结不增加事件计数。
- 网页、无脚本HTML、API、MCP与AI交接共用同源编号；单日交接带跨日关联资料，范围过滤与撤回不会保留无效日志入口。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Add Tibo’s official Day 2 roundup above October 7 calendar Day 3, linking the four existing logs in 2.1–2.4 order with his verified avatar, original post and translation.
- Order that date’s details as 2.2, 2.3 and 2.4; keep 2.1 on its real October 6 date and both API entries in other OpenAI. The roundup adds no extra events.
- Share source-backed numbering across the website, static HTML, API, MCP and AI handoff, including cross-date references and scoped or withdrawn-link handling.
<!-- release-summary:en:end -->

对应[REQ-20-11](FieldToFit-PM.md#req-20-11)。沿用现有动态D-85承载总结原帖与四条已审关联，不另建新闻或公开数据源；原始日期、分组和89条动态／11条专题计数保持。新增可选roundup／roundups／ordered_ids字段，旧接口与数据库结构兼容。用户直接提供总结原帖和2.1–2.4结构要求，范围为本批展示及来源整理；未来新选题仍需具体确认。103项回归、构建、仓库检查、本地及正式三宽度、后台双端、HTML／API／两MCP与原位置增量均通过；晚到小结按真实日期可查且不增加事件。实际证据见[10月7日小结展示验收](docs/validation/2026-10-07-codex-updates.md#official-roundup)。

<a id="v1.8.3"></a>
## v1.8.3 · Codex日志补录与Decisions公测整理 · 2026-10-07

### 更新重点

<!-- release-summary:zh:start -->
- 补录Auto-review免费、Meetings专题公告、API用量等级、Decisions公开测试、ChatGPT音频上传和数学成果公告，专题共11条：4条Codex／Work、7条其他OpenAI。
- 六条新增日志同步中英文概览；有真实关联原帖的五条附Tibo摘录及经当前X身份核对的同款头像，补充回复保持折叠。
- D-55保留9月29日事件和有限预览背景，补记Decisions公测并关联新记录；仅来源日期的两条不推造北京时刻。
- 网页、公开HTML、API及MCP共用发布修订；正式站共89条动态、49项持续关注，日报、历史专题及模型图保留。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Backfill free Auto-review, the Meetings topic announcement, API tiers, Decisions public beta, ChatGPT audio uploads and mathematical results: 11 topic logs, with four Codex / Work entries and seven other OpenAI entries.
- Add bilingual overviews to all six entries and verified Tibo excerpts and current X-profile avatars to the five entries with related posts; keep supplementary replies collapsed.
- Preserve D-55's September 29 limited-preview context while adding its public-beta follow-up and related record; retain source-date precision for the two date-only announcements.
- Keep the website, static HTML, API and MCP on the same published revision: 89 developments and 49 watch profiles, retaining the briefing, earlier topic logs and reviewed charts.
<!-- release-summary:en:end -->

对应[REQ-20](FieldToFit-PM.md#req-20)。用户在具体六项提案及D-55补记后明确授权整理并发布；新记录D-84至D-89沿用既有保存、预览、复核和发布流程。Meetings记录专题公告而非首次上线，研究成果不表示内部模型可用；重置因范围与生效时间缺失留内部，不生成占位。无接口或数据库迁移；77项回归、构建及仓库检查、本地与正式三宽度、原位置增量同步、health／两MCP v1.8.3及143项站点地图通过；正式部署与同源验收见[本批证据](docs/validation/2026-10-07-codex-updates.md)。真实定时准点、连续三日及末次收尾尚未通过，不以本次补发冒充。

<a id="v1.8.2"></a>
## v1.8.2 · Mistral Large 4、Cowork及运行工具档案更新 · 2026-10-07

### 更新重点

<!-- release-summary:zh:start -->
- 新增Mistral Large 4公共预览与Claude Cowork云端任务两条动态，并同步本期速览；共83条动态、49项持续关注。
- 更新Ollama v0.40.0、vLLM v0.31.0、Claude Code v2.1.292档案，分别说明运行条件、迁移配置和任务修复，保留历史版本。
- 新增Ollama／vLLM固定README与许可证共四份原文，网页与MCP可读取；其他官方正文保留链接及缺口说明。
- 保留Mistral官方参数口径差异与权重未开放状态；明确Cowork云端任务与本机资源在线条件。AA152／Arena92及原核对日期保持。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Add Mistral Large 4 public preview and Claude Cowork cloud-task developments and refresh the overview: 83 developments and 49 watch profiles.
- Update Ollama v0.40.0, vLLM v0.31.0 and Claude Code v2.1.292 profiles with runtime requirements, migration changes and task fixes while retaining historical versions.
- Add four fixed README and license documents for Ollama and vLLM, readable through the website and MCP; other official originals remain linked with explicit coverage gaps.
- Preserve conflicting Mistral parameter descriptions and pending weights, explain Cowork local-resource availability, and retain AA's 152 points, Arena's 92 points and their review dates.
<!-- release-summary:en:end -->

对应REQ-4、REQ-6、REQ-8/9、REQ-11。用户明确批准10月7日日报A–E；本批无接口或数据库结构修改，保留Codex专题及同步入口。没有运行上游性能或安全复测，REQ-19仍未开发；选题分页核验、全对象内容对照及日报准时交付缺口保留。113项回归、双端正式页面、18次MCP调用及四份原文完整哈希、正式v1.8.2已验，见[本批证据](docs/validation/2026-10-07-editorial.md)。

<a id="v1.8.1"></a>
## v1.8.1 · For your AI补充Codex每日同步入口 · 2026-10-06

### 更新重点

<!-- release-summary:zh:start -->
- 在For your AI页首和连接方式后提供Codex专题入口，复用连接地址、范围选择及每日同步说明。
- 在“接入后，可以这样问”增加首次全量、之后每日新增／更正／撤回的双语示例和专用工具说明；无脚本HTML可读。
- 明确由支持定时任务的AI客户端配置每日北京时间22:30接收，连接本身不创建任务。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Add a Codex topic entry in the For your AI header and after connection setup, reusing the connection URL, sync scopes and daily instructions.
- Add a bilingual initial-full/daily-changes example and dedicated-tool guidance under “After connecting, try this,” with readable static HTML.
- Explain that the AI client must configure daily reads at 22:30 Beijing time; connecting alone does not create a scheduled task.
<!-- release-summary:en:end -->

完善[REQ-8-1](FieldToFit-PM.md#req-8-1)与[REQ-20-10](FieldToFit-PM.md#req-20-10)的接入页面发现及示例。通用资料连接与专题连接明确区分，复用现有专题控件；不改MCP契约、公开日志或既有22:00／22:30日程。实际检查见[本批验收](docs/validation/2026-10-06-codex-overview-posts.md#ai-page-sync)。

<a id="v1.8.0"></a>
## v1.8.0 · 紧凑月历与Codex专题每日同步 · 2026-10-06

### 更新重点

<!-- release-summary:zh:start -->
- 月历默认折叠连续空白周，显示一条摘要及剩余项数，支持范围展开、完整月份、今天与视图偏好，保留日历条及所选日志。
- 新增专题MCP连接/api/mcp/codex和单一codex_updates工具，首次全量、之后同步新增／更正／撤回，支持范围、分页、过期恢复与同源出处。
- 专题提供连接地址与每日同步说明；只读客户端完整保存缓存后才推进位置，本聊天已配置每日北京时间22:30接收。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Fold consecutive empty calendar weeks by default, show one summary plus remaining counts, and support range/full-month expansion, today and remembered preferences while preserving strip views and selected logs.
- Add the topic MCP connection /api/mcp/codex with one codex_updates tool for initial full reads and subsequent additions, corrections and removals, including scoped pagination, expiry recovery and shared sources.
- Provide connection and daily-sync instructions plus a read-only client that advances its checkpoint only after saving the complete cache; daily reads at 22:30 Beijing time are configured for this chat.
<!-- release-summary:en:end -->

实现[REQ-20-9](FieldToFit-PM.md#req-20-9)与[REQ-20-10](FieldToFit-PM.md#req-20-10)，用户明确确认v1.8.0。既有MCP及新闻发布集合兼容，无数据库迁移或新闻内容变更；专题同步位置仅保存公开ID／哈希，实际正文每页重新检查当前发布权限。一次窗口合并为最新已发布状态，更正保留原事件日期；恢复全量后替换所选范围缓存。开发、验证、部署与客户端日程的实际结果见[本批验收](docs/validation/2026-10-06-codex-overview-posts.md#compact-mcp-implementation)，配置不冒充连续自然日运行。

<a id="v1.7.4"></a>
## v1.7.4 · 紧凑月历与专题MCP需求登记 · 2026-10-06
<!-- release-tag:unpublished -->

### 更新重点

<!-- release-summary:zh:start -->
- 新增REQ-20-9，提出按整周折叠空白日期、缩短日志格与完整月份展开方案，保留月历／日历条和所选详情。
- 新增REQ-20-10，按用户选择登记AI客户端每日同步：专题专用MCP首次全量，之后接收新增、更正与撤回，保留同源出处和修订。
- 交付两种日历交互预览及接口提案；新功能尚未开发部署，正式站保持v1.7.3，客户端日程尚未配置。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Register REQ-20-9 with a proposal to fold empty calendar weeks, shorten log cells and expand the full month, preserving month/strip views and selected details.
- Register REQ-20-10 for the selected daily AI-client sync: a topic-specific MCP connection reads all logs initially, then additions, corrections and removals with shared sources and revisions.
- Deliver two interactive calendar previews and an interface proposal. The new features remain unbuilt and undeployed; production stays at v1.7.3 and no client schedule is configured.
<!-- release-summary:en:end -->

新增[REQ-20-9](FieldToFit-PM.md#req-20-9)与[REQ-20-10](FieldToFit-PM.md#req-20-10)，总计20项主REQ／128项子REQ。修正文首当前状态与验收导航中的旧描述，保留历史批次证据。本批只修改需求、方案、检查记录及版本元数据；不修改网站组件、生产日志、MCP行为或原22:00任务。候选连接地址及工具未启用，每日主动读取依赖客户端定时能力和保存同步位置。实际预览、协议核查及文档验证见[本批检查](docs/validation/2026-10-06-codex-overview-posts.md#compact-mcp-alignment)。

<a id="v1.7.3"></a>
## v1.7.3 · Codex月历概览与Tibo原帖卡片 · 2026-10-06

### 更新重点

<!-- release-summary:zh:start -->
- 新增月历／日历条切换、每日摘要、跨月和今天导航，保存视图偏好并保持所选日志。
- 在提速日志附上Tibo原帖摘录、中文摘译和真实X头像；英文原文、出处及相关回复可折叠阅读。
- 后台可审核概览、原帖和头像资料，网页、无脚本HTML、API、MCP及AI交接共用同一发布修订。
- 修复构建验收发现的既有source-map-js传递依赖漏洞，采用兼容补丁版1.2.2。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Add month-calendar and date-strip views with daily summaries, month and today navigation, remembered preferences and preserved log selection.
- Attach Tibo's original excerpt, Chinese translation and matching X avatar to the speed announcement, with expandable originals, provenance and related posts.
- Review overview, post and avatar data in the existing editor; share one published revision across the website, static HTML, API, MCP and AI handoff.
- Patch the existing source-map-js build dependency to compatible version 1.2.2 after build verification identified its advisory.
<!-- release-summary:en:end -->

实现[REQ-20-7](FieldToFit-PM.md#req-20-7)与[REQ-20-8](FieldToFit-PM.md#req-20-8)，20项主REQ／126项子REQ不变。沿用既有发布集合，无数据库迁移或新增公开接口。仅更新已批准的五项概览及D-78原帖／头像资料，不从示例截图补造重置。头像从官方社区Tibo原帖嵌入核对并缓存，不声称实时读取当前X个人页；正文明确为摘录。162项相关测试、三宽度本地及正式站交互与同源读取通过，v1.7.3已正式部署；22:00提示已同步，未来实际触发仍待验。实际开发、验证与部署状态见[验收记录](docs/validation/2026-10-06-codex-overview-posts.md#implementation)。

<a id="v1.7.2"></a>
## v1.7.2 · Codex月历切换与真实头像方案对齐 · 2026-10-06
<!-- release-tag:unpublished -->

### 更新重点

<!-- release-summary:zh:start -->
- 按用户新要求将REQ-20-7改为可切换的月历／日历条，共享所选日期与日志详情；月历展示完整自然日期，事件标记只来自已审日志。
- 明确REQ-20-8使用Tibo在X的同款真实头像并保存出处；对话预览使用用户原帖截图中的头像，已定位官方社区原帖嵌入的头像来源。
- 修订需求和交互方案，区分自然日期网格与待核实／生效状态，保持同源审核规则；新能力尚未开发部署，正式站仍为v1.7.0。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Revise REQ-20-7 to support month-calendar and date-strip views sharing the selected date and log details. Show complete calendar dates, with event marks drawn only from reviewed logs.
- Require Tibo's matching real X avatar with source provenance in REQ-20-8. The conversation preview uses the avatar from the user's post screenshot; its source has been located in the official community's embedded post.
- Update requirements and interactions, separating calendar structure from unverified or pending-effect states while preserving shared review rules. These additions remain unbuilt and undeployed; production stays at v1.7.0.
<!-- release-summary:en:end -->

对应[REQ-20-7](FieldToFit-PM.md#req-20-7)与[REQ-20-8](FieldToFit-PM.md#req-20-8)，沿用编号与20项主REQ／126项子REQ。用户此次明确允许月历自然日期网格，并要求产品内可切换月历／日历条；旧的按周卡片建议被取代。截图中的额度重置次数及状态不是新增事实，不据此发布。头像已找到官方原帖嵌入出处，X当前个人页直接读取仍受阻，预览复用用户提供的头像快照，不声称实时核对当前头像。仅交付方案修订与文档批次，未修改网站组件、公开接口、生产数据或夜间任务。实际来源和演示检查见[对齐记录](docs/validation/2026-10-06-codex-overview-posts.md#month-avatar-alignment)。

<a id="v1.7.1"></a>
## v1.7.1 · Codex日历概览与原帖卡片需求登记 · 2026-10-06
<!-- release-tag:unpublished -->

### 更新重点

<!-- release-summary:zh:start -->
- 新增REQ-20-7：在每日日志详情前展示日历式概览，每日简述更新／已生效重置，点击日期阅读详情。
- 新增REQ-20-8：在对应事件下附Tibo原帖卡片，区分中文译文、英文原文、主公告与补充回复，并保留X原帖入口。
- 交付需求与交互方案，保留只展示已审真实日志、日期精度和同源审核规则；两项尚未开发、部署，正式站仍为v1.7.0。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Add REQ-20-7 for a calendar-style overview before daily details, with concise summaries of updates or effective resets and date-based drill-down.
- Add REQ-20-8 for Tibo source-post cards below related events, separating Chinese translations, English originals, primary announcements and supplementary replies, with links to X.
- Deliver requirements and interaction proposals while retaining reviewed-log, date-precision and shared-publication rules. Both additions remain unbuilt and undeployed; production remains v1.7.0.
<!-- release-summary:en:end -->

对应[REQ-20-7](FieldToFit-PM.md#req-20-7)与[REQ-20-8](FieldToFit-PM.md#req-20-8)。新增两个子REQ，总计20项主REQ、126项子REQ。本批只登记方案并同步版本文档；既有日期导航及来源链接已上线，但尚不具备概览摘要或原帖卡片。用户截图用作界面参考，10月2／3日内容不据此补成10月5日起的专题事件。未修改网站组件、公开接口、生产数据或夜间任务；新方案待对齐。实际文档与演示检查见[登记与检查记录](docs/validation/2026-10-06-codex-overview-posts.md)。

<a id="v1.7.0"></a>
## v1.7.0 · Codex 28天进化日志 · 2026-10-06

### 更新重点

<!-- release-summary:zh:start -->
- 上线「Codex 28天进化日志」，与本期速览、发布与更新同级；提供日期导航、最新日志与倒序时间线，支持手机、明暗主题及AI交接。
- 从北京时间10月5日起算，补录约50%默认提速和CLI 0.160.1修复；其他OpenAI公告独立归组，复用textGrain并新增API HIPAA入口、ChatGPT Ads测量更新。
- 网页、公开HTML、API与MCP共用审核发布记录、修订和来源；增加后台专题编辑、日期精度与重置范围校验，接入22:00夜间准备流程。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Launch Codex: 28 Days of Progress alongside At a glance and Releases & updates, with date navigation, latest logs, a reverse chronological timeline, mobile and theme support, and AI handoff.
- Start on October 5 in Beijing and backfill the announced ~50% default speed improvement and CLI 0.160.1 fix. Group other OpenAI announcements separately, reusing textGrain and adding API HIPAA self-service and ChatGPT Ads measurement updates.
- Share reviewed publication records, revisions and sources across the website, public HTML, API and MCP. Add topic editing and validation of date precision and reset scope, and connect the 22:00 nightly preparation workflow.
<!-- release-summary:en:end -->

对应[REQ-20](FieldToFit-PM.md#req-20)。用户确认minor升级至v1.7.0；保留现有公开接口与内容编号，无数据库表迁移。仅公开已审真实日志；来源只给日期时不推造北京时刻，本站日历编号与官方Day分开。约50%是官方声称，本站未实测；免费自动审核原文和免费范围继续留内部补核。22:00为检查触发时间，后续每批新内容仍须具体确认；首次定时执行、连续三日及最终收尾须在实际发生后验收。实现、补录与部署证据见[专题验收](docs/validation/2026-10-06-codex-progress.md)。

<a id="v1.6.6"></a>
## v1.6.6 · Codex夜间安排与历史补录准备 · 2026-10-06
<!-- release-tag:unpublished -->

### 更新重点

<!-- release-summary:zh:start -->
- 按用户对齐结果，为「Codex 28天进化日志」配置北京时间每天22:00的独立检查日程，回查晚到更新；11月2日作末次补查，保留原晨报安排。
- 核对承诺原帖嵌入与帖子ID时间，按北京时间10月5日为Day 1；准备默认提速、CLI修复两项日志及其他OpenAI发布文案，保留官方Day编号和日期精度。
- 更新REQ-20、查询与配置证据及双语文档；免费自动审核原文仍在内部补核。专题未开发、未发布，正式站最近已验仍为v1.6.3。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Configure a separate daily 22:00 Beijing-time check for “Codex: 28 Days of Progress,” including late-arriving updates and a final November 2 catch-up. Preserve the morning editorial schedule.
- Cross-check the pledge's embedded original post and ID-derived timestamp; use October 5 in Beijing as Day 1. Prepare speed and CLI-fix logs plus other OpenAI announcements, preserving official day labels and date precision.
- Update REQ-20, research and schedule evidence, and bilingual documentation. The free Auto-review announcement still needs its primary text. The website section is unbuilt and unpublished; the last verified deployment remains v1.6.3.
<!-- release-summary:en:end -->

对应[REQ-20](FieldToFit-PM.md#req-20)。本批仅交付方案、独立heartbeat日程和可审阅补录文案；未改网站组件、数据库或公开接口，未创建网站内容草稿或部署。承诺与提速通过OpenAI社区的官方原帖嵌入读取；毫秒时间由帖子ID推导并标明方法，未声称X接口返回created_at。首次定时执行、社交公告完整覆盖和网站交互均待验。实际来源、日程回读、准备内容与文档检查见[本批证据](docs/validation/2026-10-06-codex-28-days-proposal.md#nightly-backfill)。

<a id="v1.6.5"></a>
## v1.6.5 · Codex日志展示与发布时间方案修订 · 2026-10-06
<!-- release-tag:unpublished -->

### 更新重点

<!-- release-summary:zh:start -->
- 按用户反馈修订REQ-20：网站只展示已核实的当日更新日志，取消待核实／核对失败状态、空白日占位及兑现评分，改用日期导航＋倒序时间线。
- 核对近期11次Codex CLI正式发布的精确时间，保存UTC、北京／PT换算和官方出处；区分CLI样本与功能／额度重置公告。
- 提出北京时间12:00主核对＋18:00补查及按北京时间归入日志的方案，时点仍待对齐；未改日程、未开发部署，正式站最近已验版本仍为v1.6.3。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Revise REQ-20 to show only verified daily updates. Remove public verification-failure states, unverified or empty-day placeholders and pledge scoring; propose date navigation with a reverse chronological timeline.
- Check precise publication times for 11 recent stable Codex CLI releases and retain UTC, Beijing/Pacific conversions and official sources. Distinguish CLI timing from product and usage-reset announcements.
- Propose a noon main check and 18:00 follow-up in Beijing time, with logs grouped by Beijing publication date. Timing remains under discussion; schedules and production are unchanged, with the last verified deployment at v1.6.3.
<!-- release-summary:en:end -->

对应[REQ-20](FieldToFit-PM.md#req-20)，仅交付方案修订和查询证据，不修改网站组件、数据库或公开接口。11次样本中9次在北京时间02:00–11:00，5次晚于08:00；样本不能作为Tibo或全部Codex更新的固定发布时间。原帖及完整专题公告时段仍未核实。元数据及文档检查见[本次实际记录](docs/validation/2026-10-06-codex-28-days-proposal.md#release-time-alignment)；未配置新的检查时点，未创建网站内容草稿或发布。

<a id="v1.6.4"></a>
## v1.6.4 · Codex 28天专题需求与可视化方案 · 2026-10-06
<!-- release-tag:unpublished -->

### 更新重点

<!-- release-summary:zh:start -->
- 登记REQ-20及六个子项，推荐「Codex 28天进化日志」，作为近期动态内与本期速览、发布与更新同级的专题。
- 提出28格状态日历＋倒序时间线、每日官方证据核对、日期和额度重置状态、审核后发布及专题收尾方案。
- 本批仅交付需求与文档，专题未开发、未上线，日程未变；正式站保持v1.6.3。原帖正文与28天起算口径仍待核实。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Register REQ-20 and six child requirements for “Codex: 28 Days of Progress,” a peer section to At a glance and Releases & updates within Recent developments.
- Propose a 28-day status calendar with a reverse chronological timeline, daily official-source checks, date and usage-reset states, reviewed publication and an end-of-series recap.
- Deliver requirements and documentation only. The feature is unbuilt and undeployed, schedules are unchanged, and production remains v1.6.3. The original post and campaign start convention still need verification.
<!-- release-summary:en:end -->

对应[REQ-20](FieldToFit-PM.md#req-20)，依赖REQ-2／5／6／8／9／10／11／19；本批不修改公开接口、数据库、前台组件或生产内容。官方日志及CLI 0.160.1发布正文已取得，Tibo原帖直接读取403；不将第三方解释记为官方28天日期，也不将CLI修复记为承诺已兑现。文档及版本检查见[本次实际验证](docs/validation/2026-10-06-codex-28-days-proposal.md)。未部署、未推送发布标签，专题具体方案待对齐。

<a id="v1.6.3"></a>
## v1.6.3 · Beam、Web Search API 与持续关注更新 · 2026-10-06

### 更新重点

<!-- release-summary:zh:start -->
- 新增Beam、Cloudflare Web Search API、OpenAI textGrain三条动态，速览同步；当前77条动态、49项持续关注。
- 新增Cloudflare搜索工具档案，补充GPT水印采用说明，更新ComfyUI 0.39、Pi 1.0.4和Deep Agents SDK 0.7.22版本资料，保留历史版本。
- 增加12份固定原文及许可供网页与MCP读取：Cloudflare文档、Pi README与MCP说明、ComfyUI和Deep Agents README及各自许可。Beam与textGrain官方正文仍仅提供链接。
- Beam权重尚未开放、textGrain分阶段范围和检测局限均明确说明；AA152／Arena92点及来源日期保持。同步中英文README、项目管理和验证记录。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Add Beam, Cloudflare Web Search API and OpenAI textGrain developments and refresh the overview: 77 developments and 49 watch profiles.
- Add a Cloudflare search tool profile and GPT watermark adoption notes; update ComfyUI 0.39, Pi 1.0.4 and Deep Agents SDK 0.7.22 while preserving earlier versions.
- Provide 12 fixed source documents and license texts through the website and MCP: Cloudflare documentation, Pi README and MCP guide, and ComfyUI and Deep Agents READMEs with their licenses. Beam and textGrain originals remain links.
- Explain Beam's pending weights and textGrain's rollout and detection limitations. Preserve AA's 152 points, Arena's 92 points and their dates; synchronize bilingual READMEs, project management and verification records.
<!-- release-summary:en:end -->

对应REQ-4、REQ-6、REQ-8/9、REQ-11；本次为用户批准10月6日日报A–F的内容发布，无数据库结构或API修改。CC BY 4.0、GPL-3.0、MIT材料逐份保留原作者、固定来源和许可，文档源文件未改写；没有安装上游软件或复测性能。REQ-19结构化台账仍未开发。131项回归、双端页面、39次MCP调用与12份原文完整哈希、正式v1.6.3及站点地图均已核对，见[本批验证](docs/validation/2026-10-06-editorial.md)。

<a id="v1.6.2"></a>
## v1.6.2 · Strata 与五项持续关注档案更新 · 2026-10-05

### 更新重点

<!-- release-summary:zh:start -->
- 新增Strata动态与工具档案，说明消费级显卡、量化和内存条件；当前74条动态、48项持续关注。
- 补齐GPT-6 Sol/Luna、GPT-6.1 Sol和Claude Opus/Sonnet 5.5版本表，关联已发布动态，保留历史型号，不重复发新闻。
- 更新Claude Code权限修复、DeepSeek Harness预览能力及Addy Skills执行流程与错误指令修正；增加11份固定原文与许可供网页和MCP读取。
- 修复关联动态事件在缓冲写入后读取数据库导致的发布500；关联快照先读取并参与并发校验，材料观测与关系操作沿用同一修正。
- Claude Code正文再分发许可未确认，保留官方链接与解读；AA152点、Arena92点及核对日期保持。同步中英文README、项目管理与验证记录。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Add a Strata development and tool profile with hardware, quantization and memory requirements: 74 developments and 48 watch profiles.
- Bring GPT-6 Sol/Luna, GPT-6.1 Sol and Claude Opus/Sonnet 5.5 into their existing version tables, linking published developments and preserving historical entries without duplicate news.
- Update Claude Code permission fixes, DeepSeek Harness preview capabilities and Addy Skills workflow and instruction corrections. Add 11 fixed source documents and license texts for web and MCP reading.
- Fix publication failures caused by reading related-news context after buffered writes. Snapshot associations before writes and retain concurrency checks across publication, material observations and relationship changes.
- Keep Claude Code originals as links while redistribution rights remain unverified. Preserve AA's 152 points, Arena's 92 points and their dates; synchronize bilingual READMEs, project management and verification records.
<!-- release-summary:en:end -->

对应REQ-4、REQ-6、REQ-8/9、REQ-11；本次为用户明确批准10月5日日报A–F的内容交付，不代表REQ-19台账功能已实现。无数据库结构或API变更。原始发布日期、订阅记录时间与本站核对日期分开记录。本站未部署上游工具或复测性能/安全修复；115项回归、双端预览和正式页面、35次MCP读取及11份全文哈希、v1.6.2部署已验，见[本批证据](docs/validation/2026-10-05-editorial.md)。

<a id="v1.6.1"></a>
## v1.6.1 · 修正本期速览整列留白 · 2026-10-04

### 更新重点

<!-- release-summary:zh:start -->
- 本期速览改为顶部通栏主精选、下方两列紧凑条目，取消主精选跨四行造成的整列留白。
- 相关图片与所属条目的文字并排；保留出处，完整图注、版本和许可在放大窗口展示，手机按原顺序单列阅读。
- 保留已审正文、精选顺序、关注与动态筛选行为；六种宽度布局检查和25项阅读回归通过，正式域名版本、双端布局与图片交互已验。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Place the lead briefing across the top with a two-column grid beneath, removing the empty column caused by a four-row lead span.
- Keep each image beside its own story and retain its source. Full captions, revision and license details remain in the enlarged view; mobile uses the original reading order in one column.
- Preserve reviewed text, editorial order, follows and archive filters. Six viewport layout checks and 25 reading regressions pass; production version, responsive layout and image interactions are verified.
<!-- release-summary:en:end -->

对应REQ-6-2。仅调整速览布局，不修改公开内容或数据库结构。[布局修正验收](docs/validation/2026-10-04-follow-traffic.md#glance-layout-fix)。

<a id="v1.6.0"></a>
## v1.6.0 · 无账号关注、私有统计与阅读改版 · 2026-10-04

### 更新重点

<!-- release-summary:zh:start -->
- 上线无账号关注、我关注的更新、独立已读／检查进度、导入导出与旧收藏预览迁移；清单留在当前浏览器。
- 为 HTTP/MCP 增加显式包含直接关联动态的变化范围与初始化基线，提供个人 AI 清单交接说明，保留原接口默认语义。
- 新增 UV/PV、内容可见事件、来源、复访和成功导出／取材聚合，以及私有统计后台与 CSV；新增独立统计表，生产增量迁移与部署已验。
- 将既有对象每日官方更新核对加入原日报日程；新增 REQ-19；上线 B 图文速览与媒体审核、紧凑日期列表及分层 overview；保留旧链接和完整详情。D-72官方配图已在正式前台显示；生产备份、增量迁移、云端构建和双端发布验收通过，自然跨日观察仍待完成。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Ship anonymous browser-local follows, unread updates, independent read/check progress, import/export and explicit legacy-save migration previews. Lists remain in the current browser.
- Add opt-in direct-related-news scope and baseline initialization to HTTP/MCP changes, with personal AI handoff guidance and unchanged default API behavior.
- Add aggregate UV/PV, visible content, entry sources, returning browsers and successful exports/source reads, plus a private dashboard and CSV. The additive production migration and deployment are verified.
- Add daily official update checks for existing profiles to the original briefing schedule. Record REQ-19 and implement the image-led briefing with reviewed media, date-grouped release lists and layered section overviews; preserve detail links and existing reads. Display D-72’s reviewed official image in production. Verify the backup, additive migration, cloud build and desktop/mobile deployment; natural cross-day observation remains pending.
<!-- release-summary:en:end -->

对应 REQ-6-12、REQ-9-5/8、REQ-17-1至4、REQ-14-3。用户于2026-10-04确认完整模块的minor升级至v1.6.0；账号和自动同步仍关闭。数据库迁移仅新增统计表，原累计次数和内容保留；关闭详细分析开关可回退到既有计数。真实AI连接回执、生产连续三日及独立客户端跨日仍待完成。保留73条动态／47项持续关注的正文与图表快照，仅为D-72补充已审配图。本地与正式部署验证、日程配置和待验边界见[验收记录](docs/validation/2026-10-04-follow-traffic.md)，已按[部署指南](docs/guides/deployment.md)完成本批上线。

<a id="v1.5.24"></a>
## v1.5.24 · Kolibri、昇腾工具与科研和交互资源 · 2026-10-04

### 更新重点

<!-- release-summary:zh:start -->
- 发布Kolibri、DeepSeek昇腾工具、BootLoops、AG-UI 1.0、Supabase/Turso五条动态，同步本期速览；当前73条动态、47项持续关注。
- 新增Kolibri模型、BootLoops Harness与AG-UI工具档案；为DeepSeek补充昇腾计算和专家通信资料，保留旧内容。
- 网页与MCP共享九份新增固定原文与许可，说明模型内存门槛、硬件配套、科研验证与SDK迁移条件；DeepEP许可未核实，保留链接。
- AA152点、Arena92点及核对日期保持；同步中英文README、项目管理总览与实际发布证据。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Publish five developments covering Kolibri, DeepSeek Ascend tools, BootLoops, AG-UI 1.0 and Supabase/Turso, refreshing the overview: 73 developments and 47 watch profiles.
- Add Kolibri, BootLoops and AG-UI profiles; extend DeepSeek with Ascend computation and expert communication material while preserving previous content.
- Share nine new fixed originals and license texts through web and MCP. Explain model memory, hardware availability, research verification and SDK migration limits; retain DeepEP as links while licensing remains unverified.
- Preserve AA's 152 points, Arena's 92 points and their review dates. Synchronize bilingual READMEs, project management and publication evidence.
<!-- release-summary:en:end -->

对应REQ-4、REQ-6、REQ-8-9、REQ-9、REQ-11。无数据库结构或接口变更。发布日期与本站核对日期分别记录，不将9月30日资源补录冒充10月4日首发。原文许可逐份保留，未运行上游模型、科研工具或硬件。56项回归、双端预览与正式页面、34次MCP读取、九份完整原文及v1.5.24部署已验，见[验收记录](docs/validation/2026-10-04-editorial.md)。

<a id="v1.5.23"></a>
## v1.5.23 · 五项动态、Muse Gadgets 与 AstaBrief · 2026-10-03

### 更新重点

<!-- release-summary:zh:start -->
- 发布FLUX 3 Image、Muse Gadgets、llama.cpp决策模型、AstaBrief、微软MAI语音模型五项动态，并同步本期速览；当前68条动态、44项持续关注。
- 新增Muse Gadgets工具与AstaBrief模型档案；为Laya补充llama.cpp接入说明，保留旧版本和原文。
- 网页与MCP共享八份新增固定文档与许可：Muse设备SDK、Linux说明，llama.cpp服务器接口和AstaBrief模型卡；明确权限、支持范围、检查点与许可差异。
- AA152点、Arena92点及各自核对日期保持；同步中英文README、项目管理总览和实际发布验收。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Publish five developments covering FLUX 3 Image, Muse Gadgets, decision models in llama.cpp, AstaBrief and Microsoft MAI audio models, and refresh the overview: 68 developments and 44 watch profiles.
- Add Muse Gadgets and AstaBrief profiles; extend Laya with llama.cpp integration material while preserving existing versions and originals.
- Share eight new fixed documents and license texts through web and MCP, including device SDK, Linux permissions, server API and model-card guidance. Explain support, checkpoint and licensing boundaries.
- Preserve AA's 152 points, Arena's 92 points and their review dates. Synchronize bilingual READMEs, project management and publication evidence.
<!-- release-summary:en:end -->

对应REQ-4、REQ-6、REQ-8-9、REQ-9、REQ-11。无数据库结构或API变更。Muse官网未标精确发布日，事件日期按仓库创建时间说明；AstaBrief技术介绍日期不等于仓库创建日；llama.cpp本次尚不支持Clef。85项回归、双端预览／正式页面、31次MCP协议调用、完整原文回读与v1.5.23部署已核对，见[验收记录](docs/validation/2026-10-03-editorial.md)。独立客户端跨日及连续全来源验收仍待完成。

<a id="v1.5.22"></a>
## v1.5.22 · 六项动态、固定原文与 AA 完整快照 · 2026-10-02

### 更新重点

<!-- release-summary:zh:start -->
- 发布 Gemini 4 Argon、Pi 1.0、Clef、Google Skills、Data Agent Kit 和 Olmo-core 3 六条动态，速览同步前五项；当前63条动态、42项持续关注。
- 更新 Gemini、Pi；新增 Clef、Data Agent Kit、Olmo-core，网页与MCP共享十份新增固定原文及MIT/Apache-2.0许可。
- AA完整快照更新为152个可绘制配置，306个2026年配置中154个缺坐标；修复releaseSlug发布日期映射，保留原始名称与空值；Arena92点及原日期保持。
- Google旗舰更新为Argon；Arena旧快照未收录该系列时明确显示缺项。同步双语README、项目管理总览及真实验收记录。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Publish six developments: Gemini 4 Argon, Pi 1.0, Clef, Google Skills, Data Agent Kit and Olmo-core 3; feature the first five in the overview: 63 developments and 42 watch profiles.
- Update Gemini and Pi; add Clef, Data Agent Kit and Olmo-core. Share ten new fixed originals with MIT/Apache-2.0 license text through web and MCP.
- Refresh the complete AA snapshot: 152 plotted configurations and 154 missing coordinates among 306 releases from 2026. Resolve releaseSlug date references and retain source names/nulls; preserve Arena's 92 points and dates.
- Select Argon as Google's flagship and explicitly show its absence in the unchanged Arena snapshot. Synchronize bilingual READMEs, project management and validation evidence.
<!-- release-summary:en:end -->

对应REQ-4、REQ-6、REQ-7、REQ-8-9、REQ-9、REQ-11。图表只采用本次整批来源值，不混用旧分数；AA榜单标示v4.3，Argon详情方法页细分v4.3.2，页面说明保留此区别。无数据库结构或API变更。发布、93项回归、47次MCP协议调用、双端页面及v1.5.22正式部署已核对，见[验收记录](docs/validation/2026-10-02-editorial.md)。独立AI客户端跨日验收和连续全来源成功仍未完成。

<a id="v1.5.21"></a>
## v1.5.21 · 五项动态与 Kumo Tabular 固定原文 · 2026-09-30

### 更新重点

<!-- release-summary:zh:start -->
- 发布 GPT-6.1 Sol、Dots、DevDay 开发工具、Muse for Small Business、Kumo Tabular 五条动态，本期速览同步五项。
- 持续关注新增 Kumo Tabular：表格上下文分类与回归、采用入口、版本及限制；当前57条动态、39项持续关注。
- 网页与MCP提供 Kumo 的固定模型卡、代码README、第三方许可说明、Apache-2.0及OpenMDW-1.1全文，保留版本、署名与许可。
- 明确Sol缓存／长上下文价格、Dots权限及额度、MCP Events提案、Decisions有限预览与Muse地区边界；AA133／Arena92图表保持既有快照。同步双语README、项目管理总览与验收记录。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Publish five developments: GPT-6.1 Sol, Dots, DevDay developer tools, Muse for Small Business and Kumo Tabular; refresh all five overview entries.
- Add Kumo Tabular to Model watch profiles with tabular in-context prediction, adoption requirements and limitations: 57 developments and 39 watch profiles.
- Share five fixed Kumo originals via web and MCP: model card, code README, third-party license statement, Apache-2.0 and OpenMDW-1.1 licenses, preserving revisions and attribution.
- Clarify Sol cache/long-context pricing, Dots permissions and usage, proposed MCP Events, limited Decisions preview and Muse availability. Preserve AA133/Arena92 snapshots and update bilingual READMEs, project management and validation.
<!-- release-summary:en:end -->

对应REQ-4、REQ-6、REQ-8-9、REQ-9、REQ-11。仅内容与版本交付，不改变数据库结构和接口。实际状态见[本批验收](docs/validation/2026-09-30-editorial.md)。准时日报、连续全来源成功及Jev官方全文缺口仍未关闭。

<a id="v1.5.20"></a>
## v1.5.20 · 五项资料与 Kitesurf 接入原文 · 2026-09-29

### 更新重点

<!-- release-summary:zh:start -->
- 发布 Sonnet 5.5、Holo4、Cloudflare cf／Forge、YODAS v3 四条动态，并同步本期速览；保留原始日期、版本与采用限制。
- 持续关注新增 Kitesurf，介绍 WebMCP、Browser Run 接入、终端查看与兼容边界；当前52条动态、38项持续关注。
- 网页与MCP同步六份固定原文：Forge README与Apache-2.0许可；Kitesurf采用文档、Cloudflare授权声明、CC-BY-4.0与MIT许可证。
- 区分Sonnet单token价格与任务成本、Holo4两型号许可、YODAS标注覆盖以及Kitesurf不同日期的文档数据；AA133／Arena92保持。同步中英文README、项目管理总览与验收记录。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Publish Sonnet 5.5, Holo4, Cloudflare cf/Forge and YODAS v3, and refresh the overview while preserving original dates, versions and adoption limits.
- Add Kitesurf to Tool watch profiles, covering WebMCP, Browser Run access, terminal rendering and compatibility: 52 developments and 38 watch profiles.
- Share six fixed originals through web and MCP: Forge README and Apache-2.0 license; Kitesurf adoption documentation, Cloudflare attribution statement, CC-BY-4.0 and MIT licenses.
- Distinguish Sonnet token pricing from task cost, Holo4 model licenses, YODAS annotation coverage and dated Kitesurf documentation. Keep AA133/Arena92; update bilingual READMEs, project management and validation.
<!-- release-summary:en:end -->

对应REQ-4、REQ-6、REQ-8-9、REQ-9、REQ-11。内容及版本交付，不改变数据库结构、接口或账户权限。实际结果见[本批验收](docs/validation/2026-09-29-editorial.md)。准时日报、连续全来源成功及Jev官方全文缺口仍未关闭。

<a id="v1.5.19"></a>
## v1.5.19 · 六项资料与 relore 原文 · 2026-09-28

### 更新重点

<!-- release-summary:zh:start -->
- 发布 Copilot 本地沙箱、Nemotron 3 Diarization、LeRobot 人形机器人流程、Ember-1 和 DeepSeek DSec 五条动态，同步本期速览；原始发布日期与本站核对日分别保留。
- 持续关注新增 relore，说明已有修复检索、历史决定追溯与当前代码核验；当前48条动态、37项持续关注。
- 网页与MCP共享 relore 同一固定提交的README、部署说明、使用说明、版本记录与Apache-2.0许可证五份原文；其他材料按已核实范围提供链接。
- 保留 Ember 训练支持说明差异、DSec 未确认整体开源与各项未复测边界；AA133点／Arena92点保持。同步中英文README、项目管理总览与发布验收。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Publish five developments: Copilot local sandboxing, Nemotron 3 Diarization, LeRobot humanoids, Ember-1 and DeepSeek DSec. Refresh the overview while keeping original publication and review dates distinct.
- Add relore to the Tool watch category, covering work-in-progress discovery, historical decisions and verification against current code: 48 developments and 37 watch profiles.
- Share five originals from one fixed relore commit through web and MCP: README, operations, CLI guide, changelog and Apache-2.0 license. Other materials retain verified source links.
- Disclose conflicting Ember training availability, unconfirmed DSec platform open-source availability and untested claims. Keep the 133-point AA and 92-point Arena snapshots; update bilingual READMEs, project management and validation.
<!-- release-summary:en:end -->

对应REQ-4、REQ-6、REQ-8-9、REQ-9、REQ-11。修正三处随公开资料增长而失效的测试数据隔离，74项相关回归通过。内容与版本交付，不改变接口、数据库结构、注册或执行权限。实际结果见[本批验收](docs/validation/2026-09-28-editorial.md)。日报准时送达、连续全来源成功和Jev官方正文缺口未关闭。

<a id="v1.5.18"></a>
## v1.5.18 · Muse 实时形象与三项持续关注 · 2026-09-27

### 更新重点

<!-- release-summary:zh:start -->
- 发布 Muse Realtime Avatar 技术动态并同步本期速览；明确实时形象与 Muse Spark 文本模型的区别，保留官方指标与开放范围。
- 持续关注新增 Ollaya、Whiteboard、AgentRun，按工具／Harness展示用途、采用入口及限制；当前43条动态、36项持续关注。
- 为网页与MCP补充三个项目共10份固定提交原文，包括README、API／采用说明、版本记录、许可证和NOTICE；保留署名与SHA-256。
- 两张模型图表保留已审核AA133点、Arena92点及真实日期。同步中英文README、项目管理总览与实际发布验收。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Publish the Muse Realtime Avatar technical announcement and refresh the overview, distinguishing real-time embodiment from Muse Spark text-model scores and documenting reported metrics and availability limits.
- Add Ollaya, Whiteboard and AgentRun to the Tool/Harness watch categories with adoption paths and limitations, reaching 43 developments and 36 watch profiles.
- Provide 10 fixed-revision originals through web and MCP: READMEs, API/adoption guides, changelog, licenses and NOTICE, preserving attribution and SHA-256 hashes.
- Retain the reviewed 133-point AA and 92-point Arena snapshots and their genuine dates. Update both READMEs, the project overview and release verification evidence.
<!-- release-summary:en:end -->

对应REQ-4、REQ-6、REQ-8-9、REQ-9、REQ-11。内容发布，不改变数据库结构、注册或执行权限；MCP读取资料不会自动安装工具。实际验证见[本批验收](docs/validation/2026-09-27-editorial.md)。准时日报、连续来源成功与Jev官方正文等缺口未关闭。

<a id="v1.5.17"></a>
## v1.5.17 · 三项动态与 Arena 最新快照 · 2026-09-26

### 更新重点

<!-- release-summary:zh:start -->
- 发布已确认的 LFM2.5-VL-DSpark、Transformers GGUF 与 Gemini Connected Apps；42 条动态、33 项持续关注，本期速览同步，保留 Muse 与 Live Avatar。
- Arena 采用 9 月 25 日来源数据、9 月 26 日核对：92 个可绘制配置，新增 Muse Spark 1.3、Opus 5.5、MiMo V2.6 等点；旗舰筛选同步至 9 个有完整坐标的系列。
- AA 保留此前 133 点及原核对日期；Muse Spark 1.3 max／xhigh 已在其中。两站评分、价格单位和缺项分别展示，不互相替代。
- 为网页与 MCP 提供固定提交的 Transformers GGUF 文档及 Apache-2.0 许可证全文；其余官网材料保持仅链接，性能数字保留作者实测与本站未复测边界。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Publish the approved LFM2.5-VL-DSpark, Transformers GGUF and Gemini Connected Apps developments: 42 news items and 33 watch profiles, with an updated overview retaining Muse and Live Avatar.
- Refresh Arena using September 25 source data reviewed on September 26: 92 plotted configurations, including Muse Spark 1.3, Opus 5.5 and MiMo V2.6; nine flagship series now have complete coordinates.
- Preserve the existing 133-point AA snapshot and its review date, including Muse Spark 1.3 max/xhigh. Keep each source’s score, price unit and missing-data disclosures separate.
- Share fixed-revision Transformers GGUF documentation and its Apache-2.0 license through web and MCP. Other announcements remain link-only, and reported benchmarks are not presented as independent FieldToFit tests.
<!-- release-summary:en:end -->

对应 REQ-4、REQ-6-2、REQ-7、REQ-8-9、REQ-9、REQ-11。修复长模型版本号撑破手机动态卡片的问题。日期证据校验新增官方模型卡域名 huggingface.co，仍限制 HTTPS、精确域名和安全 URL。未变更数据库结构、凭据、注册或执行权限。实际验证及部署状态见[本批验收](docs/validation/2026-09-26-editorial.md)。

<a id="v1.5.16"></a>
## v1.5.16 · 六项动态与 Strands Harness 材料更新 · 2026-09-25

### 更新重点

<!-- release-summary:zh:start -->
- 发布用户确认的 A–F：Gemini 3.8 TTS、Antigravity SDK 本地模型、Meta Muse、Strands Harness、FLUX 3 Action 与 Gemini Live Avatar；当前 39 条动态、33 项持续关注。
- 本期速览同步五项新动态；Strands 同时加入持续关注的 Harness 分类，以表格说明默认机制、采用入口及限制。既有动态仍保留。
- Antigravity、Strands 与 FLUX 提供 10 份去重后的固定版本原文，包括 README、采用说明、许可证及 NOTICE；网页和 MCP 共享材料，未取得再分发许可的公告仍仅链接。
- 保留真实原文日期、本站核对日及使用边界；FLUX 代码文档的 Apache-2.0 不替代模型权重的自定义许可。两张模型图表保持此前已审核快照。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Publish the approved A–F topics: Gemini 3.8 TTS, local models in Antigravity SDK, Meta Muse, Strands Harness, FLUX 3 Action and Gemini Live Avatar, reaching 39 developments and 33 watch profiles.
- Refresh the five-item overview and add Strands to the Harness watch category, documenting default mechanisms, adoption paths and limitations while retaining earlier developments.
- Provide 10 distinct fixed-revision originals from Antigravity, Strands and FLUX, including READMEs, adoption guides, licenses and NOTICE files. Web and MCP share these materials; unlicensed announcements remain link-only.
- Preserve original dates, review dates and availability boundaries. Apache-2.0 for FLUX repository code and documentation does not replace the model weights’ custom license. Existing reviewed model chart snapshots are retained.
<!-- release-summary:en:end -->

对应 REQ-4、REQ-6-2、REQ-8-9、REQ-9、REQ-11。未变更数据库结构、接口、注册或执行权限；MCP读取材料不安装或执行外部工具。各项真实验证与部署状态见[本批验收](docs/validation/2026-09-25-editorial.md)。

<a id="v1.5.15"></a>
## v1.5.15 · 站点地图读取提速 · 2026-09-23

### 更新重点

<!-- release-summary:zh:start -->
- 站点地图改为一次只读事务获取公开集合、归并关系和真实更新时间，省去重复的远程维护状态查询；正式响应从约 8.7–9.1 秒降至 2.11–2.67 秒。
- 保留同源公开校验、草稿与下架排除、归并排除和无缓存规则；现有介绍及正文不改写。
- Google 域名 DNS 验证已完成，地图已提交且实际网址测试通过；地图报告仍显示无法抓取，尚未确认成功读取或收录。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Read published collections, reviewed merges and genuine modification dates in one read-only transaction for the sitemap, removing repeated remote maintenance lookups; production responses improved from about 8.7–9.1 seconds to 2.11–2.67 seconds.
- Preserve shared public validation, draft/withdrawal/merge exclusions and no-cache behavior without rewriting existing introductions or content.
- Google domain DNS verification is complete, and the submitted sitemap passed a live URL test; its report still shows a fetch failure, with successful processing and indexing unconfirmed.
<!-- release-summary:en:end -->

对应 REQ-18-4/5/6。合入 v1.5.14 最新内容，保留全部 70 个地图网址和日期。34 项相关测试、远端构建、正式单次 Turso 读取及健康／MCP 版本通过。实测原地图响应约 8.7 秒；本批解决已确认的读取开销，不将其推断为 Google 失败的确定原因。不新增数据库或缓存，不变更公开 API/MCP。实际验证与上线结果见[搜索验收记录](docs/validation/2026-09-22-search.md)。

<a id="v1.5.14"></a>
## v1.5.14 · 五项动态与模型图表更新 · 2026-09-23

### 更新重点

<!-- release-summary:zh:start -->
- 发布 Opus 5.5、GPT-6 Sol/Luna、Step 5 Preview、阿里云 AI 路线图及 rabbitOS 3 五项确认内容；速览加入前两项，保留原有动态，当前 33 条动态、32 项持续关注。
- 更新 AA / Arena 两张能力与价格图至本站 9 月 23 日核对快照，分别绘制 133 / 84 个配置；保留各自单位、评分区间及缺项，Arena 来源截止日为 9 月 13 日。
- 旗舰名单更新 Opus 5.5、Grok 4.7 和 MiMo V2.6 Pro；未进入 Arena 或缺价格的系列明确说明，不拿旧系列代替。兼容 AA 新数值成本字段，避免误用 token 单价。
- 网页与 AI 同源资料保留原始出处、日期和限制；新增五项的官网正文均仅链接，不声称已提供原文全文。实际验收与部署状态见本批证据。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Publish the five approved developments on Opus 5.5, GPT-6 Sol/Luna, Step 5 Preview, Alibaba’s AI roadmap and rabbitOS 3; feature the first two while retaining earlier news, for 33 developments and 32 profiles.
- Refresh AA and Arena snapshots reviewed on September 23, plotting 133 and 84 configurations with independent units, score intervals and explicit gaps. Arena’s source cutoff is September 13.
- Select Opus 5.5, Grok 4.7 and MiMo V2.6 Pro as current flagship representatives; show missing Arena listings or prices without substituting older series. Support AA’s numeric task-cost field without substituting token prices.
- Preserve source links, original dates and limitations in shared web and AI content. The five new developments provide links to official materials, not licensed full-text copies. Verification and deployment status are recorded below.
<!-- release-summary:en:end -->

对应 REQ-6-2、REQ-7-2/3/4/5、REQ-8-9、REQ-11。公开接口和数据库结构不变；每日来源检查仍不自动发布图表。实际数据、双端预览、回归及正式部署以[本批验收](docs/validation/2026-09-23-editorial.md)为准。

<a id="v1.5.13"></a>
## v1.5.13 · 搜索页面发布配置修正 · 2026-09-23

### 更新重点

<!-- release-summary:zh:start -->
- 纳入 v1.5.12 的搜索可读主入口、已发布内容独立页、逐页信息及自动站点地图；既有标题、介绍和正文保持原样。
- 修正 Vercel 上传排除规则，只排除根目录维护脚本，保留生成搜索页面外壳所必需的前端构建脚本；首页及 index.html 永久跳转到 For you，避免静态空壳抢先响应。
- 保留旧长页链接、公开 API/MCP 和累计访问数据；正式 65 个页面、双端 40 项检查及健康／MCP 版本通过，站长账号验证及搜索提交仍待执行。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Include v1.5.12's crawlable main pages, published detail URLs, page metadata and automatic sitemap while preserving existing titles, introductions and body copy.
- Fix the Vercel upload exclusion to omit only root maintenance scripts and retain the frontend script required to generate the search HTML shell; permanently redirect the root and index.html to For you before static-file handling.
- Preserve long-page links, public API/MCP and cumulative visits. Production verification passed for all 65 pages, 40 browser checks and health/MCP versions; webmaster verification and search submission remain pending.
<!-- release-summary:en:end -->

v1.5.12 首次远端构建因 `scripts/` 规则同时排除 `frontend/scripts/` 而失败，未替换当时的 v1.5.11 正式站。本批将规则限定为 `/scripts/`，新增修复交付按项目规则递增补丁版本；不改数据库或发布内容。初次 v1.5.13 验收另发现静态根页面抢先响应，本批追加 Vercel 根入口永久跳转并于 2026-09-23 完成线上复验。实际远端构建、正式接口与网页结果见[搜索页面验收](docs/validation/2026-09-22-search.md)。

<a id="v1.5.12"></a>
## v1.5.12 · 搜索可读页面与已发布内容独立页 · 2026-09-22

<!-- release-tag:unpublished -->

### 更新重点

<!-- release-summary:zh:start -->
- 保留现有主入口标题、介绍和正文；抽取同一份既有介绍供初始 HTML 与网页读取，没有改写宣传文案。
- 已发布动态与持续关注拥有独立网址，复用原有阅读、资料交接和访问计数组件；新分享和目录使用独立页，旧长页锚点继续可用。
- 增加同源公开 HTML、逐页搜索信息、robots 和自动 sitemap；草稿不公开，下架立即移除，归并仅跳转到公开目标，错误页返回真实状态。
- 本批开发与隔离验收记录见下方；正式站仍为 v1.5.11，尚未部署搜索功能，也未执行搜索平台验证或提交。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Preserve existing main-page titles, introductions and body copy; share the same existing introductions between initial HTML and the client without rewriting promotional text.
- Add stable URLs for published news and ongoing-watch profiles, reusing reading, handoff and visit counting; new shares and directory links open details while old long-page anchors remain valid.
- Add public HTML, page-specific metadata, robots and an automatic sitemap; exclude drafts, remove withdrawn content immediately, redirect merged identities only to public targets and return real error statuses.
- Development and isolated verification are recorded below. Production remains v1.5.11; search features have not been deployed and webmaster verification/submission has not been performed.
<!-- release-summary:en:end -->

该源码批次随后纳入 v1.5.13 正式发布，未单独创建 v1.5.12 发布标签。对应 REQ-18-1 至 4；按用户补充约束保留既有文案，REQ-18-5/6 的平台提交和效果观察仍待执行。API/MCP 内容契约与生产数据库不变；详情页不缓存，站点地图仅从公开集合生成，更新日期仅取实际发布内容变化，种子／静态页面无可靠修改日时省略。详情路由纳入现有 30 分钟访问会话。实际验收、部署准备与未验范围见[搜索页面验收](docs/validation/2026-09-22-search.md)。

<a id="v1.5.11"></a>
## v1.5.11 · 公共页脚全站累计访问次数 · 2026-09-22

### 更新重点

<!-- release-summary:zh:start -->
- 在公共页脚显示全站累计访问次数与真实统计起始日，支持手机、英文、深色主题及不可用提示。
- 按 30 分钟浏览器访问会话计数，刷新、换页、多标签页和重试不重复累加；数据库事务保证并发一致，累计值跨重启、迁移和明细清理保留。
- 提供统计说明与退出，排除隐私信号、管理、测试和已知机器人；只存短期摘要标识，不存浏览历史或完整 IP。
- 增加增量建表、启停配置和过期清理；正式站 v1.5.11、真实 Turso 迁移／事务及双端页脚已验，连续三日观察待验，搜索发现仍待开发。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Show cumulative site visits and the genuine start date in the public footer, including mobile, English, dark mode and unavailable states.
- Count 30-minute browser sessions without duplicate visits from refreshes, navigation, tabs or retries; atomic writes preserve totals through concurrency, restarts, migrations and identifier cleanup.
- Add an explanation and opt-out, respecting privacy signals and excluding administration, tests and known bots; retain only short-lived hashed identifiers, without browsing histories or full IP addresses.
- Add additive migration, collection controls and expiry cleanup; production v1.5.11, live Turso migration/transactions and desktop/mobile footers are verified. Three-day observation remains pending; search discovery is still unimplemented.
<!-- release-summary:en:end -->

对应 REQ-17-7 与 REQ-17-1/2/5/6 的首期范围。新增独立统计表及 `/api/analytics/total`、`/api/analytics/visit`；现有业务接口不变。默认停采，迁移与正式启用按[部署指南](docs/guides/deployment.md#全站访问次数)进行；不修改既有内容数据或公开账户策略。部署前合入 v1.5.10 内容提交，保留两批历史和最新公开内容。用户已对齐 REQ-18 首期为主入口与已发布内容独立页，本轮仅登记该范围，不执行 SEO 开发或提交。实际验证与未验边界见[访问次数验收](docs/validation/2026-09-22-visits.md)。

<a id="v1.5.10"></a>
## v1.5.10 · MiMo、Grok、Tokenizers 与 Laya · 2026-09-22

### 更新重点

<!-- release-summary:zh:start -->
- 发布获确认的 MiMo V2.6、Grok 4.7、Tokenizers v1 候选版三条动态，并新增 Laya 持续关注模型；MiMo 与 Grok 同步本期速览，较早动态保留。
- For your AI 新增八份可分段读取的固定材料：MiMo Pro/Flash 模型卡、Tokenizers README/发布记录/许可、Laya README/模型卡/许可；保留原文、出处、版本与再分发说明。
- 明确 MiMo 9B 的许可缺口、Grok 官方材料仅链接、Tokenizers 候选版及基准范围、Laya 任务微调与判断错误边界；未运行模型或更改图表快照。
- 更新真实日报、MCP 跨日读取及周维护证据；来源延后、失败、积压和 Jev 官方正文缺失仍明确保留。访问统计与搜索发现需求文档继续保留，功能未开发。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Publish the approved MiMo V2.6, Grok 4.7 and Tokenizers v1 release-candidate developments, add the Laya model profile, and feature MiMo and Grok in the quick overview while retaining earlier news.
- Add eight pinned readable materials for personal AI: MiMo Pro/Flash model cards, Tokenizers README/release notes/license, and Laya README/model card/license, preserving original text, sources, revisions and redistribution notices.
- State the MiMo 9B license gap, link-only Grok sources, Tokenizers prerelease and benchmark scope, and Laya fine-tuning and decision-error limitations; no model execution or chart-snapshot updates.
- Record actual briefing delivery, cross-day MCP reading and the weekly maintenance review, retaining unresolved collection failures, deferrals, backlog and missing Jev source bodies. Traffic and search-discovery requirements remain documented, without implementation.
<!-- release-summary:en:end -->

对应 REQ-4、REQ-5、REQ-6-2、REQ-8-9、REQ-9-6、REQ-11、REQ-15-5。当前内容与正式部署以[本批验收](docs/validation/2026-09-22-editorial.md)为准；无应用功能或数据库迁移变化。此前 v1.5.8/v1.5.9 文档提交保留，不覆盖其版本记录。

<a id="v1.5.9"></a>
## v1.5.9 · 全站累计访问次数需求对齐 · 2026-09-22

<!-- release-tag:unpublished -->

### 更新重点

<!-- release-summary:zh:start -->
- 将 REQ-17 首期对齐为在公共页脚展示全站累计访问次数，新增 REQ-17-7 的位置、文案及双端验收要求。
- 明确按访问会话累计、30 分钟内刷新和换页不重复计数，保留真实起始日、持久累计及故障提示。
- 详细访客、内容、来源、复访和私有后台调整为后续范围；本批仅更新需求，功能尚未开发或部署。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Align the first phase of REQ-17 with a public footer showing cumulative site visits, adding REQ-17-7 for placement, wording and desktop/mobile acceptance.
- Define session-based counting without duplicate visits from refreshes or navigation within 30 minutes, with a genuine start date, persistent totals and failure states.
- Defer detailed visitor, content, acquisition, return-visit and private dashboard analytics; this batch updates requirements only, without implementation or deployment.
<!-- release-summary:en:end -->

对应 REQ-17-7、REQ-17 首期范围与相关分期；REQ-18 搜索发现方案保留。无功能、公开 API 或数据库迁移变化。文档与版本核对见[当日需求核对记录](docs/validation/2026-09-22-traffic-search.md)。

<a id="v1.5.8"></a>
## v1.5.8 · 访问统计与搜索发现需求方案 · 2026-09-22

<!-- release-tag:unpublished -->

### 更新重点

<!-- release-summary:zh:start -->
- 新增 REQ-17：明确独立访客、浏览量、会话、内容曝光、来源与复访口径，设计站内采集和私有流量后台。
- 新增 REQ-18：规划独立内容网址、可抓取正文、逐页元数据、站点地图，以及 Google、Bing、百度验证与提交。
- 记录分期、隐私控制、兼容方案、验收条件及真实现状；本批仅交付需求文档，功能未开发、未部署，未提交搜索引擎。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Add REQ-17 with definitions for unique visitors, page views, sessions, visible content, acquisition and return visits, plus first-party collection and a private dashboard design.
- Add REQ-18 covering stable content URLs, crawlable HTML, per-page metadata, sitemaps, and verification and submission for Google, Bing and Baidu.
- Record phases, privacy controls, compatibility, acceptance criteria and observed baselines; this batch delivers requirements only, without feature implementation, deployment or search-engine submission.
<!-- release-summary:en:end -->

对应 REQ-17-1 至 REQ-17-6、REQ-18-1 至 REQ-18-6，并关联 REQ-14-3/4。无功能、API 或数据库迁移变化；公开账号继续关闭，应用案例仍暂缓。源码文档批次 v1.5.8 与正式站版本分开记录；仓库检查及只读核对的实际结果见[本批证据](docs/validation/2026-09-22-traffic-search.md)。

<a id="v1.5.7"></a>
## v1.5.7 · 热门线索核验与日报漏项检查 · 2026-09-21

### 更新重点

<!-- release-summary:zh:start -->
- 修复旧候选指标或材料变化后未重评的问题，保存真实来源观测时间，保留人工分组与用户处理决定。
- 每日审阅增加独立“优先核验”入口与理由；高讨论不自动变成可信材料，累计 Star 不冒充增长。
- 日报增加选题检查、逐项或批量编辑记录及准备前漏项检查；明确当天处理容量、剩余积压和无变化记录复用。
- 本地安排接入同一检查与记录流程；用 Jev 发布前真实快照验证漏报修复，公开资料与发布权限不变。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Reassess existing candidates when metrics or source material change, retain actual observation times, and preserve manual groups and owner decisions.
- Add a separate investigation-priority view with reasons; discussion signals do not establish factual quality, and cumulative stars are not growth.
- Add briefing selection checks, individual or bulk editorial records, and a preparation gate, with explicit daily capacity, backlog and unchanged-evidence reuse.
- Connect the existing local briefing workflow to these checks and replay the missed Jev lead from a prepublication snapshot without changing public content or publication permissions.
<!-- release-summary:en:end -->

对应 REQ-2-1/3/4/5、REQ-11-1。沿用既有私密表和公开接口，无数据库迁移。327项回归通过、1项跳过；最终50项针对性回归、桌面／手机、生产版本和公开内容不变已核对；既有每日安排已更新。状态与真实验收见[本批记录](docs/validation/2026-09-21-selection.md)；未来自然日的主动选题质量与准时日报需继续观察。

<a id="v1.5.6"></a>
## v1.5.6 · 图像、同传与 Jev 决策模型 · 2026-09-21

### 更新重点

<!-- release-summary:zh:start -->
- 发布确认的 Qwen-Image-2.1、Qwen3.8-LiveTranslate 与 Jev 三条动态，同步本期速览；OpenClaw 表补充 v2026.9.5 并保留旧版本。
- 图像模型单列研究许可；同传区分语音与文字覆盖、API与博客日期；Jev区分结构化输出与判断正确性，保留Vercel采用数据的统计范围。
- 网页与 MCP 共用公开介绍、逐点解读和来源清单；本批新增官方材料仅链接，不声称取得全文许可或运行模型。
- 排查 Jev 漏报：9月16日官方发布已入候选，但优先级未跟随指标刷新，社区线索未追溯至官方；改进方案列入项目管理总览，尚未开发。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Publish the approved Qwen-Image-2.1, Qwen3.8-LiveTranslate and Jev developments, refresh the quick overview, and add OpenClaw v2026.9.5 while retaining earlier versions.
- Highlight the image model's research license, distinguish translation modalities and source dates, and separate Jev's typed output from decision correctness and Vercel-specific adoption figures.
- Share introductions, editorial notes and source inventories through the website and MCP; new official materials remain links, without claims of full-text redistribution rights or execution tests.
- Audit the missed Jev recommendation: its official announcement entered the inbox on September 16, but priority data went stale and related community leads were not followed; proposed improvements are recorded, not implemented.
<!-- release-summary:en:end -->

对应 REQ-2-3/4/5、REQ-5、REQ-6-2、REQ-8-9、REQ-9、REQ-10/11、REQ-15。D-23／D-24／D-25 与 CW-A06 已发布，当前 25 条动态、31 项持续关注。81 项相关回归、构建、双端页面和公开 MCP 同源检查通过。正式站和 MCP 已核对 v1.5.6；源码发布回执见[本批验收](docs/validation/2026-09-21-editorial.md)。无应用功能、数据库迁移或采集配置变更；采集连续成功和日报准时交付仍未通过。

<a id="v1.5.5"></a>
## v1.5.5 · 多模态模型、开发客户端与 Harness 研究 · 2026-09-20

### 更新重点

<!-- release-summary:zh:start -->
- 发布用户确认的四项日报内容：Qwen3.8-Omni-Flash、Kimi Code Desktop、Copilot 开发流程更新，以及 Harness 计划与验收研究。
- 本期速览同步四条动态；Qwen 模型表补充 Omni-Flash 分支，保留旧版本、原文日期、采用条件和未实测边界。
- 在动态和 Qwen 资料中提供同一固定提交的 README、安装说明和 Apache-2.0 许可证；其余官方材料明确为来源链接，网页与 MCP 同源读取。
- 记录真实日报补发、内容发布与读取验收；每日采集仍有延期或获取问题，不将本批内容发布写成连续运行验收通过。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Publish four approved briefing items: Qwen3.8-Omni-Flash, Kimi Code Desktop, Copilot workflow updates, and research on harness planning and verification.
- Refresh the quick overview and add the Omni-Flash branch to the Qwen table, retaining earlier versions, original source dates, adoption requirements and untested boundaries.
- Provide the README, installation guide and Apache-2.0 license from one pinned commit in both the development and Qwen profile; identify other official materials as links, shared by the website and MCP.
- Record actual late briefing delivery, publication and reading checks; outstanding collection failures and deferred sources remain separate from this content release.
<!-- release-summary:en:end -->

对应 REQ-4、REQ-6-2、REQ-8-9、REQ-9、REQ-10/11、REQ-15。D-19／D-20／D-21／D-22 及 CW-M07 已发布，当前 22 条动态、31 项持续关注；三份独立原文共 25,982 字符。81 项回归、构建、双端网页、原文重建与资料包通过；正式站及 MCP 已核对 v1.5.5。实际结果见[本批验收](docs/validation/2026-09-20-editorial.md)。本批沿用既有发布接口，无新增功能、数据库迁移或采集配置变化；不安装或运行所介绍的工具。

<a id="v1.5.4"></a>
## v1.5.4 · Word 与接口生成工具动态 · 2026-09-18

### 更新重点

<!-- release-summary:zh:start -->
- 发布用户确认的 ChatGPT for Word 与 Speakeasy 接口生成工具两条动态，分别说明文档内编辑、SDK／CLI 与两类 MCP 的用途及使用边界。
- 本期速览与两条动态同步，保留 9 月 17 日原文日期、9 月 18 日核对日期、具体解读和既有对象关联；持续关注不重复新增对象。
- 区分官方页面链接与获准收录的固定版本原文；Speakeasy 公告和仓库的生成产物许可描述差异逐项保留，不宣称安装或生成实测。
- 同步版本与项目管理记录：三日采集记录已齐，连续成功和 08:00 准时日报未通过；9 次真实 MCP 调用有证据，客户端最终回答未完成。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Publish the approved ChatGPT for Word and Speakeasy API-generation developments, explaining in-document editing, SDK/CLI output, two MCP uses and adoption boundaries.
- Update the quick overview with both developments, retaining September 17 source dates, September 18 review dates, specific notes and existing-object links without duplicating watch profiles.
- Distinguish official source links from licensed, pinned source text; preserve the difference between Speakeasy announcement and repository descriptions of generated-code licensing, without claiming installation or generation tests.
- Synchronize release and project records: three days of collection records are complete, continuous success and 08:00 briefing punctuality did not pass, and nine real MCP calls are evidenced without a completed final client answer.
<!-- release-summary:en:end -->

对应 REQ-4、REQ-6-2、REQ-8-9、REQ-9-3/6、REQ-11、REQ-15-1/5。D-17 ChatGPT for Word 与 D-18 Speakeasy 已发布，本期速览同步；当前 18 条动态、31 项持续关注。Speakeasy 三份固定原文共 47,095 字符，原文重建、资料包、桌面／手机、81 项相关回归和构建通过；正式站与 MCP 均为 v1.5.4。见[本批内容与运行验收](docs/validation/2026-09-18-editorial.md)。不新增 MCP 工具，不涉及数据库迁移或采集配置修改。

<a id="v1.5.3"></a>
## v1.5.3 · Diagram Design Skill 与固定原文 · 2026-09-17

### 更新重点

<!-- release-summary:zh:start -->
- 持续关注 → Skill 新增 Diagram Design，说明技术解释图的选型、可编辑 HTML／SVG、导出方式及使用边界。
- 同一固定提交收录 README、核心 Skill、导出说明、MIT 许可、第三方许可及插件清单六份完整文件，供 MCP 检索、分段读取与资料包下载。
- 保留插件版本与 Skill 元数据的区别，说明 README 与核心图形目录计数差异；未安装、执行或宣称生成效果实测。
- 同步 v1.5.3 中英文 README、版本记录、唯一项目管理总览和实际验收结果；沿用现有发布流程及 MCP 接口。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Add Diagram Design under ongoing-watch Skills, explaining diagram selection, editable HTML/SVG, export behavior and adoption boundaries.
- Publish six complete files from one pinned commit: README, core Skill, export guide, MIT license, third-party notices and plugin manifest, available through MCP search, segmented reading and bundles.
- Distinguish plugin and Skill metadata versions and disclose the README/type-directory count mismatch; no installation, execution or diagram-generation result is claimed.
- Synchronize the v1.5.3 bilingual READMEs, changelog, single project-management overview and validation evidence using the existing publication and MCP interfaces.
<!-- release-summary:en:end -->

对应 REQ-4、REQ-6、REQ-8-9、REQ-9、REQ-10。CW-S05 已发布；正式站与 MCP 均为 v1.5.3，共 16 条动态、31 项持续关注。81 项相关回归、构建、桌面／手机和六份原文逐字重建验证通过。实际网页、MCP 原文和应用部署结果见[Skill 内容验收](docs/validation/2026-09-17-diagram-design.md)。无数据库迁移，不安装项目或执行其脚本。

<a id="v1.5.2"></a>
## v1.5.2 · Gemini Live 动态与原文取材 · 2026-09-17

### 更新重点

<!-- release-summary:zh:start -->
- 新增 Gemini 3.8 Live 动态，分别说明异步工具调用、Extended Thinking 和接入材料；保留 9 月 15 日发布日期与 9 月 17 日核验日期。
- Gemini 持续关注表补充两款 Live 分支，保留 Flash 版本；两份 Google 官方文档按许可保存正文、链接、代码及固定快照，网页与 MCP 同源读取。
- 记录 Hermes 原文取材对照实验与无账号关注更新方案；Hermes 候选正文尚未发布，关注功能尚未开发，不把计划写成已上线。
- 同步中英文 README、唯一项目管理总览与发布验收记录，继续使用既有审核、资料包和 MCP 接口。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Add the Gemini 3.8 Live development with source-backed notes on asynchronous tools, Extended Thinking and adoption materials; distinguish the September 15 announcement from the September 17 review.
- Extend the Gemini watch table with both Live variants while retaining Flash; preserve two licensed Google documentation snapshots with text, code and links, shared by the website and MCP.
- Record the Hermes source-reading comparison and the approved account-free following plan; the Hermes candidate remains unpublished and following remains unimplemented.
- Synchronize both READMEs, the single project-management overview and publication evidence while retaining the existing review, bundle and MCP interfaces.
<!-- release-summary:en:end -->

对应 REQ-4、REQ-6、REQ-8-9、REQ-9、REQ-10/11。D-16 与 CW-M03 已发布，正式站与 MCP 均为 v1.5.2；当前 16 条动态、30 项持续关注。81 项相关回归、前端构建、桌面／手机及公开 MCP 分段原文校验通过。无数据库迁移，无新 MCP 工具。部署和真实验证结果见[内容验收](docs/validation/2026-09-17-editorial.md)；[Hermes 实验](docs/validation/2026-09-17-hermes-materials.md)不代表候选已上站。

<a id="v1.5.1"></a>
## v1.5.1 · 日报三项内容发布 · 2026-09-16

### 更新重点

<!-- release-summary:zh:start -->
- 发布用户确认的 Salesforce in Claude 与 Agent 开发／CI 工程实践两条动态，保留原文日期、逐点解读与关联资料。
- 持续关注新增 Hermes Agent，提供 v0.21.3 固定版本、运行方式与稳定性修复表；原文覆盖明确标为仅链接，不冒充运行实测。
- 同步 For you、For your AI 与统一 MCP 检索，记录私密提案确认、双端预览和发布过程；中英文 README、项目管理总览及版本记录同步更新。
- 补录真实 Codex 客户端的 8 次 MCP 跨日读取证据；无变化修订与固定原文末段续读通过，连续三日和准时日报仍未验收通过。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Publish the approved Salesforce in Claude and agentic-coding/CI developments, preserving source dates, specific editorial notes and related profiles.
- Add Hermes Agent to ongoing watch with the fixed v0.21.3 release, operating details and stability fixes; explicitly label source links and untested runtime claims.
- Share the reviewed content across For you, For your AI and unified MCP lookup; record proposal approval, dual previews and publication, and synchronize both READMEs and the project overview.
- Record eight real Codex MCP calls for next-day revision checks and fixed-revision continuation; three-day operation and punctual briefing delivery remain unverified.
<!-- release-summary:en:end -->

对应 REQ-6、REQ-8-9、REQ-9-3/6、REQ-10、REQ-11。已发布 D-14、D-15、CW-A08，正式站运行 v1.5.1，共 15 条动态、30 项持续关注。311 项回归、前端构建、桌面／手机双端预览和生产 MCP/API 同源取材通过；结果见[内容与跨日取材验收](docs/validation/2026-09-16-editorial.md)。无数据库迁移，不改变采集周期、账户或模型图表。

<a id="v1.5.0"></a>
## v1.5.0 · 统一取材入口 · 2026-09-15

### 更新重点

<!-- release-summary:zh:start -->
- 新增 `curated_lookup` 与同源 HTTP 入口，一次检索已发布动态、持续关注和公开原文，返回命中原因、片段、出处、版本、覆盖与精确续读参数。
- 动态和持续关注支持审核别名，保存不公开、发布后可检索；归并保留旧编号、合并别名并支持撤销，现有 MCP 地址与工具继续兼容。
- For your AI 新增搜索预览、范围与类型筛选、复制交接及新旧材料混合资料包；游标固定顺序，逐页重新核对权限，撤回正文不从旧结果泄露。
- 完成 311 项本地回归、桌面／手机浏览器及 HTTP MCP 分段原文哈希验证；同步唯一项目管理总览、中英文 README 和接入指南。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Add `curated_lookup` and a shared HTTP endpoint to discover published developments, ongoing-watch profiles and public stored text, with match reasons, excerpts, sources, versions, coverage and exact reading arguments.
- Add reviewed aliases to current content: drafts remain private until publication; merges retain old IDs and aliases with undo support, preserving the existing MCP URL and tools.
- Add search previews, scope/type filters, copy handoff and mixed-source packages to For your AI; cursor pages preserve order and recheck live permissions without exposing withdrawn text.
- Validate 311 local regression tests, desktop/mobile browsers and HTTP MCP source reconstruction by hash; synchronize the single project-management overview, bilingual READMEs and connection guides.
<!-- release-summary:en:end -->

对应 REQ-8-9，关联别名审核、MCP 兼容及资料包。已部署至 fieldtofit.top：13 项精选工具、跨内容检索和桌面／手机取材通过；13 条动态与 29 项持续关注的内容修订保持不变。无新增数据库表、索引迁移或内容发布。生产原文按 5 段重建哈希通过；实际验收见[验收记录](docs/validation/2026-09-15-unified-lookup.md)，需求状态见[项目管理总览](FieldToFit-PM.md#req-8-9)。

<a id="v1.4.1"></a>
## v1.4.1 · 生产迁移兼容修复 · 2026-09-15

<!-- release-tag:unpublished -->

### 更新重点

<!-- release-summary:zh:start -->
- 修复六张维护表在 Turso 上的增量升级：使用单次服务端原子事务；本地 SQLite 同样显式开启事务，重复执行不改写既有数据。
- 包含 v1.4.0 的对象归并、关系和材料维护功能；部署前已验证生产备份，公开内容继续保留原修订。
- 新增远程增量升级的原子调用和重复执行回归测试，同步中英文 README 与唯一项目管理总览。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Fix incremental maintenance-table upgrades on Turso with a single atomic server-side transaction; use an explicit SQLite transaction and preserve existing data on repeat upgrades.
- Include v1.4.0 identity review, relationships and material maintenance. The production backup was verified before upgrading; published content retains its revisions.
- Add regression coverage for atomic remote upgrades and repeat execution; synchronize both READMEs and the single project-management overview.
<!-- release-summary:en:end -->

部署检查发现 v1.4.0 的远程增量升级未开启事务，未完成切站；本补丁按既定 z 递增规则修复后发布。对应 REQ-15 及 REQ-3/5/9/10，已部署至 fieldtofit.top，健康接口和 MCP 均为 v1.4.1；管理只读、桌面／手机和新旧变化读取通过，公开 13 条动态／29 项持续关注修订不变。验证与部署状态见[同批验收](docs/validation/2026-09-15-stewardship.md)。

<a id="v1.4.0"></a>
## v1.4.0 · 对象归并与材料持续维护 · 2026-09-15

<!-- release-tag:unpublished -->

### 更新重点

<!-- release-summary:zh:start -->
- 内容管理新增私密候选归组、对象／事件归并预览、冲突字段确认和撤销记录；保留旧编号与原始材料，后续编辑不会被撤销操作覆盖。
- 新增带来源和适用版本的双向关系，网页、MCP 与资料包读取同一维护状态；旧链接显示归并去向。
- 每日检查材料访问，连续三个自然日失败进入复核、七天提升优先级；记录变化、恢复、延期及公开复核说明，不自动发布或删除正文。
- MCP 的 curated_changes 新增 scope=workspace，读取当前动态、持续关注及材料变化，保持旧 scope=legacy 和各自游标兼容。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Add private candidate grouping, reviewed object/event merge previews, explicit conflict choices and reversible merge records; retain identities and source materials without overwriting later edits.
- Publish source-backed, version-scoped bidirectional relationships and shared maintenance metadata across web, MCP and packages, with old-ID guidance.
- Check material access daily; three consecutive failed calendar days trigger review and seven raise priority. Track changes, recovery, deferral and reviewed notes without automatically publishing or deleting text.
- Add scope=workspace to curated_changes for current news, watch profiles and material events while preserving legacy scope and separate continuation cursors.
<!-- release-summary:en:end -->

用户已确认使用 v1.4.0。对应 REQ-3-1/3/4、REQ-10-3、REQ-5-8、REQ-9-5/7，关联 REQ-8。首轮为本地开发验收；部署时补充远程升级兼容修复，全部功能随 v1.4.1 上线。新增维护表需升级，原有公开资料未作实际归并或发布；真实对象操作仍须逐项确认。验收：292 项回归通过、1 项默认跳过，前端构建与隔离桌面／手机流程通过；见[本批验收](docs/validation/2026-09-15-stewardship.md)与[项目管理总览](FieldToFit-PM.md)。

<a id="v1.3.3"></a>
## v1.3.3 · 手机「更多」导航 · 2026-09-15

<!-- release-tag:unpublished -->

### 更新重点

<!-- release-summary:zh:start -->
- 手机底部新增「更多」，与 For you、For your AI 并列；展开后可进入关于 FieldToFit、社区、数据来源和内容管理。
- 四行导航展示简短说明与当前页面标识，支持点击背景、关闭按钮、再次点击及 Escape 收起；页内目录与更多面板互斥。
- 适配窄屏、横屏、底部安全区域、中英文和深浅色；继续使用现有管理登录。同步 REQ-6-17、项目管理总览与双语 README。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Add More beside For you and For your AI in mobile navigation, opening links to About FieldToFit, Community, Sources, and Content management.
- Show descriptions and current-page indicators. Dismiss with the backdrop, close button, repeated tap, or Escape; More and the page contents drawer cannot remain open together.
- Support narrow and landscape layouts, bottom safe areas, both languages and themes while retaining existing admin authentication. Update REQ-6-17, project management, and bilingual READMEs.
<!-- release-summary:en:end -->

对应 REQ-6-17，关联 REQ-6-14。本批源码已同步至开发分支和 main，v1.3.3 已部署到 https://fieldtofit.top；正式站手机导航、管理登录、API 与 MCP 版本复验通过。不涉及数据库迁移、资料发布或权限规则修改。验收结果见[手机导航验收](docs/validation/2026-09-15-mobile-navigation.md)。

<a id="v1.3.2"></a>
## v1.3.2 · 来源阶段统计、问题待办与运行验收 · 2026-09-15

### 更新重点

<!-- release-summary:zh:start -->
- 内容管理新增按来源的当日检查、发现、获取、提交复核及发布统计，分开当前积压、最长等待和历史未记录时间，点击数量可查看对应事项。
- 每日审阅新增自动问题清单：来源失败/待续、缺必要字段、缺材料、待复核和来源变化；可打开对应草稿、重试来源或登记复查日期，延期不算解决。
- 修复 Meta 目录分页混入文章队列与小预算下积压不推进，先处理已存文章再扩页；arXiv 检索失败时尝试官方 cs.AI 摘要补充，保留失败及原分页，不冒充检索恢复。
- 本地日报调整为 07:30 准备、08:00 交付；真实 Codex 客户端已完成线上检索、五段全文读取、带出处回答及隔离故障恢复，连续自然日和周维护仍待实际观察。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Add per-source daily checks, discoveries, material coverage, review submissions and publication counts, separately showing current backlog, longest waits and unrecorded historical timestamps with drilldowns.
- Add actionable editorial issues for failed or unfinished sources, missing fields/materials, review queues and changed evidence. Open drafts, retry sources or defer with a review date; deferral never means resolved.
- Separate Meta directory pagination from articles and drain saved articles before expanding further pages, including single-slot runs. When arXiv search fails, try the official cs.AI abstract feed while preserving the failure and search cursor.
- Prepare local briefings at 07:30 and deliver at 08:00. A real Codex client passed live retrieval, five-chunk reading and cited answers, plus isolated failure recovery; natural-day and weekly checks remain pending.
<!-- release-summary:en:end -->

对应 REQ-15-2、REQ-10-1、REQ-2-1/2、REQ-11-4、REQ-9-2/3。新增两张私密表，保留现有数据库和公开内容；阶段动作从启用日起记录，旧动作不倒推。完整连续三日、跨日实际客户端续读、每周维护不由本日测试替代。当前实采、部署与限制见[验收记录](docs/validation/2026-09-15-operations.md)。

<a id="v1.3.1"></a>
## v1.3.1 · Agents API 与 GPT-Live-1 日报补录 · 2026-09-15

### 更新重点

<!-- release-summary:zh:start -->
- 发布经用户确认的两项日报内容：OpenAI Agents API 与 GPT-Live-1；各保留三点解读、官方发布页及开发文档入口。
- 明确两项来源发布日期均为 2026-09-10，本站于 9 月 15 日核对补录；分别关联 Codex、GPT 模型族。
- 近期动态由 11 条增至 13 条，持续关注保持 29 项；For you、For your AI 与 MCP 共用公开修订，官方原文标明仅链接。
- 推荐批次记录用户确认、草稿关联与真实发布结果；同步项目管理总览、中英文 README 和版本记录。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Publish the two owner-approved briefing topics: OpenAI Agents API and GPT-Live-1, each with three editorial points and links to the official announcement and developer guide.
- Preserve the September 10, 2026 source dates and mark September 15 as the review and backfill date; link to the existing Codex and GPT profiles.
- Increase news from 11 to 13 items while retaining 29 ongoing-watch profiles. Web and MCP share the published revision; official originals remain explicitly link-only.
- Record approval, draft linkage and actual publication in the editorial batch; synchronize project management, bilingual READMEs and release history.
<!-- release-summary:en:end -->

对应 REQ-5、REQ-6、REQ-8、REQ-10、REQ-11。沿用已确认的每日提案文案，不新增重复的持续关注对象；没有把官方客户陈述当成本项目实测，也未调整图表数值或原有五条速览。发布与双端读取证据见[本批验收](docs/validation/2026-09-15-v1.3.1.md)。准时日报、连续自然日运行与日常 AI 客户端自主回答仍待验。

<a id="v1.3.0"></a>
## v1.3.0 · 推荐批次、可读材料与官方变化采集 · 2026-09-15

### 更新重点

<!-- release-summary:zh:start -->
- 运行管理新增更新批次：汇总本地推荐与网站选中项，记录继续／稍后／不采用、证据变化、草稿去向及发布记录；无新证据不重复推荐。
- 日报分开记录整理中、正文已准备、交付已核实和失败，保留交付凭据；本地 08:00 安排接入记录流程，准时交付仍须真实观察。
- 新闻与持续关注新增已审核材料清单、许可、缺失原因和正文阅读；MCP 沿用十二项工具，支持固定材料修订续读和有大小限制的资料包。
- 为已确认选题补齐材料：Artemis 与 Agent Skills 的七份开源文件保留固定提交和许可；DeepSeek、Perplexity/Astra 标明仅链接范围。
- 扩展九家公司官方发布入口，保留同网址变化前的材料；采集周期仍为 1 天，失败、待续与真正取得正文分别登记。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Add private editorial batches for local recommendations and website selections, with continue/later/decline decisions, evidence changes, draft links and publication records.
- Distinguish preparing, prepared, verified delivery and failure for briefings; preserve delivery receipts and connect the existing 08:00 local routine. On-time delivery still requires observation.
- Add reviewed material manifests, licenses, missing-coverage reasons and source reading to news and watch profiles; retain twelve MCP tools with frozen material revisions and bounded bundles.
- Include seven version-pinned open-source files for the approved Artemis and Agent Skills topics. DeepSeek and Perplexity/Astra retain explicit link-only coverage.
- Extend official discovery to nine additional companies, preserving earlier material when a URL changes. Keep daily checks and distinguish failed, queued and retrieved sources.
<!-- release-summary:en:end -->

用户已确认本次中等版本升级。对应 REQ-1-1、REQ-2-1/5、REQ-4-1/4、REQ-5-6、REQ-8-5、REQ-11-1/3/5。新增私密表使用显式增量迁移；保留已有数据、旧整数修订接口和历史标签。公开全文只来自逐份确认的材料，不自动将采集正文转为公开内容。`content_revision` 用于 D-/CW- 材料，旧资源继续用整数 `revision`；两者可在同一资料包读取。网页新增材料阅读不代表执行过上游工具。

实际测试、逐源结果、发布环境及未通过事项见[本次验收](docs/validation/2026-09-14-v1.3.0.md)。连续自然日、日常 AI 客户端自主回答和全部资料的全文覆盖均不能由本轮接口测试代替。

<a id="v1.2.1"></a>
## v1.2.1 · 日报内容发布与资料补全 · 2026-09-14

### 更新重点

<!-- release-summary:zh:start -->
- 更新 DeepSeek 动态与模型族资料：补充 V4.1 Flash 官方 API 发布日期、调用别名，以及 V4 Pro 继续提供服务的最新说明。
- 新增 Perplexity 使用 GPT-6 Astra 生成端到端测试的官方案例动态，区分客户自述与独立验证。
- 持续关注新增 Google Artemis 和 Addy Osmani Agent Skills，提供用途、使用条件、具体技能与固定提交版本的材料链接。
- 近期动态增至 11 条、持续关注增至 29 项；通过统一后台审核发布，For you、For your AI 与 MCP 读取同一公开修订。同步中英文 README 与晨报交付状态。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Update DeepSeek news and its model profile with the V4.1 Flash API release date, aliases and the current notice retaining V4 Pro service.
- Add OpenAI’s Perplexity/Astra end-to-end testing case, distinguishing customer statements from independent verification.
- Add Google Artemis and Addy Osmani Agent Skills with usage requirements, specific skills and source links pinned to commit revisions.
- Expand to 11 news items and 29 ongoing-watch profiles, published through the shared editorial workflow for For you, For your AI and MCP; synchronize bilingual READMEs and briefing-delivery status.
<!-- release-summary:en:end -->

对应 REQ-5、REQ-6、REQ-8、REQ-10 与 REQ-11。用户确认四项选题后，更新两条已有记录、新增三条记录；保留旧版本、图表和其他已发布资料。公开出处保持 `link_only`：可读取结构化解读及原始材料链接，不冒充已托管全文或完成实机验证。应用案例专题继续 pending。部署检查同步移除旧的“10 条动态”常量，按当前快照数量与 Web/MCP 一致性验证。

9 月 14 日晨报实际收到触发但未及时交付，后经补发、用户确认进入本批发布；已强化现有每日安排的交付检查，不能将补发记为准时运行通过。跨入口批次决定账本与连续定时交付仍待完成。[内容与发布验收](docs/validation/2026-09-14-editorial.md)。

<a id="v1.2.0"></a>
## v1.2.0 · 来源覆盖与每日优先审阅 · 2026-09-14

### 更新重点

<!-- release-summary:zh:start -->
- 新增来源双表：12 个重点公司／团队、实际渠道、接入与检查状态，以及关联的已发布内容；管理端可启停与检查。
- 新增 19 项正式日采集配置，覆盖官方订阅、文章列表、模型卡、仓库发现、社区线索与论文；私密材料保留原文、日期、分页和失败信息。
- 每日审阅新增优先查看、值得关注、待核实分组，展示材料依据与观测信号，支持手动调整和跨日待整理队列；选中不发布。
- 日调度配置改为北京时间 06:30，使用自然日去重与受预算限制的并行检查；现有公开资料和只读 MCP 保持不变。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Add source coverage tables for 12 organizations, showing actual channels, connection and check states, and linked published content; administrators can enable, pause and check sources.
- Add 19 daily source configurations for official feeds, article indexes, model cards, repository discovery, discussions and papers, with private materials, dates, pagination and failure records.
- Add priority, follow-up and verification groups with material-backed reasons, dated attention signals, manual overrides and a cross-day selected queue; selection never publishes.
- Schedule daily checks at 06:30 Beijing time with calendar-day claims and bounded parallel collection; existing public content and read-only MCP remain unchanged.
<!-- release-summary:en:end -->

经用户确认使用 minor 版本 v1.2.0。对应 REQ-1-1、REQ-1-2、REQ-2-1、REQ-2-3、REQ-2-4；兼顾 REQ-2-2 的失败保留。本批不实现 REQ-2-5 跨日提醒账本或 REQ-11 的批次决定记录。

2026-09-14 按用户授权部署 v1.2.0 并完成逐源生产验收：19 项新增来源中 13 项本轮成功、5 项有已取材料及待续项、arXiv 未通过；27 个已发布仓库维护检查全部成功。发布验收修复远程事务时限和连接复用问题，并验证同日去重。剩余真实访问失败及未完成分页见[验收记录](docs/validation/2026-09-14-discovery.md)。完整范围与缺口以[项目管理总览](FieldToFit-PM.md)为准。公开动态、持续关注、图表没有新增或替换内容。连续三个真实日周期尚未通过，已纳入 9 月 15–17 日的本地 08:00 晨报复查；复查不代替服务器调度。

<a id="v1.1.2"></a>
## v1.1.2 · 项目管理总览与每日选题方案 · 2026-09-13

### 更新重点

<!-- release-summary:zh:start -->
- 项目管理统一到根目录 FieldToFit-PM.md，使用 REQ-1 / REQ-1-1 编号，逐项列出开发、验证、已上线和未上线能力。
- 合并旧需求、目标、验收总表及路线图，保留 91 个旧子项和历史编号的映射，当前为 16 项主需求、99 个子项。
- 明确本地主动搜索和网站候选接续两种流程、质量与关注度排序、每日 08:00 提案格式及先与用户对齐的发布边界。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Consolidate project management in root-level FieldToFit-PM.md, using REQ-1 / REQ-1-1 IDs and explicit development, verification and shipped-feature states.
- Merge the old requirements, goals, acceptance overview and roadmap, retaining mappings for 91 previous subrequirements; the current plan has 16 requirements and 99 subrequirements.
- Define proactive local research, selected-candidate handoff, quality and attention ranking, the daily 08:00 proposal format and owner alignment before website changes.
<!-- release-summary:en:end -->

本批交付项目管理文档、引用与校验更新；本机对话安排已单独配置，不属于网站部署功能。网站来源双表、优先级与提醒账本仍未实现。2026-09-14 按用户确认发布此前完成的 v1.1.2，不因推送与部署额外递增版本；公开资料与网站业务不变。见[项目管理总览](FieldToFit-PM.md)及[整理验收](docs/validation/2026-09-13-pm.md)。

<a id="v1.1.1"></a>
## v1.1.1 · 文档统一与双语项目首页 · 2026-09-12

### 更新重点

<!-- release-summary:zh:start -->
- 版本历史统一到 CHANGELOG，合并七份逐版说明；Metis 验收证据归入历史目录，保留日期和适用范围。
- 中英文 README 采用对应结构，补全社区愿景、开发者投稿、参与入口与 MCP 接入方式。
- 版本号和双语更新摘要统一同步；发布检查验证两版 README、最新记录及前后端版本一致。
<!-- release-summary:zh:end -->

### Release highlights

<!-- release-summary:en:start -->
- Consolidate version history in CHANGELOG and merge seven release-note files; archive Metis evidence with its original dates and scope.
- Align Chinese and English READMEs, including the community, developer submissions, contribution channels and MCP access.
- Synchronize version metadata and bilingual highlights, with checks for both READMEs, the latest changelog entry and application versions.
<!-- release-summary:en:end -->

对应 REQ-O-03（发布与维护）及 REQ-C-01（社区介绍）；需求范围和既有功能状态不变。关于页版本区改为指向统一更新记录，避免重复维护易过期的摘要。本版不迁移数据库，不更改公开资料、管理权限或接口。历史标签不移动。

本批源码版本为 v1.1.1；正式站点实际运行版本以 `/api/health` 为准。[本版验证与部署记录](docs/validation/2026-09-12-v1.1.1.md)。后续仅在本文件追加版本记录，GitHub Release 正文从对应段落提取；[发布指南](docs/guides/releasing.md)。

<a id="v1.1.0"></a>
## v1.1.0 · 统一内容管理 · 2026-09-12

- 经用户确认升级 minor：单一内容管理入口，整合每日审阅、内容库、需求反馈、来源与运行（REQ-O-05.01）。
- 候选按发现日期/来源/类型/状态分页；加入待整理只创建或关联私密草稿。逐点解读、版本表、本地 AI 导入导出、冲突保护（.02/.03）。
- 预览两端后明确发布，同源 Web/MCP；可下架、恢复历史到草稿，保留原因和版本（.04）。
- 管理近期动态、五类持续关注、AA/Arena 数值与旗舰名单、开发者投稿；反馈分页、处理与候选登记（.05）。
- 版本文件原样迁入三个共享集合，幂等原子写入，保留标识、真实来源日期和旧资料；私密备份及回退说明（.06）。
- 22 项 REQ / 91 子项；12 项精选 MCP 不变。[验收与部署](docs/validation/2026-09-12-v1.1.0.md)。

<a id="v1.0.5"></a>

首次迁移基线为 10 条动态、27 项持续关注及双来源 190 个图点；管理验收未向生产新增测试材料。数据库发布成为内容权威，旧版本文件保留为基线。回退必须考虑迁移后的发布及下架数据，不能直接恢复只读旧文件的代码。操作、备份和迁移说明见[内容管理指南](docs/guides/management.md)。共享管理员不等于多人实名审计；连续真实日运营、完整原文及真实投稿仍待验。

## v1.0.5 · 社区卡片与投稿说明 · 2026-09-12

- REQ-AB-01：社区邀请改为完整内边距、细边框和主题适配的卡片，修复色块贴边问题。
- REQ-C-01.02：在投稿介绍下明确 GitHub Issue / fieldtofit@163.com 两种方式；可直接打开包含六项模板的 Issue 或邮件草稿，现有表单保留。
- REQ-O-04：说明反馈进入后台，由维护者处理，不自动发邮件或创建 GitHub Issue；记录现有保存/处理流程与后续运营建议。
- 版本同步 v1.0.5；资料数据与接口行为保持既有版本。[验收记录](docs/validation/2026-09-12-v1.0.5.md)。

<a id="v1.0.4"></a>

当时为 21 项 REQ / 85 个子项，12 项精选 MCP。未修改公开资料、数据库结构或反馈接口；自动提醒及回执未实现。构建、1440px/390px 浅深色界面及两项反馈测试通过。见[投稿方式](docs/guides/project-submissions.md)和[反馈流程](docs/guides/feedback.md)。

## v1.0.4 · 社区、开发者投稿与阅读目录 · 2026-09-11

- 阅读目录默认两级、明细单组展开、数量右对齐；手机使用可关闭并定位正文的抽屉（REQ-Y-04）。
- 关于页保留品牌开头，重组使用、收录、维护、社区及版本段落；新增关于页下方的社区导航，移除账户菜单（REQ-AB-01）。
- 新增 REQ-C-01：社区与六项开发者投稿表单，通过 GitHub / fieldtofit@163.com 由用户自行发送；审核后使用既有资料流程发布。
- For you / For your AI / 社区读取同源已审投稿，curated_watch 增加 origin 过滤；当前真实项目为空。需求更新为 21 项 / 85 子项，工具数仍为 12。[验收](docs/validation/2026-09-11-v1.0.4.md)。

<a id="v1.0.3"></a>

不新增账户、论坛或独立投稿数据库；旧账户路由保留兼容。五类 27 主体、10 条动态、190 个图点未修改，没有发送测试投稿。本地 208 项后端测试通过、1 项跳过；桌面/手机和公开 MCP 同源检查通过。首批真实投稿、邮箱实际收信及每周处理记录尚待验证。操作见[投稿维护](docs/guides/project-submissions.md)。无数据库迁移，回退使用相容数据及上一提交。

## v1.0.3 · 各家旗舰模型 · 2026-09-11

- 新增 REQ-Y-05.05：“各家旗舰模型”筛选，位于“全部公司”旁；AA 展示 11 家代表配置，Arena 展示 8 家，精确使用原名与坐标。
- 独立维护 11 家旗舰系列名单、依据与核验日期；对未收录或缺价格的系列明确说明，避免以旧系列替代。选择可以随 URL 分享、刷新恢复及跨来源保留；搜索、数值表、缺项表和放大图同步。
- 运行版本、当前文档和 REQ 同步至 v1.0.3；现有 20 项 REQ / 81 个子 REQ。[验收](docs/validation/2026-09-11-v1.0.3.md)。

<a id="v1.0.2"></a>

每个旗舰系列只展示一个来源配置，缺型号或价格明确说明。原有 190 点、来源日期、价格口径与数据库保持不变；MCP 仍为 12 项工具。

## v1.0.2 · 2026 模型图表与公司配色 · 2026-09-11

- 仅保留 Artificial Analysis 和 Arena；移除 Epoch 页签、当前数据与日检查。两图沿用原有评分与价格口径，Arena 明示 Text Overall 的 Style Control 设置（REQ-Y-05.01/.02）。
- 按 OpenAI、Anthropic、Google、xAI、Meta、Kimi、GLM、Qwen、MIMO、MiniMax、DeepSeek、其他固定配色；模型直接沿用来源名称标在点旁，连线只连接名称；加入公司筛选、名称搜索、固定坐标域、100–200% 放大和来源数值表。
- AA 读取 646 个条目，263 个日期属于 2026 年，其中 107 个可绘制；Arena 读取 400 个条目，96 个确认属于 2026 年，其中 83 个可绘制。169 个缺坐标条目与 182 个 Arena 日期待确认条目保留在折叠清单中；不补造评分、价格或日期（REQ-Y-05.02/.03）。
- 新增离线候选快照生成工具、Arena 日期依据清单和来源页面指纹；每日仍只检查两个榜单可用性，审核与发布独立（REQ-Y-05.04）。
- 应用与当前文档同步 v1.0.2；历史 v1.0.1 说明保留原貌。[验证与部署记录](docs/validation/2026-09-11-v1.0.2.md)。

<a id="v1.0.1"></a>

仅绘制 2026 年且评分与正价格齐全的来源配置，不跨来源混用价格。旧 Epoch 参数回退 AA；坐标区间保留。无数据库迁移或新凭据，当时可按 v1.0.1 提交回退，不能据此跳过后续版本的迁移约束。

## v1.0.1 · 内容、阅读与模型图表 · 2026-09-11

- For you 增加页面导读，近期动态前加入 Artificial Analysis / Arena / Epoch AI 三来源图表切换、数值与出处、真实核验日期、放大和可折叠说明（REQ-Y-05）。首版为 22 个已核对数据点的摘录，不是完整榜单。
- 新闻与持续关注默认展示前两条完整解读，更多观点、版本表和关联材料按需展开；移除页面上的旧概览归档及历史资料库入口。
- For your AI 增加 MCP 接入说明一键复制、服务地址、配置示例与资料下载；测试服务连通不冒充用户客户端已连接。
- 图表来源纳入每日可用性检查，检查结果单独记入运营记录；不自动改写数据快照与日期，数值仍经审核后随版本发布。
- 前后端、关于页和当前文档统一 v1.0.1；明确每次交付提交递增 z，y/x 升级须先获用户确认，规则见[版本规则](docs/guides/releasing.md)。

以下两批改动此前在 v1.0.0 运行，本次统一归入 v1.0.1 的交付说明；原验收文件保留当时版本，不改写历史。新验收见[本版验收](docs/validation/2026-09-11-v1.0.1.md)。

### 持续关注 CW1

- 27 个已确认主体按五类展示；补齐模型版本、工具 / Agent 更新、Skill 关注度与代表技能、Harness 运行机制。
- 同源 curated_watch / HTTP 读取、正文搜索与类型筛选、目录定位、JSON 下载与 AI 交接；原有原文库折叠保留。
- 草稿/撤回/私有字段隔离，来源覆盖与未知项明确；精选 MCP 共 12 项。[验收与部署状态](docs/validation/2026-09-11-continuous-watch.md)。

### 内容与阅读更新

- For you 改为近期动态（速览/发布与更新）和资源档案；完整解读逐点展示，减少重复内容。
- 新增页内目录，桌面固定、手机折叠，支持阅读定位、分享展开及筛选/分页同步（REQ-Y-04）。
- 加入包含 DeepSeek-V4.1-Flash 的 10 条首发动态；新增 curated_news 与同源 API，共 11 项精选 MCP 工具。
- 新闻通过版本化文件审核发布，原文仅链接；旧资源/期次/原文接口保留。验证见[阅读验收](docs/validation/2026-09-11-reading.md)。

### 前次文件整理

- 2026-09-11：整理当前文档、归档 Metis 历史，公开品牌图片收敛为网站实际使用的 5 份。
- 文件整理阶段先记录候选内容；随后根据用户确认合并为近期动态与资源档案，本次交付范围见上文。
- FieldToFit 标签采用 `fieldtofit-vX.Y.Z`；旧 Metis 标签保留。

<a id="v1.0.0"></a>

交付对应：双页导读与默认解读为 REQ-Y-01.01/Y-02.02；目录与深链接为 Y-04；图表、口径与来源为 Y-05.01–.03；每日可用性为 Y-05.04/F-04；MCP 交接为 AI-01/AI-03；版本规则为 O-03。AA/Arena 各 8 点、Epoch 6 点，Epoch 为本站配对绘图；未知日期保留。图表不新增 MCP 工具，不提供第三方完整数据库分发。

本版无数据库迁移或新增运行依赖；每日检查只执行无凭据公开 GET，限制响应体与超时，不跟随跳转，结果进入工作流运行表。当时可回退前一部署，内容快照留在版本控制；这不替代 v1.1.0 迁库之后的回退要求。

## v1.0.0 · FieldToFit · 2026-09-10

- 项目品牌更名为 **FieldToFit**，视觉表达为 **FIELD → FIT**；以人与 AI 共享的动态 AI 地图说明项目立意。
- 接入提供的深浅色 Logo、浏览器图标、触屏图标和分享图；关于页先展示 Field / To / Fit，再保留双端使用方式、来源与维护说明。
- 统一网页、MCP 身份、README、开发与部署文档中的项目名称；前后端运行版本均为 1.0.0。
- 兼容读取旧环境变量、浏览器收藏和 SQLite 数据；旧协议标识与历史证据保留用于升级兼容。
- fieldtofit.top 已完成 DNS 与生产绑定；品牌、健康、27 项资料及 10 项 MCP 工具通过公网实测。公开列表和资料包采用请求内批量读取，后续请求重新检查撤回，修复远程写锁超时与逐条查询延迟。
- 首批内容已扩展为 27 项、62 份材料；本地整理稿导出/导入、引文预览与审核发布已实现。公网部署及连续日运行仍单独验收。

这是品牌版本的新起点；以下旧版本编号保留历史顺序，不代表从 v1.1 降级数据。

升级兼容：新配置使用 `FIELDTOFIT_*`，继续接受旧 `METIS_*`；新安装默认 `fieldtofit.db`，已有 `metis.db` 继续读取。浏览器将旧收藏和设置复制到新前缀而不删除原值。旧列名、协议 schema、不可变原文及历史验证保留。首批 62 份材料合计 501,355 字符；完整性和公开读取见[品牌验收](docs/validation/2026-09-10-fieldtofit-brand.md)。品牌版本重新起算不代表迁移或降级数据库。

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

**此条仅记录 2026-09-08 的文档阶段：当时未修改功能代码或应用版本。** 后续实现见上方 2026-09-09 条目。 后续开发见 [ROADMAP](FieldToFit-PM.md#项目管理规则与下一步)。

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
