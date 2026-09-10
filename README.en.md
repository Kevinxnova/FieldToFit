# FieldToFit

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="frontend/public/brand/logo-on-dark.svg">
  <img src="frontend/public/brand/logo-on-light.svg" alt="FieldToFit" width="600">
</picture>

**FIELD → FIT**

FieldToFit is a living AI map shared by people and AI: understand existing solutions, judge their fit, and choose the right path to adopt or build.

- **Field**: AI developments, papers, models, tools, open-source projects and development materials.
- **To**: ongoing tracking, organization, comparison, verification and selection.
- **Fit**: what truly fits the user’s task, conditions and constraints.


**For you. For your AI.**

A curated AI ecosystem resource platform: structured reading for people, detailed and traceable source material for their personal AI agents.

[中文](README.md) · [Product goals](docs/product/goals.md) · [Requirements](docs/product/requirements.md) · [Documentation](docs/README.md) · [Changelog](CHANGELOG.md) · [Roadmap](ROADMAP.md)

[![CI](https://github.com/Kevinxnova/FieldToFit/actions/workflows/ci.yml/badge.svg)](https://github.com/Kevinxnova/FieldToFit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

FieldToFit serves researchers, engineers, graduate students, students and their personal AI agents. People need clear summaries, reasons for attention and sources they can check. Their AI needs deeper materials, versions, limitations and original documents it can continue reading. Both use the same objects and evidence.

FieldToFit discovers, organizes, maintains and supplies the materials. The user's own AI combines them with the user's needs to compare, choose, design or execute.

## Product direction

**The three redesigned pages now have a working local implementation. The requirements track the complete target and remaining work.**

| Page | Purpose |
| --- | --- |
| **For you** | An edition overview and curated feed of models, tools, Agents, Skills, Harnesses and important research; structured descriptions, attention signals, documented capabilities, limitations, changes and sources |
| **For your AI** | MCP/API connection, coverage previews for the same curated collection, original materials, JSON/Markdown exports and version changes |
| **About FieldToFit** | Project purpose, the two reading modes, source and maintenance principles, status and participation; accessible from the footer and secondary menu |

Two primary working pages replace the previous domain taxonomy and separate information/resource navigation. Maintain a small, useful collection first; there is no daily publishing quota. Source checks run every **1 day**. Attention signals, public claims and observed results remain distinct. Missing or stale material stays visible. See the [page design](docs/product/pages.md) for details.

## Implementation status

The current application version is **v1.0.0**, the first FieldToFit-branded version. Deployment and ongoing operational acceptance are tracked separately; a version change does not close unfinished requirements.

| Existing foundation | Work still needed |
| --- | --- |
| Curated profiles, Harness roles, quoted facts, material manifests and hashes | More maintained selections, relationships and source status |
| Publication review, optimistic concurrency, invalidation and withdrawal | Integrated queues, real daily operation and production validation |
| 19 read-only MCP tools, including 10 curated tools; HTTP/stdio, source reading and multi-object source packages | Object relations, per-material checks and an everyday AI client workflow |
| For you, For your AI, About and compatibility redirects | Bookmarks in new details and real user validation |

The [18 requirements and 72 subrequirements](docs/product/requirements.md) specify purpose, implementation approach, existing foundations and acceptance. All 42 legacy IDs retain historical mappings; previous checks do not establish completion of the new design.

Public registration, sign-in and sync remain closed. The AI application showcase is **pending**. Existing PDF samples remain technical regressions. Website-generated comparisons, task plans and learning paths leave the new core scope; existing code and interfaces remain for compatibility.

## Updates and next steps

| Record | Status / date | Highlights |
| --- | --- | --- |
| [Public history and UI acceptance](docs/validation/2026-09-10-platform-history.md) | Unreleased · 2026-09-10 | Revision-bound public history, package continuation, preserved filters and mobile checks |
| [Source and filter checks](docs/validation/2026-09-10-platform-sources.md) | Unreleased · 2026-09-10 | Source health, historical source identity and UTC publication-date/source filters; full UI interaction pending |
| [Source package checks](docs/validation/2026-09-10-platform-bundles.md) | Unreleased · 2026-09-10 | Selected publications with stored original text, JSON/Markdown downloads, explicit gaps and continuation |
| [Edition and update checks](docs/validation/2026-09-09-platform-updates.md) | Unreleased · 2026-09-09 | Reviewed editions, archive, stable pagination, selection changes and 3 more MCP tools |
| [Platform implementation checks](docs/validation/2026-09-09-platform-foundation.md) | Unreleased · 2026-09-09 | Curated publishing, three pages, shared API/MCP reading and original text checks |
| [Platform docs P1](docs/product/goals.md) | Documentation · 2026-09-08 | New purpose, two primary pages plus About, 18/72 requirements, legacy mappings, acceptance and operations; no feature release |
| [v1.1.0-beta.2](docs/releases/v1.1.0-beta.2.md) | Development candidate · 2026-09-08 | Skill/Agent materials, capability filtering, review pagination, daily backlog tracking, transactional edits and research exports |
| [v1.1.0-beta.1](docs/releases/v1.1.0-beta.1.md) | Development candidate · 2026-09-07 | Knowledge workspace, evidence, versioned materials, MCP and repository organization |
| v1.0.0 | Historical baseline · 2026-08-30 | Initial open-source release with discovery, curation and Newsletter workflows |

Next: maintained selections and complete handoff → everyday clients, real operations and release validation. See [ROADMAP](ROADMAP.md). Software releases record requirement-level changes, checks and migration details; daily content updates are a separate process.

## Quick start

Python 3.12/3.13 and Node.js 20+ are required. Clone the development candidate branch to use this UI; the v1.0.0 tag contains the earlier workflow.

```bash
git clone --branch codex/fieldtofit-knowledge-workspace https://github.com/Kevinxnova/FieldToFit.git
cd fieldtofit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
cd frontend
npm ci
cd ..
```

Keep an existing `.env` instead of replacing it. Configure admin and cron credentials as needed. Local SQLite is the default; browsing and basic retrieval do not require a model API key.

Start the backend from the repository root:

```bash
./scripts/start-backend.sh
```

Start the frontend in another terminal:

```bash
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). A new database is empty; optionally import six source-linked samples from the activated environment at the repository root:

```bash
python -m examples.editorial.load
```

The default route is now `/for-you`; legacy Information and Resources URLs redirect with a migration notice. These old sample imports do not populate curated selections. Configuration, isolated validation and commands are documented in the [local guide](docs/guides/local-development.md).

## Current MCP and API

MCP endpoint: `http://127.0.0.1:8000/api/mcp`. The existing `/for-your-ai` page checks connectivity. The HTTP API is under `/api/v1`. Reading existing materials does not require a generation-model key. Deployments may require a separate read token.

```bash
.venv/bin/python -m backend.mcp_stdio
```

Set the client's working directory to the repository root. Configure `FIELDTOFIT_MCP_URL` and optional `FIELDTOFIT_READ_TOKEN` locally. Current tools include search, records, source excerpts, changes, sources, briefs and legacy comparison/task/research capabilities. See the [current access guide](docs/guides/ai-access.md); the [future data contract](docs/product/data-contract.md) is a design proposal.

## Maintenance and participation

[Content](docs/guides/content.md) · [Management](docs/guides/management.md) · [Deployment](DEPLOY.md) · [Verification](docs/validation/README.md) · [Architecture](docs/architecture/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)

Feedback on errors, missing original material, objects to follow and AI retrieval failures is welcome. Legacy curation and Newsletter workflows remain at `/admin/curation`. The source is licensed under [MIT](LICENSE); third-party materials retain their own attribution and applicable terms.

For the current curated pages, explicit real-source preview import, API schemas and migration boundaries, see the [platform guide](docs/guides/platform.md). Legacy sample imports do not publish curated selections.
