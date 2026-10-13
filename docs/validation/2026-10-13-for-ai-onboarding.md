# For your AI 接入工作台开发验收

2026-10-13，Asia/Shanghai；源码批次v1.8.49，对应[REQ-8-10至12](../../FieldToFit-PM.md#for-ai-onboarding-plan)。所有者确认浅色留白＋局部玻璃流光，客户端为Codex、Claude、OpenClaw、Pi，并要求先完善总览再开发验证。此次未授权部署，正式站未更新。

## 实现与范围

先登记总览表、三个子REQ与实施／验收条件，再开发独立ForAI页面。页面依次为品牌导读、四客户端选择、三步接入、测试提问、三类使用示例、统一搜索／资料包与进阶同步。桌面两列接入面板，窄屏纵向排列；明暗与双语完整。主体视觉采用CSS玻璃球、细线流光和资料片，不新增图像资源或依赖。

[客户端步骤](../../backend/seo/ai_clients.json)由界面和无脚本HTML共同读取；Codex桌面／CLI、Claude网页桌面／Code、OpenClaw控制台／CLI、Pi内置MCP，共七种路径，带官方链接和实际核对日期。配置地址随当前服务生成，命令参数转义；本机地址与Claude云端访问条件明确。复制有独立反馈与手动回退，令牌不进入复制内容；服务检查只确认网站到MCP可达，初始化响应须有效，异常／超时可重试，切换与卸载取消旧请求。

原HTTP/MCP工具、读取权限、来源／修订／材料覆盖契约、数据库及调度不变。原统一搜索、资料包、档案／报告和`#ai-codex-sync`保留。英文复制问题要求每次调用传`lang=en`，原文仍保持原语言。

## 官方步骤核对

以下页面于2026-10-13实际打开读取，非仅搜索摘要：

- [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)：桌面Settings／MCP servers／Add server，Streamable HTTP，保存重启，/mcp；[官方Docs MCP示例](https://developers.openai.com/learn/docs-mcp)核对`codex mcp add … --url`。
- [Claude远程连接](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp)：Customize／Connectors、自定义连接、认证与对话中启用；[Claude Code](https://code.claude.com/docs/en/mcp)核对HTTP命令及/mcp。组织权限和远程云端网络条件单独说明。
- [OpenClaw MCP](https://docs.openclaw.ai/tools/mcp)：Settings／MCP、streamable-http、doctor --probe及运行中Gateway／Agent重载边界。
- [Pi MCP](https://pi.dev/docs/latest/mcp)：原生远程接入、pi mcp list、/reload及/mcp；已有MCP扩展可接管内置入口。指Pi coding agent。

## 自动验证

- 最终`release_metadata.py`与`check_repository.py`通过：v1.8.49、162份文档、1328个本地链接、332个相对导入、24主REQ／169子REQ，0错误；`git diff --check`通过。
- TypeScript及Vite生产构建通过。现有主包大于500KB的提示保留，不声称已优化全站主包。
- `node tests/frontend/for-ai.cjs`五组通过：七种接入方式与载荷；复制失败回退／语言；HTTP、无效协议及超时后的恢复；令牌隔离／请求清理；旧复制Promise不能覆盖新载荷。首轮发现档案与投稿组件使用重复key，修正为独立key后复验通过。
- `node tests/frontend/remote-language.cjs`六组既有语言回归通过。
- `PYTHON_DOTENV_DISABLED=1 .venv/bin/python -m pytest tests/test_search_pages.py tests/test_platform_lookup.py tests/test_platform_bundle.py tests/test_codex_sync_client.py -q`：**54项通过，90.80秒**。测试使用隔离SQLite；包含新增双语无脚本七路径与真实地址检查。
- 命令转义收尾后定向复验无脚本接入：**2项通过，17项未选中，0.77秒**；与54项重合，不叠加计数。

## 实际本地页面与服务

由[隔离启动器](../../tests/browser/for-ai_server.py)在127.0.0.1:18149提供正式构建，使用临时SQLite、关闭统计、不读取生产数据库或凭据。

- 中英两种语言分别检查320／390／736／1024／1440px，共10个尺寸／语言组合；页面宽度等于视口宽度，未发现页面元素横向越界。另检查英文深色的五宽度与390px实际画面；中文浅色及英文暗色已截图。
- 初次浏览器连接多次超时，显式重置后恢复；未将失败尝试写作通过。大窗口视觉复验发现混合光效的矩形遮挡，移除跨层混合与backdrop滤镜、隔离球体光层后，最终1440px和手机截图正常。
- 四客户端切换与对应命令、Claude Code分支、英文保持当前选择已实际检查。键盘Enter可选Codex／CLI，切换后焦点仍为CLI按钮。网页服务检查实际返回可达，文案继续要求在个人AI中完成读取。
- 浏览器点击复制显示成功；该浏览器的会话剪贴板读取返回空，故不将此项写为系统剪贴板载荷验收。精确复制内容及失败／异步回退由上方真实组件测试捕获并核对。
- 英文搜索Pi实际返回13项，首项CW-A07；加入资料包后预览1项、32,822个原文字符、3项仅链接。JSON实际下载为58,551字节，解析后包含CW-A07及对象／覆盖信息，不含测试令牌。结果来自本地种子，不代表当前生产集合数量。
- 旧`#ai-codex-sync`可定位并显示专题连接、范围与同步复制控件；既有资料包及专题按钮可用。最终页面控制台未记录error／warn。
- 独立HTTP JSON-RPC实际完成initialize／tools-list及中英`curated_lookup(Claude)`→`curated_watch`读取，18个工具、CW-M02、9项出处、原核验日2026-10-08和一致修订均保留。该验证是协议读取，未调用模型生成回答。
- 本机Codex／Claude的`mcp add --help`语法已核对；Codex通过临时`-c`覆盖解析出streamable_http与本机服务URL，未写入用户配置。环境未安装OpenClaw／Pi；未逐一进行四款真实客户端的完整聊天取材。

截图、尺寸回执与协议回执保存于忽略目录`output/operations/for-ai-20261013`。最终构建和当前本地版本同步为v1.8.49；未部署、未推送或创建发布标签。真机、屏幕阅读器、系统减少动态效果及四客户端完整聊天验收仍未完成；减少动态效果已通过CSS实现，不把静态检查冒充系统设置实测。


<a id="brand-headline-review"></a>
## 同日复审：品牌图形与主标题（v1.8.50）

所有者确认将玻璃球中的f→f替换为FieldToFit标志，主标题改为「把 FieldToFit，接入你的 AI。」。本批直接复用现有横版品牌SVG中的图形几何，保留160:112比例，浅色使用原墨色、深色使用原纸白；既有品牌素材文件未改写。共享页面文案同步为英文“Connect FieldToFit to your AI.”，无脚本页面沿用同一来源。

实际复验：

- TypeScript／Vite构建通过；现有大于500 kB的构建分块提示仍存在。本机frontend目录默认命令路径未提供npm／node，改用已安装Node的绝对路径后完成构建。
- `PYTHON_DOTENV_DISABLED=1 .venv/bin/python -m pytest tests/test_search_pages.py -q -k 'ai_setup or public_landing'`：2项通过、17项未选择，覆盖双语无脚本接入页面。未新增针对静态替换的测试，未将上一批54项回归计入本批。
- 本地隔离服务重启为v1.8.50；中文浅色、英文深色分别检查320／390／1440px，共6组尺寸／语言／主题组合，页面未横向溢出；主标题和原比例品牌图形显示正常。390px英文浅色也已视觉检查。
- 桌面中文、手机中文及手机英文深色截图分别保存于`output/operations/for-ai-20261013/brand-headline-desktop-zh.jpg`、`brand-headline-mobile-zh.jpg`、`brand-headline-mobile-en-dark.jpg`。浏览器控制台无error／warn，预览恢复中文浅色与默认窗口尺寸。
- 版本元数据同步为v1.8.50；仓库检查覆盖162份文档、1331个本地链接和332个相对导入，0错误；`git diff --check`通过。

本批仍仅本地交付，未部署；客户端聊天验收边界沿用上一批记录。
