"""Daily publication, calendar, bilingual/PDF and recovery boundaries in SQLite."""
from copy import deepcopy
from datetime import datetime,timezone,timedelta
from pathlib import Path
import hashlib,json
import pytest
from test_knowledge import client,ADMIN
from backend.daily_briefing import service,pipeline
from backend.daily_briefing.schema import validate,public_url,instant,TZ
from backend.knowledge.platform import PlatformError
from backend.knowledge.mcp import invoke

FIXTURE=Path(__file__).parent/'fixtures/daily-2026-10-13.json'
REASON={'zh':'完成样刊核验。','en':'Sample verification completed.'}
@pytest.fixture
def issue():
    d=json.loads(FIXTURE.read_text());d.pop('image',None);return d

def renderer(data,lang,image=None):
    b=('%PDF-1.4\n'+lang+data['headline'][lang]).encode()
    return {'bytes':b,'sha256':hashlib.sha256(b).hexdigest(),'pages':5}

def ready(issue):
    v=service.save(issue)['draft_version'];service.approve(issue['date'],v,{'approved':True,'method':'owner'},renderer=renderer);return v

def publish(issue):
    v=ready(issue);return service.publish(issue['date'],v,REASON)

def test_publication_freezes_both_languages_and_pdf_revision(client,issue):
    assert client.get('/api/v1/daily/latest').status_code==404
    v=ready(issue)
    assert client.get('/api/v1/daily/'+issue['date']).status_code==404
    p=service.publish(issue['date'],v,REASON)
    assert service.publish(issue['date'],v,REASON)['unchanged']
    zh=client.get('/api/v1/daily/latest').json;en=client.get('/api/v1/daily/latest?lang=en').json
    assert zh['publication']['content_hash']==en['publication']['content_hash']==p['content_hash']
    assert en==invoke('curated_daily',{'day':'latest','lang':'en'})
    assert zh['headline']!=en['headline'] and 'coverage' not in zh
    data,sha,revision=service.pdf_bytes(issue['date'],'zh');assert hashlib.sha256(data).hexdigest()==sha and revision==1
    issue['headline']['zh']='尚未发布的新标题';service.save(issue,v)
    assert service.read()['headline']==zh['headline']
    with pytest.raises(PlatformError):service.publish(issue['date'],v+1,REASON)
    assert client.get('/api/v1/daily/'+issue['date']+'/pdf?lang=en&revision=1').status_code==200

def test_stale_review_correction_and_withdrawal_override_history(client,issue):
    publish(issue);issue['intro']['en']+=' Corrected.';v=service.save(issue,1)['draft_version']
    with pytest.raises(PlatformError):service.approve(issue['date'],1,{'approved':True,'method':'owner'},renderer)
    service.approve(issue['date'],v,{'approved':True,'method':'owner'},renderer)
    service.publish(issue['date'],v,{'zh':'更正英文介绍。','en':'Corrected the English introduction.'})
    assert service.read(revision=1)['publication']['current_revision']==2
    service.withdraw(issue['date'],v,{'zh':'核对原文期间撤回。','en':'Withdrawn while sources are checked.'})
    assert service.archive()['total']==0
    for url in [f'/api/v1/daily/{issue["date"]}',f'/api/v1/daily/{issue["date"]}?revision=1',f'/api/v1/daily/{issue["date"]}/pdf?revision=1']:
        assert client.get(url).status_code==404
    with pytest.raises(PlatformError):service.publish(issue['date'],v,REASON)

def test_pdf_failure_does_not_approve_or_publish(client,issue):
    v=service.save(issue)['draft_version']
    def broken(d,l,image=None):
        if l=='en':raise RuntimeError('font failure')
        return renderer(d,l)
    with pytest.raises(RuntimeError):service.approve(issue['date'],v,{'approved':True,'method':'owner'},broken)
    assert not service.draft(issue['date'])['reviewed']
    with pytest.raises(PlatformError):service.publish(issue['date'],v,REASON)
    assert service.archive()['total']==0

@pytest.mark.parametrize('mutation',[
 lambda d:d['headline'].pop('en'),
 lambda d:d['intro'].__setitem__('en','中文不是英文'),
 lambda d:d['stories'][0].__setitem__('source_ids',['invented']),
 lambda d:d['stories'][1].__setitem__('event_key',d['stories'][0]['event_key']),
 lambda d:d['sources'][0].__setitem__('published_at','2026-10-14T00:00:00+08:00'),
 lambda d:d['markets'][0]['rows'][0].__setitem__('price',float('nan')),
 lambda d:d['markets'][2]['rows'][3].__setitem__('price',1.50),
 lambda d:d['markets'][0].__setitem__('currency','CNY'),
 lambda d:d['markets'][0].__setitem__('closed_at','2026-10-13T16:00:00-04:00'),
 lambda d:d.__setitem__('kind','daily'),
 lambda d:d.__setitem__('private_password','not allowed'),
])
def test_invalid_facts_fail_closed(issue,mutation):
    mutation(issue)
    with pytest.raises((PlatformError,ValueError)):validate(issue)

@pytest.mark.parametrize('url',['http://example.org','https://127.0.0.1/','https://[::1]/','https://169.254.169.254','https://user:pass@example.org/','https://localhost/'])
def test_public_sources_reject_private_urls(url):
    with pytest.raises(PlatformError):public_url(url)

def test_auth_csrf_and_strict_inputs(client,issue,monkeypatch):
    assert client.post('/api/v1/admin/daily',json={'issue':issue}).status_code==401
    assert client.post('/api/v1/admin/daily',json={'issue':issue},headers={**ADMIN,'Origin':'https://evil.example'}).status_code==403
    assert client.post('/api/v1/admin/daily',json={'issue':issue},headers=ADMIN).status_code==200
    assert client.get('/api/v1/daily?lang=fr').status_code==400
    assert client.get('/api/v1/daily?limit=-1').status_code==400
    monkeypatch.setenv('FIELDTOFIT_READ_TOKEN','private-read-token')
    assert client.get('/api/v1/daily').status_code==401

def test_noon_idempotence_leases_and_errors_preserve_previous(client,issue,monkeypatch):
    publish(issue);now=instant('2026-10-14T12:00:00+08:00')
    assert service.archive(now=now)['status']=='delayed'
    monkeypatch.setenv('FIELDTOFIT_DAILY_AUTOPUBLISH','1');monkeypatch.setenv('FIELDTOFIT_DAILY_SCHEDULE_VERIFIED','1')
    assert pipeline.run('publish',now=now)['state']=='failed'
    assert service.read()['date']=='2026-10-13'
    token=pipeline.claim('2026-10-14','prepare',now)
    with pytest.raises(PlatformError):pipeline.claim('2026-10-14','prepare',now)
    replacement=pipeline.claim('2026-10-14','prepare',now+timedelta(minutes=11));assert replacement!=token
    with pytest.raises(PlatformError):pipeline.finish('2026-10-14','prepare',token,'completed',{})
    pipeline.finish('2026-10-14','prepare',replacement,'completed',{})
    assert pipeline.claim('2026-10-14','prepare',now+timedelta(minutes=12)) is None

def test_daily_complete_close_before_noon_and_weekend(client,issue):
    # Friday closes are legal in a Sunday issue; calendar adapter is responsible
    # for proving that these are the most recent complete exchange sessions.
    issue['kind']='daily';issue['date']='2026-10-18';issue['window_start']='2026-10-17T11:30:00+08:00';issue['cutoff_at']='2026-10-18T11:30:00+08:00'
    for c in issue['coverage']:c['state']='checked';c['source_ids']=['s1']
    for m in issue['markets']:
        m['trade_date']='2026-10-16';m['closed_at']='2026-10-16T16:00:00-04:00' if m['id']=='us' else '2026-10-16T16:00:00+08:00';m['state']='holiday'
        for r in m['rows']:
            if r['state']=='verified':r['as_of']=m['closed_at']
    assert validate(issue,now=instant('2026-10-18T12:00:00+08:00'))
    issue['markets'][0]['closed_at']='2026-10-19T16:00:00-04:00'
    with pytest.raises(PlatformError):validate(issue,now=instant('2026-10-18T12:00:00+08:00'))

def test_empty_issue_and_coverage_failure(client,issue):
    issue['stories']=[];issue['products']=[]
    publish(issue);assert service.read()['stories']==[]
    issue['coverage'][0]['state']='failed';v=service.save(issue,1)['draft_version']
    with pytest.raises(PlatformError):service.approve(issue['date'],v,{'approved':True,'method':'owner'},renderer)

def test_source_change_during_pdf_build_invalidates_review(client,issue):
    v=service.save(issue)['draft_version'];changed=deepcopy(issue);changed['sources'][0]['url']='https://example.org/changed'
    def concurrent(data,lang,image=None):
        if lang=='en':service.save(changed,v)
        return renderer(data,lang)
    with pytest.raises(PlatformError):service.approve(issue['date'],v,{'approved':True,'method':'owner'},concurrent)
    assert not service.draft(issue['date'])['reviewed']

def test_search_html_and_sitemap_match_public_permissions(client,issue):
    publish(issue)
    response=client.get('/for-you/daily/2026-10-13');assert response.status_code==200 and issue['headline']['zh'].replace('\n','\n') in response.text
    assert client.get('/en/for-you/daily/2026-10-13').status_code==200
    assert '/for-you/daily/2026-10-13' in client.get('/sitemap.xml').text
    service.withdraw(issue['date'],1,REASON)
    assert client.get('/for-you/daily/2026-10-13').status_code==404
    assert '/for-you/daily/2026-10-13' not in client.get('/sitemap.xml').text

def test_automatic_publish_at_noon_then_readback_is_idempotent(client,issue,monkeypatch):
    issue['kind']='daily';issue['window_start']='2026-10-12T11:30:00+08:00';issue['cutoff_at']='2026-10-13T11:30:00+08:00'
    for c in issue['coverage']:c['state']='checked';c['source_ids']=['s1']
    for m in issue['markets'][1:]:
        m['trade_date']='2026-10-12';m['closed_at']='2026-10-12T16:00:00+08:00'
        for r in m['rows']:
            if r['state']=='verified':r['as_of']=m['closed_at']
    for entry in issue['sources']+issue['products']+issue['coverage']:entry['checked_at']='2026-10-13T11:30:00+08:00'
    ready(issue)
    monkeypatch.setenv('FIELDTOFIT_DAILY_AUTOPUBLISH','1');monkeypatch.setenv('FIELDTOFIT_DAILY_SCHEDULE_VERIFIED','1')
    assert pipeline.run('tick',now=instant('2026-10-13T11:55:00+08:00'))['state']=='not_due'
    r=pipeline.run('tick',now=instant('2026-10-13T12:00:00+08:00'));assert r['state']=='completed' and r['revision']==1
    assert pipeline.run('publish',now=instant('2026-10-13T12:01:00+08:00'))['state']=='already_completed'
    assert pipeline.run('tick',now=instant('2026-10-13T12:05:00+08:00'))['content_hash']==r['content_hash']
    assert service.read()['publication']['published_at']=='2026-10-13T04:00:00Z'

def test_registry_does_not_expand_morning_schedule(client):
    from backend.daily_briefing.sources import seed,CHANNELS
    from backend.db import get_db
    seed();seed()
    with get_db() as db:rows=db.execute("SELECT * FROM knowledge_sources WHERE id LIKE 'journal-%'").fetchall()
    assert len(rows)==len(CHANNELS)
    assert all(json.loads(r['config'])['daily_enabled'] is False for r in rows)
    assert not pipeline.configuration()['missing_source_dimensions']

def test_independent_review_failure_never_saves_draft(client,issue,monkeypatch):
    issue['kind']='daily';issue['window_start']='2026-10-12T11:30:00+08:00';issue['cutoff_at']='2026-10-13T11:30:00+08:00'
    for c in issue['coverage']:c['state']='checked';c['source_ids']=['s1']
    for m in issue['markets'][1:]:
        m['trade_date']='2026-10-12';m['closed_at']='2026-10-12T16:00:00+08:00'
        for r in m['rows']:
            if r['state']=='verified':r['as_of']=m['closed_at']
    packet={k:issue[k] for k in ('date','window_start','cutoff_at','coverage','markets','sources')};packet['previous_events']=[]
    monkeypatch.setattr(pipeline,'collect',lambda day:packet)
    generated=iter([(issue,{}),({'approved':False,'issues':['Unsupported claim']},{})]);monkeypatch.setattr(pipeline,'generate_json',lambda *a,**kw:next(generated))
    with pytest.raises(PlatformError):pipeline.prepare(issue['date'])
    with pytest.raises(PlatformError):service.draft(issue['date'])


def test_automatic_draft_pdf_retry_does_not_rewrite_content(client,issue,monkeypatch):
    from backend.db import get_db
    from backend.daily_briefing.schema import digest
    v=service.save(issue)['draft_version']
    packet={'generated_issue_hash':digest(issue),'review_evidence_hash':'reviewed-original-evidence'}
    with get_db() as db:db.execute('INSERT INTO fieldtofit_daily_evidence VALUES(?,?,?)',(issue['date'],json.dumps(packet),'2026-10-13T13:55:00Z'))
    original=service.approve
    monkeypatch.setattr(service,'approve',lambda day,version,report:original(day,version,report,renderer))
    assert pipeline.prepare(issue['date'])['draft_version']==v
    assert service.draft(issue['date'])['reviewed']
    issue['headline']['zh']='人工修改';service.save(issue,v)
    with pytest.raises(PlatformError):pipeline.prepare(issue['date'])

def test_portable_pdf_preserves_all_text_quotes_and_original_links(issue):
    from backend.daily_briefing.pdf import render
    from backend.daily_briefing.schema import digest
    from pypdf import PdfReader
    from io import BytesIO
    import re
    compact=lambda v:re.sub(r'\s+','',v)
    for lang in ('zh','en'):
        result=render(issue,lang,revision=3);reader=PdfReader(BytesIO(result['bytes']));body=compact(''.join(p.extract_text() for p in reader.pages))
        for story in issue['stories']:
            for field in ('title','summary','analysis'):assert compact(story[field][lang]) in body
        for product in issue['products']:assert compact(product['changes'][lang]) in body
        for market in issue['markets']:
            for quote in market['rows']:assert quote['ticker'] in body
        links={a.get_object()['/A']['/URI'] for p in reader.pages for a in p.get('/Annots',[]) if '/A' in a.get_object() and '/URI' in a.get_object()['/A']}
        assert {s['url'] for s in issue['sources']}<=links
        assert 'Revision 3' in reader.metadata.subject and digest(service._public_copy(issue)) in reader.metadata.subject
        assert result['sha256']==hashlib.sha256(result['bytes']).hexdigest()
