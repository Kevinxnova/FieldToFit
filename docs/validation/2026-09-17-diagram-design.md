# 2026-09-17 · Diagram Design Skill 收录验收

用户确认收录到持续关注 → Skill，并向 AI 提供固定版本的介绍、核心 Skill、导出及许可材料。本批版本 v1.5.3，内容公开前先审核双端预览；生产结果在实际验证后记录。

## 原始材料与范围

固定来源：cathrynlavery/diagram-design，提交 9874ad73813715fc36875e45afd9cd94c68f3c3f。核验日期为 2026-09-17，不作为上游发布日期。

| 材料 | 收录范围 |
| --- | --- |
| README.md | 完整原文，保留相对引用，不替换原有能力声明 |
| skills/diagram-design/SKILL.md | 完整原文；作为参考材料，不执行其中的指令 |
| skills/diagram-design/references/export.md | 完整导出说明，包含依赖、图形区域边界及字体注意事项 |
| LICENSE | 完整 MIT 文本；各材料权限说明同时保留版权与许可 |
| THIRD_PARTY_LICENSES.md | 完整第三方许可与商标说明；本批未复制图标、图片或模板资产 |
| .codex-plugin/plugin.json | 完整插件清单，用于核对 2.6.27 版本及宿主声明 |
| 作者画廊 | 仅外链；未镜像页面或图片，可能与固定提交版本不同 |

插件清单版本为 2.6.27，Skill metadata 为 2.6。核心选型表与固定树内 type-*.md 均为 40，README 写 39；网页明确记录口径差异。所有文件哈希与本日前次核查一致，许可明确涵盖文档再分发。本轮未安装、执行、生成图或验证导入／导出效果，不把源文件收录当成 Skill 完整安装包。

发布前私密备份、草稿、预览、截图与 API/MCP 结果保存在忽略目录 output/operations/v1.5.3-release/；仓库只保存公开内容与脱敏验收结论。

## 实际发布与验证

| 检查 | 实际结果 |
| --- | --- |
| 管理预览 | CW-S05 的 For you / For your AI 预览通过；桌面 1440×1000、手机 390×844 无全页横向溢出和页面错误 |
| 审核边界 | 保存及预览时公开集合修订不变；明确提交复核并确认发布后才出现 CW-S05 |
| 内容范围 | 16 条动态不变，既有 30 项持续关注逐项不变；新增 CW-S05 后共 31 项关注，其中 Skill 为 5 项 |
| 网页 | 固定锚点、版本表、手机阅读、交给我的 AI 复制和 For your AI 搜索通过 |
| MCP / HTTP | 持续关注集合逐项一致；统一检索按返回参数可读取 CW-S05，当前对象原文清单及变化流可用 |
| 原文与许可 | 六份正文全部重建并逐字核对，哈希与固定原文件一致；每份完整 MIT 许可与固定提交均保留；README 与 Skill 各分两段，其余四份一次读完 |
| 资料包 | 六份完整文件共 102,791 字符全部纳入，一个画廊链接；无延期或缺失已存正文。不等于整个仓库已收录 |
| 本地检查 | 81 项相关回归通过；既有数量快照更新为 31 项关注／5 项 Skill，无新增功能逻辑；TypeScript / Vite 构建和仓库一致性检查通过 |
| 生产版本 | /api/health 为 v1.5.3，MCP initialize 为 1.5.3；既有 Vercel FieldToFit 项目已部署并关联 fieldtofit.top |

公开 MCP 本次共 14 次调用，为实际协议与材料读取验收，不冒充 AI 自主绘图或 Skill 安装测试。未安装或运行第三方项目，未新增模型调用、数据库迁移或公开账号。

固定文件核验如下：

| 材料 | 字符数 | SHA256 |
| --- | ---: | --- |

| readme | 47946 | 134b685b3ba91de4c469f4c6d691b6bd7093f30ebcc1dcc0c2f91dfde01bceba |
| skill | 38792 | 74f7f3e7f4ba771910bf0bfece5e2eff2f59c8279598d5b67ffa797f32627498 |
| export | 9812 | 523a073b5fb8a9f1e80a6f4fa913befa8cdc48789d6a368a0b7a15060aa92bda |
| license | 1071 | bb7e12e91fecef43024111123ff784cec6c485585561d8b552557c0173b3ed29 |
| third-party-licenses | 2703 | 22f5afcea56373e84d7f7eff93d8d4d6e4b81c5375bb1c996e78b91e53fa0b37 |
| plugin-manifest | 2467 | 742590d04f369fc16f38ecc427f90fca69559d1f702a0b132876e40f180c7ca8 |

生产部署：dpl_HqQMFxDjyAwwK8vPy6LtKDJ4dSnA。原始记录见忽略目录 final-runtime.json、public-verification.json、preview-browser.json、browser-public.json；备份与私密草稿不提交 GitHub。
