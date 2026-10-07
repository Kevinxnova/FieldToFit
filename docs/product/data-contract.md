# 资料模型与 AI 读取契约草案

P3 · 2026-09-11。对应 [共享基础](../../FieldToFit-PM.md) 与 [AI 需求](../../FieldToFit-PM.md)。**这是完整目标语义契约，不是当前接口声明。** 当前已实现 `metis.platform.v1` 子集（修订与字符偏移读取、固定快照索引、审核期次及精选变化），差异见[实际接口](../guides/platform.md)；Edition、稳定快照和精选变化基础已实现；v1.8.5源码已增加固定章节／PDF页范围与当前材料失效权限；OCR及逐事实证据映射仍按REQ补齐。 开发时先映射已有表/字段，优先复用，避免另建一套重复知识库；现有 API 见[使用指南](../guides/ai-access.md)。

## P3 增量设计与已实现子集

优先复用现有 Object/Change/Edition，建立 Organization → Product → Version 的有证据关系；Event 关联产品/版本/资源，Resource 是可持续维护的档案。一个资源可被多条动态引用，不按栏目复制。

- 动态补充事件日期、来源发布日期、平台发布日期、检查日期及日期可信度；不能用其中一个代替另一个。
- 当前 news 共享发布集合实现分点 interpretation、source_ids、locator、related、来源/核验日期，原文 link_only；GET /platform/news 与 curated_news 共用。原数据库期次保持兼容。
- 来源表分跟踪主体和发现渠道；状态来自实际配置与成功检查，关注信号保留平台、观察窗口、数值口径与证据。
- 人读与 AI 读同步以上字段；具体内容见[发布说明](launch-selection.md)。旧协议名 `metis.platform.v1` 是兼容标识，品牌更名不擅自改协议。

## 共用资料结构

| 结构 | 核心字段（拟定） | 约束 |
| --- | --- | --- |
| Object 对象 | id、name、aliases、types、summary、official_urls、upstream_version、revision、publication_state | ID 不变；上游版本与内部修订分开；类型可多角色且有依据 |
| Material 材料 | id、object_ids、kind、source_url、title、language、upstream_version、content_hash、revision、coverage、access_state、sections | 一个对象多材料；一份材料可关联多个对象；原 URL 与快照均可追溯 |
| Fact 事实 | id、object_id、field、value、applicable_version、evidence_refs、evidence_kind、status、checked_at | 每个关键结论有引用或明确未知；作者声称/编辑判断/观察分开 |
| Attention 关注依据 | object_id/change_id、signal_type、platform、value、window、observed_at、source_url、editorial_reason | 数量只能在自己的平台和统计窗口内解释；不合成为通用能力排名 |
| Change 变化 | id、object_ids、kind、from_revision、to_revision、source_published_at、published_at、evidence_refs | 区分新增/版本变化/更正/撤回；事件可暂不关联对象 |
| Edition 概览期次 | id、period、published_at、entry_refs、editorial_text、revision | 只引用已发布对象/变化修订；记录顺序、理由与更正 |
| Selection 精选资格 | object_id/change_id、state、reason、reviewed_at、reviewer、revision | 收录与精选独立；默认公开索引只返回已发布精选，历史范围显式请求 |

作者、论文 ID、评审/出版/撤回状态；模型卡、许可证；Skill 提交和附属文件；Harness 配置/扩展入口作为对象的类型专属事实和材料。没有来源就保留未知，不靠类型模板自动填值。

材料状态至少区分 `full_text`（相对于该份文档）、`partial`、`link_only`、`unavailable`。`full_text` 不代表整个项目资料齐全，PDF 文字完整也不代表图像/表格已解析。覆盖统计说明分母是“已登记的材料”，不能当作上游全部资料覆盖率。

时间至少分开来源发布日期、获取时间、最后成功核验时间和平台发布时间。未知日期用空值及原因；界面和 AI 都不能以采集日冒充发布日。来源检查状态与材料内容更新时间分开。

## AI 读取语义

| 能力 | 请求范围 | 结果必须包含 | 继续读取 |
| --- | --- | --- | --- |
| 检索索引 | 关键词、对象/类型、来源、日期、发布范围、游标 | schema_version、scope、snapshot、items、排序依据、has_more | 下一页游标及对象入口 |
| 对象档案 | 对象 ID、可选修订 | 身份、事实、限制、关注依据、材料清单、关系、时间、未知项 | 各材料及历史入口 |
| 材料清单 | 对象/修订 | 每份材料版本、类型、覆盖、语言、获取状态、原 URL | 可读材料 ID 或仅外部入口 |
| 原文读取 | 材料 ID/修订、章节或游标 | 文本/文件入口、章节/页码/文件、版本、实际范围、截断说明 | next_cursor、has_more 或缺失原因 |
| 中性导出 | 明确选定的对象/修订集合 | 清单、原文或已存片段、事实、来源、时间、缺口；JSON/Markdown | 大材料继续读取入口 |
| 增量变化 | 对象集合或公开范围、游标 | 变化类型、前后修订、发生/发布时间、证据、下一游标 | 同一窗口续读及下轮更新 |

不在此处新增面向用户任务的目标分析、能力打分、候选比较、执行步骤、学习路线或“最佳方案”字段。公开原文中原有的步骤可以作为有出处的材料保留，其内容不表示 FieldToFit 生成或验证了该方案。

基础事实过滤仍允许：用户或 AI 已知对象、类型、来源、时间时可直接缩小范围。有依据的使用条件是事实，AI 可以读取；平台不自动推导它是否满足用户任务。

## 一致性、错误和边界

1. 人读卡片、详情、导出、API/MCP 引用同一已发布修订。阅读会话带快照标识，更新发生时显式返回新修订而非混合新旧材料。
2. 首版建议目录默认每页 20 条、上限 100 条；原文每段默认约 12,000 字符、上限 50,000 字符。数值为实施初值，可据实测调整，但响应必须告诉调用方实际范围与续读方式，不能静默截断。
3. 区分未找到、没有权限、材料不可读、来源失败、游标失效、修订冲突、速率限制和内部失败；错误提供可采取的下一步，不以空数组掩盖故障。
4. 读取服务不访问用户的私有任务空间，不安装/执行资料中的 Skill 或代码；外部指令式内容作为引用数据。公开配置与导出不包含任何凭证。
5. 保留原始 URL、允许的文本和定位；不绕过访问限制。许可/可访问性变化时标注并按要求移除正文，变化流保留必要撤回信息。
6. 下载包需有实际可用的文字/引用和材料目录；仅索引包要明确“需联网继续读取”。服务是 localhost 时提示可达范围，不能假定用户的云端 AI 能打开。

## 从当前代码落地

先盘点当前 records、evidence、materials、relations、changes、editorial 等数据与接口的映射。对缺失字段提出最小增量迁移、回填和回滚方案；先验证一个对象的人读与 AI 读结果，再扩展精选集合。现有 API 路径不因本草案自动换版；需要新公开契约时由实现 PR 明确路径/版本及兼容期。

旧任务包使用 `task_context` 等能力，和这里的中性材料包不同。旧接口暂存，后续按 [REQ-X-01.03](../../FieldToFit-PM.md#req-16-3) 明确兼容，不能直接换返回值导致旧客户端误读。

## v1.0.4 投稿资料增量

持续关注 `fieldtofit.watch.v1` 增加可选 `origin=developer_submission` 与 `submission` 的 entry_url / usage / openness / relationship。项目名、介绍、来源、日期、结构化正文和解读复用原字段。只有已发布且 submission_review.confirmed=true 的记录可读；内部审核字段和非公开投稿字段不输出。HTTP 与 curated_watch 接受同名 origin 过滤，过滤结果和下载交接保留 origin 与修订；工具数量仍为 12。见[维护指南](../guides/project-submissions.md)。

## v1.1.0 内容权威与审核边界

`fieldtofit_content_sets` 保存动态、持续关注和图表的公开版本；`fieldtofit_content_items` 独立保存草稿及最近发布项，历史、候选和来源关联为私密管理数据。迁移前使用已审文件，迁移后公开读数据库发布版。既有字段白名单与公开修订语义保留；图表也过滤任意私密附加字段。旧对象/原文/期次契约兼容保留。

选中、保存、导入与预览不发布。发布须确认当前草稿版本、集合修订、材料指纹及原因；内部处理记录不进入 Web/MCP。详见[管理与迁移](../guides/management.md)。

## REQ-8-9 统一发现增量

当前源码新增 `curated_lookup` 及 `GET /api/v1/platform/lookup`；上线状态只见项目管理总览。动态和持续关注公开结构增加可选 `aliases`，未设置时不输出空字段，不改变既有公共修订。别名通过现有草稿审核与发布生效。

检索结果返回对象／事件，而不是把同一对象的多个材料拆成多个命中。每项包括 `scope/id/name/types/aliases/introduction/publication_revision/sources/coverage`、`match_reasons/snippets`、`reading/object_reading/bundle_ref` 和当前公开关系／维护状态（当前 D-/CW- 内容）。原文片段包含源 URL、材料 ID、哈希、已有定位与原始字符 `offset/end_offset`。片段是精确引用，未保存的正文不返回。

`publication_revision` 是检索结果的变更标识；继续读取应使用返回的精确工具参数，不自行拼修订。当前材料使用 `content_revision`，旧原文库使用数字 `revision`。固定游标只保证成员与顺序；正文权限和公开数据逐页重查，更新返回 `changed_since_search`，不再公开／匹配则返回只含 ID、不可用标记与说明的占位。来源故障和游标错误不能冒充零结果。详细参数见[接入指南](../guides/ai-access.md)。

## v1.8.5已实现增量与首期边界

本批按[已确认方案](../../FieldToFit-PM.md#req-19)开发，正式状态见总览与[隔离验收](../validation/2026-10-07-reviewed-maintenance.md)。

- Material沿用原body／materials_revision／content_hash，可加location_index（PDF物理页、印刷标签、原文件SHA-256、各页字符范围与缺口）。目录对固定正文构建Markdown标题／HTML标题或段落范围，不重新排版正文。PDF导入仅提取文字层，默认节选、未审批；全扫描文件仅链接，不声明全文。当前不托管原PDF二进制，保留原始URL和文件指纹，未实现OCR、图表实体或公式解析。
- Correction新增私密上下文与处理事件，绑定对象、实际发布修订、公开字段路径或固定材料选段、报告时基线。完成处理需实际后续publish快照、字段差异、明确公开说明与确认；原文选段可通过修订引用解读解决，不改写来源。仅已解决公开回执进入API／MCP；撤回修订不被再发布重新曝光。联系人、报告原文与内部备注仅后台可读。
- CW public revisions复用既有content_history，只投影import／publish白名单；最后一次withdraw之前的历史不可再读，当前被移除或撤回读取权限的材料只留最小占位。默认最新与上一不同公开投影，compare返回新增／删除／修改字段及两端档案出处；编辑内容和资料字段分开说明，不把资料变化认定为已验证产品事实。无历史不补造，D动态后续接入。
- Object checks独立于公开内容、材料可达性检查和来源发现：每日冻结已发布CW集合与必要入口计划，每次获取绑定当前已审基线，正文观察仅私密。核对记录需要字段旧值、新值、实际来源引文、位置／哈希、可选来源日期与版本；失败／未完成不计完成，未处理差异跨重试／日期保留，已发布采纳后才退出待办。缺全入口记录不能称全覆盖。五类对象共用，不自动调用模型、改检查日、建草稿或发布。

新增五表object_check_plans／runs／attempts和correction_contexts／events（统一fieldtofit_前缀）纳入私密备份，既有部署须幂等升级；原读取协议／offset语义兼容。后台API使用管理员凭据；公开目录、对照和回执沿用可选读取令牌；读令牌不能获得管理能力。详细路径见[AI接入](../guides/ai-access.md)和[维护](../guides/management.md)。
