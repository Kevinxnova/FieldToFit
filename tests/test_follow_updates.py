import json
import pytest
from test_knowledge import client, MCP
from test_content_workspace import migrate, call, make, valid, publish
from test_stewardship import ready
from backend.knowledge import stewardship as s, content_workspace as ws, follow_updates as f
from backend.knowledge.platform import PlatformError
from backend.db import get_db


def relation(source='D-01',target='CW-M01'):
    data={'action':'relation','source':source,'target':target,'relation':'release','evidence':'https://example.org/release','version':'v2','reason':'Verified relationship'}
    p=s.preview(data);return s.apply({**data,'review_token':p['review_token'],'confirmed':True})


def test_initial_baseline_direct_relations_and_no_private_drafts(client):
    migrate(client);initial=f.changes(object_ids=['CW-M01'],initialize=True)
    assert initial['items']==[] and initial['objects'][0]['name']=='GPT'
    relation()
    d=ws.detail('news','D-01');d['draft']['summary']='PRIVATE-DRAFT';ws.save('news','D-01',d)
    out=f.changes(object_ids=['CW-M01'],after=initial['until'])
    assert 'PRIVATE-DRAFT' not in json.dumps(out)
    assert any(e['object_id']=='D-01' for e in out['items'])
    assert len({e['id'] for e in out['items']})==len(out['items'])
    data=client.get('/api/v1/platform/changes?scope=workspace&include_related=true&initialize=true&object_id=CW-M01').json
    rpc=client.post('/api/mcp/curated',headers=MCP,json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'curated_changes','arguments':{'scope':'workspace','include_related':True,'initialize':True,'object_ids':['CW-M01']}}}).json['result']
    assert rpc['structuredContent']['objects']==data['objects']
    assert rpc['structuredContent']['until']==data['until']


def test_range_change_expiry_redaction_and_old_cursor_compatibility(client):
    migrate(client);relation();start=f.changes(object_ids=['CW-M01'],limit=1)
    assert start['has_more']
    with pytest.raises(PlatformError):f.changes(object_ids=['CW-M02'],limit=1,cursor=start['next_cursor'])
    with get_db() as db:db.execute("UPDATE knowledge_read_snapshots SET expires_at='2000-01-01' WHERE id=?",(start['snapshot'],))
    with pytest.raises(PlatformError) as err:f.changes(object_ids=['CW-M01'],limit=1,cursor=start['next_cursor'])
    assert err.value.code=='snapshot_expired'
    recovered=f.changes(object_ids=['CW-M01'],after=start['after'])
    assert start['items'][0]['id'] in {e['id'] for e in recovered['items']}
    old=s.changes(object_ids=['CW-M01'],limit=1)
    assert s.changes(object_ids=['CW-M01'],limit=1,cursor=old['resume_cursor'])['scope']=='workspace'
    d=ws.detail('news','D-01');call(client,'/content/news/D-01/withdraw',{'draft_version':d['draft_version'],'reason':'withdrawn fixture','confirmed':True})
    redacted=f.changes(object_ids=['CW-M01'])
    for e in redacted['items']:
        if e['object_id']=='D-01': assert 'sources' not in e and 'name' not in e


def test_relationship_removed_delivers_event_and_invalid_flags(client):
    migrate(client);relation();baseline=f.changes(object_ids=['CW-M01'],initialize=True)
    link=s.public_status('D-01')['relationships'][0]['id']
    data={'action':'relation_remove','source':'D-01','target':'CW-M01','link_id':link,'reason':'Remove relationship'}
    p=s.preview(data);s.apply({**data,'confirmed':True,'review_token':p['review_token']})
    out=f.changes(object_ids=['CW-M01'],after=baseline['until'])
    assert any(e['kind']=='relationship_removed' for e in out['items'])
    assert client.get('/api/v1/platform/changes?scope=workspace&include_related=bad').status_code==400
    assert client.get('/api/v1/platform/changes?include_related=true&object_id=CW-M01').status_code==400


def test_merge_reverse_preserves_original_identity(client):
    migrate(client);source,_=make(client,'watch');valid(client,'watch',source);publish(client,'watch',source)
    initial=f.changes(object_ids=[source],initialize=True)
    data,p=ready({'action':'merge','source':source,'target':'CW-M01','reason':'same object'})
    result=s.apply({**data,'review_token':p['review_token'],'confirmed':True})
    out=f.changes(object_ids=[source],after=initial['until']);assert out['objects'][0]['canonical_id']=='CW-M01'
    assert any(e['kind']=='merged' for e in out['items'])
    undo={'action':'undo','source':source,'target':'CW-M01','merge_id':result['id'],'restore_target':True,'reason':'wrong merge'}
    p=s.preview(undo);s.apply({**undo,'review_token':p['review_token'],'confirmed':True})
    out=f.changes(object_ids=[source],after=out['until']);assert out['objects'][0]['canonical_id']==source
    assert any(e['kind']=='merge_reversed' for e in out['items'])


def test_completed_resume_cursor_starts_new_window_at_first_event(client):
    migrate(client)
    with get_db() as db:
        s.event(db,'CW-M01','updated',{'changed_fields':['name']})
    initial=f.changes(object_ids=['CW-M01'],limit=100)
    assert not initial['has_more'] and initial['items']
    with get_db() as db:
        s.event(db,'CW-M01','updated',{'changed_fields':['introduction']})
    resumed=f.changes(object_ids=['CW-M01'],limit=100,cursor=initial['resume_cursor'])
    assert len(resumed['items'])==1
    assert resumed['items'][0]['changed_fields']==['introduction']


@pytest.mark.parametrize('action', ['publish', 'withdraw', 'observe', 'review', 'relation', 'relation_remove'])
def test_news_events_use_snapshot_before_remote_writes(client, monkeypatch, action):
    """A related-news event must not query after buffered writes, even for material events."""
    from contextlib import contextmanager
    from test_editorial_v130 import mat
    from backend.knowledge.workspace_transactions import GuardedWrites
    migrate(client)
    relation()
    detail = ws.detail('news', 'D-01')
    detail['draft']['reading_materials'] = [mat()]
    ws.save('news', 'D-01', detail)
    publish(client, 'news', 'D-01')
    observed = s.observe('D-01', 'readme', 'https://example.org/README.md',
                         {'ok': True, 'hash': 'first', 'final_url': 'https://example.org/README.md'})
    before = f.changes(object_ids=['CW-M01'], initialize=True)['until']
    @contextmanager
    def buffered():
        with get_db() as db:
            db.execute('BEGIN IMMEDIATE')
            g = GuardedWrites(db)
            yield g
            for sql, args in g.writes: db.execute(sql, args)
    monkeypatch.setattr(s, 'editorial_transaction', buffered)
    monkeypatch.setattr(ws, 'editorial_transaction', buffered)
    if action == 'publish':
        detail = ws.detail('news', 'D-01')
        detail['draft']['reading_materials'][0]['body'] += '\nUpdated original.'
        detail['draft']['reading_materials'].append(mat(id='license', title='License', url='https://example.org/LICENSE'))
        ws.save('news', 'D-01', detail)
        publish(client, 'news', 'D-01')
    elif action == 'withdraw':
        detail = ws.detail('news', 'D-01')
        ws.publish('news', 'D-01', {'draft_version': detail['draft_version'], 'reason': 'Fixture withdrawal'}, True)
    elif action == 'observe':
        s.observe('D-01', 'readme', 'https://example.org/README.md', {'ok': True, 'hash': 'changed', 'final_url': 'https://example.org/README.md'})
    elif action == 'review':
        s.decide_material({'id': 'D-01', 'material_id': 'readme', 'decision': 'reviewed', 'reason': 'Original reviewed', 'check_revision': s.digest(observed)})
    elif action == 'relation':
        relation(target='CW-M02')
    else:
        link = s.public_status('D-01')['relationships'][0]['id']
        data = {'action': 'relation_remove', 'source': 'D-01', 'target': 'CW-M01', 'link_id': link, 'reason': 'Fixture removal'}
        pre = s.preview(data)
        s.apply({**data, 'review_token': pre['review_token'], 'confirmed': True})
    events = f.changes(object_ids=['CW-M01'], after=before)['items']
    assert events and any(e['object_id'] == 'D-01' for e in events)
    if action == 'publish':
        assert {'updated', 'material_updated', 'material_added'} <= {e['kind'] for e in events}
    with get_db() as db:
        saved = [json.loads(r['data']) for r in db.execute('SELECT data FROM fieldtofit_steward_events WHERE object_id=?', ('D-01',)).fetchall()]
    assert all('CW-M01' in e['related_watch_ids'] for e in saved)
