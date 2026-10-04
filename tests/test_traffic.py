import hashlib
import json
import uuid
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import pytest
from test_knowledge import client, ADMIN
from test_analytics import counter
from backend import traffic as t, analytics as a
from backend.db import get_db
from test_atomic_batch import remote


def event(browser=None,kind='page_view',**extra):
    return dict(browser_id=browser,event_id=str(uuid.uuid4()),kind=kind,path='/for-you',**extra)


def test_five_views_two_visitors_three_sessions_and_no_retry_growth(counter):
    now=int(datetime.fromisoformat('2026-10-04T08:00:00+08:00').timestamp());a_id,b_id=str(uuid.uuid4()),str(uuid.uuid4())
    e=event(a_id)
    for d,n in [(e,now),(event(a_id),now+1),(event(a_id,path_override=True),now+2)]:
        d.pop('path_override',None);t.record(d,n)
    t.record(event(b_id),now+3);t.record(event(a_id),now+1802);t.record(e,now+1803)
    result=t.summary('2026-10-04','2026-10-04',now+1803)
    assert (result['totals']['pv'],result['totals']['uv'],result['totals']['sessions'])==(5,2,3)
    assert a.public_total()['total']==3
    with get_db() as db:
        stored=' '.join(str(tuple(r)) for r in db.execute('SELECT * FROM fieldtofit_analytics_events').fetchall())
    assert a_id not in stored and b_id not in stored


def test_midnight_return_visits_sources_content_and_anonymous(counter):
    now=int(datetime.fromisoformat('2026-10-03T23:59:50+08:00').timestamp());bid=str(uuid.uuid4())
    t.record(event(bid,referrer='https://www.google.com/search?q=PRIVATE'),now)
    t.record(event(bid,referrer='https://private.example/path?secret=1'),now+20)
    for n in (21,22):t.record(event(bid,'content_view',content_id='CW-M01'),now+n)
    t.record(event(bid,'material_read',content_id='CW-M01'),now+23)
    t.record(event(None),now+24)
    r=t.summary('2026-10-03','2026-10-04',now+24)
    assert r['totals']['uv']==1 and r['totals']['returning_uv']==1 and r['totals']['sessions']==1
    assert r['totals']['content_views']==1 and r['totals']['anonymous_pv']==1 and r['totals']['repeat_readers']==1
    assert r['sources']==[{'source':'search:google','entry':'/for-you','sessions':1}]
    assert t.summary('2026-10-04','2026-10-04',now+24)['totals']['sessions']==0
    with get_db() as db: raw=json.dumps([dict(r) for r in db.execute('SELECT * FROM fieldtofit_analytics_events').fetchall()])
    assert 'PRIVATE' not in raw and 'private.example' not in raw


def test_concurrent_retry_and_rollback(counter):
    e=event(str(uuid.uuid4()));now=2_000_000
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(lambda _:t.record(e,now),range(4)))
    assert a.public_total()['total']==1
    with get_db() as db:
        assert db.execute('SELECT count(*) FROM fieldtofit_analytics_events').fetchone()[0]==1
        db.execute("CREATE TRIGGER fail_traffic BEFORE INSERT ON fieldtofit_analytics_state BEGIN SELECT RAISE(ABORT,'test failure'); END")
    with pytest.raises(Exception):t.record(event(str(uuid.uuid4())),now+1)
    assert a.public_total()['total']==1


def test_security_consent_failures_and_csv(counter,monkeypatch):
    data=event(str(uuid.uuid4()));headers={'Origin':'http://localhost','User-Agent':'Mozilla/5.0 browser'}
    assert counter.post('/api/analytics/events',json=data,headers=headers).status_code==204
    assert counter.get('/api/admin/analytics/summary').status_code==401
    assert counter.get('/api/admin/analytics/export').status_code==401
    for change in [{'path':'/admin'},{'path':'/for-you?secret=x'},{'content_id':'D-999999','kind':'content_view'},{'kind':'unknown'},{'secret':'PRIVATE'}]:
        assert counter.post('/api/analytics/events',json={**data,**change},headers=headers).status_code==400
    assert counter.post('/api/analytics/events',json=data,headers={**headers,'Origin':'https://evil.example'}).status_code==403
    before=a.public_total()['total']
    for h in [{'DNT':'1'},{'Sec-GPC':'1'},{'X-Admin-Password':'abc'},{'User-Agent':'Googlebot'}]:counter.post('/api/analytics/events',json=event(str(uuid.uuid4())),headers={**headers,**h})
    monkeypatch.setenv('FIELDTOFIT_ANALYTICS_REQUIRE_CONSENT','1')
    counter.post('/api/analytics/events',json=event(str(uuid.uuid4())),headers=headers)
    assert a.public_total()['total']==before
    response=counter.get('/api/admin/analytics/export',headers=ADMIN)
    assert response.status_code==200 and data['browser_id'] not in response.text and 'browser_id' not in response.text
    assert counter.get('/api/admin/analytics/summary?start=2000-01-01&end=2030-01-01',headers=ADMIN).status_code==400
    monkeypatch.setattr(t,'record',lambda *args:(_ for _ in ()).throw(RuntimeError('SECRET')))
    response=counter.post('/api/analytics/events',json={**data,'consent':True},headers=headers)
    assert response.status_code==503 and 'SECRET' not in response.text


def test_retention_preserves_aggregate_and_public_total(counter):
    now=2_000_000;t.record(event(str(uuid.uuid4())),now)
    t.clean(now+t.DAYS+1)
    with get_db() as db:
        assert not db.execute('SELECT * FROM fieldtofit_analytics_events').fetchall()
        assert db.execute('SELECT pv FROM fieldtofit_analytics_daily').fetchone()[0]==1
    assert a.public_total()['total']==1


def test_remote_atomic_path_and_additive_migration(remote,monkeypatch):
    from pathlib import Path
    from contextlib import contextmanager
    import sqlite3
    conn,db=remote
    db.executescript(Path('backend/db/analytics.sql').read_text())
    conn.row_factory=sqlite3.Row
    @contextmanager
    def remote_db():
        yield conn
    monkeypatch.setattr(t,'get_db',remote_db)
    monkeypatch.setattr(a,'get_db',remote_db)
    data=event(str(uuid.uuid4()))
    t.record(data,2_000_000);t.record(data,2_000_001)
    a.migrate();a.migrate()
    assert db.execute('SELECT visits FROM fieldtofit_visit_total').fetchone()[0]==1
    assert db.execute('SELECT pv FROM fieldtofit_analytics_daily').fetchone()[0]==1
    db.execute("CREATE TRIGGER fail_report BEFORE INSERT ON fieldtofit_analytics_state BEGIN SELECT RAISE(ABORT,'failure'); END")
    with pytest.raises(RuntimeError):t.record(event(str(uuid.uuid4())),2_000_002)
    assert db.execute('SELECT count(*) FROM fieldtofit_analytics_events').fetchone()[0]==1
    assert not db.in_transaction
