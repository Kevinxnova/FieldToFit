# Metis

**Source-grounded AI news, research and open-source resources for your next step.**

[中文](README.md) · [Documentation](docs/README.md) · [Changelog](CHANGELOG.md) · [Roadmap](ROADMAP.md)

[![CI](https://github.com/Kevinxnova/metis/actions/workflows/ci.yml/badge.svg)](https://github.com/Kevinxnova/metis/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Metis is for researchers, engineers, graduate students and students. People can review developments, compare resources and inspect sources. AI clients can query facts, read source material on demand and retrieve task context through the API or MCP. Both use the same evidence, versions and verification records.

![Metis information workspace](docs/assets/workspace-information.png)

*Current development UI with six explicitly imported local samples; source states and counts do not imply exhaustive coverage.*

## Status

This branch contains **v1.1.0-beta.1, a development candidate**, not a published stable release. v1.0.0 is the earlier open-source baseline.

- Information, resources, task context, management and read-only MCP have working foundations. Remaining gaps are recorded in the [42 requirements](docs/product/requirements.md).
- Automatic source checks run every **1 day**. Failures, backlog, stale material and unknown conditions remain visible.
- Public registration, sign-in and account sync remain closed. Local bookmarks and following are available.
- **The product showcase case is pending.** Existing technical samples remain regression material, not proof of real-world product value.

## What you can do

| Area | Current capability |
| --- | --- |
| Information | Filter events and papers; inspect explanations, briefs and original sources |
| Resources | Read model, tool, library and dataset dossiers; compare versions, adoption conditions and missing facts |
| Task workbench | Provide a goal, background and conditions; retrieve candidates, source material, adoption paths and Markdown |
| AI access | Use 9 read-only MCP tools over HTTP or stdio, sharing the same data as the web UI |
| Management | Maintain sources, facts, classifications, relationships, processing and feedback |

Documentation completeness and scoped execution results are separate. Popularity is a discovery signal, not a certification of fit or research quality.

<details>
<summary>Resources and task workbench</summary>

![Resources](docs/assets/workspace-resources.png)

![Task workbench](docs/assets/workspace-tasks.png)

</details>

## Recent updates

| Version | Status / date | Highlights |
| --- | --- | --- |
| [v1.1.0-beta.1](docs/releases/v1.1.0-beta.1.md) | Development candidate · 2026-09-07 | Knowledge workspace, versioned evidence and MCP; reorganized current/legacy code, bilingual docs, requirements and release navigation |
| v1.0.0 | Historical baseline · 2026-08-30 | First open-source release with discovery, curation and Newsletter workflows |

See [CHANGELOG](CHANGELOG.md) for changes, release notes for upgrade impact and verification, and [ROADMAP](ROADMAP.md) for planned work.

## Quick start

Python 3.12/3.13 and Node.js 20+ are required. Clone the development candidate branch to use this UI; the v1.0.0 tag contains the earlier workflow.

```bash
git clone --branch codex/metis-knowledge-workspace https://github.com/Kevinxnova/metis.git
cd metis
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

Inspect a resource dossier, review its sources and unknowns, then try task retrieval. Configuration, isolated validation and commands are documented in the [local guide](docs/guides/local-development.md).

## MCP and API

The MCP endpoint is `http://127.0.0.1:8000/api/mcp`. The Connect AI page can check the connection. Tools cover search, dossiers, source excerpts, comparison, task context, changes, sources, briefs and research materials.

The stdio bridge connects to a running backend:

```bash
.venv/bin/python -m backend.mcp_stdio
```

Set the client's working directory to the repository root. `METIS_MCP_URL` selects the endpoint and `METIS_READ_TOKEN` supplies optional read access. The HTTP API is under `/api/v1`. See the [access guide](docs/guides/ai-access.md).

## Verification and next steps

[Verification records](docs/validation/README.md) describe backend, frontend, protocol and scoped technical checks. Deeper content coverage, research comparison, learning paths, operations, container/production database validation and real-user outcomes still require work.

Current priorities are content operations, task retrieval, research material and maintenance/deployment. The replacement showcase remains pending until its goal and acceptance criteria are agreed.

## Documentation and contribution

[Deployment](DEPLOY.md) · [Management](docs/guides/management.md) · [Architecture](docs/architecture/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)

Legacy curation and Newsletter functionality remain at `/admin/curation`. Metis is licensed under the [MIT License](LICENSE). Feedback describing actual tasks, missing sources and failures is welcome.
