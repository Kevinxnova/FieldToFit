"""Private pre-delivery selection audit. Never creates drafts or changes user decisions."""
import hashlib
from collections import Counter
from backend.db import get_db
from backend.knowledge import store
from backend.knowledge.candidate_priority import inputs, age_days, urgency
from backend.knowledge.content_workspace import dump, fail, text
from backend.knowledge.editorial_batches import _batch, _audit
from backend.knowledge.workspace_transactions import editorial_transaction

OUTCOMES=('recommend','investigate','not_recommended','already_covered')


def selection(db,ident,refs=None):
    _batch(db,ident)
    candidates=inputs(db,refs)
    # Excluded/finished inbox items and explicit user decisions are not resurrected.
    topics=[dict(r) for r in db.execute('SELECT source_ref,event_url,decision,review_on FROM fieldtofit_editorial_topics').fetchall()]
    from backend.knowledge.content_workspace import today
    excluded=[t for t in topics if t['decision'] in ('published','declined','continue') or (t['decision']=='later' and (t['review_on'] or '')>today())]
    suppressed={t['source_ref'] for t in excluded if t['source_ref']}
    suppressed_urls={t['event_url'] for t in excluded}
    for r in db.execute("SELECT published_json FROM fieldtofit_content_items WHERE kind!='charts' AND published_json IS NOT NULL").fetchall():
        item=store.decode(r['published_json'],{})
        if item.get('state')!='withdrawn':suppressed_urls.update(s['url'] for s in item.get('sources',[]))
    rows=[]
    for c in candidates:
        if c['inbox_status'] not in ('pending','selected') or c['ref'] in suppressed or c['url'] in suppressed_urls:continue
        metrics=store.decode(c['metrics'],{}) if isinstance(c['metrics'],str) else c['metrics']
        metrics=metrics.get('source_observations',{}).get(c['source'],metrics)
        signals=[{'kind':k,'value':v,'observed_at':metrics.get('observed_at')} for k,v in metrics.items() if k in ('points','comments','stars','likes','votes','downloads') and isinstance(v,(int,float))]
        hot=urgency(c,{'signals':signals});age=age_days(c['discovered_at'])
        if c['inbox_status']!='selected' and not hot and (age is None or not 0<=age<=14):continue
        reasons=[]
        if c['inbox_status']=='selected':reasons.append('用户已选，先接续整理')
        reasons+=hot
        if age is not None and 3<=age<=14 and any(s['kind'] in ('points','comments') and s['value']>=10 for s in signals):reasons.append('已有讨论且等待至少三天，需要说明处理结果')
        # No time-only change resets an editorial assessment. New source content does.
        evidence=[c[k] for k in ('ref','title','summary','url','source','published_at','evidence_revision')]+[{s['kind']:s['value'] for s in signals}]
        rows.append({**{k:c[k] for k in ('ref','title','summary','url','source','discovered_at','published_at')},'reasons':reasons,'urgent':bool(hot),'selected':c['inbox_status']=='selected','signals':signals,'evidence_fingerprint':hashlib.sha256(dump(evidence).encode()).hexdigest()})
    counts=Counter(c['url'] for c in rows)
    audits={};origins={}
    for r in db.execute("SELECT topic_id,payload FROM fieldtofit_editorial_events WHERE action='selection_review' AND datetime(created_at)>=datetime('now','-14 days') ORDER BY seq").fetchall():
        a=store.decode(r['payload'],{});audits[a['ref']]=a;origins[a['ref']]=r['topic_id']
    for c in rows:
        if counts[c['url']]>1:c['reasons'].append('同一入口有多条发现，需核对是否同一事件')
        c['required']=c['selected'];a=audits.get(c['ref'])
        c['review']=a if a and a['evidence_fingerprint']==c['evidence_fingerprint'] else None
        c['review_stale']=bool(a and not c['review'])
        c['review_batch']=origins.get(c['ref']) if c['review'] else None
    def discussion_order(c):
        values={s['kind']:s['value'] for s in c['signals']}
        return (-values.get('points',0),-values.get('comments',0),c['discovered_at'],c['ref'])
    rows.sort(key=lambda c:(not c['selected'],not c['urgent'],*discussion_order(c)))
    # Daily capacity is explicit: keep all leads visible, do not call the backlog reviewed.
    for group in ([c for c in rows if c['urgent'] and (not c['review'] or c['review_batch']==ident)][:20], [c for c in rows if c['reasons'] and not c['urgent'] and not c['selected'] and (not c['review'] or c['review_batch']==ident)][:10]):
        for c in group:c['required']=True
    rows.sort(key=lambda c:(not c['required'],not c['selected'],not c['urgent'],*discussion_order(c)))
    return rows


def preflight(ident,offset=0,limit=30):
    offset=max(0,int(offset));limit=max(1,min(100,int(limit)))
    with get_db() as db:rows=selection(db,ident)
    required=[c for c in rows if c['required']];missing=[c for c in required if not c['review']]
    return {'items':rows[offset:offset+limit],'total':len(rows),'required':len(required),'unreviewed':len(missing),'ready':not missing,'offset':offset,'next_offset':offset+limit if offset+limit<len(rows) else None,'backlog':sum(bool(c['reasons']) and not c['required'] and not c['review'] for c in rows),'urgent_total':sum(c['urgent'] for c in rows),
            'notice':'推荐数量不是筛选上限；优先核验不等于可以发布。未完成核验可记录 investigate 并在日报说明材料缺口。',
            'scope':'已选候选全部检查；当日最多20项高讨论、10项重复或积压线索须处理，其余明确列为积压。覆盖近14天及最近观测的高讨论候选；同证据复用14天内的编辑记录，用户决定另行保留。'}


def review(ident,data):
    submitted=data.get('items') if 'items' in data else [data]
    if not isinstance(submitted,list) or not 1<=len(submitted)<=50:fail('Submit one to fifty selection records')
    payloads=[]
    from backend.knowledge.platform_watch import valid_url
    for d in submitted:
        if not isinstance(d,dict):fail('Invalid selection record')
        ref=text(d.get('ref'),'ref',200);outcome=d.get('outcome')
        if outcome not in OUTCOMES:fail('Unknown selection outcome')
        reason=text(d.get('reason'),'reason',2000);evidence=d.get('sources',[])
        if not isinstance(evidence,list) or len(evidence)>10:fail('At most ten checked sources')
        evidence=[valid_url(text(u,'source',1600)) for u in evidence]
        if outcome=='recommend' and not evidence:fail('推荐需要已核对的来源入口')
        payloads.append({'ref':ref,'outcome':outcome,'reason':reason,'sources':evidence,'evidence_fingerprint':d.get('evidence_fingerprint')})
    refs=[p['ref'] for p in payloads]
    if len(set(refs))!=len(refs):fail('Duplicate candidate in selection records')
    with editorial_transaction() as db:
        current={c['ref']:c for c in selection(db,ident,refs)};writes=[]
        for payload in payloads:
            c=current.get(payload['ref'])
            if not c:fail('Candidate no longer requires this review','selection_changed',409)
            if c['evidence_fingerprint']!=payload['evidence_fingerprint']:fail('Candidate evidence changed; read again','selection_changed',409)
            if c['review']!=payload:writes.append(payload)
        for payload in writes:_audit(db,ident,'selection_review',payload)
    return {'saved':True,'unchanged':not writes,'recorded':len(writes)}


def gate(ident):
    result=preflight(ident)
    if not result['ready']:fail('仍有 '+str(result['unreviewed'])+' 项重要线索未记录选题结果；先核验或说明待核验原因','selection_review_required',409)
    return result
