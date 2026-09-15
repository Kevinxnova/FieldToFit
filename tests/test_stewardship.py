"""v1.4.0 identity and material lifecycle acceptance; isolated content only."""
import copy
import json
from datetime import datetime,timedelta,timezone
import pytest
from test_knowledge import client,ADMIN,MCP
from test_content_workspace import call,migrate,make,valid,publish
from test_editorial_v130 import mat,with_material,rpc
from backend.knowledge import stewardship as s, content_workspace as ws,content_materials as cm
from backend.knowledge.platform import PlatformError
from backend.db import get_db


def ready(data):
    p=s.preview(data)
    data={**data,'choices':{c['field']:'target' for c in p['conflicts']}}
    p=s.preview(data);assert p['ready'],p['errors']
    return data,p


def pair(client,kind='watch',published=True):
    migrate(client);target='CW-M01' if kind=='watch' else 'D-01'
    ident,_=make(client,kind);valid(client,kind,ident)
    if published:publish(client,kind,ident)
    return ident,target


@pytest.mark.parametrize('kind',['watch','news'])
def test_merge_preview_cas_alias_shared_and_undo(client,kind):
    source,target=pair(client,kind)
    before=client.get('/api/v1/platform/'+kind).json
    data={'action':'merge','source':source,'target':target,'reason':'Verified duplicate event/object'}
    p=s.preview(data);assert p['conflicts'] and not p['ready']
    assert client.get('/api/v1/platform/'+kind).json==before
    data,p=ready(data)
    with pytest.raises(PlatformError):s.apply({**data,'review_token':p['review_token']})
    result=s.apply({**data,'review_token':p['review_token'],'confirmed':True})
    public=client.get('/api/v1/platform/'+kind).json
    assert len(public['items'])==len(before['items'])-1
    assert source not in [i['id'] for i in public['items']]
    old=client.get('/api/v1/platform/'+kind+'?id='+source).json
    assert old['canonical_id']==target and old['resolved_from']==source
    assert old['items'][0]['id']==target and 'INTERNAL-SECRET' not in json.dumps(old)
    with pytest.raises(PlatformError):s.apply({**data,'review_token':p['review_token'],'confirmed':True})
    undo={'action':'undo','source':source,'target':target,'merge_id':result['id'],'restore_target':True,'reason':'Wrong duplicate decision'}
    p=s.preview(undo);assert p['ready'],p
    s.apply({**undo,'review_token':p['review_token'],'confirmed':True})
    assert s.resolve(source)==source
    assert len(client.get('/api/v1/platform/'+kind).json['items'])==len(before['items'])


def test_undo_keeps_later_edits_and_does_not_republish_draft(client):
    source,target=pair(client,published=False)
    data,p=ready({'action':'merge','source':source,'target':target,'reason':'Reviewed grouping'})
    result=s.apply({**data,'review_token':p['review_token'],'confirmed':True})
    item=ws.detail('watch',target);item['draft']['introduction']='Later independently edited description'
    ws.save('watch',target,item);publish(client,'watch',target)
    undo={'action':'undo','source':source,'target':target,'merge_id':result['id'],'restore_target':True,'reason':'Restore source without discarding later edits'}
    assert not s.preview(undo)['ready']
    undo['restore_target']=False;p=s.preview(undo);assert p['ready']
    s.apply({**undo,'review_token':p['review_token'],'confirmed':True})
    assert ws.detail('watch',target)['published']['introduction']=='Later independently edited description'
    assert ws.detail('watch',source)['published'] is None


def test_relation_private_preview_both_directions_and_scope(client):
    migrate(client)
    d={'action':'relation','source':'D-01','target':'CW-M01','relation':'release','evidence':'https://example.org/official-release','version':'v2','reason':'Verified relationship'}
    before=s.public_status('D-01');p=s.preview(d);assert p['ready']
    assert s.public_status('D-01')==before
    s.apply({**d,'review_token':p['review_token'],'confirmed':True})
    a=client.get('/api/v1/platform/news?id=D-01').json['items'][0]['maintenance']
    b=client.get('/api/v1/platform/watch?id=CW-M01').json['items'][0]['maintenance']
    assert a['relationships'][0]['direction']=='outgoing' and b['relationships'][0]['direction']=='incoming'
    assert a['relationships'][0]['evidence']==d['evidence']
    ext={**d,'target':'','relation':'publisher','target_name':'Example company','target_url':'https://example.org','node_type':'company'}
    p=s.preview(ext);s.apply({**ext,'review_token':p['review_token'],'confirmed':True})
    assert len(s.public_status('D-01')['relationships'])==2
    assert client.get('/api/v1/admin/workspace/stewardship').status_code==401
    out=rpc(client,'curated_changes',{'scope':'workspace'})
    assert not out.get('isError')
    events=s.changes(limit=1);assert events['has_more']
    first=events['items'][0]['id'];nextpage=s.changes(limit=1,cursor=events['next_cursor']);assert nextpage['items'][0]['id']!=first
    with pytest.raises(PlatformError):s.changes(limit=2,cursor=events['next_cursor'])


def material(client):
    migrate(client);with_material(client);publish(client,'watch','CW-M01')
    return 'CW-M01','readme','https://example.org/README.md'

def at(day):return f'2026-09-{day:02d}T01:00:00+00:00'
FAIL={'ok':False,'error':'HTTP 429'}
OK={'ok':True,'hash':'first-body','final_url':'https://example.org/README.md'}


def test_natural_days_thresholds_recovery_keep_frozen_body(client):
    args=material(client);before=cm.read(args[0],args[1]);rev=before['content_revision']
    for _ in range(5):v=s.observe(*args,FAIL,at(1))
    assert v['failure_days']==1 and not v['needs_review']
    s.observe(*args,FAIL,at(2));v=s.observe(*args,FAIL,at(3));assert v['failure_days']==3 and v['needs_review'] and v['review_priority']==1
    for day in range(4,8):v=s.observe(*args,FAIL,at(day))
    assert v['failure_days']==7 and v['review_priority']==0
    assert cm.read(args[0],args[1])['body']==before['body']
    v=s.observe(*args,OK,at(8));assert v['failure_days']==0 and v['last_success_at']==at(8)
    assert cm.read(args[0],args[1])['content_revision']==rev
    events=s.changes(limit=100);assert any(e['kind']=='material_recovered' for e in events['items'])
    s.observe(*args,FAIL,at(8));assert s.public_status(args[0])['materials'][0]['failure_days']==0
    s.observe(*args,FAIL,at(10));assert s.public_status(args[0])['materials'][0]['failure_days']==1


def test_change_ack_deferral_and_public_private_boundary(client,monkeypatch):
    args=material(client);s.observe(*args,OK,at(1));v=s.observe(*args,{**OK,'hash':'new-body'},at(2))
    assert v['changed'] and v['needs_review']
    d={'id':args[0],'material_id':args[1],'check_revision':s.digest(v),'decision':'defer','reason':'PRIVATE-DEFER-NOTE','review_after':'2026-09-30'}
    s.decide_material(d);assert not s.dashboard()['issues']
    assert 'PRIVATE-DEFER-NOTE' not in json.dumps(s.public_status(args[0]))
    v=s.observe(*args,{**OK,'hash':'third-body'},at(3));assert v['needs_review'] and not v.get('review_after')
    assert s.dashboard()['issues']
    with pytest.raises(PlatformError):s.decide_material({**d,'decision':'reviewed'})
    s.decide_material({**d,'check_revision':s.digest(v),'decision':'reviewed','reason':'The updated document has been reviewed'})
    v=s.observe(*args,{**OK,'hash':'third-body'},at(4));assert not v['needs_review']


def test_old_material_links_permissions_after_merge_and_cursor_redaction(client):
    source,target=pair(client);with_material(client,source);publish(client,'watch',source)
    before=cm.read(source,'readme');rev=before['content_revision']
    data,p=ready({'action':'merge','source':source,'target':target,'reason':'Verified same project'})
    s.apply({**data,'review_token':p['review_token'],'confirmed':True})
    assert cm.read(source,'readme',rev)['body']==before['body']
    assert cm.read(source,'readme',rev)['maintenance']['canonical_id']==target
    item=ws.detail('watch',target);item['draft']['reading_materials']=[];ws.save('watch',target,item);publish(client,'watch',target)
    with pytest.raises(PlatformError):cm.read(source,'readme',rev)
    p=ws.preview('watch',target);ws.publish('watch',target,{'draft_version':p['draft_version'],'reason':'Withdraw test'},True)
    assert s.public_status(source)['availability']=='unavailable'


def test_failed_recheck_cannot_resurrect_withdrawn_item(client,monkeypatch):
    args=material(client);p=ws.preview('watch',args[0]);ws.publish('watch',args[0],{'draft_version':p['draft_version'],'reason':'Withdraw'},True)
    assert s.observe(*args,OK,at(5))['status']=='discarded'
    assert s.public_status(args[0])['availability']=='unavailable'


def test_check_uses_allowed_fetch_and_records_no_body(client,monkeypatch):
    args=material(client);calls=[]
    def fetch(url,**kwargs):calls.append(url);return b'<html>public text</html>',url,'text/html'
    monkeypatch.setattr('backend.knowledge.sources.fetch',fetch)
    out=s.check_materials(3,args[0]);assert out['results'] and calls
    with get_db() as db:stored=db.execute('SELECT data FROM fieldtofit_steward_checks').fetchone()[0]
    assert 'public text' not in stored
    assert cm.read(args[0],args[1])['body'].startswith('SOURCE-ONLY')


def test_remote_buffered_merge_has_no_reads_after_writes(client,monkeypatch):
    from contextlib import contextmanager
    from backend.knowledge.workspace_transactions import GuardedWrites
    source,target=pair(client)
    @contextmanager
    def buffered():
        with get_db() as db:
            g=GuardedWrites(db);yield g
            for sql,args in g.writes:db.execute(sql,args)
    monkeypatch.setattr(s,'editorial_transaction',buffered)
    data,p=ready({'action':'merge','source':source,'target':target,'reason':'Remote transaction shape'})
    s.apply({**data,'review_token':p['review_token'],'confirmed':True})
    assert s.resolve(source)==target


def test_private_group_never_publishes(client):
    source,target=pair(client,published=False)
    before=client.get('/api/v1/platform/watch').json
    data,p=ready({'action':'group','source':source,'target':target,'reason':'Candidate grouped for private review'})
    s.apply({**data,'review_token':p['review_token'],'confirmed':True})
    assert client.get('/api/v1/platform/watch').json==before
    assert ws.detail('watch',source)['published'] is None
    assert ws.detail('watch',target)['has_changes']
    assert s.resolve(source)==source


def test_stale_source_evidence_invalidates_merge(client):
    source,target=pair(client)
    data,p=ready({'action':'merge','source':source,'target':target,'reason':'Preview races source edit'})
    d=ws.detail('watch',source);d['draft']['introduction']='Edited after preview';ws.save('watch',source,d)
    with pytest.raises(PlatformError):s.apply({**data,'review_token':p['review_token'],'confirmed':True})
    assert s.resolve(source)==source


def test_removed_material_status_and_threshold_escalation(client,monkeypatch):
    args=material(client)
    for day in range(1,4):v=s.observe(*args,FAIL,at(day))
    s.decide_material({'id':args[0],'material_id':args[1],'check_revision':s.digest(v),'decision':'defer','reason':'Wait for source recovery','review_after':'2026-09-30'})
    for day in range(4,8):v=s.observe(*args,FAIL,at(day))
    assert not v.get('review_after') and s.dashboard()['issues']
    item=ws.detail('watch',args[0]);item['draft']['reading_materials']=[];ws.save('watch',args[0],item);publish(client,'watch',args[0])
    assert not s.public_status(args[0])['materials'] and not s.dashboard()['issues']
    assert any(e['kind']=='material_withdrawn' for e in s.changes(limit=100)['items'])


def test_merge_preserves_older_material_revision_and_restores_source_links(client):
    source,target=pair(client);with_material(client,source);publish(client,'watch',source)
    original=cm.read(source,'readme')
    d=ws.detail('watch',source);d['draft']['reading_materials'][0]['body']+=' New revision.';ws.save('watch',source,d);publish(client,'watch',source)
    with get_db() as db:
        db.execute('INSERT INTO fieldtofit_item_sources VALUES(?,?,?)',('watch',source,'fixture-source-reference'))
    data,p=ready({'action':'merge','source':source,'target':target,'reason':'Verified same project'})
    result=s.apply({**data,'review_token':p['review_token'],'confirmed':True})
    assert cm.read(source,'readme',original['content_revision'])['body']==original['body']
    undo={'action':'undo','source':source,'target':target,'merge_id':result['id'],'restore_target':True,'reason':'Restore initial associations'}
    p=s.preview(undo);assert p['ready'],p['errors'];s.apply({**undo,'review_token':p['review_token'],'confirmed':True})
    with get_db() as db:
        assert db.execute('SELECT item_id FROM fieldtofit_item_sources WHERE ref=?',('fixture-source-reference',)).fetchall()[0][0]==source
        assert db.execute('SELECT COUNT(*) FROM fieldtofit_item_sources WHERE ref=?',('fixture-source-reference',)).fetchone()[0]==1


def test_relation_removal_and_old_change_snapshot_redaction(client):
    args=material(client);v=s.observe(*args,FAIL,at(1))
    s.decide_material({'id':args[0],'material_id':args[1],'check_revision':s.digest(v),'decision':'retain','reason':'PUBLIC-NOTE-TO-REDACT'})
    first=s.changes(limit=1);assert first['has_more']
    d={'action':'relation','source':'D-01','target':args[0],'relation':'related','evidence':'https://example.org/relation','reason':'Verified relationship'}
    p=s.preview(d);s.apply({**d,'review_token':p['review_token'],'confirmed':True})
    lid=s.public_status('D-01')['relationships'][0]['id']
    d={'action':'relation_remove','source':'D-01','link_id':lid,'reason':'Incorrect relationship'}
    p=s.preview(d);s.apply({**d,'review_token':p['review_token'],'confirmed':True})
    assert not s.public_status('D-01')['relationships'] and not s.public_status(args[0])['relationships']
    p=ws.preview('watch',args[0]);ws.publish('watch',args[0],{'draft_version':p['draft_version'],'reason':'Withdraw'},True)
    page=first
    while page['has_more']:
        page=s.changes(limit=1,cursor=page['next_cursor'])
        assert 'PUBLIC-NOTE-TO-REDACT' not in json.dumps(page)


def test_private_group_can_hold_unapproved_material_without_publishing(client):
    source,target=pair(client,published=False)
    d=ws.detail('watch',source);d['draft']['reading_materials']=[{**mat(),'approved':False}]
    ws.save('watch',source,d)
    before=client.get('/api/v1/platform/watch').json
    data,p=ready({'action':'group','source':source,'target':target,'reason':'Materials still need review'})
    assert p['extra']['publication_blocker']
    s.apply({**data,'review_token':p['review_token'],'confirmed':True})
    assert client.get('/api/v1/platform/watch').json==before
    assert any(not m['approved'] for m in ws.detail('watch',target)['draft']['reading_materials'])
    assert not ws.preview('watch',target)['ready']
    assert not any({v['source'],v['target']}=={source,target} for v in s.suggestions())


@pytest.mark.parametrize('race',[False,True])
def test_actual_remote_merge_transaction_guard(client,monkeypatch,race):
    from contextlib import contextmanager
    from backend.db import TursoConnection,TursoCursor
    from backend.knowledge import workspace_transactions as tx
    source,target=pair(client)
    data,p=ready({'action':'merge','source':source,'target':target,'reason':'Atomic merge acceptance'})
    before=client.get('/api/v1/platform/watch').json
    class RemoteSQL(TursoConnection):
        def __init__(self,db):self.db=db
        def execute(self,sql,params=()):return TursoCursor(self.db.execute(sql,params).fetchall(),0,None)
        def atomic_statements(self,statements):
            if race:
                self.db.execute('UPDATE fieldtofit_content_items SET draft_version=draft_version+1 WHERE id=?',(source,));self.db.commit()
            self.db.execute('BEGIN IMMEDIATE')
            try:
                result=[]
                for sql,args in statements:
                    cursor=self.db.execute(sql,args);result.append(TursoCursor(cursor.fetchall(),cursor.rowcount,None))
                self.db.commit();return result
            except Exception:self.db.rollback();raise
    @contextmanager
    def remote():
        with get_db() as db:yield RemoteSQL(db)
    monkeypatch.setattr(tx,'get_db',remote)
    if race:
        with pytest.raises(PlatformError):s.apply({**data,'review_token':p['review_token'],'confirmed':True})
        assert s.resolve(source)==source
        assert client.get('/api/v1/platform/watch').json==before
        with get_db() as db:assert not db.execute('SELECT id FROM fieldtofit_steward_actions').fetchall()
    else:
        s.apply({**data,'review_token':p['review_token'],'confirmed':True})
        assert s.resolve(source)==target
        with get_db() as db:assert db.execute("SELECT 1 FROM fieldtofit_operation_events WHERE ref=? AND action='published_update'",('watch:'+target,)).fetchone()


@pytest.mark.parametrize('published',[False,True])
def test_undo_restores_editorial_topic_state(client,published):
    source,target=pair(client,published=published)
    previous='published' if published else 'continue'
    with get_db() as db:db.execute('INSERT INTO fieldtofit_editorial_topics(id,event_key,event_url,fingerprint,proposal,decision,kind,item_id,updated_at) VALUES(?,?,?,?,?,?,?,?,?)',('fixture-topic','fixture-event','https://example.org/event','fixture','{}',previous,'watch',source,ws.stamp()))
    data,p=ready({'action':'merge','source':source,'target':target,'reason':'Reviewed duplicate'})
    merged=s.apply({**data,'review_token':p['review_token'],'confirmed':True})
    with get_db() as db:assert db.execute('SELECT decision FROM fieldtofit_editorial_topics WHERE id=?',('fixture-topic',)).fetchone()[0]=='withdrawn'
    data={'action':'undo','source':source,'target':target,'merge_id':merged['id'],'reason':'Restore original topic'}
    p=s.preview(data);s.apply({**data,'review_token':p['review_token'],'confirmed':True})
    with get_db() as db:assert db.execute('SELECT decision FROM fieldtofit_editorial_topics WHERE id=?',('fixture-topic',)).fetchone()[0]==previous
