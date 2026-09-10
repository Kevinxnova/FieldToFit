"""Publication boundaries with isolated real SQLite transactions and HTTP/MCP reads."""
import hashlib
import sqlite3
from contextlib import contextmanager

import pytest

from test_knowledge import client, seed, ADMIN, MCP
from backend.knowledge import platform, store


def example(suffix='curated', version='v1'):
    url = 'https://example.org/' + suffix + '/README.md'
    body = 'An agent harness with tools. Requires a tool-calling model.\n' + 'Source detail. ' * 80
    rid = seed('Harness example', suffix=suffix, version=version, object_type='harness', topics=[], facts={
        'capabilities': {'value': 'Tool use', 'status': 'official_claim', 'source_url': url, 'version': version, 'quote': 'An agent harness with tools.'},
        'limitations': {'value': 'Tool-calling model required', 'status': 'documented', 'source_url': url, 'version': version, 'quote': 'Requires a tool-calling model.'},
    })
    eid = store.add_evidence(rid, url, 'README', body, 'README.md', version, 'documented', 'full_text')
    profile = {'introduction': 'An agent harness with documented model requirements.', 'aliases': ['Harness alias'],
               'roles': [{'type': 'harness', 'evidence_id': eid, 'quote': 'An agent harness with tools.'}],
               'attention': [{'kind': 'editorial', 'explanation': 'Documents a harness with tools and explicit model requirements.',
                              'evidence_id': eid, 'quote': 'Requires a tool-calling model.', 'observed_at': store.now()}],
               'materials': [{'evidence_id': eid, 'kind': 'readme', 'primary': True, 'note': 'Text only; not executed'}]}
    return rid, eid, profile, body


def publish(rid, profile):
    draft = platform.save_profile(rid, profile, platform.preview(rid)['profile_revision'], 'Source checked')
    review = platform.transition(rid, 'review', draft['review_token'], 'Ready for review')
    return platform.transition(rid, 'published', review['review_token'], 'Checked introduction and original citations')


def test_collection_is_not_curated_and_upgrade_is_idempotent(client):
    seed()
    store.init_knowledge()
    store.init_knowledge()
    assert client.get('/api/v1/records').json['total'] == 1
    assert client.get('/api/v1/platform/objects').json['total'] == 0


def test_publication_gate_and_state_transitions(client):
    rid = seed()
    draft = platform.preview(rid)
    assert not draft['gate']['ready']
    assert len(draft['gate']['errors']) >= 5
    with pytest.raises(platform.PlatformError, match='Submit for review'):
        platform.transition(rid, 'published', draft['review_token'], 'Premature')
    review = platform.transition(rid, 'review', draft['review_token'], 'Inspect missing materials')
    with pytest.raises(platform.PlatformError) as err:
        platform.transition(rid, 'published', review['review_token'], 'Still missing')
    assert err.value.status == 422
    assert platform.search()['total'] == 0


def test_api_mcp_and_export_share_a_reviewed_revision(client):
    rid, eid, profile, body = example()
    published = publish(rid, profile)
    assert published['gate']['ready']
    pub = client.get('/api/v1/platform/objects/' + rid).json
    assert pub['object'] == published['object']
    assert pub['object']['types'] == ['harness'] and not pub['object']['upstream_version'] is None
    search = client.get('/api/v1/platform/objects?q=alias&object_type=harness').json
    assert search['total'] == 1
    mcp = client.post('/api/mcp', headers=MCP, json={'jsonrpc':'2.0','id':1,'method':'tools/call',
        'params':{'name':'curated_object','arguments':{'id':rid}}}).json['result']
    assert not mcp['isError'] and mcp['structuredContent'] == pub
    exported = client.get('/api/v1/platform/objects/' + rid + '/export?format=json').json
    assert exported['object'] == pub['object'] and exported['revision'] == pub['revision']
    assert 'README.md' in exported['markdown'] and 'no task plan' in exported['markdown']
    assert exported['requires_service_for_full_text']
    assert client.get('/api/v1/platform/objects/' + rid + '/export?format=invalid').status_code == 400


def test_text_continuation_is_exact_and_declared_links_are_honest(client):
    rid, eid, profile, original = example()
    link = store.add_evidence(rid, 'https://example.org/api', 'API docs', coverage='link_only', version='v1')
    profile['materials'].append({'evidence_id':link,'kind':'api','note':'Only a link; not downloaded'})
    publish(rid, profile)
    publication = platform.get_object(rid)
    offset, chunks = 0, []
    while True:
        result = platform.read_material(rid, eid, publication['revision'], offset, 113)
        chunks.append(result['body'])
        assert result['material']['content_hash'] == hashlib.sha256(original.encode()).hexdigest()
        if not result['has_more']:
            break
        offset = result['next_offset']
    assert ''.join(chunks) == original
    empty = platform.read_material(rid, link)
    assert empty['material']['coverage'] == 'link_only' and empty['body'] == '' and not empty['has_more']
    assert client.get(f'/api/v1/platform/objects/{rid}/materials/{eid}?offset=99999').status_code == 400


def test_source_changes_remove_current_selection_but_preserve_reviewed_history(client):
    rid, eid, profile, body = example()
    publish(rid, profile)
    old = platform.get_object(rid)
    record = store.get_record(rid)
    record['checked_at'] = store.now()
    store.save_record(record, record_id=rid)
    assert platform.preview(rid)['selection']['state'] == 'published'  # check-only is not a content update
    record['title'] = 'Changed object'
    store.save_record(record, record_id=rid)
    assert platform.preview(rid)['selection']['state'] == 'needs_review'
    assert platform.search()['total'] == 0
    assert client.get('/api/v1/platform/objects/' + rid).status_code == 404
    assert platform.get_object(rid, old['revision'])['object']['name'] == 'Harness example'
    assert not platform.get_object(rid, old['revision'])['is_current']
    assert platform.read_material(rid, eid, old['revision'])['body'] == body


def test_stale_reviewer_cannot_publish_concurrent_edits_or_state_changes(client):
    rid, eid, profile, _ = example()
    draft = platform.save_profile(rid, profile, 0, 'Draft')
    review = platform.transition(rid, 'review', draft['review_token'], 'Review')
    # An old token cannot bypass the intervening workflow transition.
    with pytest.raises(platform.PlatformError) as err:
        platform.transition(rid, 'withdrawn', draft['review_token'], 'Stale reviewer')
    assert err.value.status == 409
    record = store.get_record(rid); record['summary'] = 'Another edit'; store.save_record(record, record_id=rid)
    with pytest.raises(platform.PlatformError) as err:
        platform.transition(rid, 'published', review['review_token'], 'Stale approval')
    assert err.value.status == 409
    with pytest.raises(platform.PlatformError):
        platform.save_profile(rid, profile, 0, 'Stale draft')


def test_new_evidence_invalidates_and_is_not_in_old_material_manifest(client):
    rid, eid, profile, _ = example()
    publish(rid, profile); old = platform.get_object(rid)
    new = store.add_evidence(rid, 'https://example.org/new', 'New doc', 'A new source body')
    assert platform.preview(rid)['selection']['state'] == 'needs_review'
    with pytest.raises(platform.PlatformError):
        platform.read_material(rid, new, old['revision'])
    assert platform.read_material(rid, eid, old['revision'])['body']


def test_withdrawal_blocks_history_even_when_draft_is_reopened(client):
    rid, eid, profile, _ = example()
    result = publish(rid, profile); old = platform.get_object(rid)
    withdrawn = platform.transition(rid, 'withdrawn', result['review_token'], 'Material withdrawn')
    assert client.get(f'/api/v1/platform/objects/{rid}?revision={old["revision"]}').status_code == 404
    profile['introduction'] += ' Revised.'
    draft = platform.save_profile(rid, profile, withdrawn['profile_revision'], 'Rework')
    assert draft['selection']['state'] == 'withdrawn'
    review = platform.transition(rid, 'review', draft['review_token'], 'Recheck')
    assert client.get(f'/api/v1/platform/objects/{rid}?revision={old["revision"]}').status_code == 410
    assert client.get(f'/api/v1/platform/objects/{rid}/materials/{eid}?revision={old["revision"]}').status_code == 410
    platform.transition(rid, 'published', review['review_token'], 'Verified again')
    assert platform.get_object(rid)['is_current']
    assert client.get(f'/api/v1/platform/objects/{rid}?revision={old["revision"]}').status_code == 410


def test_false_quotes_versions_and_cross_object_evidence_are_rejected(client):
    rid, eid, profile, _ = example()
    other, oeid, _, _ = example('other')
    profile['attention'][0]['quote'] = 'This tool is the best on every benchmark'
    draft = platform.save_profile(rid, profile, 0, 'Invalid quote')
    assert any('Attention' in e for e in draft['gate']['errors'])
    profile['materials'].append({'evidence_id':oeid,'primary':True})
    draft = platform.save_profile(rid, profile, 1, 'Wrong object')
    assert any('does not belong' in e for e in draft['gate']['errors'])
    record = store.get_record(rid); record['version'] = 'v2'; store.save_record(record, record_id=rid)
    assert any('version' in e for e in platform.preview(rid)['gate']['errors'])


def test_read_tokens_cannot_publish_and_drafts_never_leak(client, monkeypatch):
    rid, eid, profile, _ = example()
    platform.save_profile(rid, profile, 0, 'Private draft')
    monkeypatch.setenv('FIELDTOFIT_READ_TOKEN','reader')
    headers={'Authorization':'Bearer reader'}
    assert client.get('/api/v1/platform/objects').status_code == 401
    assert client.get('/api/v1/platform/objects',headers=headers).json['total'] == 0
    assert client.get('/api/v1/admin/platform/objects/'+rid,headers=headers).status_code == 401
    assert client.post('/api/v1/admin/platform/objects/'+rid+'/transition',json={},headers=headers).status_code == 401
    assert client.get('/api/v1/platform/objects/'+rid,headers=headers).status_code == 404
    assert client.patch('/api/v1/admin/platform/objects/'+rid,json={'profile':[], 'expected_revision':0,'reason':'bad'},headers=ADMIN).status_code == 400


def test_transaction_failure_keeps_profile_publication_and_source_consistent(client, monkeypatch):
    rid, eid, profile, _ = example()
    publish(rid, profile)
    original_db = store.get_db
    @contextmanager
    def fail_log(*args, **kwargs):
        with original_db(*args, **kwargs) as db:
            class Connection:
                def execute(self, sql, params=()):
                    if sql.startswith('INSERT INTO knowledge_publications'):
                        raise sqlite3.OperationalError('Simulated audit failure')
                    return db.execute(sql, params)
            yield Connection()
    monkeypatch.setattr(store,'get_db',fail_log)
    before=store.get_record(rid)
    changed=dict(before);changed['title']='Should roll back'
    with pytest.raises(sqlite3.OperationalError):
        store.save_record(changed,record_id=rid)
    assert store.get_record(rid)['title']==before['title']
    assert platform.get_object(rid)['is_current']
    monkeypatch.setattr(platform,'get_db',fail_log)
    with pytest.raises(sqlite3.OperationalError):
        platform.save_profile(rid,{**profile,'introduction':'Also rolls back'},1,'Update')
    assert platform.preview(rid)['profile_revision']==1
    assert platform.preview(rid)['selection']['state']=='published'


@pytest.mark.parametrize('query',['limit=true','limit=1.5','limit=101','offset=-1','object_type=unknown'])
def test_invalid_queries(client, query):
    assert client.get('/api/v1/platform/objects?'+query).status_code == 400


def test_license_alone_cannot_count_as_the_primary_document(client):
    rid, eid, profile, _ = example()
    profile['materials'][0]['kind'] = 'license'
    draft = platform.save_profile(rid, profile, 0, 'Mislabelled primary material')
    assert any('primary material' in error for error in draft['gate']['errors'])


def test_capture_integrity_and_explicit_preview_loader(tmp_path):
    import os, subprocess, sys
    env = {**os.environ, 'PYTHON_DOTENV_DISABLED':'1'}
    result = subprocess.run([sys.executable,'-m','examples.platform.load','--data-dir',str(tmp_path/'preview'),'--publish'],
                            env=env,capture_output=True,text=True,check=True)
    import json
    report=json.loads(result.stdout)
    assert report['gate']['ready'] and report['selection']['state']=='published'
    assert report['source_capture']['upstream_version'] is None
    # Reimport cannot overwrite subsequent editorial work or republish a withdrawn record.
    repeated=subprocess.run([sys.executable,'-m','examples.platform.load','--data-dir',str(tmp_path/'preview'),'--publish'],
                            env=env,capture_output=True,text=True,check=True)
    assert json.loads(repeated.stdout)['status']=='already_exists'


def test_readonly_inventory_and_consistent_backup(client,tmp_path):
    from scripts.maintenance.platform_inventory import inspect
    from backend.config import DB_PATH
    rid, eid, profile, _ = example()
    report=inspect(DB_PATH,tmp_path/'copy.sqlite')
    assert report['counts']['knowledge_records']==1 and report['backup']['integrity']=='ok'
    with pytest.raises(FileExistsError):
        inspect(DB_PATH,tmp_path/'copy.sqlite')
    with sqlite3.connect(tmp_path/'copy.sqlite') as copied:
        assert copied.execute('SELECT id FROM knowledge_records').fetchone()[0]==rid


@pytest.mark.parametrize('changes', [
    {'kind':'metric','value':True,'platform':'GitHub','window':'total'},
    {'kind':'metric','value':float('nan'),'platform':'GitHub','window':'total'},
    {'observed_at':'2999-01-01T00:00:00Z'},
])
def test_invalid_attention_observations(client, changes):
    rid, eid, profile, _ = example()
    profile['attention'][0].update(changes)
    with pytest.raises(platform.PlatformError):
        platform.save_profile(rid,profile,0,'Bad observation')
