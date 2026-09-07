# 本地中文 PDF → 金额与页码来源

这是 AI-03 / A-05 的首个完整开发任务案例，配方版本 1。它接受用户自己的 PDF 文件，输出 JSON；内置演示另行生成五个合成 PDF。运行结果只覆盖指定格式，不代表任意发票识别能力。

## 输入、输出与成功判据

- 输入：有文本层、未加密的 PDF，金额行格式为 `发票金额：128.50 元`。扫描件需要另外的 OCR 步骤。
- 输出：`amount`（十进制字符串）、`currency`、`source_page`、原文 `quote`、输入 SHA-256、逐页文本与运行库版本。
- 正例：两页中文样本输出 `128.50 / CNY / 第 1 页`，原文与页码一致。
- 缺失金额返回 `not_found`，多处金额返回 `ambiguous`，均不猜测金额。
- 无文本返回 `needs_ocr_or_text_review`；演示中的空白页只检验拒绝猜测，不代表实际 OCR 验证。
- 负数、外币、千分位、多栏表格、手写或任意版式尚未支持。不得作为自动记账或付款的依据。

## 事实、设计与四条采用路径

1. **直接使用**：按 pypdf 6.17.0 的 [提取文档](https://pypdf.readthedocs.io/en/6.17.0/user/extract-text.html) 使用 `PdfReader` 与 `page.extract_text()`，取得逐页文本。该步骤不自动完成字段识别。
2. **基于开源扩展**：`page_materials` 是项目自行编写的包装层，返回页码和文本。它调用文档中的公开接口，没有修改 pypdf 上游源码；没有证据的内部扩展位置不作推荐。
3. **自行实现**：`extract_amount` 是自行编写的业务规则，输入已有的逐页文本。用 `Decimal` 保留小数精度、严格匹配一整行并处理歧义；这不等于自行实现一个 PDF 解析器。
4. **混合采用**：`process_pdf` 组合现有解析库、包装接口和业务规则，附上文件哈希与版本信息，是本例完整目标的推荐路径。

前两项库行为依据官方文档；业务规则、阈值和成功判据属于本例的设计决定。实际通过状态以运行记录为准。pypdf 的 BSD-3-Clause 许可见 [固定版本许可证](https://github.com/py-pdf/pypdf/blob/6.17.0/LICENSE)。部署及分发前按具体依赖逐项检查许可。

## 复现

在仓库根目录，使用独立的 Python 环境：

```bash
python3 -m venv /tmp/metis-pdf-env
/tmp/metis-pdf-env/bin/pip install pypdf==6.17.0 reportlab==4.5.1
/tmp/metis-pdf-env/bin/python examples/task_packets/pdf_amount.py --demo-dir /tmp/metis-pdf-demo --output /tmp/metis-pdf-demo-result.json
/tmp/metis-pdf-env/bin/python examples/task_packets/pdf_amount.py --input /tmp/metis-pdf-demo/searchable.pdf --output /tmp/metis-pdf-amount.json
```

将 `--input` 替换成自己的文件，再检查输出状态、原文和页码。脚本在本地执行，不调用模型或上传文件。JSON 包含文档原文，请自行选择保存位置。

演示产生五组 PDF/JSON 文件，检查七个判据；真实结果另存于 `docs/validation/2026-09-07-task-packet-results.json`。环境不同需重新执行，版本改变不会继承旧版本的通过状态。
