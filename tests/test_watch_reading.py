"""Source-backed overview and milestone behavior, using isolated publications."""
import copy
import json
import re

from test_knowledge import client, MCP
from backend.knowledge import platform_watch, platform_news
from backend.knowledge.watch_reading import recent_event
from backend.knowledge.watch_reading_data import PROFILES
from backend.knowledge.watch_history import HISTORY, historical_milestones


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


def test_history_starts_with_first_generation_and_keeps_real_launch_context(client):
    chat = client.get('/api/v1/platform/watch?id=CW-M01').json['items'][0]
    claude = client.get('/api/v1/platform/watch?id=CW-M02').json['items'][0]
    assert (chat['milestones'][0]['date'], chat['milestones'][0]['name']) == ('2018-06-11', 'GPT（初代）')
    assert (claude['milestones'][0]['date'], claude['milestones'][0]['name']) == ('2023-03-14', 'Claude（初代）')
    for profile in (chat, claude):
        history = [m for m in profile['milestones'] if m['id'].startswith('history-')]
        assert len(history) >= 19
        assert history[0]['kind'] == 'model'
        assert history[0]['price'] is None and history[0]['price_condition']
        assert len({m['id'] for m in profile['milestones']}) == len(profile['milestones'])
        assert [m['date'] for m in profile['milestones']] == sorted(m['date'] for m in profile['milestones'])
        for m in history:
            assert m['news_id'] is None and m['checked_at'] == '2026-10-12'
            assert all(s['url'].startswith(('https://openai.com/', 'https://community.openai.com/', 'https://www.anthropic.com/')) for s in m['sources'])
            assert all(set(p['source_ids']) <= {s['id'] for s in m['sources']} for p in m['points'])
        assert all(e['id'].startswith('D-') for e in profile['events'])
    by_name = {m['name']: m for m in chat['milestones']}
    assert by_name['GPT-4o']['price'] == '5 / 15'  # Launch, not the later $2.50 / $10.
    assert by_name['GPT-3.5 Turbo']['date'] == '2023-03-01'  # Not the blog's 2024 update.
    assert by_name['ChatGPT 研究预览']['date'] == '2022-11-30'
    assert by_name['ChatGPT 研究预览']['kind'] == 'product'
    assert by_name['GPT-5.5']['date'] == '2026-04-23' and '24' in by_name['GPT-5.5']['price_condition']
    haiku = next(m for m in claude['milestones'] if m['name'] == 'Claude 3 Haiku')
    assert haiku['date'] == '2024-03-13'  # Availability, not the family announcement.


def test_history_is_copied_revisioned_and_does_not_create_news(client, monkeypatch):
    first = historical_milestones('CW-M01')
    first[0]['points'][0]['text'] = 'LOCAL RESPONSE EDIT'
    assert 'LOCAL RESPONSE EDIT' not in json.dumps(historical_milestones('CW-M01'))
    before = client.get('/api/v1/platform/watch?id=CW-M01').json
    changed = copy.deepcopy(HISTORY['CW-M01'])
    changed[0]['price_condition'] = ('研究发布，无商业报价', 'Research release without commercial pricing')
    monkeypatch.setitem(HISTORY, 'CW-M01', changed)
    after = client.get('/api/v1/platform/watch?id=CW-M01').json
    assert before['revision'] != after['revision']
    assert before['items'][0]['events'] == after['items'][0]['events']


def test_withdrawn_profile_does_not_reappear_through_history(client, tmp_path, monkeypatch):
    data = json.loads(platform_watch.CONTENT_PATH.read_text())
    next(i for i in data['items'] if i['id'] == 'CW-M01')['state'] = 'withdrawn'
    path = tmp_path/'watch.json'; path.write_text(json.dumps(data))
    monkeypatch.setattr(platform_watch, 'CONTENT_PATH', path)
    body = client.get('/api/v1/platform/watch').json
    assert all(i['id'] != 'CW-M01' for i in body['items'])
    assert 'history-gpt-1' not in json.dumps(body)


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
