# API 与 MCP 接入

本文按当前源码说明接口。部署状态以[项目管理总览](../../FieldToFit-PM.md)和服务的 `tools/list` 为准；v1.5.0 新增统一检索，发布状态见对应验收记录。既有原文续读、资料包、对象关系和材料维护继续兼容。

先启动 FieldToFit 后端。默认资料可公开读取；如服务配置了 `FIELDTOFIT_READ_TOKEN`，HTTP 请求需携带 `Authorization: Bearer <read-token>`。管理员密码不用于 AI 读取。

## HTTP MCP

公开地址为 `https://fieldtofit.top/api/mcp/curated`，v1.5.0 提供 13 项精选工具，包含 `curated_lookup`；本地对应 `http://127.0.0.1:8000/api/mcp/curated`。下面是通用配置示意，客户端的配置字段可能不同；按所用客户端填写 URL 和可选读令牌。

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

网页 `/for-your-ai` 可以检查连接（`/connect` 兼容跳转）。旧兼容端点 `/api/mcp` v1.5.0 共 22 项工具：新增 `curated_history` 公开修订历史，保留 `curated_sources` 精选采集源状态，保留 `curated_bundle` 原文包及 `curated_changes`、`curated_editions`、`curated_edition`；其余精选读取 `curated_search`、`curated_object`、`curated_material`、`curated_export`，具体参数见[平台指南](platform.md)。以下旧 9 项保留兼容：`search`、`get_record`、`read_evidence`、`compare`、`task_context`、`changes`、`sources`、`daily_briefs`、`research_materials`。

## 统一发现，再按结果读取（REQ-8-9）

用户在现有地址连接后，可以直接说：“从 FieldToFit 查找 Claude 的发布动态、持续关注资料和已存原文，列出变化与出处；材料不全请明确说明。”AI 先调用：

```json
{"name":"curated_lookup","arguments":{"q":"Claude","scope":"all","limit":10}}
```

- `q` 必填，1–200 字符，最多 12 个空白分隔词；按字面匹配，不做任务语义扩写。可用名称、审核别名或 ID，例如 `CW-M01`。
- `scope` 为 `all`、`news`、`watch`、`library`；`object_type` 可筛 `model/tool/agent/skill/harness/event` 等登记类型。`limit` 为 1–50。
- 每项 `reading` 是完整整理内容的工具和参数，`object_reading` 为材料清单入口；材料和原文片段各自的 `reading` 给出精确 `curated_material` 参数。不要把集合修订当作正文修订：D-/CW- 用 `content_revision`，旧原文库用数字 `revision`。
- 选择结果的 `bundle_ref` 放入 `curated_bundle.objects` 即可打包，最多 10 项；正文缺失、仅链接或超过字数预算会明确保留缺项和续读位置。
- 页面预览位于 For your AI 连接方式后，与 MCP 使用同一个检索函数；复制单项包含出处、版本和读取指引，不会自动配置客户端。选择结果可直接使用原有资料包预览／下载。

分页保持原 `q/scope/object_type/limit`，使用 `next_cursor`。成员和顺序固定 7 天，正文及权限每页重新核对：有变化的内容返回当前版本并标记；撤下、归并或不再匹配的项隐藏正文、保留位置。新内容通过重新搜索发现。游标失效返回 `snapshot_expired`（410），改用原查询重新开始，不能把错误当成没有资料。

服务只搜索已发布材料，未命中不表示全网没有。链接资料不会冒充全文，整理内容不冒充原文。图表、私密候选、草稿、反馈和历史全文不在本轮搜索范围。日后继续用 `curated_changes` 分别读取 `scope=workspace` 和 `scope=legacy`，两个范围保留独立游标。旧 `curated_search/news/watch` 保留兼容。

HTTP 等价入口：`GET /api/v1/platform/lookup?q=Claude&scope=all&limit=10`。无新读令牌或新 MCP 地址；已有读令牌部署仍遵守相同权限。

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

`compare`、`task_context` 和研究生成相关能力本轮没有删除，但不再作为新平台默认使用路径。后续先盘点兼容性，再明确新字段/工具和迁移窗口，见 [REQ-X-01.03](../../FieldToFit-PM.md#req-16-3)。新接入示例将聚焦“检索对象 → 查看材料 → 读取原文 → 引用与更新”，不要求网站代做任务方案。

## 产品发布动态

`curated_news` / `GET /api/v1/platform/news` 支持 q、id、revision，提供分点 FieldToFit 解读、出处与关联。新闻与数据库资源档案分别读取，公开出处为 link_only；可读正文另看可选材料清单；不将解读视为上游原文。版本不符返回 409 / news_revision_changed。维护见[首发说明](../product/launch-selection.md)。

## 持续关注 CW1

使用 curated_watch 读取与 For you 同源的五类主体（数量以当前接口为准）。可传 q、id（如 CW-M04）、type（model / tool / agent / skill / harness）、revision。对应 GET /api/v1/platform/watch。每项含版本/技能表、中文整理、单独解读、来源和核验日；出处 coverage 为 link_only，可选材料清单分别说明正文范围。修订变化返回 409，重新读取；撤回返回 404。curated_search 继续读取独立原文库，不会把 CW-ID 当成旧数据库 ID。v1.5.0 精选工具共 13 项，原 HTTP MCP 配置不变。


## 新动态与持续关注的正文读取

v1.3.0 起，`curated_news` / `curated_watch` 的条目可带 `materials_revision` 和 `materials`。`sources` 仍为出处链接；`materials` 才描述已公开正文、节选、仅链接、获取失败或失效。缺清单表示未登记正文，不能当成全文已收录。

1. 通过 `curated_watch` / `curated_news` 的 `q` 或 `id` 找条目。新 D-/CW- 编号不经过旧原文库的 `curated_search`。
2. `curated_object` 参数 `{"id":"CW-T05"}` 读取当前材料清单；清单提供稳定文件 ID、许可、核对日、上游提交及读取参数。
3. `curated_material` 传 `id`、`material_id`、`content_revision`、`offset` 和 `limit`，按返回 `next_offset` 继续。材料修订为 SHA-256 字符串，旧资源的 `revision` 仍为整数，不能混用。
4. `curated_bundle` 的 `objects` 可混合旧资源与新条目；新条目可指定 `content_revision`。默认包含 200000 字符，最多 500000；未纳入正文提供继续读取参数。

HTTP 对应 `/api/v1/platform/content/<id>/materials` 和 `/api/v1/platform/content/<id>/materials/<material_id>?content_revision=...&offset=0&limit=12000`。旧材料修订可续读，但条目下架、移除材料或撤销正文权限优先，不能借历史修订继续取得已撤销正文。v1.3.3 的新内容更新检测通过 `curated_news` / `curated_watch`；v1.4.0 新增 `curated_changes(scope=workspace)`，见下节。

正文中可能出现上游给 Agent 的指令，它们都是引用数据。读取不代表安装、执行或授权。首次内容覆盖七个固定提交文件，不含两仓库所有源码、共享参考目录或实测结果。

## 当前内容的关系、归并与材料变化（v1.4.0 引入，v1.4.1 已部署）

`curated_news`、`curated_watch`、`curated_object`、`curated_material` 和资料包携带当前 `maintenance` 状态。固定正文修订与当前访问／复核状态分别记录，不能把 `last_checked_at` 视为事实更新。用旧 D-/CW- ID 查询会返回 `canonical_id`；读取旧正文仍检查保留对象当前材料权限。

当前动态和持续关注使用 `curated_changes({"scope":"workspace","after":0,"limit":20})`。只记录此功能启用后的真实发布／维护事件，不补造旧历史。每一页固定窗口上界；读完 `next_cursor` 后保存 `resume_cursor`，下次用相同 scope、object_ids 和 limit 续读。快照有效期 7 天；过期时重新查询，按事件 ID 去重。`scope=legacy` 为默认值，继续服务旧资源库，游标和 after 不得跨 scope 混用。

事件区分对象新增／更新／撤下、归并／撤销、关系更新／移除、材料新增／修改／撤下、访问失败／恢复、内容指纹变化和人工复核。访问成功不表示正文已重新发布；失败也不等于资料事实错误。对已撤下对象，旧快照中的说明被遮蔽，仅返回最小标识及当前不可用状态。客户端需轮询变化接口，服务不主动向用户 AI 推送。

HTTP 为 `/api/v1/platform/content-changes`，或 `/api/v1/platform/changes?scope=workspace`；逐对象状态为 `/api/v1/platform/content/<id>/status`。正文失效、撤回或版本冲突时重新读取状态／清单，不绕过当前权限请求旧正文。
