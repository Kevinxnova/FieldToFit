"""Editorial lifecycle on isolated SQLite; never touches live content or services."""
import copy
import json
import pytest
from test_knowledge import client, ADMIN, MCP, seed
from backend.db import get_db
from backend.knowledge import content_workspace as ws

BASE='/api/v1/admin/workspace'
def call(client,path,body=None,method='post'):
    return getattr(client,method)(BASE+path,headers=ADMIN,**({'json':body or {}} if method!='get' else {}))
def migrate(client):
    r=call(client,'/migrate');assert r.status_code==200,r.json

def make(client,kind='watch'):
    ref=call(client,'/inbox',{'title':'Isolated example','url':'https://example.org/review','summary':'Candidate summary only'}).json['ref']
    r=call(client,'/select',{'ref':ref,'action':'select','kind':kind,'type':'tool'});assert r.status_code==200,r.json
    return r.json['id'],ref

def valid(client,kind,ident):
    d=call(client,f'/content/{kind}/{ident}',method='get').json
    content=copy.deepcopy(ws.seeds()[kind]['items'][0]);content['id']=ident;content['name']='Reviewed isolated example';content['highlight']=False
    if kind=='watch':content['type']='tool'
    content['private_note']='INTERNAL-SECRET'
    r=call(client,f'/content/{kind}/{ident}',{'draft_version':d['draft_version'],'draft':content},'patch');assert r.status_code==200,r.json
    return r.json

def publish(client,kind,ident):
    preview=call(client,f'/content/{kind}/{ident}/preview').json;assert preview['ready'],preview
    r=call(client,f'/content/{kind}/{ident}/publish',{'draft_version':preview['draft_version'],'review_token':preview['review_token'],'confirmed':True,'reason':'Reviewed isolated test content'})
    assert r.status_code==200,r.json
    return r.json


def test_migration_exact_public_equality_and_idempotence(client):
    paths=['news','watch','model-landscape'];before={p:client.get('/api/v1/platform/'+p).json for p in paths}
    assert not call(client,'/status',method='get').json['migrated']
    migrate(client)
    assert call(client,'/status',method='get').json['migrated']
    assert {p:client.get('/api/v1/platform/'+p).json for p in paths}==before
    d=call(client,'/content/watch/CW-M01',method='get').json
    assert d['history'][0]['action']=='import'
    d['draft']['name']='Private draft only'
    call(client,'/content/watch/CW-M01',d,'patch');migrate(client)
    assert call(client,'/content/watch/CW-M01',method='get').json['draft']['name']=='Private draft only'
    assert client.get('/api/v1/platform/watch').json==before['watch']
    assert call(client,'/backup',method='get').json['tables']['fieldtofit_content_items']
    assert call(client,'/backup',method='get').headers['Cache-Control']=='private, no-store'


@pytest.mark.parametrize('kind,tool',[('watch','curated_watch'),('news','curated_news')])
def test_select_save_preview_publish_shared_and_private(client,kind,tool):
    migrate(client);before=client.get('/api/v1/platform/'+kind).json
    ident,ref=make(client,kind)
    assert client.get('/api/v1/platform/'+kind).json==before
    assert call(client,f'/content/{kind}/{ident}/preview').json['ready'] is False
    d=valid(client,kind,ident)
    assert 'published_json' not in d and d['published'] is None
    assert client.get('/api/v1/platform/'+kind).json==before
    preview=call(client,f'/content/{kind}/{ident}/preview').json
    assert preview['ready'] and 'INTERNAL-SECRET' not in json.dumps(preview)
    assert client.get('/api/v1/platform/'+kind).json==before
    published=publish(client,kind,ident)
    assert not published['has_changes']
    public=client.get('/api/v1/platform/'+kind).json
    assert public['total']==before['total']+1
    assert 'INTERNAL-SECRET' not in json.dumps(public)
    rpc=client.post('/api/mcp/curated',headers=MCP,json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':tool,'arguments':{}}}).json['result']
    assert rpc['structuredContent']==public
    assert call(client,'/inbox?status=selected',method='get').json['total']==0
    assert call(client,'/inbox?status=completed',method='get').json['items'][0]['ref']==ref


def test_conflicts_import_provenance_and_publication_preview(client):
    migrate(client);ident,ref=make(client);d=valid(client,'watch',ident)
    exported=call(client,f'/content/watch/{ident}/export',method='get').json
    assert exported['materials'][0]['coverage']=='discovery_summary'
    bad={**exported,'materials_fingerprint':'stale'}
    assert call(client,f'/content/watch/{ident}',bad,'patch').status_code==409
    preview=call(client,f'/content/watch/{ident}/preview').json
    assert call(client,f'/content/watch/{ident}',exported,'patch').status_code==200
    assert call(client,f'/content/watch/{ident}',exported,'patch').status_code==409
    assert call(client,f'/content/watch/{ident}/publish',{'draft_version':preview['draft_version'],'review_token':preview['review_token'],'reason':'test','confirmed':True}).status_code==409
    preview=call(client,f'/content/watch/{ident}/preview').json
    publish(client,'watch','CW-M01') # collection changed by another editor
    assert call(client,f'/content/watch/{ident}/publish',{**preview,'reason':'test','confirmed':True}).status_code==409
    preview=call(client,f'/content/watch/{ident}/preview').json
    with get_db() as db:db.execute('UPDATE fieldtofit_manual_candidates SET summary=? WHERE ref=?',('Changed source summary',ref))
    assert call(client,f'/content/watch/{ident}/publish',{**preview,'reason':'test','confirmed':True}).status_code==409
    assert call(client,f'/content/watch/{ident}/publish',{**preview,'reason':'test','confirmed':False}).status_code==400


def test_withdraw_restores_to_draft_and_preserves_previous_public_while_editing(client):
    migrate(client);ident='CW-M01';original=client.get('/api/v1/platform/watch?id='+ident).json
    d=call(client,f'/content/watch/{ident}',method='get').json
    original_seq=d['history'][0]['seq'];d['draft']['name']='Revised name'
    call(client,f'/content/watch/{ident}',d,'patch')
    assert client.get('/api/v1/platform/watch?id='+ident).json==original
    d=publish(client,'watch',ident)
    withdrawn=call(client,f'/content/watch/{ident}/withdraw',{'draft_version':d['draft_version'],'reason':'Temporary correction'}).json
    assert withdrawn['state']=='withdrawn'
    assert client.get('/api/v1/platform/watch?id='+ident).status_code==404
    restored=call(client,f'/content/watch/{ident}/restore',{'draft_version':withdrawn['draft_version'],'seq':original_seq})
    assert restored.status_code==200 and restored.json['draft']['name']==original['items'][0]['name']
    assert client.get('/api/v1/platform/watch?id='+ident).status_code==404
    publish(client,'watch',ident)
    assert client.get('/api/v1/platform/watch?id='+ident).json['items']==original['items']


def test_discovery_date_paging_reselection_semantic_links_and_feedback(client):
    migrate(client)
    for i in range(33):
        call(client,'/inbox',{'title':f'Manual {i}','url':f'https://example.org/a?id={i}','summary':'Public summary'})
    with get_db() as db:
        db.execute("UPDATE fieldtofit_manual_candidates SET created_at='2026-09-11T16:01:00Z'")
    assert call(client,'/inbox?since=2026-09-11&until=2026-09-11',method='get').json['total']==0
    r=call(client,'/inbox?since=2026-09-12&until=2026-09-12',method='get').json
    assert r['total']==33 and len(r['items'])==30 and r['next_offset']==30
    assert len(call(client,'/inbox?offset=30',method='get').json['items'])==3
    ref=r['items'][0]['ref'];s=call(client,'/select',{'ref':ref,'action':'select','kind':'watch'}).json
    call(client,'/select',{'ref':ref,'action':'deferred'})
    assert call(client,'/select',{'ref':ref,'action':'select'}).json['id']==s['id']
    assert call(client,'/inbox?status=selected',method='get').json['total']==1
    rid=seed(title='Knowledge source')
    assert any(x['ref']=='record:'+rid for x in call(client,'/inbox?q=Knowledge',method='get').json['items'])
    for i in range(32):client.post('/api/v1/feedback',json={'category':'general','content':f'Recommend a public resource {i}'})
    # Use SQL fixture because public feedback rate limiting intentionally prevents bulk anonymous spam.
    with get_db() as db:
        db.execute('DELETE FROM knowledge_feedback')
        for i in range(32):db.execute('INSERT INTO knowledge_feedback(category,content,created_at) VALUES(?,?,?)',('general',f'Recommend resource {i}',ws.stamp()))
    feedback=call(client,'/feedback',method='get').json
    assert feedback['total']==32 and len(feedback['items'])==30
    fid=feedback['items'][0]['id']
    assert client.patch(f'/api/v1/admin/feedback/{fid}',headers=ADMIN,json={'status':'reviewing','resolution':'Related CW-M01'}).status_code==200
    assert call(client,'/feedback?status=reviewing',method='get').json['total']==1
    assert call(client,'/inbox',{'title':'Recommended','url':'https://example.org/recommended','feedback_id':fid}).status_code==201


def test_submission_and_order_gates(client):
    migrate(client);ident,ref=make(client);d=valid(client,'watch',ident)
    d['draft'].update(origin='developer_submission',submission={'usage':'Open demo','openness':'Open source','relationship':'Author','entry_url':'https://example.org/demo'},submission_review={'confirmed':False},_position=1)
    call(client,f'/content/watch/{ident}',d,'patch')
    assert not call(client,f'/content/watch/{ident}/preview').json['ready']
    d=call(client,f'/content/watch/{ident}',method='get').json;d['draft']['submission_review']['confirmed']=True
    call(client,f'/content/watch/{ident}',d,'patch');publish(client,'watch',ident)
    public=client.get('/api/v1/platform/watch?origin=developer_submission').json
    assert public['items'][0]['id']==ident and 'submission_review' not in public['items'][0]
    assert '_position' not in public['items'][0]


def test_chart_snapshot_validation_and_no_implicit_publish(client):
    migrate(client);before=client.get('/api/v1/platform/model-landscape').json
    d=call(client,'/content/charts/snapshot',method='get').json
    d['draft']['landscape']['sources'][0]['price_unit']='unreviewed_unit'
    call(client,'/content/charts/snapshot',d,'patch')
    assert not call(client,'/content/charts/snapshot/preview').json['ready']
    assert client.get('/api/v1/platform/model-landscape').json==before
    d=call(client,'/content/charts/snapshot',method='get').json
    call(client,'/content/charts/snapshot/restore',{'draft_version':d['draft_version'],'seq':d['history'][0]['seq']})
    publish(client,'charts','snapshot')
    assert client.get('/api/v1/platform/model-landscape').json==before


def test_admin_auth_origin_and_missing_migration(client):
    assert client.get(BASE+'/status').status_code==401
    assert client.post(BASE+'/migrate',headers={**ADMIN,'Origin':'https://hostile.example'},json={}).status_code==403
    ref=call(client,'/inbox',{'title':'Candidate','url':'https://example.org/candidate'}).json['ref']
    assert call(client,'/select',{'ref':ref,'action':'select'}).status_code==409
    assert client.get('/api/v1/platform/watch').json['total']==27
    migrate(client)
    assert client.get(BASE+'/backup').status_code==401
    assert call(client,'/content/watch/CW-M01/publish',{'draft_version':1,'reason':'Missing preview','confirmed':True}).status_code==409
    assert call(client,'/content/watch/CW-M01',{'draft_version':1,'draft':{'id':'changed-id'}},'patch').status_code==400


def test_daily_intake_original_materials_reach_editor_without_publishing(client):
    import hashlib
    from backend.knowledge.platform_maintenance import stage
    migrate(client)
    source={'id':'github-skills','url':'https://example.org/intake','config':{'name':'Maintained source','object_type':'tool'}}
    body='Actual captured README, with enough detail for editorial review.'
    material={'key':'readme','kind':'readme','primary':True,'url':'https://example.org/readme','locator':'README.md','body':body,'coverage':'full_text','hash':hashlib.sha256(body.encode()).hexdigest()}
    stage(source,[material],{'stars':123})
    pending=call(client,'/inbox?q=Maintained',method='get').json['items']
    assert len(pending)==1 and pending[0]['ref'].startswith('intake:') and pending[0]['metrics']['stars']==123
    selected=call(client,'/select',{'ref':pending[0]['ref'],'action':'select','kind':'watch'}).json
    exported=call(client,f"/content/watch/{selected['id']}/export",method='get').json
    assert exported['materials'][0]['body']==body and exported['materials'][0]['coverage']=='full_text'
    assert client.get('/api/v1/platform/watch').json['total']==27


def test_malformed_drafts_cannot_break_editor_and_chart_private_fields_stay_private(client):
    migrate(client)
    d=call(client,'/content/watch/CW-M01',method='get').json;d['draft']['blocks']='bad shape'
    assert call(client,'/content/watch/CW-M01',d,'patch').status_code==400
    d=call(client,'/content/charts/snapshot',method='get').json
    chart=d['draft']['landscape'];chart['private_note']='SECRET-CHART';chart['sources'][0]['private_note']='SECRET-CHART';chart['sources'][0]['points'][0]['private_note']='SECRET-CHART'
    call(client,'/content/charts/snapshot',d,'patch')
    preview=call(client,'/content/charts/snapshot/preview').json
    assert preview['ready'] and 'SECRET-CHART' not in json.dumps(preview)
    published=publish(client,'charts','snapshot');assert not published['has_changes']
    before=client.get('/api/v1/platform/model-landscape').json
    assert 'SECRET-CHART' not in json.dumps(before)
    publish(client,'charts','snapshot')
    assert client.get('/api/v1/platform/model-landscape').json==before


def test_explicit_migration_creates_tables_when_production_auto_init_disabled(client):
    with get_db() as db:
        for table in ('fieldtofit_content_sets','fieldtofit_content_items','fieldtofit_content_history','fieldtofit_inbox','fieldtofit_manual_candidates','fieldtofit_item_sources'):
            db.execute('DROP TABLE '+table)
    assert call(client,'/status',method='get').json['migrated'] is False
    before=client.get('/api/v1/platform/watch').json
    migrate(client)
    assert call(client,'/status',method='get').json['migrated'] is True
    assert client.get('/api/v1/platform/watch').json==before


def test_remote_server_batch_lifecycle_and_race_rollbacks(client,monkeypatch):
    """Execute the actual generated remote guard SQL; no interactive transaction."""
    from contextlib import contextmanager
    from backend.db import TursoConnection, TursoCursor
    from backend.knowledge import workspace_transactions as tx
    migrate(client)
    counts=[];race=[None]
    class RemoteSQL(TursoConnection):
        def __init__(self,db):self.db=db
        def execute(self,sql,params=()):
            assert not self.db.in_transaction
            rows=self.db.execute(sql,params).fetchall()
            return TursoCursor(rows,0,None)
        def atomic_statements(self,statements):
            assert not self.db.in_transaction
            if race[0]:
                mutation=race[0];race[0]=None;mutation(self.db);self.db.commit()
            counts.append(len(statements));self.db.execute('BEGIN IMMEDIATE')
            try:
                results=[]
                for sql,args in statements:
                    cursor=self.db.execute(sql,args);results.append(TursoCursor(cursor.fetchall(),cursor.rowcount,None))
                self.db.commit();return results
            except Exception:
                self.db.rollback();raise
    @contextmanager
    def remote():
        with get_db() as db:yield RemoteSQL(db)
    monkeypatch.setattr(tx,'get_db',remote)
    ident,ref=make(client);d=valid(client,'watch',ident);published=publish(client,'watch',ident)
    assert counts and all(n>=2 for n in counts)
    before=client.get('/api/v1/platform/watch').json
    preview=call(client,f'/content/watch/{ident}/preview').json
    race[0]=lambda db:db.execute('UPDATE fieldtofit_content_sets SET revision=revision+1 WHERE kind=?',('watch',))
    r=call(client,f'/content/watch/{ident}/publish',{**preview,'reason':'Race check','confirmed':True})
    assert r.status_code==409,r.json
    assert client.get('/api/v1/platform/watch').json==before
    d=call(client,f'/content/watch/{ident}',method='get').json;d['draft']['name']='Must not overwrite concurrent draft'
    race[0]=lambda db:db.execute('UPDATE fieldtofit_content_items SET draft_version=draft_version+1 WHERE kind=? AND id=?',('watch',ident))
    assert call(client,f'/content/watch/{ident}',d,'patch').status_code==409
    assert call(client,f'/content/watch/{ident}',method='get').json['draft']['name']!='Must not overwrite concurrent draft'
    preview=call(client,f'/content/watch/{ident}/preview').json
    race[0]=lambda db:db.execute('UPDATE fieldtofit_manual_candidates SET summary=? WHERE ref=?',('New source after validation',ref))
    assert call(client,f'/content/watch/{ident}/publish',{**preview,'reason':'Source race','confirmed':True}).status_code==409
    d=call(client,f'/content/watch/{ident}',method='get').json
    assert call(client,f'/content/watch/{ident}/withdraw',{'draft_version':d['draft_version'],'reason':'Remote withdrawal'}).status_code==200
    d=call(client,f'/content/watch/{ident}',method='get').json
    assert call(client,f'/content/watch/{ident}/restore',{'draft_version':d['draft_version'],'seq':d['history'][-1]['seq']}).status_code==200
