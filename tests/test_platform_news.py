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
    by_id = {item['id']: item for item in body['items']}
    assert {'D-10', 'D-12', 'D-13'} <= by_id.keys()
    assert all(by_id[ident]['source_published_at'] == '2026-09-10' for ident in ('D-10', 'D-12', 'D-13'))
    expected = [item for item in json.loads(news.CONTENT_PATH.read_text())['items'] if item['state'] == 'published']
    assert body['total'] == len(expected)
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
    assert client.get('/api/v1/platform/news?id='+data['items'][0]['id']).status_code == 404
    assert client.get('/api/v1/platform/news?revision='+first['revision']).status_code == 409
    assert news.news()['total'] == first['total'] - 1


@pytest.mark.parametrize('broken', ['missing_source', 'bad_url', 'missing_date', 'duplicate_id', 'false_fulltext', 'missing_public_field', 'missing_metadata'])
def test_invalid_publication_is_not_partially_served(client,tmp_path,monkeypatch,broken):
    data = json.loads(news.CONTENT_PATH.read_text()); item=data['items'][0]
    if broken=='missing_source': item['interpretation'][0]['source_ids']=['absent']
    if broken=='bad_url': item['related']=[{'id':'CW-M01','name':'Unsafe link','url':'javascript:alert(1)'}]
    if broken=='missing_date': item['checked_at']=''
    if broken=='duplicate_id': data['items'].append(copy.deepcopy(item))
    if broken=='missing_public_field': del item['note']
    if broken=='missing_metadata': del data['edition']
    if broken=='false_fulltext': item['sources'][0]['coverage']='full_text'
    path=tmp_path/'news.json';path.write_text(json.dumps(data));monkeypatch.setattr(news,'CONTENT_PATH',path)
    response=client.get('/api/v1/platform/news')
    assert response.status_code==503 and 'items' not in response.json


def test_news_filters_access_and_read_only_tools(client,monkeypatch,tmp_path):
    # Keep filtering assertions independent of new editorial publications.
    data=json.loads(news.CONTENT_PATH.read_text())
    data['items']=[item for item in data['items'] if item['id'] in {'D-07','D-10','D-01'}]
    path=tmp_path/'filter-news.json';path.write_text(json.dumps(data))
    monkeypatch.setattr(news,'CONTENT_PATH',path)
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


def media_fixture():
    return {'url':'https://example.org/thumb.png','full_url':'https://example.org/full.png',
            'source_url':'https://example.org/release','alt':'Reviewed diagram','caption':'Diagram of this version',
            'credit':'Example authors','reuse_basis':'Permission recorded','version':'v1 · 2026-10-01',
            'reviewed_at':'2026-10-01','fit':'contain'}


def test_optional_media_is_public_whitelisted_and_revisioned(client):
    data=json.loads(news.CONTENT_PATH.read_text()); original=news.news(_data=data)
    item=data['items'][0]; item['media']={**media_fixture(),'internal_note':'SECRET'}; item['category']='tool'
    changed=news.news(_data=data)
    public=next(x for x in changed['items'] if x['id']==item['id'])
    assert public['media']==media_fixture() and public['category']=='tool'
    assert changed['revision']!=original['revision'] and 'SECRET' not in json.dumps(changed)
    item['state']='withdrawn'
    assert item['id'] not in {x['id'] for x in news.news(_data=data)['items']}


@pytest.mark.parametrize('patch', [{'url':'javascript:alert(1)'},{'url':'https://localhost/private'},
    {'full_url':'https://127.0.0.1/private'},{'source_url':'https://user:pass@example.org/x'},
    {'alt':''},{'reuse_basis':''},{'reviewed_at':'invalid'},{'fit':'stretch'}])
def test_media_validation_blocks_unsafe_or_incomplete_publication(client,patch):
    data=json.loads(news.CONTENT_PATH.read_text());data['items'][0]['media']={**media_fixture(),**patch}
    with pytest.raises(Exception):news.validate(data)
