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

[访问网站](https://fieldtofit.top) · [For you](https://fieldtofit.top/for-you) · [For your AI](https://fieldtofit.top/for-your-ai) · [English](README.en.md)

给你看，也给你的 AI 用。面向研究者、工程师、研究生和学生，平台维护有出处的资料；用户和自己的 AI 结合任务继续比较、选择和构建。

## 两种阅读方式

| 入口 | 当前作用 | 下一版已对齐方向 |
| --- | --- | --- |
| For you | 本期概览、27 项已发布精选对象、结构化详情、出处、原文、资料导出 | 本期重点 → 重点动态 → 精选资源；重点跟踪公司/产品更新，以及近期受关注、长期有价值的项目 |
| For your AI | 同一套已发布资料的 MCP/API、原文续读、修订历史和资料包 | 同步读取公司、产品、版本与事件关系，保留来源观点与编辑评价的区别 |
| 关于 FieldToFit | 项目立意、使用方法、维护原则、真实版本与参与入口 | 补充新的内容方向；来源辅助页增加跟踪主体和发现渠道说明 |

**当前运行 v1.0.0。** 2026-09-10 已验证公开网站及 10 项精选 MCP 工具，见[品牌与公网验收](docs/validation/2026-09-10-fieldtofit-brand.md)。以上新内容组织和[首发具体名单草案](docs/product/launch-selection.md)仍待实施/确认，不能将设计视为已上线。

资料每 **1 天**检查，有值得发布的变化才更新内容。事实、作者声明、编辑评价和实测分开；未知、失败与材料缺口明确保留。公开账户标注“待开放”，AI 应用案例 pending。

## 连接个人 AI

公开只读 MCP：[https://fieldtofit.top/api/mcp/curated](https://fieldtofit.top/api/mcp/curated)。将此地址填入支持远程 HTTP MCP 的客户端；配置说明见 [For your AI](https://fieldtofit.top/for-your-ai) 和[接入指南](docs/guides/ai-access.md)。

当前提供 10 项精选读取工具，支持检索、档案、原文、导出、资料包、来源、期次、变化和修订历史。旧 `/api/mcp` 的 19 项工具保留兼容。协议调用通过不等同于所有日常 AI 客户端都已验收。

## 当前进展与最近更新

| 日期 / 记录 | 已完成 | 待完成 |
| --- | --- | --- |
| 2026-09-11 · 文档与文件整理 | 当前介绍统一为 FieldToFit；Metis 历史归档；公开品牌素材收敛为 5 份；产品文档更新到 P2 | 首发逐条内容确认、新展示与跟踪表开发 |
| 2026-09-10 · [v1.0.0](docs/releases/v1.0.0.md) | 品牌、域名、关于页；公网 27 项对象与 10 项精选 MCP 工具验证 | 生产维护写入/恢复、连续 3 个真实日周期、日常客户端及目标用户验收 |

[18 项 REQ / 72 个子 REQ](docs/product/requirements.md)逐项记录范围与缺口。[路线图](ROADMAP.md)列出下一步，[更新记录](CHANGELOG.md)正文聚焦 FieldToFit，旧记录位于其 Metis 附录。

后续发布标签采用 `fieldtofit-v1.0.0` 这样的前缀，网站仍显示 v1.0.0。现存 `v1.0.0` 属于旧 Metis，保留原指向；本轮未新建发布标签。软件发版与内容期次分别记录。

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
