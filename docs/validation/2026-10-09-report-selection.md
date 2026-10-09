# 技术报告精选&分析栏目命名与取材核对

批次：v1.8.18，2026-10-09。用户授权栏目改名；a16z内容要求检索、整理并对齐。本批不改数据库、公开报告及日期，不填新报告网站草稿。

## 取材核对

- [a16z Top 100第7版](https://a16z.com/100-gen-ai-apps-7/)：作者Olivia Moore，页面明确2026-10-05；读取核心五节与榜单方法。访问为Similarweb月访问、移动为Sensor Tower月活；新增YipitData美国消费者卡／电子收据面板，不是公司总收入。
- [a16z State of Markets II](https://a16z.com/state-of-markets-ii/)：作者David George，页面明确2026-09-30；[官方90页PDF](https://a16z.com/state-of-markets-report-2)，36036028字节。完整渲染并检查第27–39页中的相关图表，保留原页、图注、来源与日期。第27页69%与2%为S&P500部署／持续指标披露，第33页8.3倍为OpenAI企业客户输出token使用强度，第35页为OpenRouter7日平均token及缓存，第38页2.2%为PNC家庭付费口径，截至2026年4月，不能当作今天所有AI用户比例。
- [OpenRouter Cache is Crucial](https://openrouter.ai/data/newsletter/cache-is-crucial)：2026-10-08，Peter Walker。9月末agentic API key周token约为human的7倍；9月缓存prompt占全部agent token近90%。另定义cache rate为cached prompt / total prompt，两个分母不能混用。图表排除reseller，API key按月根据行为分类，不直接统计人数／ROI。
- 配图与新内容为待对齐提案。a16z PDF版权页标为all rights reserved，不能宣称CC BY 4.0；后续核实复用依据或使用原页入口／明确标注的本站数据重绘。

## 实际验证

本地实际通过：tests/test_technical_maps.py与tests/test_map_reading.py共33项，15.29s；TypeScript／Vite正式构建通过，原有大块体积提示仍存在。真实隔离浏览器在1440／390／320px × 中英文六组检查：首页栏目、目录真实点击、索引／网页标题、既有四观点正文、AI入口及无溢出；另验手机后台显示名、禁用脚本时的首页与索引标题，页面错误0。已实际检查1440px中文及320px中英文截图，标题自然换行、入口可读。首次检查误选正文与折叠历史的两份同名结论，限定当前正文后重跑六组全部通过，未改产品行为。

release_metadata.py同步前后端版本和双语README；check_repository.py结果为v1.8.18、131份文档、1090个本地链接、269个前端相对导入、22项主REQ／141项子REQ、42个历史锚点／91个旧子项映射，错误0；git diff --check通过。

正式部署dpl_7Xs5KTqGff9DwqzLmXnD8uSZsoTk状态READY，fieldtofit.top别名已生效；health为v1.8.18，通用／精选／Codex三个MCP实际均为1.8.18。发布前后news（103条）、watch（49项）、model-landscape与maps（2个报告入口）完整投影逐字段一致；HTTP／MCP报告内容一致。首页及索引无脚本标题、两份既有报告canonical／no-store与四观点正文保持；正式JS index-Byhl8Sw8.js及CSS index-ogfXeepu.css逐字节等于本地构建。

正式浏览器1440／390／320px × 中英文六组全部通过：首页、目录真实点击、索引／网页标题、既有四观点正文、AI入口和无溢出；禁用脚本首页／索引标题通过，页面错误0。已实际查看320px中文正式截图，标题和入口清楚。本批临时测试服务已关闭。研究候选没有进入网站草稿／公开集合。
