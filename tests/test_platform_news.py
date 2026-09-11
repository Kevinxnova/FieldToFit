"""Public news shares one reviewed payload across readers and rejects unsafe drafts."""
import copy
import json
import pytest
from test_knowledge import client, MCP
from backend.knowledge import platform_news as news


def test_web_and_mcp_read_identical_news_with_deepseek(client):
    response = client.get('/api/v1/platform/news')
    assert response.status_code == 200
    body = response.json
    assert body['items'][0]['id'] == 'D-10' and body['items'][0]['source_published_at'] is None
    assert body['total'] == 10
    rpc = client.post('/api/mcp/curated', headers=MCP, json={'jsonrpc':'2.0','id':1,'method':'tools/call',
        'params':{'name':'curated_news','arguments':{}}}).json['result']
    assert not rpc.get('isError') and rpc['structuredContent'] == body
    for item in body['items']:
        assert item['interpretation'] and all(p['source_ids'] and p['locator'] for p in item['interpretation'])
        assert all(s['coverage'] == 'link_only' for s in item['sources'])


def test_revision_detects_correction_and_withdrawal_without_leaking_drafts(client, tmp_path, monkeypatch):
    data = json.loads(news.CONTENT_PATH.read_text())
    path = tmp_path / 'news.json'; path.write_text(json.dumps(data)); monkeypatch.setattr(news,'CONTENT_PATH',path)
    first = news.news()
    data['items'][0]['private_note'] = 'private editorial note'
    draft = copy.deepcopy(data['items'][0]); draft.update(id='D-99',state='draft',title='Private upcoming release')
    data['items'].append(draft); path.write_text(json.dumps(data))
    assert news.news()['revision'] == first['revision']
    assert 'private' not in json.dumps(news.news()).lower()
    data['items'][0]['state'] = 'withdrawn'; path.write_text(json.dumps(data))
    assert client.get('/api/v1/platform/news?id=D-10').status_code == 404
    assert client.get('/api/v1/platform/news?revision='+first['revision']).status_code == 409
    assert news.news()['total'] == 9


@pytest.mark.parametrize('broken', ['missing_source', 'bad_url', 'missing_date', 'duplicate_id', 'false_fulltext', 'missing_public_field', 'missing_metadata'])
def test_invalid_publication_is_not_partially_served(client,tmp_path,monkeypatch,broken):
    data = json.loads(news.CONTENT_PATH.read_text()); item=data['items'][0]
    if broken=='missing_source': item['interpretation'][0]['source_ids']=['absent']
    if broken=='bad_url': item['related'][0]['url']='javascript:alert(1)'
    if broken=='missing_date': item['checked_at']=''
    if broken=='duplicate_id': data['items'].append(copy.deepcopy(item))
    if broken=='missing_public_field': del item['note']
    if broken=='missing_metadata': del data['edition']
    if broken=='false_fulltext': item['sources'][0]['coverage']='full_text'
    path=tmp_path/'news.json';path.write_text(json.dumps(data));monkeypatch.setattr(news,'CONTENT_PATH',path)
    response=client.get('/api/v1/platform/news')
    assert response.status_code==503 and 'items' not in response.json


def test_news_filters_access_and_read_only_tools(client,monkeypatch):
    assert client.get('/api/v1/platform/news?q=deepseek').json['total']==2
    assert client.get('/api/v1/platform/news?q=nothing-match').json['total']==0
    assert client.get('/api/v1/platform/news?id=unknown').status_code==404
    assert client.post('/api/v1/platform/news',json={}).status_code==405
    monkeypatch.setenv('FIELDTOFIT_READ_TOKEN','private-read')
    assert client.get('/api/v1/platform/news').status_code==401
    assert client.get('/api/v1/platform/news',headers={'Authorization':'Bearer private-read'}).status_code==200


def test_edition_metadata_change_invalidates_revision(client, tmp_path, monkeypatch):
    data = json.loads(news.CONTENT_PATH.read_text())
    original = news.news()['revision']
    data['title'] = 'Corrected edition title'
    path = tmp_path / 'news.json'; path.write_text(json.dumps(data)); monkeypatch.setattr(news, 'CONTENT_PATH', path)
    assert client.get('/api/v1/platform/news?revision=' + original).status_code == 409
