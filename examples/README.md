# 样本与技术验证

**主案例 pending。** 本目录已有样本用于资料导入或技术检查，不代表已验证产品价值，也不是新主案例的实施安排。

| 目录 | 内容 | 运行方式 |
| --- | --- | --- |
| editorial | 六条有短引用的 GPT 整理材料 | 在配置指定的数据库中显式运行 `python -m examples.editorial.load` |
| task_packets | 既有 PDF 金额规则和文件输入示例 | 见 [技术样例说明](task_packets/pdf_amount.md)；仅作回归材料 |
| validation | 维护者审核的九项技术运行检查与 MCP 客户端 | 安装可选依赖后按下面执行 |

在隔离数据目录中导入样本，再运行：

```bash
pip install -r examples/validation/requirements.txt
python -m examples.validation.run_suite --output /tmp/fieldtofit-runtime-results.json
pip install 'mcp>=2.1.1,<3'
python -m examples.validation.mcp_client /tmp/fieldtofit-mcp-results.json
```

MCP 脚本要求本地后端已启动，通过 `FIELDTOFIT_MCP_URL` 可选择地址。运行清单会核对实际安装的资源版本；版本不匹配会失败，不会继承旧结果。

测试脚本包含合成数据和小规模教学实验，不代表任意真实文件、完整论文复现或所有模型能力。结果以 [验证索引](../docs/validation/README.md) 中记录的环境、版本和范围为准。

## Skill / Agent 读取验收

公开来源收录后，运行 `python examples/validation/resource_client.py`，使用官方 MCP SDK 经 HTTP / stdio 验证 Skill 筛选、固定版本原文和带来源任务导出。可通过 `FIELDTOFIT_MCP_URL` 指定已运行的服务；不安装或执行仓库中的 Skill。
