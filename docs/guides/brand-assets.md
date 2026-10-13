# 网站公开品牌图片

2026-09-11。用户已自行备份完整品牌包，并授权从项目删除其余素材。FieldToFit自身品牌当前仅保留以下 5 份图片，文件内容保持不变：

| 文件 | 用途 |
| --- | --- |
| `frontend/public/brand/logo-horizontal-ink.svg` | 浅色导航、关于页；README 复用 |
| `frontend/public/brand/logo-horizontal-paper.svg` | 深色导航、关于页；README 复用 |
| `frontend/public/brand/share.png` | 链接分享 |
| `frontend/public/favicon.svg` | 浏览器图标 |
| `frontend/public/apple-touch-icon.png` | 收藏网站图标 |

来源为用户提供的 FieldToFit 品牌包网站导出图片。项目不再携带母版、字体文件、生成脚本、展示板、概念图、其他配色尺寸或品牌压缩包，也不建立公开母版目录。用户备份由用户保管，本轮不访问或修改备份。

完整素材包曾进入公开 Git 历史；本轮仅清理本地工作目录和当前分支，不重写提交、标签或历史 Release，不保证清除已下载副本。后续若清理历史，应单独列出影响与操作计划。


<a id="client-marks"></a>
## 接入客户端标志

2026-10-13，按所有者要求用于For your AI客户端选择卡和连接示意。以下第三方标志与FieldToFit自身品牌素材分开存放，并随站点提供；页面不依赖外部图片请求。名称和标志归各权利人所有，仅用于识别客户端，不表示合作或背书。

| 本地文件 | 官方来源 | 处理 |
| --- | --- | --- |
| [chatgpt.svg](../../frontend/public/brand/clients/chatgpt.svg) | [ChatGPT官方CDN](https://cdn.oaistatic.com/assets/favicon-l4nq08hd.svg)；[OpenAI品牌说明](https://openai.com/brand/) | 原文件保留；按所有者指定用于Codex。通过页面color-scheme选择素材内置黑／白色，不改变图形。 |
| [claude.svg](../../frontend/public/brand/clients/claude.svg) | [Claude官网](https://claude.com/)页首ClaudeWordmark内的独立星形路径 | 提取原路径及原色#D97757，置于125×125画布；没有重新绘制。 |
| [openclaw.svg](../../frontend/public/brand/clients/openclaw.svg) | [OpenClaw官网图标](https://openclaw.ai/favicon.svg) | 原文件保留，包含龙虾形状、渐变和眼睛。 |
| [pi.svg](../../frontend/public/brand/clients/pi.svg) | [Pi官网可下载标志](https://pi.dev/logo-auto.svg)；[Pi官网](https://pi.dev/) | 原文件保留，含三色图形和800×800画布；仅在界面中等比缩放以平衡视觉尺寸。 |

入库前检查SVG结构，未包含脚本、事件处理、foreignObject或外部资源引用。第三方标志不纳入项目原创品牌的许可范围。
