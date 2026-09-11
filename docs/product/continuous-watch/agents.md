# Agent：首批具体内容

[返回首批内容总览](README.md) · CW1 已确认内容稿 · 核验日 2026-09-11

模块引导文案：**查看能持续执行工作的 Agent，以及围绕它们构建的应用与框架。**

本组包含成品 Agent、浏览器 Agent 库和控制台；每项明确形态，避免把所有项目都叫作同一种框架。

## CW-A01 · Codex

**一句话介绍：** OpenAI 的编程 Agent，围绕项目文件、工具执行和持续任务提供工作入口。

| 具体入口 | 执行与扩展 | 本次展示的材料 | 版本口径 |
| --- | --- | --- | --- |
| Codex 客户端及 CLI / SDK 入口 | 通过工具处理项目任务；程序可接入执行流程 | 官方更新记录中的运行中消息、SDK 与恢复行为 | 客户端、CLI、SDK 和所用模型分别标注 |

| 已核实更新 | 日期 | 具体内容 |
| --- | --- | --- |
| Python SDK 0.154.0 | 2026-09-10 | 分发匹配的 CLI 运行时；支持 ExternalMessage；恢复 / 分叉时 include_turns 控制返回历史，不改变模型实际上下文 |

**FieldToFit 解读**

- **运行中的信息也有来源层级。** ExternalMessage 可以把外部消息送入运行过程，其权限是工具材料级别，不能被当成用户新增授权。
- **恢复记录与模型上下文要分开。** include_turns 改变的是调用方拿到的历史，理解这一点可避免把“返回内容少”误写成“模型忘记了任务”。

依据：[Codex 官方更新记录](https://learn.chatgpt.com/docs/changelog)。关联：D-03 Codex；[CW-M01 GPT](models.md#cw-m01--gpt)。本轮未验证 SDK 集成，不将这条 SDK 版本号套用到桌面应用。

## CW-A02 · Claude Code

**一句话介绍：** Anthropic 的编程 Agent，通过项目上下文、终端工具及插件完成持续开发任务。

| 具体入口 | 执行与扩展 | 本次展示的材料 | 版本口径 |
| --- | --- | --- | --- |
| Claude Code CLI 及相关客户端入口 | 文件、命令、插件、MCP 与会话 | 官方 CHANGELOG 中接口兼容、工具调用、会话和权限修复 | Claude Code 版本，不是 Claude 模型版本 |

| 已核实更新 | 日期口径 | 具体内容 |
| --- | --- | --- |
| 2.1.268 | 2026-09-11 读取到的 CHANGELOG 顶部；未核首发日 | 修复第三方兼容接口的请求失败；修复 MCP 调用后误判空消息；插件管理支持 JSON 输出；修复部分会话恢复和权限规则问题 |

**FieldToFit 解读**

- **连接稳定性值得和新功能一起展示。** 兼容接口请求失败和 MCP 后空消息属于真实使用链路中的问题，本期不将这版泛化为“编程能力增强”。
- **可管理性也在演进。** 插件管理的 JSON 输出让其他程序更容易读取状态，适合作为 Agent 生态连接材料。

依据：[官方 CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)。关联：[CW-M02 Claude](models.md#cw-m02--claude)、[CW-S02 Anthropic Skills](skills.md#cw-s02--anthropic-skills)、[CW-H03 Claude Agent SDK](harnesses.md#cw-h03--claude-agent-sdk)。

## CW-A03 · Gemini CLI

**一句话介绍：** Google 的终端 Agent 项目，通过项目工具和扩展接口连接模型与开发环境。

| 具体入口 | 执行与扩展 | 本次展示的材料 | 版本口径 |
| --- | --- | --- | --- |
| 终端 CLI | 项目上下文、工具、MCP 与扩展 | 稳定发布和预览发布分开读取 | 本稿采用稳定版 v0.59.0；不以 nightly 替代稳定版 |

| 已核实更新 | 发布日期 | 具体内容 |
| --- | --- | --- |
| v0.59.0 | 2026-09-08 | 修复 MCP OAuth 元数据发现相关问题；工作区信任检查改为失败时保持受限，并在受限模式过滤 MCP 配置 |

**FieldToFit 解读**

- **关注它如何处理陌生项目。** 工作区信任检查决定哪些扩展可以进入执行环境，这比只列“支持 MCP”更具体。
- **发布通道本身是重要字段。** 同时存在稳定、预览和 nightly；资料要保留通道，用户和 AI 才能读清变更适用的版本。

依据：[v0.59.0 发布记录](https://github.com/google-gemini/gemini-cli/releases/tag/v0.59.0)。关联：[CW-M03 Gemini](models.md#cw-m03--gemini)、[CW-S01 Superpowers](skills.md#cw-s01--superpowers)。

## CW-A04 · OpenHands

**一句话介绍：** 围绕软件开发 Agent 的开源生态；当前主仓库提供 Agent Canvas，用一个控制台连接本地、远程或云端 Agent。

| 具体入口 | 执行与扩展 | 本次展示的材料 | 版本口径 |
| --- | --- | --- | --- |
| Agent Canvas 控制台；底层 Agent Server | 内置 OpenHands Agent，连接 ACP 兼容 Agent；自动化服务另管定时与事件触发 | 主仓库的组件职责和自部署说明 | 2026-09-11 README 快照；示例镜像为 1.17.0，不据此认定所有组件同版 |

| 组件 | 当前明确承担的工作 |
| --- | --- |
| OpenHands / Agent Canvas | 用户界面、选择运行后端、本地组件启动 |
| Software Agent SDK / Agent Server | Agent、工具、对话、工作区、事件与服务接口 |
| Automation | 调度、Webhook、执行历史与任务分发 |

**FieldToFit 解读**

- **当前主仓库的重点已是多 Agent 控制台。** 它可连接不同 Agent 后端，应展示这个现状，而不是沿用早期单一自主编程工具的介绍。
- **运行位置和触发方式可以分别配置。** Canvas 连接不同后端，自动化服务决定何时启动工作；这两份材料能解释它如何持续运行。

依据：[OpenHands 当前 README](https://github.com/OpenHands/OpenHands)。关联：[CW-H04 OpenHands SDK](harnesses.md#cw-h04--openhands-software-agent-sdk)。本条按生态主体计一项，SDK 单独解释运行机制，不重复全文。

## CW-A05 · Browser Use

**一句话介绍：** 让 Agent 操作浏览器的开源项目，把网页观察与交互接入模型执行过程。

| 具体入口 | 执行与扩展 | 本次展示的材料 | 版本口径 |
| --- | --- | --- | --- |
| Python Agent 库与浏览器集成 | 网页读取、导航与交互；模型、浏览器运行环境分别配置 | 浏览器组件与 MCP 错误处理 | 开源库版本，独立于商业云服务 |

| 已核实更新 | 发布日期 | 具体内容 |
| --- | --- | --- |
| 0.13.10 | 2026-09-04 | 更新 BrowserHarness 与 MCP SDK 依赖并固定版本；未知 MCP 工具调用明确返回应用错误 |

**FieldToFit 解读**

- **错误是否可见会影响后续动作。** 未知工具返回错误后，上层 Agent 才有机会重试或调整；把失败包装成成功会污染整个执行过程。
- **浏览器 Agent 也依赖底层运行组件。** 发布记录中的 BrowserHarness 版本应保留，不能只记录最外层模型名称。

依据：[官方项目](https://github.com/browser-use/browser-use)、[发布记录](https://github.com/browser-use/browser-use/releases)。

## CW-A06 · OpenClaw

**一句话介绍：** 连接消息入口、模型、工具与技能的个人 AI 助手项目，支持持续维护个人 Agent 的工作环境。

| 具体入口 | 执行与扩展 | 本次展示的材料 | 版本口径 |
| --- | --- | --- | --- |
| 个人助手与 Gateway | 多消息渠道、工具、技能及工作区 | 跨工作区技能、更新预演与缓存复用 | v2026.9.3 为标签；发布页日期是 2026-09-08 |

| 已核实更新 | 发布日期 | 具体内容 |
| --- | --- | --- |
| v2026.9.3 | 2026-09-08 | Skill Workshop 保留跨工作区的 Agent 技能集合；在激活前隔离预演核心与插件更新；复用已有缓存和工作进程 |

**FieldToFit 解读**

- **技能积累可以跨越单个工作区。** Skill Workshop 记录可持续保留的技能集合，这是理解个人 Agent 怎样积累工作方法的具体入口。
- **持续运行需要可控更新。** 激活前预演和缓存复用分别处理更新稳定性与重复启动开销，能看出项目在补哪些运行环节。

依据：[官方项目](https://github.com/openclaw/openclaw)、[发布记录](https://github.com/openclaw/openclaw/releases)。与 Skill 模块相互关联，但不把 OpenClaw 项目整体归成一个 Skill。

## CW-A07 · Pi

**一句话介绍：** 可扩展的编程 Agent 工具包，同时提供终端入口、Agent 核心与模型调用组件。

| 具体入口 | 执行与扩展 | 本次展示的材料 | 版本口径 |
| --- | --- | --- | --- |
| 编程 CLI、SDK 与扩展 | 工具循环、状态、扩展包与多模型接口 | 项目分层、扩展机制、SDK 兼容变化 | 当前官方仓库 earendil-works/pi；旧仓库名称作为别名 |

| 已核实更新 | 发布日期 | 具体内容 |
| --- | --- | --- |
| v0.85.1 | 2026-09-05 | 新增模型支持；修复 0.85.0 中 SDK 导入意外加载实验模块的问题；现有 SDK / stdio RPC 接口保持兼容 |

**FieldToFit 解读**

- **既能直接用，也能读它的 Agent 核心。** 终端入口与底层工具包分层，是 Pi 同时出现在 Agent 与 Harness 讨论中的原因；网站保留一个主体、多个关系。
- **SDK 导入修复会影响嵌入式使用。** 已有应用加载 Pi 时是否意外带入实验代码，是比笼统“修复若干问题”更有用的版本信息。

依据：[官方项目](https://github.com/earendil-works/pi)、[发布记录](https://github.com/earendil-works/pi/releases)。关联：[CW-S01 Superpowers](skills.md#cw-s01--superpowers) 的 Pi 适配。运行权限继承宿主进程，项目自述没有内置权限系统；本稿未实测隔离配置。
