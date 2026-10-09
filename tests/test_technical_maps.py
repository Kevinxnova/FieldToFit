"""Question maps and maintenance use isolated SQLite; no live publication or credentials."""
import copy
import json
from datetime import date,timedelta
import pytest
from test_knowledge import client,ADMIN,MCP
from test_content_workspace import call,migrate,publish,make
from backend.db import get_db
from backend.knowledge import content_workspace as ws, technical_maps as tm, map_maintenance as mm, editorial_batches as batches
from backend.knowledge.platform import PlatformError

SLUG='agent-context-cost'
URL='https://arxiv.org/html/2609.19969v1'

@pytest.fixture(autouse=True)
def focused_map_seed(monkeypatch):
    """Exercise this report's workflow independently of later curated reports."""
    seeds=ws.seeds()
    for item in seeds['news']['items']:
        if item['id']!='D-90':
            item.pop('technical_map',None)
    monkeypatch.setattr(ws,'seeds',lambda:copy.deepcopy(seeds))

def draft():return copy.deepcopy(next(x for x in ws.seeds()['news']['items'] if x['id']=='D-90'))
def reading(version=0,body=None,**extra):return {'url':URL,'version':version,'status':'read','change_kind':'baseline','body':body or ('Actual original technical report material. '*15),'first_published_at':'2026-09-17','revised_at':None,'report_version':'arXiv v1','locator':'§2–3','note':'已实际读取架构、条件和局限。',**extra}
def edit(client,changes):
    d=call(client,'/content/news/D-90',method='get').json;changes(d['draft']);r=call(client,'/content/news/D-90',d,'patch');assert r.status_code==200,r.json
    return r.json

def test_case_graph_and_http_mcp_exact_match(client):
    migrate(client);public=client.get('/api/v1/platform/maps?slug='+SLUG).json
    obj=public['items'][0];assert obj['reports'][0]['first_published_at']=='2026-09-17'
    assert len(obj['nodes'])==5 and set(e['relation'] for e in obj['edges'])==set(tm.RELATIONS)
    metrics=[m for n in obj['nodes'] for m in n['metrics']]
    assert [m['value'] for m in metrics]==[8,890,.125]
    assert all(m['unit'] and m['baseline'] and m['conditions'] for m in metrics)
    rpc=client.post('/api/mcp/curated',headers=MCP,json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'curated_maps','arguments':{'slug':SLUG}}}).json['result']
    assert rpc['structuredContent']==public
    assert client.get('/api/v1/platform/maps?slug='+SLUG+'&revision=stale').status_code==409
    assert client.get('/api/v1/platform/maps?archive=bad').status_code==400

@pytest.mark.parametrize('mutate',[
 lambda m:m['nodes'][0]['evidence'][0].update(source_id='missing'),
 lambda m:m['nodes'][1].update(evidence=['bad shape']),
 lambda m:m['nodes'][1].update(metrics=[42]),
 lambda m:m['nodes'][1].update(stage=True),
 lambda m:m['nodes'][1]['metrics'][0].update(value=True),
 lambda m:m['nodes'][1]['metrics'][0].update(unit=''),
 lambda m:m['edges'][0].update(to='missing'),
 lambda m:m['edges'].append({'from':'v41','to':'ced','relation':'inheritance','label':'loop','evidence':[{'source_id':'report','locator':'§1'}]}),
 lambda m:m['nodes'][0]['evidence'][0].update(fragment='javascript:alert(1)'),
 lambda m:m['reports'][0].update(first_published_at='2999-01-01'),
 lambda m:m['reports'][0].update(substantive_revision=True,revised_at='2026-10-01',revision_note=''),
 lambda m:m['nodes'].append({**copy.deepcopy(m['nodes'][0]),'id':'orphan'}),
])
def test_bad_graph_cannot_preview_or_publish(client,mutate):
    migrate(client);original=tm.maps();edit(client,lambda d:mutate(d['technical_map']))
    p=call(client,'/content/news/D-90/preview').json;assert p['ready'] is False,p
    assert tm.maps()==original
    r=call(client,'/content/news/D-90/publish',{'draft_version':p['draft_version'],'confirmed':True,'reason':'must fail','review_token':'bad'})
    assert r.status_code in (400,409)


def test_draft_history_private_notes_restore_and_withdraw(client):
    migrate(client);before=tm.maps();edit(client,lambda d:d['technical_map'].update(takeaway='Corrected editorial explanation',change_summary='补充条件',private_reason='PRIVATE-MAP-SECRET'))
    assert tm.maps()==before and tm.history(SLUG)['total']==1
    publish(client,'news','D-90');after=tm.maps();assert after['revision']!=before['revision']
    history=tm.history(SLUG);assert history['total']==2
    assert 'PRIVATE-MAP-SECRET' not in json.dumps(history)
    with get_db() as db:db.execute("UPDATE fieldtofit_content_history SET reason='PRIVATE-EDITOR-SECRET' WHERE kind='news' AND item_id='D-90'")
    assert 'PRIVATE-EDITOR-SECRET' not in json.dumps(tm.history(SLUG))
    assert any(f['field']=='takeaway' for f in tm.compare(SLUG)['fields'])
    seq=history['items'][1]['revision'];d=ws.detail('news','D-90')
    r=call(client,'/content/news/D-90/restore',{'seq':seq,'draft_version':d['draft_version']});assert r.status_code==200,r.json
    assert tm.maps()==after and tm.history(SLUG)['total']==2
    d=ws.detail('news','D-90');r=call(client,'/content/news/D-90/withdraw',{'draft_version':d['draft_version'],'reason':'correction'});assert r.status_code==200,r.json
    for path in ('/api/v1/platform/maps?slug='+SLUG,'/api/v1/platform/maps/'+SLUG+'/history','/api/v1/platform/maps/'+SLUG+'/compare'):
        assert client.get(path).status_code==404


def test_checks_do_not_refresh_public_dates_failed_keeps_baseline_and_conflicts(client):
    migrate(client);before=tm.maps();mm.check(reading());assert tm.maps()==before
    with get_db() as db:old=dict(db.execute('SELECT * FROM fieldtofit_map_checks WHERE url=?',(URL,)).fetchone())
    with pytest.raises(PlatformError):mm.check(reading())
    mm.check({'url':URL,'version':1,'status':'failed','error':'actual transport failure'})
    with get_db() as db:new=dict(db.execute('SELECT * FROM fieldtofit_map_checks WHERE url=?',(URL,)).fetchone())
    assert new['fingerprint']==old['fingerprint'] and new['last_success_at']==old['last_success_at'] and new['proof']==old['proof']
    mm.check(reading(version=2));assert tm.maps()==before and tm.history(SLUG)['total']==1
    assert mm.handoff()['reports'][0]['last_status']=='read'
    assert client.get('/api/v1/admin/workspace/maps/handoff').status_code==401
    assert client.post('/api/v1/admin/workspace/maps/check',headers={'X-Read-Token':'anything'},json=reading()).status_code==401
    assert 'Actual original' not in json.dumps(tm.maps())


def test_proposal_requires_read_owner_decision_and_preserves_stable_map(client):
    migrate(client);content=draft();content['technical_map']['takeaway']='More precise explanation';content['technical_map']['change_summary']='更正条件'
    args={'content':content,'reason':'已核对报告，补充范围','base_revision':tm.maps(slug=SLUG)['revision']}
    with pytest.raises(PlatformError):mm.propose(args)
    mm.check(reading());before=tm.maps();result=mm.propose(args)
    assert not result['published'] and not result['draft_created'] and tm.maps()==before
    with get_db() as db:t=batches._topic(db,result['id'])
    with pytest.raises(PlatformError):batches.attach(t['id'],{'version':t['version'],'kind':'news','target_id':'D-90'})
    batches.decide(t['id'],{'version':t['version'],'decision':'continue'})
    with get_db() as db:t=batches._topic(db,result['id'])
    with pytest.raises(PlatformError):batches.attach(t['id'],{'version':t['version'],'kind':'news','target_id':'D-01'})
    batches.attach(t['id'],{'version':t['version'],'kind':'news','target_id':'D-90'})
    with get_db() as db:t=batches._topic(db,result['id'])
    mm.apply_proposal(t['id'],{'topic_version':t['version'],'draft_version':ws.detail('news','D-90')['draft_version']})
    assert tm.maps()==before
    publish(client,'news','D-90');assert tm.maps()['items'][0]['slug']==SLUG
    with pytest.raises(PlatformError):mm.propose(args)
    edit(client,lambda d:d['technical_map'].update(slug='different-entry'))
    assert not call(client,'/content/news/D-90/preview').json['ready']


def test_report_dates_archive_cosmetic_and_substantive(client,monkeypatch):
    migrate(client)
    monkeypatch.setattr(ws,'today',lambda:'2026-10-20')
    assert tm.maps(archive='historical')['total']==1 and tm.maps(archive='recent')['total']==0
    edit(client,lambda d:d['technical_map']['reports'][0].update(revised_at='2026-10-19',revision_note='排版调整'))
    publish(client,'news','D-90');assert tm.maps(archive='historical')['total']==1
    edit(client,lambda d:d['technical_map']['reports'][0].update(substantive_revision=True,revision_note='新增独立实验设置与结果'))
    publish(client,'news','D-90');assert tm.maps(archive='recent')['total']==1
    assert tm.maps()['items'][0]['reports'][0]['first_published_at']=='2026-09-17'


def test_no_js_pages_sources_sitemap_and_withdraw(client):
    migrate(client);page=client.get('/maps/'+SLUG,headers={'Host':'fieldtofit.top'});assert page.status_code==200,page.data
    html=page.data.decode();assert '890' in html and 'bytes／token' in html and URL+'#S2.SS3' in html and 'rel="canonical" href="https://fieldtofit.top/maps/'+SLUG+'"' in html
    assert client.get('/maps/unknown').status_code==404
    assert '/maps/'+SLUG in client.get('/sitemap.xml').data.decode()
    d=ws.detail('news','D-90');call(client,'/content/news/D-90/withdraw',{'draft_version':d['draft_version'],'reason':'withdraw'})
    assert client.get('/maps/'+SLUG).status_code==404
    assert '/maps/'+SLUG not in client.get('/sitemap.xml').data.decode()


def test_recent_intake_uses_source_dates_and_daily_budget(client):
    migrate(client)
    from backend.knowledge import discovery, source_catalog
    source=next(s for s in source_catalog.definitions() if s['config'].get('mode')=='arxiv')
    for i in range(12):discovery.capture(source,{'title':'Paper '+str(i),'url':'https://arxiv.org/abs/2610.'+str(10000+i),'published_at':ws.today()+'T00:00:00+08:00','metadata':{'primary':True},'summary':'technical paper'})
    discovery.capture(source,{'title':'Old report','url':'https://arxiv.org/abs/2501.10000','published_at':'2025-01-01T00:00:00Z','metadata':{'upstream_updated_at':ws.today()+'T00:00:00Z','revision_kind':'cosmetic'},'summary':'old'})
    board=mm.handoff();assert len(board['targets'])==10 and board['backlog']==3
    assert any(x['reason'].startswith('超过30日') for x in board['excluded'])
    targets=[x for x in board['reports'] if x['url']!=URL]
    for t in targets[:10]:mm.check({'url':t['url'],'version':0,'status':'failed','error':'actual source failure'})
    with pytest.raises(PlatformError) as err:mm.check({'url':targets[10]['url'],'version':0,'status':'failed','error':'outside budget'})
    assert err.value.code=='map_budget_reached'
    assert tm.maps()['total']==1


def test_nonfinite_units_and_private_sources_rejected(client):
    value=draft();value['technical_map']['nodes'][1]['metrics'][0]['value']=float('inf')
    with pytest.raises(ValueError):tm.metadata(value)
    value=draft();value['sources'][0]['url']='https://127.0.0.1/report'
    with pytest.raises(ValueError):tm.metadata(value)


def test_beijing_morning_check_is_same_day_and_can_propose(client,monkeypatch):
    migrate(client);monkeypatch.setattr(ws,'stamp',lambda:'2026-10-06T23:30:00+00:00');monkeypatch.setattr(ws,'today',lambda:'2026-10-07')
    mm.check(reading());assert not next(r for r in mm.handoff()['reports'] if r['url']==URL)['needs_check']
    content=draft();content['technical_map']['caution']='更明确的条件范围'
    assert mm.propose({'content':content,'base_revision':tm.maps(slug=SLUG)['revision'],'reason':'07:30实际核对'})['published'] is False


def test_report_html_abs_representations_share_exact_version(client):
    migrate(client)
    from backend.knowledge import discovery,source_catalog
    source=next(s for s in source_catalog.definitions() if s['id']=='daily-map-research')
    discovery.capture(source,{'title':'Fixture technical report','url':'https://arxiv.org/abs/2610.10050v1','published_at':ws.today()+'T00:00:00+08:00','metadata':{'primary':True,'first_published_at':ws.today()},'summary':'Synthetic report for identity workflow validation'})
    url='https://arxiv.org/html/2610.10050v1'
    mm.check(reading(url=url,first_published_at=ws.today()))
    with pytest.raises(PlatformError):mm.check(reading(url='https://arxiv.org/html/2610.10050v2',first_published_at=ws.today()))
    content=draft();content['technical_map'].update(slug='fixture-new-question',question='新报告的独立问题');content['sources'][0]['url']=url;content['technical_map']['reports'][0]['first_published_at']=ws.today()
    result=mm.propose({'content':content,'reason':'Synthetic workflow fixture','base_revision':None})
    assert not result['draft_created'] and not result['published']
    with get_db() as db:topic=batches._topic(db,result['id'])
    assert topic['source_ref'].startswith('discovery:') and topic['proposal']['report_fingerprints']
    assert mm.propose({'content':content,'reason':'Synthetic workflow fixture','base_revision':None})['suppressed'] is False  # Same batch: linked once, no duplicate member.
    with get_db() as db:assert db.execute('SELECT count(*) FROM fieldtofit_editorial_members WHERE topic_id=?',(result['id'],)).fetchone()[0]==1
