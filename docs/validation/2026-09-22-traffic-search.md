# 访问统计与搜索发现：需求文档核对

日期：2026-09-22。范围：v1.5.8 文档批次；新增 REQ-17 / REQ-18，各六个子项。此记录只保存核对证据，需求和分期唯一来源为 [FieldToFit-PM.md](../../FieldToFit-PM.md#req-17)。不代表功能测试、生产部署或搜索引擎收录通过。

## 已执行核对

- 工作开始时仓库无未提交修改，当前提交为 `215eed9`（v1.5.7）。
- 读取项目管理总览、AGENTS.md、发布指南及部署指南；公开账户继续关闭，应用案例暂缓。
- 检查 `frontend/index.html`、`frontend/src/App.tsx`、D-/CW- 阅读组件、`backend/api/main.py` 和 `vercel.json`。前端模板 canonical/OG URL 指向首页；浏览器端更新标题；D-/CW- 分享使用页内 hash。Flask 对旧 `/records/:id` 有标题／描述替换，但不等于新 D-/CW- 独立搜索页；Vercel 非 API 请求兜底到 index.html。源码中未发现访问事件／访客统计或专门 robots/sitemap 实现。
- 查询 Google 的 JavaScript SEO、sitemap 与搜索工作原理，以及 Bing 验证与 sitemap 官方资料；具体来源保存在 [REQ-18 官方依据](../../FieldToFit-PM.md#req-18)。百度普通收录官方搜索摘要可读，直接打开超时；没有核验任何站长账号的具体权限。
- 首次 Python 公网请求遇到当前执行环境 DNS 限制；获准联网重试后，五个地址均遇到本机证书链验证失败：`/api/health`、`/robots.txt`、`/sitemap.xml`、`/for-you`、`/about`。网页工具也未能打开前三个地址。这些失败不证明正式站宕机、证书无效或搜索引擎未收录。

## 检查结果

- `release_metadata.py --write`：通过，前后端及两份 README 同步到 v1.5.8，发布标签标记为未推送。
- `check_repository.py`：通过，98 份文档、796 个本地链接、143 个相对导入、18 项主 REQ、113 项子 REQ、42 个历史锚点、91 个旧子项映射，0 错误。
- `git diff --check`：通过。
- 系统 curl 使用正常证书验证补验成功；响应日期 2026-09-22 00:05 UTC（北京时间 08:05）。`/api/health` 返回 HTTP 200，`{"status":"ok","version":"v1.5.7"}`。
- `/robots.txt` 和 `/sitemap.xml` 均返回 HTTP 200，但 Content-Type 为 `text/html; charset=utf-8`、Content-Disposition 为 `index.html`，正文是应用 HTML 外壳，不是有效 robots 文本或 XML 站点地图。两者与公开页 ETag 相同。
- `/for-you` 和 `/about` 均为 HTTP 200，初始响应只有空的 `root` 内容容器，title 均为 `FieldToFit · FIELD → FIT`，canonical 均为 `https://fieldtofit.top/`。这证明初始 HTML 及元数据缺口；不证明 Google 渲染后不能读取，也不证明尚未收录。
- 没有站长平台登录或索引报告，Google/Bing/百度当前收录状态仍未知。

## 未执行事项

未新增采集代码、统计表、HTML 路由、robots 或 sitemap；未读取或修改生产数据库，未进行部署；未登录站长平台、验证域名、提交网址、创建自动监控或向外发送消息。访客计数、桌面／手机交互、权限、迁移、连续自然日、抓取、收录和搜索效果均待功能实现后另验。本批不运行应用功能测试或前端构建，文档检查不替代这些验收。


## 同日补充：v1.5.9 全站累计访问次数需求对齐

用户重新要求在网站合适位置展示 FieldToFit 总站访问次数。本次核对 `frontend/src/App.tsx` 现有公共页脚，选定站点介绍文字下方；仅更新 REQ-17 首期方案及新增 REQ-17-7，将详细分析和私有后台列为后续。未编辑前端组件、采集服务或数据库，未部署；本轮没有重新请求生产，正式站状态沿用上方带时间的只读证据。

验收检查：`release_metadata.py --write` 同步 v1.5.9 通过；`check_repository.py` 通过，98 份文档、796 个本地链接、143 个相对导入、18 项主 REQ、114 项子 REQ、42 个历史锚点、91 个旧子项映射，0 错误；`git diff --check` 通过。本轮不运行功能测试，公开次数、持久化与双端显示仍未验证。
