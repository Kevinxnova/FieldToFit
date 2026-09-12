# FieldToFit REQ list · 平台基线 P3

更新日期：2026-09-12。**现行需求与状态唯一入口。** 当前应用版本 v1.1.0。P3 + CW1 已实现 10 条近期动态、五类 27 个持续关注主体、结构化版本/技能表、分点解读、页内目录及同源 curated_watch；精选 MCP 共 12 项。原有数据库及兼容 API 保留，页面删除旧归档/资料库入口。两来源 2026 年模型图表、公司配色、直接名称标注与各家旗舰筛选已实现；保留双页导读；图表证据见[v1.0.3 验收](../validation/2026-09-11-v1.0.3.md)，前版卡片与说明调整见[v1.0.5 验收](../validation/2026-09-12-v1.0.5.md)。[本轮验收与部署状态](../validation/2026-09-11-continuous-watch.md)。v1.1.0 新增统一内容管理、每日审阅→草稿→双端预览→发布及原样迁移，见[本版验收](../validation/2026-09-12-v1.1.0.md)。来源跟踪表、完整原文采集、统一对象关系及持续运营仍未完成。

[项目立意](goals.md) · [页面方案与文案](pages.md) · [资料与读取契约](data-contract.md) · [验收](acceptance.md) · [路线图](../../ROADMAP.md)

## 范围与状态规则

- 当前范围为 **22 个 REQ、91 个子 REQ**。使用 `REQ-` 前缀区别于历史编号；子项以 `.01` 等后缀标识。下面链接逐项给出用途、方案、验收、依赖和状态。
- 全部属于本轮平台目标；按路线图分阶段完成。现有功能可复用，父项仅在全部子项通过各自标准后关闭。各子项按本次实现更新；证据见[基础检查](../validation/2026-09-09-platform-foundation.md)及[期次与增量检查](../validation/2026-09-09-platform-updates.md)。
- “待开发”需新增能力；“待适配”有代码基础但仍需调整/验证；“待实测”需真实环境或用户记录；“待执行”为运营动作。后续新增“开发中 / 已验收 / 受阻”，附日期、原因与证据。
- 对外内容精选、中文结构化表达与原文并存；不保证全网覆盖、所有类型各有固定数量或全量双语。每个自动检查/更新周期 **1 天**。
- 社区为独立辅助页；开发者投稿复用现有审核与资料读取，账户菜单移除。案例 pending；注册、登录、同步待开放；任务选型比较、场景和执行计划生成不在新主线。
- 旧 200 资源 / 100 论文 / 60 任务包 / 12 案例目标失效。已有 27 项公开对象；动态按[内容说明](launch-selection.md)维护，新增档案另经材料审核，发布质量门槛优先。

## 现行 REQ 总表

| REQ | 需求 | 子 REQ 范围 | 本轮状态 | 阶段 |
| --- | --- | --- | --- | --- |
| [REQ-F-01](requirements/foundation.md#req-f-01) | 统一对象档案与身份 | .01–.04 | 部分实现；范围与缺口见子项 | S1 |
| [REQ-F-02](requirements/foundation.md#req-f-02) | 可追溯的完整材料 | .01–.04 | 部分实现；范围与缺口见子项 | S1 |
| [REQ-F-03](requirements/foundation.md#req-f-03) | 事实、关注依据与双端一致 | .01–.04 | 部分实现；范围与缺口见子项 | S1 |
| [REQ-F-04](requirements/foundation.md#req-f-04) | 每日来源检查与增量更新 | .01–.04 | 1 天基础保留；连续真实周期待验 | S1–S4 |
| [REQ-F-05](requirements/foundation.md#req-f-05) | 精选发布与内容质量 | .01–.04 | 部分实现；范围与缺口见子项 | S1 |
| [REQ-Y-01](requirements/for-you.md#req-y-01) | For you 本期速览 | .01–.04 | 部分实现；范围与缺口见子项 | S2 |
| [REQ-Y-02](requirements/for-you.md#req-y-02) | For you 动态与持续关注 | .01–.04 | 部分实现；范围与缺口见子项 | S2 |
| [REQ-Y-04](requirements/for-you.md#req-y-04) | For you 页内目录与阅读定位 | .01–.04 | 已实现并通过本地及公网页面验收 | S2 |
| [REQ-Y-05](requirements/for-you.md#req-y-05) | 模型能力与价格两来源图表 | .01–.05 | 已实现；连续真实日维护待验 | S2 |
| [REQ-Y-03](requirements/for-you.md#req-y-03) | 档案详情与交给我的 AI | .01–.04 | 部分实现；范围与缺口见子项 | S2–S3 |
| [REQ-AI-01](requirements/for-ai.md#req-ai-01) | For your AI 入口与资料索引 | .01–.04 | 部分实现；范围与缺口见子项 | S3 |
| [REQ-AI-02](requirements/for-ai.md#req-ai-02) | 分层读取与中性资料包 | .01–.04 | 部分实现；范围与缺口见子项 | S3 |
| [REQ-AI-03](requirements/for-ai.md#req-ai-03) | 只读 MCP 与实际客户端接入 | .01–.04 | 部分实现；范围与缺口见子项 | S3 |
| [REQ-AI-04](requirements/for-ai.md#req-ai-04) | 版本变化与持续取材 | .01–.04 | 部分实现；范围与缺口见子项 | S3 |
| [REQ-AB-01](requirements/about.md#req-ab-01) | 关于 FieldToFit 页面 | .01–.04 | 部分实现；范围与缺口见子项 | S2–S3 |
| [REQ-C-01](requirements/community.md#req-c-01) | 社区与开发者投稿 | .01–.04 | 页面/通道/读取已实现；真实投稿运营待执行 | S2–S4 |
| [REQ-O-01](requirements/operations.md#req-o-01) | 维护后台与发布审核 | .01–.04 | 部分实现；范围与缺口见子项 | S1–S4 |
| [REQ-O-02](requirements/operations.md#req-o-02) | 运行监控与整理服务 | .01–.04 | 既有运行基础；在线整理与连续运营待验 | S1–S4 |
| [REQ-O-03](requirements/operations.md#req-o-03) | 访问边界与可部署运行 | .01–.04 | 公网读取与本版管理写入已验；全库灾难恢复待验 | S1–S4 |
| [REQ-O-05](requirements/operations.md#req-o-05) | 统一内容管理工作台 | .01–.06 | 已实现；范围与验收见 v1.1.0 | S4 |
| [REQ-O-04](requirements/operations.md#req-o-04) | 小范围运营与需求反馈 | .01–.04 | 反馈入口已有；真实用户与运营待验 | S1–S4 |
| [REQ-X-01](requirements/migration.md#req-x-01) | 旧功能与新入口迁移 | .01–.04 | 文档/导航/增量表已适配；生产迁移待验 | S0–S4 |

## 历史 42 项 REQ 的去向

**下表只用于旧链接和版本记录的追溯，不是现行 42 项完成率。** 调整前的逐项状态与原始验收要求见[完整快照](../archive/metis/2026-09/2026-09-08-before-platform-requirements.md)。历史版本说明继续描述当时交付，不改写成新目标的完成证据。

新编号必须写全 `REQ-` 前缀，尤其旧 AI-03（任务资料包）与新 REQ-AI-03（MCP）不可混用。映射中的“退出”表示退出后续产品主线，本轮没有删除对应代码/API。

| 旧 REQ | 现行对应 | 处理决定 |
| --- | --- | --- |
| <a id="d-01"></a>D-01 | [REQ-F-04](requirements/foundation.md#req-f-04) / [REQ-O-01](requirements/operations.md#req-o-01) | 保留来源管理，按精选范围维护 |
| <a id="d-02"></a>D-02 | [REQ-F-04](requirements/foundation.md#req-f-04) / [REQ-O-02](requirements/operations.md#req-o-02) | 保留 1 天更新和真实连续观察 |
| <a id="d-03"></a>D-03 | [REQ-F-01](requirements/foundation.md#req-f-01) / [REQ-X-01](requirements/migration.md#req-x-01) | 保留身份与归并，适配对象/变化 |
| <a id="d-04"></a>D-04 | [REQ-F-01](requirements/foundation.md#req-f-01) / [REQ-Y-02](requirements/for-you.md#req-y-02) | 稳定 ID 和类型保留；领域导航退出 |
| <a id="d-05"></a>D-05 | [REQ-F-03](requirements/foundation.md#req-f-03) | 保留事实和证据，加入关注依据 |
| <a id="d-06"></a>D-06 | [REQ-F-01](requirements/foundation.md#req-f-01) / [REQ-AI-04](requirements/for-ai.md#req-ai-04) | 保留关系和版本历史 |
| <a id="d-07"></a>D-07 | [REQ-F-03](requirements/foundation.md#req-f-03) / [REQ-O-01](requirements/operations.md#req-o-01) | 保留双端一致及冲突处理 |
| <a id="d-08"></a>D-08 | [REQ-F-02](requirements/foundation.md#req-f-02) / [REQ-AI-02](requirements/for-ai.md#req-ai-02) | 加强完整材料清单、版本和分段 |
| <a id="i-01"></a>I-01 | [REQ-Y-01](requirements/for-you.md#req-y-01) / [REQ-Y-02](requirements/for-you.md#req-y-02) | 独立信息页改统一概览和精选流 |
| <a id="i-02"></a>I-02 | [REQ-Y-03](requirements/for-you.md#req-y-03) / [REQ-F-03](requirements/foundation.md#req-f-03) | 保留分层解释，移除推演式任务建议 |
| <a id="i-03"></a>I-03 | [REQ-Y-01](requirements/for-you.md#req-y-01) | 简报改本期概览，中文优先保留原文 |
| <a id="i-04"></a>I-04 | [REQ-Y-03](requirements/for-you.md#req-y-03) / [REQ-AI-04](requirements/for-ai.md#req-ai-04) | 保留本地对象跟踪；任务条件订阅退出 |
| <a id="a-01"></a>A-01 | [REQ-F-01](requirements/foundation.md#req-f-01) / [REQ-Y-03](requirements/for-you.md#req-y-03) | 重心改为持续维护的精选对象档案 |
| <a id="a-02"></a>A-02 | [REQ-AI-01](requirements/for-ai.md#req-ai-01) / [REQ-Y-02](requirements/for-you.md#req-y-02) | 保留事实检索；任务语义扩展退出主线 |
| <a id="a-03"></a>A-03 | [REQ-F-03](requirements/foundation.md#req-f-03) / [REQ-F-02](requirements/foundation.md#req-f-02) | 有依据的使用条件作为事实保留 |
| <a id="a-04"></a>A-04 | [REQ-X-01](requirements/migration.md#req-x-01) | 比较/适配排序退出新主线，旧能力兼容 |
| <a id="a-05"></a>A-05 | [REQ-F-02](requirements/foundation.md#req-f-02) / [REQ-AI-02](requirements/for-ai.md#req-ai-02) / [REQ-X-01](requirements/migration.md#req-x-01) | 版本材料保留；任务步骤生成退出；案例 pending |
| <a id="a-06"></a>A-06 | [REQ-F-01](requirements/foundation.md#req-f-01) | 保留已证实关系；不生成替代品方案 |
| <a id="ai-01"></a>AI-01 | [REQ-AI-01](requirements/for-ai.md#req-ai-01) / [REQ-AI-02](requirements/for-ai.md#req-ai-02) | 保留独立 API 并适配新数据视图 |
| <a id="ai-02"></a>AI-02 | [REQ-AI-02](requirements/for-ai.md#req-ai-02) / [REQ-F-02](requirements/foundation.md#req-f-02) | 保留并加强原文续读 |
| <a id="ai-03"></a>AI-03 | [REQ-AI-02](requirements/for-ai.md#req-ai-02) / [REQ-X-01](requirements/migration.md#req-x-01) | 原任务规划职责退出；中性资料包另列，新 REQ-AI-03 专指 MCP |
| <a id="ai-04"></a>AI-04 | [REQ-F-03](requirements/foundation.md#req-f-03) / [REQ-AI-02](requirements/for-ai.md#req-ai-02) | 保留未知、证据和读取边界 |
| <a id="ai-05"></a>AI-05 | [REQ-AI-04](requirements/for-ai.md#req-ai-04) | 保留对象增量；任务条件订阅退出 |
| <a id="h-01"></a>H-01 | [REQ-Y-01](requirements/for-you.md#req-y-01) / [REQ-Y-02](requirements/for-you.md#req-y-02) / [REQ-AI-01](requirements/for-ai.md#req-ai-01) / [REQ-AB-01](requirements/about.md#req-ab-01) / [REQ-X-01](requirements/migration.md#req-x-01) | 原双模块导航由两主页面加关于页替代 |
| <a id="h-02"></a>H-02 | [REQ-Y-03](requirements/for-you.md#req-y-03) / [REQ-AB-01](requirements/about.md#req-ab-01) / [REQ-X-01](requirements/migration.md#req-x-01) | 保留稳定分享、直达和元信息 |
| <a id="h-03"></a>H-03 | [REQ-Y-03](requirements/for-you.md#req-y-03) / [REQ-O-03](requirements/operations.md#req-o-03) | 本地保存保留；注册/同步继续关闭 |
| <a id="h-04"></a>H-04 | [REQ-Y-03](requirements/for-you.md#req-y-03) / [REQ-AI-02](requirements/for-ai.md#req-ai-02) | 保留中性材料导出；比较/任务导出仅兼容 |
| <a id="o-01"></a>O-01 | [REQ-O-01](requirements/operations.md#req-o-01) | 保留后台并增加精选/概览发布审核 |
| <a id="o-02"></a>O-02 | [REQ-O-02](requirements/operations.md#req-o-02) / [REQ-F-04](requirements/foundation.md#req-f-04) | 保留监控、预算、恢复与日记录 |
| <a id="o-03"></a>O-03 | [REQ-O-03](requirements/operations.md#req-o-03) | 保留部署验证、备份和恢复 |
| <a id="o-04"></a>O-04 | [REQ-O-03](requirements/operations.md#req-o-03) / [REQ-AI-03](requirements/for-ai.md#req-ai-03) | 保留读写权限边界 |
| <a id="o-05"></a>O-05 | [REQ-O-05](requirements/operations.md#req-o-05) | 统一内容管理工作台 | .01–.06 | 已实现；范围与验收见 v1.1.0 | S4 |
| [REQ-O-04](requirements/operations.md#req-o-04) / [REQ-O-01](requirements/operations.md#req-o-01) | 转为理解、取材、复访和纠错验证 |
| <a id="o-06"></a>O-06 | [REQ-O-02](requirements/operations.md#req-o-02) | 生成仅用于资料整理，不做用户任务规划 |
| <a id="m-01"></a>M-01 | [REQ-AI-03](requirements/for-ai.md#req-ai-03) | 保留只读 MCP；改验收为真实客户端取材引用 |
| <a id="m-02"></a>M-02 | [REQ-AI-01](requirements/for-ai.md#req-ai-01) / [REQ-AI-03](requirements/for-ai.md#req-ai-03) | 接入示例围绕读取，取消四类任务方案要求 |
| <a id="v-01"></a>V-01 | [REQ-X-01](requirements/migration.md#req-x-01) | AI 应用案例 pending，退出当前正式版门槛 |
| <a id="v-02"></a>V-02 | [REQ-AI-02](requirements/for-ai.md#req-ai-02) / [REQ-O-03](requirements/operations.md#req-o-03) / [REQ-X-01](requirements/migration.md#req-x-01) | 既有技术检查保留；通用执行沙箱退出当前范围 |
| <a id="r-01"></a>R-01 | [REQ-F-01](requirements/foundation.md#req-f-01) / [REQ-F-02](requirements/foundation.md#req-f-02) / [REQ-F-03](requirements/foundation.md#req-f-03) | 论文作为 Research 对象，保留作者/版本/评审状态与引用 |
| <a id="r-02"></a>R-02 | [REQ-F-01](requirements/foundation.md#req-f-01) | 保留论文与代码、模型、数据的有证据关系 |
| <a id="r-03"></a>R-03 | [REQ-F-03](requirements/foundation.md#req-f-03) / [REQ-X-01](requirements/migration.md#req-x-01) | 论文报告条件作为事实；方法比较产品退出主线 |
| <a id="r-04"></a>R-04 | [REQ-F-02](requirements/foundation.md#req-f-02) / [REQ-X-01](requirements/migration.md#req-x-01) | 官方学习材料作为来源保留；学习路径生成退出 |
| <a id="r-05"></a>R-05 | [REQ-F-02](requirements/foundation.md#req-f-02) / [REQ-AI-02](requirements/for-ai.md#req-ai-02) / [REQ-X-01](requirements/migration.md#req-x-01) | 保留可核实引用与材料导出；提纲/阅读顺序生成退出 |

## 更新方式

1. 开发前选定父 REQ 和子项；执行时引用完整新编号，不能沿用旧标题推断范围。
2. 开发后只更新实际完成子项，附验证记录；父项全部验收才能关闭。不能以文档、接口自测或内容数量替代真实验收。
3. 需求范围变化同时更新目标、方案、验收和路线图；实现变化进入 CHANGELOG 和对应版本说明。
4. 仓库检查器已同时校验 22 个父项、91 个子项及 42 个历史锚点，输出三类独立计数；见 REQ-X-01.04。
