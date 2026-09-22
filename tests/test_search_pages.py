"""Search HTML, publication boundaries and metadata; isolated SQLite, no search submissions."""
import copy
import html
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
from test_knowledge import client
from test_content_workspace import migrate, make, valid, publish, call
from backend.db import get_db
from backend import seo


@pytest.fixture
def site(client, tmp_path, monkeypatch):
    import backend.api.main as main
    dist = tmp_path / 'dist'
    dist.mkdir()
    (dist / 'index.html').write_text(Path('frontend/index.html').read_text())
    monkeypatch.setattr(main, 'CLIENT_DIST', dist)
    monkeypatch.delenv('VERCEL_ENV', raising=False)
    return client


def get(site, path):
    return site.get(path, base_url=seo.ORIGIN)


def urls(site):
    response = get(site, '/sitemap.xml')
    assert response.status_code == 200
    assert response.mimetype == 'application/xml'
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    root = ET.fromstring(response.data)
    return {node.find('s:loc', ns).text: node.findtext('s:lastmod', namespaces=ns) for node in root}


@pytest.mark.parametrize('path', seo.PAGES)
def test_main_copy_and_one_canonical(site, path):
    response = get(site, path)
    assert response.status_code == 200
    copy = seo.PAGES[path]
    assert '<h1>' + html.escape(copy['heading'][0]) + '</h1>' in response.text
    assert html.escape(copy['description'][0]) in response.text
    assert response.text.count('rel="canonical"') == 1
    assert response.text.count('property="og:title"') == 1
    assert '<title>' + copy['title'][0] + '</title>' in response.text
    assert f'href="{seo.ORIGIN}{path}"' in response.text
    assert 'X-Robots-Tag' not in response.headers
    assert response.headers['Cache-Control'] == 'no-store'


@pytest.mark.parametrize('kind', ['news', 'watch'])
def test_every_published_detail_html_matches_public_api(site, kind):
    collection = site.get('/api/v1/platform/'+kind).json
    for item in collection['items']:
        response = get(site, seo.detail_url(item['id']))
        assert response.status_code == 200, item['id']
        assert f'data-public-revision="{collection["revision"]}"' in response.text
        assert html.escape(item.get('title', item['name'])) in response.text
        assert html.escape(item.get('summary', item.get('introduction', ''))) in response.text
        for point in item['interpretation']:
            assert html.escape(point['title']) in response.text
            assert str(seo.inline(point['text'])) in response.text
        for block in item.get('blocks', []):
            for text in ([block['text']] if block['kind']=='paragraph' else [cell for row in block['rows'] for cell in row]):
                assert str(seo.inline(text)) in response.text
        for source in item['sources']:
            assert html.escape(source['url'], quote=True) in response.text


def test_sitemap_exact_public_set_and_real_dates(site):
    expected = {seo.ORIGIN+p for p in seo.PAGES}
    for kind in ('news', 'watch'):
        expected.update(seo.ORIGIN+seo.detail_url(item['id']) for item in site.get('/api/v1/platform/'+kind).json['items'])
    actual = urls(site)
    assert set(actual) == expected
    assert all(date is None for date in actual.values())  # seed review dates aren't modification dates
    assert all(get(site, url.removeprefix(seo.ORIGIN)).status_code == 200 for url in actual)
    migrate(site)
    assert urls(site) == actual  # importing unchanged content doesn't manufacture freshness


@pytest.mark.parametrize('kind', ['news', 'watch'])
def test_draft_publish_edit_withdraw_no_cached_body(site, kind):
    migrate(site)
    ident, _ = make(site, kind)
    draft = valid(site, kind, ident)
    path = seo.detail_url(ident)
    assert get(site, path).status_code == 404
    assert seo.ORIGIN+path not in urls(site)
    publish(site, kind, ident)
    assert get(site, path).status_code == 200
    date = urls(site)[seo.ORIGIN+path]
    assert date and 'T' in date
    publish(site, kind, ident)
    assert urls(site)[seo.ORIGIN+path] == date  # no-op publication is not a content update
    draft = call(site, f'/content/{kind}/{ident}', method='get').json
    draft['draft']['title' if kind == 'news' else 'name'] = 'UNPUBLISHED-SECRET'
    assert call(site, f'/content/{kind}/{ident}', draft, 'patch').status_code == 200
    assert 'UNPUBLISHED-SECRET' not in get(site, path).text
    assert 'INTERNAL-SECRET' not in get(site, path).text
    assert urls(site)[seo.ORIGIN+path] == date
    publish(site, kind, ident)
    assert 'UNPUBLISHED-SECRET' in get(site, path).text
    d = call(site, f'/content/{kind}/{ident}', method='get').json
    response = call(site, f'/content/{kind}/{ident}/withdraw', {'draft_version':d['draft_version'], 'reason':'isolation test', 'confirmed':True})
    assert response.status_code == 200, response.json
    page = get(site, path)
    assert page.status_code == 404 and 'UNPUBLISHED-SECRET' not in page.text
    assert seo.ORIGIN+path not in urls(site)
    assert '<script ' not in page.text and page.headers['Cache-Control'] == 'no-store'


def test_merge_redirect_checks_public_destination(site):
    migrate(site)
    with get_db() as db:
        db.execute('INSERT INTO fieldtofit_steward_aliases VALUES(?,?,?)', ('D-999','D-01','test'))
    response = get(site, '/news/D-999')
    assert response.status_code == 308 and response.headers['Location'] == '/news/D-01'
    assert response.headers['Cache-Control'] == 'no-store'
    with get_db() as db:
        row = db.execute("SELECT published_json FROM fieldtofit_content_sets WHERE kind='news'").fetchone()
        data = json.loads(row[0])
        next(i for i in data['items'] if i['id']=='D-01')['state'] = 'withdrawn'
        db.execute("UPDATE fieldtofit_content_sets SET published_json=? WHERE kind='news'", (json.dumps(data),))
    response = get(site, '/news/D-999')
    assert response.status_code == 404 and 'Location' not in response.headers


def test_robots_preview_errors_and_private_routes(site, monkeypatch):
    r = get(site, '/robots.txt')
    assert r.mimetype == 'text/plain' and 'Sitemap: '+seo.ORIGIN+'/sitemap.xml' in r.text
    assert 'Disallow:' not in r.text  # crawlers must be able to read noindex headers
    assert get(site, '/api/v1/platform/news').headers['X-Robots-Tag'] == 'noindex'
    for path in ('/admin', '/collection', '/account', '/feedback'):
        response = get(site, path)
        assert response.status_code == 200 and response.headers['X-Robots-Tag'] == 'noindex'
    for path in ('/news/D-9999', '/watch/CW-M9999', '/unknown', '/news/bad'):
        response = get(site, path)
        assert response.status_code == 404 and response.headers['X-Robots-Tag'] == 'noindex'
    assert get(site, '/api/v1/admin/workspace/status').status_code == 401
    assert get(site, '/api/v1/platform/news').headers['Cache-Control'] == 'no-store'
    monkeypatch.setenv('VERCEL_ENV', 'preview')
    assert 'Disallow: /\n' in get(site, '/robots.txt').text
    assert 'noindex' in get(site, '/for-you').headers['X-Robots-Tag']
    assert 'name="robots" content="noindex"' in get(site, '/for-you').text


def test_redirects_query_canonical_and_failure(site, monkeypatch):
    response = get(site, '/?utm_source=demo')
    assert response.status_code == 308 and response.headers['Location'] == '/for-you?utm_source=demo'
    assert get(site, '/connect').headers['Location'] == '/for-your-ai'
    assert get(site, '/for-you?object=legacy').headers['X-Robots-Tag'] == 'noindex'
    assert get(site, '/news/D-01/').headers['Location'] == '/news/D-01'
    assert f'rel="canonical" href="{seo.ORIGIN}/for-you"' in get(site, '/for-you?q=test').text
    def broken(*args, **kwargs):
        raise RuntimeError('SECRET database credentials')
    monkeypatch.setattr(seo, 'news', broken)
    for path in ('/for-you', '/news/D-01', '/sitemap.xml'):
        response = get(site, path)
        assert response.status_code == 503 and 'SECRET' not in response.text
        assert response.headers['Cache-Control'] == 'no-store'


def test_escaped_markup_and_metadata(site, monkeypatch):
    data = copy.deepcopy(site.get('/api/v1/platform/news?id=D-01').json)
    data['items'][0].update(title='Title <script>alert(1)</script>', summary='"/><script>unsafe</script>')
    monkeypatch.setattr(seo, 'news', lambda **kw: data)
    response = get(site, '/news/D-01')
    assert response.status_code == 200 and '<script>alert(1)' not in response.text
    assert '&lt;script&gt;alert(1)' in response.text
    assert '<a' not in str(seo.inline('[bad](javascript:alert)'))
    assert '<img' not in str(seo.inline('<img src=x> **<script>**'))
