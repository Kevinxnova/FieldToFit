"""Database layer. Uses Turso HTTP API when deployed, local SQLite for dev."""

import os
import ssl
import sqlite3
import json
import urllib.request
import urllib.error
from urllib.parse import urlsplit
import certifi
from pathlib import Path
from contextlib import contextmanager
from backend.config import DATA_DIR

_SSL_CTX = ssl.create_default_context(cafile=certifi.where())

TURSO_URL = os.getenv("TURSO_DATABASE_URL", "").strip()
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "").strip()


def _use_turso() -> bool:
    return bool(TURSO_URL and TURSO_TOKEN)


def _turso_http_url() -> str:
    url = TURSO_URL
    if url.startswith("libsql://"):
        url = "https://" + url[len("libsql://"):]
    return url


class TursoRow:
    """sqlite3.Row-compatible wrapper."""
    def __init__(self, columns: list[str], values: list):
        self._data = dict(zip(columns, values))

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self._data.values())[key]
        return self._data[key]

    def keys(self):
        return self._data.keys()


class TursoConnection:
    """sqlite3-compatible connection using Turso HTTP API via urllib."""

    def __init__(self):
        self._base = _turso_http_url().rstrip('/')
        self._token = TURSO_TOKEN
        self.row_factory = None
        self._transaction = False
        self._baton = None
        self._broken = False

    def _post(self, payload: dict) -> dict:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base}/v2/pipeline",
            data=data,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30, context=_SSL_CTX) as resp:
            return json.loads(resp.read().decode("utf-8"))

    @staticmethod
    def _statement(sql, params):
        args = []
        for p in params:
            if p is None:
                args.append({"type": "null"})
            elif isinstance(p, int):
                args.append({"type": "integer", "value": str(p)})
            elif isinstance(p, float):
                args.append({"type": "float", "value": p})
            else:
                args.append({"type": "text", "value": str(p)})

        return {"type":"execute","stmt":{"sql":sql,"args":args}}

    def _pipeline(self, requests):
        expected=len(requests)
        if self._broken:
            raise RuntimeError('Database connection failed; retry the whole transaction')
        if not self._transaction:
            requests.append({"type": "close"})
        payload = {"requests": requests}
        if self._baton:
            payload['baton'] = self._baton
        try:
            data = self._post(payload)
        except Exception:
            self._broken = True
            raise
        if self._transaction:
            self._baton = data.get('baton')
            if not self._baton:
                self._broken = True
                raise RuntimeError('Database transaction expired; retry the whole operation')
            if data.get('base_url'):
                original, candidate = urlsplit(_turso_http_url()), urlsplit(data['base_url'])
                same_host = candidate.hostname == original.hostname and candidate.port == original.port
                turso_host = (original.hostname or '').endswith('.turso.io') and (candidate.hostname or '').endswith('.turso.io')
                if candidate.scheme != 'https' or candidate.username or candidate.password or candidate.query or candidate.fragment or not (same_host or turso_host):
                    self._broken = True
                    raise RuntimeError('Untrusted database stream address')
                self._base = data['base_url'].rstrip('/')

        results=data.get('results',[])
        if len(results)!=len(requests):
            self._broken=True
            raise RuntimeError('Incomplete database response')
        for result in results[:expected]:
            if result.get('type')!='ok' or 'result' not in result.get('response',{}):
                self._broken=True
                raise RuntimeError(result.get('error',{}).get('message','Invalid database response'))
        return results[:expected]

    def execute_batch(self, statements):
        if not self._transaction: raise RuntimeError('Batch writes require an explicit transaction')
        if statements: self._pipeline([self._statement(sql,params) for sql,params in statements])

    def execute(self, sql: str, params: tuple | list = ()) -> 'TursoCursor':
        result=self._pipeline([self._statement(sql,params)])[0]
        response = result.get("response", {}).get("result", {})
        cols = [c["name"] for c in response.get("cols", [])]
        rows_raw = response.get("rows", [])
        affected = response.get("affected_row_count", 0)
        last_id = response.get("last_insert_rowid", None)

        rows = []
        for row_data in rows_raw:
            converted = []
            for cell in row_data:
                v = cell.get("value")
                if cell.get("type") == "integer" and v is not None:
                    converted.append(int(v))
                elif cell.get("type") == "float" and v is not None:
                    converted.append(float(v))
                else:
                    converted.append(v)
            if self.row_factory == sqlite3.Row:
                rows.append(TursoRow(cols, converted))
            else:
                rows.append(tuple(converted))

        return TursoCursor(rows, affected, last_id)

    def executescript(self, sql: str):
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if stmt and not stmt.startswith("--") and not stmt.startswith("PRAGMA"):
                try:
                    self.execute(stmt)
                except:
                    pass

    def begin(self):
        if self._transaction:
            raise RuntimeError('Transaction already open')
        self._transaction = True
        self.execute('BEGIN IMMEDIATE')

    def commit(self):
        if self._transaction:
            self.execute('COMMIT')
            self._transaction = False

    def rollback(self):
        # Closing an uncommitted stream rolls back. Never reopen a lost stream
        # or replay statements after a timeout / ambiguous network response.
        self.close()

    def close(self):
        baton, self._baton = self._baton, None
        self._transaction = False
        if baton:
            try:
                self._post({'baton':baton,'requests':[{'type':'close'}]})
            except Exception:
                # The server also expires idle streams; preserve the original error.
                pass


def execute_statements(conn, statements):
    if isinstance(conn,TursoConnection):
        conn.execute_batch(statements)
    else:
        for sql,params in statements:
            conn.execute(sql,params)


class TursoCursor:
    def __init__(self, rows, affected, last_id):
        self._rows = rows
        self.rowcount = affected
        self.lastrowid = int(last_id) if last_id else None

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


def init_db():
    """Initialize database with schema and run migrations."""
    if _use_turso():
        conn = TursoConnection()
    else:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        from backend.config import DB_PATH
        conn = sqlite3.connect(str(DB_PATH))

    schema_path = Path(__file__).parent / "schema.sql"
    import re
    schema = re.sub(r"(?m)^\s*--.*$", "", schema_path.read_text())
    for statement in schema.split(";"):
        statement = statement.strip()
        if statement and not statement.startswith("--") and not statement.startswith("PRAGMA"):
            conn.execute(statement)

    try:
        cols = [row[1] for row in conn.execute("PRAGMA table_info(tools)").fetchall()]
        for col, default in [
            ("title_zh", "TEXT"), ("description_zh", "TEXT"),
            ("content_type", "TEXT DEFAULT 'other'"), ("domain", "TEXT DEFAULT 'general'"),
            ("is_featured", "INTEGER DEFAULT 0"), ("is_metis_pick", "INTEGER DEFAULT 0"),
            ("take_en", "TEXT"),
            ("discovery_category", "TEXT DEFAULT 'other'"),
            ("short_summary", "TEXT"),
            ("short_summary_zh", "TEXT"),
            ("trending_score", "REAL"),
            ("ai_intro", "TEXT"),
            ("ai_intro_zh", "TEXT"),
        ]:
            if col not in cols:
                conn.execute(f"ALTER TABLE tools ADD COLUMN {col} {default}")
    except:
        pass

    conn.commit()
    conn.close()
    from backend.knowledge.store import init_knowledge
    init_knowledge()


@contextmanager
def get_db(atomic=False):
    """Get a database connection with row factory."""
    if _use_turso():
        conn = TursoConnection()
    else:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        from backend.config import DB_PATH
        conn = sqlite3.connect(str(DB_PATH))

    conn.row_factory = sqlite3.Row
    if not _use_turso():
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
    try:
        if atomic:
            if isinstance(conn, TursoConnection):
                conn.begin()
            else:
                conn.execute('BEGIN IMMEDIATE')
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
