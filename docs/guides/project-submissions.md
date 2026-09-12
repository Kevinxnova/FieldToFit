# 开发者投稿项目：提交、审核与更新

网站入口：[FieldToFit 社区](https://fieldtofit.top/community#submit-project)。个人与团队都可提交已有原型、演示或代码；第三方也可以推荐。不设 Star 门槛。

## 六项投稿信息

| 信息 | 填什么 |
| --- | --- |
| 项目名称 | 公开名称 |
| 项目介绍（解决的问题、面向的人） | 用具体问题与人群说明用途；协作需求可写在这里 |
| 项目入口 | 可查看的原型、演示、仓库或产品链接 |
| 如何使用 | 最短尝试路径，必要的条件；详细说明可链接 README |
| 开放情况 | 开源、部分开源或闭源；具体许可可在使用说明中补充 |
| 作者与提交者关系 | 本人开发、团队成员或第三方推荐 |

投稿介绍下已经明确列出 GitHub Issue 和邮箱两种方式，可直接打开带六项模板的 Issue 或邮件草稿。两种方式任选其一，无需重复发送。

网页填写后生成预览，再打开预填的 GitHub Issue 或发往 fieldtofit@163.com 的邮件。用户自行确认提交；网页不会代发，也不把草稿上传到后台。可复制空白模板，复制权限不可用时提供可手动选择的文本。填写内容只在当前页面内存，离开页面不会保存草稿。

GitHub Issue 内容公开，邮件不公开。不要在公开项目介绍中放密码或私人信息。收录只整理确认后的公开项目信息，邮件全文和内部审核备注不进入代码库、网站或 MCP。

## 每周人工审核

1. 在 GitHub 和邮箱集中查看新投稿，检查是否与既有主体重复。
2. 打开项目入口，核对是否有实际成果，明确作者与提交者关系。第三方推荐保持“第三方推荐”，不能表示作者参与或背书。
3. 核对用途、公开使用步骤、开放情况及许可出处；不能验证的能力明确为作者声明或未知。未执行项目不能写成实测。
4. 必要时在原通道联系补充，给提交者确认准备公开的项目资料。确认只涉及项目公开描述，不要求披露私人联系方式。
5. 维护者按下面流程发布；每周处理节奏是运营安排，不是网站自动任务。真实首批投稿与周期记录目前待执行。

## 复用现有资料发布

v1.1.0 维护入口：内容库的持续关注/开发者投稿项目。数据库共享集合为发布权威，`backend/knowledge/content/watch.json` 保留为首次迁移基线。不建立第二套投稿数据库。新投稿选已有五类中最合适的一类，分配唯一 `CW-M/T/A/S/H` 编号，复用 name、introduction、checked_at、sources、interpretation、blocks。保持集合 reviewed_at、edition 和条目日期符合实际审核时间。

增加字段：

```json
{
  "origin": "developer_submission",
  "submission": {
    "entry_url": "https://example.com/project",
    "usage": "实际核对后的使用路径",
    "openness": "开源 / 部分开源 / 闭源中的实际情况",
    "relationship": "本人开发 / 团队成员 / 第三方推荐中的实际关系"
  },
  "submission_review": {"confirmed": true}
}
```

以上只是字段示意，不得作为真实项目发布。entry_url 使用经核对的 HTTPS 公开入口；sources 保留原始出处，coverage 仍为 link_only。介绍、步骤、协作需求放在结构化正文，未测试声明仍为 `official_materials_reviewed_not_runtime_tested`，不能将文档审核包装为运行验收。

先写 `state=draft`；核对材料与公开描述确认后才标 `published` 和 `submission_review.confirmed=true`。撤回使用 `state=withdrawn`，不复用旧 ID。发布前执行：

```bash
PYTHON_DOTENV_DISABLED=1 .venv/bin/python -m pytest tests/test_platform_watch.py -q
.venv/bin/python scripts/maintenance/check_repository.py
```

管理页先保存草稿、核对双端预览，再明确发布；无需重新部署前端。正式交付提交按[版本规则](releasing.md)递增版本并记录。禁止将私密邮件、内部备份或凭据加入公开数据；操作见[内容管理](management.md)。

## 同源展示与更新

- For you 在持续关注分类中保留完整条目，并在“开发者投稿项目”汇集投稿介绍；社区和 For your AI 提供同源入口。
- HTTP：`GET /api/v1/platform/watch?origin=developer_submission`。
- MCP：`curated_watch`，参数 `{"origin":"developer_submission"}`；可加 id 或 revision。当前没有已收录项目时 total=0、items=[]。
- 下载资料保留 origin 和修订。修订变更返回明确冲突，撤回后不继续提供旧公开条目。
- 后续在原 Issue 或邮件写项目名称、入口与变化；维护者核对后更新同一 ID。日来源检查继续按 1 天执行，人工投稿审核按周安排，二者都不自动发布未审核内容。

不需要使用者注册 FieldToFit 账户。GitHub 投稿使用其自身账号，邮箱作为另一种提交方式。
