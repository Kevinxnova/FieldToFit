"""Private name workflow: real identity boundaries, evidence gates and daily caps."""
import hashlib
import json
from datetime import datetime,timedelta,timezone
import pytest
from test_knowledge import client,ADMIN
from backend.db import get_db
from backend.knowledge import discovery as d, discovery_names as n, source_catalog, store


def lead(title,url,points=0,body='',original=None,version=''):
    source=next(s for s in source_catalog.definitions() if s['id']=='daily-hn-hot')
    d.capture(source,{'title':title,'url':url,'summary':body,'version':version,
        'materials':[d.material(url,body)] if body else [],'metrics':{'points':points},
        'metadata':{'original_url':original} if original else {}})
    return 'discovery:'+store.stable_id('daily',store.canonical_url(url),version)


def group(name):return next(g for g in n.overview()['items'] if g['name']==name and g['version']=='')


def mat(url='https://typesafe.ai/blog/introducing-system-one-models-and-jev'):
    body='Jev is a System One decision model from TypeSafe. Jevons is a namesake. '+('Official release and authorship material. '*5)
    return {'url':url,'body':body,'quote':'Jev is a System One decision model from TypeSafe.','coverage':'full_text','content_hash':hashlib.sha256(body.encode()).hexdigest()}


def investigation(g,outcome='recommend'):
    m=mat()
    return {'fingerprint':g['fingerprint'],'outcome':outcome,'reason':'已读官方发布；Jev 是结构化决策模型，TypeSafe 是组织，不是别名。',
        'ai_relevance':'confirmed','searches':['Jev TypeSafe official release'],'materials':[m],
        'identities':[{'key':'typesafe.ai/jev','refs':[l['ref'] for l in g['leads']],
            'basis':'官方发布正文明确署名和产品关系','evidence':[m['url']],
            'organization':'TypeSafe','change':'Jev 结构化决策模型的发布，需下一步与用户对齐推荐'}]}


def test_jev_group_disambiguation_versions_and_reprints(client):
    lead('Introducing Jev and System One','https://typesafe.ai/blog/introducing-system-one-models-and-jev',642)
    lead('Jev review by independent author','https://example.org/jev-review')
    lead('Jev mirror','https://mirror.example.org/jev',original='https://typesafe.ai/blog/introducing-system-one-models-and-jev')
    lead('Jevons paradox discussion','https://example.org/jevons',150)
    lead('Jev v2 release','https://example.org/jev-v2',150)
    n.refresh();g=group('Jev');names=[(x['name'],x['version']) for x in n.overview()['items']]
    assert g['families']==2 and len(g['leads'])==3
    assert len(g['known_objects'])==len({x['id'] for x in g['known_objects']})
    assert ('Jevons','') in names and ('Jev','v2') in names
    assert g['version']=='' and all(l['mention']['quote']=='Jev' for l in g['leads'])
    n.prepare();assert n.review(g['id'],investigation(g))['saved']
    assert group('Jev')['review']['identities'][0]['organization']=='TypeSafe'
    with get_db() as db:
        assert db.execute('SELECT count(*) FROM fieldtofit_steward_aliases').fetchone()[0]==0
        assert db.execute('SELECT count(*) FROM fieldtofit_content_items WHERE published_json IS NULL').fetchone()[0]==0


def test_same_name_can_be_two_projects_without_public_merge(client):
    a=lead('Atlas new agent','https://one.example.org/atlas',200)
    b=lead('Atlas desktop agent','https://two.example.org/atlas')
    n.prepare();g=group('Atlas');payload=investigation(g);m2=mat('https://two.example.org/atlas');payload['materials'].append(m2)
    payload['identities']=[{'key':u,'refs':[r],'basis':'官方网站与作者署名分开','evidence':[m['url']],'change':'不同产品的发布'} for u,r,m in [('one.example.org/atlas',a,payload['materials'][0]),('two.example.org/atlas',b,m2)]]
    n.review(g['id'],payload);assert len(group('Atlas')['review']['identities'])==2


def test_reviewed_reprint_family_updates_display_without_public_writes(client):
    lead('Jev official release','https://typesafe.ai/blog/introducing-system-one-models-and-jev')
    lead('Jev reprint','https://mirror.example.org/jev')
    n.prepare();g=group('Jev');assert g['families']==2
    p=investigation(g);p['identities'][0]['families']={l['ref']:p['materials'][0]['url'] for l in g['leads']}
    n.review(g['id'],p);reviewed=group('Jev')
    assert reviewed['families']==1 and len({l['family'] for l in reviewed['leads']})==1
    assert n.review(g['id'],p)['unchanged']


def test_failed_trace_and_investigate_keep_pending_not_verified(client,monkeypatch):
    from backend.knowledge import sources
    monkeypatch.setattr(sources,'fetch',lambda *a,**k:(_ for _ in ()).throw(TimeoutError()))
    lead('Jev is new','https://example.org/jev',200);n.prepare();g=group('Jev')
    assert n.trace({'id':g['id'],'fingerprint':g['fingerprint'],'urls':['https://example.org/jev']})['items'][0]['status']=='pending'
    n.review(g['id'],{'fingerprint':g['fingerprint'],'outcome':'investigate','reason':'官网暂时无法读取，身份和变化点待核实'})
    assert group('Jev')['review']['outcome']=='investigate'
    with pytest.raises(ValueError):n.review(g['id'],{**investigation(g),'materials':[{**mat(),'coverage':'excerpt'}]})


def test_exact_extraction_body_names_and_stale_evidence(client):
    body='The new coding tool is called 新工具. It is maintained by Example Lab.'
    ref=lead('A new coding experience','https://example.org/tool',200,body)
    c=next(x for x in n.handoff()['candidates'] if x['ref']==ref);start=body.index('新工具')
    payload={'ref':ref,'fingerprint':c['name_fingerprint'],'mentions':[{'name':'新工具','field':'summary','start':start,'end':start+3,'quote':'新工具'}]}
    assert n.extract({'items':[payload]})['saved']==1
    assert group('新工具')['leads'][0]['mention']['method']=='local_extraction'
    with pytest.raises(ValueError):n.extract({'items':[{**payload,'mentions':[{**payload['mentions'][0],'start':0}]}]})
    lead('A new coding experience','https://example.org/tool',200,body+' Updated.')
    with pytest.raises(ValueError):n.extract({'items':[payload]})


def test_declined_same_evidence_suppressed_changed_evidence_reopens_and_audit(client):
    lead('Jev release','https://example.org/jev',200);n.prepare();g=group('Jev')
    p={'fingerprint':g['fingerprint'],'outcome':'not_recommended','reason':'已核对，暂不采用'}
    n.review(g['id'],p);assert group('Jev')['suppressed']
    assert n.review(g['id'],p)['unchanged']
    n.refresh();assert group('Jev')['suppressed']
    n.reopen(g['id'],{'fingerprint':g['fingerprint'],'reason':'用户希望重新核对新用途'})
    assert not group('Jev')['review'] and len(n.history(g['id'])['items'])==2
    n.review(g['id'],p)
    lead('Jev release','https://example.org/jev',200,'New official API change')
    n.refresh();assert not group('Jev')['review']


def test_daily_ten_groups_rotate_and_three_searches_ceiling(client,monkeypatch):
    for i in range(15):lead('Project'+str(i)+' released','https://example.org/p'+str(i),200)
    first=n.prepare();assert len(first['targets'])==10
    assert n.prepare()['targets']==first['targets']
    for target in first['targets']:
        n.review(target['id'],{'fingerprint':target['fingerprint'],'outcome':'investigate','reason':'已做三次检索，官方材料仍有缺口','searches':['one','two','three']})
    target=first['targets'][0]
    with pytest.raises(ValueError):n.review(target['id'],{'fingerprint':target['fingerprint'],'outcome':'investigate','reason':'再次搜索','searches':['four']})
    monkeypatch.setattr(n,'today',lambda:'2026-10-08')
    second=n.prepare();assert {t['id'] for t in second['targets']}!={t['id'] for t in first['targets']}
    assert len({t['id'] for t in first['targets']+second['targets']})==15


def test_selected_old_lead_and_auth_boundary(client):
    ref=lead('Jev old selected','https://example.org/old')
    with get_db() as db:
        db.execute("UPDATE fieldtofit_discoveries SET discovered_at=? WHERE id=?",((datetime.now(timezone.utc)-timedelta(days=30)).isoformat(),ref[10:]))
        db.execute("INSERT INTO fieldtofit_inbox(ref,status,updated_at) VALUES(?,'selected',?)",(ref,store.now()))
    n.refresh();assert group('Jev')['selected']
    assert client.get('/api/v1/admin/workspace/names').status_code==401
    result=client.get('/api/v1/admin/workspace/names',headers=ADMIN)
    assert result.status_code==200 and 'no-store' in result.headers['Cache-Control']
    assert client.post('/api/v1/admin/workspace/names/prepare',json={},headers=ADMIN).status_code==200


def test_five_material_budget_shared_by_tracing_and_local_import(client,monkeypatch):
    from backend.knowledge import sources
    lead('Jev is new','https://example.org/jev',200);n.prepare();g=group('Jev')
    m=mat();monkeypatch.setattr(sources,'fetch',lambda url,**k:(('<p>'+m['body']+'</p>').encode(),url,'text/html'))
    urls=['https://example.org/source'+str(i) for i in range(5)]
    read=n.trace({'id':g['id'],'fingerprint':g['fingerprint'],'urls':urls})['items']
    first={**read[0],'quote':m['quote']}
    p={'fingerprint':g['fingerprint'],'outcome':'investigate','reason':'沿用已取得的材料继续核验','materials':[first]}
    assert n.review(g['id'],p)['saved'] and n.review(g['id'],p)['unchanged']
    with pytest.raises(ValueError):n.review(g['id'],{**p,'reason':'额外读取新材料','materials':[mat()]})
    with pytest.raises(ValueError):n.trace({'id':g['id'],'fingerprint':g['fingerprint'],'urls':['https://example.org/sixth']})


def test_local_handoff_imports_all_batches_before_freezing_queue(client,monkeypatch,tmp_path):
    from scripts.maintenance import discovery_names as cli
    from types import SimpleNamespace
    for i in range(55):lead('新工具'+str(i)+' 发布','https://example.org/c'+str(i),200)
    candidates=n.handoff()['candidates'];items=[]
    for c in candidates:
        name=c['title'].split()[0]
        items.append({'ref':c['ref'],'fingerprint':c['name_fingerprint'],'mentions':[{'name':name,'field':'title','start':0,'end':len(name),'quote':name}]})
    extraction=tmp_path/'extractions.json';extraction.write_text(json.dumps(items))
    env=tmp_path/'isolated.env';env.write_text('ADMIN_PASSWORD='+ADMIN['X-Admin-Password'])
    steps=[]
    class Session:
        def request(self,method,url,headers,json,**kwargs):
            path='/api/'+url.split('/api/',1)[1]
            steps.append((path,len(json.get('items',[])) if json else 0))
            response=client.post(path,headers=headers,json=json) if method=='POST' else client.get(path,headers=headers)
            return SimpleNamespace(status_code=response.status_code,json=response.get_json)
    monkeypatch.setattr(cli.requests,'Session',Session)
    result=cli.run('http://isolated.local',env,tmp_path/'handoff.json',extraction)
    assert result['groups']==10 and [count for path,count in steps if path.endswith('/extract')]==[50,5]
    assert steps[2][0].endswith('/prepare') and n.overview()['total']==55
