"""Independent company topics, current publication boundaries and shared reading."""
import copy
import json
from bs4 import BeautifulSoup
from test_knowledge import client
from test_search_pages import site
from backend.knowledge.company_updates import metadata, ordered, projection


def test_identity_dates_and_no_invented_timestamps():
    item={'id':'D-999','organization':'OpenAI','name':'Codex CLI','source_published_at':'2026-11-03'}
    assert metadata(item, '2026-11-09') == {'company':'openai','date':'2026-11-03','display_time':'2026-11-03','date_precision':'source_date','products':['codex'],'announced_at':None}
    for change in ({'organization':'Third party using OpenAI'}, {'organization':'OpenAI / Other'}, {'state':'draft'}, {'state':'withdrawn'}, {'source_published_at':'2026-11-01'}, {'event_date':'2026-11-11'}, {'source_published_at':None}):
        assert metadata({**item,**change},'2026-11-09') is None
    timed={**item,'codex_28_days':{'date':'2026-11-02','date_precision':'exact','announced_at':'2026-11-01T23:27:20Z','group':'codex'}}
    assert metadata(timed,'2026-11-09')['display_time']=='2026-11-02 07:27'


def test_sort_does_not_promote_corrections_and_projection_never_mutates():
    items=[]
    for n,day in [(1,'2026-11-03'),(2,'2026-11-05')]:
        i={'id':f'D-{n:03}','organization':'Anthropic','name':'Claude Code','event_date':day,'publication':{'updated_at':'2026-11-09' if n==1 else '2026-11-05'}}
        i['company_update']=metadata(i,'2026-11-09');items.append(i)
    before=copy.deepcopy(items)
    assert [i['id'] for i in ordered(items,'anthropic')]==['D-002','D-001']
    assert projection(items)['anthropic']['products']==['claude-code']
    assert items==before


def test_api_mcp_and_reading_have_identical_company_membership(client):
    from test_mcp_reading import call
    full=client.get('/api/v1/platform/news').json
    for lang in ('zh','en'):
        for company in ('openai','anthropic'):
            api=client.get('/api/v1/platform/news',query_string={'company':company,'lang':lang}).json
            assert api['revision']==full['revision']
            ids=api['company_topics'][company]['ids']
            assert ids and len(ids)==api['total']
            assert all(i['organization']==('OpenAI' if company=='openai' else 'Anthropic') for i in api['items'])
            read=client.get('/api/v1/platform/reading?view='+company+'&lang='+lang).json
            assert [i['id'] for i in read['news']['items']]==ids
            result=call(client,'curated_news',company=company,lang=lang)
            assert not result['isError']
            mcp=json.loads(result['content'][0]['text'])
            assert mcp['company_topics'][company]['ids']==ids
    assert client.get('/api/v1/platform/news?company=unknown').status_code==400


def test_home_bounds_and_archive_default_folded(site):
    for prefix,lang in (('','zh'),('/en','en')):
        data=site.get('/api/v1/platform/reading?view=home&lang='+lang).json
        soup=BeautifulSoup(site.get(prefix+'/for-you').text,'html.parser')
        for company in ('openai','anthropic'):
            preview=data['home_preview']['companies'][company]
            assert len(preview)<=10
            node=soup.select_one('#'+company+'-updates')
            direct=node.find('ul',recursive=False)
            assert len(direct.select('li'))==min(3,len(preview))
            assert len(node.select('li'))==len(preview)
            assert [li['id'].split('-',1)[1] for li in node.select('li')]==preview
        archive=soup.select_one('#historical-topics details')
        assert archive is not None and not archive.has_attr('open')
        assert archive.select_one('a')['href']==prefix+'/for-you/codex'
        assert site.get(prefix+'/for-you/codex').status_code==200


def test_full_page_filters_work_without_scripts_and_bootstrap_stays_whole(site):
    for prefix in ('','/en'):
        soup=BeautifulSoup(site.get(prefix+'/for-you/anthropic?product=claude-code&month=2026-11&topic_q=Claude').text,'html.parser')
        rows=soup.select('.company-topic li')
        assert rows
        boot=json.loads(soup.select_one('#fieldtofit-reading').text)
        by_id={i['id']:i for i in boot['data']['news']['items']}
        for row in rows:
            item=by_id[row['id'].split('-',1)[1]]
            assert 'claude-code' in item['company_update']['products']
        assert len(by_id)>len(rows)
        empty=BeautifulSoup(site.get(prefix+'/for-you/openai?topic_q=not-an-existing-update').text,'html.parser')
        assert not empty.select('.company-topic li')


def test_current_withdrawal_and_company_change_remove_topic_membership(client):
    from test_content_workspace import migrate
    from backend.db import get_db
    migrate(client)
    current=client.get('/api/v1/platform/news?company=anthropic').json
    withdrawn,moved=[i['id'] for i in current['items'][:2]]
    with get_db() as db:
        raw=json.loads(db.execute("SELECT published_json FROM fieldtofit_content_sets WHERE kind='news'").fetchone()[0])
        for item in raw['items']:
            if item['id']==withdrawn:item['state']='withdrawn'
            if item['id']==moved:item['organization']='Another company'
        db.execute("UPDATE fieldtofit_content_sets SET published_json=?, revision=revision+1 WHERE kind='news'",(json.dumps(raw),))
    result=client.get('/api/v1/platform/reading?view=anthropic').json
    assert {withdrawn,moved}.isdisjoint(i['id'] for i in result['news']['items'])
