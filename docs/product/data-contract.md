# 资料模型与 AI 读取契约草案

P2 · 2026-09-11。对应 [共享基础](requirements/foundation.md) 与 [AI 需求](requirements/for-ai.md)。**这是完整目标语义契约，不是当前接口声明。** 当前已实现 `metis.platform.v1` 子集（修订与字符偏移读取、固定快照索引、审核期次及精选变化），差异见[实际接口](../guides/platform.md)；Edition、稳定快照和精选变化基础已实现；章节级游标、独立材料失效等仍按 REQ 补齐。 开发时先映射已有表/字段，优先复用，避免另建一套重复知识库；现有 API 见[使用指南](../guides/ai-access.md)。

## P2 增量设计（尚未实现）

优先复用现有 Object/Change/Edition，建立 Organization → Product → Version 的有证据关系；Event 关联产品/版本/资源，Resource 是可持续维护的档案。一个资源可被多条动态引用，不按栏目复制。

- 动态补充事件日期、来源发布日期、平台发布日期、检查日期及日期可信度；不能用其中一个代替另一个。
- 期次要点分为带引用的来源观点数组与 FieldToFit 编辑评价，保留作者、适用范围、未确认项和所引修订。
- 来源表分跟踪主体和发现渠道；状态来自实际配置与成功检查，关注信号保留平台、观察窗口、数值口径与证据。
- 人读与 AI 读同步以上字段；首发名单见[候选清单](launch-selection.md)。旧协议名 `metis.platform.v1` 是兼容标识，品牌更名不擅自改协议。

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

旧任务包使用 `task_context` 等能力，和这里的中性材料包不同。旧接口暂存，后续按 [REQ-X-01.03](requirements/migration.md#req-x-01.03) 明确兼容，不能直接换返回值导致旧客户端误读。
