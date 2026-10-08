# 模型图表与来源维护

仅 Artificial Analysis / Arena，移除 Epoch。保留各自坐标定义，不统一评分。快照：`backend/knowledge/content/model-landscape.json`；HTTP：`/api/v1/platform/model-landscape`。图表由公开 HTTP 读取；既有 MCP 工具范围不变。

v1.8.10新增任意公司多选，具体交互见下节；本地开发和验证状态见[本批验收](../validation/2026-10-08-chart-selection.md)。下方来源覆盖表和旗舰名单说明记录v1.5.14／2026-09-23快照；最新已发布数据为AA161／Arena94，见[2026-10-08内容验收](../validation/2026-10-08-editorial.md)。

## 任意公司多选 · REQ-7-6

- 两来源共用12组公司按钮，包含“其他”。从全部或旗舰模式点击公司进入该公司的完整模型；继续点其他公司累加，点已选公司移除。取消最后一家恢复全部，显式选齐12组也可逐家取消；快速连续键盘操作保留每次选择。
- “全部公司”只清除公司集合，保留当前模型搜索；“各家旗舰模型”清除公司集合和搜索，沿用独立审核名单；“重置筛选”清除公司、搜索和模型详情。改变公司集合清除模型详情，避免展示已被筛除的选中点。
- URL用重复参数保存，例如`?chart=arena&company=OpenAI&company=Anthropic`。写入按固定图例顺序；读取去重并忽略未知公司，有有效公司时优先采用公司集合，没有有效公司但含`flagship`则进入旗舰，其余回退全部。旧`company=OpenAI`、`company=flagship`及`company=all`继续有效；写入保留其他参数和页内位置。
- 切换AA／Arena保留公司集合，刷新及分享网址恢复；模型名称搜索沿用当前页面状态，来源切换后按既有行为清空。搜索在公司集合内匹配；图中点、数值、缺坐标及日期待确认清单采用同一过滤规则。
- 主图和放大窗口共用公司、搜索、重置及当前数量提示；弹窗内调整即时同步主图和表格。选中按钮有勾选、样式及`aria-pressed`状态；原生按钮支持Tab、Enter和空格；关闭／Escape返回放大按钮。
- 坐标域始终取完整来源快照，筛选只控制显示；公司颜色、来源分数／价格、区间、配置、原名和真实日期沿用已审快照。不增加后端筛选接口或数据库字段。

| 来源 | 坐标 | 已读取 / 2026 条目 / 可绘制 / 缺坐标 / 日期待确认 |
| --- | --- | --- |
| [Artificial Analysis](https://artificialanalysis.ai/leaderboards/models) | Intelligence Index v4.3 × 每项评测任务加权美元成本 | 673 / 290 / 133 / 157 / 0 |
| [Arena](https://arena.ai/leaderboard/text) | Text Overall（Style Control=true）偏好评分及来源区间 × 每百万输出 token 美元单价 | 402 / 98 / 84 / 14 / 182 |

## 范围与真实性

- 范围为这两个来源已收录、日期有依据且属于 2026 年的模型 / 配置，并非整个行业所有模型。AA 383 个、Arena 122 个已确认其他年份的条目不进入今年图；Arena 182 个日期待确认条目留清单，不暗示它们全部属于今年。
- AA 名称取来源 `shortName`；Arena 取 `modelDisplayName`，不翻译或自行缩写。保留原始机构，映射公司图例：SpaceXAI → xAI、Moonshot → Kimi、Z AI → GLM、Alibaba → Qwen、Xiaomi → MIMO，其余未列机构归其他。
- 12 组颜色在两图一致。每点直接标名，名称避让使用引线；不抖动真实坐标、不画趋势线。筛选公司或名称不改变坐标范围；手机可以放大和双向滚动。
- 分数、价格来自同一来源。AA 使用 `intelligenceIndexCostPerTask` 数值或旧格式 `.cost.total`，不用 token 单价替代。Arena 只用来源输出单价，不从 AA 拼接价格；保留完整原始评分与区间，显示时四位以内小数。
- 缺评分、缺价格、非正价格无法定位到对数坐标时，保留在缺项表。来源标记的 deprecated 仍可入图（用户要求今年全部版本），表格注明旧版本；若来源有估计分则空心点及表格注明。
- AA 使用来源 `releaseDate`。Arena 榜单不含日期，独立维护 `model-landscape-arena-dates.json`：匹配明确的同模型发布记录、官方公告或带完整年份的版本日期。日期只用于年份筛选，不从其他评测复制分数；不把推理配置的模型发布日期声称为该配置首次实测日期。无法确定同一版本时保留 unknown。
- AA 整体数据更新日未给出，保留 null；Arena 采用来源投票截止日 2026-09-13。本站核验 2026-09-23 与以上日期分开。来源页面 SHA-256 保留用于复核。

## 维护流程

1. 获取上述两个公开网页并保存到本地临时文件。仅抽取必需事实、名称、配置和出处；不复制原文文章、图片或免费 API 的受限数据产品。图表内外署名，参见 [AA 引用说明](https://artificialanalysis.ai/brand-kit)。
2. 核对 Arena 日期证据清单；同名不同版本、preview/instant 等不能模糊合并。清单记录原始模型 ID、日期、出处和依据类型，未确认项不自动补年份。
3. 运行候选生成器：

```bash
.venv/bin/python scripts/maintenance/prepare_model_landscape.py \
  --aa-html /tmp/aa.html --arena-html /tmp/arena.html \
  --checked-at 2026-09-23 --output /tmp/model-landscape-candidate.json
```

4. 工具读取公开网页的内嵌数据，识别模型及选定榜单；格式变化报错停止。它不联网、不调用模型、不写生产库、不覆盖发布文件。核对候选 diff、覆盖数量、日期、价格口径与缺项，再将确认的候选替换快照。
5. 更新 revision、checked_at、版本 z、CHANGELOG/REQ/发布说明，完成校验、浏览器验收再部署。没有数据变更不生成空版本。

现有 Vercel `/api/cron/platform` 每 1 天调用 `model_landscape.check_sources`，现在只检查上述两个榜单，不随数百个模型扩展请求。GET 不带凭据、不跟随重定向，限制大小/超时；结果与指纹写入现有 `knowledge_workflow_runs`（model_landscape_daily）。可用不等于值已更新，也不等于已经核对了每个日期链接。失败保留既有快照。

[本批验收](../validation/2026-09-23-editorial.md)。继续补日期依据与来源缺项；连续真实日维护和自动发布完整榜单尚未验收。

## 各家旗舰模型 · REQ-7-5

独立文件 `model-landscape-flagships.json` 维护本期旗舰名单、核验日期、系列依据及两个来源的精确 ID。每家选一个代表配置，不以最高分/最高价格算法自动贴旗舰标签。OpenAI GPT-6 Astra、Anthropic Claude Opus 5.5、Google Gemini 3.1 Pro、xAI Grok 4.7、Meta Muse Spark 1.3、Kimi K3、GLM-5.3、Qwen3.8 Max、MiMo-V2.6-Pro、MiniMax-M3、DeepSeek V4 Pro 0813。这是 FieldToFit 编辑维护的系列选择，来源负责数值与模型名称，不能称为来源官方旗舰分类。

AA 11 家均可绘制。Arena 的 GPT-6 Astra、Muse Spark 1.3、Kimi K3 缺价格；Opus 5.5、Grok 4.7、MiMo V2.6 Pro 未收录于本次来源快照，故绘制 5 家。面板逐项显示原因，不改用旧系列凑齐。旗舰名单不修改全图的 133 / 84 个点或测量日期；JSON API 附加与网页一致的 flagship 字段。

本次补充三份对应模型日期依据：Arena 新 ID 的 Grok 4.6、GPT-6 Astra max、Muse Spark 1.3 max；后两项仍无输出价格。AA 的 Inkling Small、DeepSeek V4 Flash (high)、MiMo-V2.5、Mercury 2 因最新来源缺任务成本移入缺项表，保留条目，不沿用旧价格。

URL `company=flagship` 保存选择，切换 AA / Arena 保留；选择具体公司转为查看该公司的完整模型，重置恢复全部。图中点、数值和缺项表同时筛选，坐标不变。名单来源用链接核查，更新时间与评分快照时间分开。

维护时先审核系列与精确来源 ID。来源下架或改名导致 ID 不再存在时，校验拒绝旧映射；需一并更新名单，确认来源未收录时显式设为 null。候选生成工具仍只生成测量快照，不能自动替换旗舰系列。
