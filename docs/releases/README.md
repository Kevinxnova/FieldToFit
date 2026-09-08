# 版本维护

完整变更记录只有根目录的 [CHANGELOG](../../CHANGELOG.md)。本目录提供逐版重点、REQ 对应、验证和升级说明；[ROADMAP](../../ROADMAP.md) 记录未来安排。

## 当前版本

- [v1.1.0-beta.2](v1.1.0-beta.2.md)：开发候选版，Skill / Agent、筛选、每日运营、编辑事务和研究导出。
- [v1.1.0-beta.1](v1.1.0-beta.1.md)：开发候选版，目录与展示整理；主案例 pending。
- v1.0.0 及更早历史：见 CHANGELOG 和 [历史归档](../archive/README.md)。

## 后续更新流程

1. 合入改动时，把用户可感知的变化写入 CHANGELOG 的 Unreleased，标注相关 REQ；更新唯一的需求状态表。
2. 准备版本时，参照 [说明模板](template.md) 创建版本文件，同步后端 `__version__`、frontend package 和 lockfile。
3. 检查 README 的“最近更新”、ROADMAP 和版本说明内容一致；更新真实截图，不把计划或模拟结果当作实测。
4. 运行必要检查，保留版本、输入和环境对应的证据；记录未完成事项与升级影响。
5. 确认发布后，为检查通过的同一提交创建标签和 GitHub Release；Release 正文来自该版本说明。开发候选不等于已经发布。

补丁版本用于修复；兼容新增功能用次版本；破坏兼容的改动需升级说明和主版本评估。原 API 路径与 MCP 协议版本单独管理。
