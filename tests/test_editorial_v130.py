"""Recommendation decisions, publication boundaries and frozen public source reading."""
import copy
import hashlib
import json
import pytest
from test_knowledge import client, ADMIN, MCP
from test_content_workspace import call,migrate,make,valid,publish
from backend.db import get_db
from backend.knowledge import editorial_batches as b, content_materials as cm, discovery as d, source_catalog as catalog
from backend.knowledge.platform import PlatformError


def proposal(**extra):
    return {'event_url':'https://example.org/event','fingerprint':'evidence-v1','proposal':{'title':'A release','reason':'A concrete primary change','summary':'A reviewed proposal'},**extra}


def topic(batch,ident):return next(t for t in b.detail(batch)['items'] if t['id']==ident)


def mat(**extra):
    return {'id':'readme','title':'Original README','url':'https://example.org/README.md','body':'SOURCE-ONLY '+('preserve original text\n'*50),
        'coverage':'full_text','checked_at':b.today(),'upstream_revision':'commit-1','approved':True,
        'rights':{'basis':'MIT permission','url':'https://example.org/LICENSE','notice':'Retain this notice'},**extra}


def with_material(client,ident='CW-M01',material=None):
    doc=call(client,'/content/watch/'+ident,method='get').json
    doc['draft']['reading_materials']=[material or mat()]
    r=call(client,'/content/watch/'+ident,doc,'patch');assert r.status_code==200,r.json
    return r.json


def rpc(client,name,args):
    return client.post('/api/mcp/curated',headers=MCP,json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':args}}).json['result']


def test_batches_dedup_new_evidence_and_due_decision(client,monkeypatch):
    first=b.create({'day':'2026-09-12'})['id'];second=b.create({'day':'2026-09-13'})['id']
    ident=b.propose(first,proposal())['id'];assert b.propose(second,proposal())['suppressed']
    assert len(b.detail(first)['items'])==1 and not b.detail(second)['items']
    v=topic(first,ident)['version'];b.decide(ident,{'version':v,'decision':'declined'})
    with pytest.raises(PlatformError):b.decide(ident,{'version':v,'decision':'continue'})
    assert not b.propose(second,proposal(fingerprint='evidence-v2'))['suppressed']
    t=topic(second,ident);assert t['decision']=='pending' and any(h['action']=='evidence_changed' for h in t['history'])
    b.decide(ident,{'version':t['version'],'decision':'later','review_on':b.today()})
    assert b.overview()['due'][0]['id']==ident
    b.propose(second,proposal(fingerprint='evidence-v2'));assert topic(second,ident)['decision']=='pending'


def test_delivery_requires_receipt_and_prepared_is_not_delivered(client):
    batch=b.create({});assert b.overview()['delivery']=='pending'
    batch=b.delivery(batch['id'],{'version':batch['version'],'state':'prepared','body_hash':'hash'})
    assert b.overview()['notice'] and batch['delivery_state']=='prepared'
    with pytest.raises(PlatformError):b.delivery(batch['id'],{'version':batch['version'],'state':'delivered','confirmed':True})
    batch=b.delivery(batch['id'],{'version':batch['version'],'state':'delivered','confirmed':True,'receipt':'verified thread/message-id'})
    assert not b.overview()['notice']
    with pytest.raises(PlatformError):b.delivery(batch['id'],{'version':batch['version'],'state':'failed'})
    assert client.get('/api/v1/admin/workspace/batches').status_code==401


def test_confirmed_attach_publish_and_changed_evidence_not_marked_done(client):
    migrate(client);batch=b.create({})['id']
    ref=call(client,'/inbox',{'title':'Example','url':'https://example.org/event','summary':'Candidate'}).json['ref']
    ident=b.propose(batch,proposal(ref=ref))['id'];t=topic(batch,ident)
    with pytest.raises(PlatformError):b.attach(ident,{'version':t['version'],'kind':'watch'})
    b.decide(ident,{'version':t['version'],'decision':'continue'});t=topic(batch,ident)
    linked=b.attach(ident,{'version':t['version'],'kind':'watch','type':'tool'})
    valid(client,'watch',linked['id']);publish(client,'watch',linked['id'])
    assert topic(batch,ident)['decision']=='published'
    b.propose(batch,proposal(ref=ref,fingerprint='changed'))
    publish(client,'watch',linked['id'])
    assert topic(batch,ident)['decision']=='pending' # unrelated publication is not a new decision
    backup=call(client,'/backup',method='get').json['tables']
    assert backup['fieldtofit_editorial_events']


def test_private_material_review_gates_and_frozen_continuation(client):
    migrate(client);with_material(client,material=mat(approved=False))
    assert not call(client,'/content/watch/CW-M01/preview').json['ready']
    with_material(client,material=mat(rights={}))
    assert not call(client,'/content/watch/CW-M01/preview').json['ready']
    with_material(client);assert 'SOURCE-ONLY' not in client.get('/api/v1/platform/watch').text
    publish(client,'watch','CW-M01')
    manifest=rpc(client,'curated_object',{'id':'CW-M01'})['structuredContent'];rev=manifest['materials_revision']
    assert manifest['materials'][0]['characters']==len(mat()['body']) and 'SOURCE-ONLY' not in json.dumps(manifest)
    a=rpc(client,'curated_material',{'id':'CW-M01','material_id':'readme','content_revision':rev,'limit':30})['structuredContent']
    assert a['has_more'] and a['body']==mat()['body'][:30]
    with_material(client,material=mat(body='UPDATED CONTENT',upstream_revision='commit-2'));publish(client,'watch','CW-M01')
    old=cm.read('CW-M01','readme',rev,30,50000);assert a['body']+old['body']==mat()['body']
    assert old['material']['content_hash']==hashlib.sha256(mat()['body'].encode()).hexdigest()
    current=cm.read('CW-M01','readme');assert current['body']=='UPDATED CONTENT' and current['content_revision']!=rev
    with_material(client,material=mat(coverage='withdrawn',body='',reason='Redistribution permission revoked'));publish(client,'watch','CW-M01')
    with pytest.raises(PlatformError) as exc:cm.read('CW-M01','readme',rev)
    assert exc.value.status==410
    assert cm.read('CW-M01','readme')['body']==''


def test_bundle_budget_continuation_and_missing_ranges(client,monkeypatch):
    migrate(client);with_material(client);publish(client,'watch','CW-M01')
    data=rpc(client,'curated_bundle',{'objects':[{'id':'CW-M01'}],'max_characters':50})['structuredContent']
    assert data['coverage']['included_characters']==50 and not data['coverage']['all_stored_text_included']
    m=data['objects'][0]['materials'][0];args=m['continuation']['arguments']
    assert m['body']+rpc(client,'curated_material',args)['structuredContent']['body']==mat()['body']
    assert rpc(client,'curated_bundle',{'objects':[{'id':'CW-M01'}],'format':'markdown'})['structuredContent']['markdown']
    with_material(client,material=mat(coverage='link_only',body='',reason='Only original link may be redistributed'));publish(client,'watch','CW-M01')
    assert cm.object_data('CW-M01')['materials'][0]['coverage']=='link_only'
    monkeypatch.setenv('FIELDTOFIT_READ_TOKEN','isolated-reader')
    assert client.get('/api/v1/platform/content/CW-M01/materials').status_code==401


def test_same_url_changed_body_preserves_previous_material(client,monkeypatch):
    src=next(s for s in catalog.definitions() if s['id']=='daily-deepseek-announcements')
    raw={'body':('<html><article><h1>Official changes</h1><p>'+('Version one details. '*30)+'</p></article></html>').encode()}
    from backend.knowledge import sources
    monkeypatch.setattr(sources,'fetch',lambda url:(raw['body'],url,{}))
    d.collect(src)
    with get_db() as db:old=dict(db.execute('SELECT * FROM fieldtofit_discoveries').fetchone())
    d.collect(src)
    with get_db() as db:assert db.execute('SELECT count(*) FROM fieldtofit_discovery_versions').fetchone()[0]==0
    raw['body']=raw['body'].replace(b'one',b'two');d.collect(src)
    with get_db() as db:
        history=db.execute('SELECT * FROM fieldtofit_discovery_versions').fetchone()
        current=db.execute('SELECT * FROM fieldtofit_discoveries').fetchone()
        assert history['fingerprint']==old['fingerprint'] and json.loads(history['materials'])[0]['body']==json.loads(old['materials'])[0]['body']
        assert current['id']==old['id'] and current['fingerprint']!=old['fingerprint']
    assert len([s for s in catalog.definitions() if s['id'].endswith('-announcements')])==9


def test_qwen_public_payload_and_bounded_repeat_cycle(client,monkeypatch):
    from backend.knowledge import sources
    src=next(s for s in catalog.definitions() if s['id']=='daily-qwen-announcements');src=copy.deepcopy(src);src['config']['limit']=2
    articles=[{'id':str(i),'path':'example-'+str(i),'title':'Official '+str(i),'content':'<article><h1>Title</h1><p>'+('Source facts. '*20)+'</p></article>',
        'extra':{'date':'2026-09-01T00:00:00Z','introduction':'Primary summary','git_url':'PRIVATE-METADATA'}} for i in range(3)]
    monkeypatch.setattr(sources,'fetch',lambda url,**kw:(json.dumps({'success':True,'data':{'articles':articles}}).encode(),url,{}))
    with pytest.raises(sources.PartialSourceError):d.collect(src)
    assert d.collect(src)[0]==2
    with get_db() as db:
        rows=db.execute('SELECT * FROM fieldtofit_discoveries').fetchall();assert len(rows)==3
        assert 'PRIVATE-METADATA' not in json.dumps([dict(r) for r in rows])


def test_index_rechecks_body_of_older_publication_and_finishes_queue(client,monkeypatch):
    from backend.knowledge import sources,paging
    src=copy.deepcopy(next(s for s in catalog.definitions() if s['id']=='daily-kimi-announcements'));src['config']['limit']=2
    raw={'text':'Version 1 facts. '*30}
    def fetch(url):
        html='<main>'+''.join(f'<a href="/en/blog/item-{i}">Item {i}</a>' for i in range(3))+'</main>' if url==src['url'] else '<article><h1>Release</h1><time datetime="2026-07-01"></time><p>'+raw['text']+'</p></article>'
        return html.encode(),url,{}
    monkeypatch.setattr(sources,'fetch',fetch)
    with pytest.raises(sources.PartialSourceError):d.collect(src)
    d.collect(src);assert paging.progress(src['id'])['status']=='complete'
    raw['text']='Version 2 facts. '*30
    with pytest.raises(sources.PartialSourceError):d.collect(src)
    with get_db() as db:assert db.execute('SELECT count(*) FROM fieldtofit_discovery_versions').fetchone()[0]==2



def test_intake_does_not_replace_researched_proposal_or_owner_decision(client):
    migrate(client);ident,ref=make(client);batch=b.create({})['id']
    tid=b.propose(batch,proposal(ref=ref,event_url='https://example.org/review',proposal={'title':'Researched topic','reason':'Concrete evidence','website_copy':'REVIEWED COPY'}))['id']
    b.decide(tid,{'version':topic(batch,tid)['version'],'decision':'later','review_on':b.today()})
    before=topic(batch,tid);b.intake(batch);after=topic(batch,tid)
    assert after['proposal']==before['proposal'] and after['decision']=='later' and after['version']==before['version']


def test_mixed_bundle_preserves_budget_and_rejects_same_legacy_revision(client):
    from test_platform_updates import selected
    from backend.knowledge import platform_bundle as bundle
    migrate(client);with_material(client);publish(client,'watch','CW-M01');old,_,_=selected('mixed')
    refs=[{'id':'CW-M01'},{'id':old['object']['id']}]
    package=bundle.build(refs,1)
    assert package['coverage']['included_characters']==1 and package['objects'][1]['materials'][0]['inclusion']=='deferred'
    with pytest.raises(PlatformError):bundle.build([*refs,{'id':old['object']['id'],'revision':old['revision']}])
