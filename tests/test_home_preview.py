"""Homepage boundaries, live publication identity, and new reading routes."""
import copy
import json
import re
from bs4 import BeautifulSoup
from werkzeug.datastructures import MultiDict

from test_knowledge import client
from test_search_pages import site
from backend.knowledge.home_preview import project
from backend.seo.for_you import news_archive

PATH = '/api/v1/platform/reading'


def test_home_contains_only_bounded_previews_and_real_chart_metadata(client):
    full = client.get(PATH).json
    response = client.get(PATH+'?view=home')
    assert response.status_code == 200
    home = response.json
    preview = home['home_preview']
    assert preview['highlights'] == [i['id'] for i in full['news']['items'] if i.get('highlight')][:3]
    assert preview['reports'] == full['news']['report_selection']['ids'][:4]
    assert len(preview['hot_cards']) <= 3 and len(preview['codex']) <= 3
    assert len(home['watch']['items']) <= 3
    assert home['watch']['groups'] == full['watch']['groups']
    assert home['watch']['total'] == full['watch']['total']
    assert home['news']['total'] == full['news']['total']
    assert home['charts']['sources'] == [] and home['projects']['items'] == []
    assert 'codex_progress' not in home['news']
    assert all('source_posts' not in i.get('codex_28_days', {}) and not i['interpretation'] for i in home['news']['items'])
    originals = {i['id']:i for i in full['news']['items']}
    for item in home['news']['items']:
        assert item['title'] == originals[item['id']]['title']
        if 'hot_card' in item:
            assert item['hot_card'] == originals[item['id']]['hot_card']
    for source, preview in zip(full['charts']['sources'], home['chart_previews']):
        assert preview['coverage'] == source['coverage']
        for key in ('source_url','source_updated_at','checked_at','score_label','price_label','price_label_en'):
            assert preview[key] == source[key]
        assert 'points' not in preview and preview['image'].startswith('data:image/svg+xml;base64,')
    assert len(response.data) < len(client.get(PATH).data)*.45
    assert home['safety'] == full['safety']
    assert client.get(PATH).json == full  # A lightweight view cannot mutate full public reads.


def test_section_views_keep_complete_column_and_omit_unrelated_bodies(client):
    full = client.get(PATH).json
    for view in ('news','watch','models','hot-cards','codex'):
        response = client.get(PATH+'?view='+view)
        assert response.status_code == 200
        data = response.json
        assert data['safety'] == full['safety']
        if view == 'models':
            assert data['charts'] == full['charts'] and not data['news']['items']
        else:
            assert not data['charts']['sources']
        if view == 'watch':
            assert data['watch'] == full['watch']
            ids = {i['id'] for i in data['watch']['items']}
            assert all(any(r['id'] in ids for r in i['related']) for i in data['news']['items'])
            assert {i['id'] for i in full['news']['items'] if i.get('technical_map') and any(r['id'] in ids for r in i['related'])} <= {i['id'] for i in data['news']['items']}
        else:
            assert not data['watch']['items']
        if view == 'codex':
            assert data['news']['codex_progress'] == full['news']['codex_progress']
            assert data['news']['items'] == [i for i in full['news']['items'] if i.get('codex_28_days')]
        else:
            assert 'codex_progress' not in data['news']
        if view == 'hot-cards':
            assert {i['id'] for i in data['news']['items']} == {i['id'] for i in full['news']['items'] if i.get('hot_card')}
            assert data['news']['total'] == len(data['news']['items'])
    assert client.get(PATH+'?view=unknown').status_code == 400
    assert client.get(PATH+'?view=home&after='+full['revision']).json['unchanged'] is True


def test_no_events_means_no_invented_watch_updates_or_filled_slots(client):
    full = client.get(PATH).json
    original = copy.deepcopy(full)
    for item in full['news']['items']:
        item['event_date'] = item['source_published_at'] = None
        item['highlight'] = False
        item.pop('codex_28_days', None)
        item.pop('hot_card', None)
    full['news']['report_selection']['ids'] = []
    home = project(full, 'home')
    assert not home['watch']['items']
    assert home['home_preview'] == {'highlights':[], 'hot_cards':[], 'reports':[], 'codex':[], 'watch_events':[]}
    assert home['watch']['groups'] == original['watch']['groups']


def test_public_pages_bootstrap_same_projection_and_seven_section_order(site):
    order = ['daily-preview','recent-news','hot-information-cards','technical-evolution-maps','news-codex-28-days','model-landscape','resource-dossiers']
    for prefix, lang in (('', 'zh'),('/en','en')):
        for view in ('home','news','hot-cards','codex','models','watch'):
            path = '/for-you'+('' if view == 'home' else '/'+view)
            response = site.get(prefix+path)
            assert response.status_code == 200, (path,response.text[:200])
            boot = json.loads(re.search(r'id="fieldtofit-reading">(.*?)</script>', response.text, re.S)[1])
            assert boot['view'] == view and boot['language'] == lang
            assert boot['data'] == site.get(PATH+'?view='+view+'&lang='+lang).json
            assert response.text.count('rel="canonical"') == 1
            assert 'https://fieldtofit.top'+prefix+path+'"' in response.text
            if view == 'home':
                positions = [response.text.index('id="'+anchor+'"') for anchor in order]
                assert positions == sorted(positions)
                assert 'codex-month-grid' not in response.text
                assert 'class="watch-table"' not in response.text
                for slug in ('news','models','watch','hot-cards','codex'):
                    assert 'href="'+prefix+'/for-you/'+slug in response.text


def test_watch_search_still_matches_complete_profile_body(client):
    for query in ('runtime','Docker','GPT','部署'):
        expected=client.get('/api/v1/platform/watch',query_string={'q':query}).json
        actual=client.get(PATH,query_string={'view':'watch','q':query}).json
        assert [i['id'] for i in actual['watch']['items']] == [i['id'] for i in expected['items']]


def test_shared_archive_filters_work_without_scripts(site):
    query = {'news_range':'all', 'news_q':'Codex', 'news_page':'2'}
    response = site.get('/for-you/news', query_string=query)
    soup = BeautifulSoup(response.text, 'html.parser')
    cards = soup.select('#news-releases article')
    assert len(cards) == 10
    originals = {i['id']:i for i in site.get(PATH).json['news']['items']}
    ids = {c.select_one('a')['href'].split('/')[-1] for c in cards}
    for ident in ids:
        item = originals[ident]
        # Related dossier names are searchable even when absent from the visible title.
        searchable = [item['title'],item['name'],item['summary'],item['organization']]+[r['name'] for r in item['related']]
        assert any('codex' in text.lower() for text in searchable)
    first = BeautifulSoup(site.get('/for-you/news?news_range=all&news_q=Codex').text, 'html.parser')
    assert ids.isdisjoint(c['href'].split('/')[-1] for c in first.select('#news-releases article h3 a'))
    assert 'news_q=Codex' in soup.select_one('#news-releases nav a')['href']
    empty = BeautifulSoup(site.get('/for-you/news?news_range=all&news_q=no-such-record-xyz').text, 'html.parser')
    assert not empty.select('#news-releases article')
    assert '当前筛选没有匹配条目' in empty.select_one('#news-releases').text
    assert len(BeautifulSoup(site.get('/for-you/hot-cards').text, 'html.parser').select('#news-releases article')) == 3


def test_archive_date_basis_category_and_invalid_page():
    records = [dict(id=f'D-{n}', title='Agent news', summary='', name='Example', organization='Org',
                    event_date='2020-01-01', related=[{'id':'CW-A01','name':'Example'}],
                    publication={'updated_at':f'2020-01-{n:02d}T16:30:00Z'}) for n in range(1,13)]
    args = MultiDict({'news_range':'all','news_type':'agent','news_sort':'updated','news_page':'bad'})
    result = news_archive(records, args)
    assert result['total'] == 12 and result['page'] == 1
    assert result['items'][0]['id'] == 'D-12'
    args['news_type'] = 'model'
    assert not news_archive(records, args)['items']
