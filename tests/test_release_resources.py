"""Resource identity, version safety and shared human/MCP filters."""
import base64
import json

import pytest

from test_knowledge import client, seed, MCP
from backend.knowledge import skills, sources, store


def test_skill_metadata_rejects_invalid_or_executable_yaml():
    text = '---\nname: pdf\ndescription: |\n  Read and edit PDF documents.\ncompatibility: Python\n---\n# Instructions\nRead the supplied document.'
    assert skills.parse_skill(text)['description'] == 'Read and edit PDF documents.'
    for bad in ['no metadata', '---\n- list\n---', '---\nname: invalid name\ndescription: d\n---',
                '---\nname: pdf\ndescription: !!python/object/apply:os.system ["echo forbidden"]\n---']:
        with pytest.raises(ValueError):
            skills.parse_skill(bad)
    assert not skills.safe_path('../SKILL.md')
    assert not skills.safe_path('/etc/SKILL.md')
    assert not skills.safe_path('skills/../SKILL.md')


def skill_source():
    return next(s for s in sources.list_sources() if s['id'] == 'github-skills')


def fake_repository(monkeypatch, commit='a' * 40, names=('pdf',)):
    tree = [{'path': f'skills/{name}/SKILL.md', 'type': 'blob', 'mode': '100644', 'sha': name, 'size': 200} for name in names]
    tree += [{'path': 'skills/pdf/scripts/run.py', 'type': 'blob', 'mode': '100644', 'sha': 'script', 'size': 10},
             {'path': 'skills/pdf/unsafe-link', 'type': 'blob', 'mode': '120000', 'sha': 'symlink'}]
    calls = []
    def fetch(url, headers=None):
        calls.append(url)
        if '/commits/' in url:
            return {'sha': commit}
        if '/git/trees/' in url:
            return {'tree': tree, 'truncated': False}
        if '/git/blobs/' in url:
            name = url.rsplit('/', 1)[-1]
            assert name in names, 'Supporting scripts must not be fetched or executed'
            text = f'---\nname: {name}\ndescription: Read and edit PDF documents.\nlicense: See LICENSE.txt\ncompatibility: Python\n---\n# Instructions\nRead the original document and retain its page numbers.'
            return {'encoding': 'base64', 'content': base64.b64encode(text.encode()).decode()}
        return {'default_branch': 'main'}
    monkeypatch.setattr(sources, 'fetch_json', fetch)
    return calls


def test_skill_version_identity_and_original_material(client, monkeypatch):
    calls = fake_repository(monkeypatch)
    assert skills.collect(skill_source()) == (1, 1)
    item = store.search_records(object_type='skill')['items'][0]
    rid = item['id']
    assert item['version'] == 'a' * 40
    assert item['facts']['license']['value'] == 'See LICENSE.txt'
    assert item['metadata']['skill']['execution'] == 'not_run'
    assert len(item['metadata']['skill']['files']) == 1
    assert '/blob/' + 'a' * 40 in item['metadata']['skill']['entrypoint']
    assert store.get_record(rid, include_body=True)['evidence'][0]['body'].startswith('---')
    assert all('run.py' not in url for url in calls)
    assert skills.collect(skill_source()) == (1, 0)
    fake_repository(monkeypatch, commit='b' * 40)
    assert skills.collect(skill_source()) == (1, 1)
    current = store.get_record(rid, include_body=True)
    assert current['version'] == 'b' * 40 and len(current['evidence']) == 2
    assert current['verification_status'] == 'not_verified'


def test_skill_paging_finishes_snapshot_before_new_version(client, monkeypatch):
    source = skill_source(); source['config']['limit'] = 1
    fake_repository(monkeypatch, names=('pdf', 'writing'))
    with pytest.raises(sources.PartialSourceError) as partial:
        skills.collect(source)
    assert partial.value.found == 1
    calls = fake_repository(monkeypatch, commit='b' * 40, names=('pdf', 'writing'))
    assert skills.collect(source)[0] == 1
    assert any('/git/trees/' + 'a' * 40 in url for url in calls)
    assert {r['version'] for r in store.search_records(object_type='skill')['items']} == {'a' * 40}


def test_capability_filter_is_independent_paginated_and_shared_with_mcp(client):
    one = seed('Skill', suffix='skill', object_type='skill', metadata={'capability_tags': ['PDF', 'pdf', 'coding']})
    seed('Agent', suffix='agent', object_type='agent', metadata={'capability_tags': ['pdf']})
    seed('PDF title only', suffix='unclassified', metadata={'capability_tags': ['pdf-extra']})
    seed('Hidden', suffix='hidden', status='withdrawn', metadata={'capability_tags': ['hidden']})
    seed('Grouped', suffix='grouped', metadata={'capability_tags': ['grouped'], 'merged_into': one})
    page = client.get('/api/v1/records?capability=pdf&limit=1').json
    assert page['total'] == 2 and page['next_offset'] == 1
    next_page = client.get('/api/v1/records?capability=pdf&limit=1&offset=1').json
    assert page['items'][0]['id'] != next_page['items'][0]['id']
    response = client.post('/api/mcp', json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
        'params': {'name': 'search', 'arguments': {'object_type': 'skill', 'capability': 'pdf'}}}, headers=MCP)
    result = response.json['result']['structuredContent']
    assert [r['id'] for r in result['items']] == [one]
    tags = {r['value']: r['count'] for r in client.get('/api/v1/catalog').json['capabilities']}
    assert tags == {'coding': 1, 'pdf': 2, 'pdf-extra': 1}
    assert client.get('/api/v1/records?capability=' + 'x' * 81).status_code == 400


def test_selected_agent_repository_preserves_type_and_version(client,monkeypatch):
    from backend.knowledge import repositories
    source={'id':'github-projects','config':{'projects':[{'repo':'example/agent','type':'agent'}]}}
    commit='c'*40
    body='An agent development framework. See the original instructions before running any code.'
    def fetch(url,headers=None):
        if '/commits/' in url:return {'sha':commit}
        if '/readme?' in url:return {'path':'README.md','encoding':'base64','content':base64.b64encode(body.encode()).decode()}
        return {'default_branch':'main','description':'An agent development framework','archived':True}
    monkeypatch.setattr(sources,'fetch_json',fetch)
    assert repositories.collect(source)==(1,1)
    record=store.search_records(object_type='agent')['items'][0]
    assert record['version']==commit and record['metadata']['repository_archived'] is True
    assert 'license' not in record['facts'] and store.get_record(record['id'])['verification_status']=='not_verified'
    material=store.get_record(record['id'],include_body=True)['evidence'][0]
    assert material['body']==body and commit in material['url']
    record['status']='withdrawn';store.save_record(record,record_id=record['id'])
    repositories.collect(source)
    assert store.search_records(object_type='agent')['total']==0
