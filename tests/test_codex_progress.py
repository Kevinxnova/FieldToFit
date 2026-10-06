"""Topic dates and lifecycle use the same reviewed publications as web and MCP."""
import copy
import json
import pytest
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
    assert [(d['date'], d['calendar_day']) for d in days] == [('2026-10-06', 2), ('2026-10-05', 1)]
    assert days[0]['codex_ids'] == ['D-79', 'D-78']
    assert set(days[1]['other_openai_ids']) == {'D-77', 'D-80', 'D-81'}
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
            return cls.fromisoformat('2026-10-06T12:00:00+08:00').astimezone(tz)
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
    assert body['codex_progress']['total'] == 4
    assert 'D-78' not in body['codex_progress']['days'][0]['codex_ids']
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
    monkeypatch.setattr(ws, 'today', lambda: '2026-10-06')
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
