"""Homepage rotation against isolated SQLite; never publishes to the live site."""
import copy
import json

import pytest
from bs4 import BeautifulSoup
from test_knowledge import client, MCP
from test_content_workspace import call, make, migrate, publish
from test_search_pages import site
from english_fixtures import fixture_fields, approve_fixture
from backend.knowledge import content_workspace as ws, locale, technical_maps as tm
from backend.knowledge import report_selection as rs


@pytest.fixture
def reports(monkeypatch):
    data = ws.seeds()
    template = copy.deepcopy(next(i for i in data['news']['items'] if i['id'] == 'D-90'))
    data['news']['items'] = [i for i in data['news']['items'] if not i.get('technical_map')]
    rows = []
    for n in range(1, 7):
        item = copy.deepcopy(template)
        item.update(id=f'D-90{n}', title=f'Isolated report {n}', highlight=False,
                    publication={'first_published_at': f'2026-10-0{n}T10:00:00+00:00',
                                 'updated_at': f'2026-10-0{n}T10:00:00+00:00'})
        graph = item['technical_map']
        graph.update(slug=f'isolated-report-{n}', question=f'Isolated question {n}')
        # Source recency deliberately disagrees with site publication order.
        graph['reports'][0].update(first_published_at='2000-01-01' if n == 6 else '2026-10-01',
                                   revised_at=None, substantive_revision=False)
        item.pop('translations', None)
        item['translations'] = {'en': {'state': 'reviewed', 'source_hash': locale.source_hash('news', item),
                                      'fields': fixture_fields(locale.status('news', item))}}
        rows.append(item)
    data['news']['items'] = rows + data['news']['items']
    monkeypatch.setattr(ws, 'seeds', lambda: copy.deepcopy(data))
    return rows


def edit(ident, change):
    current = ws.detail('news', ident)
    change(current['draft'])
    return ws.save('news', ident, current)


def ids():
    return [i['id'] for i in tm.maps()['items']]


def test_complete_index_homepage_html_reading_and_mcp_agree(site, reports):
    migrate(site)
    expected = ['D-906', 'D-905', 'D-904', 'D-903']
    for lang in ['zh', 'en']:
        news = site.get('/api/v1/platform/news', query_string={'lang': lang}).json
        maps = site.get('/api/v1/platform/maps', query_string={'lang': lang}).json
        reading = site.get('/api/v1/platform/reading', query_string={'lang': lang}).json
        assert news['report_selection']['ids'] == maps['report_selection']['ids'] == expected
        assert reading['news']['report_selection'] == news['report_selection']
        assert [m['id'] for m in maps['items'][:4]] == expected and maps['total'] == 6
        prefix = '/en' if lang == 'en' else ''
        response = site.get(prefix + '/for-you')
        assert response.status_code == 200
        section = BeautifulSoup(response.data, 'html.parser').find(id='technical-evolution-maps')
        assert len(section.select('time[datetime]')) == 4
        assert [a['href'].split('/')[-1] for a in section.select('article h3 a')] == [f'isolated-report-{n}' for n in [6, 5, 4, 3]]
        index = site.get(prefix + '/maps')
        assert index.status_code == 200
        for n in range(1, 7):
            assert ('/maps/isolated-report-' + str(n)).encode() in index.data
        rpc = site.post('/api/mcp/curated', headers=MCP, json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                        'params': {'name': 'curated_maps', 'arguments': {'lang': lang}}}).json['result']
        assert not rpc.get('isError') and rpc['structuredContent'] == maps
    assert site.get('/api/v1/platform/maps?archive=historical').json['items'][0]['id'] == 'D-906'
    assert site.get('/api/v1/platform/maps?q=question+1').json['items'][0]['id'] == 'D-901'


def test_new_report_replaces_oldest_only_after_success(client, reports, monkeypatch):
    migrate(client)
    original = tm.maps()
    ident, _ = make(client, 'news')
    content = copy.deepcopy(reports[0])
    content.update(id=ident, title='Selected new report', publication={'first_published_at': '1999-01-01T00:00:00Z',
                   'updated_at': '2999-01-01T00:00:00Z', 'report_selected_at': '2999-01-01T00:00:00Z'})
    content['technical_map'].update(slug='selected-new-report', question='Selected new question')
    current = ws.detail('news', ident)
    ws.save('news', ident, {'draft_version': current['draft_version'], 'draft': content})
    assert tm.maps() == original
    preview = call(client, f'/content/news/{ident}/preview').json
    assert preview['ready'] and tm.maps() == original
    stale = call(client, f'/content/news/{ident}/publish', {'draft_version': preview['draft_version'],
                 'review_token': 'stale', 'confirmed': True, 'reason': 'Must not rotate'})
    assert stale.status_code == 409 and tm.maps() == original
    monkeypatch.setattr(ws, 'stamp', lambda: '2026-10-15T10:00:00+00:00')
    result = publish(client, 'news', ident)
    receipt = result['report_rotation']
    assert receipt['status'] == 'published' and receipt['changed']
    assert [i['id'] for i in receipt['entered']] == [ident]
    assert [i['id'] for i in receipt['index_only']] == ['D-903']
    assert ids() == [ident, 'D-906', 'D-905', 'D-904', 'D-903', 'D-902', 'D-901']
    assert result['published']['publication']['report_selected_at'] == '2026-10-15T10:00:00+00:00'
    assert client.get('/api/v1/platform/maps?slug=isolated-report-3').status_code == 200


def test_copy_checks_links_and_forged_dates_never_promote(client, reports, monkeypatch):
    migrate(client)
    original = ids()
    monkeypatch.setattr(ws, 'stamp', lambda: '2026-10-15T11:00:00+00:00')
    def copy_edit(draft):
        draft['summary'] = 'Corrected explanation only'
        draft['checked_at'] = ws.today()
        draft['publication']['report_selected_at'] = '2999-01-01T00:00:00+00:00'
        draft['sources'][0]['url'] = 'https://example.org/corrected-report-link'
    edit('D-901', copy_edit)
    result = publish(client, 'news', 'D-901')
    assert ids() == original and not result['report_rotation']['changed']
    assert result['published']['publication']['updated_at'] == '2026-10-15T11:00:00+00:00'
    assert result['published']['publication']['report_selected_at'] == reports[0]['publication']['first_published_at']
    assert result['published']['publication']['first_published_at'] == reports[0]['publication']['first_published_at']


def test_new_substantive_revision_promotes_once(client, reports, monkeypatch):
    migrate(client)
    monkeypatch.setattr(ws, 'stamp', lambda: '2026-10-15T12:00:00+00:00')
    def revision(draft):
        draft['technical_map']['reports'][0].update(version='v2', revised_at=ws.today(),
                      substantive_revision=True, revision_note='New method and experiment results')
        draft['technical_map']['change_summary'] = 'New method and experiment results'
    edit('D-901', revision)
    first = publish(client, 'news', 'D-901')
    assert ids()[0] == 'D-901' and first['report_rotation']['entered'][0]['id'] == 'D-901'
    selected = first['published']['publication']['report_selected_at']
    monkeypatch.setattr(ws, 'stamp', lambda: '2026-10-15T13:00:00+00:00')
    edit('D-901', lambda d: d['technical_map'].update(caution='Copy clarification only'))
    second = publish(client, 'news', 'D-901')
    assert not second['report_rotation']['changed']
    assert second['published']['publication']['report_selected_at'] == selected
    assert second['published']['publication']['updated_at'] != selected


def test_withdraw_refills_and_transaction_failure_preserves_public_selection(client, reports, monkeypatch):
    migrate(client)
    edit('D-901', lambda d: d['technical_map'].update(takeaway='Uncommitted change'))
    approve_fixture('news', 'D-901')
    preview = ws.preview('news', 'D-901')
    before = tm.maps()
    def fail(*args):
        raise RuntimeError('Simulated transactional failure')
    with monkeypatch.context() as m:
        m.setattr(ws, 'execute_statements', fail)
        with pytest.raises(RuntimeError):
            ws.publish('news', 'D-901', {**preview, 'confirmed': True, 'reason': 'Isolated failure'})
    assert tm.maps() == before
    current = ws.detail('news', 'D-906')
    result = ws.publish('news', 'D-906', {'draft_version': current['draft_version'], 'reason': 'Isolated withdrawal'}, True)
    assert [i['id'] for i in result['report_rotation']['after']] == ['D-905', 'D-904', 'D-903', 'D-902']
    assert result['report_rotation']['index_only'] == [] and tm.maps()['total'] == 5
    assert client.get('/api/v1/platform/maps?slug=isolated-report-6').status_code == 404


def test_unknown_dates_do_not_invent_recency_and_small_windows_are_complete():
    items = [{'id': 'D-1', 'technical_map': {'slug': 'unknown'}, 'publication': {'updated_at': '2999-01-01T00:00:00Z'}},
             {'id': 'D-2', 'technical_map': {'slug': 'known'}, 'publication': {'first_published_at': '2020-01-01T00:00:00Z'}}]
    assert rs.selection(items)['ids'] == ['D-2', 'D-1']
    assert rs.selected_at(items[0]) is None
    assert rs.selection([])['ids'] == [] and len(rs.selection(items)['ids']) == 2
