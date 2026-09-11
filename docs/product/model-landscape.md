# 模型图表与来源维护

v1.0.1 · 2026-09-11。页面以三来源标签切换，不统一或归一化分数。快照文件为 backend/knowledge/content/model-landscape.json，HTTP 读取 /api/v1/platform/model-landscape；不新增 MCP 工具。

| 来源 | 首版数值 | 核验和来源 |
| --- | --- | --- |
| Artificial Analysis | 8 点，Intelligence Index v4.3 × 每项评测任务加权美元成本 | [公开榜单](https://artificialanalysis.ai/leaderboards/models)、[方法](https://artificialanalysis.ai/models)、[引用规则](https://artificialanalysis.ai/brand-kit)。保留配置/指数版本/图内署名；没有使用其限制外部分发的免费 API。 |
| Arena | 8 点，Text Overall 偏好评分及来源 ± 区间 × 输出美元/百万 token | [来源榜单](https://arena.ai/leaderboard/text)，页面日期 2026-09-02，本站核验 2026-09-11。gemini-3.8-flash-high 为 Preliminary；不解释为显著胜出。 |
| Epoch AI | 6 点，ECI × 同模型页输出价 | [ECI](https://epoch.ai/eci)、[数据与许可](https://epoch.ai/benchmarks/use-this-data)。各点链接同一模型页，ECI 为跨设置最佳成绩汇总，标明本站配对绘图与口径限制。 |

这是跨厂商/价位/配置的小规模公开事实摘录，不是全榜、榜首推荐或第三方数据镜像。AA 和 Epoch 未给这组摘录提供明确整体更新日，保留 null；不得把本站核验日期或模型发布日期填入源数据更新字段。仅保留事实数值和必要标识，未复制源站文章或完整数据集。Epoch 标注 Creative Commons Attribution，相关外部数据仍遵循各自许可。

## 更新链路

现有 Vercel /api/cron/platform 每 1 天运行，调用 model_landscape.check_sources。仅固定白名单公开 URL，无凭据、不跟随重定向；限制超时/响应大小，失败保留。结果写入现有 knowledge_workflow_runs（model_landscape_daily），包含逐 URL 状态与页面指纹；运营记录不冒充完成数值验证。

维护者可运行 `.venv/bin/python -c 'from backend.knowledge.model_landscape import check_sources; print(check_sources(record=False))'` 做只读检查，不写数据库。自动检查当前只判断可读取及记录内容指纹，不自动抽取/发布评分；动态页面可能返回阻拦页，必须进入人工核验。

收到待复核内容后，本地 GPT/维护者逐点核对模型名、推理设置、评分版本、价格口径及日期；修改快照、更新 revision、checked_at、CHANGELOG 和软件 z 版本；完成验证再部署。没有值得更新的内容，不伪造每日新数据。若要持续自动分发完整第三方数据，需要先单独确认其数据产品授权，本轮不接入。

验收包括单位与日期验证、三标签与 URL、目录、手机与键盘、失败状态、默认解读及 MCP 交接。连续每日成功与完整第三方实时数据自动更新不属于本轮已完成结论。
