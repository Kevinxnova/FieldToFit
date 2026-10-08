"""Topic dates and lifecycle use the same reviewed publications as web and MCP."""
import copy
import json
import pytest
from pathlib import Path
from test_knowledge import client, MCP
from test_content_workspace import call, migrate, publish
from backend.knowledge import platform_news as news


def collection():
    return json.loads(news.CONTENT_PATH.read_text())


def event(data, ident='D-78'):
    return next(i for i in data['items'] if i['id'] == ident)


def test_dates_numbering_precision_shared_api_and_mcp(client):
    body = client.get('/api/v1/platform/news').json
    days = body['codex_progress']['days']
    assert [(d['date'], d['calendar_day']) for d in days] == [('2026-10-08', 4), ('2026-10-07', 3), ('2026-10-06', 2), ('2026-10-05', 1)]
    assert days[0]['codex_ids'] == ['D-96'] and days[0]['other_openai_ids'] == []
    assert days[1]['codex_ids'] == ['D-94', 'D-85', 'D-95']
    assert set(days[1]['other_openai_ids']) == {'D-86', 'D-87', 'D-97', 'D-91'}
    assert days[2]['codex_ids'] == ['D-84', 'D-79', 'D-78']
    assert set(days[2]['other_openai_ids']) == {'D-88', 'D-89'}
    assert set(days[3]['other_openai_ids']) == {'D-77', 'D-80', 'D-81'}
    assert event(body)['codex_28_days']['official_day'] == 1
    assert event(body, 'D-77')['event_date'] is None
    assert event(body, 'D-77')['codex_28_days']['announced_at'] is None
    rpc = client.post('/api/mcp/curated', headers=MCP, json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'curated_news','arguments':{}}}).json['result']
    assert rpc['structuredContent'] == body
    filtered = client.get('/api/v1/platform/news?id=D-78').json
    assert filtered['codex_progress']['total'] == 1 and filtered['revision'] == body['revision']
    assert filtered['codex_progress']['days'][0]['codex_ids'] == ['D-78']


@pytest.mark.parametrize('broken', ['no_timezone', 'wrong_day', 'fake_instant', 'unknown_source', 'duplicate', 'future', 'official_day', 'reset_scope'])
def test_invalid_evidence_blocks_publication(broken, monkeypatch):
    from datetime import datetime
    from backend.knowledge import codex_progress
    class FixedTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls.fromisoformat('2026-10-07T12:00:00+08:00').astimezone(tz)
    monkeypatch.setattr(codex_progress, 'datetime', FixedTime)
    data = collection(); item = event(data); meta = item['codex_28_days']
    if broken == 'no_timezone': meta['announced_at'] = '2026-10-05T17:20:29'
    if broken == 'wrong_day': item['event_date'] = '2026-10-05'
    if broken == 'fake_instant': meta.update(date_precision='source_date', timestamp_basis='source_date')
    if broken == 'unknown_source': meta['event_key'] = 'https://example.org/unreviewed'
    if broken == 'duplicate': clone = copy.deepcopy(item); clone['id'] = 'D-99'; data['items'].append(clone)
    if broken == 'future': meta['announced_at'] = '2026-11-01T04:00:00Z'; item['event_date'] = '2026-11-01'
    if broken == 'official_day': meta['official_day'] = True
    if broken == 'reset_scope': meta['type'] = 'reset'
    with pytest.raises((ValueError, TypeError)): news.validate(data)


def test_drafts_withdrawals_and_corrections_are_revisioned_without_private_states(client):
    migrate(client); first = client.get('/api/v1/platform/news').json
    cur = call(client, '/content/news/D-78', method='get').json
    cur['draft']['codex_28_days']['official_day'] = 2
    cur['draft']['codex_28_days']['internal_status'] = 'SECRET-PENDING'
    call(client, '/content/news/D-78', cur, 'patch')
    assert client.get('/api/v1/platform/news').json == first
    preview = call(client, '/content/news/D-78/preview').json
    assert preview['ready'] and preview['preview']['codex_progress']['total'] == 1
    assert 'SECRET-PENDING' not in json.dumps(preview)
    published = publish(client, 'news', 'D-78')
    body = client.get('/api/v1/platform/news').json
    assert body['revision'] != first['revision']
    assert event(body)['publication']['updated_at']
    call(client, '/content/news/D-78/withdraw', {'draft_version':published['draft_version'], 'reason':'Source correction'})
    body = client.get('/api/v1/platform/news').json
    assert body['codex_progress']['total'] == first['codex_progress']['total'] - 1
    assert all('D-78' not in day['codex_ids'] for day in body['codex_progress']['days'])
    assert client.get('/api/v1/platform/news?id=D-78').status_code == 404
    assert client.get('/api/v1/platform/news?revision=' + first['revision']).status_code == 409


def test_no_empty_topic_days_and_search_html_reads_same_logs(client):
    data = collection()
    for item in data['items']: item.pop('codex_28_days', None)
    assert news.news(_data=data)['codex_progress']['days'] == []
    page = client.get('/for-you', headers={'Host':'fieldtofit.top'})
    assert page.status_code == 200
    assert 'id="news-codex-28-days"' in page.text and 'Codex CLI 0.160.1' in page.text
    assert '官方 Day 1' in page.text and '来源日期 · 未提供时刻' in page.text
    assert 'SECRET-PENDING' not in page.text


def test_private_topic_notes_do_not_refresh_public_dates(client, monkeypatch):
    from backend.knowledge import content_workspace as ws
    monkeypatch.setattr(ws, 'today', lambda: collection()['reviewed_at'])
    migrate(client)
    first=client.get('/api/v1/platform/news').json
    cur=call(client, '/content/news/D-78', method='get').json
    cur['draft']['codex_28_days']['internal_status']='SECRET-PENDING'
    call(client, '/content/news/D-78', cur, 'patch')
    publish(client, 'news', 'D-78')
    assert client.get('/api/v1/platform/news').json==first


def test_confirmed_reset_requires_effective_scope_and_keeps_revisioned_evidence():
    data=collection(); item=event(data); meta=item['codex_28_days']
    meta['type']='reset'
    meta['reset']={'scope':'Codex usage allowance','plans':'Eligible subscription plans','source_url':meta['event_key'],'effective_at':'2026-10-06T02:00:00+08:00','internal_note':'SECRET'}
    result=news.news(_data=data)
    reset=event(result)['codex_28_days']['reset']
    assert reset['plans']=='Eligible subscription plans' and 'SECRET' not in json.dumps(result)
    for key in ('scope','plans','source_url','effective_at'):
        broken=copy.deepcopy(data); del event(broken)['codex_28_days']['reset'][key]
        with pytest.raises((ValueError,TypeError)): news.validate(broken)


def source_post():
    return copy.deepcopy(event(collection())['codex_28_days']['source_posts'][0])


@pytest.mark.parametrize('broken', ['account','unregistered','time','duplicate','primary','avatar','future_check','context','private_url'])
def test_source_post_evidence_gate(broken):
    data=collection(); item=event(data); post=item['codex_28_days']['source_posts'][0]
    if broken=='account': post['author_handle']='someone_else'
    if broken=='unregistered': post['evidence_url']='https://example.org/unreviewed'
    if broken=='time': post['announced_at']='2026-10-05T17:20:30.019Z'
    if broken=='duplicate': item['codex_28_days']['source_posts'].append(copy.deepcopy(post))
    if broken=='primary': post['kind']='supplement'
    if broken=='avatar': post['avatar']['url']='https://example.org/tibo.jpg'
    if broken=='future_check': post['avatar']['checked_at']='2099-01-01'
    if broken=='context': post['context']={'kind':'quote','url':post['url'],'author_name':'Other','author_handle':'other','text_en':'Excerpt','translation_zh':'摘译','text_scope':'excerpt'}
    if broken=='private_url': post['url']='https://x.com/thsottiaux/status/2107158998495748264?token=secret'
    with pytest.raises((ValueError,TypeError)): news.validate(data)


def test_posts_round_trip_corrections_private_notes_and_withdrawal(client,monkeypatch):
    from backend.knowledge import content_workspace as ws
    from backend import seo
    monkeypatch.setattr(ws,'today',lambda:collection()['reviewed_at'])
    migrate(client)
    first=client.get('/api/v1/platform/news').json
    cur=call(client,'/content/news/D-78',method='get').json
    cur['draft']['codex_28_days']['source_posts'][0]['private_note']='SECRET-PENDING'
    cur['draft']['codex_28_days']['source_posts'][0]['avatar']['internal']='SECRET-PENDING'
    call(client,'/content/news/D-78',cur,'patch');publish(client,'news','D-78')
    assert client.get('/api/v1/platform/news').json==first
    cur=call(client,'/content/news/D-78',method='get').json
    cur['draft']['codex_28_days']['overview_zh']='已审摘要修订'
    cur['draft']['codex_28_days']['source_posts'][0]['translation_zh']='已审摘译修订'
    call(client,'/content/news/D-78',cur,'patch')
    assert client.get('/api/v1/platform/news').json==first
    pre=call(client,'/content/news/D-78/preview').json
    assert pre['ready'] and 'SECRET-PENDING' not in json.dumps(pre)
    published=publish(client,'news','D-78');body=client.get('/api/v1/platform/news').json
    assert body['revision']!=first['revision'] and event(body)['publication']['updated_at']
    for path in ('/for-you','/news/D-78'):
        page=client.get(path,base_url=seo.ORIGIN)
        assert page.status_code==200 and '已审摘译修订' in page.text and 'SECRET-PENDING' not in page.text
        assert 'tibo-6a3ab22f.jpg' in page.text and '英文原文摘录' in page.text
    rpc=client.post('/api/mcp/curated',headers=MCP,json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'curated_news','arguments':{}}}).json['result']['structuredContent']
    assert rpc==body
    assert any(path=='/news/D-78' and changed for path,changed in seo.sitemap_entries())
    call(client,'/content/news/D-78/withdraw',{'draft_version':published['draft_version'],'reason':'撤销原帖记录'})
    assert 'tibo-6a3ab22f.jpg' not in client.get('/for-you').text
    assert client.get('/news/D-78').status_code==404


def test_related_posts_preserve_distinct_context_author_and_private_projection():
    data=collection();item=event(data);post=copy.deepcopy(item['codex_28_days']['source_posts'][0])
    post.update(url='https://x.com/thsottiaux/status/2106845241357824205',kind='supplement',announced_at='2026-10-04T20:33:43.488Z')
    item['sources'].append({'id':'context','title':'Registered quote','url':'https://x.com/example/status/123','coverage':'link_only'})
    post['context']={'kind':'quote','url':'https://x.com/example/status/123','author_name':'Other author','author_handle':'example','text_en':'Context excerpt','translation_zh':'上下文摘译','text_scope':'excerpt','private_note':'SECRET'}
    item['sources'].append({'id':'supplement','title':'Registered supplement','url':post['url'],'coverage':'link_only'})
    item['codex_28_days']['source_posts'].append(post)
    result=event(news.news(_data=data))['codex_28_days']['source_posts']
    assert result[0]['kind']=='primary' and result[1]['context']['author_handle']=='example'
    assert 'SECRET' not in json.dumps(result)


def test_month_grid_has_real_dates_without_creating_logs():
    from backend.knowledge.codex_progress import calendar_month
    topic=news.news(_data=collection())['codex_progress'];before=copy.deepcopy(topic)
    oct=calendar_month(2026,10,topic);nov=calendar_month(2026,11,topic)
    assert len(oct)==35 and oct[0]['date']=='2026-09-28' and oct[-1]['date']=='2026-11-01'
    assert len(nov)==42 and nov[0]['date']=='2026-10-26' and nov[-1]['date']=='2026-12-06'
    assert sum(bool(c['log']) for c in oct)==4 and sum(bool(c['log']) for c in nov)==0
    assert topic==before


def test_cached_avatar_is_a_static_image_and_missing_files_are_404(client,tmp_path,monkeypatch):
    import backend.api.main as main
    folder=tmp_path/"source-authors";folder.mkdir()
    (folder/"tibo-6a3ab22f.jpg").write_bytes(Path("frontend/public/source-authors/tibo-6a3ab22f.jpg").read_bytes())
    monkeypatch.setattr(main,"CLIENT_DIST",tmp_path)
    image=client.get('/source-authors/tibo-6a3ab22f.jpg')
    assert image.status_code==200 and image.mimetype=='image/jpeg'
    assert image.data.startswith(b'\xff\xd8')
    assert client.get('/source-authors/missing.jpg').status_code==404
