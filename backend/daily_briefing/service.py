"""Immutable bilingual editions. All render work finishes before publication."""
import base64
import json
from datetime import datetime, timezone
from backend.db import get_db
from backend.knowledge.workspace_transactions import editorial_transaction
from .schedule import PUBLISH_AT, local_time
from .schema import TZ, validate, digest, project, day_key, stamp, fail, bilingual


def enc(v): return json.dumps(v,ensure_ascii=False,separators=(',',':'),allow_nan=False)
def dec(v): return json.loads(v) if v else None

def _issue(db, day):
    row=db.execute('SELECT * FROM fieldtofit_daily_issues WHERE day=?',(day_key(day),)).fetchone()
    if not row: fail('Daily edition not found','daily_not_found',404)
    return dict(row)

def _version(row, version):
    if type(version) is not int or row['draft_version']!=version: fail('Draft changed. Reload and review the current version.','daily_conflict',409)

def save(raw, version=0):
    data=validate(raw);day=data['date'];now=stamp()
    with editorial_transaction() as db:
        row=db.execute('SELECT * FROM fieldtofit_daily_issues WHERE day=?',(day,)).fetchone()
        if row:
            _version(row,version)
            if dec(row['draft_json'])==data: return {'date':day,'draft_version':version}
            db.execute('UPDATE fieldtofit_daily_issues SET draft_json=?,draft_version=?,review_hash=NULL,review_json=NULL,updated_at=? WHERE day=?',(enc(data),version+1,now,day))
        else:
            if version!=0: fail('Draft changed','daily_conflict',409)
            db.execute('INSERT INTO fieldtofit_daily_issues(day,draft_json,draft_version,created_at,updated_at) VALUES(?,?,1,?,?)',(day,enc(data),now,now))
    return {'date':day,'draft_version':version+1}

def draft(day):
    with get_db() as db:
        row=_issue(db,day)
        history=db.execute('SELECT revision,published_at,reason_json FROM fieldtofit_daily_publications WHERE day=? ORDER BY revision DESC',(day,)).fetchall()
    return {'date':day,'draft':dec(row['draft_json']),'draft_version':row['draft_version'],'state':row['state'],'review':dec(row['review_json']),'reviewed':row['review_hash']==digest(dec(row['draft_json'])),'published_revision':row['published_revision'],'history':[{'revision':r['revision'],'published_at':r['published_at'],'reason':dec(r['reason_json'])} for r in history]}

def administrative_index():
    with get_db() as db:
        rows=db.execute('SELECT day,draft_version,state,published_revision,review_hash,updated_at FROM fieldtofit_daily_issues ORDER BY day DESC LIMIT 100').fetchall()
        runs=db.execute('SELECT day,phase,state,started_at,finished_at,attempts,result_json FROM fieldtofit_daily_runs ORDER BY day DESC,started_at DESC LIMIT 30').fetchall()
    from .pipeline import configuration
    return {'items':[dict(r) for r in rows],'runs':[{**dict(r),'result':dec(r['result_json']),'result_json':None} for r in runs],'configuration':configuration()}

def approve(day, version, report, renderer=None):
    """Review binds copy + evidence. Saving any change invalidates both PDFs."""
    from .pdf import render
    d=draft(day);_version(d,version);data=validate(d['draft']);content_hash=digest(data)
    if not isinstance(report,dict) or report.get('approved') is not True or report.get('method') not in ('owner','independent_model'): fail('Explicit fact and bilingual review is required')
    if any(c['state']=='failed' for c in data['coverage']): fail('Failed coverage must be resolved before review','daily_coverage',409)
    if data['kind']=='daily' and any(c['state']!='checked' for c in data['coverage']): fail('All eleven dimensions require successful checks','daily_coverage',409)
    if renderer is None:
        next_revision=(d['published_revision'] or 0)+1
        renderer=lambda data,lang,image=None:render(data,lang,image=image,revision=next_revision)
    image=None
    if data.get('image'):
        from backend.knowledge.sources import fetch
        image=fetch(data['image']['url'],max_bytes=5_000_000)[0]
    artifacts={lang:renderer(data,lang,image=image) for lang in ('zh','en')}
    if sum(len(a['bytes']) for a in artifacts.values())>2_500_000:fail('PDF pair exceeds the publication storage budget','daily_pdf_size',413)
    review={'approved':True,'method':report['method'],'checked_at':stamp(),'content_hash':content_hash,'evidence_hash':report.get('evidence_hash'), 'pages':{l:a['pages'] for l,a in artifacts.items()}}
    with editorial_transaction() as db:
        row=_issue(db,day);_version(row,version)
        if digest(dec(row['draft_json']))!=content_hash: fail('Review is stale','daily_conflict',409)
        for lang,a in artifacts.items():
            db.execute('INSERT OR REPLACE INTO fieldtofit_daily_prepared(day,content_hash,lang,data_base64,sha256,pages) VALUES(?,?,?,?,?,?)',(day,content_hash,lang,base64.b64encode(a['bytes']).decode(),a['sha256'],a['pages']))
        db.execute('UPDATE fieldtofit_daily_issues SET review_hash=?,review_json=?,updated_at=? WHERE day=?',(content_hash,enc(review),stamp(),day))
    return review

def publish(day, version, reason, automatic=False, now=None):
    now=now or datetime.now(timezone.utc);bilingual(reason,'publication/correction reason',600)
    with editorial_transaction() as db:
        row=_issue(db,day);_version(row,version);data=validate(dec(row['draft_json']),now=now);h=digest(data)
        previous=db.execute('SELECT * FROM fieldtofit_daily_publications WHERE day=? ORDER BY revision DESC LIMIT 1',(day,)).fetchone()
        artifacts=db.execute('SELECT * FROM fieldtofit_daily_prepared WHERE day=? AND content_hash=? ORDER BY lang',(day,h)).fetchall()
        if row['review_hash']!=h or {r['lang'] for r in artifacts}!={'zh','en'}: fail('Review and both PDFs must be ready','daily_not_ready',409)
        if automatic:
            if row['state']=='withdrawn': fail('A withdrawn edition requires owner action','daily_withdrawn',409)
            if data['kind']!='daily' or now.astimezone(TZ).date().isoformat()!=day or local_time(now)<PUBLISH_AT: fail('Automatic publication is only permitted from '+PUBLISH_AT.strftime('%H:%M')+' Asia/Shanghai on the issue date','daily_not_due',409)
            if previous and digest(dec(previous['snapshot_json']))!=digest(_public_copy(data)): fail('Automatic corrections require owner review','daily_correction',409)
        public=_public_copy(data);public_hash=digest(public)
        if previous and previous['content_hash']==public_hash and row['state']=='published': return {'date':day,'revision':previous['revision'],'content_hash':public_hash,'unchanged':True}
        revision=(previous['revision'] if previous else 0)+1
        db.execute('INSERT INTO fieldtofit_daily_publications VALUES(?,?,?,?,?,?)',(day,revision,enc(public),public_hash,stamp(now),enc(reason)))
        for r in artifacts:
            db.execute('INSERT INTO fieldtofit_daily_pdfs VALUES(?,?,?,?,?,?)',(day,revision,r['lang'],r['data_base64'],r['sha256'],r['pages']))
        db.execute('UPDATE fieldtofit_daily_issues SET state=?,published_revision=?,updated_at=? WHERE day=?',('published',revision,stamp(now),day))
    return {'date':day,'revision':revision,'content_hash':public_hash,'unchanged':False}

def _public_copy(data):
    data=json.loads(enc(data));data.pop('coverage',None)
    if data.get('image'): data['image'].pop('reuse_basis',None)
    return data

def withdraw(day, version, reason):
    bilingual(reason,'withdrawal reason',600)
    with editorial_transaction() as db:
        row=_issue(db,day);_version(row,version)
        # Increment the draft version to invalidate every in-flight publication.
        db.execute('UPDATE fieldtofit_daily_issues SET state=?,draft_version=?,review_hash=NULL,review_json=?,updated_at=? WHERE day=?',('withdrawn',version+1,enc({'withdrawal_reason':reason,'at':stamp()}),stamp(),day))
    return {'state':'withdrawn','draft_version':version+1}

def archive(lang='zh', limit=30, offset=0, now=None):
    if type(limit) is not int or not 1<=limit<=100 or type(offset) is not int or offset<0: fail('Invalid archive pagination')
    now=now or datetime.now(timezone.utc);today=now.astimezone(TZ).date().isoformat()
    with get_db() as db:
        rows=db.execute('SELECT p.day,p.revision,p.content_hash,p.published_at,p.snapshot_json FROM fieldtofit_daily_publications p JOIN fieldtofit_daily_issues i ON i.day=p.day AND i.published_revision=p.revision WHERE i.state=? ORDER BY p.day DESC LIMIT ? OFFSET ?',('published',limit,offset)).fetchall()
        total=db.execute('SELECT COUNT(*) n FROM fieldtofit_daily_issues WHERE state=?',('published',)).fetchone()['n']
        latest=db.execute('SELECT MAX(day) day FROM fieldtofit_daily_issues WHERE state=?',('published',)).fetchone()['day']
    items=[{'date':r['day'],'revision':r['revision'],'content_hash':r['content_hash'],'published_at':r['published_at'],'headline':project(dec(r['snapshot_json'])['headline'],lang),'kind':dec(r['snapshot_json'])['kind']} for r in rows]
    return {'items':items,'total':total,'offset':offset,'next_offset':offset+limit if offset+limit<total else None,'latest':latest,'today':today,'status':'delayed' if local_time(now)>=PUBLISH_AT and latest!=today else 'scheduled' if latest!=today else 'published','timezone':'Asia/Shanghai'}

def read(day=None,lang='zh',revision=None):
    if lang not in ('zh','en'): fail('Unsupported language')
    if day is None: day=archive(lang,1)['latest']
    if not day: fail('No published daily edition yet','daily_not_found',404)
    if revision is not None and (type(revision) is not int or revision<1): fail('Invalid publication revision')
    with get_db() as db:
        row=_issue(db,day)
        if row['state']!='published': fail('Edition is unavailable or withdrawn','daily_not_found',404)
        revision=revision or row['published_revision']
        p=db.execute('SELECT * FROM fieldtofit_daily_publications WHERE day=? AND revision=?',(day,revision)).fetchone()
        if not p: fail('Publication revision not found','daily_not_found',404)
        pdf=db.execute('SELECT lang,sha256,pages FROM fieldtofit_daily_pdfs WHERE day=? AND revision=?',(day,revision)).fetchall()
        history=db.execute('SELECT revision,published_at,reason_json FROM fieldtofit_daily_publications WHERE day=? ORDER BY revision DESC',(day,)).fetchall()
        older=db.execute("SELECT MAX(day) day FROM fieldtofit_daily_issues WHERE state='published' AND day<?",(day,)).fetchone()['day']
        newer=db.execute("SELECT MIN(day) day FROM fieldtofit_daily_issues WHERE state='published' AND day>?",(day,)).fetchone()['day']
    result=project(dec(p['snapshot_json']),lang)
    result['publication']={'revision':revision,'current_revision':row['published_revision'],'content_hash':p['content_hash'],'published_at':p['published_at'],'reason':project(dec(p['reason_json']),lang),'history':[{'revision':r['revision'],'published_at':r['published_at'],'reason':project(dec(r['reason_json']),lang)} for r in history]}
    result['navigation']={'older':older,'newer':newer}
    result['pdf']={r['lang']:{'sha256':r['sha256'],'pages':r['pages'],'url':f'/api/v1/daily/{day}/pdf?lang={r["lang"]}&revision={revision}'} for r in pdf}
    return result

def pdf_bytes(day,lang,revision=None):
    data=read(day,lang,revision);revision=data['publication']['revision']
    with get_db() as db:
        # Join current visibility again: withdrawal overrides archived downloads.
        r=db.execute('SELECT p.* FROM fieldtofit_daily_pdfs p JOIN fieldtofit_daily_issues i ON i.day=p.day WHERE p.day=? AND p.revision=? AND p.lang=? AND i.state=?',(day,revision,lang,'published')).fetchone()
    if not r: fail('PDF is unavailable','daily_pdf_unavailable',503)
    return base64.b64decode(r['data_base64']),r['sha256'],revision
