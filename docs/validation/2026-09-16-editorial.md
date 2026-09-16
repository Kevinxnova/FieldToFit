# 2026-09-16 · 内容发布与跨日取材验收

本批范围：用户确认日报 A/B/C，发布两条近期动态与 Hermes Agent 持续关注；版本 v1.5.1。内容发布、应用部署和客户端证据分别记录，不能互相替代。

## 已有真实客户端证据

发布本批新内容前，独立临时目录、临时公开 MCP 配置运行真实 Codex CLI。最初模型 WebSocket 请求超时，切换 HTTPS 后完成 8 次 MCP 调用：curated_lookup、curated_news × 2、curated_watch、curated_object × 3、curated_material。无 shell、网页或项目文件读取操作。

- curated_lookup 检索 Agents API，再按返回入口读取 D-12 并给出带出处回答。
- 动态、持续关注、D-12、D-13、CW-S04 的材料修订与 9 月 15 日基线一致；未人为制造发布。
- CW-S04 的 skills-interview-me-skill 按昨日固定修订，从 offset=12000 续读 2313 字符，总长 14313；has_more=false、next_offset=null。
- 全文哈希为 1d94741d10d2c826cd0c191aea3981ee94c8abb27ef2a166f6a372117d06448f；此处核对服务返回的哈希和末段，不宣称本次重新下载了全文。
- 原始事件与回答保存在忽略目录 output/briefings/2026-09-16-evidence/，不提交私密日报或运行输出。

## 运行观察边界

观察计划从 9 月 16 日开始，今天仅第 1 天。07:07–07:10 日任务结果为 44 成功、8 未完成、3 延期；Meta 公告、arXiv、字节公告未在本轮续跑。scheduler_header 是线索；平台日志查询 HTTP 400，不能认定 06:30 准时自动运行。今日日报补发，准时送达未通过；周维护计划 9 月 22 日。

## 本批内容与生产验证

| 检查 | 实际结果 |
| --- | --- |
| 原始材料 | Salesforce 与 CI 官网正文可读取；Hermes v2026.9.14 README 与 MIT LICENSE 固定版本已核对 |
| 发布前备份 | 私密内容库备份包含三集合及历史／批次／材料／维护记录；不是本次全库灾难恢复验收 |
| 审核边界 | 三份草稿生成、保存和浏览器预览时，公开集合修订保持不变 |
| 双端预览 | D-14、D-15、CW-A08 均通过真实管理页 For you / For your AI 预览，桌面 1440×1000、手机 390×844，无页面异常或全页横向溢出 |
| 内容发布 | 三项明确提交复核并发布，批次全部回写 published；保留原有 13 条动态、29 项关注内容，现为 15 / 30 |
| 网页 | 三项锚点、人读正文、Hermes 版本表与手机横向表格、交给我的 AI 复制、For your AI 搜索可用 |
| MCP / API | 两集合返回逐项一致；分别以 Salesforce、test impact analysis、Hermes 统一检索并按返回参数读取；三对象资料包共 7 份仅链接材料、0 正文字符；当前变化流返回新增对象与材料事件 |
| 同批文字复核 | Hermes 第三点去掉拟稿时的布局建议，改为面向读者的采用说明；重新预览发布，ID、材料和版本范围不变 |
| 本地回归 | 首轮 4 个测试仍固定旧资源数量，更新现有快照断言后 311 passed、1 skipped；无功能逻辑修改 |
| 构建与文档 | TypeScript / Vite 构建通过；仓库文档、链接、双语元数据检查通过 |
| 正式版本 | https://fieldtofit.top/api/health 返回 v1.5.1；MCP initialize 返回 1.5.1 |

首次应用部署：Vercel kevinnova-projects/fieldtofit，dpl_GXZXdz7umt2SnjcbnDP9b4pGVPnt，正式域名已关联。最终交付提交同步公开快照与本文件，后续同批部署可从平台记录核对；网站数据库发布与源码快照分别保留证据。

本批未把原文发布日期改成核对日期，未增加 Star 增长结论或运行实测结论，未改模型图表和五条速览。新增内容全部为结构化整理加来源链接，全文缺项明确保留。原始快照、提案、备份、截图与运行记录保存在忽略目录 output/operations/v1.5.1-release/，不提交 GitHub。

初次发布动态修订 d808367e00a8d9193758013a0d39fff2dc5251aa1a9d3c6dc43c06425f369ef0；Hermes 同批文字复核后的最终持续关注修订以 final-runtime.json 为准。真实客户端的无变化跨日验证发生在本批新增发布之前；新增内容后的客户端变化观察仍留待下一次真实读取。
