"""Reviewed identities/relations and observational material health for D-/CW- content.

No collector publishes, merges, deletes body text or changes editorial review dates.
All public mutations use preview-bound optimistic transactions and append events.
"""
import copy
import hashlib
import json
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from backend.db import get_db, execute_statements
from backend.knowledge import content_workspace as ws
from backend.knowledge.platform import PlatformError, text, integer
from backend.knowledge.workspace_transactions import editorial_transaction

RELATIONS = {'publisher','family','version','release','implementation','integration','related'}

def digest(v): return hashlib.sha256(ws.dump(v).encode()).hexdigest()
def kind(ident):
    from backend.knowledge.content_materials import is_content
    if not is_content(ident): ws.fail('请选择当前动态或持续关注编号')
    return 'news' if ident.startswith('D-') else 'watch'

def rows(db,table):
    try:return [dict(r) for r in db.execute('SELECT * FROM '+table).fetchall()]
    except Exception as e:
        if 'no such table: '+table not in str(e):raise
        return []

def upgrade():
    sql=(Path(__file__).parent/'schema.sql').read_text().split('CREATE TABLE IF NOT EXISTS fieldtofit_steward_actions',1)[1]
    with get_db() as db:execute_statements(db,[(s.strip(),()) for s in ('CREATE TABLE IF NOT EXISTS fieldtofit_steward_actions'+sql).split(';') if s.strip()])
    return {'ok':True}

def event(db,ident,action,data=None):
    # Callers supply only public identity/status metadata, never review notes or bodies.
    db.execute('INSERT INTO fieldtofit_steward_events(object_id,kind,data,created_at) VALUES(?,?,?,?)',(ident,action,ws.dump(data or {}),ws.stamp()))

def publication_event(db,kind_,ident,old,new):
    if kind_=='charts':return
    event(db,ident,'withdrawn' if new.get('state')=='withdrawn' else 'updated' if old else 'added',
          {'from_revision':digest(old) if old else None,'to_revision':digest(new)})
    previous={m['id']:m for m in (old or {}).get('reading_materials',[])}
    current={m['id']:m for m in new.get('reading_materials',[])}
    for mid,m in previous.items():
        if new.get('state')=='withdrawn' or mid not in current or (m.get('body') and not current[mid].get('body')):
            event(db,ident,'material_withdrawn',{'material_id':mid,'availability':'unavailable'})
        elif current[mid]!=m:event(db,ident,'material_updated',{'material_id':mid,'from_revision':digest(m),'to_revision':digest(current[mid])})
    for mid,m in current.items():
        if mid not in previous:event(db,ident,'material_added',{'material_id':mid,'to_revision':digest(m)})

def raw_items(db):
    items={}
    for k in ('news','watch'):
        r=db.execute('SELECT published_json FROM fieldtofit_content_sets WHERE kind=?',(k,)).fetchone()
        data=json.loads(r[0]) if r else json.loads((ws.CONTENT/(k+'.json')).read_text())
        items.update({i['id']:i for i in data['items']})
    return items

def resolve(ident,db=None,aliases=None):
    if db is None:
        with get_db() as conn:return resolve(ident,conn)
    links={r['source_id']:r['target_id'] for r in (aliases if aliases is not None else rows(db,'fieldtofit_steward_aliases'))}
    current=ident;seen=set()
    while current in links:
        if current in seen:ws.fail('归并链存在循环','merge_cycle',409)
        seen.add(current);current=links[current]
    return current

def public_status(ident,db=None,context=None):
    if db is None:
        with get_db() as conn:return public_status(ident,conn)
    context=context or {'items':raw_items(db),**{t:rows(db,'fieldtofit_steward_'+t) for t in ('aliases','links','checks')}}
    all_items=context['items'];canonical=resolve(ident,db,context['aliases']);item=all_items.get(canonical)
    if not item or item.get('state')!='published':
        # Minimal tombstone; no draft, private reason or withdrawn body.
        return {'id':ident,'canonical_id':canonical,'availability':'unavailable','relationships':[],'materials':[]}
    related=[]
    for row in context['links']:
        left_id=resolve(row['source_id'],db,context['aliases']);right_id=resolve(row['target_id'],db,context['aliases'])
        if canonical not in (left_id,right_id) or left_id==right_id:continue
        other=right_id if left_id==canonical else left_id
        data=json.loads(row['data'])
        if other in all_items:
            target=all_items.get(resolve(other,db,context['aliases']))
            if not target or target.get('state')!='published':continue
            name=target['name'];url='/for-you#'+('news-' if other.startswith('D-') else 'watch-')+other.lower()
        else:name=data['target_name'];url=data['target_url']
        related.append({'id':row['id'],'target_id':other,'name':name,'url':url,'direction':'outgoing' if left_id==canonical else 'incoming',**data})
    materials=[]
    current_materials={(m['id'],m['url']) for m in item.get('reading_materials',[]) if m.get('coverage')!='withdrawn'}
    for row in context['checks']:
        if row['object_id']==canonical and (row['material_id'],row['url']) in current_materials:
            data=json.loads(row['data']);materials.append({'id':row['material_id'],'url':row['url'],**{k:data.get(k) for k in ('availability','last_checked_at','last_success_at','failure_days','error','needs_review','review_priority','changed','last_decision','public_note','last_decision_at')}})
    result={'id':ident,'canonical_id':canonical,'availability':'merged' if canonical!=ident else 'available','relationships':related,'materials':materials,
            'scope':'Current maintenance observations; separate from fixed publication/material revision. Access success is not factual revalidation.'}
    result['status_revision']=digest(result)
    return result

def decorate(entries):
    with get_db() as db:
        # Avoid changing established payloads until there is actual maintenance data.
        context={t:rows(db,'fieldtofit_steward_'+t) for t in ('aliases','links','checks')}
        if not any(context.values()):return entries
        context['items']=raw_items(db)
        return [{**i,'maintenance':public_status(i['id'],db,context)} for i in entries]

def suggestions():
    from backend.knowledge.store import canonical_url
    with get_db() as db:
        records=[ws.row_item(r) for r in db.execute("SELECT * FROM fieldtofit_content_items WHERE kind IN ('news','watch')").fetchall()]
        ignored={(r['source_id'],r['target_id']):json.loads(r['data']) for r in rows(db,'fieldtofit_steward_decisions')}
        aliases={r['source_id'] for r in rows(db,'fieldtofit_steward_aliases')}
    records=[r for r in records if r['id'] not in aliases and r['state']!='withdrawn'];found=[]
    for n,left in enumerate(records):
        a=left['draft'];au={canonical_url(s['url']) for s in a.get('sources',[])}
        for right in records[n+1:]:
            b=right['draft'];pair=tuple(sorted((a['id'],b['id'])));fingerprint=digest([a,b] if a['id']<b['id'] else [b,a])
            if ignored.get(pair,{}).get('fingerprint')==fingerprint:continue
            bu={canonical_url(s['url']) for s in b.get('sources',[])};reasons=[]
            if au & bu:reasons.append('共享来源入口：'+next(iter(sorted(au & bu))))
            if a.get('name','').casefold()==b.get('name','').casefold():reasons.append('名称一致；仍需核对作者、产品与版本')
            if not reasons:continue
            same_event=left['kind']==right['kind']=='news' and a.get('event_date') and a.get('event_date')==b.get('event_date')
            found.append({'source':a['id'],'target':b['id'],'source_name':a['name'],'target_name':b['name'],'reasons':reasons,
                'suggestion':'核对是否同一事件' if same_event else '核对对象身份或仅建立关联','fingerprint':fingerprint})
    return found[:100]

def dashboard():
    with get_db() as db:
        records=[ws.row_item(r) for r in db.execute("SELECT * FROM fieldtofit_content_items WHERE kind IN ('news','watch') ORDER BY id").fetchall()]
        checks=rows(db,'fieldtofit_steward_checks');actions=rows(db,'fieldtofit_steward_actions');items=raw_items(db)
        issues=[]
        for row in checks:
            d=json.loads(row['data']);obj=items.get(row['object_id'],{})
            if obj.get('state')!='published' or not any(m['id']==row['material_id'] and m['url']==row['url'] and m.get('coverage')!='withdrawn' for m in obj.get('reading_materials',[])):continue
            impacts=[i['id'] for i in items.values() if i.get('state')=='published' and any(m.get('url')==row['url'] for m in i.get('reading_materials',[]))]
            if d.get('needs_review') and (not d.get('review_after') or d['review_after']<=ws.today()):
                issues.append({**row,**d,'data':None,'check_revision':digest(d),'name':obj.get('name',row['object_id']),'affected_objects':impacts,
                    'materials':[{k:m.get(k) for k in ('id','title','url','coverage','checked_at')} for m in obj.get('reading_materials',[])],
                    'affected_points':[{'title':point['title'],'locator':point.get('locator','')} for point in obj.get('interpretation',[]) if set(point.get('source_ids',[])) & {m.get('id') for m in obj.get('sources',[]) if m.get('url')==row['url']}],
                    'impact_scope':'Only explicit source-ID references are located; other prose requires manual review'})
        available=bool(db.execute("SELECT name FROM sqlite_master WHERE name='fieldtofit_steward_actions'").fetchone())
        return {'available':available,'items':[{'id':r['id'],'kind':r['kind'],'name':r['draft']['name'],'state':r['state'],'draft_version':r['draft_version']} for r in records],
            'suggestions':suggestions(),'issues':sorted(issues,key=lambda r:(r.get('review_priority',1),r['last_checked_at'])),
            'actions':[{k:r[k] for k in ('id','action','source_id','target_id','reason','created_at','undone_at')} for r in actions][-50:][::-1],
            'links':rows(db,'fieldtofit_steward_links'),'interval_days':1,'scope':'Private maintenance workspace; reading never publishes'}

def combine(source,target,choices):
    merged=copy.deepcopy(target);conflicts=[]
    # Identity comes from the retained record. Never silently choose conflicting prose.
    for key in ('name','organization','title','summary','introduction','type','event_date','source_published_at','note','editor','attention','origin','submission','submission_review'):
        if key not in merged and key in source:merged[key]=copy.deepcopy(source[key])
        if key in source and key in target and source[key]!=target[key]:
            conflicts.append({'field':key,'source':source[key],'target':target[key]})
            if choices.get(key) not in ('source','target'):continue
            merged[key]=copy.deepcopy(source[key] if choices[key]=='source' else target[key])
    prefix=source['id'].lower()+'-';mapping={}
    for s in source.get('sources',[]):
        match=next((v for v in merged['sources'] if v['url']==s['url']),None)
        if 'id' in s:mapping[s['id']]=match['id'] if match else prefix+s['id']
        if not match:merged['sources'].append({**s,**({'id':mapping[s['id']]} if 'id' in s else {})})
    for p in source.get('interpretation',[]):
        point=copy.deepcopy(p)
        if 'source_ids' in point:point['source_ids']=[mapping[v] for v in point['source_ids']]
        if point not in merged['interpretation']:merged['interpretation'].append(point)
    for key in ('blocks','related'):
        if key in source:
            merged.setdefault(key,[])
            for v in source[key]:
                if v not in merged[key]:merged[key].append(copy.deepcopy(v))
    merged.setdefault('reading_materials',[])
    for m in source.get('reading_materials',[]):
        if not any(m==other for other in merged['reading_materials']):merged['reading_materials'].append({**m,'id':prefix+m['id']})
    merged['checked_at']=ws.today()
    if 'highlight' in merged:merged['highlight']=bool(target.get('highlight'))
    return merged,conflicts


def plan(data,db):
    action=data.get('action');source=text(data.get('source'),'source',100);target=text(data.get('target',''),'target',100,False)
    left=ws.detail(kind(source),source,db);right=ws.detail(kind(target),target,db) if target else None
    # Include complete read state in the token to invalidate previews after independent edits.
    sets=[dict(r) for r in db.execute('SELECT * FROM fieldtofit_content_sets').fetchall()]
    aliases=rows(db,'fieldtofit_steward_aliases');links=rows(db,'fieldtofit_steward_links');actions=rows(db,'fieldtofit_steward_actions')
    proposed=None;conflicts=[];errors=[];extra={};before={source:left};after={}
    if right:before[target]=right
    if action in ('merge','group'):
        if not right or source==target or kind(source)!=kind(target):ws.fail('仅能归并同类条目；动态与资源请建立关联')
        if resolve(source,db)!=source or resolve(target,db)!=target:ws.fail('请使用当前保留的对象编号','merge_conflict',409)
        if left['state']=='withdrawn' or right['state']=='withdrawn':ws.fail('请先通过原审核流程恢复撤下条目')
        proposed,conflicts=combine(left['draft'],right['draft'],data.get('choices',{}))
        if any(data.get('choices',{}).get(c['field']) not in ('source','target') for c in conflicts):errors.append('逐项选择冲突字段后重新预览')
        after[target]=proposed
        if action=='merge':after[source]={**(left['published'] or left['draft']),'state':'withdrawn'}
        elif left['published'] is not None:errors.append('私密归组只用于尚未发布的来源条目；已发布内容请使用归并审核')
    elif action=='undo':
        row=next((r for r in actions if r['id']==data.get('merge_id') and r['source_id']==source and r['target_id']==target),None)
        if not row or row['undone_at']:ws.fail('归并记录不可撤销','merge_conflict',409)
        old=json.loads(row['before_json']);expected=json.loads(row['after_json'])
        if not any(a['source_id']==source and a['action_id']==row['id'] for a in aliases):ws.fail('归并链已经变化，请先处理后续归并','merge_conflict',409)
        if resolve(target,db)!=target:ws.fail('保留对象又被归并，请先撤销后续归并','merge_conflict',409)
        changed=right['draft']!=expected[target] or right['published']!=expected[target]
        if changed and data.get('restore_target') is True:errors.append('目标有后续编辑，不能覆盖；请选择保留当前目标后恢复来源条目')
        after[source]=old[source]['published'] or {**old[source]['draft'],'state':'draft'}
        after[target]=old[target]['published'] or old[target]['draft'] if not changed and data.get('restore_target') is True else right['published']
        if after[target] is None:ws.fail('目标没有可保留的已发布版本')
        extra={'target_has_later_edits':changed,'source_draft_will_be_preserved':left['draft']!=expected[source],
               'copied_refs':json.loads(row['payload']).get('copied_refs',[]),'topic_states':json.loads(row['payload']).get('topic_states',{})}
    elif action=='relation':
        from backend.knowledge.platform_watch import valid_url
        if left['state']!='published' or (right and right['state']!='published'):ws.fail('请先审核发布关联对象；未发布候选可以保持独立或归入整理稿')
        relation=data.get('relation')
        if relation not in RELATIONS:ws.fail('请选择关系类型')
        if target==source:ws.fail('不能关联自身')
        extra={'relation':relation,'version':text(data.get('version',''),'version',200,False),'evidence':valid_url(data.get('evidence','')),
               'target_name':right['published']['name'] if right else text(data.get('target_name'),'target_name',200),
               'target_url':('/for-you#'+('news-' if target.startswith('D-') else 'watch-')+target.lower()) if right else valid_url(data.get('target_url','')),
               'node_type':data.get('node_type','object')}
        if extra['node_type'] not in ('object','company','family','version'):ws.fail('不支持的关系目标类型')
        if not target:target='E-'+digest([extra['target_url'],extra['node_type'],extra['target_name'].casefold() if extra['node_type']!='company' else '',extra['version']])[:20]
    elif action=='relation_remove':
        row=next((r for r in links if r['id']==data.get('link_id') and r['source_id']==source),None)
        if not row:ws.fail('关联已变化，请刷新','relation_conflict',409)
        target=row['target_id'];extra=json.loads(row['data'])
    elif action=='separate':
        if not right or source==target:ws.fail('请选择两个不同条目')
    else:ws.fail('不支持的维护动作')
    focused=[]
    if after:
        for k in {kind(i) for i in after}:
            base=json.loads(next(r['published_json'] for r in sets if r['kind']==k))
            existing={i['id'] for i in base['items']}
            base['items']=[after.get(i['id'],i) for i in base['items']]+[v for i,v in after.items() if kind(i)==k and i not in existing]
            base['reviewed_at']=ws.today()
            try:
                for ident,value in after.items():
                    if kind(ident)==k and value.get('state')=='published' and action!='group':ws.gate(k,ident,value,base)
                rendered=ws.render(k,base);focused.extend(i for i in rendered['items'] if i['id'] in after)
            except (ValueError,KeyError,PlatformError) as exc:
                if action=='group':extra['publication_blocker']='待整理稿尚未满足公开展示要求，请在内容库补全解读与逐份材料审核。'
                else:errors.append(str(exc))
    if action=='group':
        ws.draft_shape(kind(target),after[target])
        extra['draft_summary']={k:after[target].get(k) for k in ('id','name','summary','introduction','sources')}
        extra['material_count']=len(after[target].get('reading_materials',[]))
    request_data={k:v for k,v in data.items() if k not in ('review_token','confirmed')}
    token=digest([request_data,before,sets,aliases,links,actions])
    return {'ready':not errors,'errors':errors,'conflicts':conflicts,'review_token':token,'source':source,'target':target,'action':action,
            'before':before,'after':after,'extra':extra,'preview':focused,'sets':sets,'scope':'Private review only; no publication until confirmed'}


def preview(data):
    with get_db() as db:return plan(data,db)

def apply(data):
    reason=text(data.get('reason'),'reason',2000)
    with editorial_transaction() as db:
        p=plan(data,db)
        if not p['ready']:ws.fail('; '.join(p['errors']))
        if data.get('confirmed') is not True or data.get('review_token')!=p['review_token']:ws.fail('请重新预览并确认','preview_conflict',409)
        aid=uuid.uuid4().hex;source,target=p['source'],p['target'];action=p['action'];stamp=ws.stamp()
        # All reads precede buffered writes, including guard-protected source associations.
        refs=[dict(r) for r in db.execute('SELECT * FROM fieldtofit_item_sources WHERE item_id IN (?,?)',(source,target)).fetchall()]
        from backend.knowledge.operation_board import content_source,event as operation_event
        from backend.knowledge.editorial_batches import published
        origins={i:content_source(db,kind(i),i) for i in p['after']}
        topics={i:[dict(r) for r in db.execute('SELECT id,decision FROM fieldtofit_editorial_topics WHERE kind=? AND item_id=?',(kind(i),i)).fetchall()] for i in p['after']}
        updates=[]
        for k in ({kind(i) for i in p['after']} if action!='group' else set()):
            base=json.loads(next(r['published_json'] for r in p['sets'] if r['kind']==k));known={i['id'] for i in base['items']}
            base['items']=[p['after'].get(i['id'],i) for i in base['items']]+[v for i,v in p['after'].items() if kind(i)==k and i not in known];base['reviewed_at']=ws.today()
            updates.append(('UPDATE fieldtofit_content_sets SET published_json=?,revision=revision+1,updated_at=? WHERE kind=?',(ws.dump(base),stamp,k)))
        for ident,value in p['after'].items():
            if action=='group':
                updates.append(('UPDATE fieldtofit_content_items SET draft_json=?,draft_version=draft_version+1,updated_at=? WHERE kind=? AND id=?',(ws.dump(value),stamp,kind(ident),ident)))
                continue
            current=p['before'][ident]
            draft=value if action=='merge' or current['draft']==current['published'] else current['draft']
            updates.extend([('UPDATE fieldtofit_content_items SET published_json=?,draft_json=?,draft_version=draft_version+1,updated_at=? WHERE kind=? AND id=?',(None if value.get('state')=='draft' else ws.dump(value),ws.dump(draft),stamp,kind(ident),ident)),
                ('INSERT INTO fieldtofit_content_history(kind,item_id,action,reason,snapshot,created_at) VALUES(?,?,?,?,?,?)',(kind(ident),ident,'merge_source' if action=='merge' and ident==source else 'restore_draft' if value.get('state')=='draft' else 'withdraw' if value.get('state')=='withdrawn' else 'publish',reason,ws.dump(value),stamp))])
        if action=='group':
            for ref in refs:
                if ref['item_id']==source:updates.append(('INSERT OR IGNORE INTO fieldtofit_item_sources(kind,item_id,ref) VALUES(?,?,?)',(kind(target),target,ref['ref'])))
            a,b=sorted((source,target))
            fingerprint=digest([p['after'].get(a,p['before'][a]['draft']),p['after'].get(b,p['before'][b]['draft'])])
            updates.append(('INSERT INTO fieldtofit_steward_decisions VALUES(?,?,?) ON CONFLICT(source_id,target_id) DO UPDATE SET data=excluded.data',(a,b,ws.dump({'fingerprint':fingerprint,'grouped_into':target,'at':stamp}))))
        if action=='merge':
            prior_refs={r['ref'] for r in refs if r['item_id']==target}
            data={**data,'topic_states':topics,'copied_refs':[r['ref'] for r in refs if r['item_id']==source and r['ref'] not in prior_refs]}
            updates.append(('INSERT INTO fieldtofit_steward_aliases VALUES(?,?,?)',(source,target,aid)))
            for ref in refs:
                if ref['item_id']==source:updates.append(('INSERT OR IGNORE INTO fieldtofit_item_sources(kind,item_id,ref) VALUES(?,?,?)',(kind(target),target,ref['ref'])))
        elif action=='undo':
            if data.get('restore_target') is True:
                for ref in p['extra']['copied_refs']:
                    updates.append(('DELETE FROM fieldtofit_item_sources WHERE kind=? AND item_id=? AND ref=?',(kind(target),target,ref)))
            updates.extend([('DELETE FROM fieldtofit_steward_aliases WHERE source_id=?',(source,)),('UPDATE fieldtofit_steward_actions SET undone_at=? WHERE id=?',(stamp,data['merge_id']))])
        elif action=='relation':
            lid=digest([source,target,p['extra']['relation'],p['extra']['version']])[:32]
            updates.append(('INSERT INTO fieldtofit_steward_links VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data',(lid,source,target,ws.dump(p['extra']))))
        elif action=='relation_remove':
            updates.append(('DELETE FROM fieldtofit_steward_links WHERE id=?',(data['link_id'],)))
        elif action=='separate':
            a,b=sorted((source,target));fingerprint=digest([p['before'][a]['draft'],p['before'][b]['draft']])
            updates.append(('INSERT INTO fieldtofit_steward_decisions VALUES(?,?,?) ON CONFLICT(source_id,target_id) DO UPDATE SET data=excluded.data',(a,b,ws.dump({'fingerprint':fingerprint,'reason':reason,'at':stamp}))))
        updates.append(('INSERT INTO fieldtofit_steward_actions VALUES(?,?,?,?,?,?,?,?,?,NULL)',(aid,action,source,target,ws.dump(data),ws.dump(p['before']),ws.dump(p['after']),reason,stamp)))
        for ident,value in p['after'].items():
            current=p['before'][ident];version=str(current['draft_version']+1)
            if action=='group':operation_event(db,origins[ident],kind(ident)+':'+ident,'edited',version)
            elif current['published']!=value:
                withdrawn=value.get('state')!='published'
                if value.get('state')!='draft':
                    published(db,kind(ident),ident,value,withdrawn,topics=[t for t in topics[ident] if withdrawn or t['decision']=='continue' or (action=='undo' and t['decision']=='withdrawn')])
                elif action=='undo':
                    previous={t['id']:t['decision'] for t in p['extra'].get('topic_states',{}).get(ident,[])}
                    for t in topics[ident]:
                        if t['decision']=='withdrawn' and t['id'] in previous:
                            updates.append(('UPDATE fieldtofit_editorial_topics SET decision=?,version=version+1,updated_at=? WHERE id=?',(previous[t['id']],stamp,t['id'])))
                            from backend.knowledge.editorial_batches import _audit
                            _audit(db,t['id'],'merge_reversed',{'kind':kind(ident),'id':ident,'decision':previous[t['id']]})
                operation_event(db,origins[ident],kind(ident)+':'+ident,'withdrawn' if withdrawn else 'published_update' if current['published'] else 'published_new',version)
                if not withdrawn:updates.append(("UPDATE fieldtofit_inbox SET status='completed',updated_at=? WHERE kind=? AND item_id=? AND status='selected'",(stamp,kind(ident),ident)))
        execute_statements(db,updates)
        if action not in ('separate','group'):
            event(db,source,{'merge':'merged','undo':'merge_reversed','relation':'relationship_updated','relation_remove':'relationship_removed'}[action],{'target_id':target})
            if target in p['before']:event(db,target,'updated',{'related_id':source})
    return {'ok':True,'id':aid,'source':source,'target':target,'action':action}


def material_records(db):
    from backend.knowledge.content_materials import normalize
    result=[]
    for obj in raw_items(db).values():
        if obj.get('state')!='published':continue
        for m in normalize(obj):
            if m['coverage']=='withdrawn':continue
            result.append((obj['id'],m))
    return result


def observe(ident,mid,expected_url,result,at=None):
    """Persist a fetch observation; repeated attempts never inflate natural-day streaks."""
    at=at or ws.stamp();day=datetime.fromisoformat(at).astimezone(ZoneInfo('Asia/Shanghai')).date()
    with editorial_transaction() as db:
        pairs=material_records(db);material=next((m for i,m in pairs if i==ident and m['id']==mid and m['url']==expected_url),None)
        if material is None:return {'status':'discarded','reason':'Published material changed during check'}
        oldrow=db.execute('SELECT data FROM fieldtofit_steward_checks WHERE object_id=? AND material_id=?',(ident,mid)).fetchone()
        old=json.loads(oldrow[0]) if oldrow else {};old=old if old.get('url')==expected_url else {}
        if old.get('last_checked_at') and datetime.fromisoformat(old['last_checked_at'])>datetime.fromisoformat(at):return {'status':'discarded','reason':'A newer observation exists'}
        d=copy.deepcopy(old);ok=result['ok'];lastday=date.fromisoformat(old['checked_day']) if old.get('checked_day') else None
        failures=set(old.get('failed_days',[]));successes=set(old.get('success_days',[]))
        if ok:successes.add(day.isoformat());failures.discard(day.isoformat())
        elif day.isoformat() not in successes:failures.add(day.isoformat())
        streak=0;cur=day
        while cur.isoformat() in failures:streak+=1;cur-=timedelta(days=1)
        changed=bool(old.get('observed_hash') and ok and (old['observed_hash']!=result.get('hash') or old.get('final_url')!=result.get('final_url')))
        # Changed evidence remains pending even if subsequent reads return the same bytes.
        pending_change=changed or bool(old.get('changed') and old.get('needs_review'))
        ack=old.get('acknowledged_failure_days',0)
        needs=pending_change or (streak>=3 and (not ack or streak>=7>ack))
        if ok:d['acknowledged_failure_days']=0
        d.update(url=expected_url,availability='reachable' if ok else 'check_failed',last_checked_at=at,checked_day=day.isoformat(),
          last_success_at=at if ok else old.get('last_success_at'),failed_days=sorted(failures)[-30:],success_days=sorted(successes)[-30:],
          failure_days=streak,error='' if ok else result['error'],changed=pending_change,needs_review=needs,review_priority=0 if pending_change or streak>=7 else 1)
        if ok:d.update(observed_hash=result.get('hash'),final_url=result.get('final_url'))
        if changed or (streak>=7 and old.get('failure_days',0)<7):d.pop('review_after',None)
        state_changed=any(d.get(k)!=old.get(k) for k in ('availability','needs_review','review_priority','changed'))
        db.execute('INSERT INTO fieldtofit_steward_checks VALUES(?,?,?,?) ON CONFLICT(object_id,material_id) DO UPDATE SET url=excluded.url,data=excluded.data',(ident,mid,expected_url,ws.dump(d)))
        if state_changed or changed:
            action='material_changed' if changed else 'material_recovered' if ok and old.get('availability')=='check_failed' else 'material_check_failed' if not ok else 'material_checked'
            event(db,ident,action,{'material_id':mid,'availability':d['availability'],'failure_days':streak,'needs_review':needs,'checked_at':at})
    return d


def check_materials(budget_seconds=30,ident=None):
    from backend.knowledge.sources import fetch, COLLECTION_DEADLINE
    with get_db() as db:
        records=material_records(db);existing={(r['object_id'],r['material_id']):json.loads(r['data']) for r in rows(db,'fieldtofit_steward_checks')}
    nowday=ws.today();results=[];start=time.monotonic();deadline=COLLECTION_DEADLINE.set(start+budget_seconds)
    records.sort(key=lambda pair:existing.get((pair[0],pair[1]['id']),{}).get('last_checked_at',''))
    try:
        for oid,m in records:
            if ident and oid!=ident:continue
            if not ident and existing.get((oid,m['id']),{}).get('checked_day')==nowday:continue
            if time.monotonic()-start>=budget_seconds:results.append({'status':'deferred','object_id':oid});break
            try:
                raw,final,ctype=fetch(m['url'],max_bytes=2_000_000)
                if not raw.strip():raise ValueError('empty response')
                result={'ok':True,'hash':hashlib.sha256(raw).hexdigest(),'final_url':final}
            except Exception as exc:
                status=getattr(getattr(exc,'response',None),'status_code',None)
                result={'ok':False,'error':'HTTP '+str(status) if status else type(exc).__name__}
            observation=observe(oid,m['id'],m['url'],result)
            results.append({'object_id':oid,'material_id':m['id'],'status':observation.get('availability',observation.get('status','discarded'))})
    finally:COLLECTION_DEADLINE.reset(deadline)
    return {'interval_days':1,'results':results,'deferred':any(r['status']=='deferred' for r in results),'scope':'Observations only; does not publish, remove or rewrite material text'}


def decide_material(data):
    ident=text(data.get('id'),'id',100);mid=text(data.get('material_id'),'material_id',100)
    decision=data.get('decision');reason=text(data.get('reason'),'reason',2000)
    if decision not in ('retain','reviewed','defer'):ws.fail('撤下或补材料请使用内容库预览与发布；此处选择保留、已复核或延期')
    with editorial_transaction() as db:
        row=db.execute('SELECT data FROM fieldtofit_steward_checks WHERE object_id=? AND material_id=?',(ident,mid)).fetchone()
        if not row:ws.fail('检查记录不存在','not_found',404)
        current=json.loads(row[0])
        if digest(current)!=data.get('check_revision'):ws.fail('材料状态已变化，请刷新','revision_conflict',409)
        if decision=='defer':
            after=text(data.get('review_after'),'review_after',10);date.fromisoformat(after)
            if after<=ws.today():ws.fail('复查日期必须晚于今天')
            current['review_after']=after
        else:
            current.update(acknowledged_failure_days=current.get('failure_days',0),needs_review=False,changed=False,review_after=None,public_note=reason,last_decision=decision,last_decision_at=ws.stamp())
        db.execute('UPDATE fieldtofit_steward_checks SET data=? WHERE object_id=? AND material_id=?',(ws.dump(current),ident,mid))
        if decision!='defer':event(db,ident,'material_reviewed',{'material_id':mid,'decision':decision,'note':reason})
        db.execute('INSERT INTO fieldtofit_steward_actions VALUES(?,?,?,?,?,?,?,?,?,NULL)',(uuid.uuid4().hex,'material_'+decision,ident,'',ws.dump(data),row[0],ws.dump(current),reason,ws.stamp()))
    return {'ok':True}


def changes(after=0,object_ids=None,limit=20,cursor=None):
    from backend.knowledge import platform_updates as u
    ids=u._ids(object_ids or []);limit=integer(limit,'limit',1,100);after=integer(after,'after')
    query={'object_ids':ids,'limit':limit}
    if cursor and after:ws.fail('Use cursor without after','invalid_cursor')
    with get_db() as db:
        pos=0
        if cursor:
            snap,pos=u._resume(db,cursor,'workspace_changes',query)
            if pos==len(snap['data']['items']):after=snap['data']['until'];cursor=None
        if not cursor:
            upper=db.execute('SELECT COALESCE(MAX(seq),0) FROM fieldtofit_steward_events').fetchone()[0]
            if after>upper:ws.fail('Checkpoint exceeds this database','invalid_checkpoint')
            records=db.execute('SELECT * FROM fieldtofit_steward_events WHERE seq>? AND seq<=? ORDER BY seq',(after,upper)).fetchall()
            events=[{'id':'workspace:'+str(r['seq']),'object_id':r['object_id'],'kind':r['kind'],'observed_at':r['created_at'],**json.loads(r['data'])} for r in records if not ids or r['object_id'] in ids]
            snap=u._snapshot(db,'workspace_changes',query,{'items':events,'after':after,'until':upper})
        result=u._page(snap,pos,limit);events=[]
        for e in snap['data']['items'][pos:pos+limit]:
            live=public_status(e['object_id'],db)
            # Withdrawal redacts historical prose even when a snapshot predates it.
            if live['availability']=='unavailable':e={k:v for k,v in e.items() if k in ('id','object_id','kind','observed_at','material_id','target_id')}
            events.append({**e,'current_availability':live['availability'],'canonical_id':live['canonical_id']})
        result.update(items=events,after=snap['data']['after'],until=snap['data']['until'],resume_cursor=f"{snap['id']}:{min(pos+limit,result['total'])}",scope='workspace',
            retention='Events recorded after this feature is enabled; no invented historical observations. Cursors last 7 days. Poll to receive changes; no push notifications.')
        return result
