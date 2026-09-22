"""Visit totals, concurrency, expiry and fail-closed public collection; isolated DB only."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import sqlite3
import uuid

import pytest
from test_knowledge import client
from test_atomic_batch import remote
from backend import analytics as a
from backend.db import get_db


def ident():
    return str(uuid.uuid4())


@pytest.fixture
def counter(client, monkeypatch):
    monkeypatch.setenv('FIELDTOFIT_ANALYTICS_ENABLED', '1')
    monkeypatch.setenv('FIELDTOFIT_ANALYTICS_ORIGIN', 'http://localhost')
    return client


def post(client, browser=None, event=None, path='/for-you', headers=None, extra=None):
    return client.post('/api/analytics/visit', json={
        'browser_id': browser or ident(), 'event_id': event or ident(), 'path': path, **(extra or {})},
        headers={'Origin': 'http://localhost', 'User-Agent': 'Mozilla/5.0 human browser', **(headers or {})})


def total(client):
    response = client.get('/api/analytics/total')
    assert response.status_code == 200
    return response.json


def test_read_only_zero_activation_and_public_fields(counter):
    for _ in range(3):
        data = total(counter)
        assert data['total'] == 0 and data['started_at'] is None
    with get_db() as db:
        assert db.execute('SELECT count(*) FROM fieldtofit_visit_total').fetchone()[0] == 0
    assert post(counter).status_code == 204
    data = total(counter)
    assert data['total'] == 1 and data['started_at'] and data['updated_at']
    assert set(data) == {'total', 'started_at', 'updated_at', 'status', 'collection_enabled', 'collection_origin'}
    assert counter.get('/api/analytics/total').headers['Cache-Control'] == 'no-store'
    assert counter.get('/api/analytics/sessions').status_code == 404


def test_sessions_refresh_tabs_midnight_and_retry(counter):
    browser, second, event = ident(), ident(), ident()
    at = int(datetime(2026, 9, 21, 15, 59, 50, tzinfo=timezone.utc).timestamp())  # 23:59:50 Shanghai; the next event crosses midnight.
    for offset, page in [(0, '/for-you'), (20, '/about'), (40, '/sources')]:
        assert a.record_visit(browser, ident(), now=at + offset)
    a.record_visit(second, event, now=at + 50)
    # Retry must neither count nor postpone the original session's expiry.
    a.record_visit(second, event, now=at + 1000)
    assert total(counter)['total'] == 2
    a.record_visit(browser, ident(), now=at + 40 + 1799)
    assert total(counter)['total'] == 2
    a.record_visit(browser, ident(), now=at + 40 + 1799 + 1800)
    a.record_visit(second, ident(), now=at + 50 + 1800)
    assert total(counter)['total'] == 4
    with get_db() as db:
        rows = db.execute('SELECT * FROM fieldtofit_visit_sessions').fetchall()
        assert all(r['browser_id'] not in (browser, second) for r in rows)


def test_duplicate_parallel_new_sessions_and_restart(counter):
    browser, event = ident(), ident()
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _: a.record_visit(browser, event, now=2_000_000), range(12)))
    assert total(counter)['total'] == 1
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _: a.record_visit(browser, ident(), now=2_000_001), range(12)))
    assert total(counter)['total'] == 1
    from backend.db import init_db
    init_db()
    a.migrate()
    a.migrate()
    assert total(counter)['total'] == 1
    a.clean_expired(now=2_000_001 + 86401)
    with get_db() as db:
        for table in ['sessions', 'events', 'limits']:
            assert db.execute('SELECT count(*) FROM fieldtofit_visit_' + table).fetchone()[0] == 0
    assert total(counter)['total'] == 1
    a.record_visit(ident(), ident(), now=2_000_002 + 86401)
    assert total(counter)['total'] == 2


def test_transaction_failure_rolls_back_all_counting(counter):
    with get_db() as db:
        db.execute("CREATE TRIGGER reject_visit BEFORE INSERT ON fieldtofit_visit_events BEGIN SELECT RAISE(ABORT, 'failure'); END")
    assert post(counter).status_code == 503
    assert total(counter)['total'] == 0
    with get_db() as db:
        assert db.execute('SELECT count(*) FROM fieldtofit_visit_sessions').fetchone()[0] == 0


@pytest.mark.parametrize('headers', [
    {'DNT': '1'}, {'Sec-GPC': '1'}, {'X-Admin-Password': 'excluded'},
    {'User-Agent': 'Googlebot'}, {'User-Agent': 'HeadlessChrome'}, {'User-Agent': ''},
])
def test_privacy_admin_and_bots_do_not_count(counter, headers):
    assert post(counter, headers=headers).status_code == 204
    assert total(counter)['total'] == 0


@pytest.mark.parametrize('path', ['/admin', '/api/health', '/for-you?q=private', '/for-you#secret', '/records/missing', '/account', '/news/D-01'])
def test_invalid_private_and_unimplemented_pages(counter, path):
    assert post(counter, path=path).status_code == 400
    assert total(counter)['total'] == 0


def test_origin_schema_limits_disabled_and_fault(counter, monkeypatch):
    assert post(counter, headers={'Origin': 'https://preview.example'}).status_code == 403
    assert post(counter, headers={'Origin': ''}).status_code == 403
    assert post(counter, headers={'Sec-Fetch-Site': 'cross-site'}).status_code == 403
    assert post(counter, extra={'email': 'not-stored@example.org'}).status_code == 400
    assert post(counter, browser='not-a-random-id').status_code == 400
    assert counter.post('/api/analytics/visit', json=[], headers={'Origin':'http://localhost','User-Agent':'Mozilla'}).status_code == 400
    assert post(counter, extra={'oversize': 'x' * 1500}).status_code == 400
    browser = ident()
    monkeypatch.setattr(a.time, 'time', lambda: 2_000_000)
    for _ in range(60):
        assert post(counter, browser=browser).status_code == 204
    assert post(counter, browser=browser).status_code == 429
    assert total(counter)['total'] == 1
    monkeypatch.setenv('FIELDTOFIT_ANALYTICS_ENABLED', '0')
    assert post(counter).status_code == 204
    assert total(counter)['total'] == 1 and total(counter)['status'] == 'paused'
    monkeypatch.setattr(a, 'public_total', lambda: (_ for _ in ()).throw(RuntimeError('secret')))
    response = counter.get('/api/analytics/total')
    assert response.status_code == 503 and response.json == {'status': 'unavailable'}


def test_global_rate_limit(counter):
    with get_db() as db:
        db.execute("INSERT INTO fieldtofit_visit_limits VALUES('global',?,1200)", (2_000_000 // 60,))
    assert not a.record_visit(ident(), ident(), now=2_000_000)
    assert total(counter)['total'] == 0
    assert a.record_visit(ident(), ident(), now=2_000_060)
    assert total(counter)['total'] == 1


def test_remote_atomic_batch_same_semantics(remote, monkeypatch):
    from contextlib import contextmanager
    from pathlib import Path
    conn, db = remote
    db.executescript(Path('backend/db/schema.sql').read_text())
    db.executescript(Path('backend/db/analytics.sql').read_text())
    conn.row_factory = sqlite3.Row
    @contextmanager
    def remote_db():
        yield conn
    monkeypatch.setattr(a, 'get_db', remote_db)
    browser, event = ident(), ident()
    a.record_visit(browser, event, now=2_000_000)
    a.record_visit(browser, event, now=2_001_000)
    a.record_visit(browser, ident(), now=2_001_799)
    a.record_visit(browser, ident(), now=2_003_599)
    assert db.execute('SELECT visits FROM fieldtofit_visit_total').fetchone()[0] == 2
    assert db.execute('SELECT last_seen FROM fieldtofit_visit_sessions WHERE browser_id=?', (hashlib.sha256(browser.encode()).hexdigest(),)).fetchone()[0] == 2_003_599
    db.execute("CREATE TRIGGER reject_visit BEFORE INSERT ON fieldtofit_visit_events BEGIN SELECT RAISE(ABORT, 'failure'); END")
    with pytest.raises(RuntimeError):
        a.record_visit(ident(), ident(), now=2_003_600)
    assert db.execute('SELECT visits FROM fieldtofit_visit_total').fetchone()[0] == 2
    assert not db.in_transaction


def test_existing_database_additive_migration(counter):
    with get_db() as db:
        db.execute('CREATE TABLE preserved_fixture(value TEXT)')
        db.execute("INSERT INTO preserved_fixture VALUES('keep')")
        for name in ['total', 'sessions', 'events', 'limits']:
            db.execute('DROP TABLE fieldtofit_visit_' + name)
    assert counter.get('/api/analytics/total').status_code == 503
    a.migrate()
    a.migrate()
    with get_db() as db:
        assert db.execute('SELECT value FROM preserved_fixture').fetchone()[0] == 'keep'
    assert total(counter)['total'] == 0
    assert post(counter).status_code == 204
    assert total(counter)['total'] == 1
