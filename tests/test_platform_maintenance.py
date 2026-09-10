"""Intake cannot silently modify public publications or accept stale AI drafts."""
import hashlib

import pytest

from test_knowledge import client, ADMIN, MCP
from backend.db import get_db
from backend.knowledge import platform, platform_maintenance as maintenance


def sample(body='A library for building AI agents. Requires Python 3.10. More source details.'):
    sid = maintenance.register('example/library', 'Example library', 'library')
    source = {'id': sid, 'url': 'https://github.com/example/library',
              'config': {'name': 'Example library', 'object_type': 'library'}}
    m = {'key': 'readme', 'url': source['url'] + '/blob/main/README.md', 'kind': 'readme', 'primary': True,
         'locator': 'README.md', 'body': body, 'hash': hashlib.sha256(body.encode()).hexdigest(), 'coverage': 'full_text'}
    maintenance.stage(source, [m])
    return source, m


def draft():
    job = maintenance.jobs()['items'][0]
    return {'schema_version': maintenance.SCHEMA, 'id': job['id'], 'fingerprint': job['fingerprint'],
        'base_token': job['base_token'], 'editor': 'Test editor', 'reason': 'Checked original material',
        'introduction': '用于构建 AI Agent 的程序库。', 'roles': [{'type': 'library', 'material': 'readme', 'quote': 'A library'}],
        'attention': [{'kind': 'editorial', 'material': 'readme', 'quote': 'building AI agents',
                       'explanation': '作者明确描述 Agent 构建能力。', 'observed_at': job['observed_at']}],
        'facts': {'capabilities': {'value': '构建 AI Agent', 'material': 'readme', 'quote': 'building AI agents'},
                  'limitations': {'status': 'unknown', 'value': None}}}


def test_review_is_dry_run_and_publish_is_atomic(client):
    sample(); data = draft()
    result = maintenance.apply(data)
    assert result['gate']['ready']
    assert platform.search()['total'] == 0
    assert maintenance.jobs()['items'][0]['base_token'] is None
    published = maintenance.apply(data, publish=True)
    assert published['selection']['state'] == 'published'
    assert platform.search()['total'] == 1 and not maintenance.jobs()['items']
    with pytest.raises(platform.PlatformError):
        maintenance.apply(data, publish=True)


def test_collection_keeps_published_material_until_review(client):
    source, m = sample(); maintenance.apply(draft(), publish=True)
    old = platform.search()['items'][0]
    assert maintenance.stage(source, [m]) == (1, 0)
    assert not maintenance.jobs()['items']
    m = {**m, 'body': m['body'] + ' Added new details.'}
    m['hash'] = hashlib.sha256(m['body'].encode()).hexdigest()
    assert maintenance.stage(source, [m]) == (1, 1)
    assert platform.get_object(old['object']['id'])['revision'] == old['revision']
    data = draft(); data['facts']['capabilities']['quote'] = 'invented quotation'
    with pytest.raises(ValueError):
        maintenance.apply(data, publish=True)
    assert platform.get_object(old['object']['id'])['revision'] == old['revision']
    assert maintenance.jobs()['items']


def test_superseded_and_concurrently_edited_drafts_rejected(client):
    source, m = sample(); data = draft()
    sample(m['body'] + ' New version.')
    with pytest.raises(platform.PlatformError, match='superseded'):
        maintenance.apply(data, publish=True)
    maintenance.apply(draft(), publish=True)
    sample(m['body'] + ' Next version.')
    data = draft(); rid = maintenance.jobs()['items'][0]['record_id']
    current = platform.preview(rid)
    current['profile']['introduction'] = 'A concurrent editor changed this.'
    platform.save_profile(rid, current['profile'], current['profile_revision'], 'Concurrent edit')
    with pytest.raises(platform.PlatformError, match='changed since export'):
        maintenance.apply(data, publish=True)


def test_reverted_upstream_content_is_a_new_job(client):
    source, m = sample(); maintenance.apply(draft(), publish=True)
    sample(m['body'] + ' New version.'); maintenance.apply(draft(), publish=True)
    assert maintenance.stage(source, [m]) == (1, 1)
    assert len(maintenance.jobs()['items']) == 1


def test_private_intake_and_public_mcp_scope(client):
    sample()
    assert client.get('/api/v1/admin/platform/intake').status_code == 401
    assert client.get('/api/v1/admin/platform/intake', headers=ADMIN).json['items']
    message = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}
    listing = client.post('/api/mcp/curated', json=message, headers=MCP).json['result']['tools']
    assert len(listing) == 10 and all(t['name'].startswith('curated_') for t in listing)
    assert client.post('/api/mcp', json=message, headers=MCP).json['result']['tools'] != listing
    message.update(method='tools/call', params={'name': 'task_context', 'arguments': {'goal': 'Run code'}})
    assert client.post('/api/mcp/curated', json=message, headers=MCP).json['result']['isError']


def test_failure_after_writes_rolls_back_and_keeps_publication(client):
    source,m = sample(); maintenance.apply(draft(), publish=True)
    before=platform.search()['items'][0]
    sample(m['body']+' Changed.')
    data=draft();data['roles'][0]['quote']='invented'
    with pytest.raises(ValueError): maintenance.apply(data,publish=True)
    assert platform.get_object(before['object']['id'])['revision']==before['revision']
    assert len(maintenance.jobs()['items'])==1


def test_optional_file_failure_does_not_remove_body_or_refresh_its_check(client):
    source,m=sample()
    license={**m,'key':'license','kind':'license','primary':False,'body':'License text'}
    license['hash']=hashlib.sha256(license['body'].encode()).hexdigest()
    maintenance.stage(source,[m,license])
    with get_db() as db:
        old=db.execute("SELECT checked_at FROM knowledge_platform_material_checks WHERE material_key='license'").fetchone()[0]
    assert maintenance.stage(source,[m],gaps=['License fetch failed'])==(1,0)
    assert len(maintenance.jobs()['items'][0]['materials'])==2
    with get_db() as db:
        assert db.execute("SELECT checked_at FROM knowledge_platform_material_checks WHERE material_key='license'").fetchone()[0]==old


def test_intake_reuses_legacy_identity_created_after_capture(client):
    from backend.knowledge import store
    source,m=sample()
    store.save_record({'kind':'resource','canonical_url':source['url'],'title':'Existing legacy identity'},record_id='legacy-123')
    data=draft()
    assert data['base_token']
    result=maintenance.apply(data,publish=True)
    assert result['object']['id']=='legacy-123'
    assert platform.search()['total']==1


def test_daily_update_preserves_existing_aliases_when_not_supplied(client):
    source, material = sample()
    first = draft(); first['aliases'] = ['OriginalAlias']
    maintenance.apply(first, publish=True)
    sample(material['body'] + ' Updated documentation.')
    maintenance.apply(draft(), publish=True)
    assert platform.search(q='OriginalAlias')['total'] == 1
