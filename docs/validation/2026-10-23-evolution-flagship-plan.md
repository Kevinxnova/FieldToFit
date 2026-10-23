# 2026-10-23 旗舰型号与三图方案：文档验证

## 授权与范围

所有者要求先完善项目总览中的具体方案，再进一步整理原始材料。本轮首先编辑FieldToFit-PM.md，登记REQ-25-21—26及页面布局、证据规则、兼容、维护与验收条件；随后继续检索并形成[15家公司矩阵及24条候选关系](../product/evolution-flagship-evidence.md)。本文件只记录本轮事实，不另维护计划。

基线提交06a02f9，v1.16.3，分支codex/fieldtofit-knowledge-workspace，开始时工作区干净。已评估自v1.16.0以来累计首页和内容变化：本批仅文档，patch v1.16.4；后续型号索引、跨图联动与比较建议minor v1.17.0，尚待单独确认。没有实施或发布新图，没有CMS、数据库、生产配置、部署或自动化变更。

## 材料核对

- GPT-6.1 Sol增补§2明确引用Astra的训练类型；只在该层级记录关联，不推定蒸馏或权重继承。
- Claude Opus 5.5自适应思考及effort文档已读正文；系统卡PDF获取失败仍记录为缺口。
- Gemini 4 Argon模型卡分别提供结构、训练与TPU／JAX／ML Pathways证据。
- GLM型号分支和前代报告分别绑定；IndexShare／IndexCache命名冲突未解决。
- Qwen Max级开放模型卡补充架构与推理控制；ERNIE 5.0报告摘要、Hy4 Preview官方平台说明和MiniMax M3.1 Flash发布日期补入矩阵。
- 矩阵覆盖15家公司检索范围，不宣称已确认各家全部最新旗舰。24条为研究候选，含正文、摘要和待核关系，均未写入正式目录。性能没有复测；多数报告未逐页完整审阅。

## 本地检查

- `.venv/bin/python scripts/maintenance/release_metadata.py --write`：通过，后端、前端package／lock、双语README与唯一CHANGELOG投影统一为1.16.4，保留未发布标记。
- `.venv/bin/python -m pytest tests/test_release_metadata.py -q`：8项通过（0.19秒）。
- `.venv/bin/python scripts/maintenance/check_repository.py`：通过，200份文档、1608处本地链接、410处相对导入；25主REQ、209子REQ、42历史锚点、91旧子项映射，0错误。
- 独立计数核对：25主REQ、209个唯一子REQ；材料矩阵15家公司、E01—E24共24条候选关系。
- 相对HEAD核对`backend/llm_evolution`、`frontend/src`、`frontend/public`：无变化；没有修改正式图谱、问题文章、前端实现或静态资源。
- `git diff --check`：通过。本批只有文档、版本元数据及自动生成日志投影，不运行前端构建、功能浏览器验收或性能实验；不将既有功能测试冒充本轮新图验收。

## 交付状态

本轮为未部署文档批次。正式站点的型号联动、双模型比较和新的旗舰覆盖图仍未实现；既有浏览器连接超时与真机／屏幕阅读器验证缺口没有因本文档而消除。不作推送、标签或部署成功声明。
