# 公开 AI 日报运行说明

对应 [REQ-24](../../FieldToFit-PM.md#req-24)。本模块与既有 08:00 私密选题日报分开，主导航仍只有 For you / For your AI。当前源码完成本地实现；本说明不代表已部署或启用生产定时发布。

## 阅读、发布和版本

- `/for-you/daily` 打开最新真实期次；日期页 `/for-you/daily/YYYY-MM-DD`，归档 `/for-you/daily/archive`；英文加 `/en`。
- 管理入口 `/admin?section=journal`：整期 JSON 导入 → 保存私密草稿 → 中英文预览 → 确认来源、行情时间及双语 → 生成两份 PDF → 发布。更新用 `draft_version` 防止覆盖并发修改，原因中英文必填；撤回后全部历史下载和读取不可用。
- `GET /api/v1/daily` 返回归档，`/latest` 返回最新；`/<date>?lang=en&revision=1` 返回指定语言/修订。`/<date>/pdf` 使用相同参数，文件名包含期次、语言、修订。
- MCP `curated_daily` 不传 `day` 返回归档；`day="latest"` 或实际日期读取；所有入口共享 `publication.content_hash`。PDF 的 Subject 和页脚保留内容哈希及修订，内部覆盖台账不公开。旧 `/api/daily-news` 和旧简报接口保持。
- 七个新闻栏目、最多三条重点、产品追踪和全部三个市场；PDF 页数由实际内容决定，不能把样刊的五页写成永久常数。发布事务先确认双语 PDF 都已准备好；任何失败都不替换上一期。

## 服务端调度

2026-10-14所有者将12:00方案调整为09:00。北京时区当前执行顺序：07:45 增量采集，08:30 截稿与准备，08:55前完成核验／双语／排版，09:00 发布，09:05 检查公开读取回执。新闻窗口为前日08:30至当日08:30；含周末；不足时不凑新闻，失败不伪装正常出刊。

已实现带 `CRON_SECRET` Bearer 校验的 `/api/cron/daily-journal?phase=tick`，以及 `scripts/maintenance/run_daily_journal.py`。同日同阶段持久锁，已完成阶段不重做，十分钟过期锁可续跑；每阶段自动最多五次，人工从内容管理重试可在排查后继续。失败只记录错误类别，避免公开服务商响应或凭据。已准备的自动稿可恢复 PDF 生成，人工修改或撤回后自动续跑被阻断；自动流程不能更正已发表内容。

生产接入采用支持分钟精度的服务器调度器。每分钟调用 `tick`，07:45 前返回未到期，准备完成后等到09:00发布；迟到时保留实际出刊时间，随后检查。可用服务器任务调用上述 CLI；也可由已有部署平台调用受保护的 HTTP 入口。**本批没有安装本地系统任务、创建 Codex 心跳或改变 Vercel 的既有晨间日程。**

Vercel Hobby 的每日任务不能保证指定分钟；须实际核实套餐与执行预算后才设置 `FIELDTOFIT_DAILY_SCHEDULE_VERIFIED=1`。文档：[Vercel Cron 限制](https://vercel.com/docs/cron-jobs/usage-and-pricing)。未核实前不升级套餐、不承诺已能09:00准点。

环境配置：

| 名称 | 作用 |
| --- | --- |
| `FIELDTOFIT_DAILY_AUTOPUBLISH=1` | 启用已获持续授权的日报流程；默认关闭，其他内容发布规则不变 |
| `FIELDTOFIT_DAILY_SCHEDULE_VERIFIED=1` | 部署方已实际验证分钟调度与预算 |
| `FIELDTOFIT_DAILY_QUOTES_URL` | 已授权、稳定的 JSON 收盘行情适配端点，仅允许公开 HTTPS 地址；不在公开界面展示配置 |
| `FIELDTOFIT_DAILY_SOURCE_MAP` | 可选 JSON 对象，明确将10个新闻维度映射到来源 ID；默认覆盖公司、开源、编程、芯片、具身、基础设施、研究、政策和商业 |
| 既有模型配置 | 复用 `backend.knowledge.models`；生成与独立事实/双语复核分别调用。未配置时失败，不自动跳过核验 |

`backend/daily_briefing/sources.py` 新增17个官方渠道，只有日报增量阶段登记并采集，`daily_enabled=false` 避免挤占既有晨间流程。采集复用原有来源库、真实日期、材料及分页积压记录。自动原文材料当前只提取文本；原图可由管理端随整期导入并核对出处与使用依据，尚未自动选图。注册不等于取材成功；每个维度所有登记渠道都须成功且足够新鲜，失败或未完成分页会延迟整期。部署前须完成新增渠道真实扫描，不能以本地模拟测试代替。覆盖登记不声称穷尽全部产品，Claude Science 等未明确对象不虚构版本。

## 最近完整收盘口径

所有者于2026-10-14确认，美股／A股／港股统一使用各自最近完整交易日收盘。不能将 A/H 盘中价标成当日完整收盘。观察证券15只，Intel使用 `INTC`。每个市场冻结币种、交易日、收市时间、来源及缺值；来源未披露的延迟记 `null`。

行情适配响应为 JSON：

```json
{
  "date": "2026-10-14",
  "cutoff_at": "2026-10-14T08:30:00+08:00",
  "basis": "latest_complete_close",
  "redistribution_authorized": true,
  "calendar_checked": true,
  "sources": [],
  "markets": []
}
```

这里的空数组仅展示外层协议，实际响应会因不完整而被拒绝。`sources`、三个 `markets` 及15行证券的完整字段以 `backend/daily_briefing/schema.py` 为准。适配方负责实际交易日历（休市、半日市、临时停市）、复权口径和涨跌基准，必须完成来源授权核实后才能将上述布尔值置为 true。程序校验日历日期、时区、截稿前完整收盘、币种、有限数值和缺值一致性；不自行猜测上个工作日就是上个交易日。未核实证券的价格、涨跌和时间必须为 `null`，不以旧价填补。

当前没有选定/购买行情供应商，不能将历史样刊的公开行情网站链接视为批量自动分发授权。

## 部署与回滚

按[发布指南](releasing.md)操作；先备份，再执行已有 `init_db()` 的增量建表。六张 `fieldtofit_daily_*` 表独立，不改动现有公开资料、账号或模型数值。PDF 以 base64 与期次修订一起持久保存，适配现有 Turso HTTP 客户端；部署包包含开源 Noto Sans SC 字体和 OFL 许可证，运行时不依赖 macOS 字体。新增 `reportlab` 依赖。

先在预览环境实际跑完采集、行情、两次模型调用、双语PDF、公开回读和跨日重试，确认服务时限/体积/配额后再启用生产。回滚时先关闭 `FIELDTOFIT_DAILY_AUTOPUBLISH` 和外部日报任务，再回退程序；保留新增表和历史记录。原公开 API 不变。

验收依据：[本地开发验证](../validation/2026-10-14-daily-journal.md)。历史10月13日晚间样刊保留真实21:55截稿，不倒填为09:00出刊，不冒充10月14日新闻。上线后仍须连续三个真实自然日验证。
