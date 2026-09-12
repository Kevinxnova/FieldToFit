# 精选平台：当前实现与使用

v1.1.0 当前维护入口见[统一内容管理](management.md)：近期动态、持续关注与模型图表保存至数据库共享发布集合。以下对象、原文、概览接口与旧材料工作流继续兼容，不是当前首页结构。

2026-09-11 · FieldToFit v1.0.0，已公开部署。这里描述实际接口；[产品契约](../product/data-contract.md)包含仍待实现的目标。

## 打开页面

按[本地指南](local-development.md)启动后打开 `/for-you`。前端入口源码为 `frontend/src/main.tsx`，页面在 `frontend/src/pages/Platform.tsx`，不能通过双击文件使用完整服务。

| 页面 | 当前可以做什么 | 仍未完成 |
| --- | --- | --- |
| `/for-you` | 近期动态（速览/发布与更新）、资源档案和页内目录、旧期次归档、名称/类型/来源/发布日期搜索、固定修订详情、事实/来源/原文、复制资料清单、手选集合及含原文 JSON/Markdown 预览下载 | 新详情本地收藏、统一产品/事件关系 |
| `/for-your-ai` | 实际 MCP 配置与连接检查、同一集合的 JSON/材料预览、逐段原文、固定快照分页与精选变化读取 | 日常 AI 客户端验收、完整关注集合交接 |
| `/about` | 项目立意、双端职责、维护原则、真实服务版本和参与入口 | 目标用户理解验证及分享元信息完善 |
| `/admin` | 每日审阅、内容库、需求反馈、来源与运行；保存草稿与双端预览后明确发布；旧对象/概览编辑收在次级区 | 多编辑者实名审计及长期运营 |

`/information`、`/apps` 转向新首页并解释迁移；名称查询及可识别类型保留，旧领域筛选不再沿用。`/connect` 转向 AI 页。旧档案 `/records/:id`、任务/比较/案例、`/legacy/information`、`/legacy/apps` 暂保留兼容。旧记录不会自动出现在精选页面。

## 从原始资料到精选

1. 沿用现有记录/事实/证据编辑，保存来源和版本。关键事实必须是有来源引文的声明，或者显式未知。
2. 在精选审核区填写简介、名称别名、角色依据、收录理由，以及本次发布声明包含的材料。引文必须能在该对象的材料中核对。
3. 保存草稿，查看缺口，送审，再发布。至少有一份可读的主要材料；许可证或发现链接不能单独满足主要材料门槛。未解决冲突不能发布。
4. 发布创建固定修订，两端和导出共用。资料/证据变化会使当前精选进入待复核；重新审核前退出当前公开集合。只更新检查时间不会制造新发布。
5. 撤回会阻止读取撤回之前的发布正文；再发布必须重新审核。修改原因会记录；当前尚无逐操作管理员身份审计。

并发保存/审核携带版本和审核令牌；过期操作返回冲突，需重新加载后核查，不能覆盖新修改。审核记录、源变更及精选失效在同一数据库事务中完成。

## 使用真实材料的隔离预览

仓库包含 2026-09-08 获取的 Deep Agents 官方 README、MIT 许可证及来源哈希。官方文档只保存链接。没有取得上游提交号，因此上游版本为空，不能把内容哈希称为官方版本。它是资料链路验证对象，不是 AI 应用案例或热度榜单。

```bash
# 明确选择新的隔离目录；默认只导入候选，不发布
python -m examples.platform.load --data-dir /tmp/fieldtofit-platform-preview

# 或在首次导入时明确发布到另一个全新目录
python -m examples.platform.load --data-dir /tmp/fieldtofit-platform-published --publish
# 已导入的候选请在后台审核；重复导入不会修改或发布既有记录

# 使用同一隔离目录启动，避免载入本机 .env / 远程数据库
PYTHON_DOTENV_DISABLED=1 TURSO_DATABASE_URL='' TURSO_AUTH_TOKEN='' \
FIELDTOFIT_DATA_DIR=/tmp/fieldtofit-platform-preview ./scripts/start-backend.sh
```

原来的 `examples.editorial.load` 导入旧记录，不会绕过精选审核。空精选集合是正常状态，页面不会拿旧样本填充。

## 公共读取接口

统一 `schema_version: metis.platform.v1`，公共路径位于 `/api/v1/platform`，沿用部署者配置的可选读取令牌。管理员接口单独鉴权。

| HTTP GET | MCP 工具 | 语义 |
| --- | --- | --- |
| `/objects?q=&object_type=&limit=20&offset=0` | `curated_search` | 最新发布优先；首次建立固定快照，按 `next_cursor` / `previous_cursor` 续读，保持相同查询和 limit；旧 offset 只保留兼容 |
| `/objects/{id}?revision={publication_revision}` | `curated_object` | 固定发布修订的对象、事实、关注依据、材料清单、当前状态 |
| `/objects/{id}/materials/{material_id}?revision={revision}&offset=0&limit=12000` | `curated_material` | 字符偏移续读，单次最多 50000 字符；返回 `body`、`next_offset`、`has_more`、覆盖、哈希和来源 |
| `/objects/{id}/export?revision={revision}&format=json` | `curated_export` | JSON 快照及 Markdown 资料清单；HTTP 默认 Markdown，支持 `json`/`markdown` |

材料清单只统计已登记资料，`full_text` 只指该份文档文字。`link_only` 明确返回空正文，不冒充完整材料。材料不存在、修订不可访问、内容哈希变化及撤回分别返回明确错误。对象的 `record_checked_at` 是记录检查时间，不能视为网络来源最后成功检查时间。

原有 `curated_export` 是带事实、引用、版本和读取链接的**资料清单**，正文需继续读取。新增 `curated_bundle` 可直接包含所存正文，两者均不生成任务步骤。网页清单使用实际 API 地址，本机地址会标明云端 AI 无法直接访问。私有部署应另外配置读令牌，不把密钥写进清单。

现有 10 个精选工具，旧 9 个保留，共 19 个。旧 `search` / `changes` 等仍面向旧知识库，不等价于精选索引/变化流。新接入从 `curated_search` 开始，变化使用 `curated_changes`，概览使用 `curated_editions` / `curated_edition`。HTTP/stdio 连接见[接入指南](ai-access.md)。

## 来源检查与日期筛选

For you 和 For your AI 的资料区域提供“来源与发布日期筛选”及“当前精选来源的检查状态”。筛选作用于对象列表，概览期次保持自身的涵盖日期。卡片、详情和 AI 页同时显示对象关联采集源的状态。人工导入且未登记日检查的来源显示“未接入日检查”，不会由记录整理时间补出成功记录。

`curated_search` / GET `/api/v1/platform/objects` 新增可选参数：

| 参数 | 含义 |
| --- | --- |
| `source` | 采集来源 ID，精确匹配，不是官方网站域名；来源身份绑定发布版本 |
| `since` | FieldToFit 精选发布日期起始日，严格 `YYYY-MM-DD` |
| `until` | FieldToFit 精选发布日期截止日，严格 `YYYY-MM-DD` |

日期统一按 UTC，包含首尾两天，不代表上游发布日期。时间倒置、无效日期返回 `invalid_request`；未匹配来源返回空集合。翻页时必须保持原来源、日期、其他筛选和 limit，否则返回 `cursor_scope_mismatch`。没有新增筛选时，既有游标仍可续读。响应 `filters` 和 `date_basis` 说明实际使用的范围。

`curated_sources` / GET `/api/v1/platform/sources` 只列当前精选对象关联的采集源，返回对象数量、`registered`、`enabled`、固定 `interval_days: 1`、`last_attempt_at`、`last_success_at`、`last_run_status`、`freshness`、`state`；没有当前精选对象时返回空列表。它与旧全库 `sources` 工具范围不同，不返回采集配置、带参数源地址和原始错误文本。

`curated_object` 顶层 `source_check` 同样携带这组当前运行状态，原文包 JSON 和 Markdown 保留它。该状态会随运行变化，不属于冻结的正文事实。`record_checked_at` 仍是记录整理/检查时间；材料的 `retrieved_at` 是取得材料时间；`source_check.last_success_at` 只是所属采集适配器最后完整成功时间，不能证明选定对象或某份正文刚刚重新获取。

采集源成功不足 1 天为 current，超过 1 天为 stale；失败或部分成功保留已有最后成功时间，停用/运行中分别标注；未登记、无成功记录、无时区/无效/未来时间均不虚构成功。新发布快照保存 `source_id`；早期快照从其自身 `source_revision` 对应的历史记录恢复来源身份，历史证据不足则显示未知，不使用当前可变记录推断。

日期/来源接口和 SDK 已验；网页的来源选择、日期区间、空结果、清除条件、刷新恢复及 390px 手机视图已补验。逐份材料的自动核查及失效事件另列未完成项。

## 下载含原文资料包

For you 在卡片勾选“加入资料包”，最多 10 个对象，可以跨搜索和分页保留选择；各自绑定勾选时的发布修订。刷新或离开页面后清空，当前不属于持久收藏。对象详情与 For your AI 的选中对象也提供预览和下载。

“预览含原文资料包”“下载 JSON 原文包”“下载 Markdown 原文包”每次重新核对所选修订的可读性。文件包含实际所存正文，可离线提供给个人 AI；既有“下载资料清单”仅含入口。页面同时展示可用对象比例、实际字符数、仅链接、需续读及不可用材料数。预览也可复制；浏览器不允许自动复制时保留文本框手动复制。

HTTP：`POST /api/v1/platform/bundle`，请求正文与 MCP `curated_bundle` 参数相同：

```json
{
  "objects": [{"id": "OBJECT_ID", "revision": 6}],
  "max_characters": 200000,
  "format": "json"
}
```

- `objects` 必须含 1–10 个引用；`revision` 可省略以读取当前精选，但网页始终指定勾选修订。相同修订不能重复；不会自动换成新修订。
- `format` 为 `json` 或 `markdown`。HTTP 两种格式均返回 JSON：前者包含 `objects`，后者包含 `markdown` 字符串；浏览器分别保存 `.json` / `.md`。
- `max_characters` 限制本包原文总字符，默认 200000，最大 500000；网页采用默认值。此限制不包含档案/引用等元信息，字符也不等于 token 或字节。
- 每个对象保留发布修订、是否当前、事实、未知项、来源与材料。每份材料有原内容哈希、`body`、`included_characters` 和 `inclusion`：`complete`、`partial`、`deferred`、`link_only` 或 `unavailable`。
- 超出长度时不静默删材料；`continuation` 给出准确 `curated_material` 调用参数，包括固定发布修订、材料 ID 和下一字符偏移。材料哈希对应完整所存正文，部分正文需续读后再核对完整哈希。
- 撤回/缺失对象保留最小 ID/修订及错误；其他对象仍可打包。缺失或哈希不符的材料不返回正文。`all_stored_text_included` 只表示登记范围中的所存文本已包含，不代表所有上游文档已获取，`link_only` 数量仍单独显示。
- 多对象与材料在同一数据库事务读取；包是导出时的快照，之后的更正/撤回需通过变化接口检查。当前包附截至选定修订的公开历史（最多先带 20 条，更早记录有续读参数）；不包含对象关系、管理员审核备注或全部上游发布历史。
- 外部原文作为字面引用保存，不安装或运行工具。Markdown 采用能包住原文围栏的代码块；源文本不作为网页 HTML 渲染。
- 网页把续读服务地址放在原文外，保留原文字符不改写；本机服务不能供云端 AI 直接续读。读取令牌从当前会话使用，但不进入文件或复制文本。

本轮 Chrome 已核对实际下载文件；内置预览浏览器仅确认生成和预览，未确认下载落盘。新接口临时生成包，不新增表、不在服务端保存下载文件，也不改变精选状态。

## 读取公开修订历史

For you 详情和 For your AI 选中对象后展示“这份资料如何变化”，包括首次精选、修订、待复核和撤回，修订项列出发生变化的字段。打开旧修订时，历史止于该修订；较新事件仍在 `curated_changes` 中读取。详情及跨历史修订跳转保留原列表的筛选/分页参数，关闭后可以继续原列表。

GET `/api/v1/platform/objects/{id}/history?revision=6&limit=5` 对应 `curated_history`：

```json
{"id":"OBJECT_ID","revision":6,"limit":5}
```

首次可省略 `revision`，以当前精选发布为准。返回明确的 `revision`、`items`、`total`、`sort: event_id_desc`、固定快照及前后页游标。每条历史含公开事件 ID/时间、前后发布修订、变化字段和当前可读状态；有可读正文时提供对应固定修订入口。版本号都是 FieldToFit 内部发布修订，不是上游软件版本。

续读必须传回首次解析出的 `revision` 和原 `limit`，使用返回的 `next_cursor`；也可以直接执行 `continuation.tool` 和 `continuation.arguments`。遗漏修订、换范围/条数、游标过期均明确报错。游标有效 7 天，过期后按同一修订重新读取。后来发生的事件不进入这次历史窗口，但撤回即时生效；再发布不恢复曾撤回的旧正文入口。

资料包自动带入最多 20 条公开历史，超过时保留 `total`、`has_more` 和准确续读参数，不能把前 20 条当作完整历史。未超限无需创建续读快照。包内历史与对象/原文同一事务核对，Markdown 以字面数据块保留，私有审核原因不进入页面或导出。它是平台公开发布历史，不代表上游全部版本记录，也不替代对象关系材料。

历史查询复用原有快照缓存和发布日志，不新增数据表、不创建资料变更。现有 `curated_changes` 仍供每日增量读取，两个接口按相同规则处理公开事件。

## 发布本期与回看往期

后台 `/admin` →“概览期次”，新建标题与涵盖日期，加入 1–5 个已审核对象，每对象一条重点。引用固定对象修订，填写重点、关注理由和支持原句；可调整期内顺序。保存后查看缺口，填写私有审核依据，再“审核并发布本期”。

草稿编辑不覆盖公开版本。公开期次 URL 为 `/for-you?edition={id}&edition_revision={revision}`；没有新发布时保留原日期。编辑更正会产生新修订，旧链接仍可追溯。引用来源变化后标记待复核；材料不可用时遮蔽该条正文。整个期次撤回后停止读取此前修订，再发布不会恢复撤回前的正文。

概览目前人工编写，校验保证引用、版本和发布范围，但不会自动证明文案语义；维护者仍需逐句核查。期次日期不代表当天发现了上游新版本。后台只列最近 100 个草稿/精选候选，适合当前小范围维护，尚未完成大规模管理分页。

## 持续取材与恢复

| HTTP GET | MCP 工具 | 返回 |
| --- | --- | --- |
| `/changes?after=0&limit=20&object_id={id}` | `curated_changes` | 可省略对象筛选；MCP 使用 `object_ids` 数组。返回新增 `added`、修订 `updated`、待复核 `needs_review`、撤回 `withdrawn`，以及前后修订/变化字段 |
| `/editions?limit=5` | `curated_editions` | 已发布期次，最新修订优先；按固定快照游标回看历史 |
| `/editions/{id}?revision={revision}` | `curated_edition` | 固定期次重点、来源原句、对象修订及当前可读状态；草稿不公开 |

一次检索/变化/归档读取固定成员和顺序。新内容留给新查询或下一变化窗口。撤回仍即时生效：固定页保留不可用位置和最小 ID/修订，绝不靠旧快照重新公开正文。

1. 首次调用 `curated_changes`，例如 `{"object_ids": [], "limit": 20, "after": 0}`。空对象数组代表全部精选。
2. `has_more=true` 时，用返回的 `next_cursor` 和同一对象范围、limit 继续；不要同时传 after。重复读取同一中间页不会改变事件成员。
3. 全部读完后保存 `resume_cursor`；下次（建议每 1 天）以相同范围和 limit 调用，建立以上次窗口上界为起点的新窗口。没有变化返回空列表及可继续保存的检查点。
4. 断线重试保留游标。对象/筛选/limit 改变会返回 `cursor_scope_mismatch`，格式无效为 `invalid_cursor`；游标 7 天后返回 HTTP 410 / MCP `snapshot_expired`。此时重新从 `after=0` 读取，用事件 ID 去重；数据库恢复导致水位超界返回 `invalid_checkpoint`。

游标是不透明的客户端状态，不应手工构造。浏览器“给 AI 的续读配置”可复制实际对象范围、页大小及检查点；它不让网站代替用户 AI 后台运行。源材料仍是不可信引用数据，不自动执行外部代码。

读快照属于派生缓存，存于数据库，创建新快照时清理已过期缓存；它不修改资料或发布状态。发布日志目前未自动清理，不承诺永久保存全文；采集源最后成功时间已公开，但逐份材料复核状态与独立失效事件仍待补齐。

## 升级与恢复边界

平台累计新增六张表：`knowledge_platform_profiles`、`knowledge_selections`、`knowledge_publications`，以及本轮的 `knowledge_read_snapshots`、`knowledge_editions`、`knowledge_edition_publications`；复用现有对象与证据 ID，不自动修改存量精选资格。

升级前可对明确的本地 SQLite 做只读盘点和一致备份，不加载 `.env`：

```bash
python scripts/maintenance/platform_inventory.py --database /absolute/path/fieldtofit.db \
  --backup /absolute/path/new-backup.sqlite
```

脚本拒绝覆盖既有备份。停止服务后回退到相容代码和备份数据库；恢复操作先在隔离目录验证。本次只盘点了本地 SQLite，不能据此推断已运行服务或远程 Turso 的存量。生产公开读取已验；生产维护写入、正式备份恢复和容器部署仍待验。

已验证的真实范围见[基础检查](../validation/2026-09-09-platform-foundation.md)与[本轮期次/增量检查](../validation/2026-09-09-platform-updates.md)。每日 1 天调度基础保留，已发布 27 项对象；连续 3 个真实日周期与 P2 首发内容更新仍未完成；注册关闭，案例 pending。

## 新闻与目录

最新双区阅读与目录见[页面方案](../product/pages.md)。GET /api/v1/platform/news 与 curated_news 同源，内容维护与 link_only 原文边界见[新闻说明](../product/launch-selection.md)。资源目录按当前页显示，保留全匹配数量；更换筛选/分页后重建。
