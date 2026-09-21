"""Private recommendation ledger. Decisions never implicitly publish content."""
import hashlib
import json
from datetime import date
from backend.db import get_db
from backend.knowledge.content_workspace import dump, stamp, today, fail, text
from backend.knowledge.workspace_transactions import editorial_transaction
from backend.knowledge import store


def _batch(db, ident):
    row=db.execute('SELECT * FROM fieldtofit_editorial_batches WHERE id=?',(ident,)).fetchone()
    if not row: fail('Batch not found','not_found',404)
    return dict(row)


def _topic(db, ident):
    row=db.execute('SELECT * FROM fieldtofit_editorial_topics WHERE id=?',(ident,)).fetchone()
    if not row: fail('Recommendation not found','not_found',404)
    out=dict(row);out['proposal']=json.loads(out['proposal']);return out


def _audit(db, topic, action, payload):
    db.execute('INSERT INTO fieldtofit_editorial_events(topic_id,action,payload,created_at) VALUES(?,?,?,?)',(topic,action,dump(payload),stamp()))


def create(data):
    day=data.get('day',today());date.fromisoformat(day)
    if day>today():fail('Future briefing date')
    ident='brief-'+day
    with editorial_transaction() as db:
        db.execute('INSERT OR IGNORE INTO fieldtofit_editorial_batches(id,day,title,created_at) VALUES(?,?,?,?)',(ident,day,text(data.get('title',day+' 推荐更新'),'title',200),stamp()))
    return detail(ident)


def detail(ident):
    with get_db() as db:
        b=_batch(db,ident)
        ids=[r['topic_id'] for r in db.execute('SELECT topic_id FROM fieldtofit_editorial_members WHERE batch_id=? ORDER BY created_at,topic_id',(ident,)).fetchall()]
        b['items']=[_topic(db,i) for i in ids]
        for t in b['items']:
            t['history']=[dict(r) for r in db.execute('SELECT action,payload,created_at FROM fieldtofit_editorial_events WHERE topic_id=? ORDER BY seq DESC LIMIT 30',(t['id'],)).fetchall()]
    return b


def overview():
    with get_db() as db:
        rows=[dict(r) for r in db.execute('SELECT * FROM fieldtofit_editorial_batches ORDER BY day DESC LIMIT 30').fetchall()]
        due=[_topic(db,r['id']) for r in db.execute("SELECT id FROM fieldtofit_editorial_topics WHERE decision='later' AND review_on<=? ORDER BY review_on LIMIT 100",(today(),)).fetchall()]
    b=next((b for b in rows if b['day']==today()),None)
    return {'items':rows,'due':due,'today':today(),'delivery':b['delivery_state'] if b else 'missing',
            'notice':'今日没有已核实的日报交付记录' if not b or b['delivery_state']!='delivered' else ''}


def propose(ident,data):
    proposal=data.get('proposal',{})
    if not isinstance(proposal,dict):fail('Invalid proposal')
    text(proposal.get('title'),'title',1000);text(proposal.get('reason'),'reason',2000)
    from backend.knowledge.platform_watch import valid_url
    event_url=valid_url(text(data.get('event_url'),'event_url',1600))
    # The caller may give a canonical event URL to merge primary and secondary sources.
    event_key=store.canonical_url(event_url)+'|'+text(data.get('event_version',''),'event_version',200,False)
    fingerprint=text(data.get('fingerprint'),'fingerprint',128)
    topic_id=hashlib.sha256(event_key.encode()).hexdigest()[:24];ref=text(data.get('ref',''),'ref',200,False)
    if len(dump(proposal))>40000:fail('Proposal too large')
    with editorial_transaction() as db:
        _batch(db,ident)
        if ref:
            from backend.knowledge.content_workspace import candidate
            if not candidate(ref,db):fail('Candidate not found','not_found',404)
        old=db.execute('SELECT * FROM fieldtofit_editorial_topics WHERE id=?',(topic_id,)).fetchone()
        if old:
            same=old['fingerprint']==fingerprint and json.loads(old['proposal'])==proposal
            member=db.execute('SELECT 1 FROM fieldtofit_editorial_members WHERE batch_id=? AND topic_id=?',(ident,topic_id)).fetchone()
            due=old['decision']=='later' and old['review_on'] and old['review_on']<=today()
            if same and not member and not due:
                return {'id':topic_id,'suppressed':True,'decision':old['decision'],'reason':'已推荐且没有新证据；保留原批次，不重复提醒'}
            if not same:
                db.execute("UPDATE fieldtofit_editorial_topics SET fingerprint=?,proposal=?,decision='pending',review_on=NULL,version=version+1,updated_at=? WHERE id=?",(fingerprint,dump(proposal),stamp(),topic_id))
                _audit(db,topic_id,'evidence_changed',{'previous_fingerprint':old['fingerprint'],'previous_proposal':json.loads(old['proposal'])})
            elif due:
                db.execute("UPDATE fieldtofit_editorial_topics SET decision='pending',version=version+1,updated_at=? WHERE id=?",(stamp(),topic_id))
                _audit(db,topic_id,'review_due',{'review_on':old['review_on']})
        else:
            db.execute('INSERT INTO fieldtofit_editorial_topics(id,event_key,event_url,fingerprint,proposal,source_ref,updated_at) VALUES(?,?,?,?,?,?,?)',(topic_id,event_key,event_url,fingerprint,dump(proposal),ref,stamp()))
            _audit(db,topic_id,'proposed',{'batch':ident,'fingerprint':fingerprint})
        db.execute('INSERT OR IGNORE INTO fieldtofit_editorial_members VALUES(?,?,?)',(ident,topic_id,stamp()))
    return {'id':topic_id,'suppressed':False}


def decide(ident,data):
    decision=data.get('decision')
    if decision not in ('continue','later','declined'):fail('Invalid decision')
    review_on=data.get('review_on') or None
    if decision=='later':
        if not review_on or date.fromisoformat(review_on)<date.fromisoformat(today()):fail('Choose a future review date')
    else:review_on=None
    with editorial_transaction() as db:
        t=_topic(db,ident)
        if data.get('version')!=t['version']:fail('Recommendation changed; read again','topic_conflict',409)
        db.execute('UPDATE fieldtofit_editorial_topics SET decision=?,review_on=?,version=version+1,updated_at=? WHERE id=?',(decision,review_on,stamp(),ident))
        _audit(db,ident,'decision',{'decision':decision,'note':text(data.get('note',''),'note',2000,False),'fingerprint':t['fingerprint']})
    return {'id':ident,'decision':decision}


def attach(ident,data):
    """Link a confirmed recommendation to an existing editor or selected candidate."""
    from backend.knowledge.content_workspace import select, detail as content_detail
    with editorial_transaction() as db:
        t=_topic(db,ident)
        if t['decision']!='continue' or data.get('version')!=t['version']:fail('Confirm this recommendation before drafting','decision_required',409)
        kind=data.get('kind') or t['kind'] or 'watch';target=data.get('target_id') or t['item_id']
        if kind not in ('watch','news'):fail('Choose news or watch')
        if target:content_detail(kind,target,db)
        elif t['source_ref']:
            linked=select({'ref':t['source_ref'],'action':'select','kind':kind,'type':data.get('type','tool')},db)
            target=linked['id'];kind=linked['kind']
        else:fail('Register the approved material as a candidate or choose an existing content ID')
        db.execute('UPDATE fieldtofit_editorial_topics SET kind=?,item_id=?,version=version+1,updated_at=? WHERE id=?',(kind,target,stamp(),ident))
        _audit(db,ident,'draft_linked',{'kind':kind,'id':target})
    return {'kind':kind,'id':target}


def intake(ident):
    from backend.knowledge.content_workspace import inbox
    results=[];offset=0
    while True:
        page=inbox(status='selected',offset=offset)
        for item in page['items']:
            # Intake is a handoff, not permission to overwrite an existing researched proposal.
            with editorial_transaction() as db:
                _batch(db,ident)
                existing=db.execute('SELECT id FROM fieldtofit_editorial_topics WHERE source_ref=? OR event_key=? ORDER BY updated_at DESC LIMIT 1',
                    (item['ref'],store.canonical_url(item['url'])+'|')).fetchone()
                if existing:
                    db.execute('INSERT OR IGNORE INTO fieldtofit_editorial_members VALUES(?,?,?)',(ident,existing['id'],stamp()))
            if existing:
                results.append({'id':existing['id'],'suppressed':True,'reason':'保留已有提案与决定；新材料由本地补搜后明确更新。'})
                continue
            result=propose(ident,{'event_url':item['url'],'ref':item['ref'],'fingerprint':hashlib.sha256(dump([item['title'],item['summary'],item['matches']]).encode()).hexdigest(),
              'proposal':{'title':item['title'],'reason':'用户已选中，待补搜原始材料及具体上站文案；选中不等于授权发布。','summary':item['summary'],'origin':'website'}})
            results.append(result)
        if page['next_offset'] is None:break
        offset=page['next_offset']
    return {'items':results}


def delivery(ident,data):
    state=data.get('state')
    if state not in ('running','prepared','delivered','failed'):fail('Invalid delivery state')
    # An actual delivery receipt must still be recorded if new leads arrive later.
    if state=='prepared':
        from backend.knowledge.briefing_review import gate
        gate(ident)
    with editorial_transaction() as db:
        b=_batch(db,ident)
        if data.get('version')!=b['version']:fail('Briefing changed','batch_conflict',409)
        if b['delivery_state']=='delivered':fail('Already delivered; preserve the receipt','already_delivered',409)
        receipt=text(data.get('receipt',''),'receipt',2000,False)
        if state=='delivered' and (not receipt or data.get('confirmed') is not True):fail('An actual confirmed delivery receipt is required')
        body_hash=text(data.get('body_hash',''),'body_hash',128,False)
        db.execute('UPDATE fieldtofit_editorial_batches SET delivery_state=?,receipt=?,body_hash=?,version=version+1,updated_at=? WHERE id=?',(state,receipt,body_hash,stamp(),ident))
        _audit(db,ident,'delivery',{'state':state,'receipt':receipt,'body_hash':body_hash,'note':text(data.get('note',''),'note',2000,False)})
    return detail(ident)


def published(db,kind,ident,content,withdraw,topics=None):
    if topics is None:topics=db.execute("SELECT id FROM fieldtofit_editorial_topics WHERE kind=? AND item_id=? AND (decision='continue' OR ?=1)",(kind,ident,int(withdraw))).fetchall()
    for row in topics:
        state='withdrawn' if withdraw else 'published'
        db.execute('UPDATE fieldtofit_editorial_topics SET decision=?,version=version+1,updated_at=? WHERE id=?',(state,stamp(),row['id']))
        _audit(db,row['id'],state,{'kind':kind,'id':ident,'content_hash':hashlib.sha256(dump(content).encode()).hexdigest(),'url':'/for-you#'+('news-' if kind=='news' else 'watch-')+ident.lower()})


def upgrade():
    """Explicit additive migration; existing content, source settings and credentials stay intact."""
    from pathlib import Path
    from backend.db import execute_statements
    from backend.knowledge.source_catalog import definitions
    schema=(Path(__file__).parent/'schema.sql').read_text().split('CREATE TABLE IF NOT EXISTS fieldtofit_editorial_batches',1)[1]
    statements=[(s.strip(),()) for s in ('CREATE TABLE IF NOT EXISTS fieldtofit_editorial_batches'+schema).split(';') if s.strip()]
    for s in definitions():
        if s['id'].endswith('-announcements'):
            statements.append(('INSERT OR IGNORE INTO knowledge_sources(id,name,category,url,adapter,config) VALUES(?,?,?,?,?,?)',(s['id'],s['name'],s['category'],s['url'],s['adapter'],store.encode(s['config']))))
    with get_db() as db:
        from backend.db import TursoConnection
        if isinstance(db,TursoConnection):db.atomic_statements(statements)
        else:
            db.execute('BEGIN IMMEDIATE');execute_statements(db,statements)
    return {'ok':True,'added_source_ids':[s['id'] for s in definitions() if s['id'].endswith('-announcements')]}
