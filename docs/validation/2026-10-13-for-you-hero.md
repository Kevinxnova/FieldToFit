# For you沉浸首屏开发与发布验证

2026-10-13，Asia/Shanghai；源码批次v1.8.47，对应[REQ-6-23／24](../../FieldToFit-PM.md#for-you-hero-proposal)。所有者确认新版视觉并授权开发、验证后发布；删除交互提示与播放按钮，默认持续运动；第二项确认为无补充。

## 实现范围

正式ForYouHero、独立WebGL场景／着色器／小型球面流体、双语同源导读、按容器宽度响应式布局；原三个锚点和取消我关注的行为保留。原参考纹理来源／哈希清单位于[公开资源目录](../../frontend/public/assets/for-you-scene/sources.json)，静态回退由同一渲染器实际画面截取，未包含网页文案。场景资源总计764,756字节，独立动画模块构建约17KB；图片和模块失败时阅读入口仍可用。无API、迁移、生产内容或调度改动。

## 本地实际验证

- TypeScript及Vite正式构建通过；现有主包大于500KB提示保留，本次动画已拆为独立模块，不把警告写成失败或声称主包已优化。
- `node tests/frontend/for-you-scene.cjs`通过三组生命周期／流体检查：默认动画及输入染色；减少动态效果、后台、离屏与恢复；上下文丢失／恢复；GPU、监听、观察器清理；卸载后图片回调和图片失败；跨球面接缝的流体衰减。假时钟首次未递增导致断言失败，修正测试时钟后通过，没有据此更改真实动画逻辑。
- `PYTHON_DOTENV_DISABLED=1 .venv/bin/python -m pytest tests/test_search_pages.py tests/test_model_landscape.py tests/test_watch_reading.py tests/test_hot_cards.py -q`：75项通过，73.61秒。使用隔离SQLite；未访问生产数据库。
- 最终标题分行调整后独立复验`tests/test_search_pages.py`：17项通过，70.50秒；属于同组复验，不与前述75项相加。
- 浏览器使用127.0.0.1:18146与独立SQLite副本，关闭统计；生产构建资源实际渲染成功。中英、浅／深色，320／390／736／1024／1440px已检查；横幅宽度等于滚动宽度，文字未截断，画面无提示和播放控件。
- 736px首次检查发现侧栏导致实际横幅仅511px、场景纵向拉伸；修为容器查询并保证背景覆盖后复验通过。320px标题按语义分行，英文允许自然换行。
- 英文我关注的切为选中后点击三个首屏入口，均恢复全部内容；URL锚点和焦点分别为model-landscape／recent-news／resource-dossiers，标题距视口顶部约110px，不被固定导航遮挡。
- 鼠标进入／点击球体出现染色与平台能量波；键盘Enter触发同一按钮。进入For your AI后场景数为0，返回For you后WebGL2重新就绪；控制台无错误／警告。连续原生坐标悬停路径未获得可靠浏览器回执，使用实际进入／点击及流体输入测试确认核心机制，不声称完整轨迹或真机手势通过。
- 静态图实际加载宽1100px；无WebGL、资源失败、减少动态效果与后台行为由生命周期测试覆盖，未冒充真实低端设备或系统偏好设置验收。

## 发布前数据与范围

已只读记录正式v1.8.42及news／watch／maps／model-landscape完整公开响应，保存于忽略的output/operations/for-you-hero-20261013。生产数据库82表原子备份完成，独立SQLite完整性为ok，生产未修改。发布采用实际v1.8.42授权部署目录作为基线，仅替换本次页面、素材、SEO文案及版本元数据；不顺带发布并行来源种子或日报功能。

## 正式部署与实际核对

2026-10-13已在原Vercel项目部署v1.8.47并绑定fieldtofit.top；首轮部署ID为`dpl_5ZydaVaiCpVZnxmcvkTrR26JPeFo`，发布状态元数据收尾后的最终部署为`dpl_GWdXwSyTdbidR6rHTSwrzSCzKQ33`，均为READY。正式清单281文件、约14.56MB，仅16条路径与已验v1.8.42部署基线不同；最后一轮仅更新站内日志数据，前端构建哈希未变化。API与数据库种子逐文件保持，凭据、SQLite、私密output、依赖及缓存排除。

- `/api/health`与普通／curated／codex三个MCP的initialize实际版本均为1.8.47；MCP初次测试遗漏协议要求的Accept头得到406，补齐后全部通过，未修改应用接口。
- `/for-you`和`/en/for-you`均返回200，标题、短导读、canonical及双语服务端正文已核对；`/api/changelog`实际当前版本为1.8.47。
- news／watch／maps／model-landscape四个完整公开JSON与发布前逐对象一致；场景city／surface／geometry／poster四张图片线上字节哈希与本地清单一致。
- 最终部署于北京时间18:45完成公开只读复验：上述项目仍通过；另核对主JS、首屏独立JS、主CSS线上字节哈希全部等于本地已验构建，站内日志revision与生成源一致。
- 正式浏览器页已进入正确URL并返回页面标题，但导航、DOM与截图请求连续超时；恢复连接后本地同一正式构建截图正常。未声称正式站视觉或真实手机性能复验通过；最终本地截图保存于忽略目录`output/operations/for-you-hero-20261013/local-final.png`。
- 发布日期与标签说明收尾仍属于同一v1.8.47批次。验收回执、部署清单及后续正式发布回执保存在忽略的`output/operations/for-you-hero-20261013`；源码与GitHub Release以`fieldtofit-v1.8.47`标签为准。
- 提交前仓库检查：版本1.8.47，160份文档、1310个本地链接、322个相对导入、24主REQ／166子REQ，0错误；`git diff --check`通过。远端main及工作分支仍为已纳入的v1.8.42，采用保留历史的快进发布，不移动历史标签。
