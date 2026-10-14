"""Local GPT handoff exercises the real HTTP review/publication boundary."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import json
import hashlib
from pathlib import Path

import pytest
from test_knowledge import client, ADMIN
from test_daily_journal import renderer
from backend.daily_briefing import service, pdf
from backend.daily_briefing.schema import TZ, digest, instant, stamp
from backend.knowledge.platform import PlatformError
from scripts.maintenance.local_daily_journal import run, write, Website, check_layout


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    now=datetime.now(TZ)
    day=now.date().isoformat()
    cutoff=now.replace(hour=8,minute=30,second=0,microsecond=0)
    # A past completed issue keeps these tests independent of the machine hour.
    if cutoff>now:
        cutoff-=timedelta(days=1);day=cutoff.date().isoformat()
    data=json.loads((Path(__file__).parent/'fixtures/daily-2026-10-13.json').read_text())
    data.pop('image',None)
    data.update(date=day,kind='daily',window_start=(cutoff-timedelta(days=1)).isoformat(),cutoff_at=cutoff.isoformat())
    # Fixture sources after the new cutoff are only synthetic test references.
    for source in data['sources']:
        source['published_at']=None;source['checked_at']=stamp(cutoff)
    for c in data['coverage']:
        c.update(state='checked',checked_at=stamp(cutoff),source_ids=[data['sources'][0]['id']])
    for story in data['stories']:story['event_date']=min(story['event_date'],day)
    for product in data['products']:
        product['release_date']=min(product['release_date'],day);product['checked_at']=stamp(cutoff)
    for market in data['markets']:
        closed=cutoff-timedelta(days=1,hours=16 if market['id']=='us' else 1)
        market.update(trade_date=closed.astimezone(__import__('zoneinfo').ZoneInfo('America/New_York') if market['id']=='us' else TZ).date().isoformat(),closed_at=closed.isoformat())
        for row in market['rows']:
            if row['state']=='verified':row['as_of']=market['closed_at']
    evidence={'date':day,'source_checks':[{'source_id':s['id'],'url':s['url'],'checked_at':s['checked_at'],'excerpt':'Synthetic source quotation for isolated integration testing only.'} for s in data['sources']]}
    review={'method':'local_gpt','approved':True,'issues':[],'content_hash':digest(data),'evidence_hash':digest(evidence),'reviewed_at':stamp(cutoff),'checks':dict.fromkeys(service.LOCAL_REVIEW_CHECKS,True)}
    for name,obj in [('issue',data),('evidence',evidence),('review',review)]:write(tmp_path/(name+'.json'),obj)
    monkeypatch.setattr(pdf,'render',lambda data,lang,image=None,revision=1:renderer(data,lang,image))
    return data,review,tmp_path,cutoff


class Site:
    def __init__(self,client):self.client=client;self.writes=[]
    def call(self,path,data=None,binary=False,missing=False):
        if data is not None:self.writes.append((path,data))
        response=self.client.post(path,json=data,headers=ADMIN) if data is not None else self.client.get(path,headers=ADMIN)
        if response.status_code==404 and missing:return None
        assert response.status_code==200,response.get_json()
        return response.data if binary else response.get_json()


def test_local_handoff_without_any_model_call(client,bundle,monkeypatch):
    data,review,directory,cutoff=bundle;site=Site(client);day=data['date']
    from backend.knowledge import models
    monkeypatch.setattr(models,'generate_json',lambda *a,**kw:pytest.fail('Local handoff must not call a model API'))
    assert run('validate',day,directory,now=cutoff)['state']=='validated'
    assert run('stage',day,directory,site,now=cutoff)['state']=='prepared'
    assert (directory/'proof-zh.pdf').read_bytes().startswith(b'%PDF-')
    assert client.get('/api/v1/admin/daily/'+day+'/pdf').status_code==401
    assert run('publish',day,directory,site,now=cutoff)['state']=='not_due'
    before=len(site.writes)
    assert run('stage',day,directory,site,now=cutoff)['state']=='prepared'
    assert len(site.writes)==before
    assert service.draft(day)['review']['method']=='local_gpt'
    # The real service enforces the same publication clock used by cloud jobs.
    with pytest.raises(PlatformError,match='Automatic publication'):
        service.publish(day,1,{'zh':'测试','en':'Test'},automatic=True,now=cutoff)
    hashes={lang:hashlib.sha256((directory/('proof-'+lang+'.pdf')).read_bytes()).hexdigest() for lang in ('zh','en')}
    service.publish(day,1,{'zh':'测试','en':'Test'},automatic=True,now=cutoff+timedelta(minutes=30),proof_hashes=hashes)
    assert run('check',day,directory,site,now=cutoff+timedelta(minutes=35))['state']=='published'
    assert (directory/'published-zh.pdf').read_bytes().startswith(b'%PDF-')
    assert run('publish',day,directory,site,now=cutoff+timedelta(minutes=40))['state']=='published'
    assert len(service.draft(day)['history'])==1


@pytest.mark.parametrize('field,value',[('content_hash','0'*64),('evidence_hash','bad'),('issues',['Unverified statement']),('reviewed_at','2099-01-01T00:00:00Z'),('checks',{})])
def test_invalid_local_review_never_renders_or_publishes(client,bundle,field,value,monkeypatch):
    data,report,_,_=bundle
    version=service.save(data)['draft_version'];report[field]=value
    monkeypatch.setattr(pdf,'render',lambda *a,**kw:pytest.fail('Invalid review must be rejected before rendering'))
    response=client.post('/api/v1/admin/daily/'+data['date']+'/review',json={'draft_version':version,'review_report':report},headers=ADMIN)
    assert response.status_code in (400,409)
    assert not service.draft(data['date'])['reviewed']


def test_changed_evidence_and_existing_drafts_cannot_be_overwritten(client,bundle):
    data,report,directory,cutoff=bundle;site=Site(client);day=data['date']
    evidence=json.loads((directory/'evidence.json').read_text());evidence['changed']=True
    write(directory/'evidence.json',evidence)
    with pytest.raises(ValueError,match='Evidence changed'):run('stage',day,directory,site,now=cutoff)
    assert not site.writes
    evidence.pop('changed');write(directory/'evidence.json',evidence)
    other=deepcopy(data);other['intro']['en']+=' Owner edit.';service.save(other)
    with pytest.raises(ValueError,match='owner inspection'):run('stage',day,directory,site,now=cutoff)
    assert not site.writes


@pytest.mark.parametrize('action',['edit','withdraw'])
def test_private_pdf_proof_expires_on_edit_or_withdrawal(client,bundle,action):
    data,report,directory,cutoff=bundle;day=data['date'];site=Site(client)
    run('stage',day,directory,site,now=cutoff)
    assert client.get('/api/v1/admin/daily/'+day+'/pdf?lang=en',headers=ADMIN).status_code==200
    if action=='edit':
        changed=deepcopy(data);changed['intro']['en']+=' New copy.'
        service.save(changed,1)
    else:
        service.withdraw(day,1,{'zh':'撤回测试','en':'Withdrawal test'})
    assert client.get('/api/v1/admin/daily/'+day+'/pdf',headers=ADMIN).status_code==409
    assert client.get('/api/v1/daily/'+day).status_code==404


def test_review_sample_and_previous_date_cannot_be_automated(client,bundle):
    data,report,directory,cutoff=bundle
    with pytest.raises(ValueError,match='current Beijing'):run('validate',data['date'],directory,now=cutoff+timedelta(days=1))
    data['kind']='review_sample';write(directory/'issue.json',data)
    with pytest.raises(ValueError,match='current Beijing'):run('validate',data['date'],directory,now=cutoff)


def test_local_gpt_can_repair_only_its_own_unpublished_draft(client,bundle):
    data,report,directory,cutoff=bundle;site=Site(client);day=data['date']
    run('stage',day,directory,site,now=cutoff)
    data['intro']['en']+=' Corrected before publication.'
    report['content_hash']=digest(data)
    write(directory/'issue.json',data);write(directory/'review.json',report)
    repaired=run('stage',day,directory,site,now=cutoff)
    assert repaired['draft_version']==2 and service.draft(day)['reviewed']
    manual=deepcopy(data);manual['intro']['zh']+=' 人工修改。'
    service.save(manual,2)
    with pytest.raises(ValueError,match='owner inspection'):run('stage',day,directory,site,now=cutoff)


def test_publish_requires_visual_review_of_the_exact_pdf_pair(client,bundle):
    import hashlib
    data,report,directory,cutoff=bundle;site=Site(client);day=data['date']
    run('stage',day,directory,site,now=cutoff)
    with pytest.raises(ValueError,match='visual review'):
        run('publish',day,directory,site,now=cutoff+timedelta(minutes=30))
    layout={'approved':True,'content_hash':digest(data),'proofs':{lang:{'sha256':hashlib.sha256((directory/('proof-'+lang+'.pdf')).read_bytes()).hexdigest(),'checked_pages':[1,2,3,4,5]} for lang in ('zh','en')}}
    write(directory/'layout-review.json',layout)
    check_layout(directory,data,{'zh':5,'en':5})
    (directory/'proof-en.pdf').write_bytes(b'%PDF- changed')
    with pytest.raises(ValueError,match='Every page'):check_layout(directory,data,{'zh':5,'en':5})


def test_automatic_flag_is_strict_and_old_owner_review_still_works(client,bundle):
    data,_,_,_=bundle;day=data['date'];service.save(data)
    assert client.post('/api/v1/admin/daily/'+day+'/review',json={'draft_version':1,'facts_and_languages_checked':True},headers=ADMIN).status_code==200
    assert client.post('/api/v1/admin/daily/'+day+'/publish',json={'draft_version':1,'automatic':'false','reason':{'zh':'测试','en':'Test'}},headers=ADMIN).status_code==400


def test_remote_pdf_replacement_is_rejected_at_atomic_publication(client,bundle,monkeypatch):
    from backend.db import get_db
    data,_,directory,cutoff=bundle;site=Site(client);day=data['date']
    run('stage',day,directory,site,now=cutoff)
    hashes={lang:hashlib.sha256((directory/('proof-'+lang+'.pdf')).read_bytes()).hexdigest() for lang in ('zh','en')}
    write(directory/'layout-review.json',{'approved':True,'content_hash':digest(data),'proofs':{lang:{'sha256':hashes[lang],'checked_pages':[1,2,3,4,5]} for lang in ('zh','en')}})
    publish=service.publish
    monkeypatch.setattr(service,'publish',lambda *args,**kwargs:publish(*args,now=cutoff+timedelta(minutes=30),**kwargs))
    with get_db() as db:
        db.execute("UPDATE fieldtofit_daily_prepared SET sha256=? WHERE day=? AND lang='en'",('0'*64,day))
    # The local proofs still pass, but the server must reject a concurrently changed PDF.
    check_layout(directory,data,{'zh':5,'en':5})
    with pytest.raises(AssertionError,match='PDF proofs changed'):
        run('publish',day,directory,site,now=cutoff+timedelta(minutes=30))
    assert not service.draft(day)['history']
    with get_db() as db:
        db.execute("UPDATE fieldtofit_daily_prepared SET sha256=? WHERE day=? AND lang='en'",(hashes['en'],day))
    assert run('publish',day,directory,site,now=cutoff+timedelta(minutes=30))['state']=='published'
    assert site.writes[-1][1]['proof_hashes']==hashes


def test_credentials_only_go_to_fixed_admin_origin(tmp_path,monkeypatch):
    env=tmp_path/'settings';env.write_text('ADMIN_PASSWORD=local-test-only\n')
    site=Website(env);seen=[]
    class Response:
        status_code=200
        def json(self):return {}
    def request(method,url,**kwargs):seen.append((url,kwargs));return Response()
    monkeypatch.setattr(site.session,'request',request)
    site.call('/api/v1/admin/daily');site.call('/api/v1/daily/latest')
    assert seen[0][0]=='https://fieldtofit.top/api/v1/admin/daily'
    assert seen[0][1]['headers']=={'X-Admin-Password':'local-test-only'}
    assert seen[1][1]['headers']=={} and not seen[0][1]['allow_redirects']
    with pytest.raises(ValueError):site.call('https://elsewhere.example')
