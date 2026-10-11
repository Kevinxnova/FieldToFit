"""Source-backed overview and milestone behavior, using isolated publications."""
import copy
import json
import re

from test_knowledge import client, MCP
from backend.knowledge import platform_watch, platform_news
from backend.knowledge.watch_reading import recent_event
from backend.knowledge.watch_reading_data import PROFILES


def test_all_profiles_have_meaningful_overview_and_real_event_basis(client):
    body = client.get('/api/v1/platform/watch').json
    assert body['reading_status'] == 'ready'
    assert [i['id'] for i in body['items'][:2]] == ['CW-M01', 'CW-M02']
    assert [i['name'] for i in body['items'][:2]] == ['ChatGPT', 'Claude']
    assert {i['id'] for i in body['items']} <= set(PROFILES)
    for item in body['items']:
        overview = item['overview']
        event = overview['recent_event']
        assert overview['category'] != '-'
        assert event['title'] not in ('', '-')
        assert event['date_kind'] in ('release', 'source', 'review', 'commit')
        assert event.get('news_id') or event['url'].startswith('https://')
        if overview['category'] == '通用模型': assert overview['purpose'] == '-'
    kimi = next(i for i in body['items'] if i['id'] == 'CW-M04')
    assert kimi['overview']['recent_event']['news_id'] != 'D-75'  # Beam is further reading, not Kimi's launch.
    assert client.get('/api/v1/platform/watch?type=tool').json['items'][0]['type'] == 'tool'
    assert client.get('/api/v1/platform/watch?q=ChatGPT').json['items'][0]['id'] == 'CW-M01'
    assert not any(i['id'] == 'CW-M01' for i in client.get('/api/v1/platform/watch?q=Kolibri').json['items'])


def test_history_prices_and_dates_are_preserved(client):
    chat = client.get('/api/v1/platform/watch?id=CW-M01').json['items'][0]
    claude = client.get('/api/v1/platform/watch?id=CW-M02').json['items'][0]
    assert {m['kind'] for m in chat['milestones']} == {'model', 'product'}
    assert all(chat['milestones'][i]['date'] <= chat['milestones'][i+1]['date'] for i in range(len(chat['milestones'])-1))
    assert len(chat['events']) > 10  # Full history, not a homepage seven-day filter.
    assert len({e['id'] for e in chat['events']}) == len(chat['events'])
    assert chat['events'] == sorted(chat['events'], key=lambda e: (e.get('event_date') or e.get('source_published_at') or '', e['id']), reverse=True)
    astra = next(m for m in chat['milestones'] if m['name'] == 'GPT-6 Astra')
    assert astra['date'] == '2026-09-03' and astra['date_kind'] == 'source' and astra['price'] is None
    sol = next(m for m in chat['milestones'] if m['name'] == 'GPT-6.1 Sol')
    assert sol['price'] == '2 / 10' and '272K' in sol['price_condition']
    haiku = next(m for m in claude['milestones'] if m['name'] == 'Claude Haiku 5.5')
    assert haiku['price'] == '0.10 / 0.50' and '$0.50 / $2.50' in haiku['price_condition']
    assert all(m['sources'] and m['points'] for m in [*chat['milestones'], *claude['milestones']])


def test_newest_window_uses_editorial_evidence_not_fake_heat():
    events = [{'id': 'D-1', 'event_date': '2026-09-01', 'highlight': True},
              {'id': 'D-2', 'event_date': '2026-10-05', 'highlight': False},
              {'id': 'D-3', 'event_date': '2026-10-04', 'highlight': True}]
    assert recent_event(events)['id'] == 'D-3'
    assert recent_event(events[:2])['id'] == 'D-2'


def test_withdrawn_and_private_news_never_leak_and_revision_changes(client, tmp_path, monkeypatch):
    before = client.get('/api/v1/platform/watch?id=CW-M01').json
    data = json.loads(platform_news.CONTENT_PATH.read_text())
    item = next(i for i in data['items'] if i['id'] == 'D-53')
    item['state'] = 'withdrawn'
    draft = copy.deepcopy(item); draft.update(id='D-999',state='draft',title='PRIVATE EVENT')
    data['items'].append(draft)
    path = tmp_path/'news.json'; path.write_text(json.dumps(data))
    monkeypatch.setattr(platform_news, 'CONTENT_PATH', path)
    after = client.get('/api/v1/platform/watch?id=CW-M01').json
    assert before['revision'] != after['revision']
    assert 'PRIVATE EVENT' not in json.dumps(after)
    assert not any(e['id']=='D-53' for e in after['items'][0]['events'])
    assert not any(m['news_id']=='D-53' for m in after['items'][0]['milestones'])


def test_bilingual_api_and_mcp_share_complete_reading_data(client):
    response = client.get('/api/v1/platform/watch?lang=en')
    assert response.status_code == 200, response.json
    body = response.json
    for item in body['items']:
        for key in ('overview', 'milestones', 'events'):
            assert not re.search(r'[\u3400-\u9fff]',json.dumps(item.get(key),ensure_ascii=False))
    rpc = client.post('/api/mcp/curated', headers=MCP, json={'jsonrpc':'2.0','id':1,'method':'tools/call',
        'params':{'name':'curated_watch','arguments':{'lang':'en'}}}).json['result']
    assert rpc['structuredContent'] == body


def test_news_failure_remains_explicit_with_profile_records(client, tmp_path, monkeypatch):
    path = tmp_path/'broken.json'; path.write_text('{}')
    monkeypatch.setattr(platform_news, 'CONTENT_PATH', path)
    response = client.get('/api/v1/platform/watch')
    assert response.status_code == 200
    assert response.json['reading_status'] == 'news_unavailable'
    assert all(i['overview']['recent_event']['title'] not in ('', '-') for i in response.json['items'])
