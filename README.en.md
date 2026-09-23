# FieldToFit

[中文](README.md) | [English](README.en.md)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="frontend/public/brand/logo-horizontal-paper.svg">
  <img src="frontend/public/brand/logo-horizontal-ink.svg" alt="FieldToFit" width="600">
</picture>

**FIELD → FIT**

**FieldToFit is a living AI map shared by people and their AI: understand existing approaches, assess fit, and choose how to adopt and build.**

- **Field:** the AI landscape of developments, papers, models, tools, open-source projects and developer materials.
- **To:** continuous tracking, organization, comparison, verification and selection.
- **Fit:** understanding what fits a user's task, conditions and constraints.

[Website](https://fieldtofit.top) · [For you](https://fieldtofit.top/for-you) · [For your AI](https://fieldtofit.top/for-your-ai) · [FieldToFit Community](https://fieldtofit.top/community)

<!-- section:overview -->
## What FieldToFit offers

For researchers, engineers, graduate students, students and AI application developers. The platform maintains sourced materials; you and your own AI use them to decide what to adopt and build.

| Entry | What it provides | Where to start |
| --- | --- | --- |
| For you | AA / Arena capability-and-price charts, recent developments, and ongoing coverage of models, tools, Agents, Skills and Harnesses | Read recent changes, then follow the contents to projects, version tables, editorial notes and sources |
| For your AI | The same published materials through MCP / API, source-text continuation, revision history and bundles | Connect your AI using the MCP address, or download materials to give it |
| FieldToFit Community | Community purpose, developer submissions and ways to contribute | Submit a project, recommend or correct resources, or help with development |

Sources are checked every **1 day**. Meaningful changes are prepared, reviewed and published for people and AI. Facts, source claims, editorial opinions and tested results stay distinct, with unknowns stated. Registration and synchronization remain unavailable; application cases are on hold.

<!-- section:release -->
## Current version and release highlights

<!-- current-version:start -->
**Current source version: [v1.5.13](CHANGELOG.md#v1.5.13)** · [fieldtofit-v1.5.13](https://github.com/Kevinxnova/FieldToFit/tree/fieldtofit-v1.5.13)
<!-- current-version:end -->

Source and deployed versions are verified separately; see this release's [validation and deployment evidence](docs/validation/README.md) for website status.

<!-- latest-summary:start -->
- Include v1.5.12's crawlable main pages, published detail URLs, page metadata and automatic sitemap while preserving existing titles, introductions and body copy.
- Fix the Vercel upload exclusion to omit only root maintenance scripts and retain the frontend script required to generate the search HTML shell; permanently redirect the root and index.html to For you before static-file handling.
- Preserve long-page links, public API/MCP and cumulative visits. Production verification passed for all 65 pages, 40 browser checks and health/MCP versions; webmaster verification and search submission remain pending.
<!-- latest-summary:end -->

[Full changelog](CHANGELOG.md) · [Project management: plans, development, verification and deployment](FieldToFit-PM.md)

<!-- section:ai -->
## Connect your AI

Public read-only MCP address:

```text
https://fieldtofit.top/api/mcp/curated
```

Add this address to an AI client that supports remote HTTP MCP. Ask your AI to retrieve relevant materials, sources, versions and known limitations, then continue with your task.

The live `curated_lookup` tool lets your AI discover developments, ongoing-watch profiles and permitted stored text within the same MCP service, with exact reading arguments and shared search previews on For your AI. Available since v1.5.0; check `tools/list` for live capabilities.

No website account is required. For client support and configuration, see [For your AI](https://fieldtofit.top/for-your-ai) and the [connection guide](docs/guides/ai-access.md). Protocol checks do not establish that every client has been tested in daily use.

<!-- section:community -->
## FieldToFit Community

FieldToFit is gradually building a community around AI applications and a continuously maintained, traceable **AI Application Database** that both people and AI can use.

We organize noteworthy models, tools, development experience and developer-submitted projects so existing work is easier to discover, understand and adopt. Submit projects, recommend resources, contribute materials, or help with testing, documentation and development. Build something meaningful together.

### Developer-submitted projects

**Let more people discover your project.** Individuals and teams can submit AI applications, tools and open-source projects with a viewable prototype, demo or code and a clear explanation of the problem they solve. Include any need for testers, development partners or documentation contributors.

Submit through a [GitHub Issue](https://github.com/Kevinxnova/FieldToFit/issues/new) or [fieldtofit@163.com](mailto:fieldtofit@163.com) with six fields: **project name, introduction (problem and audience), project URL, how to use, openness, and your relationship to the author**.

Maintainers plan to review submissions weekly; submission does not mean automatic inclusion. GitHub issues are public; emails are not directly published. Confirmed project materials are reviewed and shared with For you and For your AI. The [community page](https://fieldtofit.top/community#submit-project) can prepare your submission draft.

### Take part

- [Submit a developer project](https://fieldtofit.top/community#submit-project): share your work and find users and collaborators.
- [Recommend resources or report errors](https://fieldtofit.top/feedback): contribute materials and improve accuracy.
- [Contribute to FieldToFit](CONTRIBUTING.md): start with curation, tests, documentation or features.

<!-- section:local -->
## Run locally

Requirements: Python 3.12 / 3.13 and Node.js 20+.

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

Preserve an existing `.env`. SQLite is the default; basic browsing needs no model-service credentials. Start the backend and frontend in separate terminals:

```bash
./scripts/start-backend.sh
```

```bash
cd frontend
npm run dev
```

Open [localhost:5173/for-you](http://localhost:5173/for-you). A new database starts empty; see the [platform guide](docs/guides/platform.md) for import and review. Full functionality requires the backend; opening an HTML file directly is insufficient.

<!-- section:docs -->
## Documentation, contributions and license

[Documentation](docs/README.md) · [Requirements](FieldToFit-PM.md) · [Content management](docs/guides/management.md) · [Deployment](docs/guides/deployment.md) · [Release policy](docs/guides/releasing.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)

Source code is [MIT licensed](LICENSE). Third-party materials retain their original terms. The [brand guide](docs/guides/brand-assets.md) lists the public image inventory. Historical Metis materials are kept in the [changelog appendix](CHANGELOG.md#附录metis-历史更新记录) and [archive](docs/archive/README.md).
