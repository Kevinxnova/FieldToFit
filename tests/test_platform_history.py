"""Public history stays tied to a chosen revision and never exposes private notes."""
import pytest
from test_knowledge import client, MCP
from test_platform_updates import selected, withdraw
from test_platform import publish
from backend.db import get_db
from backend.knowledge import platform as p, platform_updates as u, platform_bundle as b, store


def revised(pub, profile, count=1):
    for index in range(count):
        profile['introduction'] += f' Revision {index}.'
        publish(pub['object']['id'],profile)
    return p.get_object(pub['object']['id'])


def test_history_is_bound_to_selected_revision_and_omits_private_notes(client):
    old,_,profile=selected()
    new=revised(old,profile)
    with get_db() as db:
        db.execute("UPDATE knowledge_publications SET reason='PRIVATE AUDIT NOTE'")
    initial=u.history(old['object']['id'],old['revision'])
    assert len(initial['items'])==1 and initial['items'][0]['to_revision']==old['revision']
    timeline=u.history(new['object']['id'],new['revision'])
    assert [e['kind'] for e in timeline['items']]==['updated','needs_review','added']
    assert 'introduction' in timeline['items'][0]['changed_fields']
    assert 'PRIVATE AUDIT NOTE' not in store.encode(timeline)
    assert all(e['id']<=new['revision'] for e in timeline['items'])


def test_history_pages_remain_fixed_after_new_publication(client):
    pub,_,profile=selected();pub=revised(pub,profile,3)
    page=u.history(pub['object']['id'],limit=2)
    ids=[e['id'] for e in page['items']]
    revised(pub,profile)
    while page['next_cursor']:
        args=page['continuation']['arguments']
        assert args['revision']==pub['revision']
        page=u.history(args['id'],args['revision'],args['limit'],args['cursor'])
        ids.extend(e['id'] for e in page['items'])
    assert len(ids)==7 and len(ids)==len(set(ids)) and max(ids)==pub['revision']
    assert ids==sorted(ids,reverse=True)


def test_withdrawal_blocks_history_cursor_and_republication_redacts_old_versions(client):
    pub,_,profile=selected();pub=revised(pub,profile)
    first=u.history(pub['object']['id'],pub['revision'],limit=1)
    withdraw(pub['object']['id'])
    with pytest.raises(p.PlatformError):
        u.history(pub['object']['id'],pub['revision'],1,first['next_cursor'])
    new=revised(pub,profile)
    page=u.history(pub['object']['id'],new['revision'])
    old=[e for e in page['items'] if e['id']<=pub['revision']]
    assert old and all(e['availability']=='unavailable' for e in old)
    assert all('name' not in e and 'read_url' not in e for e in old)


def test_bundle_includes_history_with_explicit_continuation_and_markdown(client):
    pub,_,profile=selected();pub=revised(pub,profile,11)
    result=b.build([{'id':pub['object']['id'],'revision':pub['revision']}])
    history=result['objects'][0]['history']
    assert history['total']==23 and len(history['items'])==20 and history['has_more']
    args=history['continuation']['arguments']
    rest=u.history(args['id'],args['revision'],args['limit'],args['cursor'])
    assert len(rest['items'])==3 and not rest['has_more']
    assert 'Public history through this publication' in b.markdown(result)
    assert 'curated_history' in b.markdown(result)
    # A historical export does not accidentally include later events.
    first_revision=rest['items'][-1]['to_revision']
    old=b.build([{'id':pub['object']['id'],'revision':first_revision}])
    assert old['objects'][0]['history']['total']==1


def test_history_cursor_errors_expiration_and_read_auth(client,monkeypatch):
    pub,_,profile=selected();pub=revised(pub,profile)
    page=u.history(pub['object']['id'],pub['revision'],limit=1)
    with pytest.raises(p.PlatformError,match='returned publication revision'):
        u.history(pub['object']['id'],cursor=page['next_cursor'])
    with pytest.raises(p.PlatformError,match='another query'):
        u.history(pub['object']['id'],pub['revision'],2,page['next_cursor'])
    with get_db() as db:
        db.execute("UPDATE knowledge_read_snapshots SET expires_at='2000-01-01T00:00:00+00:00'")
    route=f"/api/v1/platform/objects/{pub['object']['id']}/history"
    response=client.get(route,query_string={'revision':pub['revision'],'limit':1,'cursor':page['next_cursor']})
    assert response.status_code==410 and response.json['code']=='snapshot_expired'
    monkeypatch.setenv('FIELDTOFIT_READ_TOKEN','read-history')
    assert client.get(route).status_code==401
    headers={'Authorization':'Bearer read-history'}
    http=client.get(route,headers=headers).json
    mcp=client.post('/api/mcp',headers={**MCP,**headers},json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'curated_history','arguments':{'id':pub['object']['id']}}}).json['result']['structuredContent']
    assert http['items']==mcp['items'] and http['revision']==mcp['revision']


def test_unpublished_object_has_no_public_history(client):
    from test_platform import example
    rid,_,_,_=example('draft-only')
    assert client.get(f'/api/v1/platform/objects/{rid}/history').status_code==404
