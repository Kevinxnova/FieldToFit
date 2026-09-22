"""Minimal first-party visit counter; no page histories or visitor reports."""
from datetime import datetime, timezone
import hashlib
import os
import re
import time
from pathlib import Path

from flask import Blueprint, jsonify, request
from backend.db import get_db, TursoConnection, TursoCursor

bp = Blueprint('analytics', __name__)
SESSION_SECONDS = 1800
RETENTION_SECONDS = 86400
PUBLIC_PATHS = {'/for-you', '/for-your-ai', '/about', '/community', '/sources'}
BOT = re.compile(r'bot|spider|crawler|headless|selenium|playwright|curl|wget|python|httpx|monitor|uptime', re.I)
UUID = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')
TOTAL_SQL = 'SELECT visits, started_at, updated_at FROM fieldtofit_visit_total WHERE id=1'


def enabled():
    return os.getenv('FIELDTOFIT_ANALYTICS_ENABLED', '0') == '1'


def site_origin():
    return os.getenv('FIELDTOFIT_ANALYTICS_ORIGIN', 'https://fieldtofit.top').rstrip('/')


def iso(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat().replace('+00:00', 'Z') if value is not None else None


def public_total():
    with get_db() as db:
        row = db.execute(TOTAL_SQL).fetchone()
    return {'total': row['visits'] if row else 0,
            'started_at': iso(row['started_at']) if row else None,
            'updated_at': iso(row['updated_at']) if row else None,
            'status': 'active' if enabled() else 'paused',
            'collection_enabled': enabled(), 'collection_origin': site_origin()}


def atomic(db, statements):
    # One remote transaction avoids Turso's short interactive transaction lifetime.
    if isinstance(db, TursoConnection):
        return db.atomic_statements(statements)
    db.execute('BEGIN IMMEDIATE')
    cursors = []
    for sql, params in statements:
        cursor = db.execute(sql, params)
        cursors.append(TursoCursor(cursor.fetchall(), cursor.rowcount, cursor.lastrowid))
    return cursors


def migrate():
    """Create only the visit tables atomically; existing totals are never reset."""
    schema = Path(__file__).with_name('db').joinpath('analytics.sql').read_text()
    schema = re.sub(r'(?m)^\s*--.*$', '', schema)
    statements = [(sql.strip(), ()) for sql in schema.split(';') if sql.strip()]
    with get_db() as db:
        atomic(db, statements)


def record_visit(browser_id, event_id, now=None):
    now = int(time.time()) if now is None else int(now)
    browser = hashlib.sha256(browser_id.encode()).hexdigest()
    event = hashlib.sha256(event_id.encode()).hexdigest()
    bucket = now // 60
    # All decisions and writes run in the same transaction on every deployment.
    # The transient guard preserves the decision across statements without Python
    # branches between remote reads and writes. Duplicate retries don't extend a visit.
    statements = [
        ('DELETE FROM fieldtofit_visit_events WHERE received_at < ?', (now - RETENTION_SECONDS,)),
        ('DELETE FROM fieldtofit_visit_sessions WHERE last_seen < ?', (now - RETENTION_SECONDS,)),
        ('DELETE FROM fieldtofit_visit_limits WHERE bucket < ?', (bucket - 1,)),
        ("INSERT INTO fieldtofit_visit_limits(scope,bucket,hits) VALUES('global',?,1) ON CONFLICT(scope,bucket) DO UPDATE SET hits=hits+1", (bucket,)),
        ('INSERT INTO fieldtofit_visit_limits(scope,bucket,hits) VALUES(?,?,1) ON CONFLICT(scope,bucket) DO UPDATE SET hits=hits+1', (browser, bucket)),
        ('DROP TABLE IF EXISTS temp.visit_guard', ()),
        ('CREATE TEMP TABLE visit_guard(fresh INTEGER, new_visit INTEGER, limited INTEGER)', ()),
        ('''INSERT INTO visit_guard SELECT
            NOT EXISTS(SELECT 1 FROM fieldtofit_visit_events WHERE event_id=?),
            NOT EXISTS(SELECT 1 FROM fieldtofit_visit_sessions WHERE browser_id=? AND last_seen>?),
            EXISTS(SELECT 1 FROM fieldtofit_visit_limits WHERE bucket=? AND
                ((scope='global' AND hits>1200) OR (scope=? AND hits>60)))''',
         (event, browser, now - SESSION_SECONDS, bucket, browser)),
        ('''INSERT INTO fieldtofit_visit_total(id,visits,started_at,updated_at)
            SELECT 1,1,?,? FROM visit_guard WHERE fresh AND new_visit AND NOT limited
            ON CONFLICT(id) DO UPDATE SET visits=visits+1, updated_at=excluded.updated_at''', (now, now)),
        ('''INSERT INTO fieldtofit_visit_sessions(browser_id,last_seen)
            SELECT ?,? FROM visit_guard WHERE fresh AND NOT limited
            ON CONFLICT(browser_id) DO UPDATE SET last_seen=MAX(last_seen,excluded.last_seen)''', (browser, now)),
        ('''INSERT INTO fieldtofit_visit_events(event_id,received_at)
            SELECT ?,? FROM visit_guard WHERE fresh AND NOT limited''', (event, now)),
        ('SELECT limited FROM visit_guard', ()),
        ('DROP TABLE temp.visit_guard', ()),
    ]
    with get_db() as db:
        results = atomic(db, statements)
        return not bool(results[-2].fetchone()[0])


def clean_expired(now=None):
    """May be run by maintenance even when collection is paused; total is permanent."""
    now = int(time.time()) if now is None else int(now)
    with get_db() as db:
        atomic(db, [
            ('DELETE FROM fieldtofit_visit_events WHERE received_at < ?', (now - RETENTION_SECONDS,)),
            ('DELETE FROM fieldtofit_visit_sessions WHERE last_seen < ?', (now - RETENTION_SECONDS,)),
            ('DELETE FROM fieldtofit_visit_limits WHERE bucket < ?', (now // 60 - 1,)),
        ])


@bp.after_request
def no_store(response):
    # Never cache eligibility or an error as a successful public total.
    response.headers['Cache-Control'] = 'no-store'
    return response


@bp.get('/api/analytics/total')
def total():
    try:
        return jsonify(public_total())
    except Exception:
        return jsonify({'status': 'unavailable'}), 503


@bp.post('/api/analytics/visit')
def visit():
    if not enabled():
        return '', 204
    origin = site_origin()
    if request.headers.get('Origin') != origin or request.host_url.rstrip('/') != origin:
        return jsonify({'detail': 'Origin not allowed'}), 403
    if request.headers.get('Sec-Fetch-Site') not in (None, 'same-origin'):
        return jsonify({'detail': 'Origin not allowed'}), 403
    ua = request.headers.get('User-Agent', '')
    if (request.headers.get('DNT') == '1' or request.headers.get('Sec-GPC') == '1'
            or request.headers.get('X-Admin-Password') or not ua or BOT.search(ua)):
        return '', 204
    if not request.is_json or (request.content_length or 0) > 1024:
        return jsonify({'detail': 'Invalid visit'}), 400
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or set(data) != {'browser_id', 'event_id', 'path'}:
        return jsonify({'detail': 'Invalid visit'}), 400
    if not all(isinstance(data[k], str) and UUID.fullmatch(data[k]) for k in ('browser_id', 'event_id')):
        return jsonify({'detail': 'Invalid visit'}), 400
    path = data['path']
    if not isinstance(path, str) or len(path) > 200:
        return jsonify({'detail': 'Invalid page'}), 400
    if path not in PUBLIC_PATHS:
        # Only successfully loaded, currently public details are eligible.
        if not re.fullmatch(r'/(?:records/[A-Za-z0-9_-]+|news/D-\d{2,}|watch/CW-[MATSH]\d{2,})', path):
            return jsonify({'detail': 'Invalid page'}), 400
        try:
            if path.startswith('/records/'):
                from backend.knowledge.store import get_record
                exists = get_record(path.removeprefix('/records/'))
            else:
                from backend.seo import news, watch
                kind, ident = path.strip('/').split('/')
                exists = (news if kind == 'news' else watch)(id=ident)['items']
            if not exists:
                return jsonify({'detail': 'Invalid page'}), 400
        except ValueError as exc:
            if getattr(exc, 'status', None) == 404:
                return jsonify({'detail': 'Invalid page'}), 400
            return jsonify({'status': 'unavailable'}), 503
        except Exception:
            return jsonify({'status': 'unavailable'}), 503
    try:
        if not record_visit(data['browser_id'], data['event_id']):
            response = jsonify({'detail': 'Too many visits'})
            response.headers['Retry-After'] = '60'
            return response, 429
    except Exception:
        # Do not log identifiers, request bodies or database credentials.
        return jsonify({'status': 'unavailable'}), 503
    return '', 204


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['migrate', 'clean'])
    args = parser.parse_args()
    if args.action == 'migrate':
        migrate()
        print('Visit tables ready; existing totals retained. Collection requires explicit enablement.')
    else:
        clean_expired()
        print('Expired visit identifiers removed; cumulative total retained.')
