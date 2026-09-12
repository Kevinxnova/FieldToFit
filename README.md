# FieldToFit

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="frontend/public/brand/logo-horizontal-paper.svg">
  <img src="frontend/public/brand/logo-horizontal-ink.svg" alt="FieldToFit" width="600">
</picture>

**FIELD → FIT**

- **Field**：动态、论文、模型、工具、开源项目和开发资料组成的 AI 全景。
- **To**：持续跟踪、整理、比较、验证和筛选。
- **Fit**：结合用户的任务、条件与限制，判断什么真正适用。

**FieldToFit 是人与 AI 共享的动态 AI 地图：看清已有方案，判断是否适配，选择正确的采用与构建路线。**

[社区与投稿](https://fieldtofit.top/community) · [访问网站](https://fieldtofit.top) · [For you](https://fieldtofit.top/for-you) · [For your AI](https://fieldtofit.top/for-your-ai) · [English](README.en.md)

给你看，也给你的 AI 用。面向研究者、工程师、研究生和学生，平台维护有出处的资料；用户和自己的 AI 结合任务继续比较、选择和构建。

## 两种阅读方式

| 入口 | 当前作用 | 本轮实现与后续方向 |
| --- | --- | --- |
| For you | 10 条近期动态（5 条速览）、五类 27 个持续关注主体、版本 / 技能表与阅读目录 | 补充资源原文，完善动态与档案关系 |
| For your AI | 同一套已发布档案与动态的 MCP/API、原文续读、修订历史和资料包 | 同步读取公司、产品、版本与事件关系，保留来源观点与编辑评价的区别 |
| FieldToFit 社区 | 共建介绍、开发者投稿项目、GitHub / 邮箱投稿和资源反馈 | 每周人工审核；收录后同步展示给人和 AI |
| 关于 FieldToFit | 项目立意、使用方法、维护原则、真实版本与参与入口 | 补充新的内容方向；来源辅助页增加跟踪主体和发现渠道说明 |

**当前运行 v1.1.0：统一内容管理，已部署并通过本版验收。** 四模块串联每日审阅、草稿、双端预览和明确发布；同一数据库同时供网页与 MCP 读取。现有公开内容保留。[本版更新与部署状态](docs/releases/v1.1.0.md) · [内容管理指南](docs/guides/management.md)。

资料每 **1 天**检查，有值得发布的变化才更新内容。事实、作者声明、编辑评价和实测分开；未知、失败与材料缺口明确保留。公开账户入口已移除，注册与同步继续关闭，AI 应用案例 pending。

## 连接个人 AI

公开只读 MCP：[https://fieldtofit.top/api/mcp/curated](https://fieldtofit.top/api/mcp/curated)。将此地址填入支持远程 HTTP MCP 的客户端；配置说明见 [For your AI](https://fieldtofit.top/for-your-ai) 和[接入指南](docs/guides/ai-access.md)。

当前提供 12 项精选读取工具（包括 curated_news、curated_watch），支持检索、档案、原文、导出、资料包、来源、期次、变化和修订历史。旧 `/api/mcp` 的 21 项工具保留兼容。协议调用通过不等同于所有日常 AI 客户端都已验收。

## 当前进展与最近更新

| 日期 / 记录 | 已完成 | 待完成 |
| --- | --- | --- |
| 2026-09-12 · [v1.1.0](docs/releases/v1.1.0.md) | 统一内容管理、每日候选、私密草稿、双端发布、图表与反馈管理、原样迁移 | 连续真实日运营、全文补齐、多编辑者实名审计 |
| 2026-09-12 · [v1.0.5](docs/releases/v1.0.5.md) | 关于页邀请卡片留白与主题适配；直接说明 GitHub / 邮箱投稿；解释反馈保存去向 | 真实投稿与反馈的持续处理；自动通知尚未实现 |
| 2026-09-11 · [v1.0.4](docs/releases/v1.0.4.md) | 精简目录、更新关于页、社区与六项投稿表单、已审投稿同源读取 | 首批真实投稿及每周审核运营 |
| 2026-09-11 · [v1.0.3](docs/releases/v1.0.3.md) | 新增“各家旗舰模型”：AA 11 点、Arena 8 点；名单依据、缺项说明与筛选分享 | 持续维护旗舰名单和来源缺项 |
| 2026-09-11 · [v1.0.2](docs/releases/v1.0.2.md) | AA / Arena 2026 年图表：190 点、12 组公司配色、来源原名直接标注、筛选/放大/缺项清单；移除 Epoch | Arena 未确认日期、来源未给出的评分/价格继续补核 |
| 2026-09-11 · [v1.0.1](docs/releases/v1.0.1.md) | 三来源模型图表、双页导读、解读默认可见、MCP 交接、移除旧展示入口、版本规则 | 图表覆盖、连续真实日维护、客户端验收 |
| 2026-09-11 · [持续关注 CW1](docs/validation/2026-09-11-continuous-watch.md) | 五类 27 主体、具体表格与解读、同源 MCP、复制 / 下载 | 原文补齐、自动维护及统一对象关系 |
| 2026-09-11 · 阅读结构更新 | 近期动态与资源档案、10 条动态分点解读、桌面/手机目录、第 11 项 MCP 工具 | 新闻自动采集与全文、来源跟踪表 |
| 2026-09-11 · 文档与文件整理 | 当前介绍统一为 FieldToFit；Metis 历史归档；公开品牌素材收敛为 5 份；产品文档更新到 P3 | 来源跟踪表与持续运营验收 |
| 2026-09-10 · [v1.0.0](docs/releases/v1.0.0.md) | 品牌、域名、关于页；公网 27 项对象与 10 项精选 MCP 工具验证 | 生产维护写入/恢复、连续 3 个真实日周期、日常客户端及目标用户验收 |

[22 项 REQ / 91 个子 REQ](docs/product/requirements.md)逐项记录范围与缺口。[路线图](ROADMAP.md)列出下一步，[更新记录](CHANGELOG.md)正文聚焦 FieldToFit，旧记录位于其 Metis 附录。

后续发布标签采用 `fieldtofit-v1.0.0` 这样的前缀，网站显示当前实际版本。现存 `v1.0.0` 属于旧 Metis，保留原指向。每次交付提交递增 z，y/x 升级须先确认；[版本规则](docs/releases/versioning.md)。

## 本地启动

环境：Python 3.12/3.13、Node.js 20+。

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

已有 `.env` 请保留。默认 SQLite；浏览和基础读取无需模型密钥。生产数据库、管理员及维护凭据按[部署说明](docs/guides/deployment.md)独立配置。

两个终端分别启动：

```bash
./scripts/start-backend.sh
```

```bash
cd frontend
npm run dev
```

打开 [本地前端](http://localhost:5173/for-you)。新数据库为空；真实材料隔离预览与审核发布见[平台指南](docs/guides/platform.md)。网页依赖服务，不能双击 HTML 获得完整功能。

## 维护与参与

[文档首页](docs/README.md) · [目标](docs/product/goals.md) · [需求](docs/product/requirements.md) · [内容维护](docs/guides/content.md) · [目录与兼容清单](docs/architecture/repository.md) · [品牌素材范围](docs/guides/brand-assets.md) · [贡献](CONTRIBUTING.md) · [安全报告](SECURITY.md)

欢迎提出值得跟踪的对象、资料纠错和 AI 取材反馈。源码采用 [MIT](LICENSE)；第三方材料遵循各自原始许可，品牌文件的公开范围见上述说明。
