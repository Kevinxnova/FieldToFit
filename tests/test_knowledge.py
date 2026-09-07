"""End-to-end checks against isolated SQLite data; no live services or credentials."""
import json
import socket

import pytest

from backend.knowledge import store


@pytest.fixture
def client(tmp_path, monkeypatch):
    import backend.config as config
    import backend.db as database
    monkeypatch.setenv('PYTHON_DOTENV_DISABLED', '1')
    monkeypatch.setenv('ADMIN_PASSWORD', 'test-admin-password')
    monkeypatch.delenv('METIS_READ_TOKEN', raising=False)
    monkeypatch.delenv('METIS_PUBLIC_ACCOUNTS', raising=False)
    monkeypatch.setattr(config, 'DB_PATH', tmp_path / 'metis.db')
    monkeypatch.setattr(config, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(database, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(database, 'TURSO_URL', '')
    monkeypatch.setattr(database, 'TURSO_TOKEN', '')
    from backend.api.main import app
    database.init_db()
    app.config['TESTING'] = True
    return app.test_client()


def seed(title='PDF pipeline', suffix='one', **extra):
    return store.save_record({'kind': 'resource', 'canonical_url': f'https://example.org/{suffix}', 'title': title,
                              'summary': 'Local Python PDF processing library', 'source_id': 'manual', **extra})[0]


ADMIN = {'X-Admin-Password': 'test-admin-password'}
MCP = {'Accept': 'application/json, text/event-stream'}


def test_initialization_and_daily_sources(client):
    overview = client.get('/api/v1/overview').json
    assert overview['counts'] == {'event': 0, 'paper': 0, 'resource': 0}
    assert overview['verified'] == 0
    sources = client.get('/api/v1/sources').json['items']
    assert len(sources) == 17 and all(s['interval_days'] == 1 for s in sources)
    assert all(s['last_success_at'] is None for s in sources)


def test_production_frontend_links_and_metadata(client, tmp_path, monkeypatch):
    import backend.api.main as main
    dist = tmp_path / 'dist'; dist.mkdir()
    (dist / 'index.html').write_text('<html><head><title>Metis</title><meta name="description" content="Metis" /></head><body></body></html>')
    monkeypatch.setattr(main, 'CLIENT_DIST', dist)
    rid = seed(title=r'Paper <unsafe> \LaTeX', summary='A "quoted" description')
    page = client.get('/records/' + rid)
    assert page.status_code == 200 and '&lt;unsafe&gt;' in page.text and 'og:title' in page.text
    assert client.get('/apps').status_code == 200
    assert client.get('/api/not-a-real-endpoint').status_code == 404


def test_semantic_urls_and_versions_are_distinct(client):
    a = seed(suffix='paper?id=1')
    b = seed(suffix='paper?id=2')
    c = seed(suffix='paper?id=1&utm_source=feed')
    assert a != b and a == c
    assert store.canonical_url('https://github.com/owner/repo/releases/tag/v1') != store.canonical_url('https://github.com/owner/repo/releases/tag/v2')


def test_dedup_reuses_migrated_identity(client):
    data = {'kind': 'resource', 'canonical_url': 'https://github.com/example/project', 'title': 'Project'}
    first, _ = store.save_record(data, record_id='legacy-123')
    second, _ = store.save_record(data)
    assert first == second == 'legacy-123'


def test_pagination_and_publication_filters(client):
    seed(suffix='one', published_at='2026-09-01T00:00:00Z')
    seed(suffix='two', published_at='2026-09-02T00:00:00Z')
    seed(suffix='unknown')
    first = client.get('/api/v1/records?limit=1').json
    second = client.get('/api/v1/records?limit=1&offset=1').json
    assert first['total'] == 3 and first['next_offset'] == 1
    assert first['items'][0]['id'] != second['items'][0]['id']
    filtered = client.get('/api/v1/records?since=2026-09-02').json
    assert filtered['total'] == 1 and filtered['items'][0]['published_at'].startswith('2026-09-02')
    assert client.get('/api/v1/records?limit=101').status_code == 400
    assert client.get('/api/v1/records?kind=invalid').status_code == 400


def test_information_query_contains_papers_and_events(client):
    seed(kind='paper', suffix='paper')
    seed(kind='event', suffix='event')
    seed(suffix='tool')
    result = client.get('/api/v1/records?kind=information').json
    assert {i['kind'] for i in result['items']} == {'paper', 'event'}


def test_search_handles_chinese_and_literal_sql_characters(client):
    seed()
    assert client.get('/api/v1/records?q=本地%20PDF').json['total'] == 1
    assert client.get('/api/v1/records', query_string={'q': "%' OR 1=1 --"}).json['total'] == 0
    missing = client.post('/api/v1/task', json={'goal': 'zzzzneverexists'}).json
    assert missing['conclusion'] == 'not_found_in_scope'


def test_hard_constraints_keep_unknown_and_version_mismatch(client):
    rid = seed(version='v2', facts={'deployment': {'value': ['local'], 'status': 'documented', 'source_url': 'https://example.org/docs', 'version': 'v1', 'exhaustive': True}})
    matches = store.constraint_match(store.get_record(rid), {'deployment': 'local', 'cost': 'free'})
    assert [m['state'] for m in matches] == ['unknown', 'unknown']
    data = store.get_record(rid); data['facts']['deployment']['version'] = 'v2'; store.save_record(data, record_id=rid)
    assert store.constraint_match(store.get_record(rid), {'deployment': 'local'})[0]['state'] == 'satisfied'
    assert store.constraint_match(store.get_record(rid), {'deployment': 'cloud'})[0]['state'] == 'unmet'


def test_inferences_never_satisfy_hard_constraints(client):
    rid = seed(facts={'cost': {'value': 'free', 'status': 'inferred', 'source_url': 'https://example.org/docs'}})
    assert store.constraint_match(store.get_record(rid), {'cost': 'free'})[0]['state'] == 'unknown'


def test_corrections_sync_public_api_mcp_and_history(client):
    rid = seed()
    response = client.patch('/api/v1/admin/records/' + rid, json={'title': 'Corrected PDF pipeline', 'reason': 'Official documentation'}, headers=ADMIN)
    assert response.status_code == 200
    assert client.get('/api/v1/records/' + rid).json['title'] == 'Corrected PDF pipeline'
    mcp = client.post('/api/mcp', json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'get_record', 'arguments': {'id': rid}}}, headers=MCP).json
    assert mcp['result']['structuredContent']['title'] == 'Corrected PDF pipeline'
    assert len(mcp['result']['structuredContent']['history']) == 2


def test_withdrawn_record_and_material_are_not_readable(client):
    rid = seed(); eid = store.add_evidence(rid, 'https://example.org/docs', 'Docs', 'Text')
    client.patch('/api/v1/admin/records/' + rid, json={'status': 'withdrawn', 'reason': 'Source withdrawn'}, headers=ADMIN)
    assert client.get('/api/v1/records/' + rid).status_code == 404
    assert client.get('/api/v1/records').json['total'] == 0
    assert client.get('/api/v1/evidence/' + eid).status_code == 400
    assert client.get('/api/v1/records/' + rid + '/export').status_code == 404
    assert all('title' not in x['snapshot'] for x in client.get('/api/v1/changes').json['items'])


def test_new_evidence_appears_in_incremental_updates(client):
    rid = seed()
    cursor = store.changes()['next_cursor']
    eid = store.add_evidence(rid, 'https://example.org/docs', 'Docs', 'Body')
    update = store.changes(after=cursor)['items']
    assert len(update) == 1 and update[0]['snapshot']['evidence_id'] == eid
    store.add_evidence(rid, 'https://example.org/docs', 'Docs', 'Body')
    assert len(store.changes(after=cursor)['items']) == 1


def test_evidence_paging_and_export_provenance(client):
    rid = seed()
    eid = store.add_evidence(rid, 'https://example.org/docs', 'Docs', 'abcdefghij', locator='Section 2', version='v1', coverage='excerpt')
    first = client.get('/api/v1/evidence/' + eid + '?limit=4').json
    assert first['body'] == 'abcd' and first['next_offset'] == 4 and first['truncated']
    last = client.get('/api/v1/evidence/' + eid + '?offset=8&limit=4').json
    assert last['body'] == 'ij' and last['next_offset'] is None
    exported = client.get('/api/v1/records/' + rid + '/export').text
    assert 'https://example.org/docs' in exported and 'excerpt' in exported and 'Section 2' in exported
    citation = client.get('/api/v1/records/' + rid + '/export?format=bibtex').text
    assert 'doi =' not in citation and 'author =' not in citation


def test_change_cursor_does_not_drop_same_time_records(client):
    for i in range(4):
        seed(suffix=str(i))
    seen, cursor = [], 0
    while True:
        page = client.get(f'/api/v1/changes?after={cursor}&limit=2').json
        seen.extend(x['record_id'] for x in page['items']); cursor = page['next_cursor']
        if not page['has_more']:
            break
    assert len(seen) == len(set(seen)) == 4


def test_rechecking_same_facts_does_not_fabricate_changes(client):
    data = {'kind': 'resource', 'canonical_url': 'https://example.org/one', 'title': 'PDF',
            'facts': {'license': {'value': 'MIT', 'status': 'documented', 'source_url': 'https://example.org/license', 'checked_at': '2026-09-01'}}}
    rid, _ = store.save_record(data)
    data['facts']['license']['checked_at'] = '2026-09-02'
    _, changed = store.save_record(data)
    assert not changed and len(store.get_record(rid)['history']) == 1


def test_daily_source_claim_and_error_status(client, monkeypatch):
    from backend.knowledge import sources
    calls = []
    def collect(source):
        calls.append(source['id'])
        if source['id'] == 'hf-models':
            raise ValueError('Unavailable')
        return 3, 2
    monkeypatch.setattr(sources, 'collect_source', collect)
    result = sources.run_daily(source_id='arxiv')
    assert result['status'] == 'success'
    sources.run_daily(source_id='arxiv')
    assert calls == ['arxiv']
    failed = sources.run_daily(source_id='hf-models')
    assert failed['status'] == 'partial'
    source = next(s for s in sources.list_sources() if s['id'] == 'hf-models')
    assert source['last_success_at'] is None and source['status'] == 'error'
    assert client.patch('/api/v1/admin/sources/arxiv', json={'interval_days': 0}, headers=ADMIN).status_code == 400


def test_read_token_cannot_mutate_or_administer(client, monkeypatch):
    monkeypatch.setenv('METIS_READ_TOKEN', 'private-read-token')
    assert client.get('/api/v1/records').status_code == 401
    headers = {'Authorization': 'Bearer private-read-token'}
    assert client.get('/api/v1/records', headers=headers).status_code == 200
    assert client.post('/api/v1/admin/records', json={}, headers=headers).status_code == 401
    assert client.get('/api/v1/admin/sources', headers=headers).status_code == 401


def test_mcp_protocol_and_readonly_discovery(client):
    assert client.get('/api/mcp').status_code == 405
    assert client.post('/api/mcp', json={}).status_code == 406
    assert client.post('/api/mcp', json={}, headers={**MCP, 'Origin': 'https://malicious.example'}).status_code == 403
    assert client.post('/api/mcp', json={}, headers={**MCP, 'Origin': 'http://malicious.example', 'Host': 'malicious.example'}).status_code == 403
    assert client.post('/api/v1/task', json={'goal': 'PDF'}, headers={'Origin': 'http://127.0.0.1:5173'}).status_code == 200
    init = client.post('/api/mcp', json={'jsonrpc': '2.0', 'id': 0, 'method': 'initialize', 'params': {'protocolVersion': '2025-11-25'}}, headers=MCP)
    assert init.json['result']['protocolVersion'] == '2025-11-25'
    notice = client.post('/api/mcp', json={'jsonrpc': '2.0', 'method': 'notifications/initialized'}, headers=MCP)
    assert notice.status_code == 202 and notice.data == b''
    listing = client.post('/api/mcp', json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}, headers=MCP).json
    assert all(t['annotations']['readOnlyHint'] for t in listing['result']['tools'])
    invalid = client.post('/api/mcp', json={'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': 'delete_all', 'arguments': {}}}, headers=MCP).json
    assert invalid['result']['isError']
    invalid = client.post('/api/mcp', json={'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {'name': 'search', 'arguments': {'limit': 'bad'}}}, headers=MCP).json
    assert invalid['result']['isError']


def test_verification_has_scoped_version(client):
    rid = seed(version='v1')
    data = {'title': 'Minimal check', 'method': 'Manual', 'environment': 'Python 3.13', 'steps': 'Read one sample', 'expected': 'One parsed field', 'result': 'passed', 'output': 'Field matched', 'limitations': 'Only one fixture'}
    response = client.post(f'/api/v1/admin/records/{rid}/verify', json=data, headers=ADMIN)
    assert response.status_code == 201
    assert store.get_record(rid)['verification_status'] == 'passed'
    client.patch('/api/v1/admin/records/' + rid, json={'version': 'v2', 'reason': 'New release'}, headers=ADMIN)
    assert store.get_record(rid)['verification_status'] == 'not_verified'
    assert len(client.get('/api/v1/cases').json['items']) == 1


def test_accounts_isolate_collections(client, monkeypatch):
    monkeypatch.setenv('METIS_PUBLIC_ACCOUNTS', '1')
    rid = seed()
    first = client.post('/api/v1/account/register', json={'username': 'alice', 'password': 'long-test-password'})
    assert first.status_code == 200 and 'HttpOnly' in first.headers['Set-Cookie']
    assert client.post('/api/v1/collection', json={'record_id': rid, 'action': 'save'}).status_code == 200
    assert len(client.get('/api/v1/collection').json['items']) == 1
    client.post('/api/v1/account/logout', json={})
    assert client.get('/api/v1/collection').status_code == 401
    client.post('/api/v1/account/register', json={'username': 'bob', 'password': 'long-test-password'})
    assert client.get('/api/v1/collection').json['items'] == []
    assert client.post('/api/v1/collection', json={'record_id': rid, 'action': 'save'}, headers={'Origin': 'https://malicious.example'}).status_code == 403


def test_feedback_and_invalid_inputs(client):
    assert client.post('/api/v1/feedback', json={'content': 'A real use case', 'category': 'use_case'}).status_code == 201
    assert client.post('/api/v1/feedback', json={'content': 'x' * 2001}).status_code == 400
    assert client.post('/api/v1/task', json=[]).status_code == 400
    assert client.post('/api/v1/compare', json={'ids': []}).status_code == 400
    assert client.post('/api/v1/task', json={'goal': 'PDF', 'constraints': {'invented': True}}).status_code == 400


@pytest.mark.parametrize('ip', ['127.0.0.1', '10.0.0.1', '169.254.169.254', '::1', '192.168.1.5'])
def test_source_fetch_rejects_private_addresses(monkeypatch, ip):
    from backend.knowledge.sources import public_url
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *args, **kwargs: [(2, 1, 6, '', (ip, 443))])
    with pytest.raises(ValueError):
        public_url('https://example.org/document')


@pytest.mark.parametrize('kind', ['researcher', 'engineer', 'graduate', 'student'])
def test_all_personas_can_retrieve_task_context(client, kind):
    seed()
    result = client.post('/api/v1/task', json={'goal': 'PDF processing', 'persona': kind}).json
    assert result['persona'] == kind and len(result['candidates']) == 1
    assert result['ai_generated'] is False
    assert {p['path'] for p in result['paths']} == {'use', 'extend', 'build', 'mixed'}
