"""Explainable private review groups; no quality score or automatic publication."""
import hashlib
from datetime import datetime,timedelta,timezone
from backend.db import get_db
from backend.knowledge import store

GROUPS={'priority':3,'follow':2,'verify':1}


def evaluate(c,db,context=None):
    ref=c['ref'];primary=False;mats=[];meta={};metrics=store.decode(c.get('metrics'),{}) if isinstance(c.get('metrics'),str) else c.get('metrics') or {}
    if context is not None:
        meta,mats=context['materials'].get(ref,({},[]))
        primary=bool(meta.get('primary'))
    elif ref.startswith('discovery:'):
        row=db.execute('SELECT * FROM fieldtofit_discoveries WHERE id=?',(ref[10:],)).fetchone()
        meta=store.decode(row['metadata'],{});mats=store.decode(row['materials'],[]);primary=bool(meta.get('primary'))
    elif ref.startswith('intake:'):
        row=db.execute('SELECT data FROM knowledge_platform_intake WHERE id=?',(ref[7:],)).fetchone()
        data=store.decode(row['data'],{});mats=data.get('materials',[]);metrics=data.get('metrics',{});primary=bool(mats)
        meta={'change':'repository_update','gaps':data.get('gaps',[])}
    elif ref.startswith('record:'):
        row=db.execute('SELECT metadata FROM knowledge_records WHERE id=?',(ref[7:],)).fetchone()
        mats=[dict(x) for x in db.execute('SELECT * FROM knowledge_evidence WHERE record_id=?',(ref[7:],)).fetchall()]
        meta=store.decode(row['metadata'],{});primary=any(m.get('evidence_type') in ('official_claim','documented') for m in mats)
    reasons=[];unknowns=list(meta.get('gaps',[]));signals=[]
    full=any(m.get('coverage')=='full_text' and len(m.get('body',''))>=150 for m in mats)
    useful=any(any(word in m.get('body','').lower() for word in ('pip install','npm install','uv add','docker run','quick start','quickstart','usage','使用方法')) for m in mats)
    if primary:reasons.append('原始材料：已获取作者／官方材料，具体说法仍须审阅。')
    else:unknowns.append('原始出处或正文尚未核对，先保留为发现线索。')
    if not full:unknowns.append('尚无足够的完整正文；摘要、指标和链接不代表完整材料。')
    if useful:reasons.append('可尝试入口：材料包含安装或使用说明，可进一步检查实际可用性。')
    observed=metrics.get('source_observations',{}).get(c['source'],{})
    if observed:metrics=observed
    histories=(context['histories'].get((c['url'],c['source']),[])[:8] if context is not None else [dict(r) for r in db.execute('SELECT observed_at,metrics FROM fieldtofit_attention_observations WHERE url=? AND source_id=? ORDER BY observed_at DESC LIMIT 8',(c['url'],c['source'])).fetchall()])
    # A retained historical snapshot must not replace newer candidate metrics.
    if histories and metrics and any(metrics.get(k)!=store.decode(histories[0]['metrics'],{}).get(k) for k in ('stars','points','comments','likes') if k in metrics):
        histories=[]
    growth=False
    if histories:
        latest=histories[0];new=store.decode(latest['metrics'],{})
        for old in histories[1:]:
            days=(datetime.fromisoformat(latest['observed_at'].replace('Z','+00:00'))-datetime.fromisoformat(old['observed_at'].replace('Z','+00:00'))).total_seconds()/86400
            previous=store.decode(old['metrics'],{})
            if .8<=days<=8 and isinstance(new.get('stars'),int) and isinstance(previous.get('stars'),int):
                delta=new['stars']-previous['stars'];signals.append({'kind':'stars_change','value':delta,'from':old['observed_at'],'to':latest['observed_at'],'url':c['url']})
                growth=delta>=50 and days<=2;break
        for key,value in new.items():
            signals.append({'kind':key,'value':value,'observed_at':latest['observed_at'],'url':c['url'],'window':'采集快照，非增量'})
    elif metrics:
        for key in ('stars','points','likes','downloads','votes','comments'):
            if isinstance(metrics.get(key),int):signals.append({'kind':key,'value':metrics[key],'observed_at':metrics.get('observed_at'),'url':c['url'],'window':'累计快照；没有观测日期时不能认定近期关注'})
    if not signals:unknowns.append('没有可核对的关注指标；不按零关注处理。')
    if growth:reasons.append('近期关注：约两日内有至少 50 个新增 Star 的两次实际快照；不是能力评分。')
    date=meta.get('upstream_updated_at') or c.get('published_at');fresh=False
    if date:
        try:
            age=(datetime.now(timezone.utc)-datetime.fromisoformat(date.replace('Z','+00:00')).replace(tzinfo=timezone.utc)).total_seconds()
            fresh=0<=age<=8*86400
        except (ValueError,TypeError):pass
    else:unknowns.append('原文发布时间未知；发现时间不代替发布时间。')
    change=meta.get('change','');major=change in ('official_article','model_revision','repository_update')
    if any('本次正文未重新核对' in x for x in unknowns):fresh=False
    if major:reasons.append({'official_article':'官方文章：建议核对新发布、政策或使用条件变化。','model_revision':'模型材料：保留了来源修订和模型卡，可核对版本变化。','repository_update':'已有仓库：原始文件发生变化，建议核对当前网站资料。'}[change])
    group='priority' if primary and full and ((fresh and (major or useful)) or change=='repository_update' or growth) else 'follow' if primary and mats else 'verify'
    if meta.get('archived'):group='follow';unknowns.append('仓库已归档，需确认后续维护安排。')
    # Only known same-source facts determine the group. Human overrides remain separate.
    return {'group_name':group,'sort_rank':GROUPS[group], 'reasons':reasons,'unknowns':list(dict.fromkeys(unknowns)),
            'signals':signals,'fingerprint':hashlib.sha256(store.encode([meta,mats,metrics]).encode()).hexdigest()}


# Urgency is an editorial investigation queue, never a quality or publication verdict.
URGENT_SQL = "EXISTS(SELECT 1 FROM json_each(COALESCE(p.signals,'[]')) sig WHERE json_extract(sig.value,'$.kind')='review_urgency' AND json_extract(sig.value,'$.value')='urgent')"


def age_days(value):
    try:
        d=datetime.fromisoformat(value.replace('Z','+00:00'))
        if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc)-d).total_seconds()/86400
    except (ValueError,TypeError,AttributeError):return None


def urgency(c, assessment):
    signals=assessment['signals'];reasons=[]
    age=age_days(c.get('discovered_at'))
    recent=age is not None and 0<=age<=14
    for signal in signals:
        value=signal.get('value');observed_age=age_days(signal.get('observed_at'))
        current=recent or (observed_age is not None and 0<=observed_age<=7)
        if not isinstance(value,(int,float)):continue
        if current and ((signal['kind']=='points' and value>=100) or (signal['kind']=='comments' and value>=50)):
            reasons.append(f"讨论信号：{signal['kind']} {value}；{'观测时间未知，仅作为核验线索' if observed_age is None else '有日期的累计快照，非增长速度'}。")
        if signal['kind']=='stars_change' and value>=50:reasons.append('实际跨日 Star 增量值得核验；不代表项目质量。')
    return reasons


def candidate_hot(c):
    metrics=store.decode(c['metrics'],{}) if isinstance(c['metrics'],str) else c['metrics']
    metrics=metrics.get('source_observations',{}).get(c['source'],metrics)
    return bool(urgency(c,{'signals':[{'kind':k,'value':v,'observed_at':metrics.get('observed_at')} for k,v in metrics.items() if k in ('points','comments')]}))


def attention_order(c):
    metrics=store.decode(c['metrics'],{}) if isinstance(c['metrics'],str) else c['metrics']
    metrics=metrics.get('source_observations',{}).get(c['source'],metrics)
    return tuple(-metrics.get(k,0) if isinstance(metrics.get(k,0),(int,float)) else 0 for k in ('points','comments'))


def inputs(db,refs=None):
    """Bulk lightweight input fingerprints; no remote per-candidate reads."""
    from backend.knowledge.content_workspace import CANDIDATES
    where=' WHERE c.ref IN ('+','.join('?' for _ in refs)+')' if refs else ''
    rows=[dict(r) for r in db.execute(CANDIDATES+"SELECT c.*,p.fingerprint assessed_fingerprint,p.updated_at assessed_at,COALESCE(i.status,'pending') inbox_status FROM candidates c LEFT JOIN fieldtofit_candidate_priority p ON p.ref=c.ref LEFT JOIN fieldtofit_inbox i ON i.ref=c.ref"+where,refs or []).fetchall()]
    revisions={}
    revision_sql="SELECT 'discovery:'||id ref,fingerprint||metadata rev FROM fieldtofit_discoveries UNION ALL SELECT 'record:'||id,updated_at||COALESCE((SELECT group_concat(content_hash) FROM knowledge_evidence WHERE record_id=knowledge_records.id),'') FROM knowledge_records UNION ALL SELECT 'intake:'||id,data FROM knowledge_platform_intake"
    revision_args=[]
    if refs:
        revision_sql='SELECT * FROM ('+revision_sql+') WHERE ref IN ('+','.join('?' for _ in refs)+')';revision_args=refs
    for r in db.execute(revision_sql,revision_args).fetchall():revisions[r['ref']]=r['rev']
    obs={}
    urls=list({c['url'] for c in rows})
    obs_sql='SELECT url,source_id,MAX(observed_at) observed_at FROM fieldtofit_attention_observations'
    if refs and urls:obs_sql+=' WHERE url IN ('+','.join('?' for _ in urls)+')'
    for r in db.execute(obs_sql+' GROUP BY url,source_id',urls if refs and urls else []).fetchall():obs[(r['url'],r['source_id'])]=r['observed_at']
    for c in rows:
        data=[c[k] for k in ('ref','title','summary','url','source','published_at','metrics')]+[revisions.get(c['ref']),obs.get((c['url'],c['source']))]
        c['evidence_revision']=hashlib.sha256(str(revisions.get(c['ref'],'')).encode()).hexdigest()
        c['input_fingerprint']='v2:'+hashlib.sha256(store.encode(data).encode()).hexdigest()
    return rows


def evaluation_context(db,rows):
    result={'materials':{},'histories':{}}
    if not rows:return result
    refs=[c['ref'] for c in rows];marks=','.join('?' for _ in refs)
    for r in db.execute("SELECT 'discovery:'||id ref,metadata,materials FROM fieldtofit_discoveries WHERE 'discovery:'||id IN ("+marks+')',refs).fetchall():
        result['materials'][r['ref']]=(store.decode(r['metadata'],{}),store.decode(r['materials'],[]))
    for r in db.execute("SELECT 'intake:'||id ref,data FROM knowledge_platform_intake WHERE 'intake:'||id IN ("+marks+')',refs).fetchall():
        data=store.decode(r['data'],{});mats=data.get('materials',[]);result['materials'][r['ref']]=({'primary':bool(mats),'change':'repository_update','gaps':data.get('gaps',[])},mats)
    for r in db.execute("SELECT 'record:'||id ref,metadata FROM knowledge_records WHERE 'record:'||id IN ("+marks+')',refs).fetchall():result['materials'][r['ref']]=(store.decode(r['metadata'],{}),[])
    for r in db.execute("SELECT * FROM knowledge_evidence WHERE 'record:'||record_id IN ("+marks+')',refs).fetchall():
        meta,mats=result['materials']['record:'+r['record_id']];mats.append(dict(r));meta['primary']=meta.get('primary',False) or r['evidence_type'] in ('official_claim','documented')
    urls=[c['url'] for c in rows]
    for r in db.execute('SELECT * FROM fieldtofit_attention_observations WHERE url IN ('+','.join('?' for _ in urls)+') ORDER BY observed_at DESC',urls).fetchall():result['histories'].setdefault((r['url'],r['source_id']),[]).append(dict(r))
    return result


def refresh(refs=None,limit=100):
    from backend.db import execute_statements,TursoConnection
    limit=max(1,min(int(limit),100));now=store.now()
    with get_db() as db:
        rows=inputs(db,refs)
        if refs:rows=[c for c in rows if c['ref'] in refs]
        else:
            rows=[c for c in rows if c['inbox_status'] in ('pending','selected') and (c['input_fingerprint']!=c['assessed_fingerprint'] or (age_days(c['assessed_at']) or 0)>=1)]
            # Changes to previously reviewed inputs first, then rotate stale/unassessed work.
            # Reserve capacity for never-assessed candidates so new material cannot starve.
            changed=[c for c in rows if c['assessed_fingerprint'] and c['input_fingerprint']!=c['assessed_fingerprint']]
            changed_refs={c['ref'] for c in changed}
            rest=[c for c in rows if c['ref'] not in changed_refs]
            changed.sort(key=lambda c:(not candidate_hot(c),*attention_order(c),c['assessed_at'] or '',c['ref']))
            rest.sort(key=lambda c:(not candidate_hot(c),*attention_order(c),c['assessed_at'] or '',c['discovered_at'],c['ref']))
            selected=changed[:max(1,limit*3//4)]+rest[:max(1,limit//4)]
            used={c['ref'] for c in selected};selected+= [c for c in changed+rest if c['ref'] not in used]
            total=len(rows);rows=selected[:limit]
        context=evaluation_context(db,rows)
        statements=[]
        for c in rows:
            v=evaluate(c,db,context);reasons=urgency(c,v)
            v['signals'].append({'kind':'review_urgency','value':'urgent' if reasons else 'normal','reasons':reasons})
            statements.append(('INSERT INTO fieldtofit_candidate_priority(ref,group_name,sort_rank,reasons,unknowns,signals,fingerprint,updated_at) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(ref) DO UPDATE SET group_name=excluded.group_name,sort_rank=excluded.sort_rank,reasons=excluded.reasons,unknowns=excluded.unknowns,signals=excluded.signals,fingerprint=excluded.fingerprint,updated_at=excluded.updated_at',
                (c['ref'],v['group_name'],v['sort_rank'],store.encode(v['reasons']),store.encode(v['unknowns']),store.encode(v['signals']),c['input_fingerprint'],now)))
    if statements:
        with get_db() as db:
            if isinstance(db,TursoConnection):db.atomic_statements(statements)
            else:execute_statements(db,statements)
    return {'assessed':len(rows),'limit':limit,'remaining':max(0,total-len(rows)) if not refs else 0}


def override(data):
    ref=data.get('ref');group=data.get('group');reason=data.get('reason','').strip()
    if group not in (*GROUPS,None):raise ValueError('Unknown priority group')
    if group and not 2<=len(reason)<=1000:raise ValueError('调整优先级需要填写具体理由')
    from backend.knowledge.content_workspace import candidate
    with get_db() as db:
        if not candidate(ref,db):raise ValueError('Candidate not found')
    refresh([ref])
    with get_db() as db:db.execute('UPDATE fieldtofit_candidate_priority SET manual_group=?,manual_reason=?,updated_at=? WHERE ref=?',(group,reason,store.now(),ref))
    return {'ref':ref,'group':group,'reason':reason}
