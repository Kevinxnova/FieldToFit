"""Quality-edition regressions. All content and quotes are synthetic."""
from copy import deepcopy
from datetime import timedelta, datetime, timezone
from io import BytesIO
import re
import hashlib
import pytest
from bs4 import BeautifulSoup
from pypdf import PdfReader
from test_knowledge import client, ADMIN
from test_daily_journal import issue, renderer, publish
from test_local_daily_journal import bundle, Site
from daily_editorial_helpers import evidence_fields
from backend.daily_briefing import service, pipeline
from backend.daily_briefing.schema import validate, digest, instant, SECTIONS, SECURITIES, CURRENCIES, EDITION_ORDER
from backend.daily_briefing.watchlist import securities, TICKER_GROUP
from backend.daily_briefing.editorial import validate_editorial
from backend.daily_briefing.pdf import render
from backend.knowledge.platform import PlatformError
from scripts.maintenance.local_daily_journal import run, write


def quality(data):
    data['layout_version']=3
    data['market_overview']={k:{'zh':'隔离测试行情，不是真实价格。','en':'Synthetic market fixture, not actual quotes.'} for k in ('title','summary','note')}
    for section in SECTIONS:
        if not any(s['section']==section for s in data['stories']):
            story=deepcopy(data['stories'][0]);story.update(id='test-'+section,event_key='test-'+section,section=section,highlight=False)
            data['stories'].append(story)
    for s in data['stories']:
        s.update(freshness='new',date_label={'zh':'本期测试','en':'Current test'})
        if s['highlight']:s.update(highlight_title=s['title'],highlight_summary={'zh':'隔离测试重点摘要。','en':'Synthetic highlight summary.'})
    for p in data['products']:p['release_channel']='stable'
    old={m['id']:m for m in data['markets']}
    for key,rows in securities(SECURITIES,3).items():
        m=deepcopy(old.get(key,old['cn']));m.update(id=key,currency=CURRENCIES[key],state='closed',rows=[])
        for ticker,zh,en in rows:
            m['rows'].append(dict(ticker=ticker,name={'zh':zh,'en':en},price=100,change_pct=1,state='verified',source_ids=[data['sources'][0]['id']],as_of=m['closed_at'],delay_minutes=None,group=TICKER_GROUP[ticker]))
        old[key]=m
    data['markets']=list(old.values())
    return data


def evidence(data):
    e={'date':data['date'],'source_checks':[dict(source_id=s['id'],url=s['url'],checked_at=s['checked_at'],excerpt='Synthetic dated source excerpt for isolated testing only.') for s in data['sources']],**evidence_fields(data)}
    e['quality_review']={
        'sections':[dict(section=k,story_ids=[s['id'] for s in data['stories'] if s['section']==k],selection_reason='Synthetic section value: explains a material decision and the limits of the actual evidence.') for k in SECTIONS],
        'stories':[dict(story_id=s['id'],reader_value='Synthetic reader value: distinguishes the announcement from verified operations and practical limits.',previously_covered=False,new_information='') for s in data['stories']],
        'previous_editions':[], 'count_reason':'Synthetic story count follows substantive scope, not a minimum quota.', 'market_assessment':'Synthetic market observations separate price facts from unverified causal explanations.'}
    return e


@pytest.fixture
def quality_bundle(bundle):
    d,r,path,cutoff=bundle;quality(d);e=evidence(d)
    r.update(content_hash=digest(d),evidence_hash=digest(e),checks=dict.fromkeys(service.QUALITY_REVIEW_CHECKS,True))
    for n,v in [('issue',d),('evidence',e),('review',r)]:write(path/(n+'.json'),v)
    return d,e,r,path,cutoff


@pytest.mark.parametrize('mutate',[
 lambda d:d['markets'][-1].update(currency='USD'),
 lambda d:d['markets'][-1]['rows'].pop(),
 lambda d:d['markets'][0]['rows'][0].update(group='storage'),
 lambda d:d['markets'][0]['rows'][0].update(state='partial'),
 lambda d:d['stories'][0].update(event_date='2026-01-01'),
 lambda d:d['products'][0].update(release_channel='unknown'),
])
def test_invalid_quality_snapshot(quality_bundle,mutate):
    d,*_=quality_bundle;mutate(d)
    with pytest.raises(PlatformError):validate(d)


def test_partial_close_keeps_price_without_inventing_change(quality_bundle):
    d,*_=quality_bundle;row=d['markets'][2]['rows'][2];row.update(state='partial',change_pct=None)
    assert validate(d)['markets'][2]['rows'][2]['price']==100
    row['price']=None
    with pytest.raises(PlatformError):validate(d)


@pytest.mark.parametrize('change,match',[
 (lambda d,e:e.pop('quality_review'),'complete quality'),
 (lambda d,e:e['quality_review']['sections'][0].update(story_ids=[]),'does not match'),
 (lambda d,e:e['quality_review']['stories'][0].update(previously_covered=True,new_information='same'),'substantive new'),
 (lambda d,e:e['product_checks'][0].update(release_status='beta'),'channel differs'),
 (lambda d,e:e.update(research_checks=[r for r in e['research_checks'] if r['section']!='chips']),'chips'),
])
def test_quality_evidence_is_enforced(quality_bundle,change,match):
    d,e,_,_,cutoff=quality_bundle;change(d,e)
    with pytest.raises(ValueError,match=match):validate_editorial(d,e,cutoff)


def test_date_only_recent_and_exact_timestamp_boundary(quality_bundle):
    d,e,_,_,cutoff=quality_bundle;s=d['stories'][0];s.update(freshness='recent',event_date=(cutoff-timedelta(days=3)).date().isoformat())
    e['event_checks'][0]['event_time']=(cutoff-timedelta(days=3)).isoformat()
    validate(d);validate_editorial(d,e,cutoff)
    e['event_checks'][0]['event_time']=(cutoff-timedelta(days=3,seconds=1)).isoformat()
    with pytest.raises(ValueError,match='too old'):validate_editorial(d,e,cutoff)


def test_empty_section_and_repeated_event_cannot_be_signed(quality_bundle):
    d,e,_,_,cutoff=quality_bundle
    prior=(cutoff-timedelta(days=1)).date().isoformat()
    e['quality_review']['previous_editions']=[dict(date=prior,content_hash='a'*64,event_keys=[d['stories'][0]['event_key']])]
    with pytest.raises(ValueError,match='marked unseen'):validate_editorial(d,e,cutoff)
    e['quality_review']['previous_editions']=[]
    d['stories']=[s for s in d['stories'] if s['section']!='chips'];e['event_checks']=[c for c in e['event_checks'] if c['story_id'] in {s['id'] for s in d['stories']}]
    with pytest.raises(ValueError,match='substantive reporting'):validate_editorial(d,e,cutoff)


def test_real_quality_http_review_and_auto_publication(client,quality_bundle,monkeypatch):
    d,e,r,path,cutoff=quality_bundle
    config=pipeline.configuration
    monkeypatch.setattr(pipeline,'configuration',lambda:dict(config(),supported_layout_versions=[1,2,3]))
    site=Site(client)
    assert run('stage',d['date'],path,site,now=cutoff)['state']=='prepared'
    version=service.draft(d['date'])['draft_version']
    assert service.draft(d['date'])['review']['checks']['editorial_value']
    bad=deepcopy(e);bad['quality_review']['sections']=[]
    response=client.post('/api/v1/admin/daily/'+d['date']+'/review',json={'draft_version':version,'review_report':r,'evidence':bad},headers=ADMIN)
    assert response.status_code==409
    service.publish(d['date'],version,{'zh':'测试','en':'Test'},automatic=True,now=cutoff+timedelta(minutes=30),proof_hashes={l:hashlib.sha256((path/('proof-'+l+'.pdf')).read_bytes()).hexdigest() for l in ('zh','en')})
    for lang in ('zh','en'):
        live=service.read(d['date'],lang);assert sum(len(m['rows']) for m in live['markets'])==30
        page=client.get(('/en' if lang=='en' else '')+'/for-you/daily/'+d['date'])
        soup=BeautifulSoup(page.text,'html.parser')
        assert len(soup.select('tbody tr'))==30 and len(soup.select('#daily-markets'))==1
        assert 'KRW' in soup.get_text() and 'market_assessment' not in page.text


def test_missing_market_rejected_at_server_review(client,quality_bundle):
    d,e,r,_,_=quality_bundle
    for row in d['markets'][-1]['rows']:row.update(state='missing',price=None,change_pct=None,as_of=None)
    r['content_hash']=digest(d);v=service.save(d)['draft_version']
    with pytest.raises(PlatformError,match='complete market'):service.approve(d['date'],v,r,renderer,e)


def test_quality_pdf_preserves_all_copy_sources_and_currency(quality_bundle):
    d,*_=quality_bundle
    for lang in ('zh','en'):
        result=render(d,lang,revision=2);reader=PdfReader(BytesIO(result['bytes']))
        body=re.sub(r'\s+','',''.join(p.extract_text() for p in reader.pages))
        assert 'KRW' in body and '000660' in body and '688825' in body
        assert all(re.sub(r'\s+','',s['summary'][lang]) in body for s in d['stories'])
        urls={a.get_object()['/A']['/URI'] for p in reader.pages for a in p.get('/Annots',[]) if '/A' in a.get_object() and '/URI' in a.get_object()['/A']}
        used={i for s in d['stories'] for i in s['source_ids']}|{i for p in d['products'] for i in p['source_ids']}|{i for m in d['markets'] for r in m['rows'] for i in r['source_ids']}
        assert {s['url'] for s in d['sources'] if s['id'] in used}<=urls
        assert digest(service._public_copy(d)) in reader.metadata.subject
