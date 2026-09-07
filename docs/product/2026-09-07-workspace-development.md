> 后续交付已更新：[42 项 REQ 结果](2026-09-07-delivery.md)。本文保留上一阶段快照。

# Metis 工作界面重构：运行与验证记录

日期：2026-09-07。

## 最新范围调整：账户暂不开放

当前版本不开放账户注册与登录。侧栏“我的账户”和收藏页“账户与同步”置灰、不可点击，并标注“待开放”；直接访问 `/account` 显示准备中说明，不展示登录或注册表单。浏览、检索、本地收藏及关注照常使用。

注册接口已有默认关闭保护，当前环境未启用 `METIS_PUBLIC_ACCOUNTS`，配置示例保持 `0`。现有账户数据和后台同步能力保留，账户开放与依赖账户的个性化订阅不属于当前开放范围。需求基线已同步到 v0.4。

## 当前成果

已完成首个可运行的页面与资料查询流程：信息和应用两个入口，任务关键词检索，主题、来源及发布日期筛选，稳定详情页，来源材料分段读取，2–4 项对比，收藏与关注，Markdown/JSON/BibTeX 导出，来源状态、反馈与账户页面。

前端采用新的统一导航、浅色和深色主题、中英文界面及手机底部导航。旧 `/discover`、`/daily-news` 和 `/community` 链接保留跳转；原策展与简报后台保留在 `/admin/curation`。

新资料库使用独立表维护事件、论文、资源、证据、关系、版本变更和指定条件下的验证记录。旧 `tools` 数据保留，迁移可重复执行；不相关或身份不明确的旧新闻进入待整理状态，未知发布日期不再用采集时间代替。

网页与 MCP 共用 `/api/v1` 查询服务。来源注册表、Mac 调度脚本和 Vercel 调度配置统一为每 1 天；新的日采集流程已接到原 cron 入口和本地调度器。

## 本地运行

沿用现有 Python 虚拟环境与前端依赖：

```bash
.venv/bin/python -m flask --app backend.api.main run --host 127.0.0.1 --port 8000
```

另一个终端启动网页：

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

访问 `http://127.0.0.1:5173`。普通资料查询不需要生成模型凭证。复制 `.env.example` 配置管理密码；私有部署可设置 `METIS_READ_TOKEN`，在网页 AI 接入页填入浏览器读取令牌，并在 MCP 客户端设置相同的 Bearer 令牌。

如果使用单一服务部署，先运行 `frontend` 下的 `npm run build`，然后由后端直接提供构建后的页面和 API。容器配置提供 `web` 与每日 `collector` 两个服务，数据库通过命名卷保存：

```bash
docker compose up --build -d
```

此容器配置尚未实际构建验证；当前环境没有 Docker。默认端口只发布到本机，需要远程访问时应在部署环境配置对应域名、来源白名单和管理凭证。

手动执行一次每日来源检查：

```bash
.venv/bin/python -m backend.scheduler
```

常驻调度使用 `--daemon`，每 1 天执行一次。已经检查过的来源在一个日周期内不重复自动抓取；管理页的手动重试用于处理失败。采集服务不会自动向用户发送邮件。

## AI 查询与 MCP

- `GET /api/v1/overview`：真实数据量及最近成功采集时间。
- `GET /api/v1/records`：`q`、`kind`、`topic`、`source`、`since`、`until`、`object_type`、`limit`、`offset`。`kind=information` 同时查询动态和论文。
- `GET /api/v1/records/{id}`：档案、事实来源、关系、材料目录及历史。
- `GET /api/v1/evidence/{id}`：按字符 `offset`、`limit` 读取材料，返回 `next_offset` 和覆盖范围。
- `GET /api/v1/records/{id}/export?format=markdown|json|bibtex`：导出保留来源和状态的资料。
- `POST /api/v1/compare`：`ids` 数组，2–4 项；可附 `constraints`。
- `POST /api/v1/task`：`goal`、`persona`、`constraints`；返回检索候选和待核实条件。
- `GET /api/v1/changes?after=0`：按单调递增游标获取变化；保留 `next_cursor`，当 `has_more=true` 时继续读取。下架或未发布资料仅返回状态，不泄露其历史正文。
- `GET /api/v1/sources`：来源状态，每个来源 `interval_days=1`。
- `GET /api/v1/cases`：实际存储的验证记录。

接口使用 `api_version=1`。检索分页每页最多 100 项；正文每次最多 100,000 字符。参数错误返回 400，读取令牌错误返回 401，跨来源写入返回 403，缺失或已下架档案返回 404。检索没有结果只表示当前收录范围内未找到。

MCP 地址为 `/api/mcp`，使用 Streamable HTTP 的 JSON 响应，支持协议版本 `2025-11-25`、`2025-06-18`、`2025-03-26`。工具包括 `search`、`get_record`、`read_evidence`、`compare`、`task_context`、`changes`、`sources`；均为只读，不包含管理、采集、生成和发送操作。

需要 stdio 的客户端可启动：

```bash
METIS_MCP_URL=http://127.0.0.1:8000/api/mcp .venv/bin/python -m backend.mcp_stdio
```

stdout 仅输出 JSON-RPC；诊断信息写入 stderr。HTTP 客户端请求需要 `Accept: application/json, text/event-stream`。协议依据：[MCP 传输说明](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)。

## 已执行的验证

- Python 自动检查 37 项通过，1 项外部服务集成测试按配置跳过；使用独立 SQLite 临时数据库，不连接生产库或生成模型。
- 前端 TypeScript 检查和生产构建通过。
- 浏览器验证：真实历史数据查询、无结果状态、收藏、两项对比、详情、材料读取、MCP 初始化。另用实际 stdio 客户端经过 HTTP 桥接完成初始化、列出 7 个工具、搜索、档案及证据读取。
- 手机检查：页面能切换到底部导航，正文可展开；已检查页面没有横向页面溢出。
- 实际公开来源检查：arXiv 成功获取 100 篇论文，官方 RSS 成功获取 30 条动态，写入隔离预览数据库。
- Hugging Face 模型和数据接口连接超时；OpenReview 返回 403。它们保留失败状态，没有伪造采集结果，也没有绕过访问限制。

浏览器预览使用旧数据库的副本，未把测试数据写回原库。构建没有发布到外部站点。页面上的记录和数量来自实际数据库，案例页面在没有实测记录时显示空状态。

## 与完整 42 项需求的差距

本次成果是可检查的工作界面与资料访问基础，不代表全部 42 项已经验收。

后续仍需完成：新资料的持续深入整理和关联，任务资料包与真实复现案例，复杂事件归并和拆分的管理流程，个性化邮件订阅和历史简报入口，新资料的双语摘要及可切换生成模型，自动运行验证，更多真实 MCP 客户端兼容检查，以及容器和生产部署验证。

当前任务查询使用文本和中英文关键词扩展，不能等同于已经完成语义检索或自动方案设计。界面上的“待核实”需要后续证据补充，不能用模型生成内容替代实测。200 个资源、60 份完整任务资料包和 12 个验证案例仍是资料建设目标，尚未全部完成。
