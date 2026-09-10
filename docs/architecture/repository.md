# FieldToFit 目录与兼容清单

2026-09-11。当前功能与历史材料分开管理，运行目录保持稳定。

| 路径 | 用途与处理 |
| --- | --- |
| `frontend/` | 现行页面、构建与 5 份网站图片；不改变应用路由 |
| `backend/knowledge/platform*` | 现行精选、原文、来源、期次、维护与资料包 |
| `api/` | Vercel 入口；当前每日 cron 是 `/api/cron/platform` |
| `content/` | 既有导入名单与整理稿；新首发建议在文档中，未写入这些数据文件 |
| `docs/product/` | P2 目标、REQ、方案和待确认首发内容 |
| `docs/releases/` | FieldToFit 逐版说明 |
| `docs/archive/metis/` | Metis 旧版本、规划、设计与截图 |
| `docs/validation/` | 真实证据，索引区分现版与历史 |
| `examples/`、`tests/` | 技术样例与回归，旧案例不作为新产品成果 |
| `data/`、根目录旧数据库、`output/` | 数据与私有备份；不因名称旧就移走或删除 |
| `.env`、`.vercel/` | 本地凭据与部署关联，保留且不提交 |
| `.venv/`、`node_modules/`、构建及缓存 | 本地运行所需或可重建产物，保持忽略，不重新提交 |

## 仍在使用的旧模块

- `frontend/src/legacy/`：`/admin/curation` 仍引用的旧策展界面。
- `TaskWorkbench`、`KnowledgeReading`、旧资源与比较页面：App 的兼容路由仍有引用，不以退出主线等同死代码。
- `/api/mcp`：保留旧 9 项工具；公开新入口 `/api/mcp/curated` 只暴露 10 项精选工具。
- `scripts/start-backend.sh`、`scrape.sh` 等包装：转交 runtime 或 maintenance 实现，仍供已有启动方式使用。
- `backend/requirements.txt`：仅引用根依赖清单，属于兼容入口。
- 旧环境变量、`metis.db` 回退、数据库列及历史 schema：升级兼容；不能机械改名导致空库或客户端失效。

本轮没有改变数据库、定时任务、管理员配置或旧 API 返回值，没有批量删除 Python/前端代码。资料保留是否必要需由调用链和运行证据决定，不能只搜索旧名称。
