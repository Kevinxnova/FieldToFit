# Codex 28天专题：需求与方案核对

日期：2026-10-06（Asia/Shanghai）。源码批次v1.6.4；正式站最近已验版本仍为v1.6.3，本轮未部署或复验生产版本。

本记录只保留查询和文档检查证据，唯一需求与方案来源为[FieldToFit-PM.md中的REQ-20](../../FieldToFit-PM.md#req-20)。专题未开发、未上线；未修改每日安排，未创建网站内容草稿或发布任何新记录。

## 来源查询

| 来源／检查 | 实际结果 | 能支持的结论与限制 |
| --- | --- | --- |
| [OpenAI官方更新日志](https://learn.chatgpt.com/docs/changelog)（从developers.openai.com/codex/changelog重定向） | 正文可读，列出2026-10-05 Codex CLI 0.160.1 | 修复远程stdio MCP服务器启动时SYSTEMROOT／TEMP／TMP环境变量保留；不证明属于28天计划或符合多数用户改进 |
| [openai/codex 0.160.1发布](https://github.com/openai/codex/releases/tag/rust-v0.160.1) | 正文可读；显示05 Oct 18:29、tag rust-v0.160.1及提交d27764b；同一修复及PR #51121 | 官方发布条目与日志一致；页面未标明该显示时间的时区，因此不据此构造精确跨时区时间 |
| [Tibo原帖](https://x.com/thsottiaux/status/2106845241357824205) | 网页工具直接读取返回403 Forbidden | 仅定位到原帖地址；正文、原始发布时间、起算日及官方时区未独立确认 |
| [公开追踪线索](https://whenresets.net/)与[另一追踪页](https://t.co/YiyilRWK8W) | 前者可读，链接指向上述原帖；后者搜索结果将28天解释为PT 10月5日至11月1日，并明确称自身解释 | 仅用于定位原始来源和发现日期解释差异，不作为正式发布日期、进度或兑现依据 |

补充读取：系统Python请求公开追踪页先遇到网络／本机证书链错误，系统curl使用默认证书校验成功读取原帖链接；未关闭证书校验。X官方公开嵌入接口请求20秒超时（curl退出28），没有取得正文，不更改原帖未核实状态。

## 仓库与方案核对

- 初始工作区没有未提交改动；已读AGENTS.md、发布指南和现有REQ-6／REQ-19。
- `NewsIndex.tsx`目前在「近期动态」下依次展示本期速览与发布列表；`ReadingContents.tsx`已有两个目录锚点。本轮只登记第三个同级专题，未修改组件。
- 新增主REQ-20和子REQ-20-1至REQ-20-6；主项20、子项124。原历史编号映射和现有网站状态保留。
- 本轮递增patch至v1.6.4；CHANGELOG双语摘要为唯一来源，使用发布元数据工具同步双语README和前端版本。

## 实际检查

- 发布元数据同步：`python3 scripts/maintenance/release_metadata.py --write`通过，前端package／lock及中英文README同步为1.6.4。
- 仓库检查：`python3 scripts/maintenance/check_repository.py`通过，115份文档、878条本地链接、199个相对导入、20主REQ／124子REQ、42历史锚点与91旧子项映射，错误0。
- 既有版本元数据回归：`.venv/bin/python -m pytest tests/test_release_metadata.py -q`，8项通过（0.06秒）。
- 对话结构示意：独立片段通过visualize渲染器的片段格式检查；JavaScript隔离执行确认28个日期按钮、选择状态及交互状态恢复，无虚构日期或实际每日记录。未完成浏览器布局验收，不能据此宣称正式手机／键盘流程通过。
- `git diff --check`通过，无空白错误。
- 本轮未运行前台构建、正式专题浏览器或生产验收；没有修改前台组件或运行逻辑。对话中的结构示意不代表正式网站实现或真实每日数据。

## 未验收范围

正式专题入口、28格日历、时间线、每日内容存储及API／MCP读取、审核发布、跨时区日期、手机／键盘／明暗主题交互、连续三个真实自然日维护和28天收尾均未开发验证。可视化结构示意只说明推荐阅读方式，不含真实每日记录或正式网站组件。
