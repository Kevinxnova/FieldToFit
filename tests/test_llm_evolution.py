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


def test_atlas_evidence_relations_and_historical_dates():
    nodes = {n['id']: n for r in CATALOG['routes'] for n in r['nodes']}
    tracks = {n['id']: r['track'] for r in CATALOG['routes'] for n in r['nodes']}
    assert len(nodes) >= 90
    assert all(sum(n['date'] >= '2025' for r in CATALOG['routes'] if r['track'] == track for n in r['nodes']) >= 7
               for track in ('train', 'inference', 'systems'))
    for node in nodes.values():
        assert node['kind'] in ('method', 'model', 'engineering')
        assert isinstance(node['highlight'], bool)
        for field in ('problem','mechanism','evidence','limit'):
            assert len(node[field]) == 2 and all(node[field])
        assert node['references'] and node['references'][0]['source'] == node['source']
        for ref in node['references']:
            assert ref['source'] in CATALOG['sources']
            assert len(ref['section']) == 2 and all(ref['section'])
    for route in CATALOG['routes']:
        for case in route['cases']:
            assert set(case['nodes']) <= {n['id'] for n in route['nodes']}
    assert len({e['id'] for e in CATALOG['relations']}) == len(CATALOG['relations'])
    assert {e['kind'] for e in CATALOG['relations']} == {'improvement','alternative','combination','adoption','cross-track'}
    for edge in CATALOG['relations']:
        assert edge['from_node'] in nodes and edge['to_node'] in nodes
        assert edge['from_node'] != edge['to_node']
        assert len(edge['reason']) == 2 and all(edge['reason'])
        assert edge['sources'] and all(s in CATALOG['sources'] for s in edge['sources'])
        if edge['kind'] in ('improvement','adoption'):
            assert nodes[edge['from_node']]['date'] <= nodes[edge['to_node']]['date']
        if edge['kind'] == 'cross-track':
            assert tracks[edge['from_node']] != tracks[edge['to_node']]
    # First-publication dates must not drift to a later revision or adoption.
    assert nodes['repr-mhc']['date'] == '2025-12-31'
    assert nodes['latent-v2']['date'] == '2024-05-07'
    assert nodes['system-areal']['date'] == '2025-05-30'
    assert CATALOG['sources']['areal']['revised_at'] == '2026-03-02'
    assert nodes['system-deepep']['date'] == '2025'
    assert nodes['repr-v4']['date_kind'] == 'model-adoption'
    assert any(r['source']=='v4' for r in nodes['repr-v4']['references'])


def test_original_links_and_read_versions_are_preserved():
    import hashlib
    import json
    nodes = {n['id'] for r in CATALOG['routes'] for n in r['nodes']}
    legacy = '''dense-transformer dense-scaling dense-chinchilla moe-switch moe-v3 moe-qwen
    preference-instruct preference-dpo reasoning_rl-o1 reasoning_rl-r1_paper shared_kv-mqa
    shared_kv-gqa_paper latent_kv-v3 draft_verify-spec_paper draft_verify-speculative
    thinking-testtime thinking-claude thinking-qwen long_context-rope long_context-lost
    quantization-awq sharding-zero_paper sharding-zero model_parallel-megatron
    model_parallel-parallel kernels-flash kv_paging-paged batching-orca
    disaggregation-distserve disaggregation-dynamo disaggregation-epd'''.split()
    assert set(legacy) <= nodes
    # This batch does not revise the 18 articles or invalidate existing reading records.
    assert hashlib.sha256(json.dumps(CATALOG['questions'], sort_keys=True, ensure_ascii=False).encode()).hexdigest() == '74c67e2c92c399bd7c0f3cad17669ba2f06ffcecaf6faef9c753889cc22c6fb5'


@pytest.mark.parametrize('english', [False, True])
def test_atlas_server_body_contains_each_node_and_relation(site, english):
    body = site.get(('/en' if english else '')+ROOT).text
    i = int(english)
    for route in CATALOG['routes']:
        for node in route['nodes']:
            assert 'id="node-'+node['id']+'"' in body
            for key in ('title','problem','mechanism','limit'):
                assert html.escape(node[key] if key=='title' else node[key][i]) in body
            for ref in node['references']:
                assert html.escape(CATALOG['sources'][ref['source']]['url']) in body
    for edge in CATALOG['relations']:
        assert html.escape(edge['reason'][i]) in body


def test_complete_atlas_definitions_and_summaries(site):
    for track in CATALOG['tracks']:
        assert len(track['definition']) == 2 and all(track['definition'])
    nodes = [node for route in CATALOG['routes'] for node in route['nodes']]
    assert len(nodes) >= 93
    for node in nodes:
        assert len(node['summary']['technology']) == 2 and all(node['summary']['technology'])
        assert node['summary']['representative'].strip()
    for index, prefix in enumerate(('', '/en')):
        page = site.get(prefix + ROOT).text
        for track in CATALOG['tracks']:
            assert html.escape(track['definition'][index]) in page
        for node in nodes:
            assert html.escape(node['summary']['technology'][index]) in page
            assert html.escape(node['summary']['representative']) in page


@pytest.mark.parametrize('prefix,index', [('',0),('/en',1)])
def test_home_curated_milestones_match_shared_preview(site, prefix, index):
    from backend.llm_evolution import HOME_PREVIEW, NODE_BY_ID
    text = site.get(prefix+'/for-you').text
    section = text.split('<section id="llm-evolution">',1)[1].split('<section id="news-codex-28-days">',1)[0]
    selected = [entry['id'] for entries in HOME_PREVIEW.values() for entry in entries]
    assert len(set(selected)) >= 21
    assert all(len(entries) == len({e['id'] for e in entries}) for entries in HOME_PREVIEW.values())
    for track, entries in HOME_PREVIEW.items():
        for entry in entries:
            node = NODE_BY_ID[entry['id']]
            assert any(node in r['nodes'] for r in CATALOG['routes'] if r['track']==track) or any(e['node']==node['id'] and e['track']==track for e in CATALOG['flagships']['adoptions'])
            assert 'node='+entry['id'] in section
            assert html.escape(node['summary']['technology'][index]) in section
            assert html.escape(node['summary']['representative']) in section
    assert 'node=dense-llama' not in section  # Old automatically selected route endpoint.
    assert QUESTIONS in section


def test_flagship_identity_adoption_and_unknown_boundaries():
    nodes = {n['id'] for r in CATALOG['routes'] for n in r['nodes']}
    f = CATALOG['flagships']; models = {m['id']: m for m in f['models']}
    assert len(models) == len(f['models']) == 25
    assert len(f['scope']) == len(set(m['company'] for m in models.values())) == 15
    assert {'openai','anthropic','google','zai','baidu','tencent','huawei'} <= set(f['scope'])
    assert len({e['id'] for e in f['adoptions']}) == len(f['adoptions'])
    for m in models.values():
        assert m['source'] in CATALOG['sources']
        assert set(m['gaps']) == {'train','inference','systems'}
        assert all(len(m[k])==2 and all(m[k]) for k in ('role','status','notes','date_kind'))
        assert m['checked_at'] == f['checked_at']
    for edge in f['adoptions']:
        assert edge['model'] in models and edge['node'] in nodes
        assert edge['source'] in CATALOG['sources'] and edge['reading']=='body'
        assert edge['track'] in ('train','inference','systems')
        assert all(len(edge[k])==2 and all(edge[k]) for k in ('statement','boundary','section'))
    # No extrapolation to the undisclosed successor, API deployment or unresolved flagship.
    assert not any(e['model'] in ('minimax31','qwen38-max','pangu') for e in f['adoptions'])
    assert not any(e['node']=='think-cot' and e['model'].startswith('gpt') for e in f['adoptions'])
    assert any(e['model']=='opus55' and e['track']=='train' for e in f['adoptions'])
    assert models['mistral4']['status'][1]=='Public preview'


@pytest.mark.parametrize('prefix,index', [('',0),('/en',1)])
def test_flagships_same_sources_in_home_full_and_api(site,prefix,index):
    f=CATALOG['flagships']
    assert site.get('/api/v1/platform/evolution').json['flagships']==f
    for path in ('/for-you',ROOT):
        body=site.get(prefix+path).text
        for m in f['models']:
            assert html.escape(m['name']) in body and html.escape(m['notes'][index]) in body
            assert 'evolution_models='+m['id'] in body
        for e in f['adoptions']:
            assert html.escape(e['statement'][index]) in body
            assert html.escape(CATALOG['sources'][e['source']]['url']) in body
