"""Nine-section reading and evidence failures, with legacy publication protection."""
from copy import deepcopy
from datetime import timedelta
from io import BytesIO
import json
import re
from pathlib import Path
import pytest
from bs4 import BeautifulSoup
from pypdf import PdfReader
from test_knowledge import client
from test_daily_journal import issue, renderer, publish
from test_local_daily_journal import bundle, Site
from daily_editorial_helpers import modernize, evidence_fields
from backend.daily_briefing import service
from backend.daily_briefing.schema import EDITION_ORDER, LABELS, validate, digest, instant, project
from backend.daily_briefing.editorial import validate_editorial, research_plan
from backend.daily_briefing.pdf import render
from backend.knowledge.mcp import invoke
from backend.knowledge.platform import PlatformError
from scripts.maintenance.local_daily_journal import run, write


def test_new_sections_share_content_but_do_not_rewrite_old_issue(client,issue):
    publish(issue);old=service.read(issue['date']);old_pdf=service.pdf_bytes(issue['date'],'zh')[0]
    newer=modernize(deepcopy(issue));newer['date']='2026-10-14';newer['window_start']='2026-10-13T08:30:00+08:00';newer['cutoff_at']='2026-10-14T08:30:00+08:00'
    newer['stories'][-1]['section']='business'
    publish(newer)
    for lang in ('zh','en'):
        live=service.read(newer['date'],lang)
        assert live['section_order']==list(EDITION_ORDER)
        assert live==invoke('curated_daily',{'day':newer['date'],'lang':lang})
        response=client.get(('/en' if lang=='en' else '')+'/for-you/daily/'+newer['date'])
        assert response.status_code==200
        soup=BeautifulSoup(response.text,'html.parser')
        assert [n['href'].removeprefix('#daily-') for n in soup.select('nav[aria-label] a[href^="#daily-"]')]==list(EDITION_ORDER)
        ids=[node['id'] for node in soup.select('[id^="daily-"]') if node['id'] in {'daily-'+key for key in EDITION_ORDER}]
        assert ids==['daily-'+key for key in EDITION_ORDER]
        assert soup.select_one('#daily-products') and not soup.select_one('#daily-companies #daily-products')
        assert newer['products'][0]['version'][lang] in soup.select_one('#daily-products').get_text()
        assert len(soup.select('#daily-business article'))==1
    previous=service.read(issue['date'])
    assert previous['publication']==old['publication'] and 'layout_version' not in previous and 'section_order' not in previous
    assert service.pdf_bytes(issue['date'],'zh')[0]==old_pdf
    assert digest(service._public_copy(issue))==old['publication']['content_hash']


@pytest.mark.parametrize('change',[
 lambda d:d.__setitem__('layout_version',True),
 lambda d:d.__setitem__('layout_version',3),
 lambda d:d['section_notes'].pop('business'),
 lambda d:d['stories'][0].__setitem__('section','products'),
])
def test_invalid_new_layout_is_rejected(issue,change):
    modernize(issue);change(issue)
    with pytest.raises(PlatformError):validate(issue)


def test_legacy_layout_cannot_hide_a_business_story(issue):
    issue['stories'][0]['section']='business'
    with pytest.raises(PlatformError):validate(issue)


def test_nine_section_pdf_order_links_and_long_versions(issue,tmp_path):
    modernize(issue)
    issue['stories'][-1]['section']='business'
    for lang in ('zh','en'):
        issue['products'][0]['version'][lang]='0.66.0-nightly.20261017.ged96faedf-long-version'
        rendered=render(issue,lang); reader=PdfReader(BytesIO(rendered['bytes']))
        # Cover index is excluded: inspect actual content order after the cover.
        body=re.sub(r'\s+','',''.join(p.extract_text() for p in reader.pages[1:]))
        titles=[LABELS[k][lang=='en'] for k in EDITION_ORDER[1:]]
        positions=[body.index(re.sub(r'\s+','',t)) for t in titles]
        assert positions==sorted(positions)
        assert all(re.sub(r'\s+','',s['summary'][lang]) in body for s in issue['stories'])
        assert all(r['ticker'] in body for m in issue['markets'] for r in m['rows'])
        assert digest(service._public_copy(issue)) in reader.metadata.subject
        links=[a.get_object() for p in reader.pages for a in p.get('/Annots',[])]
        assert len([a for a in links if '/Dest' in a])==9
        urls={a['/A']['/URI'] for a in links if '/A' in a and '/URI' in a['/A']}
        assert {s['url'] for s in issue['sources']}<=urls


@pytest.mark.parametrize('mutate,expected',[
 (lambda e:e.pop('research_checks'),'research_checks'),
 (lambda e:e.update(research_checks=[c for c in e['research_checks'] if c['topic']!='physical_robots']),'unchecked topic'),
 (lambda e:e.update(research_checks=[c for c in e['research_checks'] if c['region']!='cn']),'Chinese and international'),
 (lambda e:e.update(research_checks=[c for c in e['research_checks'] if c['method']!='media']),'official, search and media'),
 (lambda e:[c.update(status='failed') for c in e['research_checks'] if c['section']=='infrastructure'],'unchecked topic'),
 (lambda e:[c.update(source_ids=['s1']) for c in e['research_checks']],'one source domain'),
 (lambda e:e['event_checks'][0].update(event_time='2025-09-01'),'outside'),
 (lambda e:e['event_checks'][0].update(event_status='breakthrough'),'stage'),
 (lambda e:e['event_checks'][0].update(source_ids=['s3']),'omits'),
 (lambda e:e['product_checks'][0].update(release_status='unknown'),'release channel'),
 (lambda e:e['product_checks'][0].update(release_time='2025-01-01'),'outside'),
 (lambda e:e['event_checks'].append(e['event_checks'][0]),'one dated status'),
])
def test_incomplete_evidence_blocks_before_network_write(client,bundle,mutate,expected):
    data,report,directory,cutoff=bundle
    evidence=json.loads((directory/'evidence.json').read_text());mutate(evidence)
    report['evidence_hash']=digest(evidence)
    write(directory/'evidence.json',evidence);write(directory/'review.json',report)
    site=Site(client)
    with pytest.raises(ValueError,match=expected):run('stage',data['date'],directory,site,now=cutoff)
    assert site.writes==[]


def test_media_business_claim_needs_independent_original_publishers(bundle):
    data,report,directory,cutoff=bundle;data['stories'][0]['section']='business'
    evidence=json.loads((directory/'evidence.json').read_text());check=evidence['event_checks'][0]
    check['attribution']='media'
    with pytest.raises(ValueError,match='two independent'):validate_editorial(data,evidence,cutoff)
    check['source_ids']=list(set(check['source_ids']+['s3']))
    check['independent_publishers']=[{'publisher':'One wire','source_id':'s1'},{'publisher':'one WIRE','source_id':'s3'}]
    with pytest.raises(ValueError,match='two independent'):validate_editorial(data,evidence,cutoff)
    check['independent_publishers'][1]['publisher']='Another original publisher'
    validate_editorial(data,evidence,cutoff)


def test_new_review_requires_research_and_event_status_checks(client,bundle):
    data,report,_,_=bundle;version=service.save(data)['draft_version'];report['checks'].pop('event_status')
    with pytest.raises(PlatformError,match='every editorial check'):service.approve(data['date'],version,report,renderer)


def test_legacy_bundle_is_readable_but_cannot_create_new_local_edition(client,bundle):
    data,report,directory,cutoff=bundle
    data.pop('layout_version');data['section_notes'].pop('business')
    report['content_hash']=digest(data);report['checks']=dict.fromkeys(service.LOCAL_REVIEW_CHECKS,True)
    write(directory/'issue.json',data);write(directory/'review.json',report)
    site=Site(client)
    with pytest.raises(ValueError,match='nine-section'):run('stage',data['date'],directory,site,now=cutoff)
    assert site.writes==[]
    version=service.save(data)['draft_version'];service.approve(data['date'],version,report,renderer)
    service.publish(data['date'],version,{'zh':'测试','en':'Test'})
    assert run('check',data['date'],directory,site,now=cutoff)['state']=='published'


def test_plan_needs_no_credentials_or_network(tmp_path):
    plan=run('plan','2026-10-18',tmp_path)
    assert plan['layout_version']==2 and len(plan['sections'])==3
    assert all(set(s['queries'])=={'cn','global'} for s in plan['sections'].values())
    for section in plan['sections'].values():
        for queries in section['queries'].values():
            assert [q['topic'] for q in queries]==list(section['topics'])
            assert all('before:2026-10-19' in q['query'] for q in queries)
    assert not list(tmp_path.iterdir())


def test_new_daily_window_cannot_be_widened_to_fit_old_events(bundle):
    data,_,_,cutoff=bundle
    data['window_start']=(cutoff-timedelta(days=2)).isoformat()
    with pytest.raises(PlatformError,match='exactly 24 hours'):validate(data,now=cutoff)


def test_new_bundle_never_writes_to_an_old_production_server(client,bundle):
    data,_,directory,cutoff=bundle
    class OldSite(Site):
        def call(self,path,data=None,**kwargs):
            result=super().call(path,data,**kwargs)
            if path=='/api/v1/admin/daily':result['configuration'].pop('supported_layout_versions',None)
            return result
    site=OldSite(client)
    with pytest.raises(ValueError,match='Deploy nine-section'):run('stage',data['date'],directory,site,now=cutoff)
    assert site.writes==[]


def test_long_empty_pdf_sections_still_render_and_keep_sources(issue):
    modernize(issue);issue['stories']=[];issue['products']=[]
    for lang in ('zh','en'):
        pdf=render(issue,lang)
        reader=PdfReader(BytesIO(pdf['bytes']))
        text=''.join(p.extract_text() for p in reader.pages)
        assert LABELS['business'][lang=='en'] in text
        assert ('本期无产品版本更新' if lang=='zh' else 'No product version updates') in text
