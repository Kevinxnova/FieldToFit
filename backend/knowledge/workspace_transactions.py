"""Optimistic remote writes, committed in one server-side transaction.

Turso interactive transactions expire after five seconds. Read and validate without
holding a transaction open across regional roundtrips, then assert every observed
row set again and apply all writes atomically. No ambiguous commit is retried.
"""
from contextlib import contextmanager
import json
from backend.db import get_db, TursoConnection, TursoCursor
from backend.knowledge.platform import PlatformError


class GuardedWrites:
    def __init__(self, db):
        self.db = db
        self.reads = []
        self.writes = []

    def execute(self, sql, params=()):
        if sql.lstrip().upper().startswith(('SELECT', 'WITH')):
            if self.writes:
                raise RuntimeError('Workspace transactions require reads before buffered writes')
            cursor = self.db.execute(sql, params)
            rows = cursor.fetchall()
            self.reads.append((sql, tuple(params), rows))
            return TursoCursor(rows, 0, None)
        self.writes.append((sql, tuple(params)))
        return TursoCursor([], 0, None)

    def commit(self):
        if not self.writes:
            return
        statements = [('CREATE TEMP TABLE workspace_guard (n INTEGER CONSTRAINT workspace_snapshot_unchanged CHECK(n=0))', ())]
        for sql, params, rows in self.reads:
            # Compare typed row values, not JSON string formatting. The observed
            # queries include unique identities (or a single aggregate row).
            if not rows:
                statements.append(('INSERT INTO workspace_guard SELECT count(*) FROM (' + sql + ')', params))
                continue
            keys = list(rows[0].keys())
            columns = ','.join('"' + k.replace('"', '""') + '"' for k in keys)
            expected_columns = ','.join("json_extract(value,'$[" + str(i) + "]')" for i in range(len(keys)))
            expected = json.dumps([[r[k] for k in keys] for r in rows], ensure_ascii=False, allow_nan=False)
            guard = ('INSERT INTO workspace_guard SELECT CASE WHEN '
                     '(SELECT count(*) FROM (' + sql + '))=? AND NOT EXISTS('
                     'SELECT ' + columns + ' FROM (' + sql + ') EXCEPT SELECT ' + expected_columns +
                     ' FROM json_each(?)) THEN 0 ELSE 1 END')
            statements.append((guard, (*params, len(rows), *params, expected)))
        statements.extend(self.writes)
        try:
            self.db.atomic_statements(statements)
        except Exception as exc:
            if 'workspace_snapshot_unchanged' in str(exc):
                raise PlatformError('内容或来源在操作期间发生变化，请重新读取并预览', 'workspace_conflict', 409) from exc
            raise


@contextmanager
def editorial_transaction():
    with get_db() as db:
        if isinstance(db, TursoConnection):
            buffered = GuardedWrites(db)
            yield buffered
            buffered.commit()
        else:
            db.execute('BEGIN IMMEDIATE')
            yield db
