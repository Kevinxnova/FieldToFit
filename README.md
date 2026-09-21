# FieldToFit

[中文](README.md) | [English](README.en.md)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="frontend/public/brand/logo-horizontal-paper.svg">
  <img src="frontend/public/brand/logo-horizontal-ink.svg" alt="FieldToFit" width="600">
</picture>

**FIELD → FIT**

**FieldToFit 是人与 AI 共享的动态 AI 地图：看清已有方案，判断是否适配，选择正确的采用与构建路线。**

- **Field**：动态、论文、模型、工具、开源项目和开发资料组成的 AI 全景。
- **To**：持续跟踪、整理、比较、验证和筛选。
- **Fit**：结合用户的任务、条件与限制，判断什么真正适用。

[访问网站](https://fieldtofit.top) · [For you](https://fieldtofit.top/for-you) · [For your AI](https://fieldtofit.top/for-your-ai) · [FieldToFit 社区](https://fieldtofit.top/community)

<!-- section:overview -->
## FieldToFit 提供什么

面向研究者、工程师、研究生、学生及 AI 应用开发者。平台维护有出处的资料；你和自己的 AI 结合任务继续判断、采用与构建。

| 入口 | 提供什么 | 如何开始 |
| --- | --- | --- |
| For you | AA / Arena 模型能力与价格图、近期动态，以及模型、工具、Agent、Skill、Harness 的持续关注资料 | 先看近期变化，再沿目录阅读具体项目、版本表、逐点解读和出处 |
| For your AI | 同一套已发布资料的 MCP / API、原文续读、修订历史和资料包 | 复制 MCP 地址接入个人 AI，或下载资料交给它继续使用 |
| FieldToFit 社区 | 共建介绍、开发者投稿及参与入口 | 提交项目、推荐资源、纠错，或参与开发 |

资料每 **1 天**检查，发现值得发布的变化后整理、审核，再同步给人和 AI。事实、来源观点、编辑评价与实测结果分开，未知项明确保留。注册与同步尚未开放，AI 应用案例暂缓。

<!-- section:release -->
## 当前版本与本版更新

<!-- current-version:start -->
**当前源码版本：[v1.5.5](CHANGELOG.md#v1.5.5)** · [fieldtofit-v1.5.5](https://github.com/Kevinxnova/FieldToFit/tree/fieldtofit-v1.5.5)
<!-- current-version:end -->

源码版本与网站运行版本分别核验；网站部署状态见[本版验收](docs/validation/README.md)。

<!-- latest-summary:start -->
- 发布用户确认的四项日报内容：Qwen3.8-Omni-Flash、Kimi Code Desktop、Copilot 开发流程更新，以及 Harness 计划与验收研究。
- 本期速览同步四条动态；Qwen 模型表补充 Omni-Flash 分支，保留旧版本、原文日期、采用条件和未实测边界。
- 在动态和 Qwen 资料中提供同一固定提交的 README、安装说明和 Apache-2.0 许可证；其余官方材料明确为来源链接，网页与 MCP 同源读取。
- 记录真实日报补发、内容发布与读取验收；每日采集仍有延期或获取问题，不将本批内容发布写成连续运行验收通过。
<!-- latest-summary:end -->

[完整更新记录](CHANGELOG.md) · [项目管理总览：方案、开发、验证与网站状态](FieldToFit-PM.md)

<!-- section:ai -->
## 给你的 AI 使用

公开只读 MCP 地址：

```text
https://fieldtofit.top/api/mcp/curated
```

将地址添加到支持远程 HTTP MCP 的 AI 客户端。连接后，让 AI 检索相关资料、读取出处、版本和已知限制，并结合你的任务继续工作。

`curated_lookup` 已上线：在同一 MCP 内检索近期动态、持续关注和可公开原文，按结果继续读取或打包；For your AI 提供同源搜索预览。本版继续提供同一 MCP 地址；正式服务能力可通过 `tools/list` 核对。

无需网站账户。客户端是否支持远程 MCP、如何填写配置，请参阅 [For your AI](https://fieldtofit.top/for-your-ai) 和[接入指南](docs/guides/ai-access.md)。协议验证不代表所有客户端均已完成实际验收。

<!-- section:community -->
## FieldToFit 社区

FieldToFit 正在逐步建设围绕 AI 应用的共建社区，维护持续更新、可追溯、人与 AI 都能使用的 **AI 应用资料库（AI Application Database）**。

我们整理值得关注的模型、工具、开发经验和开发者投稿项目，让已有成果更容易被发现、理解和采用。欢迎提交项目、推荐资源、补充资料，或参与测试、文档与功能开发，一起做出有意义的事情。

### 开发者投稿项目

**让你的项目，被更多人看见。** 个人和团队的 AI 应用、工具与开源项目，只要有可查看的原型、演示或代码，并能说明解决的问题，就可以投稿。也欢迎说明你需要的测试者、开发伙伴或文档协作。

通过 [GitHub Issue](https://github.com/Kevinxnova/FieldToFit/issues/new) 或 [fieldtofit@163.com](mailto:fieldtofit@163.com) 提交六项信息：**项目名称、项目介绍（解决的问题及面向的人）、项目入口、如何使用、开放情况、作者与提交者关系**。

维护者计划每周集中审核；提交不等于自动收录。GitHub Issue 公开，邮件本身不会直接公开；确认后的项目材料经审核同步至 For you 和 For your AI。也可用[社区页面](https://fieldtofit.top/community#submit-project)准备投稿草稿。

### 参与共建

- [提交开发者项目](https://fieldtofit.top/community#submit-project)：介绍成果，寻找使用者和开发伙伴。
- [推荐资源或纠错](https://fieldtofit.top/feedback)：补充资料，帮助内容保持准确。
- [参与 FieldToFit 开发](CONTRIBUTING.md)：从资料整理、测试、文档或功能开发开始。

<!-- section:local -->
## 本地运行

环境：Python 3.12 / 3.13、Node.js 20+。

```bash
git clone https://github.com/Kevinxnova/FieldToFit.git fieldtofit
cd fieldtofit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
cd frontend
npm ci
cd ..
```

已有 `.env` 请保留。默认使用 SQLite；基础浏览不需要模型服务密钥。在两个终端分别启动：

```bash
./scripts/start-backend.sh
```

```bash
cd frontend
npm run dev
```

打开 [localhost:5173/for-you](http://localhost:5173/for-you)。新数据库为空，内容导入及审核见[平台指南](docs/guides/platform.md)。完整功能依赖后端服务，不能直接双击 HTML 使用。

<!-- section:docs -->
## 文档、贡献与许可

[文档导航](docs/README.md) · [REQ list](FieldToFit-PM.md) · [内容管理](docs/guides/management.md) · [部署](docs/guides/deployment.md) · [发布规则](docs/guides/releasing.md) · [贡献指南](CONTRIBUTING.md) · [安全报告](SECURITY.md)

源码采用 [MIT](LICENSE)；第三方资料遵循各自原始许可。[品牌素材说明](docs/guides/brand-assets.md)列出公开图片的范围。历史 Metis 资料位于[更新记录附录](CHANGELOG.md#附录metis-历史更新记录)和[历史目录](docs/archive/README.md)。
