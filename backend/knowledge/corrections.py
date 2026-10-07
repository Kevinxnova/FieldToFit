"""Location-bound private reports and explicitly reviewed public resolution receipts."""
import json
import re
import uuid
from backend.db import get_db
from backend.knowledge import content_workspace as ws, stewardship as s
from backend.knowledge.workspace_transactions import editorial_transaction
from backend.knowledge.platform import integer, text

FIELDS = {'name','title','summary','introduction','blocks','interpretation','sources','aliases','submission'}
STATES = {'pending','reviewing','ready','publishing','resolved','declined'}


def value_at(item, field):
    if not isinstance(field, str) or field.split('.')[0] not in FIELDS or len(field)>200: ws.fail('请选择公开内容字段')
    value = item
    try:
        for part in field.split('.'):
            value = value[int(part)] if isinstance(value, list) and part.isdigit() else value[part]
    except (KeyError, IndexError, TypeError): ws.fail('字段不在此公开修订中', 'field_not_found', 404)
    return value


def public_item(ident, db):
    kind = s.kind(ident); item = s.raw_items(db).get(ident)
    if not item or item.get('state') != 'published' or s.resolve(ident, db)!=ident: ws.fail('内容未公开或已归并', 'not_found', 404)
    projected = ws.render(kind, {**ws.seeds()[kind], 'items':[item]})['items'][0]
    projected.pop('maintenance', None); projected.pop('publication', None)
    return projected


def context(ident, field='introduction', material_id='', content_revision='', start=0, end=None):
    with get_db() as db:
        item = public_item(ident, db)
        row = db.execute("SELECT MAX(seq) seq FROM fieldtofit_content_history WHERE item_id=? AND action IN ('import','publish')", (ident,)).fetchone()
    result = {'object_id': ident, 'field': field, 'publication_revision': row['seq'], 'baseline_hash': s.digest(item)}
    if material_id:
        from backend.knowledge.content_materials import _load, normalize, manifest
        raw = _load(ident, content_revision); revision = manifest(raw)['materials_revision']
        material = next((m for m in normalize(raw) if m['id']==material_id), None)
        if not material or not material['body']: ws.fail('原文不可读取', 'material_unavailable', 410)
        start = integer(start, 'start', 0, len(material['body']))
        end = integer(end if end is not None else min(start+2000,len(material['body'])), 'end', start, min(start+4000,len(material['body'])))
        result.update(field='material', material_id=material_id, content_revision=revision, content_hash=material['content_hash'],
                      source_url=material['url'], start=start, end=end, quoted_text=material['body'][start:end], value=item['interpretation'])
    else:
        result['value'] = value_at(item, field)
    return result


def submit(data):
    supplied = data.get('context')
    if not isinstance(supplied, dict): ws.fail('缺少纠错位置')
    actual = context(supplied.get('object_id'), supplied.get('field','introduction'), supplied.get('material_id',''),
                     supplied.get('content_revision',''), supplied.get('start',0), supplied.get('end'))
    if actual != supplied: ws.fail('资料或位置已变化，请重新核对报告位置', 'correction_conflict', 409)
    report = text(data.get('content'), '问题说明', 12000)
    contact = text(data.get('contact',''), '联系方式', 500, False)
    fid = int(uuid.uuid4().int % (2**52))
    with editorial_transaction() as db:
        # The same baseline is guarded again across remote writes.
        if s.digest(public_item(actual['object_id'], db)) != actual['baseline_hash']: ws.fail('资料已更新，请重读', 'correction_conflict', 409)
        db.execute('INSERT INTO knowledge_feedback(id,record_id,category,content,created_at) VALUES(?,?,?,?,?)', (fid,actual['object_id'],'correction',report,ws.stamp()))
        db.execute('INSERT INTO fieldtofit_correction_contexts VALUES(?,?,?,\'pending\',1,\'{}\',?)', (fid,actual['object_id'],ws.dump({**actual,'contact':contact}),ws.stamp()))
    return {'ok': True, 'id': fid, 'status':'pending'}


def detail(fid):
    with get_db() as db:
        row = db.execute('SELECT * FROM fieldtofit_correction_contexts WHERE feedback_id=?',(fid,)).fetchone()
        if not row: ws.fail('纠错报告不存在','not_found',404)
        data = dict(row); data['context']=json.loads(data.pop('data')); data['resolution']=json.loads(data['resolution'])
        data['history']=[{**dict(r),'data':json.loads(r['data'])} for r in db.execute('SELECT * FROM fieldtofit_correction_events WHERE feedback_id=? ORDER BY created_at,id',(fid,)).fetchall()]
        try:
            current = public_item(data['object_id'],db)
            data['current_value'] = value_at(current,data['context']['field']) if data['context']['field']!='material' else None
            data['changed_since_report']=s.digest(current)!=data['context']['baseline_hash']
        except ws.PlatformError:
            data['current_unavailable']=True
    return data


def handle(fid, data):
    state = data.get('status'); note = text(data.get('resolution'), '内部处理说明', 6000)
    if state not in STATES: ws.fail('未知纠错状态')
    with editorial_transaction() as db:
        row = db.execute('SELECT * FROM fieldtofit_correction_contexts WHERE feedback_id=?',(fid,)).fetchone()
        if not row: ws.fail('纠错报告不存在','not_found',404)
        if data.get('version')!=row['version']: ws.fail('处理记录已变化，请重新读取','correction_conflict',409)
        ctx=json.loads(row['data']); receipt={'internal_note':note}
        if state=='resolved':
            if data.get('confirmed') is not True: ws.fail('请确认公开更正说明')
            seq=integer(data.get('fixed_revision'),'fixed_revision',1)
            fixed=db.execute("SELECT snapshot,created_at FROM fieldtofit_content_history WHERE item_id=? AND seq=? AND action='publish'",(row['object_id'],seq)).fetchone()
            withdrawn=db.execute("SELECT MAX(seq) seq FROM fieldtofit_content_history WHERE item_id=? AND action='withdraw'",(row['object_id'],)).fetchone()['seq'] or 0
            if not fixed or seq <= (ctx['publication_revision'] or 0): ws.fail('必须关联报告之后的实际发布修订')
            if seq <= withdrawn: ws.fail('所选修复修订已撤回，请核对重新公开的修订')
            public_item(row['object_id'],db)
            snapshot=json.loads(fixed['snapshot'])
            if snapshot.get('state')!='published': ws.fail('修复修订不可公开')
            kind=s.kind(row['object_id'])
            fixed_public=ws.render(kind,{**ws.seeds()[kind],'items':[snapshot]})['items'][0]
            if ctx['field']=='material':
                old=ctx['content_hash']; material=next((m for m in snapshot.get('reading_materials',[]) if m['id']==ctx['material_id']),None)
                import hashlib
                if material and hashlib.sha256(material.get('body','').encode()).hexdigest()==old and fixed_public.get('interpretation')==ctx['value']:
                    ws.fail('原文与引用解读尚未修复；请修订引用说明或说明不采纳')
            elif value_at(fixed_public,ctx['field'])==ctx['value']: ws.fail('该字段尚未在所选修订中修复')
            receipt.update(fixed_revision=seq, published_at=fixed['created_at'], field=ctx['field'], public_note=text(data.get('public_note'),'公开更正说明',2000),
                           sources=[{'title':m['title'],'url':m['url']} for m in fixed_public.get('sources',[])])
        db.execute('UPDATE fieldtofit_correction_contexts SET status=?,version=version+1,resolution=?,updated_at=? WHERE feedback_id=?',(state,ws.dump(receipt),ws.stamp(),fid))
        db.execute('INSERT INTO fieldtofit_correction_events VALUES(?,?,?,?,?)',(uuid.uuid4().hex,fid,state,ws.dump(receipt),ws.stamp()))
    return detail(fid)


def public(ident):
    with get_db() as db:
        public_item(ident,db)
        rows=db.execute("SELECT resolution FROM fieldtofit_correction_contexts WHERE object_id=? AND status='resolved' AND json_extract(resolution,'$.fixed_revision')>COALESCE((SELECT MAX(seq) FROM fieldtofit_content_history WHERE item_id=? AND action='withdraw'),0) ORDER BY updated_at DESC",(ident,ident)).fetchall()
    return {'id':ident,'items':[{k:v for k,v in json.loads(r['resolution']).items() if k!='internal_note'} for r in rows]}
