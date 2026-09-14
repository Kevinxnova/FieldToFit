"""Explainable private review groups; no quality score or automatic publication."""
import hashlib
from datetime import datetime,timezone
from backend.db import get_db
from backend.knowledge import store

GROUPS={'priority':3,'follow':2,'verify':1}


def evaluate(c,db):
    ref=c['ref'];primary=False;mats=[];meta={};metrics=store.decode(c.get('metrics'),{}) if isinstance(c.get('metrics'),str) else c.get('metrics') or {}
    if ref.startswith('discovery:'):
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
    histories=[dict(r) for r in db.execute('SELECT observed_at,metrics FROM fieldtofit_attention_observations WHERE url=? AND source_id=? ORDER BY observed_at DESC LIMIT 8',(c['url'],c['source'])).fetchall()]
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


def refresh(refs=None,limit=100):
    from backend.knowledge.content_workspace import CANDIDATES
    with get_db() as db:
        if refs:
            rows=db.execute(CANDIDATES+'SELECT * FROM candidates WHERE ref IN ('+','.join('?' for _ in refs)+')',refs).fetchall()
        else:
            rows=db.execute(CANDIDATES+'SELECT c.* FROM candidates c LEFT JOIN fieldtofit_candidate_priority p ON p.ref=c.ref WHERE p.ref IS NULL ORDER BY datetime(discovered_at) DESC,ref LIMIT ?',(limit,)).fetchall()
        for row in rows:
            c=dict(row);v=evaluate(c,db)
            db.execute('INSERT INTO fieldtofit_candidate_priority(ref,group_name,sort_rank,reasons,unknowns,signals,fingerprint,updated_at) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(ref) DO UPDATE SET group_name=excluded.group_name,sort_rank=excluded.sort_rank,reasons=excluded.reasons,unknowns=excluded.unknowns,signals=excluded.signals,fingerprint=excluded.fingerprint,updated_at=excluded.updated_at',
                       (c['ref'],v['group_name'],v['sort_rank'],store.encode(v['reasons']),store.encode(v['unknowns']),store.encode(v['signals']),v['fingerprint'],store.now()))
    return {'assessed':len(rows),'limit':limit}


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
