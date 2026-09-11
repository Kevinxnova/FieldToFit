# FieldToFit 版本导航

当前网站运行 **FieldToFit v1.0.3**，地址为 [fieldtofit.top](https://fieldtofit.top)。公开读取已验收，生产维护写入与连续真实日周期仍待验；运行版本不等同全部 REQ 完成。

## 当前版本

- [FieldToFit v1.0.3](v1.0.3.md)：新增各家旗舰模型筛选、名单说明与缺项展示。

- [FieldToFit v1.0.2](v1.0.2.md)：2026 年 AA / Arena 图表、统一公司配色、直接名称与覆盖清单；移除 Epoch。

- [FieldToFit v1.0.1](v1.0.1.md)：三来源图表、双页导读、解读默认可见、MCP 接入、移除旧展示入口；状态见版本验收。

- [FieldToFit v1.0.0](v1.0.0.md)：品牌、网站、27 项既有发布资料和 10 项精选 MCP 工具公网验收。
- [2026-09-11 阅读更新](../validation/2026-09-11-reading.md)：10 条动态、逐点解读、两区布局、目录和第 11 项 MCP 工具，当时运行版本为 v1.0.0，本次交付归入 v1.0.1。
- [更新记录与历史附录](../../CHANGELOG.md)：当前变化及前次文档、公开素材整理。
- [下一步](../../ROADMAP.md)：资源材料补充、来源跟踪表及维护验收。

## 标签规则

FieldToFit 使用 `fieldtofit-v1.0.0`、`fieldtofit-v1.0.1` 等品牌前缀；软件内部仍使用 1.0.0、1.0.1。只有实际创建并核对过的标签才能写成可下载版本。旧 `v1.0.0` 是 Metis，保留原提交，不移动、不覆盖。

## 后续更新流程

1. 在 CHANGELOG 的 Unreleased 记录实际变化及对应 REQ；需求方案与实现验收分开。
2. 发布说明按[模板](template.md)记录改动、验证、迁移和缺口，同步前后端版本。
3. 更新 README 最近版本、文档导航、REQ 状态及 ROADMAP；每个有实际修改的交付提交都递增 z（包括内容/文档）；无变更的每日检查不递增。y/x 须先对齐确认，见[版本规则](versioning.md)。
4. 完成构建、相关回归和实际部署检查，记录证据。
5. 对验收的提交创建品牌前缀标签与 Release，正文使用逐版说明；失败或未做的检查不能标完成。

## 附录：Metis 历史版本

[beta.2](../archive/metis/releases/v1.1.0-beta.2.md) · [beta.1](../archive/metis/releases/v1.1.0-beta.1.md) · [历史目录](../archive/README.md)。
