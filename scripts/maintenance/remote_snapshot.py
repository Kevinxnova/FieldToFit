"""Snapshot configured FieldToFit Turso into a new local SQLite file, without printing data.

Run before migrations. Copies table schemas and rows in one remote transaction,
then validates the independent local restore. Requires explicit --env-file.
"""
import argparse
import sqlite3
from pathlib import Path


def snapshot(target):
    from backend.db import get_db
    target = Path(target).resolve()
    with target.open('xb'):
        pass
    target.chmod(0o600)
    counts = {}
    try:
        with get_db() as remote, sqlite3.connect(target) as local:
            schema = remote.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
            statements=[]
            for table in schema:
                escaped='"'+table['name'].replace('"','""')+'"'
                statements.extend([('SELECT count(*) FROM '+escaped,()),('SELECT * FROM '+escaped,())])
            statements.append(("SELECT sql FROM sqlite_master WHERE type IN ('index','trigger','view') AND sql IS NOT NULL",()))
            snapshot=remote.atomic_statements(statements,read_only=True)
            for index,table in enumerate(schema):
                name = table['name']
                escaped = '"' + name.replace('"', '""') + '"'
                local.execute(table['sql'])
                expected = snapshot[index*2].fetchone()[0]
                rows = snapshot[index*2+1].fetchall()
                if len(rows) != expected:
                    raise ValueError('Incomplete table snapshot: ' + name)
                if rows:
                    local.executemany('INSERT INTO '+escaped+' VALUES('+','.join('?' for _ in rows[0])+')', [tuple(r) for r in rows])
                counts[name] = len(rows)
            for item in snapshot[-1].fetchall():
                local.execute(item[0])
            if local.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Restored database integrity failed')
        return {'path':str(target),'tables':counts,'local_restore_integrity':'ok','remote_modified':False}
    except Exception:
        target.unlink(missing_ok=True)
        raise


if __name__ == '__main__':
    import json
    from dotenv import load_dotenv
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--env-file',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    load_dotenv(a.env_file,override=True)
    print(json.dumps(snapshot(a.output),ensure_ascii=False,indent=2))
