"""Reading labels for existing reviewed profiles; no new publication or heat claims.

Chinese/English pairs are projected through the existing locale catalog. Events
refer to public D- records or to specific already-reviewed dossier updates.
"""

PROFILES = {
    'CW-M01': ('OpenAI', 'general', '-', ['D-113', 'D-91', 'D-88', 'D-87', 'D-86', 'D-81', 'D-80', 'D-77', 'D-78', 'D-53', 'D-30', 'D-17', 'D-13', 'D-12', 'D-02']),
    'CW-M02': ('Anthropic', 'general', '-', ['D-102', 'D-92', 'D-83', 'D-49', 'D-29', 'D-14', 'D-05']),
    'CW-M03': ('Google', 'general', '-', ['D-100', 'D-58', 'D-39', 'D-42', 'D-34', 'D-16', 'D-04']),
    'CW-M04': ('Moonshot AI', 'general', '-', ['D-20']),
    'CW-M05': ('Z.ai', 'general', '-', ['D-01']),
    'CW-M06': ('DeepSeek', 'general', '-', ['D-90', 'D-10', 'D-07']),
    'CW-M07': ('Alibaba', 'general', '-', ['D-23', 'D-24', 'D-19', 'D-06']),
    'CW-M08': ('MiniMax', 'general', '-', ['D-08']),
    'CW-M09': ('ByteDance', 'general', '-', ['D-09']),
    'CW-M10': ('Nandha Kishor', 'decision', ('分类、评分与概率', 'Classification, scoring and probabilities'), []),
    'CW-M11': ('NVIDIA', 'tabular', ('表格分类与回归', 'Tabular classification and regression'), ['D-57']),
    'CW-M12': ('Cloudflare', 'decision', ('分类、路由与图像判断', 'Classification, routing and image decisions'), ['D-60']),
    'CW-M13': ('Ai2', 'research', ('带引用的论文报告', 'Cited research reports'), ['D-67']),
    'CW-M14': ('Aleph Alpha', 'general', '-', ['D-69']),
    'CW-M15': ('Cactus Compute', 'speech', ('CPU 端侧语音识别', 'On-device CPU speech recognition'), []),
    'CW-T01': ('Comfy Org', 'creative', ('节点式媒体工作流', 'Node-based media workflows'), []),
    'CW-T02': ('Ollama', 'inference', ('本地运行与调用模型', 'Run and call local models'), []),
    'CW-T03': ('vLLM', 'inference', ('部署模型推理服务', 'Serve model inference'), []),
    'CW-T04': ('Docling', 'data', ('解析文档、保留结构', 'Parse documents with structure'), []),
    'CW-T05': ('Google', 'integration', ('Android 设备测试', 'Android device testing'), []),
    'CW-T06': ('-', 'inference', ('本地运行决策模型', 'Run decision models locally'), []),
    'CW-T07': ('devdotfast', 'creative', ('用图示审阅代码', 'Review code through diagrams'), []),
    'CW-T08': ('Hugging Face', 'data', ('检索仓库讨论与决定', 'Retrieve repository discussions and decisions'), []),
    'CW-T09': ('Cloudflare', 'integration', ('为 Agent 提供浏览器', 'Browser access for agents'), []),
    'CW-T10': ('Google', 'data', ('连接云数据工作流', 'Connect cloud data workflows'), ['D-62']),
    'CW-T11': ('Ai2', 'training', ('训练大规模 MoE', 'Train large MoE models'), ['D-63']),
    'CW-T12': ('Meta', 'integration', ('连接自制硬件与 Muse', 'Connect custom hardware to Muse'), ['D-65']),
    'CW-T13': ('CopilotKit', 'integration', ('同步 Agent 与界面状态', 'Sync agent and interface state'), ['D-72']),
    'CW-T14': ('Niko1221', 'inference', ('消费级显卡推理', 'Inference on consumer GPUs'), ['D-74']),
    'CW-T15': ('Cloudflare', 'data', ('切换网页搜索来源', 'Switch web search providers'), ['D-76']),
    'CW-T17': ('TerseAI', 'integration', ('共享会话与持久状态', 'Shared sessions and persistent state'), []),
    'CW-T16': ('-', 'integration', ('本地逆向分析与 MCP', 'Local reverse engineering through MCP'), []),
    'CW-A01': ('OpenAI', 'coding', ('代码修改、审阅与验证', 'Edit, review and verify code'), ['D-108', 'D-107', 'D-105', 'D-99', 'D-98', 'D-96', 'D-95', 'D-94', 'D-84', 'D-79', 'D-55', 'D-03']),
    'CW-A02': ('Anthropic', 'coding', ('终端内持续开发', 'Develop in the terminal'), ['D-111']),
    'CW-A03': ('Google', 'coding', ('终端工具与扩展执行', 'Run terminal tools and extensions'), []),
    'CW-A04': ('OpenHands', 'coding', ('多 Agent 开发控制台', 'Multi-agent development console'), []),
    'CW-A05': ('Browser Use', 'browser', ('网页观察与交互', 'Observe and interact with web pages'), []),
    'CW-A06': ('OpenClaw', 'assistant', ('连接消息、工具与技能', 'Connect messaging, tools and skills'), []),
    'CW-A07': ('earendil-works', 'coding', ('可扩展的编程执行', 'Extensible coding execution'), ['D-59']),
    'CW-A09': ('nano-muse', 'assistant', ('跨设备个人任务与模型接入', 'Personal tasks and model connections across devices'), []),
    'CW-A08': ('Nous Research', 'assistant', ('跨会话记忆与任务执行', 'Cross-session memory and tasks'), []),
    'CW-S01': ('Jesse Vincent / obra', 'devskills', ('从需求澄清到验收', 'From requirements to verification'), []),
    'CW-S02': ('Anthropic', 'docs', ('文档处理与技能制作', 'Document work and skill creation'), []),
    'CW-S03': ('Vercel', 'devskills', ('前端性能与界面检查', 'Frontend performance and UI checks'), []),
    'CW-S04': ('Addy Osmani', 'devskills', ('需求、测试与代码审阅', 'Requirements, tests and code review'), []),
    'CW-S05': ('Cathryn Lavery', 'docs', ('技术图示与可编辑出图', 'Editable technical diagrams'), []),
    'CW-H01': ('DeepSeek', 'orchestration', ('插件化组织执行', 'Compose execution with plugins'), []),
    'CW-H02': ('LangChain', 'orchestration', ('规划、文件与子 Agent', 'Planning, files and subagents'), []),
    'CW-H03': ('Anthropic', 'orchestration', ('复用工具循环与上下文', 'Reuse tool loops and context'), []),
    'CW-H04': ('OpenHands', 'orchestration', ('软件任务执行与工作区', 'Software task execution and workspaces'), []),
    'CW-H05': ('Strands Agents', 'orchestration', ('默认工具、缓存与会话', 'Default tools, caching and sessions'), ['D-37']),
    'CW-H06': ('Parcha', 'orchestration', ('确定流程与 Agent 调查', 'Defined workflows and agent investigation'), []),
    'CW-H07': ('BootLoops', 'research', ('科研计算与结果验证', 'Scientific computation and validation'), ['D-71']),
}

CATEGORIES = {
    'general': ('通用模型', 'General model'), 'decision': ('决策模型', 'Decision model'),
    'tabular': ('表格模型', 'Tabular model'), 'research': ('科研任务', 'Research'), 'speech': ('语音识别', 'Speech recognition'),
    'creative': ('生成与编辑', 'Creation and editing'), 'inference': ('推理部署', 'Inference'),
    'data': ('检索与数据', 'Search and data'), 'integration': ('开发集成', 'Integration'),
    'training': ('模型训练', 'Model training'), 'coding': ('编程', 'Coding'),
    'browser': ('浏览器操作', 'Browser operation'), 'assistant': ('个人助手', 'Personal assistant'),
    'devskills': ('开发协作', 'Development'), 'docs': ('文档与设计', 'Documents and design'),
    'orchestration': ('执行编排', 'Orchestration'),
}

# Date kind is explicit: release, source update, commit or dossier review.
# These are condensed references to the existing watch blocks, never invented releases.
UPDATES = {
    'CW-M15': ('2026-10-02', 'source', ('Whistle：16.9MB CPU 语音识别模型', 'Whistle: a 16.9MB CPU speech recognition model'), 'https://cactuscompute.com/blog/whistle'),
    'CW-T01': ('2026-10-05', 'source', ('v0.39.0：离线开关与 FLUX 3 Image 节点', 'v0.39.0: offline controls and FLUX 3 Image nodes'), 'https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.39.0'),
    'CW-T02': ('2026-10-06', 'source', ('v0.40.0：Apple Silicon 默认 MLX', 'v0.40.0: default MLX on Apple Silicon'), 'https://github.com/ollama/ollama/releases/tag/v0.40.0'),
    'CW-T03': ('2026-10-06', 'source', ('v0.31.0：权重缓存与配置迁移', 'v0.31.0: weight caching and configuration migration'), 'https://github.com/vllm-project/vllm/releases/tag/v0.31.0'),
    'CW-T04': ('2026-09-04', 'release', ('v2.126.0：原生 PDF 管线与格式保留', 'v2.126.0: native PDF pipeline and format preservation'), 'https://github.com/docling-project/docling/releases'),
    'CW-T05': ('2026-09-12', 'commit', ('固定 Android MCP 测试与回放材料', 'Pinned Android MCP testing and replay materials'), 'https://github.com/google/artemis/blob/371aa6df56880643da57b30da936e9812fb0ec66/README.md'),
    'CW-T09': ('2026-09-28', 'release', ('加入 WebMCP、Quick Actions 与终端渲染', 'WebMCP, Quick Actions and terminal rendering'), 'https://blog.cloudflare.com/kitesurf-update/'),
    'CW-A03': ('2026-09-08', 'release', ('v0.59.0：MCP OAuth 与工作区信任修复', 'v0.59.0: MCP OAuth and workspace trust fixes'), 'https://github.com/google-gemini/gemini-cli/releases/tag/v0.59.0'),
    'CW-A05': ('2026-09-04', 'release', ('0.13.10：浏览器依赖与 MCP 错误处理', '0.13.10: browser dependencies and MCP errors'), 'https://github.com/browser-use/browser-use/releases'),
    'CW-A06': ('2026-09-19', 'release', ('v2026.9.5：插件重载无需重启 Gateway', 'v2026.9.5: reload plugins without restarting Gateway'), 'https://github.com/openclaw/openclaw/releases'),
    'CW-A08': ('2026-09-14', 'release', ('v0.21.3：修复并发登录与数据库句柄', 'v0.21.3: concurrent login and database handle fixes'), 'https://github.com/NousResearch/hermes-agent/releases/tag/v2026.9.14'),
    'CW-S04': ('2026-10-03', 'source', ('0.6.12：修正规范批准步骤与命令示例', '0.6.12: specification approval and command example fixes'), 'https://github.com/addyosmani/agent-skills/releases/tag/0.6.12'),
    'CW-H01': ('2026-10-03', 'source', ('v0.2.1-alpha.1：创造模式与 Mods 兼容层', 'v0.2.1-alpha.1: creation mode and Mods compatibility'), 'https://github.com/deepseek-ai/deepseek-harness/releases/tag/dsh-v0.2.1-alpha.1'),
    'CW-H02': ('2026-10-05', 'source', ('SDK 0.7.22：读取 Skill 后再加载工具', 'SDK 0.7.22: load tools when a Skill is read'), 'https://github.com/langchain-ai/deepagents/releases/tag/deepagents==0.7.22'),
    'CW-H06': ('2026-09-24', 'release', ('beta.4：固定流程、分支与有界循环', 'beta.4: defined workflows, branches and bounded loops'), 'https://github.com/Parcha-ai/agentrun'),
}

# Where no release date has been reviewed, show the actual dossier record date.
# A review snapshot is never relabelled as a launch or a fresh upstream event.
SNAPSHOTS = {
    'CW-T16': ('本地 MCP 逆向分析与配套技能', 'Local MCP reverse engineering and companion skills'),
    'CW-M10': ('开放权重与结构化决策 SDK', 'Open weights and structured decision SDK'),
    'CW-T06': ('本地决策模型与 TypeSafe 兼容接口', 'Local decision models and TypeSafe-compatible interface'),
    'CW-T07': ('代码画布、语义差异与分享边界', 'Code canvas, semantic diffs and sharing boundaries'),
    'CW-T08': ('relore 0.3.17：仓库记忆与历史决定', 'relore 0.3.17: repository memory and past decisions'),
    'CW-A04': ('Agent Canvas 与自动化组件职责', 'Agent Canvas and automation responsibilities'),
    'CW-S01': ('开发流程技能与多宿主接入', 'Development workflow skills and host integration'),
    'CW-S02': ('技能制作、文档技能与许可边界', 'Skill creation, document skills and licensing'),
    'CW-S03': ('React、界面检查与部署后优化技能', 'React, UI review and post-deployment optimization skills'),
    'CW-S05': ('固定 v2.6.27 图示技能与导出说明', 'Pinned v2.6.27 diagram skill and export guide'),
    'CW-H03': ('Agent SDK 工具循环与托管产品的区别', 'Agent SDK tool loops and managed product boundaries'),
    'CW-H04': ('SDK、Agent Server 与 Canvas 的职责', 'SDK, Agent Server and Canvas responsibilities'),
}

# Historical launch API prices, USD per million input/output tokens.
# None means that no launch price was established in the reviewed material.
MILESTONES = {
    'CW-M01': [
        ('D-02', 'GPT-6 Astra', None, ''),
        ('D-12', '', None, ''), ('D-17', '', None, ''),
        ('D-30', 'GPT-6 Sol', '2 / 10', ''),
        ('D-30', 'GPT-6 Luna', '0.10 / 0.50', ''),
        ('D-53', 'GPT-6.1 Sol', '2 / 10', ('输入 ≤272K', 'Input ≤272K')),
        ('D-54', '', None, ''), ('D-91', '', None, ''),
    ],
    'CW-M02': [
        ('D-05', 'Claude Fable 5.1', None, ''), ('D-14', '', None, ''),
        ('D-29', 'Claude Opus 5.5', '4 / 20', ''),
        ('D-49', 'Claude Sonnet 5.5', '2 / 10', ''),
        ('D-83', '', None, ''),
        ('D-92', 'Claude Haiku 5.5', '0.10 / 0.50', ('输入 ≤100K；>100K：$0.50 / $2.50', 'Input ≤100K; >100K: $0.50 / $2.50')),
    ],
}

PRODUCT_NAMES = {
    'D-12': ('Agents API 开放', 'Agents API opens'),
    'D-17': ('ChatGPT 进入 Word', 'ChatGPT comes to Word'),
    'D-54': ('Dots 常驻 Agent 推出', 'Dots persistent agents launch'),
    'D-91': ('GPT-6 与 Intelligent UI 推出', 'GPT-6 and Intelligent UI launch'),
    'D-14': ('Salesforce 连接 Claude', 'Salesforce connects to Claude'),
    'D-83': ('Claude Cowork 转向云端任务', 'Claude Cowork moves tasks to the cloud'),
}

def translations():
    from backend.knowledge.watch_history import HISTORY
    result = {}
    def visit(value):
        if isinstance(value, tuple) and len(value) == 2 and all(isinstance(v, str) for v in value):
            result[value[0]] = value[1]
        elif isinstance(value, (tuple, list)):
            for v in value: visit(v)
        elif isinstance(value, dict):
            for v in value.values(): visit(v)
    for data in (PROFILES, CATEGORIES, UPDATES, SNAPSHOTS, MILESTONES, PRODUCT_NAMES, HISTORY): visit(data)
    return result
