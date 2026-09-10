"""Request-scoped batches for public publication reads over remote SQL.

Only explicitly requested rows are loaded. Publication permissions are read in the
same batch as their immutable bodies. Nothing is cached across HTTP requests.
"""
from backend.db import TursoConnection, TursoCursor
from backend.knowledge import store


class PreparedReads:
    def __init__(self, db):
        self.db = db
        self.rows = {}

    def prepare(self, statements):
        pending = list(dict.fromkeys((sql, tuple(params)) for sql, params in statements
                                     if (sql, tuple(params)) not in self.rows))
        if pending:
            results = self.db.atomic_statements(pending, read_only=True)
            for key, cursor in zip(pending, results):
                self.rows[key] = cursor.fetchall()

    def execute(self, sql, params=()):
        key = (sql, tuple(params))
        if key in self.rows:
            return TursoCursor(self.rows[key], 0, None)
        return self.db.execute(sql, params)


def prepare_publications(db, refs):
    if not isinstance(db, TursoConnection):
        return db
    cached = PreparedReads(db)
    statements = []
    for ref in refs:
        rid, revision = ref['id'], ref['revision']
        statements.extend([
            ('SELECT * FROM knowledge_records WHERE id=?', (rid,)),
            ('SELECT * FROM knowledge_selections WHERE record_id=?', (rid,)),
            ("SELECT * FROM knowledge_publications WHERE record_id=? AND seq=? AND state='published'", (rid, revision)),
            ("SELECT MAX(seq) FROM knowledge_publications WHERE record_id=? AND state='withdrawn'", (rid,)),
        ])
    cached.prepare(statements)
    objects = []
    for ref in refs:
        row = cached.execute("SELECT * FROM knowledge_publications WHERE record_id=? AND seq=? AND state='published'",
                             (ref['id'], ref['revision'])).fetchone()
        if row:
            objects.append(store.decode(row['snapshot'], {}))
    cached.prepare([('SELECT snapshot FROM knowledge_changes WHERE record_id=? AND seq<=? ORDER BY seq DESC LIMIT 1',
                     (obj['id'], obj.get('source_revision', 0))) for obj in objects if 'source_id' not in obj])
    from backend.knowledge.platform_sources import source_id
    sids = {source_id(cached, obj) for obj in objects}
    cached.prepare([(sql, (sid,)) for sid in sids for sql in (
        'SELECT id,name,enabled,status,last_attempt_at,last_success_at FROM knowledge_sources WHERE id=?',
        'SELECT * FROM knowledge_platform_material_checks WHERE source_id=?',
        "SELECT 1 FROM knowledge_platform_intake WHERE source_id=? AND state='pending' LIMIT 1",
    )])
    return cached


def prepare_sources(db, sids):
    if not isinstance(db, TursoConnection):
        return db
    cached = PreparedReads(db)
    cached.prepare([('SELECT id,name,enabled,status,last_attempt_at,last_success_at FROM knowledge_sources WHERE id=?', (sid,))
                    for sid in sids if sid])
    return cached
