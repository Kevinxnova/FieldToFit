# 仓库文件盘点（整理前）

> 历史快照，不作为当前需求状态或操作说明。现行入口：[需求清单](../../product/requirements.md)、[文档导航](../../README.md)。主案例现为 pending，旧样例通过不代表产品价值已经验证。

日期：2026-09-07。只列项目源码、文档及配置模板，不展开依赖、缓存、数据库、凭证或 Git 内部文件。

受版本管理或拟在本轮提交的文件共 151 个。目录处理建议见 [整理方案](2026-09-07-repository-and-release-plan.md)。

这是盘点快照，不会随后续文件变化自动更新。

## 根目录

- `.dockerignore`
- `.env.example`
- `.gitignore`
- `.python-version`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `DEPLOY.md`
- `Dockerfile`
- `LICENSE`
- `README.md`
- `SECURITY.md`
- `compose.yaml`
- `pyproject.toml`
- `requirements-dev.txt`
- `requirements.txt`
- `vercel.json`

## .github

- `dependabot.yml`

## .github/workflows

- `ci.yml`

## api

- `cron.py`
- `cron_classify.py`
- `cron_daily_news.py`
- `cron_digest.py`
- `cron_knowledge.py`
- `cron_scrape.py`
- `index.py`

## backend

- `__init__.py`
- `ai_recommend.py`
- `classifier.py`
- `config.py`
- `cron_tasks.py`
- `daily_news.py`
- `mcp_stdio.py`
- `requirements.txt`
- `scheduler.py`
- `security.py`
- `translate.py`

## backend/api

- `__init__.py`
- `main.py`

## backend/db

- `__init__.py`
- `queries.py`
- `schema.sql`

## backend/dedup

- `__init__.py`
- `url_normalize.py`

## backend/email

- `__init__.py`
- `sender.py`

## backend/knowledge

- `__init__.py`
- `api.py`
- `daily.py`
- `editorial.py`
- `export.py`
- `materials.py`
- `mcp.py`
- `models.py`
- `paging.py`
- `processing.py`
- `schema.sql`
- `sources.py`
- `store.py`
- `task_plans.py`
- `tasks.py`
- `verification.py`

## backend/scrapers

- `__init__.py`
- `base.py`
- `github.py`
- `hackernews.py`
- `producthunt.py`
- `rss_news.py`

## docs

- `metis_design-v0.1.0.md`

## docs/assets

- `fieldtofit-homepage.png`

## docs/product

- `2026-09-06-goals-and-requirements.md`
- `2026-09-07-delivery.md`
- `2026-09-07-file-inventory.md`
- `2026-09-07-remaining-requirements-and-plan.md`
- `2026-09-07-repository-and-release-plan.md`
- `2026-09-07-task-packet-delivery.md`
- `2026-09-07-workspace-development.md`

## docs/superpowers/plans

- `2026-04-07-ai-daily-news.md`
- `2026-04-10-cron-split-and-monitoring.md`
- `2026-04-12-issues-summary.md`
- `2026-04-13-weekly-discoveries-v010.md`

## docs/updates

- `v0.3.0-discovery-modules.md`

## docs/validation

- `2026-09-07-mcp-results.json`
- `2026-09-07-reading-cases.md`
- `2026-09-07-runtime-results.json`
- `2026-09-07-task-packet-mcp.json`
- `2026-09-07-task-packet-results.json`

## examples/editorial

- `gpt-reviewed-batch.json`
- `load.py`

## examples/task_packets

- `pdf_amount.md`
- `pdf_amount.py`

## examples/validation

- `manifest.json`
- `mcp_client.py`
- `ml_workflows.py`
- `pdf_amount_workflow.py`
- `pdf_workflows.py`
- `requirements.txt`
- `run_suite.py`

## frontend

- `index.html`
- `package-lock.json`
- `package.json`
- `tsconfig.json`
- `vite.config.ts`

## frontend/public

- `favicon.svg`

## frontend/src

- `App.tsx`
- `i18n.ts`
- `main.tsx`
- `theme.ts`
- `vite-env.d.ts`
- `workspace.css`

## frontend/src/api

- `client.ts`
- `knowledge.ts`

## frontend/src/components

- `NewsletterPreview.tsx`
- `ScrapeHealth.tsx`
- `TakeEditor.tsx`
- `ToolCard.tsx`
- `ToolFeed.tsx`

## frontend/src/components/discover

- `CategorySection.tsx`
- `HeroCarousel.tsx`
- `SectionCarousel.tsx`
- `ToolDetail.tsx`
- `ToolRow.tsx`

## frontend/src/components/workspace

- `RelationshipEditor.tsx`
- `ResearchComparison.tsx`
- `TaskPlan.tsx`
- `UI.tsx`

## frontend/src/hooks

- `useTools.ts`

## frontend/src/pages

- `Admin.tsx`
- `Community.tsx`
- `DailyNews.tsx`
- `Discover.tsx`
- `Dossier.tsx`
- `Explore.tsx`
- `KnowledgeOps.tsx`
- `KnowledgeReading.tsx`
- `Landing.tsx`
- `TaskWorkbench.tsx`
- `WorkspacePages.tsx`

## scripts

- `backfill.py`
- `gen_daily_news.py`
- `parallel_classify.py`
- `parallel_score.py`
- `scrape.sh`
- `setup-mac.sh`
- `start-backend.sh`

## tests

- `test_daily_news_debug.py`
- `test_email_sender.py`
- `test_knowledge.py`
- `test_security.py`
- `test_task_packets.py`
- `test_translate.py`
- `test_workspace_completion.py`
