# 2026-09-25 · 六项动态及固定原文发布验收

用户明确确认“A–F 全部发布”。本批版本 v1.5.16；承接9月24日五项提案与9月25日Live Avatar提案，不重复创建日报提案。私密草稿、备份、预览、发布回执及MCP响应保存于 `output/operations/v1.5.16-release/`，不提交到公开仓库。

| 编号 | 内容 | 位置 | 公开原文范围 |
| --- | --- | --- | --- |
| A | Gemini 3.8 Flash TTS / Flash-Lite TTS | 动态、速览 | 官网公告仅链接；保留已开放／预告功能区别 |
| B | Antigravity SDK 本地模型 | 动态、速览 | 固定 README、Apache LICENSE；混合云方案不称完全离线 |
| C | Meta Muse Connect 更新 | 动态、速览 | 官网仅链接；Mac与连接器和未来眼镜功能分开说明 |
| D | Strands Harness | 动态补录、持续关注 Harness | 根 README、Python Harness README、LICENSE.APACHE、NOTICE；相同四份材料供两种条目读取 |
| E | FLUX 3 Action | 动态、速览 | 代码 README、安装说明、LICENSE、NOTICE；权重自定义许可仅链接 |
| F | Gemini 3.8 Live Avatar | 动态、速览 | 官网仅链接；企业接入及自定义头像白名单边界 |

## 固定材料

- Antigravity：`google-antigravity/antigravity-sdk-python@7f19db07e7c6c5038102b45a8a7a5da7eecc8b11`，2份。
- Strands：`strands-agents/harness-sdk@7ae759d3ad43916d373cf0f3251ac7f57e95339c`，4份。
- FLUX：`black-forest-labs/flux-action@e2dd1d8dbc5977b54315d61f7548c63c043d6d4f`，4份。

共10份不同原文，Strands在新闻与持续关注中共享，形成14份对象材料引用。保存原始正文与SHA-256，不复制外链图片、权重、数据集或未经确认许可的官网公告。源码及文档Apache许可与外部模型/服务条款分别说明。本次未安装三个项目，也未复测作者性能或成本数据。

## 实际验证

- 已完成：发布前公开内容与私密工作区备份；生产数据库只读快照及本地SQLite完整性检查通过。
- 已通过：七个条目管理预览，For you与For your AI数据一致；桌面1440px／手机390px均无页面横向撑破、无页面脚本错误。
- 已通过：39条动态／33项持续关注；D-34至D-39与CW-H05审核发布回执；两日六个私密提案均回写published，日报按实际消息补记送达而非准时。
- 已通过：五条本期速览为D-39／D-36／D-34／D-35／D-38；旧33条新闻除五项highlight取消外逐项保持一致，旧32项持续关注逐项不变。
- 已通过：公开双端阅读、复制AI交接、For your AI统一检索；两张模型图表133／84及旗舰11／5保持不变，真实日期保留。
- 已通过：43次MCP协议调用；新闻与持续关注HTTP/MCP内容一致，七项统一检索与对象读取，14份对象材料引用跨段拼接与原始正文、SHA-256及固定提交一致，去重10份；资料包覆盖全部已存正文，变化流可读。本批不是自主客户端最终作答测试。
- 已通过：七个新详情页面HTTP200、初始HTML及canonical；77个sitemap网址包含全部七项。未将生成地图等同于搜索引擎已经收录。
- 已通过：71项内容相关回归；导出新公开种子后41项新闻／持续关注及搜索页面回归通过；前端构建、版本元数据与仓库检查。
- 已通过：Vercel生产部署READY，健康接口v1.5.16、MCP initialize=1.5.16，部署ID `dpl_GeBoBAWSZ545tz4aUigJmodYsPtB`。没有数据库结构或凭据变更。
- 源码发布标签fieldtofit-v1.5.16；GitHub推送及Release以实际回执为准。

本批不将MCP协议核对当作自主客户端完整作答验收；既有Jev官网原文缺口、08:00准时日报、来源延期及连续三日全来源成功等缺口未关闭。模型图表仍为本站9月23日核对快照，AA133／Arena84点，Arena来源截止日9月13日。
