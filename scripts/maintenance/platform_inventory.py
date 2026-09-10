"""Read-only SQLite inventory and optional consistent backup before platform migration.

Requires explicit database paths; never reads .env or connects to production Turso.
"""
import argparse
import json
import sqlite3
from pathlib import Path

TABLES = ('knowledge_records', 'knowledge_evidence', 'knowledge_changes', 'knowledge_relations',
          'knowledge_platform_profiles', 'knowledge_selections', 'knowledge_publications',
          'knowledge_read_snapshots', 'knowledge_editions', 'knowledge_edition_publications')


def inspect(path, backup=None):
    path = Path(path).resolve(strict=True)
    if backup and Path(backup).resolve() == path:
        raise ValueError('Backup must use another path')
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as source:
        present = {r[0] for r in source.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        counts = {table: source.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] if table in present else None for table in TABLES}
        result = {'database':str(path), 'counts':counts, 'new_tables_present':all(t in present for t in TABLES[4:]),
                  'existing_records_are_not_auto_selected':True, 'source_modified':False}
        if backup:
            target = Path(backup).resolve()
            # Exclusive creation prevents accidentally replacing somebody's existing backup.
            with target.open('xb'):
                pass
            try:
                with sqlite3.connect(str(target)) as dest:
                    source.backup(dest)
                    integrity = dest.execute('PRAGMA integrity_check').fetchone()[0]
                    if integrity != 'ok':
                        raise ValueError('Backup integrity check failed')
                result['backup'] = {'path':str(target), 'integrity':integrity}
            except Exception:
                target.unlink(missing_ok=True)
                raise
        return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True)
    parser.add_argument('--backup', help='Optional new SQLite backup path (must not exist)')
    args=parser.parse_args()
    print(json.dumps(inspect(args.database,args.backup),ensure_ascii=False,indent=2))
