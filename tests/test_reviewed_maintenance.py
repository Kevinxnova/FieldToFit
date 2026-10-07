"""New maintenance contracts on isolated data, with no live network or publications."""
import copy
import hashlib
import io
import json
from datetime import timedelta,date
import pytest
from test_knowledge import client, ADMIN, MCP
from test_content_workspace import migrate,call,publish
from test_editorial_v130 import mat
from backend.db import get_db
from backend.knowledge import content_workspace as ws,content_materials as cm,object_checks as checks,corrections as c,content_revisions as rev
from backend.knowledge.platform import PlatformError

ID='CW-T01'
URL='https://example.org/guide'

def prepare(client,body='# Guide\n\nIntroduction 🧭.\n\n## Install\n\nFirst step.\n\n## Usage\n\nSecond step.\n',pdf=None):
    migrate(client)
    d=ws.detail('watch',ID)
    material=mat(body=body,locator='README.md');material['id']='guide';material['url']=URL
    if pdf:material.update(pdf)
    d['draft']['reading_materials']=[material]
    ws.save('watch',ID,d);publish(client,'watch',ID)
    return cm.object_data(ID)

def rpc(client,name,args):
    return client.post('/api/mcp/curated',headers=MCP,json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':args}}).json

def configured(client,monkeypatch,fail=False):
    migrate(client)
    checks.configure(ID,{'entries':[{'url':URL,'title':'Official guide','required':True,'scope':'Versions and access'}]})
    checks.start()
    def fetch(url,**kw):
        if fail:raise ValueError('Source unavailable')
        return b'# Guide\nNew verified feature.\n',url,'text/plain'
    monkeypatch.setattr('backend.knowledge.sources.fetch',fetch)
    return checks.scan(ws.today(),ID)

def review(result,changed=True,completed=True):
    return {'attempt_id':result['attempt_id'],'completed':completed,'reason':'Compared registered version and access statements against published dossier.',
            'changes':[{'field':'introduction','before':result['baseline']['introduction'],'after':'A changed official feature.','source_url':URL,'quote':'New verified feature.'}] if changed else []}

def test_daily_full_scope_fetch_not_approval_and_no_public_mutation(client,monkeypatch):
    before=client.get('/api/v1/platform/watch').json
    result=configured(client,monkeypatch)
    board=checks.overview();assert board['totals']['expected']==49
    assert board['totals']['completed']==0 and result['status']=='incomplete'
    checks.review(ws.today(),ID,review(result))
    board=checks.overview();assert board['totals']['changed']==1 and board['totals']['completed']==1
    assert client.get('/api/v1/platform/watch').json==before
    assert checks.start()['created_at']==board['created_at']

def test_failure_partial_change_and_retry_history_remain(client,monkeypatch):
    result=configured(client,monkeypatch);checks.review(ws.today(),ID,review(result))
    monkeypatch.setattr('backend.knowledge.sources.fetch',lambda *a,**k:(_ for _ in ()).throw(ValueError('HTTP 429')))
    failed=checks.scan(ws.today(),ID)
    assert failed['status']=='failed' and failed['changes'][0]['pending_from_previous']
    with pytest.raises(PlatformError):checks.review(ws.today(),ID,review(failed,False))
    board=checks.review(ws.today(),ID,review(failed,False,False))
    target=next(r for r in board['items'] if r['id']==ID)
    assert target['latest']['changes'] and len(target['history'])==4

def test_unchanged_does_not_clear_pending_and_baseline_changes_invalidate(client,monkeypatch):
    result=configured(client,monkeypatch);checks.review(ws.today(),ID,review(result))
    second=checks.scan(ws.today(),ID);board=checks.review(ws.today(),ID,review(second,False))
    assert board['totals']['changed']==1
    d=ws.detail('watch',ID);d['draft']['introduction']='A changed official feature.';ws.save('watch',ID,d);publish(client,'watch',ID)
    assert checks.overview()['totals']['completed']==0
    with pytest.raises(PlatformError):checks.review(ws.today(),ID,review(second))
    fresh=checks.scan(ws.today(),ID);assert fresh['changes']==[]

def test_plan_freeze_next_day_scope_and_no_historical_invention(client,monkeypatch):
    configured(client,monkeypatch)
    checks.configure(ID,{'version':1,'entries':[{'url':'https://example.org/new','title':'New','required':True,'scope':'Next plan'}]})
    assert next(r for r in checks.overview()['items'] if r['id']==ID)['entries'][0]['url']==URL
    with pytest.raises(PlatformError):checks.start((date.fromisoformat(ws.today())-timedelta(days=1)).isoformat())
    tomorrow=(date.fromisoformat(ws.today())+timedelta(days=1)).isoformat();monkeypatch.setattr(ws,'today',lambda:tomorrow)
    assert next(r for r in checks.start()['items'] if r['id']==ID)['entries'][0]['url'].endswith('/new')


def test_next_day_rechecks_the_dossier_and_carries_unresolved_findings(client,monkeypatch):
    result=configured(client,monkeypatch);checks.review(ws.today(),ID,review(result))
    next_day=(date.fromisoformat(ws.today())+timedelta(days=1)).isoformat();monkeypatch.setattr(ws,'today',lambda:next_day)
    assert checks.start()['totals']['completed']==0
    fresh=checks.scan(next_day,ID);assert fresh['changes'][0]['pending_from_previous']
    assert fresh['baseline_hash']==result['baseline_hash']
    assert checks.review(next_day,ID,review(fresh,False))['totals']['changed']==1

def test_stale_attempt_bad_quote_and_prepublication_values_rejected(client,monkeypatch):
    result=configured(client,monkeypatch)
    bad=review(result);bad['changes'][0]['quote']='Invented quote'
    with pytest.raises(PlatformError):checks.review(ws.today(),ID,bad)
    bad=review(result);bad['changes'][0]['before']='Not the approved value'
    with pytest.raises(PlatformError):checks.review(ws.today(),ID,bad)
    checks.scan(ws.today(),ID)
    with pytest.raises(PlatformError):checks.review(ws.today(),ID,review(result))

def test_update_proposal_is_private_and_no_draft_creation(client,monkeypatch):
    result=configured(client,monkeypatch);checks.review(ws.today(),ID,review(result))
    before=ws.detail('watch',ID)
    r=call(client,f'/object-checks/{ID}/proposal',{'day':ws.today()});assert r.status_code==200,r.json
    repeat=call(client,f'/object-checks/{ID}/proposal',{'day':ws.today()});assert repeat.status_code==200
    assert ws.detail('watch',ID)==before
    assert 'fieldtofit_object_check_attempts' in call(client,'/backup',method='get').json['tables']

def test_locations_exact_sections_unicode_continuation_and_mcp(client):
    manifest=prepare(client);revision=manifest['materials_revision']
    directory=cm.locations(ID,'guide',revision);assert len(directory['sections'])==3
    first=cm.read(ID,'guide',revision,0,5,'section-2')
    text=first['body'];part=first
    while part['has_more']:
        part=cm.read(ID,'guide',revision,part['next_offset'],5,'section-2');text+=part['body']
    assert text=='## Install\n\nFirst step.\n\n'
    assert first['citation']['source_url']==URL
    assert rpc(client,'curated_locations',{'id':ID,'material_id':'guide','content_revision':revision})['result']['structuredContent']==directory
    args={'id':ID,'material_id':'guide','content_revision':revision,'location_id':'section-2','limit':5}
    assert rpc(client,'curated_material',args)['result']['structuredContent']==first
    with pytest.raises(PlatformError):cm.read(ID,'guide',revision,0,10,'section-999')
    with pytest.raises(PlatformError):cm.read(ID,'guide',revision,999,10,'section-2')

def test_fenced_heading_html_and_old_material_revision(client):
    from backend.knowledge.material_locations import index
    assert [s['title'] for s in index('# Real\n```sh\n# code\n```\n## Next\n')['sections']]==['Real','Next']
    assert [s['title'] for s in index('# Real\n````md\n```\n## code\n````\n## Next\n')['sections']]==['Real','Next']
    assert index('```html\n<h2>Example</h2>\n```\n')['sections']==[]
    assert index('<h2>Hello &amp; world</h2><p>Body</p>')['sections'][0]['title']=='Hello & world'
    manifest=prepare(client);revision=manifest['materials_revision'];old=cm.locations(ID,'guide',revision)
    d=ws.detail('watch',ID);d['draft']['reading_materials'][0]['body']='# Changed\nDifferent';ws.save('watch',ID,d);publish(client,'watch',ID)
    assert cm.locations(ID,'guide',revision)==old
    assert cm.read(ID,'guide',revision)['body'].startswith('# Guide')

def pdf_bytes():
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject,NameObject,DictionaryObject,NumberObject
    writer=PdfWriter()
    page=writer.add_blank_page(200,200)
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
    stream=DecodedStreamObject();stream.set_data(b'BT /F1 12 Tf 10 100 Td (First page text) Tj ET')
    page[NameObject('/Contents')]=writer._add_object(stream)
    scan=writer.add_blank_page(200,200)
    image=DecodedStreamObject();image.set_data(b'\x00\x00\x00')
    image.update({NameObject('/Type'):NameObject('/XObject'),NameObject('/Subtype'):NameObject('/Image'),NameObject('/Width'):NumberObject(1),NameObject('/Height'):NumberObject(1),NameObject('/ColorSpace'):NameObject('/DeviceRGB'),NameObject('/BitsPerComponent'):NumberObject(8)})
    resources=DictionaryObject({NameObject('/XObject'):DictionaryObject({NameObject('/Img'):writer._add_object(image)})})
    scan[NameObject('/Resources')]=writer._add_object(resources)
    content=DecodedStreamObject();content.set_data(b'q 100 0 0 100 0 0 cm /Img Do Q');scan[NameObject('/Contents')]=writer._add_object(content)
    writer.set_page_label(0,0,style='/r',start=1)
    writer.set_page_label(1,1,style='/D',start=5)
    out=io.BytesIO();writer.write(out);return out.getvalue()

def test_pdf_page_labels_blank_scan_gaps_and_import_approval(client):
    from backend.knowledge.material_locations import extract_pdf,validate
    pdf=extract_pdf(pdf_bytes());pages=pdf['location_index']['pages']
    assert len(pages)==2 and pages[0]['page']==1
    assert pages[0]['label']=='i' and pages[1]['page']==2 and pages[1]['label']=='5'
    assert 'no_text_layer' in pages[1]['gaps'] and 'formula_layout_unverified' in pages[0]['gaps']
    assert 'images_not_extracted' in pages[1]['gaps']
    r=client.post('/api/v1/admin/workspace/materials/pdf-extract',headers=ADMIN,data={'file':(io.BytesIO(pdf_bytes()),'fixture.pdf')});assert r.status_code==200,r.json
    manifest=prepare(client,pdf=pdf);revision=manifest['materials_revision']
    assert 'First page text' in cm.read(ID,'guide',revision,location_id='page-1')['body']
    assert cm.read(ID,'guide',revision,location_id='page-2')['body']==''
    bad=copy.deepcopy(pdf['location_index']);bad['pages'][0]['end']=999999
    with pytest.raises(PlatformError):validate(pdf['body'],bad)
    with pytest.raises(ValueError):extract_pdf(b'not a pdf')
    invalid=client.post('/api/v1/admin/workspace/materials/pdf-extract',headers=ADMIN,data={'file':(io.BytesIO(b'not a pdf'),'bad.pdf')})
    assert invalid.status_code==400
    from pypdf import PdfWriter
    blank=PdfWriter();blank.add_blank_page(200,200);blank.add_blank_page(200,200);buffer=io.BytesIO();blank.write(buffer)
    scan=extract_pdf(buffer.getvalue());assert scan['coverage']=='link_only' and scan['body']==''
    assert len(scan['location_index']['pages'])==2

def test_location_revocation_blocks_old_indices_and_comparisons(client):
    manifest=prepare(client);old=manifest['materials_revision']
    d=ws.detail('watch',ID);d['draft']['reading_materials']=[];ws.save('watch',ID,d);publish(client,'watch',ID)
    with pytest.raises(PlatformError):cm.locations(ID,'guide',old)
    comp=rev.compare(ID);assert 'Source material' not in json.dumps(comp)
    materials=next(f for f in comp['fields'] if f['field']=='materials')
    assert materials['before'][0]['coverage']=='withdrawn'

def test_correction_submission_private_context_conflict_and_resolution_receipt(client):
    prepare(client);context=c.context(ID)
    result=client.post('/api/v1/feedback',json={'context':context,'content':'PRIVATE REPORT TEXT','contact':'private@example.org'});assert result.status_code==201,result.json
    fid=result.json['id'];d=c.detail(fid)
    assert c.public(ID)['items']==[]
    with pytest.raises(PlatformError):c.handle(fid,{'status':'resolved','version':1,'resolution':'private note','confirmed':True,'fixed_revision':context['publication_revision'],'public_note':'A correction'})
    draft=ws.detail('watch',ID);draft['draft']['introduction']='Corrected reviewed introduction.';ws.save('watch',ID,draft);publish(client,'watch',ID)
    fixed=ws.detail('watch',ID)['history'][0]['seq']
    with pytest.raises(PlatformError):c.submit({'context':context,'content':'Old position'})
    resolved=c.handle(fid,{'status':'resolved','version':1,'resolution':'PRIVATE INTERNAL NOTE','confirmed':True,'fixed_revision':fixed,'public_note':'Corrected the introduction using official evidence.'})
    public=c.public(ID)
    assert public['items'][0]['fixed_revision']==fixed
    assert all(secret not in json.dumps(public) for secret in ['PRIVATE','private@example.org'])
    assert resolved['changed_since_report'] and resolved['version']==2
    assert rpc(client,'curated_corrections',{'id':ID})['result']['structuredContent']==public
    assert call(client,'/feedback?status=resolved',method='get').json['items'][0]['handling_status']=='resolved'
    with pytest.raises(PlatformError):c.handle(fid,{'status':'reviewing','version':1,'resolution':'stale'})

def test_material_context_exact_quote_and_annotation_fix(client):
    manifest=prepare(client);ctx=c.context(ID,material_id='guide',content_revision=manifest['materials_revision'],start=0,end=7)
    assert ctx['quoted_text']=='# Guide'
    fid=c.submit({'context':ctx,'content':'Clarify the interpretation, do not rewrite original text.'})['id']
    draft=ws.detail('watch',ID);draft['draft']['interpretation'][0]['text']+=' Corrected annotation.';ws.save('watch',ID,draft);publish(client,'watch',ID)
    fixed=ws.detail('watch',ID)['history'][0]['seq']
    assert c.handle(fid,{'status':'resolved','version':1,'resolution':'Fixed annotation','confirmed':True,'fixed_revision':fixed,'public_note':'Clarified the cited source interpretation.'})['status']=='resolved'
    assert cm.read(ID,'guide',manifest['materials_revision'])['body'].startswith('# Guide')


def test_private_metadata_edit_cannot_close_a_public_field_correction(client):
    prepare(client);ctx=c.context(ID,field='interpretation')
    fid=c.submit({'context':ctx,'content':'Correct public interpretation'})['id']
    draft=ws.detail('watch',ID);draft['draft']['interpretation'][0]['private_note']='Internal-only edit'
    ws.save('watch',ID,draft);publish(client,'watch',ID)
    fixed=ws.detail('watch',ID)['history'][0]['seq']
    assert c.context(ID,field='interpretation')['value']==ctx['value']
    with pytest.raises(PlatformError):c.handle(fid,{'status':'resolved','version':1,'resolution':'Only private note changed','confirmed':True,'fixed_revision':fixed,'public_note':'Incorrectly claiming a repair'})
    assert c.public(ID)['items']==[] and c.detail(fid)['status']=='pending'

def test_history_baseline_same_object_privacy_share_and_mcp(client):
    prepare(client)
    history=rev.history(ID);assert history['items'][-1]['date_basis']=='migration_baseline'
    before=rev.compare(ID);assert 'private_note' not in json.dumps(before)
    assert rpc(client,'curated_revision_compare',{'id':ID})['result']['structuredContent']==before
    assert client.get('/api/v1/platform/content/'+ID+'/compare').json==before
    assert rpc(client,'curated_revisions',{'id':ID})['result']['structuredContent']==history
    with pytest.raises(PlatformError):rev.compare(ID,history['items'][0]['revision'],history['items'][-1]['revision'])
    with pytest.raises(PlatformError):rev.compare('CW-T02',history['items'][-1]['revision'],history['items'][0]['revision'])
    assert 'compare_from=' in before['share_path']
    assert any(f['kind']=='unchanged' for f in rev.compare(ID,include_unchanged=True)['fields'])

def test_withdrawal_blocks_every_new_public_view_and_admin_permissions(client):
    manifest=prepare(client)
    for path in ['/object-checks','/corrections/1']:
        assert client.get('/api/v1/admin/workspace'+path).status_code==401
    d=ws.detail('watch',ID);ws.publish('watch',ID,{'draft_version':d['draft_version'],'reason':'Isolated withdrawal'},True)
    for path in ['/revisions','/compare','/corrections','/correction-context','/materials/guide/locations']:
        assert client.get('/api/v1/platform/content/'+ID+path).status_code==404
    with pytest.raises(PlatformError):rev.history(ID)

def test_read_token_does_not_grant_admin_or_new_tools_bypass(client,monkeypatch):
    prepare(client);monkeypatch.setenv('FIELDTOFIT_READ_TOKEN','reader')
    assert client.get('/api/v1/platform/content/'+ID+'/revisions').status_code==401
    headers={'Authorization':'Bearer reader'}
    assert client.get('/api/v1/platform/content/'+ID+'/revisions',headers=headers).status_code==200
    assert client.post('/api/v1/admin/workspace/object-checks',headers=headers,json={}).status_code==401


def test_republication_does_not_resurrect_withdrawn_correction_receipt(client):
    prepare(client);ctx=c.context(ID);fid=c.submit({'context':ctx,'content':'Fix introduction'})['id']
    draft=ws.detail('watch',ID);draft['draft']['introduction']='Corrected intro';ws.save('watch',ID,draft);publish(client,'watch',ID)
    fixed=ws.detail('watch',ID)['history'][0]['seq']
    receipt={'status':'resolved','version':1,'resolution':'Verified','confirmed':True,'fixed_revision':fixed,'public_note':'Introduction corrected'}
    c.handle(fid,receipt);assert c.public(ID)['items']
    draft=ws.detail('watch',ID);ws.publish('watch',ID,{'draft_version':draft['draft_version'],'reason':'Withdraw fixture'},True)
    draft=ws.detail('watch',ID);ws.save('watch',ID,draft);publish(client,'watch',ID)
    assert c.public(ID)['items']==[]
    with pytest.raises(PlatformError):c.handle(fid,{**receipt,'version':2})


@pytest.mark.parametrize('operation',['review','correction'])
@pytest.mark.parametrize('race',[False,True])
def test_actual_remote_atomic_review_and_correction_guard(client,monkeypatch,operation,race):
    from contextlib import contextmanager
    from backend.db import TursoConnection,TursoCursor
    from backend.knowledge import workspace_transactions as tx
    if operation=='review':
        result=configured(client,monkeypatch)
        action=lambda:checks.review(ws.today(),ID,review(result))
        mutation="UPDATE fieldtofit_object_check_attempts SET data=json_set(data,'$.reason','Concurrent reviewer') WHERE id=?"
        params=(result['attempt_id'],)
    else:
        prepare(client);fid=c.submit({'context':c.context(ID),'content':'Private review'})['id']
        action=lambda:c.handle(fid,{'status':'reviewing','version':1,'resolution':'Verified privately'})
        mutation='UPDATE fieldtofit_correction_contexts SET version=version+1 WHERE feedback_id=?'
        params=(fid,)
    class RemoteSQL(TursoConnection):
        def __init__(self,db):self.db=db
        def execute(self,sql,params=()):return TursoCursor(self.db.execute(sql,params).fetchall(),0,None)
        def atomic_statements(self,statements):
            if race:self.db.execute(mutation,params);self.db.commit()
            self.db.execute('BEGIN IMMEDIATE')
            try:
                results=[]
                for sql,args in statements:
                    cursor=self.db.execute(sql,args);results.append(TursoCursor(cursor.fetchall(),cursor.rowcount,None))
                self.db.commit();return results
            except Exception:self.db.rollback();raise
    @contextmanager
    def remote():
        with get_db() as db:yield RemoteSQL(db)
    monkeypatch.setattr(tx,'get_db',remote)
    if race:
        with pytest.raises(PlatformError) as error:action()
        assert error.value.code=='workspace_conflict'
    else:action()
    if operation=='review':assert checks.overview()['totals']['completed']==(0 if race else 1)
    else:
        detail=c.detail(fid);assert detail['status']==('pending' if race else 'reviewing')
        assert len(detail['history'])==(0 if race else 1)
