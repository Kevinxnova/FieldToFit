"""Layout 4 contracts; fixtures are synthetic and never publishable research."""
from copy import deepcopy
from io import BytesIO
import re

import pytest
from bs4 import BeautifulSoup
from pypdf import PdfReader
from test_knowledge import client
from test_daily_journal import issue, renderer, publish
from test_local_daily_journal import bundle, Site
from test_daily_quality import quality, evidence, quality_bundle
from test_daily_preview import frozen_publication, fixed_clock
from backend.daily_briefing import service, pipeline
from backend.daily_briefing.schema import validate, digest
from backend.daily_briefing.editorial import validate_editorial, research_plan
from backend.daily_briefing.pdf import render
from backend.knowledge.mcp import invoke
from backend.knowledge.platform import PlatformError
from scripts.maintenance.local_daily_journal import run, write


def event_first(data):
    from daily_editorial_helpers import layout_sample
    if data.get('layout_version',1)==1:
        data.update(layout_sample())
    quality(data)
    data['layout_version']=4
    return data


def selected_candidates(data):
    return [dict(event_key=s['event_key'],event=s['title']['en'],section=s['section'],source_ids=s['source_ids'],decision='selected',story_ids=[s['id']],reason='Synthetic selection: a concrete material release with its verified availability and reader value.') for s in data['stories']]


@pytest.fixture
def event_bundle(quality_bundle):
    d,e,r,path,cutoff=quality_bundle
    d['layout_version']=4
    e['quality_review']['candidate_review']=selected_candidates(d)
    r.update(content_hash=digest(d),evidence_hash=digest(e))
    for name,value in [('issue',d),('evidence',e),('review',r)]:write(path/(name+'.json'),value)
    return d,e,r,path,cutoff


def test_plan_prioritizes_company_events_and_product_release_records():
    plan=research_plan('2026-11-09')
    assert plan['layout_version']==4
    assert set(plan['sections'])=={'companies','products','chips','robotics','infrastructure','policy','business'}
    assert set(plan['sections']['companies']['topics'])=={'model_releases','apps_agents','coding_tools','open_weights','research','people_partnerships'}
    assert 'candidate_review' in plan['evidence_fields']['quality_review']


@pytest.mark.parametrize('change,match',[
    (lambda d,e:e['quality_review'].pop('candidate_review'),'complete quality'),
    (lambda d,e:e['quality_review']['candidate_review'].pop(),'every story'),
    (lambda d,e:e['quality_review']['candidate_review'][0].update(decision='unverified'),'unselected'),
    (lambda d,e:e['quality_review']['candidate_review'][0].update(event_key='unrelated-event'),'differs'),
    (lambda d,e:e['quality_review']['candidate_review'].append(e['quality_review']['candidate_review'][0]),'duplicate candidate'),
    (lambda d,e:e.update(research_checks=[c for c in e['research_checks'] if c['section']!='companies']),'companies'),
    (lambda d,e:e.update(research_checks=[c for c in e['research_checks'] if not(c['section']=='companies' and c['topic']=='open_weights' and c['region']=='cn' and c['method']=='search')]),'open_weights'),
    (lambda d,e:e.update(research_checks=[c for c in e['research_checks'] if c['section']!='products']),'products'),
])
def test_omitted_candidates_and_incomplete_company_research_block(event_bundle,change,match):
    d,e,_,_,cutoff=event_bundle;change(d,e)
    with pytest.raises(ValueError,match=match):validate_editorial(d,e,cutoff)


def test_unknown_launch_date_can_only_be_a_labelled_product_baseline(event_bundle):
    d,e,_,_,cutoff=event_bundle;p=d['products'][0]
    p.update(release_date=None,is_new=False,date_label={'zh':'当前文档，首发日期未核定','en':'Current documentation; launch date unverified'})
    e['product_checks'][0]['release_time']=None
    validate(d);validate_editorial(d,e,cutoff)
    p['is_new']=True
    with pytest.raises(PlatformError,match='labelled baseline'):validate(d)
    p['is_new']=False;e['product_checks'][0]['release_time']=d['date']
    with pytest.raises(ValueError,match='unknown product date'):validate_editorial(d,e,cutoff)


def test_layout_three_keeps_original_evidence_contract(quality_bundle):
    d,e,_,_,cutoff=quality_bundle
    e['research_checks']=[c for c in e['research_checks'] if c['section'] not in ('companies','products')]
    validate(d);validate_editorial(d,e,cutoff)


def test_home_short_highlights_and_bilingual_no_script_match_snapshot(client,issue,fixed_clock):
    event_first(issue)
    issue['headline']={'zh':'不应显示的导读标题','en':'INTRO TITLE MUST NOT RENDER'}
    issue['intro']={'zh':'不应显示的泛泛导读','en':'GENERIC INTRO MUST NOT RENDER'}
    issue['stories'][0]['highlight_title']={'zh':'测试公司发布新模型','en':'Test company releases a model'}
    publish(issue)
    fixed_clock[0]='2026-10-13T09:00:00+08:00'
    for lang in ('zh','en'):
        prefix='/en' if lang=='en' else ''
        preview=client.get('/api/v1/platform/reading?lang='+lang).json['daily']['issue']
        assert preview['highlights'][0]['highlight_title']==issue['stories'][0]['highlight_title'][lang]
        soup=BeautifulSoup(client.get(prefix+'/for-you').text,'html.parser')
        home=soup.select_one('#daily-preview')
        assert issue['headline'][lang] not in home.get_text() and issue['intro'][lang] not in home.get_text()
        assert preview['highlights'][0]['highlight_title'] in home.get_text()
        complete=client.get('/api/v1/daily/2026-10-13?lang='+lang).json
        assert complete==invoke('curated_daily',{'day':'2026-10-13','lang':lang})
        response=client.get(prefix+'/for-you/daily/2026-10-13')
        assert response.status_code==200, response.text
        detail=BeautifulSoup(response.text,'html.parser')
        assert issue['intro'][lang] not in detail.select_one('main').get_text()
        assert len(detail.select('tbody tr'))==30


def test_stage_v4_requires_server_support_and_uses_bound_evidence(client,event_bundle,monkeypatch):
    d,e,r,path,cutoff=event_bundle;configuration=pipeline.configuration
    monkeypatch.setattr(pipeline,'configuration',lambda:dict(configuration(),supported_layout_versions=[1,2,3]))
    site=Site(client)
    with pytest.raises(ValueError,match='Deploy nine-section'):run('stage',d['date'],path,site,now=cutoff)
    assert not site.writes
    monkeypatch.setattr(pipeline,'configuration',lambda:dict(configuration(),supported_layout_versions=[1,2,3,4]))
    assert run('stage',d['date'],path,site,now=cutoff)['state']=='prepared'
    review=next(v for route,v in site.writes if route.endswith('/review'))
    assert review['evidence']==e


def test_long_company_section_paginates_and_preserves_every_story_and_quote(issue):
    event_first(issue)
    for index in range(5):
        s=deepcopy(issue['stories'][0]);s.update(id='extra-company-'+str(index),event_key='extra-company-'+str(index),highlight=False)
        s.pop('highlight_title',None);s.pop('highlight_summary',None)
        for lang in ('zh','en'):s['summary'][lang]*=3
        issue['stories'].append(s)
    for lang in ('zh','en'):
        result=render(issue,lang);pdf=PdfReader(BytesIO(result['bytes']))
        body=re.sub(r'\s+','',''.join(page.extract_text() for page in pdf.pages))
        assert all(re.sub(r'\s+','',s['summary'][lang]) in body for s in issue['stories'])
        assert all(r['ticker'] in body for m in issue['markets'] for r in m['rows'])
        assert re.sub(r'\s+','',issue['intro'][lang]) not in body
        assert digest(service._public_copy(issue)) in pdf.metadata.subject


def test_historical_pdf_and_hash_unchanged_when_layout_four_is_published(client,issue):
    publish(issue);before=service.read(issue['date']);pdf=service.pdf_bytes(issue['date'],'en')[0]
    new=event_first(deepcopy(issue));new.update(date='2026-10-14',window_start='2026-10-13T08:30:00+08:00',cutoff_at='2026-10-14T08:30:00+08:00')
    for s in new['stories']:s['freshness']='recent'
    publish(new)
    after=service.read(issue['date'])
    before.pop('navigation');after.pop('navigation')
    assert after==before
    assert service.pdf_bytes(issue['date'],'en')[0]==pdf
