# 模型图表与来源维护

v1.0.2 · 2026-09-11。仅 Artificial Analysis / Arena，移除 Epoch。保留各自坐标定义，不统一评分。快照：`backend/knowledge/content/model-landscape.json`；HTTP：`/api/v1/platform/model-landscape`。当前 12 项精选 MCP 工具保持原有范围。

| 来源 | 坐标 | 已读取 / 2026 条目 / 可绘制 / 缺坐标 / 日期待确认 |
| --- | --- | --- |
| [Artificial Analysis](https://artificialanalysis.ai/leaderboards/models) | Intelligence Index v4.3 × 每项评测任务加权美元成本 | 646 / 263 / 107 / 156 / 0 |
| [Arena](https://arena.ai/leaderboard/text) | Text Overall（Style Control=true）偏好评分及来源区间 × 每百万输出 token 美元单价 | 400 / 96 / 83 / 13 / 182 |

## 范围与真实性

- 范围为这两个来源已收录、日期有依据且属于 2026 年的模型 / 配置，并非整个行业所有模型。AA 383 个、Arena 122 个已确认其他年份的条目不进入今年图；Arena 182 个日期待确认条目留清单，不暗示它们全部属于今年。
- AA 名称取来源 `shortName`；Arena 取 `modelDisplayName`，不翻译或自行缩写。保留原始机构，映射公司图例：SpaceXAI → xAI、Moonshot → Kimi、Z AI → GLM、Alibaba → Qwen、Xiaomi → MIMO，其余未列机构归其他。
- 12 组颜色在两图一致。每点直接标名，名称避让使用引线；不抖动真实坐标、不画趋势线。筛选公司或名称不改变坐标范围；手机可以放大和双向滚动。
- 分数、价格来自同一来源。AA 使用 `intelligenceIndexCostPerTask.cost.total`，不用 token 单价替代。Arena 只用来源输出单价，不从 AA 拼接价格；保留完整原始评分与区间，显示时四位以内小数。
- 缺评分、缺价格、非正价格无法定位到对数坐标时，保留在缺项表。来源标记的 deprecated 仍可入图（用户要求今年全部版本），表格注明旧版本；若来源有估计分则空心点及表格注明。
- AA 使用来源 `releaseDate`。Arena 榜单不含日期，独立维护 `model-landscape-arena-dates.json`：匹配明确的同模型发布记录、官方公告或带完整年份的版本日期。日期只用于年份筛选，不从其他评测复制分数；不把推理配置的模型发布日期声称为该配置首次实测日期。无法确定同一版本时保留 unknown。
- AA 整体数据更新日未给出，保留 null；Arena 采用来源投票截止日 2026-09-02。本站核验 2026-09-11 与以上日期分开。来源页面 SHA-256 保留用于复核。

## 维护流程

1. 获取上述两个公开网页并保存到本地临时文件。仅抽取必需事实、名称、配置和出处；不复制原文文章、图片或免费 API 的受限数据产品。图表内外署名，参见 [AA 引用说明](https://artificialanalysis.ai/brand-kit)。
2. 核对 Arena 日期证据清单；同名不同版本、preview/instant 等不能模糊合并。清单记录原始模型 ID、日期、出处和依据类型，未确认项不自动补年份。
3. 运行候选生成器：

```bash
.venv/bin/python scripts/maintenance/prepare_model_landscape.py \
  --aa-html /tmp/aa.html --arena-html /tmp/arena.html \
  --checked-at 2026-09-11 --output /tmp/model-landscape-candidate.json
```

4. 工具读取公开网页的内嵌数据，识别模型及选定榜单；格式变化报错停止。它不联网、不调用模型、不写生产库、不覆盖发布文件。核对候选 diff、覆盖数量、日期、价格口径与缺项，再将确认的候选替换快照。
5. 更新 revision、checked_at、版本 z、CHANGELOG/REQ/发布说明，完成校验、浏览器验收再部署。没有数据变更不生成空版本。

现有 Vercel `/api/cron/platform` 每 1 天调用 `model_landscape.check_sources`，现在只检查上述两个榜单，不随数百个模型扩展请求。GET 不带凭据、不跟随重定向，限制大小/超时；结果与指纹写入现有 `knowledge_workflow_runs`（model_landscape_daily）。可用不等于值已更新，也不等于已经核对了每个日期链接。失败保留既有快照。

[本版验收](../validation/2026-09-11-v1.0.2.md)。继续补日期依据与来源缺项；连续真实日维护和自动发布完整榜单尚未验收。
