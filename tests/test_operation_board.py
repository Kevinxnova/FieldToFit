"""Stage evidence, missing history, actual issues and private publication boundaries."""
from datetime import datetime,timedelta,timezone
import copy
import pytest
from test_knowledge import client,ADMIN
from test_content_workspace import call,migrate,make,valid,publish
from test_daily_discovery import source,item
from backend.db import get_db
from backend.knowledge import operation_board as o,discovery as d,content_workspace as ws,store,sources,paging


def board(client):
    r=call(client,'/operations',method='get');assert r.status_code==200,r.json
    return r.json

def test_unknown_history_private_access_and_activation(client):
    migrate(client)
    assert client.get('/api/v1/admin/workspace/operations').status_code==401
    before=board(client);assert before['totals']['organized'] is None
    assert call(client,'/operations/upgrade').status_code==200
    assert board(client)['totals']['organized']==0
    assert not board(client)['tracking_complete_day']
    assert call(client,'/operations?day=1900-01-01',method='get').status_code==400
    assert o.day_of('2026-09-14T18:00:00Z')=='2026-09-15'


def test_recorded_stages_idempotence_and_no_implicit_publication(client):
    migrate(client);before=client.get('/api/v1/platform/watch').json
    ident,ref=make(client);valid(client,'watch',ident)
    assert board(client)['totals']['organized']==0
    assert board(client)['totals']['organize_pending']>=1
    p=ws.preview('watch',ident)
    assert call(client,f'/content/watch/{ident}/submit-review',p).status_code==200
    assert call(client,f'/content/watch/{ident}/submit-review',p).status_code==200
    v=board(client);assert v['totals']['organized']==1 and v['totals']['review_pending']==1
    assert client.get('/api/v1/platform/watch').json==before
    with get_db() as db:db.execute('UPDATE fieldtofit_manual_candidates SET summary=? WHERE ref=?',('changed source',ref))
    v=board(client);assert v['totals']['review_pending']==0
    assert any(i['code']=='review_stale' for i in v['issues'])
    assert call(client,f'/content/watch/{ident}/submit-review',p).status_code==409
    updated=ws.preview('watch',ident)
    assert call(client,f'/content/watch/{ident}/submit-review',updated).status_code==200
    assert board(client)['totals']['review_pending']==1
    assert board(client)['totals']['organized']==1
    publish(client,'watch',ident)
    v=board(client);assert v['totals']['published_new']==1
    assert v['totals']['review_pending']==0
    valid(client,'watch',ident);publish(client,'watch',ident)
    assert board(client)['totals']['published_update']==1


def test_material_observations_not_retained_or_duplicate(client):
    s=source();d.capture(s,item());d.capture(s,item());v=board(client)
    assert v['totals']['discovered']==1 and v['totals']['full_text']==1
    d.capture(s,item(materials=[],metadata={'primary':True,'gaps':['failed']}))
    assert board(client)['totals']['full_text']==1
    other=copy.deepcopy(s);other['id']='other-official';d.capture(other,item())
    v=board(client);assert v['totals']['full_text']==1
    assert sum(x['full_text'] for x in v['sources'])==2
    details=call(client,'/operations?metric=full_text',method='get').json
    assert len(details['details'])==1


def test_wait_is_not_reset_by_edit_and_historic_wait_unknown(client):
    migrate(client);ident,ref=make(client)
    ago=(datetime.now(timezone.utc)-timedelta(days=4)).isoformat()
    with get_db() as db:db.execute('UPDATE fieldtofit_operation_events SET created_at=?',(ago,))
    valid(client,'watch',ident)
    v=board(client);assert any(i['code']=='waiting' for i in v['issues'])
    assert max(x['oldest_wait_days'] or 0 for x in v['sources'])>=4
    with get_db() as db:db.execute('DELETE FROM fieldtofit_operation_events')
    assert sum(x['unknown_wait_count'] for x in board(client)['sources'])>=1


def test_issue_defer_change_reopen_and_resolve(client):
    migrate(client);sid=source()['id']
    with get_db() as db:db.execute("UPDATE knowledge_sources SET status='error',error='HTTP 429' WHERE id=?",(sid,))
    call(client,'/operations/refresh');v=board(client);issue=next(i for i in v['issues'] if i['code']=='source_failed' and i['source']==sid)
    body={'fingerprint':issue['fingerprint'],'review_on':(datetime.now(timezone.utc)+timedelta(days=2)).date().isoformat(),'note':'等待上游恢复'}
    assert call(client,'/operations/issues/'+issue['id'],body).status_code==200
    assert next(i for i in board(client)['issues'] if i['id']==issue['id'])['status']=='later'
    with get_db() as db:db.execute("UPDATE knowledge_sources SET error='HTTP 503' WHERE id=?",(sid,))
    assert next(i for i in board(client)['issues'] if i['id']==issue['id'])['status']=='open'
    assert call(client,'/operations/issues/'+issue['id'],body).status_code==409
    call(client,'/operations/refresh')
    with get_db() as db:db.execute("UPDATE knowledge_sources SET status='success',error='' WHERE id=?",(sid,))
    call(client,'/operations/refresh');v=board(client)
    assert not any(i['id']==issue['id'] for i in v['issues'])
    assert next(i for i in v['resolved'] if i['id']==issue['id'])['note']=='等待上游恢复'


def test_abstract_is_coverage_not_automatic_error(client):
    s=source();d.capture(s,item(materials=[d.material('https://example.org','abstract text','abstract')],metadata={'gaps':['full paper not collected']}))
    assert not any(i['code']=='material_missing' for i in board(client)['issues'])


def test_index_pagination_not_article_and_single_slot_drains(client,monkeypatch):
    s=copy.deepcopy(source('index'));s['config'].update(limit=1,recheck_body=True);base=s['url'];prefix=s['config']['path_prefix'];calls=[]
    paging.save_progress(s['id'],{'pending':[{'url':base+'?page=2'}]})
    def fetch(url):
        calls.append(url)
        if url==base:return f'<a href="{prefix}one">One</a><a href="?page=2">Next</a>'.encode(),url,'text/html'
        if '?page=2' in url:return f'<a href="{prefix}two">Two</a>'.encode(),url,'text/html'
        return ('<main><h1>Release</h1><p>'+'source content '*30+'</p></main>').encode(),url,'text/html'
    monkeypatch.setattr(sources,'fetch',fetch)
    with pytest.raises(sources.PartialSourceError):d.collect(s)
    d.collect(s)
    assert paging.progress(s['id'])['status']=='complete'
    with get_db() as db:
        urls=[r[0] for r in db.execute('SELECT url FROM fieldtofit_discoveries')]
    assert len(urls)==2 and all('page=' not in url for url in urls)


def test_arxiv_fallback_preserves_failure_and_api_cursor(client,monkeypatch):
    s=source('arxiv');paging.save_progress(s['id'],{'offset':16})
    def fetch(url):
        if '/api/query' in url:raise TimeoutError('API timeout')
        return b'<feed xmlns="http://www.w3.org/2005/Atom"><title>arXiv</title><entry><title>Agent framework</title><id>https://arxiv.org/abs/2609.00001</id><link href="https://arxiv.org/abs/2609.00001"/><summary>Actual abstract only</summary></entry></feed>',url,'application/atom+xml'
    monkeypatch.setattr(sources,'fetch',fetch)
    with pytest.raises(sources.PartialSourceError) as e:d.collect(s)
    assert e.value.found==1
    p=paging.progress(s['id']);assert p['offset']==16 and p['errors']
    with get_db() as db:r=dict(db.execute('SELECT * FROM fieldtofit_discoveries').fetchone())
    assert r['published_at'] is None and 'official_cs_ai_feed' in r['metadata']


def test_registered_conflicts_and_failed_jobs_are_actionable(client):
    from test_knowledge import seed
    migrate(client);rid=seed(title='Known conflict')
    ws.select({'ref':'record:'+rid,'action':'select','kind':'watch','type':'tool'})
    with get_db() as db:
        db.execute("INSERT INTO knowledge_conflicts(id,record_id,field,alternatives,created_at) VALUES(?,?,?,?,?)",('conflict-1',rid,'cost','["free","paid"]',store.now()))
        db.execute("INSERT INTO knowledge_jobs(record_id,stage,status,error) VALUES(?,?,'error',?)",(rid,'organization','Model service unavailable'))
    issues=board(client)['issues']
    assert any(i['code']=='fact_conflict' and i['target']['ref']=='record:'+rid for i in issues)
    assert any(i['code']=='organization_failed' and 'Model service unavailable' in i['reason'] for i in issues)


def test_maintained_retrieval_is_counted_but_registration_not_scheduled(client):
    import hashlib
    from backend.knowledge import platform_maintenance as p
    sid=p.register('example/maintained','Maintained example')
    s=next(x for x in sources.list_sources() if x['id']==sid)
    body='Actual isolated README. '*10
    mats=[{'key':'readme','kind':'readme','url':s['url'],'locator':'README.md','body':body,'hash':hashlib.sha256(body.encode()).hexdigest(),'coverage':'full_text'}]
    p.stage(s,mats);p.stage(s,mats)
    v=board(client)
    assert v['totals']['discovered']==1 and v['totals']['full_text']==1
    assert v['totals']['planned_sources']==len(__import__('backend.knowledge.source_catalog',fromlist=['definitions']).definitions())
    assert len(call(client,'/operations?metric=full_text',method='get').json['details'])==1


def test_failed_arxiv_fallback_keeps_both_causes_and_resume(client,monkeypatch):
    s=source('arxiv');paging.save_progress(s['id'],{'offset':24,'watermark':'2026-09-01T00:00:00Z'})
    def fetch(url):raise TimeoutError('unavailable')
    monkeypatch.setattr(sources,'fetch',fetch)
    with pytest.raises(sources.PartialSourceError) as e:d.collect(s)
    assert e.value.found==0
    p=paging.progress(s['id']);assert p['offset']==24 and len(p['errors'])==2
    assert p['watermark']=='2026-09-01T00:00:00Z'


def test_index_drains_saved_articles_before_expanding_more_pages(client,monkeypatch):
    s=copy.deepcopy(source('index'));s['config'].update(limit=1,recheck_body=True);base=s['url'];prefix=s['config']['path_prefix'];calls=[]
    paging.save_progress(s['id'],{'pending':[{'url':base.rstrip('/')+'/old'}],'index_pending':[base+'?page=2']})
    def fetch(url):
        calls.append(url)
        if url==base:return f'<a href="{prefix}new">New</a><a href="?page=2">Next</a>'.encode(),url,'text/html'
        return ('<main><h1>Release</h1><p>'+'original source '*20+'</p></main>').encode(),url,'text/html'
    monkeypatch.setattr(sources,'fetch',fetch)
    with pytest.raises(sources.PartialSourceError):d.collect(s)
    assert base+'?page=2' not in calls
    assert paging.progress(s['id'])['index_pending']==[base+'?page=2']
    assert not any(x['url'].endswith('/old') for x in paging.progress(s['id'])['pending'])
