"""Private stage accounting and actionable editorial issues; reads never publish."""
import hashlib
import json
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from backend.db import get_db, TursoConnection
from backend.knowledge import store
from backend.knowledge.workspace_transactions import editorial_transaction
from backend.knowledge.content_workspace import fail, today, stamp, dump, detail, CANDIDATES

METRICS=('discovered','changed','full_text','excerpt','abstract','organized','published_new','published_update')
LOCAL='local-editorial'

def event(db,source,ref,action,key='',payload=None):
    at=stamp();day=datetime.fromisoformat(at).astimezone(timezone(timedelta(hours=8))).date().isoformat()
    db.execute("INSERT OR IGNORE INTO knowledge_settings(key,value,updated_at) VALUES('operation_tracking_since',?,?)",(at,at))
    identity=[source,ref,action,key,day] if action!='organized' else [source,ref,action,key,(payload or {}).get('evidence')]
    ident=hashlib.sha256(dump(identity).encode()).hexdigest()
    db.execute('INSERT OR IGNORE INTO fieldtofit_operation_events VALUES(?,?,?,?,?,?,?)',
               (ident,source or LOCAL,ref,action,dump(payload or {}),at,key))


def content_source(db,kind,ident):
    row=db.execute('SELECT source_ref FROM fieldtofit_content_items WHERE kind=? AND id=?',(kind,ident)).fetchone()
    ref=row['source_ref'] if row else ''
    if ref.startswith('discovery:'):
        r=db.execute('SELECT source_id FROM fieldtofit_discoveries WHERE id=?',(ref[10:],)).fetchone()
        if r:return r['source_id']
    if ref.startswith('intake:'):
        r=db.execute('SELECT source_id FROM knowledge_platform_intake WHERE id=?',(ref[7:],)).fetchone()
        if r:return r['source_id']
    if ref.startswith(('record:','tool:')):
        r=db.execute(CANDIDATES+'SELECT source FROM candidates WHERE ref=?',(ref,)).fetchone()
        if r:return r['source'] or LOCAL
    return LOCAL


def submit(kind,ident,data):
    from backend.knowledge.content_workspace import composed,gate,token
    with editorial_transaction() as db:
        d=detail(kind,ident,db)
        collection,revision=composed(kind,ident,d['draft'],db)
        expected=token(kind,ident,d['draft_version'],revision,d['draft'],d['materials_fingerprint'])
        if data.get('draft_version')!=d['draft_version'] or data.get('review_token')!=expected:fail('草稿或预览已变化，请重新预览','draft_conflict',409)
        gate(kind,ident,d['draft'],collection)
        if not d['has_changes']:fail('没有待复核的新修改')
        origin=content_source(db,kind,ident)
        evidence=hashlib.sha256(dump([{k:v for k,v in m.items() if k!='retrieved_at'} for m in d['source_materials']]).encode()).hexdigest()
        event(db,origin,kind+':'+ident,'organized',str(d['draft_version']),{'version':d['draft_version'],'evidence':evidence})
    return {'ok':True,'state':'review','draft_version':d['draft_version']}


def day_of(value):
    try:
        d=datetime.fromisoformat(value.replace('Z','+00:00'))
        if not d.tzinfo:d=d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone(timedelta(hours=8))).date().isoformat()
    except (ValueError,TypeError,AttributeError):return None


def age(value):
    try:
        d=datetime.fromisoformat(value.replace('Z','+00:00'))
        if not d.tzinfo:d=d.replace(tzinfo=timezone.utc)
        return round(max(0,(datetime.now(timezone.utc)-d).total_seconds()/86400),3)
    except (ValueError,TypeError,AttributeError):return None


def load():
    queries={
      'sources':'SELECT id,name,adapter,enabled,config,last_attempt_at,last_success_at,status,error FROM knowledge_sources',
      'runs':'SELECT * FROM knowledge_runs WHERE started_at>=? ORDER BY id',
      'progress':'SELECT * FROM knowledge_source_progress',
      'maintained':"SELECT DISTINCT r.source_id FROM knowledge_records r JOIN knowledge_selections s ON s.record_id=r.id WHERE s.state!='withdrawn' AND EXISTS(SELECT 1 FROM knowledge_publications p WHERE p.record_id=r.id AND p.state='published')",
      'events':'SELECT * FROM fieldtofit_operation_events ORDER BY created_at,id',
      'content':'SELECT * FROM fieldtofit_content_items',
      'inbox':'SELECT * FROM fieldtofit_inbox',
      'discoveries':'SELECT id,source_id,title,url,metadata,materials,discovered_at,updated_at,fingerprint FROM fieldtofit_discoveries',
      'intake':'SELECT * FROM knowledge_platform_intake',
      'candidates':CANDIDATES+'SELECT ref,title,url,summary,source FROM candidates',
      'conflicts':"SELECT c.*,r.title,r.source_id FROM knowledge_conflicts c JOIN knowledge_records r ON r.id=c.record_id WHERE c.status='open' AND (EXISTS(SELECT 1 FROM fieldtofit_item_sources l WHERE l.ref='record:'||r.id) OR EXISTS(SELECT 1 FROM knowledge_selections s WHERE s.record_id=r.id AND s.state!='withdrawn'))",
      'jobs':"SELECT j.*,r.title,r.source_id FROM knowledge_jobs j JOIN knowledge_records r ON r.id=j.record_id WHERE j.status='error' AND EXISTS(SELECT 1 FROM fieldtofit_item_sources l WHERE l.ref='record:'||r.id)",
      'evidence':'SELECT record_id,id,title,url,body,coverage,locator,content_hash,retrieved_at FROM knowledge_evidence',
      'history':"SELECT kind,item_id,created_at FROM fieldtofit_content_history WHERE action IN ('publish','import') ORDER BY seq",
      'links':'SELECT * FROM fieldtofit_item_sources',
            'issues':'SELECT * FROM fieldtofit_operation_issues',
      'settings':"SELECT key,value FROM knowledge_settings WHERE key='operation_tracking_since'",
    }
    statements=[(sql,((datetime.now(timezone.utc)-timedelta(days=32)).isoformat(),) if k=='runs' else ()) for k,sql in queries.items()]
    with get_db() as db:
        if isinstance(db,TursoConnection):cursors=db.atomic_statements(statements,read_only=True)
        else:
            db.execute('BEGIN');cursors=[db.execute(sql,args) for sql,args in statements]
        return {k:[dict(r) for r in cursor.fetchall()] for k,cursor in zip(queries,cursors)}


def snapshot(day='',source='',metric=''):
    day=day or today()
    try:parsed=date.fromisoformat(day)
    except (TypeError,ValueError):fail('日期格式应为 YYYY-MM-DD')
    if parsed>date.fromisoformat(today()) or parsed<date.fromisoformat(today())-timedelta(days=30):fail('请选择最近 31 天内的日期')
    if metric and metric not in (*METRICS,'checks','organize_pending','review_pending'):fail('Unknown metric')
    data=load();rows={};details=[];issues=[]
    since=next((r['value'] for r in data['settings']),None)
    tracked=bool(since and day>=day_of(since))
    def row(sid,name=None):
        if sid not in rows:rows[sid]={'id':sid,'name':name or sid,'checks':0,'attempts':0,**{m:0 if tracked else None for m in METRICS},'organize_pending':0,'review_pending':0,'oldest_wait_days':None,'unknown_wait_count':0,'last_success_at':None,'error':'','backlog_count':0,'enabled':True}
        return rows[sid]
    maintained={r['source_id'] for r in data['maintained']}
    def scheduled(s):return bool(store.decode(s['config'],{}).get('daily_enabled')) or (s['adapter']=='platform_repository' and s['id'] in maintained)
    row(LOCAL,'本地推荐与人工整理')
    for s in data['sources']:
        cfg=store.decode(s['config'],{})
        if scheduled(s):
            row(s['id'],s['name']).update(enabled=bool(s['enabled']),last_success_at=s['last_success_at'],status=s['status'],error=s['error'])
    def issue(code,ref,sid,title,reason,target,priority=2,fingerprint=''):
        ident=hashlib.sha256((code+'|'+ref).encode()).hexdigest()[:24]
        fp=hashlib.sha256(dump([code,reason,fingerprint]).encode()).hexdigest()
        issues.append({'id':ident,'code':code,'ref':ref,'source':sid,'title':title,'reason':reason,'target':target,'priority':priority,'fingerprint':fp})
    prog={p['source_id']:store.decode(p['state'],{}) for p in data['progress']}
    for s in data['sources']:
        if s['id'] not in rows or not s['enabled']:continue
        p=prog.get(s['id'],{});pending=p.get('pending') or p.get('pending_ids') or []
        rows[s['id']]['backlog_count']=len(pending)+len(p.get('index_pending',[]))
        target={'source':s['id']}
        if s['status'] in ('error','failed') or p.get('errors'):
            reason=s['error'] or '; '.join(str(x) for x in p.get('errors',[]))
            issue('source_failed',s['id'],s['id'],s['name']+'：采集异常',reason,target,0)
        if s['status']=='partial' or p.get('status')=='backlog':
            issue('source_backlog',s['id'],s['id'],s['name']+'：还有待续材料',s['error'] or '预算内未处理完，保留分页进度',target,1)
    for r in data['runs']:
        if r['source_id'] not in rows or day_of(r['started_at'])!=day:continue
        item=row(r['source_id']);item['checks']=1;item['attempts']+=1
        details.append({'source':r['source_id'],'metric':'checks','ref':'run:'+str(r['id']),'title':item['name'],'at':r['started_at'],'status':r['status'],'target':{'source':r['source_id']}})
    discoveries={'discovery:'+r['id']:r for r in data['discoveries']}
    intake_titles={'intake:'+r['id']:{'title':store.decode(r['data'],{}).get('name',r['id'])} for r in data['intake']}
    events={}
    unique={m:set() for m in METRICS}
    source_unique={}
    contents={r['kind']+':'+r['id']:r for r in data['content']}
    for e in data['events']:
        e['payload']=store.decode(e['payload'],{});events.setdefault(e['ref'],[]).append(e)
        if e['action'] not in METRICS or day_of(e['created_at'])!=day:continue
        sid=e['source_id'];r=row(sid);m=e['action'];key=(e['ref'],e['event_key']) if m in ('organized','published_new','published_update') else e['ref']
        source_unique.setdefault((sid,m),set()).add(key);unique[m].add(key)
        doc=discoveries.get(e['ref']) or contents.get(e['ref']) or intake_titles.get(e['ref']) or {}
        title=doc.get('title') or store.decode(doc.get('draft_json'),{}).get('name') or e['ref']
        target={'kind':doc['kind'],'id':doc['id']} if 'kind' in doc else {'ref':e['ref']}
        details.append({'source':sid,'metric':m,'ref':e['ref'],'title':title,'at':e['created_at'],'event_key':e['event_key'],'target':target})
    for (sid,m),keys in source_unique.items():row(sid)[m]=len(keys)
    intakes={'intake:'+t['id']:t for t in data['intake']}
    publications={}
    for h in data['history']:publications[h['kind']+':'+h['item_id']]=h
    inbox={r['ref']:r for r in data['inbox']}
    links={}
    for link in data['links']:links.setdefault(link['kind']+':'+link['item_id'],[]).append(link['ref'])
    candidates={r['ref']:r for r in data['candidates']}
    def material_rows(ref):
        if ref.startswith('discovery:'):return store.decode(discoveries.get(ref,{}).get('materials'),[])
        if ref.startswith('intake:'):
            r=intakes.get(ref);v=store.decode(r['data'],{}) if r else {}
            return [{'title':v['name']+' · '+m['key'],'url':m['url'],'body':m['body'],'coverage':m['coverage'],'locator':m['locator'],'content_hash':m['hash'],'source_id':v['source_id'],'intake_state':r['state']} for m in v.get('materials',[])]
        if ref.startswith('record:'):return [{k:v for k,v in m.items() if k not in ('record_id','retrieved_at')} for m in data['evidence'] if m['record_id']==ref[7:]]
        m=candidates.get(ref)
        return [{'title':m['title'],'url':m['url'],'body':m['summary'],'coverage':'discovery_summary','locator':'采集候选摘要，非完整原文'}] if m else []
    for key,c in contents.items():
        draft=store.decode(c['draft_json'],{});published=store.decode(c['published_json'],None)
        if draft==published:continue
        source_ref=c['source_ref'];sid=(discoveries.get(source_ref) or intakes.get(source_ref) or {}).get('source_id') or (candidates.get(source_ref,{}).get('source') if source_ref.startswith(('record:','tool:')) else None) or LOCAL
        r=row(sid);ev=events.get(key,[])
        ready=next((e for e in reversed(ev) if e['action']=='organized' and e['payload'].get('version')==c['draft_version']),None)
        if ready:
            refs=links.get(key,[])[:]
            if source_ref and source_ref not in refs:refs.append(source_ref)
            evidence=hashlib.sha256(dump([{k:v for k,v in m.items() if k!='retrieved_at'} for ref in refs for m in material_rows(ref)]).encode()).hexdigest()
            if evidence!=ready['payload'].get('evidence'):
                ready=None
                issue('review_stale',key,sid,draft.get('name',key)+'：整理后的原始材料已变化','重新核对来源，再提交复核',{'kind':c['kind'],'id':c['id']},0,evidence)
        stage='review_pending' if ready else 'organize_pending';r[stage]+=1
        lastpub=max((e['created_at'] for e in ev if e['action'] in ('published_new','published_update')),default='')
        starts=[e['created_at'] for e in ev if e['action'] in ('selected','edited') and e['created_at']>lastpub]
        entered=ready['created_at'] if ready else min(starts,default=None);waiting=age(entered)
        if waiting is None:r['unknown_wait_count']+=1
        else:r['oldest_wait_days']=max(r['oldest_wait_days'] or 0,waiting)
        target={'kind':c['kind'],'id':c['id']};title=draft.get('name','未命名内容')
        details.append({'source':sid,'metric':stage,'ref':key,'title':title,'at':entered,'wait_days':waiting,'target':target})
        if c['kind']!='charts':
            missing=[label for field,label in [('name','名称'),('sources','来源'),('interpretation','解读')] if not draft.get(field)]
            if draft.get('sources') and any(not x.get('url','').startswith('https://') for x in draft['sources']):missing.append('有效 HTTPS 原文链接')
            if missing:issue('draft_missing',key,sid,title+'：缺必要字段','、'.join(missing),target,1)
            mats=draft.get('reading_materials',[])
            if any(m.get('approved') is not True or m.get('coverage') in ('unavailable','withdrawn') for m in mats):issue('material_review',key,sid,title+'：材料需要复核','有材料未确认或当前不可读',target,1)
        if ready:issue('review',key,sid,title+'：等待复核发布','整理已完成，仍需核对并明确发布',target,1,str(c['draft_version']))
        if waiting is not None and waiting>=3:issue('waiting',key,sid,title+'：等待已超过三天','当前阶段尚未完成；重复保存不会清零等待时间',target,2)
    for ref,d in discoveries.items():
        status=inbox.get(ref,{}).get('status','pending')
        if status!='selected':continue
        meta=store.decode(d['metadata'],{});mats=store.decode(d['materials'],[])
        if not any(m.get('body') and m.get('coverage') in ('full_text','excerpt','abstract') for m in mats):
            issue('material_missing',ref,d['source_id'],d['title']+'：材料待补充','；'.join(meta.get('gaps',[])) or '选中候选没有可核对的材料；可补充材料或明确仅链接范围',{'ref':ref},2)
    for key,c in contents.items():
        if not c['published_json']:continue
        published=store.decode(c['published_json'],{});checked=published.get('checked_at','')
        for ref in links.get(key,[]):
            d=discoveries.get(ref)
            last=publications.get(key,{})
            changed=bool(d and ((last.get('created_at') and d['discovered_at']>last['created_at']) or (not last and (day_of(d['discovered_at']) or '')>checked)))
            if changed:
                issue('published_changed',key,d['source_id'],published.get('name',c['id'])+'：原始材料有后续变化','关联来源在网站最后核对之后发生变化，请重新核对',{'kind':c['kind'],'id':c['id']},0,d['fingerprint'])
    for c in data['conflicts']:
        issue('fact_conflict',c['id'],c['source_id'],c['title']+'：已登记事实冲突','字段 '+c['field']+' 的候选事实尚未完成复核；保留原始证据，不自动判断真假',{'ref':'record:'+c['record_id']},0,c['alternatives'])
    for j in data['jobs']:
        issue('organization_failed',j['record_id']+':'+j['stage'],j['source_id'],j['title']+'：整理任务失败',j['error'] or '整理任务异常，需核对服务和材料',{'ref':'record:'+j['record_id']},0)
    stored={i['id']:i for i in data['issues']}
    for i in issues:
        old=stored.get(i['id']);same=old and old['fingerprint']==i['fingerprint'] and old['status']!='resolved'
        i.update(first_seen_at=old['first_seen_at'] if old else None,status=old['status'] if same else 'open',review_on=old['review_on'] if same else None,note=old['note'] if old else '')
        if i['status']=='later' and i['review_on']<=today():i['status']='open'
    issues.sort(key=lambda i:(i['status']=='later',i['priority'],i['first_seen_at'] or '9999',i['id']))
    total={m:len(unique[m]) if tracked else None for m in METRICS}
    total.update(checks=sum(r['checks'] for r in rows.values()),attempts=sum(r['attempts'] for r in rows.values()),planned_sources=sum(bool(s['enabled']) for s in data['sources'] if scheduled(s)),organize_pending=sum(r['organize_pending'] for r in rows.values()),review_pending=sum(r['review_pending'] for r in rows.values()))
    if metric:
        found=[d for d in details if d['metric']==metric and (not source or d['source']==source)]
        # Multiple source observations share one unique item in the global drilldown.
        found=list({(d['ref'],(d.get('at') if metric=='checks' else d.get('event_key')) if metric in ('organized','published_new','published_update','checks') else ''):d for d in found}.values())
    else:found=[]
    return {'day':day,'timezone':'Asia/Shanghai','tracking_since':since,'tracking_complete_day':bool(since and day>day_of(since)),
      'scope':'当日动作与当前积压分开；获取按条目/覆盖类型去重；来源可交叉归属，全站去重。升级前的阶段动作未记录，不补造。',
      'totals':total,'sources':list(rows.values()),'issues':issues,'resolved':[{**store.decode(r['data'],{}),'resolved_at':r['resolved_at'],'note':r['note']} for r in data['issues'] if r['status']=='resolved' and r['id'] not in {i['id'] for i in issues}], 'details':found,'generated_at':stamp()}


def refresh():
    live=snapshot();items=live['issues'];ids={i['id'] for i in items}
    with editorial_transaction() as db:
        old={r['id']:dict(r) for r in db.execute('SELECT * FROM fieldtofit_operation_issues').fetchall()}
        for i in items:
            previous=old.get(i['id']);same=previous and previous['fingerprint']==i['fingerprint'] and previous['status']!='resolved'
            db.execute('INSERT INTO fieldtofit_operation_issues VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET fingerprint=excluded.fingerprint,data=excluded.data,status=excluded.status,review_on=excluded.review_on,last_seen_at=excluded.last_seen_at,resolved_at=NULL,version=fieldtofit_operation_issues.version+1',
                (i['id'],i['fingerprint'],dump(i),i['status'] if same else 'open',i['review_on'] if same else None,i['note'],previous['first_seen_at'] if previous else stamp(),stamp(),None,1))
        for ident,o in old.items():
            if ident not in ids and o['status']!='resolved':db.execute("UPDATE fieldtofit_operation_issues SET status='resolved',resolved_at=?,version=version+1 WHERE id=?",(stamp(),ident))
    return {'ok':True,'active_issues':len(items)}


def defer(ident,data):
    if not isinstance(data.get('note'),str) or not data['note'].strip():fail('请说明处理原因')
    review=data.get('review_on')
    try:valid=date.fromisoformat(review)>=date.fromisoformat(today())
    except (ValueError,TypeError):valid=False
    if not valid:fail('请选择今天或之后的复查日期')
    live=next((i for i in snapshot()['issues'] if i['id']==ident),None)
    if not live or data.get('fingerprint')!=live['fingerprint']:fail('问题已变化，请刷新','issue_conflict',409)
    refresh()
    with editorial_transaction() as db:
        r=db.execute('SELECT fingerprint FROM fieldtofit_operation_issues WHERE id=?',(ident,)).fetchone()
        if not r or r['fingerprint']!=live['fingerprint']:fail('问题已变化','issue_conflict',409)
        db.execute("UPDATE fieldtofit_operation_issues SET status='later',review_on=?,note=?,version=version+1 WHERE id=?",(review,data['note'][:2000],ident))
    return {'ok':True}


def upgrade():
    schema=(Path(__file__).parent/'schema.sql').read_text().split('CREATE TABLE IF NOT EXISTS fieldtofit_operation_events',1)[1]
    statements=[(s.strip(),()) for s in ('CREATE TABLE IF NOT EXISTS fieldtofit_operation_events'+schema).split(';') if s.strip()]
    statements.append(("INSERT OR IGNORE INTO knowledge_settings(key,value,updated_at) VALUES('operation_tracking_since',?,?)",(stamp(),stamp())))
    with get_db() as db:
        if isinstance(db,TursoConnection):db.atomic_statements(statements)
        else:
            db.execute('BEGIN IMMEDIATE')
            for sql,args in statements:db.execute(sql,args)
    return {'ok':True}
