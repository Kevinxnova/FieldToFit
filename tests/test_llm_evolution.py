"""The LLM topic is one bilingual catalog, with no writes or database migration."""
import html
from collections import Counter
import pytest
from test_knowledge import client
from test_search_pages import site, urls
from backend.llm_evolution import CATALOG, ROOT, QUESTIONS


def test_catalog_relations_and_editorial_contract():
    questions = {q['id']: q for q in CATALOG['questions']}
    assert Counter(q['track'] for q in questions.values()) == {'train': 6, 'inference': 6, 'systems': 6}
    assert len(questions) == len(CATALOG['questions']) == 18
    routes = {r['id']: r for r in CATALOG['routes']}
    nodes = [n for r in routes.values() for n in r['nodes']]
    assert len({n['id'] for n in nodes}) == len(nodes)
    assert min(n['date'] for n in nodes).startswith('2017')
    assert max(n['date'] for n in nodes).startswith('2026')
    for q in questions.values():
        assert any(n['question'] == q['id'] for n in routes[q['route']]['nodes'])
        assert q['revision'] > 0
        for key in ('title', 'goal', 'problem', 'mechanism', 'example', 'limit', 'change_reason'):
            assert len(q[key]) == 2 and all(isinstance(s,str) and s.strip() for s in q[key])
        assert q['formula'] and q['figure']['labels'] and q['sources']
        assert all(id in questions and id != q['id'] for id in q['related'])
        assert all(id in CATALOG['sources'] for id in q['sources'])
    for route in routes.values():
        assert route['group'] in CATALOG['groups']
        assert route['nodes'] == sorted(route['nodes'], key=lambda n:n['date'])
        for n in route['nodes']:
            assert len(n['mechanism']) == len(n['evidence']) == 2
            assert n['question'] in questions
            assert n['date'] == CATALOG['sources'][n['source']]['date']
            assert n['relation'] == 'related-development'
        for c in route['cases']:
            assert c['company'] in CATALOG['companies'] or c['company'] == 'research'
            assert c['source'] in CATALOG['sources'] and len(c['evidence']) == 2
            assert c['relation'] == 'documented-use'
    assert len([r for r in routes.values() if any(c['company']=='alibaba' for c in r['cases'])]) >= 3
    assert all(s['url'].startswith('https://') and s['checked_at'] for s in CATALOG['sources'].values())


def test_readonly_catalog_and_conditional_fetch(client):
    response = client.get('/api/v1/platform/evolution')
    assert response.status_code == 200 and response.json == CATALOG
    assert client.get('/api/v1/platform/evolution', headers={'If-None-Match':response.headers['ETag']}).status_code == 304
    assert client.post('/api/v1/platform/evolution', json={}).status_code == 405
    for q in CATALOG['questions']:
        response = client.get('/api/v1/platform/evolution/questions/'+q['id'])
        assert response.json['question'] == q
        assert set(response.json['sources']) == set(q['sources'])
    assert client.get('/api/v1/platform/evolution/questions/T99').status_code == 404


@pytest.mark.parametrize('english', [False, True])
def test_every_question_has_server_rendered_content_and_canonical(site,english):
    index=int(english); prefix='/en' if english else ''
    for q in CATALOG['questions']:
        path=prefix+QUESTIONS+'/'+q['id']; response=site.get(path)
        assert response.status_code == 200
        for key in ('title','goal','problem','mechanism','example','limit'):
            assert html.escape(q[key][index]) in response.text
        assert html.escape(q['formula']) in response.text
        assert response.text.count('rel="canonical"') == 1
        assert 'https://fieldtofit.top'+path in response.text
        assert all(CATALOG['sources'][s]['url'] in response.text for s in q['sources'])
    assert site.get(prefix+QUESTIONS+'/T99').status_code == 404
    assert site.get(prefix+ROOT+'/unknown').status_code == 404
    assert site.get(prefix+ROOT+'/').status_code == 308


def test_home_position_maps_directory_and_sitemap(site):
    text=site.get('/for-you').text
    assert text.index('id="technical-evolution-maps"') < text.index('id="llm-evolution"') < text.index('id="news-codex-28-days"')
    for lang in ('','/en'):
        assert site.get(lang+ROOT).status_code == 200
        directory=site.get(lang+QUESTIONS).text
        assert all(QUESTIONS+'/'+q['id'] in directory for q in CATALOG['questions'])
    sitemap=urls(site)
    assert all('https://fieldtofit.top'+QUESTIONS+'/'+q['id'] in sitemap for q in CATALOG['questions'])
    assert site.get('/maps').status_code == 200
    assert site.get('/api/v1/platform/reading?view=home').status_code == 200


def test_topic_respects_read_access(client, monkeypatch):
    monkeypatch.setenv('FIELDTOFIT_READ_TOKEN','topic-test-token')
    assert client.get('/api/v1/platform/evolution').status_code == 401
    assert client.get(ROOT).status_code == 401
