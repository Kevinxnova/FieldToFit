"""Unified public discovery against isolated published fixtures, never production."""
import json
import pytest
from test_knowledge import client, MCP
from test_content_workspace import call, migrate, publish, make, valid
from test_editorial_v130 import mat, with_material, rpc
from test_platform_updates import selected, withdraw
from backend.db import get_db
from backend.knowledge import platform_lookup as l, content_workspace as ws, stewardship as st
from backend.knowledge.platform import PlatformError


def edit(client, kind, ident, **changes):
    d=ws.detail(kind,ident);d['draft'].update(changes)
    r=call(client,f'/content/{kind}/{ident}',d,'patch');assert r.status_code==200,r.json
    return r.json


def test_cross_collection_alias_and_publication_boundary(client):
    migrate(client)
    edit(client,'news','D-01',aliases=['共享别名'],private_note='DO-NOT-DISCLOSE')
    edit(client,'watch','CW-M01',aliases=['共享别名'])
    assert l.lookup('共享别名')['total']==0
    publish(client,'news','D-01');publish(client,'watch','CW-M01')
    from test_platform import example,publish as legacy_publish
    rid,_,profile,_=example('unified');profile['aliases']=['共享别名'];legacy_publish(rid,profile)
    result=l.lookup('共享别名')
    assert {i['scope'] for i in result['items']}=={'news','watch','library'}
    assert all('alias' in i['match_reasons'] for i in result['items'])
    assert 'DO-NOT-DISCLOSE' not in json.dumps(result)
    assert l.lookup('DO-NOT-DISCLOSE')['total']==0
    assert l.lookup('共享别名',scope='watch',object_type='model')['total']==1
    for hit in result['items']:
        reading=hit['reading'];assert not rpc(client,reading['tool'],reading['arguments']).get('isError')
        assert not rpc(client,'curated_bundle',{'objects':[hit['bundle_ref']]}).get('isError')


def test_body_snippet_has_exact_offsets_hash_and_readable_continuation(client):
    migrate(client)
    body='prefix '+('original source text. '*30)+'Ｓｔｒａｓｓｅ distinctive retrieval '+('tail '*30)
    with_material(client,material=mat(body=body,locator='README.md / retrieval'))
    assert l.lookup('distinctive')['total']==0
    publish(client,'watch','CW-M01')
    result=l.lookup('strasse distinctive')
    hit=result['items'][0];snippet=next(s for s in hit['snippets'] if s.get('material_id'))
    assert snippet['text']==body[snippet['offset']:snippet['end_offset']]
    assert snippet['content_role']=='source_material' and snippet['source_url']==mat()['url']
    read=rpc(client,snippet['reading']['tool'],snippet['reading']['arguments'])['structuredContent']
    assert read['body'].startswith(snippet['text']) and read['material']['content_hash']==snippet['content_hash']
    with get_db() as db:
        raw=db.execute('SELECT data FROM knowledge_read_snapshots WHERE id=?',(result['snapshot'],)).fetchone()[0]
    assert 'distinctive' not in raw and 'original source' not in raw


def test_link_only_metadata_is_findable_but_body_not_invented(client):
    migrate(client)
    with_material(client,material=mat(title='RareLinkTitle',body='',coverage='link_only',reason='Link permission only'))
    publish(client,'watch','CW-M01')
    hit=l.lookup('RareLinkTitle')['items'][0]
    assert hit['coverage']['readable_materials']==0 and hit['coverage']['link_only_materials']==1
    assert hit['match_reasons']==['material_title'] and not any(s.get('material_id') for s in hit['snippets'])
    assert l.lookup('SOURCE-ONLY')['total']==0


def test_legacy_evidence_not_selected_or_changed_is_not_searchable(client):
    pub,mid,_=selected('read-only');rid=pub['object']['id']
    assert l.lookup('Source detail',scope='library')['total']==1
    with get_db() as db:db.execute('UPDATE knowledge_evidence SET body=? WHERE id=?',('STALE SOURCE SECRET',mid))
    assert l.lookup('Source detail',scope='library')['total']==0
    assert l.lookup('STALE SOURCE SECRET')['total']==0
    from test_platform import example
    example('unselected')
    assert l.lookup('Source detail',scope='library')['total']==0
    assert l.lookup(rid)['items'][0]['materials'][0]['coverage']=='unavailable'


def test_short_name_does_not_match_inside_api_and_ranks_exact_first(client):
    migrate(client)
    edit(client,'watch','CW-M01',name='Pi',introduction='Simple fixture')
    edit(client,'watch','CW-M02',name='API project',introduction='Simple fixture')
    publish(client,'watch','CW-M01');publish(client,'watch','CW-M02')
    result=l.lookup('Pi',scope='watch')
    assert all(i['name']=='Pi' for i in result['items'][:2])
    assert 'CW-M01' in {i['id'] for i in result['items'][:2]}
    assert 'CW-M02' not in {i['id'] for i in result['items']}
    assert l.lookup('cw-m01')['items'][0]['match_reasons'][0]=='id'


def test_cursor_keeps_membership_rechecks_changes_and_redacts_withdrawals(client):
    migrate(client)
    for ident in ('CW-M01','CW-M02'):
        edit(client,'watch',ident,aliases=['PaginationFixture']);publish(client,'watch',ident)
    first=l.lookup('PaginationFixture',limit=1)
    edit(client,'watch','CW-M03',aliases=['PaginationFixture']);publish(client,'watch','CW-M03')
    edit(client,'watch','CW-M02',introduction='Current reviewed description');publish(client,'watch','CW-M02')
    second=l.lookup('PaginationFixture',limit=1,cursor=first['next_cursor'])
    assert second['total']==2 and second['items'][0]['id']=='CW-M02' and second['items'][0]['changed_since_search']
    assert second['items'][0]['introduction']=='Current reviewed description'
    preview=call(client,'/content/watch/CW-M02/preview').json
    response=call(client,'/content/watch/CW-M02/withdraw',{'draft_version':preview['draft_version'],'review_token':preview['review_token'],'confirmed':True,'reason':'PRIVATE withdrawal reason'})
    assert response.status_code==200,response.json
    redacted=l.lookup('PaginationFixture',limit=1,cursor=first['next_cursor'])
    assert redacted['items'][0]['unavailable'] and set(redacted['items'][0])=={'id','unavailable','code','detail'}
    assert 'Current reviewed description' not in json.dumps(redacted)
    assert l.lookup('PaginationFixture')['total']==2


def test_permissions_removed_between_pages_hide_source_snippets(client):
    migrate(client);with_material(client,material=mat(body='RevocableText '*30));publish(client,'watch','CW-M01')
    first=l.lookup('RevocableText')
    with_material(client,material=mat(coverage='withdrawn',body='',reason='Revoked'));publish(client,'watch','CW-M01')
    resumed=l.lookup('RevocableText',cursor=first['page_cursor'])
    assert resumed['items'][0]['unavailable'] and 'RevocableText' not in json.dumps(resumed['items'])
    assert l.lookup('RevocableText')['total']==0


def test_merge_old_id_aliases_and_undo_are_immediate(client):
    from test_stewardship import pair,ready
    source,target=pair(client)
    edit(client,'watch',source,aliases=['MergedAlias']);publish(client,'watch',source)
    original=l.lookup(source)
    data,preview=ready({'action':'merge','source':source,'target':target,'reason':'Verified matching identity'})
    result=st.apply({**data,'review_token':preview['review_token'],'confirmed':True})
    hit=l.lookup(source)['items'][0]
    assert hit['id']==target and source in hit['previous_ids'] and 'previous_id' in hit['match_reasons']
    assert l.lookup('MergedAlias')['items'][0]['id']==target
    assert l.lookup(source,cursor=original['page_cursor'])['items'][0]['unavailable']
    undo={'action':'undo','source':source,'target':target,'merge_id':result['id'],'restore_target':True,'reason':'Undo incorrect identity'}
    preview=st.preview(undo);st.apply({**undo,'review_token':preview['review_token'],'confirmed':True})
    assert l.lookup(source)['items'][0]['id']==source


@pytest.mark.parametrize('value',[None,'wrong', ['a']*21, ['bad\nline'], [True]])
def test_alias_validation_blocks_malformed_drafts(client,value):
    migrate(client);d=ws.detail('watch','CW-M01');d['draft']['aliases']=value
    assert call(client,'/content/watch/CW-M01',d,'patch').status_code==400


def test_api_mcp_contract_validation_access_and_cursor_expiry(client,monkeypatch):
    rest=client.get('/api/v1/platform/lookup?q=GPT').json
    mcp=rpc(client,'curated_lookup',{'q':'GPT'})['structuredContent']
    assert rest['items']==mcp['items'] and rest['coverage']==mcp['coverage']
    for args in ({'q':''},{'q':'a '*13},{'q':'x','scope':'private'},{'q':'x','limit':51},{'q':'x','cursor':'wrong'}):
        assert rpc(client,'curated_lookup',args)['isError']
    with pytest.raises(PlatformError) as e:l.lookup('Claude',cursor=rest['page_cursor'])
    assert e.value.code=='cursor_scope_mismatch'
    with get_db() as db:db.execute("UPDATE knowledge_read_snapshots SET expires_at='2000-01-01'")
    assert client.get('/api/v1/platform/lookup',query_string={'q':'GPT','cursor':rest['page_cursor']}).status_code==410
    monkeypatch.setenv('FIELDTOFIT_READ_TOKEN','private-reader')
    assert client.get('/api/v1/platform/lookup?q=GPT').status_code==401


def test_confirmed_relations_and_material_health_appear_without_private_reason(client):
    migrate(client);with_material(client);publish(client,'watch','CW-M01')
    relation={'action':'relation','source':'D-01','target':'CW-M01','relation':'release',
              'evidence':'https://example.org/release','version':'v2','reason':'PRIVATE-REVIEW-REASON'}
    preview=st.preview(relation);assert preview['ready'],preview
    st.apply({**relation,'review_token':preview['review_token'],'confirmed':True})
    st.observe('CW-M01','readme',mat()['url'],{'ok':False,'error':'HTTP 429'},ws.stamp())
    result=l.lookup('CW-M01')['items'][0]
    assert result['maintenance']['availability']=='available'
    assert result['related_objects']==result['maintenance']['relationships']
    assert result['related_objects'][0]['target_id']=='D-01'
    assert result['maintenance']['materials'][0]['availability']=='check_failed'
    assert 'PRIVATE-REVIEW-REASON' not in json.dumps(result)


def test_remote_index_uses_one_consistent_batch_without_per_object_reads(client):
    migrate(client);selected('remote-one');selected('remote-two')
    from backend.db import TursoConnection
    class Remote(TursoConnection):
        def __init__(self, local):self.local=local;self.calls=[]
        def atomic_statements(self, statements, read_only=False):
            assert read_only
            self.calls.append(statements)
            return [self.local.execute(sql,args) for sql,args in statements]
        def execute(self,*args):raise AssertionError('No per-object remote reads allowed')
    with get_db() as db:
        remote=Remote(db);docs=l.index(remote)
    assert len(remote.calls)==1 and len(remote.calls[0])==6
    assert sum(d['scope']=='library' for d in docs.values())==2


def test_corrupt_collection_fails_closed_instead_of_empty_success(client):
    migrate(client)
    with get_db() as db:db.execute("UPDATE fieldtofit_content_sets SET published_json='invalid' WHERE kind='news'")
    result=client.get('/api/v1/platform/lookup?q=GPT')
    assert result.status_code==503 and result.json['code']=='lookup_unavailable'


def test_merge_deduplicates_twenty_shared_aliases_before_limit(client):
    migrate(client)
    source=ws.detail('watch','CW-M01')['draft'];target=ws.detail('watch','CW-M02')['draft']
    source['aliases']=['Alias'+str(i) for i in range(20)];target['aliases']=source['aliases'][:]
    merged,_=st.combine(source,target,{})
    assert len(merged['aliases'])==20
