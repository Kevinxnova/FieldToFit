# For your AI 接入工作台开发与部署验收

当前状态：v1.8.52已完成正式部署和检索连接修复，见[最终验收](#remote-lookup-fix)。以下保留各轮开发时的实际状态。

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


<a id="client-mark-review"></a>
## 同日复审：四客户端真实标志（v1.8.51）

所有者要求将Codex的C占位换为GPT标志，并将Claude、OpenClaw、Pi占位字符改为对应原始标志。已从官方素材取得GPT黑白结形、Claude橙色星形、OpenClaw龙虾和Pi三色图形，选择卡与上方示意图共用组件；图片仅作装饰，按钮仍用产品名称作为无障碍名称。官方出处、提取方式及归属见[素材说明](../guides/brand-assets.md#client-marks)。

实际复验：

- TypeScript／Vite构建通过；既有大于500 kB的分块提示仍存在。`node tests/frontend/for-ai.cjs`五组交互回归通过，包括四客户端七路径、双语复制、服务检查、超时和异步切换保护；既有react-test-renderer弃用提示仍存在。
- 官方素材读取遇到本机Python证书链错误，改用系统curl并保持TLS校验。OpenAI品牌页和ChatGPT首页下载受403／超时限制，最终从ChatGPT官方CDN取得SVG；没有使用第三方重绘文件。
- 初次浏览器检查发现新增独立静态目录不在后端路由中；已将素材移入现有`/brand/clients/`路径并重新构建。最终五个图标位置均加载成功、naturalWidth大于0；四客户端逐一切换后示意图名称与图片地址对应，全部加载成功。
- 1440px中文浅色／深色视觉检查通过；GPT采用SVG原有黑白配色并与页面主题一致。320／390px中文浅色与英文深色共四组手机尺寸组合未横向溢出，390px截图中的四图标及名称清晰。
- 截图保存于`output/operations/for-ai-20261013/client-marks-desktop-zh.jpg`、`client-marks-desktop-dark.jpg`、`client-marks-mobile-zh.jpg`和`client-marks-mobile-en-dark.jpg`；本地预览恢复中文浅色与默认窗口尺寸。

版本元数据同步为v1.8.51；仓库检查为162份文档、1340个本地链接、332个相对导入，0错误，`git diff --check`通过。

本批仅本地交付，未部署；接口与接入步骤保持，真实客户端完整聊天验收边界沿用上一批。


<a id="production-deployment"></a>
## 正式部署与最终验收（v1.8.51）

2026-10-13所有者确认当前页面并明确授权「最后的开发与验证、验证后更新并部署」。本批汇总v1.8.49–51已审页面及品牌修订；发布状态收尾沿用v1.8.51，不重复递增版本。

- 发布前重跑54项相关后端回归：全部通过，92.76秒；五组接入交互、六组语言回归及仓库检查通过。使用隔离SQLite。正式基线目录中的TypeScript／Vite构建通过，保留既有大分块提示。
- 以真实v1.8.47部署输入为基线，仅替换16条本批路径。源清单289文件、14,605,704字节；API、数据库种子、For you及调度保持。构建曾额外生成`backend/seo/client.html`，与已验dist/index.html字节相同，核对后从最终上传源目录排除，由Vercel构建流程重新生成；没有凭据、数据库、私密草稿、依赖、符号链接或缓存进入正式源包。
- 发布前读取正式health与news／watch／maps／model-landscape四个完整公开集合；只读原子备份生产82张表，独立SQLite恢复完整性为ok，该备份不写入生产数据库。备份位于私密临时文件，不提交源码。
- 首轮部署为`dpl_6DegbAz58mkfMhWn2y871Sg3JPBw`，Vercel构建完成并Ready，正式域名fieldtofit.top更新为v1.8.51。
- 北京时间23:00完成首轮正式HTTP核对：health为v1.8.51，三个MCP均为1.8.51；中英文For your AI和For you均返回200，接入页面包含七条路径与正式服务地址，无本地地址。四标志及主JS／CSS／For you场景JS的字节哈希与已验正式构建一致；日志版本及revision与生成源一致。
- 精选MCP实际列出18项工具，中英文均完成`curated_lookup(Claude)`→`curated_watch`完整读取，CW-M02、10项出处、核验日2026-10-09及同一修订保留。这是正式协议取材，不代表四款真实客户端均已完成聊天验收。
- 部署前后四个完整公开JSON集合逐项相等；没有借发布页面改写已审核内容。
- 本地页面已完成此前各轮桌面／手机、明暗／双语、切换、复制和打包验收。正式浏览器尝试中，旧标签已失效，重新获取当前标签后正式域名导航仍超时，后续DOM读取超时并重置工具；本批未取得正式浏览器视觉通过证据。正式HTTP／资源哈希通过不能替代该项。

发布清单、备份回执和正式检查回执保存在忽略目录`output/operations/for-ai-release-20261013`；实际生产数据及凭据不进入Git。四客户端完整聊天、真机、屏幕阅读器与系统减少动态效果验收仍按前文保留边界。


<a id="remote-lookup-fix"></a>
## 最终复验发现与修复（v1.8.52）

v1.8.51首轮协议验收确实通过。发布状态收尾部署`dpl_CQoLqve5HjpcvNY8eYR6cZVQVtz1`上线后，23:09及23:10两次`curated_lookup`返回500。正式日志均显示索引读取成功后，在清理分页快照时HTTP连接被服务端断开（RemoteProtocolError）。因此首轮成功不能作为最终检索稳定性验收。

修复限定于远程统一检索：索引原子读取完成、结果已在内存后关闭空闲连接，下一次游标读写建立新连接。SQLite仍保留原有事务；不捕获并重放未知结果的写入。两项新增回归先在旧实现复现失败，再在修复后通过，覆盖首次检索、原游标恢复，以及服务端已接受写入但响应丢失时只尝试一次。

v1.8.52实际结果：

- 74项后端回归全部通过（102.37秒），范围为页面、统一检索、资料包、Codex同步与分页更新；五组接入交互、六组语言回归通过。
- 独立正式基线构建通过。相对v1.8.47基线共17条差异路径，其中新增本次检索修复；源包289文件、14,607,746字节，公开种子／API路由保持，排除凭据、数据库、私密材料和构建缓存。
- 修复部署`dpl_AJwRs6jmCDK6apCSPkEmTb5hvxv5`已Ready并指向正式域名。
- 正式双语For your AI／For you页面、四SVG及主JS／CSS／For you资源哈希、更新日志revision通过；health与三个MCP均返回v1.8.52／1.8.52。
- 两轮中英文共4次新检索、4次原游标恢复与4次完整档案读取全部成功；保持CW-M02、10项来源、核验日期与同一资料修订。四公开集合与发布前完整JSON逐项相等。
- 正式浏览器视觉复验仍保留前文超时边界；没有将协议检查替代四客户端聊天、真机或辅助技术验收。

发布清单及正式回执为`deployment-manifest52.json`与`production-verification52-initial.json`（忽略目录）。

提交范围独立导出后，仓库检查为161份文档、1344个本地链接、332个相对导入、24项主REQ／169项子REQ，0错误；修正原有总览对未提交样刊文件的链接，改为已存在的REQ-24状态锚点。并行日报的新编辑与私密输出保留在工作区，不纳入本次交付。初次备份为只读操作；协议检索会维护短期分页快照，公开业务内容没有因验收而变更。


发布状态最终同步部署为`dpl_22qydjTHzZahwSXEJGC4KD1WziV8`（Ready）；相对已验修复部署仅更新站内日志元数据，最终源清单289文件／14,607,756字节。北京时间23:32再次完成17项公开页面／资源检查、三个MCP版本和中英文检索→原游标恢复→完整读取，全部通过，四公开集合仍与发布前相同。最终回执为`deployment-manifest52-final.json`、`deployment-result52.json`与`production-verification52-final.json`。
