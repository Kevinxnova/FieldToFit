"""Realistic isolated daily discovery and review boundaries; no production writes."""
import json
from datetime import datetime,timedelta,timezone
import pytest
from test_knowledge import client, ADMIN
from backend.db import get_db
from backend.knowledge import source_catalog as catalog, discovery as d, candidate_priority as rank, content_workspace as ws, store, sources


def source(mode='hub'):
    return next(x for x in catalog.definitions() if x['config']['mode']==mode)


def item(**extra):
    body='A useful agent development framework. Quick start: pip install example. '+('Source documentation. '*12)
    return {'url':'https://github.com/example/agent','title':'Example Agent','summary':'Agent framework with usage instructions','type':'agent','published_at':store.now(),
            'materials':[d.material('https://github.com/example/agent',body)],'metadata':{'primary':True,'change':'repository','upstream_updated_at':store.now()},**extra}


def public(client):
    return [client.get('/api/v1/platform/'+kind).json for kind in ('news','watch','model-landscape')]


def test_catalog_distinguishes_registered_collected_and_published(client):
    data=client.get('/api/v1/platform/source-catalog').json
    assert len(data['tracked'])==12
    company=next(x for x in data['tracked'] if x['id']=='deepseek')
    assert company['registered_count']==2 and company['successful_count']==0 and not company['planned']
    sid=source()['id']
    with get_db() as db:
        db.execute("UPDATE knowledge_sources SET enabled=0,error='PRIVATE_FAILURE' WHERE id=?",(sid,))
    again=client.get('/api/v1/platform/source-catalog').json
    row=next(x for x in again['channels'] if x['id']==sid)
    assert not row['daily_scheduled'] and row['state']=='paused'
    assert 'PRIVATE_FAILURE' not in json.dumps(again)
    assert 'PRIVATE_FAILURE' in json.dumps(client.get('/api/v1/admin/workspace/source-catalog',headers=ADMIN).json)
    assert client.get('/api/v1/admin/workspace/source-catalog').status_code==401


def test_low_attention_usable_project_precedes_high_star_unverified(client):
    s=source();d.capture(s,item(metrics={'stars':3}))
    d.capture(s,item(url='https://example.org/popular',title='Popular claim',materials=[],metadata={'primary':False},metrics={'stars':100000}))
    page=ws.inbox();assert page['items'][0]['title']=='Example Agent'
    assert page['items'][0]['priority']['group']=='priority'
    assert page['items'][1]['priority']['group']=='verify'
    assert not any(x['kind']=='stars_change' for x in page['items'][0]['priority']['signals'])


def test_repeat_observation_deduplicates_and_retains_all_origins(client):
    a=source();b=source('github');x=item()
    assert d.capture(a,x)==1
    assert d.capture(a,x)==0
    assert d.capture(b,x)==0
    assert ws.inbox()['total']==1
    with get_db() as db:assert db.execute('SELECT count(*) FROM fieldtofit_discovery_origins').fetchone()[0]==2


def test_versions_are_distinct_and_public_content_never_changes(client):
    before=public(client);s=source();x=item(version='v1')
    d.capture(s,x);d.capture(s,{**x,'version':'v2'})
    assert ws.inbox()['total']==2 and public(client)==before
    ws.migrate();ref=ws.inbox()['items'][0]['ref']
    ws.select({'ref':ref,'action':'select','kind':'watch','type':'agent'})
    assert public(client)==before
    assert ws.inbox(status='selected')['total']==1
    assert client.get('/api/v1/admin/workspace/candidate?ref='+ref).status_code==401
    detail=client.get('/api/v1/admin/workspace/candidate?ref='+ref,headers=ADMIN).json
    assert detail['materials'][0]['body'] and detail['origins']


def test_override_is_private_requires_reason_and_survives_refresh(client):
    s=source();d.capture(s,item());ref=ws.inbox()['items'][0]['ref']
    with pytest.raises(ValueError):rank.override({'ref':ref,'group':'verify'})
    rank.override({'ref':ref,'group':'verify','reason':'需要先检查许可证'})
    rank.refresh([ref]);row=ws.inbox()['items'][0]
    assert row['priority']['group']=='verify' and row['priority']['automatic_group']=='priority'
    rank.override({'ref':ref,'group':None});assert ws.inbox()['items'][0]['priority']['group']=='priority'
    assert client.post('/api/v1/admin/workspace/priority',json={'ref':ref,'group':None}).status_code==401


def test_attention_delta_requires_dated_same_source_observations(client):
    s=source();x=item(metrics={'stars':180});d.capture(s,x)
    earlier=(datetime.now(timezone.utc)-timedelta(days=1)).isoformat().replace('+00:00','Z')
    with get_db() as db:db.execute('INSERT INTO fieldtofit_attention_observations VALUES(?,?,?,?,?)',(x['url'],s['id'],earlier[:10],earlier,store.encode({'stars':100})))
    rank.refresh();ref=ws.inbox()['items'][0]['ref'];rank.refresh([ref])
    signal=next(z for z in ws.inbox()['items'][0]['priority']['signals'] if z['kind']=='stars_change')
    assert signal['value']==80 and signal['from']==earlier


def test_hub_author_filter_actual_card_and_missing_card(client,monkeypatch):
    s=source();name=s['config']['author']+'/example';calls=[]
    def fetch(url,*a,**kw):
        calls.append(url)
        if '/api/models?' in url:
            assert 'author='+s['config']['author'] in url
            return json.dumps([{'id':name,'sha':'commit','lastModified':store.now(),'createdAt':store.now(),'likes':2}]).encode(),url,'application/json',{}
        return ('# Model\nUsage\n'+'real source material '*20).encode(),url,'text/plain'
    monkeypatch.setattr(sources,'fetch',fetch)
    assert d.collect(s)==(1,1)
    assert ws.inbox()['items'][0]['priority']['group']=='priority'
    with get_db() as db:assert 'real source material' in db.execute('SELECT materials FROM fieldtofit_discoveries').fetchone()[0]
    def missing(url,*a,**kw):
        if '/api/models?' in url:return fetch(url,*a,**kw)
        raise TimeoutError('not available')
    monkeypatch.setattr(sources,'fetch',missing)
    with pytest.raises(sources.PartialSourceError):d.collect(s)
    assert any('模型卡读取失败' in x for x in ws.inbox()['items'][0]['priority']['unknowns'])


def test_article_navigation_does_not_change_body():
    a=d.Article();a.feed('<nav>old menu</nav><main><h1>Model release</h1><p>Useful original text</p></main><footer>2025</footer>')
    b=d.Article();b.feed('<nav>new menu</nav><main><h1>Model release</h1><p>Useful original text</p></main><footer>2026</footer>')
    assert a.body==b.body and 'menu' not in a.body


def test_bad_article_saved_for_retry_without_fabricated_date(client,monkeypatch):
    s=source('feed');today=store.now()
    xml=f'<rss><channel><item><title>Actual release</title><link>https://example.org/article</link></item></channel></rss>'.encode()
    def fetch(url,*a,**kw):
        if url==s['url']:return xml,url,'text/xml'
        raise TimeoutError('blocked')
    monkeypatch.setattr(sources,'fetch',fetch)
    with pytest.raises(sources.PartialSourceError):d.collect(s)
    assert ws.inbox()['total']==1
    assert ws.inbox()['items'][0]['published_at'] is None
    assert ws.inbox()['items'][0]['priority']['group']=='verify'
    from backend.knowledge.paging import progress
    assert progress(s['id'])['pending'][0]['url']=='https://example.org/article'


def test_daily_scheduler_includes_new_discovery_without_publication(client,monkeypatch):
    from backend.knowledge import platform_maintenance as pm,model_landscape
    monkeypatch.setattr('backend.knowledge.stewardship.check_materials',lambda *a,**k:{'results':[],'deferred':False})
    sid=source()['id'];calls=[]
    monkeypatch.setattr(sources,'list_sources',lambda:[{**source(),'enabled':True,'last_attempt_at':None}])
    monkeypatch.setattr(sources,'run_daily',lambda source_id,**kw: calls.append(source_id) or {'results':[]})
    monkeypatch.setattr(model_landscape,'check_sources',lambda:{'status':'success'})
    before=public(client);pm.run_daily();assert calls==[sid] and public(client)==before


def test_review_groups_and_date_pagination_remain_separate(client):
    for n in range(35):d.capture(source(),item(url=f'https://example.org/{n}',title=f'Project {n}'))
    assert ws.inbox(group='priority')['total']==35
    assert len(ws.inbox(group='priority',offset=30)['items'])==5
    assert ws.inbox(group='verify')['total']==0
    with pytest.raises(ValueError):ws.inbox(order='unknown')


def test_completed_feed_entries_do_not_create_permanent_backlog(client,monkeypatch):
    s=source('feed');s['config']['limit']=1;calls=[]
    xml=b'<rss><channel><item><title>A</title><link>https://openai.com/a</link></item><item><title>B</title><link>https://openai.com/b</link></item></channel></rss>'
    def fetch(url,*a,**kw):
        calls.append(url)
        if url==s['url']:return xml,url,'text/xml'
        return ('<main><h1>Release</h1><p>'+'Original body '*30+'</p></main>').encode(),url,'text/html'
    monkeypatch.setattr(sources,'fetch',fetch)
    with pytest.raises(sources.PartialSourceError):d.collect(s)
    assert d.collect(s)==(1,1)
    assert d.collect(s)==(0,0)
    assert calls.count('https://openai.com/a')==calls.count('https://openai.com/b')==1


def test_metrics_alone_do_not_create_content_changes(client):
    s=source();x=item(version='fixed',metrics={'stars':10})
    assert d.capture(s,x)==1
    with get_db() as db:original=db.execute('SELECT discovered_at FROM fieldtofit_discoveries').fetchone()[0]
    assert d.capture(s,{**x,'metrics':{'stars':11}})==0
    with get_db() as db:assert db.execute('SELECT discovered_at FROM fieldtofit_discoveries').fetchone()[0]==original


def test_fetch_budget_rejects_work_after_deadline(monkeypatch):
    import time
    token=sources.COLLECTION_DEADLINE.set(time.monotonic()-1)
    try:
        with pytest.raises(TimeoutError):sources.fetch('https://example.org')
    finally:sources.COLLECTION_DEADLINE.reset(token)


def test_unfinished_page_keeps_already_captured_models(client,monkeypatch):
    s=source();s['config']['author']='openai'
    from backend.knowledge.paging import save_progress
    save_progress(s['id'],{'next_url':'https://huggingface.co/api/models?cursor=old'})
    def fetch(url,*a,**kw):
        if 'cursor=old' in url:raise TimeoutError('source timed out')
        if '/api/models?' in url:return json.dumps([{'id':'openai/test','sha':'v1','lastModified':store.now()}]).encode(),url,'application/json',{}
        return ('Usage '+'Original model text '*30).encode(),url,'text/plain'
    monkeypatch.setattr(sources,'fetch',fetch)
    with pytest.raises(sources.PartialSourceError) as error:d.collect(s)
    assert error.value.found==1 and ws.inbox()['total']==1


def test_catalog_exposes_concrete_scope_instead_of_adapter_disclaimer(client):
    data=catalog.registry()
    assert next(c for c in data['channels'] if c['id']==source()['id'])['scope']==source()['config']['scope']


def test_index_date_labels_can_be_split_across_elements():
    article=d.Article()
    article.feed('<a href=\"/news/current\"><span>Announcements</span><span>Sep 10, 2026</span><span>New model</span></a>')
    assert d.displayed_date(article.link_labels[0][1])=='2026-09-10'


def test_daily_claim_uses_beijing_day_not_elapsed_24_hours(client,monkeypatch):
    from zoneinfo import ZoneInfo
    yesterday=(datetime.now(ZoneInfo('Asia/Shanghai'))-timedelta(days=1)).replace(hour=23,minute=59,second=0)
    s=source()
    with get_db() as db:db.execute("UPDATE knowledge_sources SET last_attempt_at=?,status='success' WHERE id=?",(yesterday.isoformat(),s['id']))
    calls=[]
    monkeypatch.setattr(sources,'collect_source',lambda x:calls.append(x['id']) or (0,0))
    sources.run_daily(s['id'])
    assert calls==[s['id']]
    sources.run_daily(s['id'])
    assert calls==[s['id']]


def test_bounded_parallel_daily_claims_keep_separate_candidates(client,monkeypatch):
    from backend.knowledge import platform_maintenance as pm,model_landscape
    monkeypatch.setattr('backend.knowledge.stewardship.check_materials',lambda *a,**k:{'results':[],'deferred':False})
    subset=[{**s,'enabled':True,'last_attempt_at':None} for s in catalog.definitions()[:3]]
    monkeypatch.setattr(sources,'list_sources',lambda:subset)
    monkeypatch.setattr(model_landscape,'check_sources',lambda:{'status':'success'})
    monkeypatch.setattr(sources,'collect_source',lambda s:(1,d.capture(s,item(url='https://example.org/'+s['id']))))
    result=pm.run_daily(budget_seconds=10)
    assert len(result['results'])==3 and all(r['status']=='success' for r in result['results'])
    assert ws.inbox()['total']==3


def test_remote_discovery_and_maintained_material_use_guarded_single_commit(client,monkeypatch):
    """Real SQL batches, no transaction held across remote reads; races roll back."""
    from contextlib import contextmanager
    from backend.db import TursoConnection,TursoCursor
    from backend.knowledge import workspace_transactions as tx, platform_maintenance as maintenance
    from backend.knowledge.platform import PlatformError
    batches=[];race=[None]
    class Remote(TursoConnection):
        def __init__(self,db):self.db=db
        def execute(self,sql,params=()):
            assert not self.db.in_transaction
            return TursoCursor(self.db.execute(sql,params).fetchall(),0,None)
        def atomic_statements(self,statements):
            assert not self.db.in_transaction
            if race[0]:
                fn=race[0];race[0]=None;fn(self.db);self.db.commit()
            # Simulate a pooled remote SQLite session left with a prior guard table.
            self.db.execute('CREATE TEMP TABLE IF NOT EXISTS workspace_guard(n INTEGER)')
            self.db.execute('INSERT INTO workspace_guard VALUES (99)');self.db.commit()
            batches.append(len(statements));self.db.execute('BEGIN IMMEDIATE')
            try:
                for sql,args in statements:self.db.execute(sql,args)
                self.db.commit()
            except Exception:self.db.rollback();raise
    @contextmanager
    def remote():
        with get_db() as db:yield Remote(db)
    monkeypatch.setattr(tx,'get_db',remote)
    s=source();x=item()
    assert d.capture(s,x)==1 and d.capture(s,x)==0
    changed={**x,'title':'Updated original'}
    race[0]=lambda db:db.execute("UPDATE fieldtofit_discoveries SET title='Concurrent update'")
    with pytest.raises(PlatformError):d.capture(s,changed)
    with get_db() as db:assert db.execute('SELECT title FROM fieldtofit_discoveries').fetchone()[0]=='Concurrent update'
    sid=maintenance.register('example/source','Source','tool')
    ms={'id':sid,'url':'https://github.com/example/source','config':{'name':'Source','object_type':'tool'}}
    body='Documented AI tool with useful setup instructions.'
    import hashlib
    m={'key':'readme','url':ms['url']+'/README.md','body':body,'hash':hashlib.sha256(body.encode()).hexdigest(),'coverage':'full_text'}
    assert maintenance.stage(ms,[m])==(1,1)
    assert maintenance.stage(ms,[m])==(1,0)
    assert len(batches)==5


def test_failed_old_model_card_is_retried_despite_recent_watermark(client,monkeypatch):
    s=source();name=s['config']['author']+'/old-model';card_calls=[]
    old=(datetime.now(timezone.utc)-timedelta(days=365)).isoformat().replace('+00:00','Z')
    def fetch(url,*a,**kw):
        if '/api/models?' in url:return json.dumps([{'id':name,'sha':'old-commit','lastModified':old,'createdAt':old}]).encode(),url,'application/json',{}
        card_calls.append(url);raise TimeoutError('Card unavailable')
    monkeypatch.setattr(sources,'fetch',fetch)
    with pytest.raises(sources.PartialSourceError):d.collect(s)
    with pytest.raises(sources.PartialSourceError):d.collect(s)
    assert len(card_calls)==2 and ws.inbox()['total']==1
