# 部署与升级

当前运行代码为 FieldToFit v1.0.2，已部署到 https://fieldtofit.top，Vercel/Turso 公网读取和 10 项精选 MCP 工具已验；容器实际构建、生产维护写入/恢复和连续日周期的验收仍未完成，状态见 [REQ-O-03](../product/requirements/operations.md#req-o-03)。

## 本地 SQLite 与单服务部署

按 [本地开发](local-development.md) 安装依赖，运行 `cd frontend && npm run build` 生成静态页面。Flask 会提供 `frontend/dist` 中的页面，默认地址为 `127.0.0.1:8000`。回到根目录，把实际浏览地址加入配置后启动：

```dotenv
FRONTEND_URL=http://127.0.0.1:8000
ALLOWED_ORIGINS=http://127.0.0.1:8000,http://localhost:5173
```

```bash
./scripts/start-backend.sh
```

默认允许的是开发前端的 5173 端口；直接浏览后端静态页面或改变端口时，也要同步 `ALLOWED_ORIGINS`。否则对比等带 Origin 的 POST 请求会被拒绝，页面能打开并不表示所有操作都可用。

运行所用数据库由配置决定：同时有 `TURSO_DATABASE_URL` 和 `TURSO_AUTH_TOKEN` 时使用远程 Turso；否则使用 `${FIELDTOFIT_DATA_DIR}/fieldtofit.db`，未指定目录时为仓库 `data/fieldtofit.db`。不会自动使用或合并根目录的同名数据库。

对外提供服务时配置 HTTPS 反向代理、`ALLOWED_ORIGINS` 和 `FRONTEND_URL`。管理访问使用 `ADMIN_PASSWORD`，定时 API 使用不同的 `CRON_SECRET`，可选的 `FIELDTOFIT_READ_TOKEN` 用于限制资料读取。

## 每日采集

```bash
source .venv/bin/activate
python -m backend.scheduler
```

上面执行一次；`--daemon` 会每 1 天再次执行。`scripts/scrape.sh` 是原路径兼容入口，具体实现位于 `scripts/runtime/collect.sh`。只安排一种本地调度方式，避免重复启动同一任务。

macOS 的 `scripts/setup-mac.sh` 会安装依赖、初始化配置指定的数据库，并写入 `~/Library/LaunchAgents` 服务定义。只有需要安装这些本机服务时才运行它；本次仓库整理没有安装或重装用户的系统服务。

## 容器配置

仓库保留 Dockerfile 与 compose.yaml，可通过 `docker compose up --build` 启动 web 和每日 collector，共用持久化卷。当前环境尚未实际构建容器，不能把配置存在当作容器验收通过。可选的技术验证依赖不在默认运行镜像内。

## Vercel 与 Turso

保留仓库根目录为部署入口。`vercel.json` 构建前端并映射 Python API，远程数据库和管理凭证放在平台环境变量中。前后端同源时留空 `VITE_API_URL`；分开时填写 API origin，不附加 `/api`，并允许对应的前端 origin。

当前 `vercel.json` 只登记 `/api/cron/platform` 一个每日定时任务，每天 UTC 02:00（北京时间 10:00）运行。旧 knowledge、scrape、daily-news、classify、digest 路由保留兼容，但没有登记为当前 Vercel 自动调度。部署前按 [兼容边界](../architecture/README.md) 核对需要的流程，再检查平台当前支持的时长和调度限制。

所有定时 API 都检查 `CRON_SECRET`；检查 `GET /api/health`、资料直达页面、来源状态和管理登录。新表会在初始化时创建。beta.2 已增加显式事务及失败回滚，并通过模拟远程传输的检查；生产 Turso 的真实事务、超时和恢复仍需验收，不能以模拟结果替代。详见 [beta.2 验证](../validation/v1.1.0-beta.2-acceptance.md)。

## 从旧版本升级

1. 记录所用提交、配置的数据库类型/目录，以及现有调度入口；停止需要写入的服务后备份并验证可恢复性。
2. 更新源码和依赖，构建前端；先用隔离数据库检查本版，再安排实际升级。
3. 保留 `.env`、数据、日志和平台配置。不要用示例配置覆盖实际配置，也不要把根目录数据库直接覆盖到 data/。
4. 验证新工作台、`/admin/curation`、MCP 和原脚本入口；检查是否出现新字段或配置需求。

回滚时使用对应提交和相容的数据备份；本次整理没有做用户数据迁移，历史目录变化见 [beta.1 整理说明](../archive/metis/releases/v1.1.0-beta.1.md)，当前升级变化见 [FieldToFit v1.0.2 说明](../releases/v1.0.2.md)。

## 每日运行监控

本地 `python -m backend.scheduler` 与 Vercel `/api/cron/platform` 均调用 `backend.knowledge.platform_maintenance.run_daily`，负责已登记来源的更新与候选采集；不把待审内容自动发布。查看精选来源状态、采集日志及后台待审变化。具体操作与本地 AI 整理交接见[运行方案](operating-model.md)。

公开版本需保持 `FIELDTOFIT_PUBLIC_ACCOUNTS=0`。生产是否执行初始化由真实配置决定，不能为文档演示修改数据库；发布前确认已完成所需迁移。`CRON_SECRET`、数据库和管理凭据仅保存在部署环境。

每 1 天检查不代表每源均成功；连续 3 个真实日周期、故障恢复与至少一次每周复核须记录实际证据。本轮文档整理不执行维护、写库或重新部署。
