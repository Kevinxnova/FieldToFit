"""Source checks cannot impersonate document freshness; filtered snapshots stay bound."""
from datetime import datetime, timedelta, timezone

import pytest
from test_knowledge import client, MCP
from test_platform import example, publish
from test_platform_updates import withdraw
from backend.db import get_db
from backend.knowledge import platform as p, platform_sources as s, store


def selected_source(sid='feed-a', suffix='one', stamp='2026-09-08T23:59:59Z'):
    rid, _, profile, _ = example(suffix)
    record = store.get_record(rid); record['source_id'] = sid
    store.save_record(record, 'Source assigned', rid)
    publish(rid, profile)
    pub = p.get_object(rid)
    with get_db() as db:
        db.execute('UPDATE knowledge_publications SET created_at=? WHERE seq=?', (stamp, pub['revision']))
    return p.get_object(rid), profile


def register(sid='feed-a', status='success', age=2, enabled=1):
    success = (datetime.now(timezone.utc)-timedelta(days=age)).isoformat()
    with get_db() as db:
        db.execute('INSERT INTO knowledge_sources(id,name,category,url,adapter,config,enabled,status,last_attempt_at,last_success_at,error) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                   (sid, 'Public source', 'official', 'https://example.org/?token=private-value', 'rss', '{"secret":"private-value"}', enabled, status, store.now(), success, 'private-value'))
    return success


def test_checks_are_separate_from_record_review_and_private_registry(client):
    pub, _ = selected_source(); register()
    record = store.get_record(pub['object']['id']); record['checked_at'] = store.now()
    store.save_record(record, 'Checked record, not network', record['id'])
    result = p.get_object(record['id'])
    assert result['freshness'] == 'current'
    assert result['source_check']['state'] == 'stale'
    assert result['source_check']['last_success_at'] != result['record_checked_at']
    register('private-only')
    sources = client.get('/api/v1/platform/sources').json
    assert [x['id'] for x in sources['items']] == ['feed-a']
    assert 'private-value' not in store.encode(sources)
    assert 'private-only' not in store.encode(sources)
    assert sources['items'][0]['objects'] == 1


@pytest.mark.parametrize('run,age,enabled,expected', [('success',0,1,'current'),('error',2,1,'error'),('partial',2,1,'partial'),('running',2,1,'running'),('success',2,0,'paused')])
def test_source_states_preserve_last_success(client,run,age,enabled,expected):
    pub,_ = selected_source(); register(status=run,age=age,enabled=enabled)
    result = p.get_object(pub['object']['id'])['source_check']
    assert result['state'] == expected and result['last_success_at']


@pytest.mark.parametrize('stamp', [None,'invalid','2026-01-01T12:00:00','2999-01-01T00:00:00Z'])
def test_invalid_or_future_timestamps_do_not_claim_success(client,stamp):
    selected_source(); register()
    with get_db() as db:
        db.execute('UPDATE knowledge_sources SET last_success_at=? WHERE id=?',(stamp,'feed-a'))
    result=s.sources()['items'][0]
    assert result['state']=='unknown' and result['last_success_at'] is None


def test_unregistered_and_withdrawn_sources(client):
    pub,_=selected_source('manual-capture')
    assert p.get_object(pub['object']['id'])['source_check']['state']=='unregistered'
    withdraw(pub['object']['id'])
    assert s.sources()['items']==[]


def test_historical_source_identity_does_not_follow_current_record(client):
    pub,profile=selected_source('original')
    # Simulate a publication written before source_id was added to the snapshot.
    with get_db() as db:
        obj=dict(pub['object']);obj.pop('source_id')
        db.execute('UPDATE knowledge_publications SET snapshot=? WHERE seq=?',(store.encode(obj),pub['revision']))
    record=store.get_record(pub['object']['id']);record['source_id']='replacement'
    store.save_record(record,'Change collection source',record['id']);publish(record['id'],profile)
    assert p.get_object(record['id'],pub['revision'])['source_check']['id']=='original'
    assert p.get_object(record['id'])['source_check']['id']=='replacement'


def test_source_date_filters_use_utc_and_bind_snapshot(client):
    one,_=selected_source(stamp='2026-09-09T07:59:59+08:00') # September 8 UTC
    two,_=selected_source(suffix='two',stamp='2026-09-08T10:00:00Z')
    selected_source('feed-b','three',stamp='2026-09-08T12:00:00Z')
    page=p.search(source='feed-a',since='2026-09-08',until='2026-09-08',limit=1)
    assert page['total']==2 and page['items'][0]['object']['id']==two['object']['id']
    selected_source(suffix='four')
    next_page=p.search(source='feed-a',since='2026-09-08',until='2026-09-08',limit=1,cursor=page['next_cursor'])
    assert next_page['total']==2 and next_page['items'][0]['revision']==one['revision']
    with pytest.raises(p.PlatformError,match='another query'):
        p.search(source='feed-b',since='2026-09-08',until='2026-09-08',limit=1,cursor=page['next_cursor'])
    assert p.search(since='2026-09-09')['total']==0
    assert p.search(source='unlisted')['total']==0


@pytest.mark.parametrize('args', [{'since':'2026-02-30'},{'until':'20260908'},{'since':'2026-09-09','until':'2026-09-08'}])
def test_date_input_errors_are_explicit(client,args):
    response=client.get('/api/v1/platform/objects',query_string=args)
    assert response.status_code==400 and response.json['code']=='invalid_request'


def test_http_mcp_filters_and_sources_share_read_auth(client,monkeypatch):
    selected_source();register()
    monkeypatch.setenv('FIELDTOFIT_READ_TOKEN','read-test')
    assert client.get('/api/v1/platform/sources').status_code==401
    headers={'Authorization':'Bearer read-test'}
    args={'source':'feed-a','since':'2026-09-08','until':'2026-09-08'}
    http=client.get('/api/v1/platform/objects',query_string=args,headers=headers).json
    def tool(name,args):
        return client.post('/api/mcp',headers={**MCP,**headers},json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':args}}).json['result']['structuredContent']
    assert tool('curated_search',args)['items']==http['items']
    assert tool('curated_sources',{})['items']==client.get('/api/v1/platform/sources',headers=headers).json['items']
