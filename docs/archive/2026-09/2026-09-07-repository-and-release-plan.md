# FieldToFit 目录、版本记录与 GitHub 展示方案（待对齐）

> 历史快照，不作为当前需求状态或操作说明。现行入口：[需求清单](../../product/requirements.md)、[文档导航](../../README.md)。主案例现为 pending，旧样例通过不代表产品价值已经验证。

日期：2026-09-07。此文件是整理方案，不是已经执行的迁移。用户要求先完成任务资料包，再对齐整理方案；本轮未移动、删除原有文件，未发布新版本。

## 目标与当前问题

让首次访问 GitHub 的人看懂 FieldToFit 能帮助他完成什么；让维护者能找到当前需求、代码入口、部署办法、验证证据与版本变化。

现有目录不大，不需要重新搭建工程结构。主要问题是新旧功能并存、需求和交付分散在按日文档中，以及 README 开头仍描述 v1.0.0 的工具发现与 Newsletter，新的任务工作台和 MCP 介绍放在末尾。根目录已有 CHANGELOG.md，应继续维护这个版本记录入口。

## 建议的目录

```text
fieldtofit/
├── README.md                    中文项目首页：价值、演示、最新变化、快速开始
├── README.en.md                 对应英文版
├── CHANGELOG.md                 唯一完整版本变更记录，保留旧版本
├── ROADMAP.md                   当前重点、下一阶段及明确延后事项
├── CONTRIBUTING.md / SECURITY.md / LICENSE
├── DEPLOY.md                    保留兼容入口，指向具体部署指南
├── requirements.txt / requirements-dev.txt / pyproject.toml
├── Dockerfile / compose.yaml / vercel.json / .github/
├── api/                         部署平台入口，保留路径兼容
├── backend/
│   ├── knowledge/               现行资料、采集、任务和 MCP 业务
│   ├── api/ / db/ / scrapers/    共享 API、数据库和采集能力
│   └── …                       仍在使用的旧流程先标记，分批迁移
├── frontend/src/
│   ├── pages/                   当前工作台页面
│   ├── components/              当前共用组件
│   ├── legacy/                  仍由旧策展入口使用的页面及配套组件
│   └── api/ / hooks/            当前共享代码
├── scripts/                     环境、日常运维与历史补采脚本
├── tests/                       自动化行为检查
├── examples/
│   ├── editorial/               显式导入的短引用与整理样本
│   ├── task_packets/            可拿去运行的任务案例与说明
│   └── validation/              维护者运行案例和 MCP 的入口
├── docs/
│   ├── README.md                文档导航
│   ├── product/                 goals.md、requirements.md、任务验收标准
│   ├── guides/                  本地启动、部署、后台、MCP、资料维护
│   ├── architecture/            当前系统结构、数据流、权限与兼容边界
│   ├── releases/                每个发布版本的重点、截图及升级说明
│   ├── validation/              有日期、环境与边界的真实结果
│   ├── assets/                  当前 README 与版本说明所用截图
│   └── archive/                 旧设计、旧计划、历史交付快照
└── data/                        本地运行数据，继续不进入 Git
```

## 文件处理清单

以下按用途覆盖当前受版本管理的文件；逐文件列表见 [整理前文件盘点](2026-09-07-file-inventory.md)。本机依赖、数据与隐藏配置单独处理。

| 当前文件 / 文件组 | 建议处理 | 理由与验收方式 |
| --- | --- | --- |
| README.md | 重写为中文首页，提炼英文版到 README.en.md | 以当前任务工作台、信息/资源及 MCP 为主；已发布版和开发中版本分开 |
| CHANGELOG.md | 原位维护，补充 Unreleased | 保留 v0.1–v1.0 历史，不另建第二个 changelog |
| CONTRIBUTING.md、SECURITY.md、LICENSE | 保留；只修正失效入口 | GitHub 常规入口继续可见 |
| DEPLOY.md | 保留短导航；详情整理进 docs/guides/ | 旧链接仍可使用；区分本地验收与尚未验收的部署方式 |
| 根 requirements、pyproject、Dockerfile、compose、vercel、.github | 保留固定入口 | 部署平台和工具依赖这些路径；不为外观移动 |
| backend/requirements.txt | 改成引用根依赖清单的兼容入口 | scripts/setup-mac.sh 仍引用它，两份清单已存在差异；避免独立维护 |
| backend/knowledge/* | 原位保留，加架构导航 | 现行核心；任务配方目前只有一个完整案例，先不扩成复杂插件系统 |
| backend/api、db、scrapers、dedup、config、security、scheduler、mcp_stdio | 原位保留 | 共享运行能力与外部入口；拆分另列为需求，不混入文档整理 |
| backend 的 classifier、translate、email、daily_news、ai_recommend、cron_tasks 等 | 标记旧流程并写调用关系，暂保留 | 仍被旧 API 和部署定时入口引用；不能直接删掉 |
| api/* | 保留，说明新旧入口 | vercel.json 仍包含旧定时路由；取消旧任务需明确的兼容迁移方案 |
| 当前前端 App、Explore、Dossier、WorkspacePages、TaskWorkbench、KnowledgeReading、KnowledgeOps、workspace 组件 | 保留当前模块位置 | 当前页面与组件正常工作；不为了整理改业务逻辑 |
| Admin.tsx、ToolFeed/ToolCard/TakeEditor/NewsletterPreview/ScrapeHealth 及相关依赖 | 迁到 frontend/src/legacy/，更新导入 | /admin/curation 仍使用旧策展后台；迁移后保留该路由及行为 |
| Landing、Discover、DailyNews、Community 页面，components/discover/*、theme.ts | 确认无引用后从当前源码移除 | 已通过 main.tsx 的相对静态导入关系检查；再次检查动态引用、构建后删除，Git 保留历史，无需塞进编译目录 |
| frontend/src/api/client.ts、i18n.ts、hooks/useTools.ts | 随旧策展依赖迁移或保留共享位置 | 按实际调用关系处理，不通过文件名判断是否过期 |
| scripts/* | 按 setup / runtime / maintenance 分类并加导航 | 改路径时同步 README、部署入口及脚本内部引用；已有公开启动脚本保留兼容入口 |
| tests/* | 保留，按功能补导航 | 不把验证脚本和自动测试混为一类；迁移只跑必要回归 |
| examples/editorial、task_packets、validation | 保留三类分工，补 examples/README.md | 整理样本、用户可运行案例和维护者验收入口各有目的 |
| docs/product 的多份按日需求/计划/交付 | 当前状态合并到 goals.md、requirements.md；按日快照归档 | requirements.md 以原 REQ ID 为锚点，保留未完成项和证据链接；归档文件标明被谁取代 |
| docs/superpowers/plans、docs/metis_design-v0.1.0、docs/updates | 移到 docs/archive/ 对应旧版本/日期目录 | 旧设计有历史价值，但不再作为当前操作说明 |
| docs/validation/* | 原位保留，增加结果索引 | 运行记录需要日期、环境、版本、范围；后续结果追加，不覆盖历史结果 |
| docs/assets/fieldtofit-homepage.png | 移到历史截图目录，首页换当前真实截图 | README 不展示已经下线的页面作为当前效果 |

## 本机文件：保留配置与数据，清理可再生物

实际发现根目录和 data/ 下各有一个 fieldtofit.db，还有日志、SQLite 辅助文件、.venv、frontend/node_modules、dist、Python/pytest 缓存、.vercel、.gstack、.DS_Store 和空 work/。

- `.git`、`.env`、`.vercel`、`.gstack` 保留；不打印凭证，不提交个人配置，也不把它们和旧源码一起清理。
- 两处数据库先核对配置指向、进程使用和备份恢复办法。确定唯一运行目录后再安排迁移；此轮方案不授权直接删除或覆盖数据库。
- `.venv` 和 `node_modules` 供本地继续开发，保留在原位置并忽略 Git；`dist`、缓存、日志只清理明确可再生或已有备份的部分，不把删除依赖当作目录整理成果。
- `.DS_Store`、空 work/ 可在正式整理时删除；补足忽略规则。日志若仍使用，先归到约定运行目录而非直接清空。

## 版本记录设计

仓库现有本地标签是 v1.0.0，本轮仍在开发分支和草稿 PR。建议当前变化先记录在 **Unreleased**，下一次对外试用发布候选为 **v1.1.0-beta.1**；这是待确认版本建议，不是在本轮打标签或发布。

| 入口 | 内容 | 更新时机 |
| --- | --- | --- |
| README“最近更新” | 最近一次发布的 3–5 个用户可感知变化、版本/日期、详细说明链接；另列开发中内容 | 发布时更新；开发中内容明确标注 Unreleased |
| CHANGELOG.md | 每版 Added / Changed / Fixed / Breaking / Known limitations，附 REQ ID 和 PR | 合入改动即写入 Unreleased；发布时归入版本和日期 |
| docs/releases/vX.Y.Z.md | 该版解决什么问题、完整例子、截图、REQ 结果、验证、升级步骤、已知缺口 | 准备发布时形成可审核正文 |
| ROADMAP.md | Now / Next / Later；每项链接 REQ，列出下一步更新重点 | 需求对齐或优先级变化时更新，不承诺未经确认的日期 |
| GitHub Release | 对应版本说明的公开镜像与源码标签 | CI 通过、升级说明齐全且确认发布后创建 |

版本约定：修复问题用补丁版本，兼容新增功能用次版本，破坏兼容且有迁移方案才升级主版本。前后端版本值与标签同步，不靠更改 README 的版本号冒充发布。核心目录重构、任务资料包数量或用户反馈尚不足时，不把 beta 标成正式稳定版。

每版说明固定包含：一句话目标 → 3–5 个重点变化 → REQ 结果表 → 验证方法及产物 → 升级影响 → 尚未完成事项。避免 README、CHANGELOG 和 Release 各写一份不同事实；详细事实以版本说明和验证记录为依据。

## GitHub README 设计

建议中文优先、英文单独文件，入口互相链接。首页按下面顺序展开：

1. **一句话定位**：FieldToFit 把 AI 动态、研究和开源资源整理成有来源、可比较、能用于下一步工作的材料，供人阅读，也供 AI 通过 API / MCP 使用。
2. **当前状态**：稳定发布版 / Unreleased 分开；当前哪些功能可用、哪些待补、账户待开放。
3. **完整案例**：用“中文 PDF → 金额与页码来源”展示目标、资料包与真实输出；链接完整脚本和运行边界。
4. **产品截图**：当前信息、应用资源和任务资料包，使用实际页面截图。
5. **能做什么**：信息、应用资源、人类工作台、AI 接入四个入口；说明事实、建议和验证结果的区别。
6. **最近更新**：发布版本/日期/重点/详情；开发中内容单独列，不把计划写成已完成。
7. **快速开始**：最小本地启动、可选样本导入、完整案例执行。明确无需模型凭证也能使用的能力。
8. **MCP / API**：最小接入配置和任务提示，链接完整指南。
9. **下一步重点**：仅展示 ROADMAP 当前 3–5 项，如更多完整案例、研究材料、内容运营和真实用户验证。
10. **文档与参与**：部署、后台说明、贡献、反馈、许可证。

后台是维护者管理资料的入口；公开注册继续关闭。所有自动检查更新周期继续固定 1 天。Newsletter 等旧能力放在兼容说明中，首页聚焦当前目标。

## 执行顺序与完成标准

1. 确认本方案，包括中文首页和版本记录安排。
2. 建立现行文档入口，收敛 REQ 状态与证据，再归档旧文档；保留必要的旧链接跳转说明。
3. 按引用关系整理前端与脚本；逐批修改导入、部署配置和文档链接。数据和凭证单独处理。
4. 更新当前截图、README、Unreleased 和 ROADMAP；按版本说明模板整理本轮重点。
5. 验收构建、核心路由、后台登录、完整案例、MCP、文档链接与本地启动；提交独立的整理改动供审阅。

完成意味着：每个源码和文档文件都有清楚归属；新用户能从 README 跑通一个任务；旧兼容入口不意外消失；当前 REQ 只有一份权威状态表；更新重点、未完成项和真实验证结果能互相追溯。
