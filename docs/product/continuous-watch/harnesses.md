# Harness：首批具体内容

[返回首批内容总览](README.md) · CW1 已确认内容稿 · 核验日 2026-09-11

模块引导文案：**看清 Agent 怎样调用工具、保存进度、扩展能力并持续运行。**

本组按运行机制收录 4 项。Pi 同时具有 Harness 属性，关联到[它的主体介绍](agents.md#cw-a07--pi)，不重复计数。LangChain / LangGraph 作为 Deep Agents 的相关框架材料，不把所有框架统一改称 Harness。

## CW-H01 · DeepSeek Harness

**一句话介绍：** 基于 Cordis 插件系统的 Agent 运行项目，模型、工具、会话和执行循环都可通过插件组合。

| 运行循环与扩展 | 状态与恢复 | 使用入口 | 当前阶段 |
| --- | --- | --- | --- |
| 标准、PTC、极简、创造模式；内核管理插件及依赖，具体能力由插件提供 | 仅追加的会话事件流；Trajectory 按来源查看，支持恢复与分叉 | Web 界面与源码；配置层选择插件 | 开发者预览，不标为稳定正式版 |

| 已核实版本 | 发布日期 | 具体变化 |
| --- | --- | --- |
| v0.1.5-rc.2，标签 dsh-v0.1.5-rc.2 | 2026-09-10 | 预发布记录包含反馈体验与文件卡片调整；核心插件机制见项目说明，不冒充此次补丁新增 |

**FieldToFit 解读**

- **连执行循环本身都能替换。** 模型以外的会话、工具和循环也由插件提供，是理解这个项目区别于单个聊天界面的具体入口。
- **同一事件流支撑查看与恢复。** Trajectory 和会话恢复基于相同记录，便于理解一次运行如何被保存、检查和继续。

依据：[官方介绍](https://www.deepseek.com/harness/)、[发布记录](https://github.com/deepseek-ai/deepseek-harness/releases)。关联：[CW-M06 DeepSeek 模型](models.md#cw-m06--deepseek)。模型与 Harness 独立建档，不将开发者预览写成生产验收结果。

## CW-H02 · Deep Agents

**一句话介绍：** LangChain 生态中提供规划、文件操作和子 Agent 等能力的 Agent Harness，支持在现有运行机制上扩展。

| 运行循环与扩展 | 状态与上下文 | 使用入口 | 组件关系 |
| --- | --- | --- | --- |
| 工具、规划、子 Agent 与可扩展中间件 | 文件系统接口与上下文管理；具体持久化跟随后端配置 | 核心 SDK；另有 deepagents-code 编程入口 | 建立在 LangChain / LangGraph 之上，分别保留库与应用版本 |

| 包 / 版本 | 发布日期 | 具体变化 |
| --- | --- | --- |
| deepagents 0.7.13 | 2026-09-02 | SDK 子 Agent 模式由 handoff 更名为 isolated |
| deepagents-code 0.1.68 | 2026-09-10 | 增加 GLM-5.3 型号资料；调整工作区确认后重启与 effort 缓存标识处理 |

**FieldToFit 解读**

- **核心库与成品入口是两份更新。** 安装核心 SDK 的开发者和使用 deepagents-code 的用户，需要读取不同的版本记录。
- **子 Agent 的模式命名属于调用契约。** handoff 改为 isolated 是使用代码和文档时需要对应的字段变化，值得保留，不扩写成未证实的能力飞跃。

依据：[官方概览](https://docs.langchain.com/oss/python/deepagents/overview)、[核心 0.7.13](https://github.com/langchain-ai/deepagents/releases/tag/deepagents==0.7.13)、[各包发布记录](https://github.com/langchain-ai/deepagents/releases)。关联：[CW-M05 GLM](models.md#cw-m05--glm)。

## CW-H03 · Claude Agent SDK

**一句话介绍：** 将 Claude Code 的工具循环、上下文管理与工具能力提供为 Python / TypeScript 库。

| 运行循环与扩展 | 状态与恢复 | 执行控制 | 使用入口 |
| --- | --- | --- | --- |
| 内置工具、MCP、子 Agent、Skills 与插件 | 多轮会话、恢复与分叉 | 权限配置与生命周期 Hooks | Python / TypeScript，在调用方进程中运行 |

| 本次材料节点 | 日期口径 | 能明确解释的内容 |
| --- | --- | --- |
| 官方 SDK 概览 | 2026-09-11 文档快照；包版本未核 | SDK 提供执行循环；普通 API Client SDK 需要应用自行实现循环；Managed Agents 是独立托管产品 |

**FieldToFit 解读**

- **它提供的是运行过程。** 文件操作、工具调用和上下文管理已在库中组织起来；页面应把这点写清，而不仅标注“支持 Claude”。
- **运行在哪里是关键区别。** Agent SDK 在调用方进程中运行，Managed Agents 由厂商托管；这决定读者应继续查看哪份部署材料。

依据：[官方概览](https://code.claude.com/docs/en/agent-sdk/overview)。关联：[CW-A02 Claude Code](agents.md#cw-a02--claude-code)、[CW-S02 Anthropic Skills](skills.md#cw-s02--anthropic-skills)。本稿未核 SDK 包的当前版本，不把概览中的既有能力写成新发布功能。

## CW-H04 · OpenHands Software Agent SDK

**一句话介绍：** 面向软件任务的 Agent SDK 与服务接口，组织工具、对话、工作区和执行事件。

| 运行循环与扩展 | 状态与上下文 | 执行环境 | 使用入口 |
| --- | --- | --- | --- |
| 命令、文件、浏览器、MCP 与自定义工具 | 持久化、上下文压缩、记忆与事件 | 本地或远程 Agent Server，可配 Docker 等运行环境 | Python / REST API |

| 本次材料节点 | 日期口径 | 能明确解释的内容 |
| --- | --- | --- |
| 官方 SDK 概览与组件职责 | 2026-09-11 文档快照；包版本未核 | SDK / Agent Server 管理执行；Agent Canvas 提供用户界面；Automation 处理调度 |

**FieldToFit 解读**

- **对话与工作区是程序里的明确对象。** 官方文档分别提供工具、事件和工作区接口，适合继续阅读一个软件 Agent 的运行状态如何组织。
- **界面与执行服务可以分开部署。** 这解释了同一个控制台为何能连接不同主机，也让读者知道该去哪个项目查运行问题。

依据：[SDK 官方文档](https://docs.openhands.dev/sdk)、[官方组件职责](https://github.com/OpenHands/OpenHands#repository-boundaries)、[SDK 仓库](https://github.com/OpenHands/software-agent-sdk)。关联：[CW-A04 OpenHands](agents.md#cw-a04--openhands)。
