# 架构与兼容边界

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
| backend/knowledge/tasks.py、task_plans.py、export.py | 任务资料与导出；技术样例保留，主案例 pending |
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

新旧表在同一配置指定的 SQLite/Turso 数据库中。`METIS_DATA_DIR` 决定本地路径，默认 `data/metis.db`；根目录同名文件不会被自动合并。本次整理保留用户数据、配置、日志、`.git`、`.vercel` 与本机依赖。

公开读取可选 `METIS_READ_TOKEN`；维护接口使用独立管理员凭证；定时接口使用 `CRON_SECRET`；公开账户当前关闭。模型服务凭证只保存在服务器。

已知技术缺口：Turso 连接缺少多步事务/失败回滚；运行脚本控制清单、临时目录和超时，但没有完整 CPU/内存/网络隔离。相关工作仍列在 [REQ](../product/requirements.md)。

## 版本与更新

应用版本由 `backend/__init__.py` 与 frontend package/package-lock 保持一致；健康接口从后端版本读取。本版是 `1.1.0-beta.1` 开发候选，API 路径仍为 `/api/v1`，二者不是同一种版本号。协议版本单独由 MCP 实现定义。

运行 `python scripts/maintenance/check_repository.py` 检查版本一致性、文档链接和前端相对导入。每次发布按 [版本维护说明](../releases/README.md) 执行。
