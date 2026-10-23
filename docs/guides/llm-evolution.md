# 大模型专题维护

范围、状态及后续需求以[REQ-25](../../FieldToFit-PM.md#req-25)为准。专题为代码内版本化内容，当前没有CMS编辑界面。新增内容、部署和自动发布授权分别处理。

## 单一内容来源

[目录](../../backend/llm_evolution/catalog.json)同时供React导入、服务端无脚本正文和只读HTTP读取。`tracks`为三主线，`routes`包含共同问题分组、节点与公司实践，`questions`为18题初始库，`sources`为共用来源。中英字段顺序固定为`[zh, en]`。节点保留`related-development`与案例`documented-use`兼容字段。新增`relations`才表达具体端点和改进／替代／组合／采用／跨主线关系；时间相邻本身不表示继承。

页面入口为`/for-you/evolution`、`/for-you/evolution/questions`及`/for-you/evolution/questions/T01`等稳定编号。HTTP只读入口为`/api/v1/platform/evolution`和`/api/v1/platform/evolution/questions/T01`，返回双语内容与来源，支持ETag条件读取，并遵循现有读取权限。此批不增加MCP工具；不能据此宣称全部MCP客户端完成专题验收。

## 一次修订

1. 在唯一PM中登记具体内容提案、影响与证据，按所有者已对齐范围编辑。
2. 核对原论文或官方披露，记录真实日期与精度：只确认年份就只写年份，维护中的项目页未标日期则留空。`checked_at`不是发布日期。
3. 保持既有节点、来源、题目ID稳定；对实质正文变化递增对应题目`revision`，更新`updated_at`与双语`change_reason`，并递增目录总修订。关系或节点实质变化也更新节点修订。
4. 同步双语叙述、机制图、算例与条件。公司标注必须绑定具体模型／项目，未知算法不推测。教学算例不作为性能实测。
5. 运行专题测试、构建和仓库检查，更新验证记录及发布元数据，遵循[发布指南](releasing.md)。不得把源站可访问性变化当作技术内容更新自动发布。

## 完整技术图谱与证据（v1.16.0）

当前目录为27路线、93节点、43关系。页面先解释三类定义，再同时展示2017—2026三张完整横向总图；不按分类折叠，不默认隐藏历史节点。`nodes.highlight`只加强完整图节点视觉权重，不控制可见性。首页使用[精选布局](../../backend/llm_evolution/home_preview.json)中的稳定ID，每图7个关键节点；React和无脚本首页共享名单，技术正文仍来自目录。`routes.highlight`保留兼容，不再决定首页自动取首尾。首页只连接目录中同时具有两个可见端点的有据关系；未显示中间节点不新增继承连线。

`tracks.definition`维护双语定义，`nodes.summary.technology`与`representative`维护“年份—技术—代表模型／项目”短标题，React、无脚本正文与只读JSON同源。代表项可为方法或项目，不将所有研究强配公司。`atlasLayout.ts`按年份分段布局、为2025保留双列；间距不表示真实时长。私有排布优先级只减少空白，不新增用户可见分类。虚线表示路线时间脉络，实线／替代虚线表示有来源的独立关系；跨图关系在详情中跳转。新增节点需复核布局、短标题溢出与来源。

每个节点包含自己的`problem/mechanism/evidence/limit`、`kind`（方法研究／型号实践／工程实现）、`references`（来源ID与对应内容）、`date_kind`与可选`formula`。`source`与`question`保留旧接口；问题链接是相关基础知识，不声称18题已穷尽全部新机制。来源的`kind`、`date`、`revised_at`和`checked_at`分别记录资料类型、首发、修订和本次核对，不相互替代。年份精度节点单列，不能默认归入上半年。

`relations`使用稳定节点ID作端点；每条含类型、双语解释和来源。`cross-track`必须跨Train／Inference／System，强调机制支撑或互补，不推断未披露公司部署。`cases.nodes`绑定确有证据的节点；空数组表示仅路线层面证据，不高亮整条路线的所有研究。

`node`直链选择并定位节点，`track`定位总图，`company`只高亮有节点级采用证据的节点。旧`period=recent`定位近期；`view`与`relation`保留链接兼容，但不再过滤完整图。全部旧节点ID有效。每图支持全图、适合阅读、缩放、滚动／拖动、缩略导航、键盘及屏幕级全屏；桌面详情为并列侧栏，手机为底部对话框。打开详情临时采用阅读视窗并保留原视图，关闭恢复；跨图跳转退出原图全屏。会话视图用新键`fieldtofit:evolution:atlas-view:v2`保存，旧开合状态不影响全部展示，题目已读键保持不变。

未完成证据核对的候选登记PM，不混入正式目录；当前Kimi K3仍属候选。修改日期或关系时同时核验原始方法与型号采用；接口继续schema_version=1，新增字段为兼容扩展。

## 首页预览（v1.16.1）

三图同屏、共用时间分段，2025占两列；桌面根据首页实际可用宽度调整列宽与卡片高度，不缩小文字。手机只设一个横向滚动区，三图同步，左侧定义保持可见；键盘可访问滚动区和所有节点。选中节点使用与完整图相同的证据组件，关闭或Esc返回原按钮；完整图定位链接保持原查询协议。首页节点图与正文数据不写入新接口，不因纯展示变化更新目录事实日期。

问题卡支持换题、手动记录、展开18题简目录及进入独立筛选目录。首页进入文章后可返回首页专题，完整图页进入后可返回完整图；相关问题之间延续该返回目标。FlashAttention卡面以显存／片上存储图解释IO，明确为机制重绘，不当作实测。

## 阅读状态

浏览器`localStorage`按稳定题目ID保存已读布尔值、所读修订和操作时间；打开页面不自动标记。新版修订大于已读修订时显示“有更新”，保留原来的已读事实，用户可确认读过新版。目录按分类、关键词和状态筛选；首页优先抽取未读／有更新题，全部读完后可复习。

同源标签通过storage事件同步。存储禁用或损坏时显示降级提示，并尽量保留当前会话记录。该功能不依赖账号、不承诺跨设备同步。全屏采用屏幕级对话框，支持Esc和焦点返回，不调用浏览器原生全屏权限。

## 本地验证

使用隔离的临时SQLite、禁用dotenv并清空Turso连接配置启动本机预览，避免连接生产。不要复制生产数据库或凭据进入测试目录。

- `PYTHON_DOTENV_DISABLED=1 .venv/bin/python -m pytest tests/test_llm_evolution.py tests/test_home_preview.py tests/test_search_pages.py -q`
- `node tests/frontend/evolution.cjs`
- `node tests/frontend/evolution-map.cjs`
- `node tests/frontend/evolution-home.cjs`
- `npm run build --prefix frontend`
- `.venv/bin/python scripts/maintenance/check_repository.py`

浏览器核对中文／英文、桌面／窄屏、深浅色、全部节点、长短标题、公司高亮、跨图定位、全屏退出、视图恢复与阅读记录。内容不能只通过结构校验就标为已审；仍需核对来源和技术表述。
