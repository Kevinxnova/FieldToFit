"""Review-file publication boundaries, revisions and web/MCP consistency."""
import copy
import json
import pytest
from test_knowledge import client, MCP
from backend.knowledge import platform_watch as watch


def replace_data(tmp_path, monkeypatch):
    data = json.loads(watch.CONTENT_PATH.read_text())
    path = tmp_path / 'watch.json'
    path.write_text(json.dumps(data))
    monkeypatch.setattr(watch, 'CONTENT_PATH', path)
    return data, path


def test_shared_content_complete_and_searchable(client):
    response = client.get('/api/v1/platform/watch')
    assert response.status_code == 200
    body = response.json
    assert body['total'] == 27
    assert [g['count'] for g in body['groups']] == [9, 4, 7, 3, 4]
    rpc = client.post('/api/mcp/curated', headers=MCP, json={'jsonrpc':'2.0','id':1,'method':'tools/call',
        'params':{'name':'curated_watch','arguments':{}}}).json['result']
    assert not rpc.get('isError') and rpc['structuredContent'] == body
    assert client.get('/api/v1/platform/watch?q=VideoCrop').json['items'][0]['name'] == 'ComfyUI'
    assert client.get('/api/v1/platform/watch?type=skill').json['total'] == 3
    assert client.get('/api/v1/platform/watch?q=not-a-known-profile').json['total'] == 0
    assert client.get('/api/v1/platform/watch?type=invalid').status_code == 400
    assert client.get('/api/v1/platform/watch?id=missing').status_code == 404
    for item in body['items']:
        assert len(item['interpretation']) == 2 and item['sources']
        assert all(s['coverage'] == 'link_only' for s in item['sources'])


def test_private_fields_drafts_and_withdrawal(client, tmp_path, monkeypatch):
    data,path = replace_data(tmp_path,monkeypatch)
    first = watch.watch()
    item = data['items'][0]
    item['private_note'] = 'SECRET'
    item['interpretation'][0]['private_note'] = 'SECRET'
    item['blocks'][0]['private_note'] = 'SECRET'
    item['sources'][0]['private_note'] = 'SECRET'
    draft = copy.deepcopy(item); draft.update(id='CW-M99',state='draft',name='SECRET')
    data['items'].append(draft);path.write_text(json.dumps(data))
    assert watch.watch()['revision'] == first['revision']
    assert 'SECRET' not in json.dumps(watch.watch())
    item['state'] = 'withdrawn';path.write_text(json.dumps(data))
    assert client.get('/api/v1/platform/watch?id=CW-M01').status_code == 404
    assert client.get('/api/v1/platform/watch?revision='+first['revision']).status_code == 409
    assert '/for-you#watch-cw-m01' not in json.dumps(watch.watch())


@pytest.mark.parametrize('broken',['link','table','date','source','duplicate','coverage','attention'])
def test_malformed_publication_fails_closed(client,tmp_path,monkeypatch,broken):
    data,path=replace_data(tmp_path,monkeypatch);item=data['items'][0]
    if broken=='link': item['blocks'][0]['rows'][0][0]='[bad](javascript:alert)'
    if broken=='table': item['blocks'][0]['rows'][0].pop()
    if broken=='date': item['checked_at']='not-a-date'
    if broken=='source': item['sources']=[]
    if broken=='duplicate': data['items'].append(copy.deepcopy(item))
    if broken=='coverage': item['sources'][0]['coverage']='full_text'
    if broken=='attention': next(i for i in data['items'] if i['type']=='skill')['attention']['growth_7d']=123
    path.write_text(json.dumps(data))
    assert client.get('/api/v1/platform/watch').status_code==503


def test_read_access_and_revision(client,monkeypatch,tmp_path):
    data,path=replace_data(tmp_path,monkeypatch);revision=watch.watch()['revision']
    assert watch.watch(id='CW-M01')['revision']==revision
    data['title']='Updated collection';path.write_text(json.dumps(data))
    assert client.get('/api/v1/platform/watch?revision='+revision).status_code==409
    monkeypatch.setenv('FIELDTOFIT_READ_TOKEN','watch-token')
    assert client.get('/api/v1/platform/watch').status_code==401
    assert client.get('/api/v1/platform/watch',headers={'Authorization':'Bearer watch-token'}).status_code==200
    assert client.post('/api/v1/platform/watch',json={}).status_code==405
