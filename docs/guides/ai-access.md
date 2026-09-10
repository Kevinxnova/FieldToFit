# API 与 MCP 接入（FieldToFit v1.0.0）

本文是现有接口使用说明。For your AI、原文续读及中性资料包已经实现；新增组织/产品/事件关系等 P2 目标仍见[需求状态](../product/requirements/for-ai.md)，不要按草案字段调用当前服务。

先启动 FieldToFit 后端。默认资料可公开读取；如服务配置了 `FIELDTOFIT_READ_TOKEN`，HTTP 请求需携带 `Authorization: Bearer <read-token>`。管理员密码不用于 AI 读取。

## HTTP MCP

公开地址为 `https://fieldtofit.top/api/mcp/curated`，只暴露 10 项精选工具；本地对应 `http://127.0.0.1:8000/api/mcp/curated`。下面是通用配置示意，客户端的配置字段可能不同；按所用客户端填写 URL 和可选读令牌。

```json
{
  "mcpServers": {
    "fieldtofit": {
      "type": "http",
      "url": "https://fieldtofit.top/api/mcp/curated"
    }
  }
}
```

网页 `/for-your-ai` 可以检查连接（`/connect` 兼容跳转）。旧兼容端点 `/api/mcp` 共 19 项工具：新增 `curated_history` 公开修订历史，保留 `curated_sources` 精选采集源状态，保留 `curated_bundle` 原文包及 `curated_changes`、`curated_editions`、`curated_edition`；其余精选读取 `curated_search`、`curated_object`、`curated_material`、`curated_export`，具体参数见[平台指南](platform.md)。以下旧 9 项保留兼容：`search`、`get_record`、`read_evidence`、`compare`、`task_context`、`changes`、`sources`、`daily_briefs`、`research_materials`。

## stdio 桥接

桥接程序向已运行的 HTTP 服务发送请求，不直接读数据库。启动客户端时将工作目录设为仓库根目录：

```bash
FIELDTOFIT_MCP_URL=https://fieldtofit.top/api/mcp/curated .venv/bin/python -m backend.mcp_stdio
```

客户端配置时，command 使用该 Python 的绝对路径，args 使用 `-m backend.mcp_stdio`，工作目录填写仓库路径；有读令牌时通过客户端环境配置 `FIELDTOFIT_READ_TOKEN`。stdout 只输出 JSON-RPC。

## 兼容保留的任务资料（退出新主线）

```json
{
  "goal": "为已有项目查找合适的工具",
  "persona": "engineer",
  "background": "已有 Python 项目，运行于 Linux",
  "constraints": {"deployment": "local"},
  "task_spec": {
    "inputs": "现有项目与公开接口说明",
    "outputs": "候选、采用依据和需要补查的材料",
    "success_criteria": "关键条件有出处，未知项明确保留"
  }
}
```

这是 `task_context` 的参数示意，不是新的产品主案例。返回值包含候选、匹配/不满足/未知条件、版本材料、四种采用路径和同份 Markdown；它不是已经完成用户任务的证明。正文可通过 `read_evidence` 分段读取，研究资料支持 BibTeX。

## 当前 HTTP API

- `GET /api/v1/records`：检索与分页。
- `GET /api/v1/records/<id>`：档案、事实、材料、关系与验证。
- `POST /api/v1/task`：使用上面的任务参数。
- `POST /api/v1/task/export`：生成 Markdown；网页导出使用当前请求返回的同份材料。
- `GET /api/v1/changes`：游标增量，按对象或主题限制范围。
- `GET /api/v1/sources`、`GET /api/v1/briefs`：覆盖情况和简报。

请求体使用 JSON。所有查询仅覆盖已收录的资料；缺失候选不代表全网没有方案。官方 Python MCP SDK 的 HTTP / stdio 技术验收见 [验证索引](../validation/README.md)，尚无所有桌面客户端或自主 Agent 效果保证。

## 当前 Skill / Agent 与独立能力筛选

`GET /api/v1/catalog` 返回已发布资源的类型和能力标签及数量；`GET /api/v1/records?object_type=skill&capability=document-processing` 按类型和标签筛选。MCP `search` 支持同名参数，分页方式不变。

`task_context`、`POST /api/v1/task` 和 `/api/v1/task/export` 接受 `object_type`、`capability`，返回的 `filters` 保留同一范围。Skill 档案的 `metadata.skill` 提供固定提交的 SKILL.md 和附属文件 URL；读取材料不会安装或执行 Skill。标签只用于发现候选，需核对事实条件和证据。

`research_materials` 和 `POST /api/v1/research` 的 `markdown` 是包含提纲、顺序、条件比较和引用的完整导出。`reading_order_basis` 区分模型建议与检索顺序；后者没有声称知识依赖已经验证。

## 后续迁移

`compare`、`task_context` 和研究生成相关能力本轮没有删除，但不再作为新平台默认使用路径。后续先盘点兼容性，再明确新字段/工具和迁移窗口，见 [REQ-X-01.03](../product/requirements/migration.md#req-x-01.03)。新接入示例将聚焦“检索对象 → 查看材料 → 读取原文 → 引用与更新”，不要求网站代做任务方案。
