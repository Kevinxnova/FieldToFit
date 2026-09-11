# Skill：首批具体内容

[返回首批内容总览](README.md) · CW1 已确认内容稿 · 核验日 2026-09-11

模块引导文案：**关注被大量收藏的技能项目，展开看它们具体教会 Agent 什么。**

首批按仓库收录 3 项，展开代表技能。选择依据是已核对的仓库关注度和可读的具体技能材料；不是“全 GitHub 前三”，也不声称代表技能各自获得这些 Star。

## 首屏关注度表

| 跟踪主体 | 类型 | GitHub 页面 Star 近似值 | 快照日期 | 先展开哪些内容 |
| --- | --- | --- | --- | --- |
| [Superpowers](https://github.com/obra/superpowers) | 技能组合与开发流程 | 284.8k | 2026-09-11 | 需求澄清、计划、调试、完成前验证 |
| [Anthropic Skills](https://github.com/anthropics/skills) | 官方技能集合 | 175.6k | 2026-09-11 | 技能制作与文档处理示例 |
| [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills) | 官方工程技能集合 | 31.0k | 2026-09-11 | React 性能、界面检查、部署后优化 |

数据来源为本次检索到的 GitHub 页面显示值，非实时精确 API 计数。当前没有连续快照，不展示近 7 天增长；没有经过核对的讨论量，不写“讨论最多”。Star 表达收藏关注，不代表采用人数、效果或安全审计。

## CW-S01 · Superpowers

**一句话介绍：** 将需求澄清、计划、测试、调试与验收组织成一套编程 Agent 工作流程。

| 代表技能 | 具体做什么 | 在页面上解释的价值 |
| --- | --- | --- |
| brainstorming | 在实现前澄清目标、展开方案并形成设计 | 展示需求如何进入后续执行流程 |
| writing-plans | 把确认后的设计拆成可执行任务，包含文件与验证信息 | 看计划是否能交给 Agent 逐项执行 |
| systematic-debugging | 按阶段调查根因 | 展示调试步骤，不把反复改代码当作完整方法 |
| verification-before-completion | 在宣布完成前核对验证证据 | 将“Agent 说完成了”与实际验证连接起来 |

**FieldToFit 解读**

- **关注技能之间怎样衔接。** 它的主体是一整套开发流程；只摘出一条提示词会漏掉设计、执行与验证的连接关系。
- **宿主适配是实际内容的一部分。** 官方 README 分别列出多种 Agent 入口和 Pi 扩展；具体加载方式跟随宿主，不写“一次安装 everywhere”。

版本记录：当前 README 与技能目录快照，尚未固定 commit；后续更新记录技能触发条件、步骤及宿主适配的变化。项目为 MIT；本轮未安装或运行这些技能。

依据：[官方 README 与技能列表](https://github.com/obra/superpowers)。关联：[CW-A07 Pi](agents.md#cw-a07--pi)、[CW-A03 Gemini CLI](agents.md#cw-a03--gemini-cli)。

## CW-S02 · Anthropic Skills

**一句话介绍：** Anthropic 公开的技能集合，展示如何把任务说明、脚本和材料组织成可加载的技能。

| 代表技能 / 材料 | 具体做什么 | 页面应保留的说明 |
| --- | --- | --- |
| skill-creator | 创建与改进技能 | 展示技能本身的制作方法，链接对应目录 |
| pdf | PDF 创建、编辑与处理相关流程 | 提供技能源材料入口；不承诺任意扫描件提取效果 |
| pptx | 幻灯片创建与编辑相关流程 | 说明技能如何连接文档产物与操作流程 |
| docx / xlsx | Word 与表格处理 | 同属文档技能组，在集合内展开 |

**FieldToFit 解读**

- **这里可以读到技能由哪些材料组成。** 独立目录里的说明、脚本和资源，是理解 Skill 如何被 Agent 加载的直接样本。
- **集合内部的许可也有区别。** 官方明确文档技能属于源码可见材料，其他许多技能使用 Apache 2.0；不能给整个集合统一贴上“全部开源可任意复用”。

版本记录：2026-09-11 官方仓库快照；尚未固定 commit。代表技能不是按单项热度排名。内容来自公开示例，不宣称等同于 Claude 产品内部的全部实现。

依据：[官方 README](https://github.com/anthropics/skills)、[技能目录](https://github.com/anthropics/skills/tree/main/skills)。关联：[CW-A02 Claude Code](agents.md#cw-a02--claude-code)、[CW-H03 Claude Agent SDK](harnesses.md#cw-h03--claude-agent-sdk)。

## CW-S03 · Vercel Agent Skills

**一句话介绍：** Vercel 将前端工程和网站运行经验整理成供编程 Agent 使用的技能集合。

| 代表技能 | 具体内容 | 值得读的材料 |
| --- | --- | --- |
| react-best-practices | React / Next.js 性能规则 | 请求瀑布、打包体积、服务端与渲染问题的优先级 |
| web-design-guidelines | 界面实现检查 | 键盘焦点、表单、无障碍、导航状态与性能 |
| vercel-optimize | 部署后成本、性能和可靠性调查 | 先取真实运行指标，再定位对应路由与文件 |
| composition-patterns | React 组件组合 | 复合组件、状态提升与内部组合方式 |

**FieldToFit 解读**

- **规则有明确对象。** React 性能与界面检查各自有规则边界，应该展开代表内容，而不是统一叫作“前端优化神器”。
- **部署后优化从指标出发。** vercel-optimize 先收集运行数据再查代码，这段流程值得阅读；它也意味着实际执行需要对应项目的数据访问条件。

版本记录：2026-09-11 仓库快照；官方 README 介绍了按主分支变化生成不可变发布及单技能产物的机制。正式入库时固定实际 release / commit，集合 Star 与技能修订分别记录。

依据：[官方 README](https://github.com/vercel-labs/agent-skills)。本轮未访问用户的 Vercel 运行数据或安装技能。
