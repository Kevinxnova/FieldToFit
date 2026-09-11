# FieldToFit project instructions

- Follow the current scope and statuses in docs/product/requirements.md. Historical Metis plans are archival; accounts remain closed and application cases are pending.
- Follow docs/releases/versioning.md (confirmed by the owner on 2026-09-11). Every change-bearing delivery commit increments the patch version z, including content/documentation changes, and updates the changelog/release/current documentation. Multiple saves before one commit are one batch. No change means no bump.
- Before any minor y or major x increment, explain the proposed scope and impact and obtain the owner’s confirmation. Do not move or overwrite historical tags. Use fieldtofit-vX.Y.Z for release tags.
- Keep backend/__init__.py, frontend/package.json, package-lock.json and current release documentation consistent. Run scripts/maintenance/check_repository.py before committing. Record actual verification, not assumed success.
- Preserve production credentials, databases and compatible public APIs. Reviewed model chart snapshots retain source URLs, configuration, units and genuine dates; daily reachability checks never automatically publish values.
