# 脚本导航

| 类别 | 实际实现 | 保留的原入口 |
| --- | --- | --- |
| 本机安装 | setup/macos.sh | setup-mac.sh |
| 后端启动 | runtime/start-backend.sh | start-backend.sh |
| 一次日采集 | runtime/collect.sh | scrape.sh |
| 旧工具评分/介绍补齐 | maintenance/legacy/backfill.py | backfill.py |
| 旧工具并发评分 | maintenance/legacy/parallel_score.py | parallel_score.py |
| 旧工具重分类 | maintenance/legacy/parallel_classify.py | parallel_classify.py |
| 旧日报生成 | maintenance/legacy/gen_daily_news.py | gen_daily_news.py |
| 目录与版本检查 | maintenance/check_repository.py | 新增维护入口 |

所有原入口转交到分组实现并保留参数。当前知识库日流程也可直接使用 `python -m backend.scheduler`；旧 maintenance/legacy 脚本可能读写实际数据库并调用模型，整理时没有执行这些生产维护任务。

启动和采集脚本在 `PYTHON_DOTENV_DISABLED=1` 时不载入 `.env`，方便隔离验证。macOS 安装脚本会写入本机 launchd 服务配置，普通开发无需运行它。
