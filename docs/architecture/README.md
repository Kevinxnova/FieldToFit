# 架构与兼容边界

当前为 **FieldToFit v1.0.2**，公开读取已部署验证。目录整理与仍在运行的兼容模块见[目录清单](repository.md)。精选实现：`backend/knowledge/platform.py` 复用对象/证据，新增配置、精选状态、发布快照三张表；本轮再加读快照、期次草稿和期次发布三表，见 `platform_updates.py`；API/MCP/网页共用已审快照。前端 `Platform.tsx` 承载 For you / For your AI / About，`CuratedReview.tsx` 承载对象审核，`EditionReview.tsx` 承载期次审核，`PlatformHistory.tsx` 展示期次与变化。目标与实际子集见[契约](../product/data-contract.md)和[平台指南](../guides/platform.md)。

```text
来源与官方材料
    ↓ 每日发现 / 原文读取 / 整理队列
backend/knowledge → 事实、证据、版本、关系、历史与验证
    ├── /api/v1 → React 工作台
    └── /api/mcp → HTTP 客户端 / stdio 桥接

旧 tools / issues 数据 → 旧 API → /admin/curation
```

## 代码导航

| 目录 / 文件 | 责任 |
| --- | --- |
| backend/api/main.py | Flask 入口、静态页面、健康检查，以及仍保留的旧 API |
| backend/knowledge/api.py、mcp.py | 当前知识库 API、管理权限与只读 MCP |
| backend/knowledge/store.py、schema.sql | 当前资料、证据、关系和历史存储 |
| backend/knowledge/sources.py、paging.py、materials.py | 来源发现、分页进度和原文获取 |
| backend/knowledge/processing.py、models.py、daily.py | 整理队列、生成适配、每日处理 |
| backend/knowledge/tasks.py、task_plans.py、export.py | 原任务资料与导出；退出新主线，代码兼容保留，案例 pending |
| backend/knowledge/editorial.py、verification.py | 审核及受维护者审核的运行检查 |
| backend/db、scrapers、dedup、config.py、security.py | 共享数据库、采集、身份归并、配置与权限辅助 |
| backend/scheduler.py、mcp_stdio.py | 本地日调度入口与 stdio 桥接 |
| frontend/src/App.tsx | 路由与工作台外壳 |
| frontend/src/pages、components/workspace、api/knowledge.ts | 当前页面、共用组件与知识库请求 |
| frontend/src/legacy | 旧策展页面、组件、请求、语言文案和 hook |
| api、vercel.json | 部署平台函数、路由与定时配置，原路径保留 |
| scripts | 分组后的安装、运行和维护脚本，旧入口兼容 |
| examples、tests | 可显式导入的材料、技术验收脚本和自动行为检查 |

## 新旧边界

旧策展后台仍依赖 `tools`、`issues`、人工推荐和 Newsletter。`backend/api/main.py`、`backend/db/queries.py`、classifier、translate、ai_recommend、daily_news、email 和 cron_tasks 等模块仍承担这条流程；本版只明确归属，没有重写这些业务。

新知识库与旧流程共用部分采集和数据库设施。来源配置中也包含旧采集器适配。`api/cron*.py` 及对应 Vercel 定时项不能仅凭名称判定无用；本轮保留它们，后续取消或迁移需验证生产用途。

前端 `/discover`、`/daily-news`、`/community` 的兼容路由仍重定向到现行页面；未使用的旧页面源码已删除。`/admin/curation` 继续加载 legacy 目录中的策展页面。

## 数据与权限

新旧表在同一配置指定的 SQLite/Turso 数据库中。`FIELDTOFIT_DATA_DIR` 决定本地路径，默认 `data/fieldtofit.db`；根目录同名文件不会被自动合并。本次整理保留用户数据、配置、日志、`.git`、`.vercel` 与本机依赖。

公开读取可选 `FIELDTOFIT_READ_TOKEN`；维护接口使用独立管理员凭证；定时接口使用 `CRON_SECRET`；公开账户当前关闭。模型服务凭证只保存在服务器。

beta.2 已加入显式事务与失败回滚，并有模拟远程传输检查；生产 Turso 公开读取已验；生产维护事务、超时恢复和完整备份恢复仍待实测。运行脚本有清单、临时目录和超时控制，没有完整 CPU/内存/网络隔离；通用运行沙箱不在新平台范围。原技术记录保留，新的部署边界见 [REQ-O-03](../product/requirements/operations.md#req-o-03)。

## 版本与更新

应用版本由 `backend/__init__.py` 与 frontend package/package-lock 保持一致；健康接口从后端版本读取。本版应用版本是 `1.0.1`，API 路径仍为 `/api/v1`，二者不是同一种版本号。协议版本单独由 MCP 实现定义。

运行 `python scripts/maintenance/check_repository.py` 检查版本一致性、文档链接和前端相对导入。每次发布按 [版本维护说明](../releases/README.md) 执行。

仓库检查器已分别校验 18 个父 REQ、72 个子 REQ 和 42 个历史锚点，检查编号归属及链接；旧 42 项不计入新需求完成率。
