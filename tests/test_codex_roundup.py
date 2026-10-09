"""Official sequence is a source-backed index, never a redated or extra event."""
import copy
import json
import pytest
from test_knowledge import client, MCP
from test_content_workspace import call, migrate, publish
from test_codex_progress import collection, event
from test_codex_feed import read
from backend.knowledge import platform_news as news


def with_roundup():
    data = collection()
    item = event(data, 'D-85')
    url = 'https://x.com/thsottiaux/status/2107575657014468879'
    if not any(s['url'] == url for s in item['sources']):
        item['sources'].append({'id': 'roundup', 'title': 'Tibo Day 2 roundup', 'url': url, 'coverage': 'link_only'})
    post = copy.deepcopy(item['codex_28_days']['source_posts'][0])
    post.update(url=url, evidence_url=url, kind='supplement', text_scope='full',
                announced_at='2026-10-06T20:56:08.151Z',
                text_en='Roundup of Day 2/\n2.1/ Auto-review\n2.2/ API\n2.3/ Meetings\n2.4/ Decisions',
                translation_zh='Day 2 小结/\n2.1/ 自动审核\n2.2/ API\n2.3/ 会议\n2.4/ 决策')
    # The released seed may already include the real roundup; replace it here.
    item['codex_28_days']['source_posts'] = [p for p in item['codex_28_days']['source_posts'] if p['url'] != url] + [post]
    item['sources'] = list({s['url']: s for s in item['sources']}.values())
    item['codex_28_days']['roundup'] = {'official_day': 2, 'source_url': url,
        'steps': [{'number': n, 'news_id': ident} for n, ident in enumerate(['D-84', 'D-86', 'D-85', 'D-87'], 1)], 'private_note': 'SECRET'}
    return data


def install(data, tmp_path, monkeypatch):
    path = tmp_path / 'roundup-news.json'
    path.write_text(json.dumps(data))
    monkeypatch.setattr(news, 'CONTENT_PATH', path)
    from backend.knowledge import content_workspace as ws
    seeds = ws.seeds(); seeds['news'] = data
    monkeypatch.setattr(ws, 'seeds', lambda: copy.deepcopy(seeds))


def test_roundup_order_preserves_dates_groups_counts_and_privacy():
    public = news.news(_data=with_roundup())
    topic = public['codex_progress']; roundup = topic['roundups'][0]
    assert topic['total'] == 22 and len(topic['days']) == 6
    assert roundup['date'] == '2026-10-07' and roundup['calendar_day'] == 3 and roundup['official_day'] == 2
    assert [s['news_id'] for s in roundup['steps']] == ['D-84', 'D-86', 'D-85', 'D-87']
    assert next(d for d in topic['days'] if d['date'] == '2026-10-07')['ordered_ids'] == ['D-86', 'D-85', 'D-87', 'D-94', 'D-95', 'D-97', 'D-91']
    assert event(public, 'D-84')['codex_28_days']['date'] == '2026-10-06'
    assert event(public, 'D-86')['codex_28_days']['group'] == 'other_openai'
    assert event(public, 'D-87')['codex_28_days']['official_day'] is None
    assert 'SECRET' not in json.dumps(public)


@pytest.mark.parametrize('broken', ['post', 'day', 'sequence', 'duplicate_number', 'duplicate_id', 'missing_id'])
def test_invalid_roundup_evidence_or_references_block_publication(broken):
    data = with_roundup(); meta = event(data, 'D-85')['codex_28_days']; roundup = meta['roundup']
    if broken == 'post': roundup['source_url'] = 'https://x.com/thsottiaux/status/123'
    if broken == 'day': roundup['official_day'] = True
    if broken == 'sequence': roundup['steps'][0]['number'] = 5
    if broken == 'duplicate_number': roundup['steps'][0]['number'] = 2
    if broken == 'duplicate_id': roundup['steps'][0]['news_id'] = 'D-85'
    if broken == 'missing_id': roundup['steps'][0]['news_id'] = 'D-999'
    with pytest.raises(ValueError): news.validate(data)


def test_roundup_scopes_static_html_and_both_mcp_interfaces(client, tmp_path, monkeypatch):
    install(with_roundup(), tmp_path, monkeypatch)
    public = client.get('/api/v1/platform/news').json
    assert read(client)['topic'] == public['codex_progress']
    for group, expected in [('codex', ['D-84', 'D-85']), ('other_openai', ['D-86', 'D-87'])]:
        scoped = read(client, group=group)
        assert [s['news_id'] for s in scoped['topic']['roundups'][0]['steps']] == expected
        assert scoped['topic']['roundups'][0]['total_steps'] == 4
    rpc = client.post('/api/mcp/curated', headers=MCP, json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
        'params': {'name': 'curated_news', 'arguments': {}}}).json['result']['structuredContent']
    assert rpc == public
    page = client.get('/for-you', headers={'Host': 'fieldtofit.top'}).text
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(page, 'html.parser'); card = soup.select_one('.codex-roundup')
    assert [e.get_text() for e in card.select('.codex-step-number')] == ['2.1', '2.2', '2.3', '2.4']
    assert '2026-10-06 已发布' in card.get_text()
    assert len(soup.select('.codex-roundup')) == 1
    assert [e.get('href') for e in soup.select('#codex-day-2026-10-07 .codex-event h6 a')] == ['/news/D-86', '/news/D-85', '/news/D-87', '/news/D-94', '/news/D-95', '/news/D-97', '/news/D-91']


def test_late_roundup_is_readable_without_an_extra_or_redated_event(client, tmp_path, monkeypatch):
    install(with_roundup(), tmp_path, monkeypatch)
    public = client.get('/api/v1/platform/news?id=D-84').json
    topic = public['codex_progress']
    assert topic['total'] == public['total'] == 1
    assert [d['date'] for d in topic['days']] == ['2026-10-07', '2026-10-06']
    assert topic['days'][0]['ordered_ids'] == []
    assert next(d for d in topic['days'] if d['date'] == '2026-10-06')['ordered_ids'] == ['D-84']
    assert topic['roundups'][0]['steps'] == [{'number': 1, 'news_id': 'D-84'}]
    assert public['items'][0]['event_date'] == '2026-10-06'


def test_private_changes_correction_and_withdrawal_do_not_leave_stale_links(client, tmp_path, monkeypatch):
    install(with_roundup(), tmp_path, monkeypatch); migrate(client)
    first = read(client)
    cur = call(client, '/content/news/D-85', method='get').json
    cur['draft']['codex_28_days']['roundup']['steps'].reverse()
    call(client, '/content/news/D-85', cur, 'patch')
    assert read(client, cursor=first['resume_cursor'])['items'] == []
    preview = call(client, '/content/news/D-85/preview').json['preview']
    assert preview['total'] == preview['codex_progress']['total'] == 1
    assert len(preview['codex_progress']['roundups'][0]['steps']) == 4
    assert {i['id'] for i in preview['referenced_items']} == {'D-84', 'D-86', 'D-87'}
    publish(client, 'news', 'D-85')
    # Normalization makes a save in arbitrary order the same public sequence.
    assert read(client, cursor=first['resume_cursor'])['items'] == []
    published = call(client, '/content/news/D-84', method='get').json
    call(client, '/content/news/D-84/withdraw', {'draft_version': published['draft_version'], 'reason': 'isolated source withdrawal'})
    changed = read(client, cursor=first['resume_cursor'])
    assert changed['items'][0]['object_id'] == 'D-84' and changed['items'][0]['kind'] == 'removed'
    assert changed['topic_changed'] and changed['topic']['total'] == first['topic']['total'] - 1
    assert all(s['news_id'] != 'D-84' for s in changed['topic']['roundups'][0]['steps'])
