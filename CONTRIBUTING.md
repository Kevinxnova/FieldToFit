# Contributing to FieldToFit

Thanks for helping improve FieldToFit.

## Before opening a change

1. Search existing issues and pull requests.
2. Keep the change focused; separate unrelated fixes.
3. Never add credentials, local databases, scraped production data, or logs.
4. For a security issue, follow [SECURITY.md](SECURITY.md) instead of filing a public issue.
5. Use the [current requirements](docs/product/requirements.md) and [roadmap](ROADMAP.md). Archived plans describe history, not current implementation instructions. The current scope is For you, For your AI and About. The 20 requirements have 80 subrequirements; all legacy IDs retain mappings. The product showcase case is pending, and website-generated task comparisons/plans are outside the new core scope.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env

cd frontend
npm ci
```

Preserve an existing `.env` rather than replacing it. Use placeholder credentials and a disposable local database while developing; see the [isolation instructions](docs/guides/local-development.md).

## Validation

For code changes, run the applicable checks before opening a pull request:

```bash
source .venv/bin/activate
pytest

cd frontend
npm run build
cd ..
python scripts/maintenance/check_repository.py
```

For documentation-only changes, check local links, requirement/subrequirement coverage, version wording and the diff; there is no need to rerun unrelated runtime tests. The current repository checker reports 42 legacy anchors, not the 18 current requirements. Use full `REQ-` IDs in new work and retain old links for history.

Live integration tests are opt-in because they can modify Turso data and spend
MiniMax credits.

## Pull requests

Describe the user-visible behavior, note any configuration or schema changes,
and include screenshots for UI changes. By contributing, you agree that your
work may be distributed under the repository's license.

Keep supported compatibility routes and script entry points working when moving files. Put changes in the root CHANGELOG Unreleased section and follow the [release guide](docs/releases/README.md); do not mark unverified product requirements complete based only on technical sample output.

## Versioning

Every change-bearing delivery commit increments z and updates the changelog, release notes and current version references, including documentation or content changes. Minor (y) and major (x) increments require prior owner confirmation and an explanation of scope and impact. Follow the [version policy](docs/releases/versioning.md).
