# FieldToFit project instructions

- Follow the current scope and statuses in FieldToFit-PM.md. Historical Metis plans are archival; accounts remain closed and application cases are pending.
- Follow docs/guides/releasing.md (confirmed by the owner on 2026-09-11). Every change-bearing delivery commit increments the patch version z, including content/documentation changes, and updates the single CHANGELOG and both READMEs. Multiple saves before one commit are one batch. No change means no bump.
- Before any minor y or major x increment, explain the proposed scope and impact and obtain the owner’s confirmation. Do not move or overwrite historical tags. Use fieldtofit-vX.Y.Z for release tags.
- Keep backend/__init__.py, frontend/package.json, package-lock.json and current release documentation consistent. Run scripts/maintenance/release_metadata.py --write to synchronize package versions and bilingual README highlights from the CHANGELOG. Do not add per-version release-note files. Run scripts/maintenance/check_repository.py before committing. Record actual verification, not assumed success.
- Preserve production credentials, databases and compatible public APIs. Reviewed model chart snapshots retain source URLs, configuration, units and genuine dates; daily reachability checks never automatically publish values.

- FieldToFit-PM.md is the only project-management source: REQ-1 / REQ-1-1, explicit implemented and missing behaviors, verification evidence and shipped website behavior. Do not recreate requirements.md or ROADMAP.md.
- Both local discovery and website-selected candidates require a concrete proposal and owner alignment before new website drafts or publications. The daily 08:00 local automation proposes topics and ready-to-review website copy; it does not authorize publication.
