"""Private daily CW coverage. Fetches are observations, never semantic approval."""
import hashlib
import json
import time
import uuid
from datetime import date
from backend.db import get_db
from backend.knowledge import content_workspace as ws, stewardship as s
from backend.knowledge.corrections import public_item, value_at
from backend.knowledge.workspace_transactions import editorial_transaction
from backend.knowledge.platform import text, integer


def plan(item):
    return [{'url': r['url'], 'title': r['title'], 'required': True, 'scope': '官方版本、获取方式、许可、弃用与重大限制'} for r in item['sources']]


def configure(ident, data):
    from backend.knowledge.platform_watch import valid_url
    if not isinstance(ident,str) or not ident.startswith('CW-'):ws.fail('检查计划仅支持CW档案')
    entries = data.get('entries')
    if not isinstance(entries, list) or not 1<=len(entries)<=12: ws.fail('登记1–12个官方入口')
    checked=[];seen=set()
    for row in entries:
        url=valid_url(row.get('url',''))
        if url in seen: ws.fail('官方入口不能重复')
        seen.add(url)
        if not isinstance(row.get('required'),bool): ws.fail('请明确必要入口')
        checked.append({'url':url,'title':text(row.get('title'),'入口标题',500),'required':row['required'], 'scope':text(row.get('scope'),'核对范围',2000)})
    if not any(r['required'] for r in checked): ws.fail('至少登记一个必要入口')
    with editorial_transaction() as db:
        public_item(ident,db)
        old=db.execute('SELECT * FROM fieldtofit_object_check_plans WHERE object_id=?',(ident,)).fetchone()
        if data.get('version',0)!=(old['version'] if old else 0): ws.fail('入口计划已变化','plan_conflict',409)
        db.execute('INSERT INTO fieldtofit_object_check_plans VALUES(?,?,?,?) ON CONFLICT(object_id) DO UPDATE SET data=excluded.data,version=excluded.version,updated_at=excluded.updated_at',(ident,ws.dump(checked),(old['version'] if old else 0)+1,ws.stamp()))
    return {'ok':True,'effective':'下一次日清单；当日已冻结入口保持'}


def start(day=None):
    day=day or ws.today(); date.fromisoformat(day)
    if day>ws.today(): ws.fail('不能提前记录未来日检查')
    with editorial_transaction() as db:
        existing=db.execute('SELECT * FROM fieldtofit_object_check_runs WHERE day=?',(day,)).fetchone()
        if not existing:
            if day!=ws.today():ws.fail('不能用当前对象清单补造历史覆盖')
            items=s.raw_items(db); configured={r['object_id']:r for r in db.execute('SELECT * FROM fieldtofit_object_check_plans').fetchall()}
            aliases=s.rows(db,'fieldtofit_steward_aliases')
            targets=[]
            for ident,item in items.items():
                if not ident.startswith('CW-') or item.get('state')!='published' or s.resolve(ident,db,aliases=aliases)!=ident:continue
                targets.append({'id':ident,'name':item['name'],'type':item['type'], 'entries':json.loads(configured[ident]['data']) if ident in configured else plan(item),
                                'plan_version':configured[ident]['version'] if ident in configured else 0})
            db.execute('INSERT INTO fieldtofit_object_check_runs VALUES(?,?,?)',(day,ws.stamp(),ws.dump(targets)))
    return overview(day)


def overview(day=None):
    day=day or ws.today(); date.fromisoformat(day)
    with get_db() as db:
        run=db.execute('SELECT * FROM fieldtofit_object_check_runs WHERE day=?',(day,)).fetchone()
        plans={r['object_id']:r for r in db.execute('SELECT * FROM fieldtofit_object_check_plans').fetchall()}
        attempts=[{**dict(r),'data':json.loads(r['data'])} for r in db.execute('''WITH ranked AS (
          SELECT *,ROW_NUMBER() OVER (PARTITION BY object_id ORDER BY created_at DESC,id DESC) n
          FROM fieldtofit_object_check_attempts WHERE day=?)
          SELECT id,day,object_id,created_at,CASE WHEN n=1 THEN data ELSE json_remove(data,'$.observations','$.baseline') END data
          FROM ranked ORDER BY created_at,id''',(day,)).fetchall()]
        targets=json.loads(run['targets']) if run else []
        current=s.raw_items(db)
        aliases=s.rows(db,'fieldtofit_steward_aliases')
    totals={'expected':len(targets),'completed':0,'changed':0,'unchanged':0,'failed':0,'incomplete':0};rows=[]
    for target in targets:
        history=[r for r in attempts if r['day']==day and r['object_id']==target['id']]
        latest=history[-1]['data'] if history else {}
        state=latest.get('status','incomplete')
        item=current.get(target['id']); baseline_changed=False
        if latest.get('baseline_hash'):
            if not item or item.get('state')!='published' or s.resolve(target['id'],aliases=aliases)!=target['id']:baseline_changed=True
            else:
                projected=ws.render('watch',{**ws.seeds()['watch'],'items':[item]})['items'][0]
                projected.pop('maintenance',None);projected.pop('publication',None)
                baseline_changed=s.digest(projected)!=latest['baseline_hash']
        if baseline_changed:state='incomplete'
        totals[state]+=1;totals['completed']+=int(state in ('changed','unchanged'))
        row={**target,'status':state,'baseline_changed':baseline_changed, 'last_attempt':history[-1]['created_at'] if history else None,
             'latest':latest,'attempt_id':history[-1]['id'] if history else '', 'history':history,
             'plan_entries_current':json.loads(plans[target['id']]['data']) if target['id'] in plans else target['entries'],
             'plan_version_current':plans[target['id']]['version'] if target['id'] in plans else 0}
        rows.append(row)
    return {'day':day,'created_at':run['created_at'] if run else None,'totals':totals,'items':rows,
            'scope':'已发布CW当次冻结清单；HTTP获取不算档案核对完成；公共内容与日期不会自动更新。'}


def append(day, ident, result):
    attempt=uuid.uuid4().hex
    with editorial_transaction() as db:
        run=db.execute('SELECT targets FROM fieldtofit_object_check_runs WHERE day=?',(day,)).fetchone()
        if not run or not any(t['id']==ident for t in json.loads(run['targets'])):ws.fail('对象不在当天冻结清单')
        db.execute('INSERT INTO fieldtofit_object_check_attempts VALUES(?,?,?,?,?)',(attempt,day,ident,ws.dump(result),ws.stamp()))
    return {'attempt_id':attempt,**result}


def scan(day, ident):
    if day!=ws.today(): ws.fail('重试按实际当日登记，不能补造历史检查')
    board=overview(day); target=next((r for r in board['items'] if r['id']==ident),None)
    if not target:ws.fail('对象不在当天清单')
    with get_db() as db:
        baseline=public_item(ident,db)
        prior=[{'changes':json.loads(r['changes'] or '[]')} for r in db.execute("SELECT json_extract(data,'$.changes') changes FROM fieldtofit_object_check_attempts WHERE object_id=? ORDER BY created_at DESC,id DESC",(ident,)).fetchall()]
    from backend.knowledge.sources import fetch,plain_html,COLLECTION_DEADLINE
    observations=[];started=time.monotonic()
    deadline_token=COLLECTION_DEADLINE.set(started+90)
    try:
        for entry in target['entries']:
            if time.monotonic()-started>90:
                observations.append({**entry,'fetched':False,'error':'本次预算已到，仍待续查'});continue
            try:
                raw,url,ctype=fetch(entry['url'],max_bytes=500000)
                if 'pdf' in ctype or raw.startswith(b'%PDF'):raise ValueError('PDF入口需要按文件页另行核对，不能把二进制当作已读原文')
                body=raw.decode('utf-8',errors='replace');body=plain_html(body) if 'html' in ctype else body
                if not body.strip():raise ValueError('没有可核对正文')
                if len(body)>100000:raise ValueError('正文超出单入口范围；需登记具体页面')
                observations.append({**entry,'fetched':True,'final_url':url,'body':body,'content_hash':hashlib.sha256(body.encode()).hexdigest(),'checked_at':ws.stamp()})
            except Exception as exc:
                observations.append({**entry,'fetched':False,'error':str(exc)[:1000],'checked_at':ws.stamp()})
    finally:
        COLLECTION_DEADLINE.reset(deadline_token)
    pending=[];seen=set()
    for attempt in prior:
        for change in attempt.get('changes',[]):
            key=ws.dump([change['field'],change['after'],change['source_url']])
            try: before=value_at(baseline,change['field'])
            except ws.PlatformError:continue
            if before!=change['after'] and key not in seen:
                pending.append({**change,'before':before,'pending_from_previous':True});seen.add(key)
    return append(day,ident,{'baseline':baseline,'baseline_hash':s.digest(baseline),'observations':observations,'changes':pending,
                            'status':'failed' if any(e['required'] and not e['fetched'] for e in observations) else 'incomplete',
                            'reason':'来源已获取，仍需对照当前已审档案；抓取成功不代表没有变化。'})


def review(day, ident, data):
    if day!=ws.today():ws.fail('按实际当日记录复核，不补造历史')
    with editorial_transaction() as db:
        previous=db.execute('SELECT * FROM fieldtofit_object_check_attempts WHERE day=? AND object_id=? ORDER BY created_at DESC,id DESC LIMIT 1',(day,ident)).fetchone()
        if not previous or previous['id']!=data.get('attempt_id'):ws.fail('来源尝试已变化，请重新读取','attempt_conflict',409)
        last=json.loads(previous['data']); baseline=public_item(ident,db)
        if s.digest(baseline)!=last['baseline_hash']:ws.fail('已审档案已变化，请重新获取并核对','baseline_conflict',409)
        reason=text(data.get('reason'),'核对说明',6000)
        changes=data.get('changes',[])
        if not isinstance(changes,list) or len(changes)>30:ws.fail('变化须为至多30项列表')
        checked=[]
        for change in changes:
            field=change.get('field');before=value_at(baseline,field)
            if before!=change.get('before') or before==change.get('after'):ws.fail('变化必须对照当前已审字段')
            source=next((r for r in last['observations'] if r.get('fetched') and r['url']==change.get('source_url')),None)
            quote=text(change.get('quote'),'定位引文',2000)
            if not source or quote not in source['body']:ws.fail('引文必须来自本次取得的官方原文')
            source_day=change.get('source_date')
            if source_day:
                date.fromisoformat(source_day)
                if source_day>ws.today():ws.fail('来源日期不能在未来')
            checked.append({'field':field,'before':before,'after':change.get('after'),'source_url':source['url'],'quote':quote,'offset':source['body'].index(quote),
                            'content_hash':source['content_hash'],'source_date':source_day,'upstream_version':text(change.get('upstream_version',''),'来源版本',200,False)})
        completed=data.get('completed') is True and all(r.get('fetched') for r in last['observations'] if r['required']) and bool(last['observations'])
        if data.get('completed') is True and not completed:ws.fail('必要入口未齐，不能登记已完成')
        # An unchanged fetch/retry cannot silently erase an unresolved finding.
        older=db.execute("SELECT json_extract(data,'$.changes') changes FROM fieldtofit_object_check_attempts WHERE object_id=? ORDER BY created_at DESC,id DESC",(ident,)).fetchall()
        seen={ws.dump([r['field'],r['after'],r['source_url']]) for r in checked}
        for attempt in older:
            old={'changes':json.loads(attempt['changes'] or '[]')}
            for change in old.get('changes',[]):
                key=ws.dump([change['field'],change['after'],change['source_url']])
                try: before=value_at(baseline,change['field'])
                except ws.PlatformError:continue
                if before!=change['after'] and key not in seen:
                    checked.append({**change,'before':before,'pending_from_previous':True});seen.add(key)
        status='changed' if completed and checked else 'unchanged' if completed else 'failed' if any(r['required'] and not r.get('fetched') for r in last['observations']) else 'incomplete'
        result={**last,'status':status,'changes':checked,'reason':reason,'reviewed_at':ws.stamp()}
        db.execute('INSERT INTO fieldtofit_object_check_attempts VALUES(?,?,?,?,?)',(uuid.uuid4().hex,day,ident,ws.dump(result),ws.stamp()))
    return overview(day)
