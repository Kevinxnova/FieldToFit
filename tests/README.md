# 自动检查导航

| 文件 | 检查范围 |
| --- | --- |
| test_knowledge.py | 知识库、查询、权限、账户关闭、MCP 与基本任务 |
| test_workspace_completion.py | 采集进度、材料、整理、约束、编辑与任务检索 |
| test_task_packets.py | 既有任务结构、证据边界、PDF 技术回归和导出 |
| test_security.py | 旧 API 管理与定时权限、输入和跨域 |
| test_translate.py、test_email_sender.py | 翻译边界与邮件内容/发送保护 |
| test_daily_news_debug.py | 显式启用的 Turso / MiniMax 集成检查，默认跳过 |

在隔离环境运行 `pytest`。主案例 pending 不影响既有技术回归继续维护，但技术测试结果不等于产品需求验收。前端目录移动通过生产构建、相对导入检查和浏览器验证；不为简单路径移动增加只重复实现的测试。
