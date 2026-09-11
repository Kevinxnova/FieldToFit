# 模型：首批具体内容

[返回首批内容总览](README.md) · CW1 已确认内容稿 · 核验日 2026-09-11

本组展示 9 个模型族。下表的“待核”仅指没有确认首次发布日期；能力事实来自对应官方文档。表中版本为重要节点，非完整历史。所有“解读”均为编辑判断。

## CW-M01 · GPT

**一句话介绍：** OpenAI 的通用模型系列；本期材料重点在工具执行方式和运行中的任务调整。

| 版本 / 分支 | 日期与状态 | 对照关系 | 主要变化或定位 | 获取与使用 | 依据 |
| --- | --- | --- | --- | --- | --- |
| GPT-6 Astra | 首发日待核；当前官方指南已列出 | 在 5.6 已有能力上继续演进 | 支持异步工具调用；通过 WebSocket 在执行中接收方向调整；不支持 none 推理档位 | API 模型标识 gpt-6-astra；具体账户权限另查 | [GPT-6 指南](https://developers.openai.com/api/docs/guides/latest-model) |
| GPT-5.6 Sol | 首发日待核；当前指南分支 | 5.6 系列，gpt-5.6 别名指向 Sol | 系列支持用代码组合工具调用；多 Agent 能力处于 beta | API；固定分支标识可避免把别名误当独立模型 | [GPT-5.6 指南](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6) |
| GPT-5.6 Terra / Luna | 首发日待核；并行分支 | 与 Sol 属于同代不同档位 | 独立模型档位；本稿不据名称推断相同输出质量或性能倍率 | API；分别保留模型标识 | [模型目录](https://developers.openai.com/api/docs/models) |

**FieldToFit 解读**

- **工具等待期间也能推进工作。** Astra 的异步调用允许模型等待工具结果时继续其他推理或工具操作；值得读的是调用过程和结果回收方式，而不只是模型名称。
- **长任务可以中途纠偏。** 执行中调整方向意味着应用需要管理正在运行的工作与新消息；它与“取消后重新问一次”有不同的交互要求。

关联：D-02 GPT-6 Astra；[CW-A01 Codex](agents.md#cw-a01--codex)。模型版本与 Codex 客户端版本分别记录。

## CW-M02 · Claude

**一句话介绍：** Anthropic 的模型系列，Fable、Opus、Sonnet、Haiku 是并行产品线；本稿展开前三条的重要节点。

| 版本 / 分支 | 发布日期 / 状态 | 对照关系 | 主要变化 | 获取与使用 | 依据 |
| --- | --- | --- | --- | --- | --- |
| Fable 5.1 | 2026-09-01；Active | Fable 5 的延续 | 官方强调长程编程与研究；新增逐消息 effort 等 beta 接口；强制工具选择存在不兼容变化 | Claude API；各云入口见官方列表 | [Fable 5.1](https://platform.claude.com/docs/en/models/fable-5-1/overview) |
| Opus 5 | 2026-07-24 | 对照 Opus 4.8 | 默认开启思考；支持对话期间调整工具集合 | Claude API；迁移时核对思考配置 | [Opus 5](https://platform.claude.com/docs/en/models/opus-5/overview) |
| Sonnet 5 | 2026-06-30 | 对照 Sonnet 4.6 | 默认自适应思考；旧手动 extended thinking 配置会返回错误；分词器改变 | Claude API；旧采样参数需要核对 | [Sonnet 5](https://platform.claude.com/docs/en/models/sonnet-5/overview) |

**FieldToFit 解读**

- **模型升级会影响已有调用流程。** Fable 5.1 的强制工具调用、思考块兼容规则值得单独读迁移说明；只换模型名可能使已有工作流报错。
- **把产品线与版本分开看。** Opus 和 Sonnet 有各自升级路线；Fable 的发布不能自动解释成其他产品线停用。

关联：D-05 Fable 5.1；[CW-A02 Claude Code](agents.md#cw-a02--claude-code)、[CW-H03 Claude Agent SDK](harnesses.md#cw-h03--claude-agent-sdk)。[完整型号目录](https://platform.claude.com/docs/en/models/overview)另列 Haiku 4.5；本稿不补未经核对的完整历史。

## CW-M03 · Gemini

**一句话介绍：** Google 的多模态模型系列；这里先展开 Flash 的相邻版本，Pro 作为独立分支关联到官方目录。

| 版本 / 分支 | 日期与状态 | 对照关系 | 材料中能确认的内容 | 获取与使用 | 依据 |
| --- | --- | --- | --- | --- | --- |
| Gemini 3.8 Flash | 页面标示 2026-09 更新；稳定版，首发日未核 | 对照 3.7 Flash | 接受文本、图像、视频、音频和 PDF，输出文本；思考档位 low / medium / high | Gemini API；不把这一文本输出型号称作生图模型 | [3.8 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash) |
| Gemini 3.7 Flash | 页面标示 2026-08 更新；稳定版 | 相邻 Flash 节点 | 同样列出上述输入类型及约 1M 输入上限，保留为对照资料 | Gemini API | [3.7 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.7-flash) |

**FieldToFit 解读**

- **视频理解和视频生成应分开。** 3.8 Flash 可以读取视频，但该型号输出是文本；不能因此把它放进视频生成模型清单。
- **没有新增的参数不写成升级。** 两页列出的输入上限和模态相同，本稿不把“约 1M 上下文”写成 3.8 独有的新能力。

关联：D-04 Gemini 3.8 Flash；[CW-A03 Gemini CLI](agents.md#cw-a03--gemini-cli)。[官方目录](https://ai.google.dev/gemini-api/docs/models)中的 Pro 预览分支不与 Flash 混成时间线。

## CW-M04 · Kimi

**一句话介绍：** Moonshot AI 的模型系列，同时覆盖原生视觉模型与面向编程的专门分支。

| 版本 / 分支 | 日期与状态 | 对照关系 | 主要变化 | 获取与使用 | 依据 |
| --- | --- | --- | --- | --- | --- |
| Kimi K3 | 首发日待核；官方权重与模型卡可见 | 新一代原生视觉模型 | 1M 上下文；采用 Kimi Delta Attention 与 Attention Residuals | 官方权重；按 K3 许可证与模型卡部署说明读取 | [K3 模型卡](https://huggingface.co/moonshotai/Kimi-K3) |
| Kimi K2.7-Code | 首发日待核；官方模型卡可见 | 基于 K2.6 的编程分支 | 官方报告相对 K2.6 减少约 30% 思考 token；上下文 256K | 官方模型材料；结果属于厂商评测 | [K2.7-Code](https://huggingface.co/moonshotai/Kimi-K2.7-Code) |
| Kimi K2.5 | 2026-01-29 是模板修订日，不是模型首发日 | 基于 K2 Base 继续训练 | 原生视觉，提供 instant / thinking 模式；该次修订调整对话模板与媒体标记 | 官方权重与模板 | [K2.5](https://huggingface.co/moonshotai/Kimi-K2.5) |

**FieldToFit 解读**

- **K2.7-Code 的看点是编程分支如何继续训练。** 它基于 K2.6，材料同时给出编程评测与推理 token 变化，可以沿这条关系读，而不是仅按数字排代际。
- **K3 的看点包括结构变化。** KDA 和 AttnRes 是具体研究入口；读者能继续查看注意力与跨层信息传递的实现，而不只看到“更强、更长”。

关联：[CW-T03 vLLM](tools.md#cw-t03--vllm)，其本稿版本记录包含 Kimi K3 支持。

## CW-M05 · GLM

**一句话介绍：** 智谱的模型系列；本稿区分 GLM-5 主线与采用新底座的 Flash 分支。

| 版本 / 分支 | 日期与状态 | 对照关系 | 主要变化 | 获取与使用 | 依据 |
| --- | --- | --- | --- | --- | --- |
| GLM-5.3-Flash | 首发日待核；官方仓库已列出 | 新底座，不能写成 5.3 的蒸馏版 | 线性与稀疏注意力结合，采用 mHC；包含多模态预训练 | 仓库下载表、模型卡及推理说明 | [GLM 官方仓库](https://github.com/zai-org/GLM-5) |
| GLM-5.3 | 首发日待核 | 对照 GLM-5.2 | 官方重点报告编程与网络安全评测提升 | 同仓库版本材料 | [GLM 官方仓库](https://github.com/zai-org/GLM-5) |
| GLM-5.2 | 首发日待核 | 对照 GLM-5.1 | 扩展至 1M 上下文；IndexShare 跨稀疏注意力层共享索引 | 同仓库部署与实现入口 | [GLM 官方仓库](https://github.com/zai-org/GLM-5) |

**FieldToFit 解读**

- **Flash 值得看的是新底座。** 混合注意力与 mHC 是理解它的材料入口；名称中的 Flash 不足以说明它只是主模型的缩小版。
- **长上下文背后还有索引机制。** 5.2 的 IndexShare 说明实现怎样减少重复索引工作，可与其他模型的跨层缓存方案对照阅读。

关联：D-01 GLM-5.3-Flash；[CW-M06 DeepSeek](#cw-m06--deepseek)、[CW-H02 Deep Agents](harnesses.md#cw-h02--deep-agents)。

## CW-M06 · DeepSeek

**一句话介绍：** DeepSeek 的模型系列；本稿重点跟踪 V4 Flash 分支的推理结构与多模态变化。

| 版本 / 分支 | 日期与状态 | 对照关系 | 主要变化 | 获取与使用 | 依据 |
| --- | --- | --- | --- | --- | --- |
| DeepSeek-V4.1-Flash | 首发日待核；官方模型卡可见 | V4 Flash 分支演进 | 图像与文本输入、文本输出，1M 上下文；编码器/解码器分工，共享全局 KV；CSA2 设置 Full / Reindex / Reuse | 官方模型卡与权重材料；本轮未核实对应 API 上架状态 | [V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash) |
| DeepSeek-V4-Flash-0731 | 官方称正式版本；不把 0731 自动当发布日期 | 替代此前 preview | DSpark 结构与推测解码模块；官方报告 Agent 评测改善 | 官方模型卡 | [V4-Flash-0731](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731) |

**FieldToFit 解读**

- **读入材料与逐步生成采用不同分工。** V4.1 的编码/解码结构以及共享 KV，是理解长输入怎样进入生成过程的具体切口。
- **缓存复用细节比一句“节省显存”更有信息。** Full、Reindex、Reuse 区分不同层的工作；材料还区分全局缓存与滑动窗口回放，值得沿这两部分继续读。

关联：D-10 DeepSeek-V4.1-Flash；[CW-H01 DeepSeek Harness](harnesses.md#cw-h01--deepseek-harness)。Harness 是独立软件项目，不是该模型的版本号。

## CW-M07 · Qwen

**一句话介绍：** 阿里 Qwen 的模型系列；本稿同时保留稠密模型与实验性稀疏架构分支。

| 版本 / 分支 | 日期与状态 | 对照关系 | 主要变化 | 获取与使用 | 依据 |
| --- | --- | --- | --- | --- | --- |
| Qwen3.8-Flash-Next | 官方博客 2026-08-26；实验分支 | 预览 Qwen4 架构方向 | Gated DeltaNet 与 QSA microblocks；另包含 Ngram Embedding 和 MTP 组件 | 官方权重；托管 Qwen3.8-Flash 与该检查点分别登记 | [模型卡](https://huggingface.co/Qwen/Qwen3.8-Flash-Next) · [发布博客](https://qwen.ai/blog?id=qwen3.8-flash-next) |
| Qwen3.8-27B | 首发日待核；官方模型卡可见 | 延续 Qwen3.5 架构的稠密分支 | 视觉语言模型；后训练关注编程与 Agent，支持灵活思考配置 | 官方权重；模型卡中的托管状态另行核验 | [27B 模型卡](https://huggingface.co/Qwen/Qwen3.8-27B) |

**FieldToFit 解读**

- **两个 3.8 不是同一种结构的大小版本。** 27B 的稠密路线与 Flash-Next 的实验架构应分别展示；数字和后缀不足以表达这层关系。
- **部署材料需要覆盖额外组件。** Flash-Next 的 Ngram 与 MTP 也属于模型材料，不能只拿活跃参数数值替代完整组成；vLLM 的适配记录提供了继续阅读入口。

关联：D-06 Qwen3.8-Flash-Next；[CW-T03 vLLM](tools.md#cw-t03--vllm)。

## CW-M08 · MiniMax

**一句话介绍：** MiniMax 的模型系列；首批展开通用与 Agent 模型主线，音乐等生成分支后续独立建表。

| 版本 / 分支 | 发布日期 | 对照关系 | 主要变化 | 获取与使用 | 依据 |
| --- | --- | --- | --- | --- | --- |
| MiniMax M3 | 2026-06-01 | M 系列新节点 | MSA 稀疏注意力，1M 上下文；图像、视频理解及桌面操作能力 | 官方文章列出 API / Code / Token Plan；权重下载状态不由文章宣传推定 | [M3 发布](https://www.minimax.io/blog/minimax-m3) |
| MiniMax M2.7 | 2026-03-18 | M 系列此前节点 | Agent 团队、复杂技能和动态工具搜索；软件与办公任务材料 | 官方发布与产品入口 | [M2.7 发布](https://www.minimax.io/news/minimax-m27-en) |

**FieldToFit 解读**

- **M3 可以沿“长输入如何计算”继续读。** MSA 的块级 KV 筛选，是它在长上下文之外值得关注的技术材料。
- **“参与自我改进”要读清发生在哪里。** M2.7 文章描述厂商将模型用于训练实验流程；这不能被简写成用户运行时模型会自动更新自身权重。

关联：D-08 MiniMax Music 3 是另一条产品动态，不混入 M 系列升级序列。

## CW-M09 · Seed / Doubao

**一句话介绍：** 字节 Seed 的模型研究与发布入口；豆包产品名称、模型研究名称和 API 型号分别保留。

| 版本 / 分支 | 日期与状态 | 对照关系 | 主要变化或定位 | 获取与使用 | 依据 |
| --- | --- | --- | --- | --- | --- |
| Seed2.1 Pro / Turbo | 首发日待核；官方称已发布 | Seed2 通用路线后续节点 | 面向 Agent 与编程交付；材料包含长视频理解 | 官方模型页与产品入口；具体 API 名称另核 | [Seed2.1](https://seed.bytedance.com/en/seed2_1) |
| Seed2.0 Pro / Lite / Mini | 已发布；本轮未核完整首发日期 | 同代并行型号 | Pro 强调长任务；Mini 强调吞吐；Lite 的 4 月底更新加入原生音频理解 | 官网模型卡、体验与 API 入口 | [Seed2.0](https://seed.bytedance.com/en/seed2) |
| SeedRealtime | 官方目录已列出；具体开放状态待核 | 独立实时交互方向 | 原生音视频、全双工交互 | 保留研究入口，不填未经确认的调用方式 | [官方模型目录](https://seed.bytedance.com/en/models) |

**FieldToFit 解读**

- **音视频理解与实时交互是两条阅读线。** Seed2.0 Lite 的音频输入升级，与 SeedRealtime 的全双工目标分别展示，读者才能看清材料在讲哪一层能力。
- **产品名称不能代替可调用型号。** “豆包”作为产品入口保留；需要 API 的读者应继续查看具体型号与服务文档，不根据研究名称直接拼接调用参数。

关联：D-09 SeedRealtime；图像与视频生成的 Seedream / Seedance 在官方目录中另列，本期不扩成额外模型族。
