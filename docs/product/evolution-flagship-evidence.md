# 大模型技术演进：旗舰型号与三图证据矩阵

核对日期：2026-10-23（Asia/Shanghai）。这是研究证据附录；范围、交付顺序、验收与实现状态统一见[项目总览 REQ-25-21—26](../../FieldToFit-PM.md#req-25-21)。首轮候选矩阵保留为2026-10-23研究快照；下方「实施复核」说明本批实际纳入与覆盖边界，不代表15家公司当前全部旗舰已核实。

## 实施复核（资料核对2026-10-23，交付2026-10-24）

目录revision 4：105技术节点、47技术关系、25型号／待核条目、27条型号披露。15家公司均有入口或明确缺口，其中12家、15型号有至少一条相关正文支持的披露；模型条目覆盖率与配方完整度分列。旧93节点完整内容、43关系与18题保持。

以下是首轮矩阵之后重新打开相关正文的修正；后文旧候选状态不覆盖这些复核结果。正文已读仅指支持论述的相关章节，不宣称逐页全文审阅。

| 材料 | 相关正文与实际纳入 | 限制 |
| --- | --- | --- |
| [Kimi K3 v2](https://arxiv.org/html/2607.24653v2) | §2.1，KDA／Gated MLA混合结构、通道遗忘与delta递推；从摘要提升为相关正文 | v1为7月27日，v2为8月7日，版本分列 |
| [DeepSeek V4.1 Flash](https://arxiv.org/html/2609.19969v1) | §2.3—2.3.1，CSA-2的Full／Reindex／Reuse与跨层KV、索引复用 | 不能继承给未核实的V4 Pro名称 |
| [ERNIE 5.0](https://arxiv.org/html/2602.04705v1) | §2—2.1，统一多模态next-group-of-tokens目标与共享专家池 | 报告身份明确，最新旗舰身份仍待核 |
| [Mistral Large 4](https://mistral.ai/news/mistral-large-4/) | Reinforcement learning at scale段：SFT＋RL、异步rollout与训练、长轨迹和反馈异质性，建立系统节点 | 更正首轮「后训练细节待公开」的过宽描述；权重计划不写成已开放 |
| [Muse Wonder](https://research.meta.ai/blog/muse-wonder) | Wonder与WonderFull并列，预训练及RL规模扩展明确，独立一般RL节点 | 不直接等同推理专用RL，不继承Llama架构 |
| [Claude Transparency](https://www.anthropic.com/transparency) | Opus 5.5的Model architecture and training methodology段，constitution引导后训练 | 不沿用旧Constitutional AI具体配方；Fable／Mythos仅身份索引状态 |
| [GPT-6 Astra](https://deploymentsafety.openai.com/gpt-6-astra) | §2内部推理与RL，独立「学习到的内部推理」节点；Sol按自身资料对Astra训练类型的说明 | 不与提示式CoT等同，不推断MoE及未披露系统结构 |
| [GLM](https://github.com/zai-org/GLM-5) | 5.3沿5.2base后训练；Flash新base与sparse／linear、mHC分开 | 动态README，未固定提交快照；精确首发日未给则仅标年份 |
| [MiniMax M3](https://www.minimax.io/blog/minimax-m3) | MSA分块筛选及KV外层算子，跨图共享技术身份 | 不继承给M3.1 Flash |
| [Seed2.1](https://seed.bytedance.com/en/seed2_1) | Pro／Turbo身份明确，产品能力和型号卡入口保留 | 型号卡PDF读取失败；无凭据的训练或系统采用线未加入 |
| [Pangu产品说明](https://support.huaweicloud.com/productdesc-pangulm/pangulm_01_0001.html) | 页面10月14日更新，作为待核入口 | 服务介绍不是精确旗舰模型报告，未画采用线 |

新增采用边只指「该型号相关正文披露此技术身份」，不是算法原创、生产框架或全部内部配方的推断。仅一侧披露的比较列不能解释为另一侧未采用。型号日期、技术首发和资料核对日独立维护。网页React、SSR与JSON均由同一目录生成；实现及测试状态只在项目总览记录。

## 证据如何阅读

| 标记 | 实际完成的阅读 | 可支持的结论 |
| --- | --- | --- |
| 正文 | 官网、模型卡或报告相关段落已核对；不等于全文逐页审完 | 仅支持该段明确披露的型号、方法及范围 |
| 摘要 | 原始论文摘要已核对 | 机制候选，细节和消融待正文核对 |
| 入口 | 找到原始论文或官方入口 | 资料存在；不证明型号采用 |
| 失败 | 找到入口但正文提取失败 | 保留缺口，不冒充已读 |
| 待核 | 当前材料不足或存在命名／版本冲突 | 不画采用线；不等于模型没有采用该技术 |

“已定位15家公司”是检索覆盖；“每家当前旗舰已确认”是型号覆盖；“每条采用关系有证据”是关系完备度，三者不混算。闭源资料缺失、全文尚未读取、当前旗舰身份未确定也分别记录。以下“未取得”只描述本次材料池，不声称厂商从未披露。

## 型号 × 训练／推理／系统

训练侧登记能力形成涉及的架构、目标、数据与优化；推理侧登记求解算法与运行行为；系统侧登记计算、存储、通信和调度实现。同一创新可能关联多个图，但不会因此变成三项独立发明。

| 公司 | 精确型号与身份边界 | Train候选 | Inference候选 | Systems候选／缺口 | 原始资料及状态 |
| --- | --- | --- | --- | --- | --- |
| OpenAI | GPT-6 Astra与GPT-6.1 Sol分别登记；后者不是仅凭名字推定的蒸馏版 | 推理RL；Sol §2明确引用Astra的数据／训练类型 | 内部思考；具体预算机制另核 | 当前卡片未取得生产并行／缓存实现 | [Astra卡](https://deploymentsafety.openai.com/gpt-6-astra)、[Sol增补](https://deploymentsafety.openai.com/gpt-6-1-sol)：正文 |
| Anthropic | Opus 5.5为已读型号；Fable／Mythos 5.1与Sonnet 5.5另列角色，未完成其独立审阅 | Opus 5.5后训练及原则引导概述；不直接继承旧CAI全流程 | 自适应思考、effort；运行约束见E05 | 无具体服务调度证据；API缓存功能不证明内部实现 | [透明度页](https://www.anthropic.com/transparency)、[Opus文档](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5)：正文；[系统卡索引](https://www.anthropic.com/system-cards)：目录已读、相关PDF失败 |
| Google | Gemini 4 Argon；模型卡称新模型，不能画成旧型号权重微调链 | 稀疏MoE、原生多模态、RL | 推理型号定位已披露；具体预算／搜索流程待核 | TPU、JAX、ML Pathways用于训练有直接证据 | [Argon模型卡](https://deepmind.google/models/model-cards/gemini-4-argon/)：正文 |
| Z.ai／GLM | GLM-5、5.3、5.3-Flash分支登记；5.3沿用5.2底座，Flash为新底座 | 5.3后训练；Flash混合注意力与mHC | GLM-5的MLA／MTP／DSA；5.2索引复用命名待核 | GLM-5异步RL与训练系统；不自动外推5.3 | [GLM-5报告](https://arxiv.org/html/2602.15763v1)、[官方仓库](https://github.com/zai-org/GLM-5)：相关正文 |
| DeepSeek | V4.1-Flash；1017服务更新与基础型号分开 | 具体架构配方需正文定位 | 长程Agent输入负载；具体压缩机制待核 | prefill、KV容量与HBM／SSD带宽瓶颈候选 | [V4.1-Flash报告](https://arxiv.org/abs/2609.19969)：摘要；[官方发布](https://api-docs.deepseek.com/zh-cn/news/news260910/) |
| Moonshot／Kimi | Kimi K3；报告修订不等于新型号发布 | KDA、Attention Residuals、MoE与分域RL候选 | 不同推理努力与Agent求解，待章节定位 | 专家并行、持久rollout／沙箱状态候选 | [K3报告](https://arxiv.org/abs/2607.24653)：摘要；[开放说明](https://www.kimi.com/news/kimi-k3-open-source)：官方正文 |
| Alibaba／Qwen | Qwen3.8-2.4T-A95B为Max级开放权重；Flash-Next单独分支；API版本身份仍需核对 | 开放权重明确Gated DeltaNet／Gated Attention＋MoE及MTP | 思考模式、reasoning_effort、历史思考保留 | 框架启动示例只能证明适配，不能认定厂商生产栈 | [开放模型卡](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B)：正文；[Next报告](https://arxiv.org/abs/2608.30320)：摘要 |
| MiniMax | M3.1 Flash于10月19日官方发布；M3及MaxProof分别登记 | M3的MSA；未取得M3.1 Flash配方 | M3.1 Flash Agent／Computer Use为能力描述；MaxProof为专门证明系统 | M3.1 Flash性能公告不足以确定加速实现 | [M3.1 Flash](https://www.minimax.io/blog/minimax-m31f)、[M3](https://www.minimax.io/blog/minimax-m3)：正文；[MaxProof](https://arxiv.org/abs/2606.13473)：摘要 |
| Meta | Muse Wonder／WonderFull候选；Muse Spark与Llama属于不同历史材料 | Wonder具体训练机制未提取 | 不能从产品演示推定搜索／验证算法 | 未取得型号系统实现 | [Wonder官方说明](https://research.meta.ai/blog/muse-wonder)：正文及报告入口；[Spark报告](https://arxiv.org/abs/2606.12429)：入口 |
| xAI | Grok 4.7为已找到新型号；4.6归历史 | 当前配方未取得 | 官方任务能力说明不等于算法公开 | 不套用Grok 4系统卡 | [4.7发布](https://x.ai/news/grok-4-7)：正文；[型号文档](https://docs.x.ai/developers/models/grok-4.7)：入口 |
| ByteDance／Seed | Seed2.1材料已定位；截至核对日是否仍为最新旗舰待核 | 不把DAPO默认附给Seed全系列 | 型号级求解路线待提取 | 型号级系统路线待提取 | [Seed2.1](https://seed.bytedance.com/en/seed2_1)：官方正文，Model card／Tech blog入口已找到 |
| Mistral | Mistral Large 4；10月6日公告与后续技术披露分开 | 公告将更多架构／后训练细节列为后续公开，当前未核得 | 具体求解机制待补 | 不能从Mixtral继承生产系统实现 | [Large 4官方说明](https://mistral.ai/news/mistral-large-4/)：正文 |
| 百度／ERNIE | ERNIE 5.0已有报告；是否仍为最新旗舰待核，4.5为历史 | 统一多模态next-group-of-tokens目标、超稀疏MoE候选 | 模态统一生成；解码机制待正文 | 系统细节待正文 | [5.0报告](https://arxiv.org/abs/2602.04705)：摘要；[4.5报告](https://ernie.baidu.com/blog/publication/ERNIE_Technical_Report.pdf)：历史入口 |
| 腾讯／Hunyuan | Hy4 Preview，保留预览身份；Hunyuan-A13B为另一条历史资料 | 官方ADP说明明确稀疏MoE | 长上下文、Agent多轮工具能力；具体算法待报告 | ADP集成是平台支持，不等于Hy4训练／服务内部实现 | [Hy4 ADP说明](https://adp.tencent.com/zh/blog/adp-hunyuan-hy4-preview-support)：正文；[研究页](https://hunyuan.tencent.com/research/hy4-preview?langVersion=zh)：读取失败 |
| 华为／Pangu | Pangu Pro MoE历史资料；当前精确旗舰身份仍缺 | 分组专家路线仅作历史候选 | 未取得当前型号求解证据 | Pangu服务与ModelArts平台介绍不能替代型号采用证据 | [Pro MoE论文](https://arxiv.org/abs/2505.21411)：入口；[服务介绍](https://support.huaweicloud.com/productdesc-pangulm/pangulm_01_0001.html)：检索摘要 |

## 可审阅关系清单

以下E编号只属于研究附录，不是正式图谱ID。日期列是**证据日期**，除明确标注发布外，不能用作技术首次出现日期；页面没有可靠日期则保留待核。本表全部核对日期为2026-10-23。正文候选仍需核对既有节点、双语表述与关系端点后才可入正式目录。

| ID | 型号／对象 → 技术及图 | 关系与定位 | 证据日期／阅读 | 允许的解释与边界 |
| --- | --- | --- | --- | --- |
| E01 | GPT-6 Astra → 推理RL（训练） | 采用；[系统卡](https://deploymentsafety.openai.com/gpt-6-astra) §2 Model Data and Training | 卡片2026-09-03；正文 | 支持RL形成推理能力；不支持指定GRPO／PPO或MoE架构 |
| E02 | GPT-6 Astra → 内部思考（推理） | 运行行为；同卡§2 | 同上；正文 | 与训练RL区分；不由“会思考”推定树搜索／多代理 |
| E03 | GPT-6.1 Sol → Astra所述训练类型（训练） | 官方明确关联；[增补](https://deploymentsafety.openai.com/gpt-6-1-sol) §2 | 卡片2026-09-29；正文 | 可沿明确引用追溯数据／训练类型；不表示蒸馏或权重继承 |
| E04 | Claude Opus 5.5 → 原则引导后训练（训练） | 概述；[透明度页](https://www.anthropic.com/transparency)型号训练说明 | 动态页日期待核；正文 | 仅限当前披露层级；旧CAI流程保留历史节点 |
| E05 | Claude Opus 5.5 → 自适应思考／effort（推理） | 运行行为；[型号文档](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5) New model／Breaking changes | 动态页日期待核；正文 | 思考始终开启，effort调节深度；固定budget及关闭思考不再适用 |
| E06 | Gemini 4 Argon → 稀疏MoE与原生多模态（训练） | 组合；[模型卡](https://deepmind.google/models/model-cards/gemini-4-argon/) Architecture | 卡片2026-10-13；正文 | 不将引用文献的每个实现细节自动归给Argon |
| E07 | Gemini 4 Argon → 推理RL（训练） | 采用；同卡Training Dataset | 同上；正文 | 包含多步问题与定理数据；具体优化器未据此确定 |
| E08 | Gemini 4 Argon → TPU／JAX／ML Pathways（系统） | 实际训练使用；同卡Hardware／Software | 同上；正文 | 可连训练实现；不外推推理生产调度 |
| E09 | GLM-5 → MLA／共享参数MTP／DSA（训练、推理） | 组合；[报告v1](https://arxiv.org/html/2602.15763v1) §2.1 | 2026报告v1；正文 | 分别解释结构、训练目标与运行作用；不宣称同属单一发明 |
| E10 | GLM-5 → 内存／并行／量化训练（系统） | 采用；同报告§2.4 | 同上；相关章节 | INT4 QAT与推理时量化区分；细节待逐项摘取 |
| E11 | GLM-5 → 异步RL系统（系统） | 采用；同报告§4 | 同上；相关章节 | 仅绑定GLM-5，不自动延伸5.3 |
| E12 | GLM-5.3 → 5.2底座＋后训练（训练） | 明确底座关系；[官方README](https://github.com/zai-org/GLM-5)型号更新 | README修订日期待固定；正文 | 可表达底座沿用与改进来源；不可虚构新架构 |
| E13 | GLM-5.3-Flash → 混合注意力＋mHC（训练、推理） | 组合；同README Flash说明 | 同上；正文 | 独立新底座分支，不能画成5.3直接缩小版 |
| E14 | GLM-5.2 → 跨层索引复用（推理、系统） | 待核；README链接文字IndexShare，但[目标论文](https://arxiv.org/abs/2603.12201)题名IndexCache | 2026论文；摘要／命名冲突 | 暂不合并技术身份，不进入正式连线 |
| E15 | Qwen3.8-2.4T-A95B → 混合注意力＋MoE／MTP（训练） | 组合；[模型卡](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B) Model Overview | 卡片日期待固定；正文 | 只绑定该开放权重；MTP目标不自动证明线上使用MTP解码 |
| E16 | Qwen3.8-2.4T-A95B → effort／思考保留（推理） | 接口与运行说明；同卡Highlights／API Usage | 同上；正文 | 区分接口说明与权重推理实现；不能套用到Next全系列 |
| E17 | Qwen3.8 Flash-Next → GDN／全局及稀疏注意力、Gated Residual（训练、推理） | 组合候选；[Next报告](https://arxiv.org/abs/2608.30320) Abstract | 2026报告；摘要 | 与Max级开放权重另列分支；n-gram存储的系统作用待正文 |
| E18 | Kimi K3 → KDA／Attention Residuals／MoE／RL（训练） | 组合候选；[K3报告](https://arxiv.org/abs/2607.24653) Abstract | v1 2026-07-27，v2 08-07；摘要 | 不能将报告日期当作各机制首发日期 |
| E19 | Kimi K3 → 专家并行／持久rollout状态（系统） | 系统候选；同报告Abstract | 同上；摘要 | 训练吞吐及环境状态影响需全文条件，未复测 |
| E20 | DeepSeek V4.1-Flash → 长程Agent输入与KV带宽瓶颈（推理、系统） | 问题链候选；[报告](https://arxiv.org/abs/2609.19969) Abstract | 提交2026-09-17；摘要 | 确定待解释瓶颈，具体机制／收益尚不能仅据摘要定稿 |
| E21 | MiniMax M3 → MSA（训练、推理） | 架构说明；[官方文章](https://www.minimax.io/blog/minimax-m3)方法段落 | 发布日期待定位；正文 | 绑定M3，不默认继承给M3.1 Flash |
| E22 | MaxProof → 生成／验证／修复与群体推理扩展（训练、推理） | 研究系统候选；[论文](https://arxiv.org/abs/2606.13473) Abstract | 2026论文；摘要 | 专门证明系统不等于MiniMax通用旗舰生产流程 |
| E23 | ERNIE 5.0 → 统一多模态目标＋超稀疏MoE（训练） | 组合候选；[报告](https://arxiv.org/abs/2602.04705) Abstract | 提交2026-02-04；摘要 | 统一next-group-of-tokens训练；路由／解码细节待正文 |
| E24 | Hy4 Preview → 稀疏MoE（训练） | 采用；[腾讯ADP说明](https://adp.tencent.com/zh/blog/adp-hunyuan-hy4-preview-support)核心参数 | 文章2026-08-28；正文 | 官方平台材料支持架构描述；预览状态保留，不证明内部服务栈 |

## 历史技术锚点与当前型号的区分

下列材料补足“技术何时出现”的索引，不因最新旗舰采用而删除。此处不是重写完整2017—2026时间线；已有93节点保留，新增候选先与其核对。年份表示报告／方法材料年份，不等于本次核对时间。

| 历史材料 | 当前可用状态 | 与旗舰路线的边界 |
| --- | --- | --- |
| [2022 InstructGPT／RLHF](https://arxiv.org/abs/2203.02155) | 检索摘要 | 历史训练转折，不证明GPT-6具体优化器 |
| [2023 GPT-4 Technical Report](https://arxiv.org/abs/2303.08774) | 入口 | 可预测扩展及披露边界，不证明新型号结构 |
| [2024 o1：Learning to reason](https://openai.com/index/learning-to-reason-with-llms/) | 检索摘要 | 推理RL与推理时计算历史锚点；当前型号需独立证据 |
| [2025 o3／o4-mini](https://openai.com/index/introducing-o3-and-o4-mini/) | 入口 | 工具与推理结合历史候选，不推定所有后继型号相同流程 |
| [Constitutional AI原始材料入口](https://www.anthropic.com/news/constitutional-ai-harmlessness-from-ai-feedback) | 入口 | 旧方法与[新constitution](https://www.anthropic.com/news/claude-new-constitution)及当前型号训练披露分别登记 |
| [2024 Gemini 1.5](https://arxiv.org/abs/2403.05530)／[2025 Gemini 2.5](https://arxiv.org/abs/2507.06261) | 前者检索摘要，后者入口 | 长上下文、多模态与推理演进；不画成Argon权重继承 |
| [2025 GLM-4.5 ARC](https://arxiv.org/abs/2508.06471) | 检索摘要 | 与GLM-5及5.3系列分开记录 |
| [Hunyuan-A13B仓库](https://github.com/Tencent-Hunyuan/Hunyuan-A13B)／[报告](https://arxiv.org/abs/2609.27284) | 入口 | 2026报告提交不能冒充模型最初发布；与Hy4 Preview分开 |
| [2025 Pangu Pro MoE](https://arxiv.org/abs/2505.21411) | 入口 | 历史候选，不能代替2026当前盘古旗舰身份 |

## 日期、缺口与结论边界

- OpenAI卡片有明确9月3日／9月29日日期；10月修订由[官方索引](https://deploymentsafety.openai.com/)另追踪，不用首次卡片日期覆盖后续服务变化。Sol与Astra的关联仅到官方明确引用的训练类型层级。
- Anthropic系统卡目录可读，但相关PDF多次未取得正文。Opus 5.5 API文档本轮已由检索片段提升为正文核对；Fable／Mythos身份与技术证据仍需独立材料，不能以Opus替代全部旗舰覆盖。
- Gemini的2026-10-13是已核对模型卡日期；若模型首发日不同，分别保留。TPU／JAX／Pathways是训练使用证据，不是泛泛“Google拥有这些技术”。
- GLM README是动态资料，正式入图前需要固定修订或提交；IndexShare／IndexCache冲突尚未解。新底座、后训练迭代与框架支持必须使用不同关系。
- Qwen已补到Max级开放模型卡，填补上一轮只有Next架构材料的缺口。但开放权重与API型号不能未经核对认作完全同一部署版本。
- MiniMax M3.1 Flash发布日已核到2026-10-19；公告中的速度／价格自报不作为加速机制证据。M3与MaxProof的技术不自动挂到新Flash。
- ERNIE 5.0与Hy4 Preview增加了2026型号材料，但“截至10月23日全部当前旗舰身份已核实”仍不成立。Seed、Pangu及部分公司互补旗舰覆盖尚有缺口。
- 报告摘要的技术细节、消融和性能条件尚未阅读全文核验；本轮没有复现实验。图中未来若展示性能，必须另附硬件、精度、输入输出长度、批量、基线和作者自报属性。

当前成果为15家公司检索矩阵与24条分级候选关系。没有将候选状态升级为网站已实现，也没有据未披露信息补画猜测路线。后续工作顺序及负责人决定只记录在项目总览。
