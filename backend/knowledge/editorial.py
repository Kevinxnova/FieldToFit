"""Editorial review, reversible grouping, source configuration and feedback triage."""
import re
from difflib import SequenceMatcher

from backend.db import get_db, execute_statements
from backend.knowledge import store


def sources_save(data,source_id=None):
    if data.get('interval_days',1)!=1:
        raise ValueError('Source checks remain every 1 day')
    allowed={'name','category','url','adapter','config','enabled','interval_days'}
    if set(data)-allowed:
        raise ValueError('Unsupported source field')
    from backend.knowledge.sources import list_sources
    old=next((s for s in list_sources() if s['id']==source_id),{})
    merged={**old,**data}
    for key in ('name','category','url','adapter'):
        if not isinstance(merged.get(key),str) or not 1<=len(merged[key])<=500:
            raise ValueError('A source needs name, category, URL and adapter')
    url=store.canonical_url(merged['url'])
    if merged['adapter'] not in {'rss','arxiv','huggingface','openreview','github_releases','github_skills','github_projects','platform_repository','legacy','pages'}:
        raise ValueError('Unsupported source adapter')
    config=merged.get('config',{})
    if not isinstance(config,dict) or len(store.encode(config))>50000:
        raise ValueError('Invalid source configuration')
    if not isinstance(merged.get('enabled',True),bool): raise ValueError('enabled must be boolean')
    if source_id and not old: raise ValueError('Source not found')
    sid=source_id or 'source-'+store.stable_id(url,merged['adapter'])
    with get_db() as db:
        db.execute('INSERT INTO knowledge_sources(id,name,category,url,adapter,config,enabled) VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,category=excluded.category,url=excluded.url,adapter=excluded.adapter,config=excluded.config,enabled=excluded.enabled',
                   (sid,merged['name'],merged['category'],url,merged['adapter'],store.encode(config),int(merged.get('enabled',True))))
    return {'id':sid}


def suggestions(limit=40):
    with get_db() as db:
        records=[store.row_record(r) for r in db.execute("SELECT * FROM knowledge_records WHERE status='published' AND kind='event' ORDER BY published_at DESC LIMIT 500").fetchall()]
    pairs=[]
    for i,left in enumerate(records):
        if left['metadata'].get('merged_into'): continue
        for right in records[i+1:]:
            if right['metadata'].get('merged_into') or left['version']!=right['version']: continue
            if not left['published_at'] or not right['published_at'] or left['published_at'][:10]!=right['published_at'][:10]: continue
            similarity=SequenceMatcher(None,left['title'].lower(),right['title'].lower()).ratio()
            if similarity>=0.68:
                pairs.append({'left':left,'right':right,'similarity':round(similarity,3),'status':'review_required','reason':'Similar titles on the same publication day and version; identity is not confirmed'})
    return {'items':sorted(pairs,key=lambda p:-p['similarity'])[:limit]}


def merge(target_id,record_ids,reason):
    if not isinstance(record_ids,list) or not 1<=len(record_ids)<=20 or not reason.strip():
        raise ValueError('Choose 1–20 records and record an evidence-based reason')
    action_id=store.stable_id(target_id,record_ids,store.now())
    with get_db(atomic=True) as db:
        ids=list(dict.fromkeys([target_id]+record_ids))
        rows=db.execute("SELECT * FROM knowledge_records WHERE id IN ("+','.join('?' for _ in ids)+") AND status='published'",ids).fetchall()
        by_id={row['id']:store.row_record(row) for row in rows}
        target=by_id.get(target_id)
        records=[by_id.get(i) for i in ids if i!=target_id]
        if not target or not records or any(r is None for r in records): raise ValueError('Record not found')
        if any(r['kind']!=target['kind'] or r['version']!=target['version'] for r in records):
            raise ValueError('Group only the same object kind and version; releases remain distinct')
        if target['metadata'].get('merged_into') or any(r['metadata'].get('merged_into') for r in records):
            raise ValueError('Undo an existing group before regrouping')
        payload={'target_id':target_id,'records':[{k:r[k] for k in ('id','metadata')} for r in records]}
        statements=[('INSERT INTO knowledge_editorial_actions(id,action,payload,reason,created_at) VALUES(?,?,?,?,?)',(action_id,'merge',store.encode(payload),reason,store.now()))]
        for r in records:
            r['metadata']['merged_into']=target_id; r['metadata']['editorial_override']=True
            statements.append(('UPDATE knowledge_records SET metadata=?,updated_at=? WHERE id=?',(store.encode(r['metadata']),store.now(),r['id'])))
            statements.append(('INSERT INTO knowledge_changes(record_id,action,snapshot,reason,changed_at) VALUES(?,?,?,?,?)',(r['id'],'grouped',store.encode(r),reason,store.now())))
        execute_statements(db,statements)
        from backend.knowledge.platform import invalidate
        for record in records:
            invalidate(db, record['id'], 'Object grouped into another record')
    return {'action_id':action_id,'target_id':target_id,'grouped':len(records)}


def undo(action_id,reason):
    with get_db(atomic=True) as db:
        row=db.execute("SELECT * FROM knowledge_editorial_actions WHERE id=? AND status='applied'",(action_id,)).fetchone()
        if not row: raise ValueError('Applied editorial action not found')
        payload=store.decode(row['payload'],{})
        ids=[original['id'] for original in payload['records']]
        rows=db.execute('SELECT * FROM knowledge_records WHERE id IN ('+','.join('?' for _ in ids)+')',ids).fetchall()
        by_id={row['id']:store.row_record(row) for row in rows}; statements=[]
        for rid in ids:
            record=by_id.get(rid)
            if not record or record['metadata'].get('merged_into')!=payload['target_id']: raise ValueError('Grouping changed; review before undo')
            record['metadata'].pop('merged_into',None)
            statements.append(('UPDATE knowledge_records SET metadata=?,updated_at=? WHERE id=?',(store.encode(record['metadata']),store.now(),record['id'])))
            statements.append(('INSERT INTO knowledge_changes(record_id,action,snapshot,reason,changed_at) VALUES(?,?,?,?,?)',(record['id'],'ungrouped',store.encode(record),reason,store.now())))
        statements.append(("UPDATE knowledge_editorial_actions SET status='undone' WHERE id=?",(action_id,)))
        execute_statements(db,statements)
    return {'ok':True}


def resolve(conflict_id,choice,reason):
    with get_db(atomic=True) as db:
        row=db.execute("SELECT * FROM knowledge_conflicts WHERE id=? AND status='open'",(conflict_id,)).fetchone()
        if not row: raise ValueError('Open conflict not found')
        options=store.decode(row['alternatives'],[])
        if not isinstance(choice,int) or not 0<=choice<len(options) or not reason.strip(): raise ValueError('Choose an alternative and document the reason')
        record=store.row_record(db.execute('SELECT * FROM knowledge_records WHERE id=?',(row['record_id'],)).fetchone())
        record['facts'][row['field']]=options[choice]
        record['metadata']['editorial_override']=True
        store.save_record(record,'Resolved evidence conflict: '+reason,record['id'],connection=db)
        db.execute("UPDATE knowledge_conflicts SET status='resolved',resolution=?,resolved_at=? WHERE id=?",(reason,store.now(),conflict_id))
    return {'ok':True}


def review_queue(status='',query='',need='',limit=30,offset=0):
    limit,offset=int(limit),int(offset)
    if not 1<=limit<=100 or not 0<=offset<=100000 or len(query)>500:
        raise ValueError('Invalid review page')
    filters={
        'unorganized': "json_extract(r.metadata,'$.organized_at') IS NULL",
        'missing_evidence': "NOT EXISTS (SELECT 1 FROM knowledge_evidence e WHERE e.record_id=r.id AND length(e.body)>0)",
        'conflict': "EXISTS (SELECT 1 FROM knowledge_conflicts c WHERE c.record_id=r.id AND c.status='open')",
        'failed': "EXISTS (SELECT 1 FROM knowledge_jobs j WHERE j.record_id=r.id AND j.status IN ('error','unavailable'))",
    }
    if need and need not in filters: raise ValueError('Invalid review filter')
    where=['(r.title LIKE ? OR r.title_zh LIKE ?)']; params=['%'+query+'%']*2
    if status:
        if status not in {'published','pending','withdrawn','basic','full'}: raise ValueError('Invalid review status')
        where.append('(r.status=? OR r.completeness=?)'); params += [status,status]
    if need: where.append(filters[need])
    clause=' AND '.join(where)
    with get_db() as db:
        total=db.execute('SELECT COUNT(*) AS n FROM knowledge_records r WHERE '+clause,params).fetchone()['n']
        rows=db.execute('SELECT r.* FROM knowledge_records r WHERE '+clause+' ORDER BY r.updated_at DESC,r.id LIMIT ? OFFSET ?',params+[limit,offset]).fetchall()
        conflicts=[dict(r) for r in db.execute("SELECT * FROM knowledge_conflicts WHERE status='open'").fetchall()]
        actions=[dict(r) for r in db.execute('SELECT * FROM knowledge_editorial_actions ORDER BY created_at DESC LIMIT 100').fetchall()]
        feedback=[dict(r) for r in db.execute("SELECT f.*,COALESCE(a.status,'pending') AS handling_status,a.resolution,a.record_id AS resolved_record FROM knowledge_feedback f LEFT JOIN knowledge_feedback_actions a ON a.feedback_id=f.id ORDER BY f.created_at DESC LIMIT 100").fetchall()]
    for c in conflicts: c['alternatives']=store.decode(c['alternatives'],[])
    records=[store.row_record(r) for r in rows]
    return {'records':records,'conflicts':conflicts,'actions':actions,'feedback':feedback,'total':total,'offset':offset,'next_offset':offset+limit if offset+limit<total else None,'truncated':offset+limit<total}
