# FieldToFit

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="frontend/public/brand/logo-horizontal-paper.svg">
  <img src="frontend/public/brand/logo-horizontal-ink.svg" alt="FieldToFit" width="600">
</picture>

**FIELD → FIT**

- **Field:** the AI landscape of developments, papers, models, tools, open-source projects and developer materials.
- **To:** continuous tracking, organization, comparison, verification and selection.
- **Fit:** understanding what fits a user's task, conditions and constraints.

**FieldToFit is a living AI map shared by people and their AI: understand existing approaches, assess fit, and choose how to adopt and build.**

[Website](https://fieldtofit.top) · [For you](https://fieldtofit.top/for-you) · [For your AI](https://fieldtofit.top/for-your-ai) · [中文](README.md)

The platform maintains sourced materials for researchers, engineers and students. People and their own AI use those materials to make task-specific decisions.

## Current release

Ongoing-watch CW1 adds 27 profiles across model families, tools, agents, Skill collections and harnesses. Version tables, editorial notes and sources are shared with `curated_watch`; 12 curated MCP tools are available. [Validation and deployment status](docs/validation/2026-09-11-continuous-watch.md).

**Current version: v1.1.0.** [Release and deployment status](docs/releases/v1.1.0.md). A unified management workspace connects daily discovery, private drafts, human/AI previews and explicit publication. News, ongoing resources and AA/Arena charts share database-backed releases. Existing content and public MCP contracts are preserved. [Management guide](docs/guides/management.md).

The initial **v1.0.0** was verified on the public deployment on September 10, 2026: 27 published curated objects and 10 curated MCP tools. [Deployment evidence](docs/validation/2026-09-10-fieldtofit-brand.md).

| Entry | Available now | Next work |
| --- | --- | --- |
| For you | 10 developments, five highlights, resource dossiers and a responsive table of contents | Additional source materials and linked news/dossier identities |
| For your AI | The same published news and dossiers through MCP/API, paged source text, revisions and bundles | Linked organizations, product families, versions and events; clearly attributed source claims and editorial comments |
| About | Purpose, reading methods, maintenance principles and project status | Updated content scope and a supporting watchlist/source table |

Checks run every **1 day**; publication depends on meaningful, reviewed changes. Accounts remain unavailable; application cases are pending. Production maintenance writes/recovery, three real daily cycles, everyday AI-client use and target-user acceptance remain open.

## Connect your AI

Public read-only MCP: [https://fieldtofit.top/api/mcp/curated](https://fieldtofit.top/api/mcp/curated).

Use a client supporting remote HTTP MCP. See [connection instructions](docs/guides/ai-access.md). The updated curated endpoint exposes 12 tools including curated_news and curated_watch; the older `/api/mcp` retains 21 tools for compatibility. Successful protocol checks do not establish compatibility with every client.

## Latest changes and planning

- September 11: current documentation reorganized around FieldToFit; Metis history archived; only five public website brand images retained; P3 requirements documented. The deployed and publicly verified reading update adds 10 developments, point-by-point notes, two content sections and a responsive table of contents. See [validation](docs/validation/2026-09-11-reading.md).
- September 10: [FieldToFit v1.0.0](docs/releases/v1.0.0.md), branding, domain and public read validation.

Track [19 requirements and 76 subrequirements](docs/product/requirements.md), the [roadmap](ROADMAP.md) and [changelog](CHANGELOG.md). Historical Metis records are in the changelog appendix and archive.

Future release tags use the `fieldtofit-v1.0.0` convention while the application displays its current version. The existing `v1.0.0` tag belongs to Metis and keeps its original target. Content revision IDs remain available for traceability; every delivery commit also increments the application patch version.

## Run locally

Python 3.12/3.13 and Node.js 20+:

```bash
git clone https://github.com/Kevinxnova/FieldToFit.git fieldtofit
cd fieldtofit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
cd frontend
npm ci
cd ..
```

Preserve an existing `.env`. SQLite is the local default; basic reading needs no model credentials. Start the backend and frontend in separate terminals:

```bash
./scripts/start-backend.sh
```

```bash
cd frontend
npm run dev
```

Open [localhost:5173/for-you](http://localhost:5173/for-you). A new database starts empty; see the [platform guide](docs/guides/platform.md) for isolated previews and publication. Opening an HTML file directly is insufficient.

## Documentation and contributions

[Documentation](docs/README.md) · [Deployment](docs/guides/deployment.md) · [Content maintenance](docs/guides/content.md) · [Repository structure](docs/architecture/repository.md) · [Public brand assets](docs/guides/brand-assets.md) · [Contributing](CONTRIBUTING.md)

Source code is [MIT licensed](LICENSE). Third-party materials retain their own terms. See the brand guide for the public asset inventory. Report factual errors, missing materials and AI retrieval issues through the repository.

Every change-bearing delivery commit increments the patch version, including content and documentation. Minor and major changes require the owner’s prior confirmation. See [version policy](docs/releases/versioning.md).

The Company flagships filter uses a reviewed 11-company selection: 11 AA points and 8 Arena points, with explicit missing-data notices. Selection persists across source tabs and shared URLs.

## Community and developer projects

[FieldToFit Community](https://fieldtofit.top/community) welcomes individual and team projects. Prepare six fields, then send through GitHub or fieldtofit@163.com. The website generates drafts; you confirm sending. Submissions are reviewed weekly and published profiles are shared with For you and curated_watch using origin=developer_submission. No submissions have been published yet. See the [review workflow](docs/guides/project-submissions.md).
