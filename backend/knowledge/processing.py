"""Resumable daily enrichment and cited bilingual editorial content."""
import hashlib
import re
import time
from datetime import datetime, timezone

from backend.db import get_db
from backend.knowledge import store, models

INSTRUCTION = '''Organize AI news, research or resource material for Chinese and English readers. Use only supplied evidence.
Return {title_zh, summary_zh, summary_en, topics:[], object_type, capability_tags:[],
 human:{zh:{what,changes,why,audience,limitations,next_step},en:{what,changes,why,audience,limitations,next_step}},
 facts:[{key,value,evidence_id,quote,version,exhaustive:false}],
 research:{question,method,contribution,experiments,limitations,prerequisites,reading_steps:[{text,evidence_id,quote}]},
 citations:[{evidence_id,quote}], importance:{score:0..5,reason_zh,reason_en}}.
Human fields are plain text, summaries <=400 characters, technical names stay accurate. Explain only supported changes; interpretation must be labeled as such. Each factual statement must be supported by citations. Do not infer support/absence/license/cost/hardware from silence. A quoted experiment is an author report, not an independent test. For facts use only allowed_fact_keys; version must match supplied material. Numeric hardware_vram_gb and cost_monthly_usd require explicit comparable units and conditions. Research fields are strings. Do not invent reading prerequisites. If evidence is insufficient, state that clearly. Never say FieldToFit ran a project.'''


def evidence_fingerprint(record):
    return store.stable_id(record['version'], record['title'], record['summary'], [(e['id'], e['content_hash']) for e in record['evidence']])


def queue_records():
    with get_db() as db:
        visible = "status='published' AND json_extract(metadata,'$.merged_into') IS NULL"
        count = db.execute('SELECT COUNT(*) AS n FROM knowledge_records WHERE '+visible).fetchone()['n']
        for stage in ('material','organize'):
            db.execute('INSERT OR IGNORE INTO knowledge_jobs(record_id,stage) SELECT id,? FROM knowledge_records WHERE '+visible,(stage,))
        # A stopped process must not leave work permanently locked.
        db.execute("UPDATE knowledge_jobs SET status='pending',error='Previous worker stopped; retry available' WHERE status='running' AND datetime(started_at)<datetime('now','-1 day')")
    return count


def normalized(text):
    return re.sub(r'\s+',' ', str(text)).strip()


def validate_citation(citation, evidence):
    if not isinstance(citation,dict):
        return None
    material = evidence.get(citation.get('evidence_id'))
    quote = citation.get('quote','')
    if not material or not isinstance(quote,str) or len(normalized(quote)) < 12 or normalized(quote) not in normalized(material['body']):
        return None
    return {'evidence_id':material['id'],'quote':quote[:2000],'source_url':material['url'],'locator':material['locator'],'version':material['version']}


def organize(record_id):
    record = store.get_record(record_id, include_body=True)
    if not record:
        raise ValueError('Published record not found')
    # Bound each request and explicitly retain coverage; further sections remain readable via MCP.
    materials = []; budget = 60000
    for e in record['evidence']:
        if budget <= 0:
            break
        body = e['body'][:min(14000,budget)]; budget -= len(body)
        if body:
            materials.append({**{k:e[k] for k in ('id','url','locator','version','coverage')},'body':body,'truncated':len(body)<len(e['body'])})
    if not materials:
        raise ValueError('No readable evidence; retrieve source material first')
    payload = {'title':record['title'],'kind':record['kind'],'version':record['version'],
               'allowed_fact_keys':sorted(store.FACT_KEYS),'allowed_topics':list(store.TOPICS),'materials':materials}
    output, generation = models.generate_json(INSTRUCTION,payload)
    generation['input_truncated'] = any(m['truncated'] for m in materials) or len(materials)<len(record['evidence'])
    return apply_organization(record_id, output, generation)


def apply_organization(record_id, output, generation):
    """Validate both provider output and an explicitly imported assistant-produced batch."""
    record=store.get_record(record_id,include_body=True)
    if not record: raise ValueError('Published record not found')
    if not isinstance(output,dict) or not isinstance(generation,dict): raise ValueError('Invalid organized material')
    materials=[{'id':e['id']} for e in record['evidence']]
    evidence = {e['id']:e for e in record['evidence']}
    citations = [c for item in output.get('citations',[]) if (c:=validate_citation(item,evidence))]
    if not citations:
        raise ValueError('Generated explanation lacks a verifiable source quotation')
    # Quote matching establishes provenance, not semantic truth; summaries remain visibly AI-organized.
    for key in ('summary_zh','summary_en','title_zh'):
        if not isinstance(output.get(key),str) or not output[key].strip():
            raise ValueError('Generation is missing bilingual text: '+key)
    human = output.get('human',{})
    if not isinstance(human,dict) or any(not isinstance(human.get(lang),dict) or any(not isinstance(human[lang].get(k),str) for k in ('what','changes','why','audience','limitations','next_step')) for lang in ('zh','en')):
        raise ValueError('Generation is missing structured bilingual reading fields')
    if not record['metadata'].get('editorial_override'):
        record.update(title_zh=output['title_zh'][:1000],summary_zh=output['summary_zh'][:2000])
        record['metadata']['summary_en'] = output['summary_en'][:2000]
        topics = output.get('topics',[])
        if isinstance(topics,list) and topics and all(t in store.TOPICS for t in topics):
            record['topics'] = topics
        if not record['metadata'].get('skill') and not record['metadata'].get('resource_type_basis') and output.get('object_type') in {'project','agent','skill','harness','tool','library','model','api','application','dataset','benchmark','paper','release','news'}:
            record['object_type'] = output['object_type']
    for candidate in output.get('facts',[]):
        if not isinstance(candidate,dict) or candidate.get('key') not in store.FACT_KEYS or 'value' not in candidate:
            continue
        citation = validate_citation(candidate,evidence)
        if not citation:
            continue
        key = candidate['key']; version = citation['version']
        if record['version'] and version != record['version']:
            continue
        new = {'value':candidate['value'],'status':'documented','version':version,'checked_at':store.now(),
               **citation,'ai_extracted':True,'exhaustive':False}
        if key in {'hardware_vram_gb','cost_monthly_usd'}:
            unit={'hardware_vram_gb':'GB','cost_monthly_usd':'USD/month'}[key]
            if candidate.get('unit')!=unit or not isinstance(candidate.get('conditions'),str) or not candidate['conditions'].strip():
                continue
            new.update(unit=unit,conditions=candidate['conditions'])
        old = record['facts'].get(key)
        if old and old['value'] != new['value'] and old.get('version') == version:
            cid = store.stable_id(record_id,key,store.encode([old,new]))
            with get_db() as db:
                db.execute('INSERT OR IGNORE INTO knowledge_conflicts(id,record_id,field,alternatives,created_at) VALUES(?,?,?,?,?)',(cid,record_id,key,store.encode([old,new]),store.now()))
                from backend.knowledge.platform import invalidate
                invalidate(db, record_id, 'Source fact conflict requires review')
            continue
        if not record['metadata'].get('editorial_override'):
            record['facts'][key] = new
    importance = output.get('importance',{})
    score = importance.get('score',0)
    if not isinstance(score,(int,float)) or not 0 <= score <= 5:
        score = 0
    record['metadata']['editorial'] = {'human':human,'research':output.get('research',{}),'citations':citations,
        'importance':{'score':score,'reason_zh':str(importance.get('reason_zh',''))[:800],'reason_en':str(importance.get('reason_en',''))[:800]},
        **generation,'material_ids':[m['id'] for m in materials],'input_truncated':bool(generation.get('input_truncated',False)),
        'review_status':'ai_organized','processing_version':'2'}
    tags = output.get('capability_tags',[])
    if isinstance(tags,list) and any(isinstance(t,str) and t.strip() for t in tags):
        record['metadata']['capability_tags'] = list(dict.fromkeys(t.strip()[:80] for t in tags if isinstance(t,str) and t.strip()))[:20]
        record['metadata']['capability_tag_basis'] = 'ai_organized_discovery_labels_not_verification'
    required = {'capabilities','limitations','deployment','license','usage'} if record['kind']=='resource' else {'method','experiments','limitations'} if record['kind']=='paper' else set()
    # A full dossier needs every required item, complete material and no open contradictory fact.
    with get_db() as db:
        conflict = db.execute("SELECT id FROM knowledge_conflicts WHERE record_id=? AND status='open'",(record_id,)).fetchone()
    if required and required.issubset(record['facts']) and record['metadata'].get('material',{}).get('coverage')=='full_text' and not conflict:
        record['completeness']='full'
    record['metadata']['organized_at']=store.now()
    store.save_record(record,'Organized bilingual material with source quotations',record_id)
    return {'id':record_id,'citations':len(citations),'facts':len(record['facts']),**generation}


def run_processing(limit=20,budget_seconds=240,record_id=None,force=False):
    limit,budget_seconds=int(limit),int(budget_seconds)
    if not 1<=limit<=1000 or not 1<=budget_seconds<=86400:
        raise ValueError('Invalid processing limit or budget')
    from backend.knowledge.operations import track_run
    with track_run('processing') as result:
        result.update(_process(limit,budget_seconds,record_id,force))
    return result


def _process(limit,budget_seconds,record_id,force):
    queue_records(); start=time.monotonic(); results=[]
    with get_db() as db:
        rows=db.execute("SELECT r.id FROM knowledge_records r LEFT JOIN knowledge_jobs j ON j.record_id=r.id AND j.stage='organize' WHERE r.status='published' AND json_extract(r.metadata,'$.merged_into') IS NULL"+(' AND r.id=?' if record_id else '')+" ORDER BY CASE WHEN j.status='pending' THEN 0 WHEN j.status IN ('error','unavailable') THEN 1 ELSE 2 END,COALESCE(j.finished_at,''),COALESCE(r.published_at,r.collected_at) DESC",(record_id,) if record_id else ()).fetchall()
    for row in rows:
        if time.monotonic()-start>budget_seconds or len({r['record_id'] for r in results})>=limit:
            break
        record=store.get_record(row['id'],include_body=True)
        for stage in ('material','organize'):
            if time.monotonic()-start>budget_seconds:
                break
            with get_db() as db:
                job=dict(db.execute('SELECT * FROM knowledge_jobs WHERE record_id=? AND stage=?',(row['id'],stage)).fetchone())
            fingerprint=record['version'] if stage=='material' else evidence_fingerprint(record)
            if not force and job['status']=='success' and job['input_hash']==fingerprint:
                # Original materials receive a daily recheck; organization only changes with evidence.
                if stage=='organize' or (job['finished_at'] and (datetime.now(timezone.utc)-datetime.fromisoformat(job['finished_at'].replace('Z','+00:00'))).total_seconds()<86400):
                    continue
            if not force and job['status'] in {'error','unavailable'} and job['finished_at'] and (datetime.now(timezone.utc)-datetime.fromisoformat(job['finished_at'].replace('Z','+00:00'))).total_seconds()<86400:
                continue
            with get_db() as db:
                claimed=db.execute("UPDATE knowledge_jobs SET status='running',attempts=attempts+1,started_at=?,error='' WHERE record_id=? AND stage=? AND status!='running'",(store.now(),row['id'],stage))
            if not claimed.rowcount:
                continue
            status='success'; error=''
            try:
                if stage=='material':
                    from backend.knowledge.materials import retrieve
                    retrieve(row['id'])
                else:
                    organize(row['id'])
            except models.ModelUnavailable as exc:
                status='unavailable'; error=str(exc)
            except Exception as exc:
                status='error'; error=str(exc)[:500]
            with get_db() as db:
                db.execute('UPDATE knowledge_jobs SET status=?,input_hash=?,finished_at=?,error=? WHERE record_id=? AND stage=?',(status,fingerprint,store.now(),error,row['id'],stage))
            results.append({'record_id':row['id'],'stage':stage,'status':status,'error':error})
            record=store.get_record(row['id'],include_body=True)
    with get_db() as db:
        remaining=db.execute("SELECT COUNT(*) AS n FROM knowledge_records r WHERE r.status='published' AND json_extract(r.metadata,'$.merged_into') IS NULL AND (json_extract(r.metadata,'$.organized_at') IS NULL OR EXISTS (SELECT 1 FROM knowledge_jobs j WHERE j.record_id=r.id AND j.status!='success'))"+(' AND r.id=?' if record_id else ''),(record_id,) if record_id else ()).fetchone()['n']
    return {'items':results,'processed_records':len({r['record_id'] for r in results}),
            'remaining_records':remaining,'budget_reached':time.monotonic()-start>=budget_seconds,
            'status':'partial' if remaining or any(r['status']!='success' for r in results) else 'success','interval_days':1}


def processing_status():
    with get_db() as db:
        counts=[dict(r) for r in db.execute('SELECT stage,status,COUNT(*) AS count FROM knowledge_jobs GROUP BY stage,status').fetchall()]
        jobs=[dict(r) for r in db.execute('SELECT j.*,r.title FROM knowledge_jobs j JOIN knowledge_records r ON r.id=j.record_id ORDER BY COALESCE(j.finished_at,j.started_at,r.collected_at) DESC LIMIT 100').fetchall()]
    return {'counts':counts,'jobs':jobs,'model':models.configuration()}


def build_brief(day=None):
    day=day or datetime.now(timezone.utc).date().isoformat()
    datetime.fromisoformat(day)
    with get_db() as db:
        rows=db.execute("SELECT * FROM knowledge_records WHERE status='published' AND kind IN ('event','paper') AND date(published_at)=date(?)",(day,)).fetchall()
    records=[store.row_record(r) for r in rows]
    records=[r for r in records if r['metadata'].get('editorial') and not r['metadata'].get('merged_into')]
    records.sort(key=lambda r:r['metadata']['editorial']['importance']['score'],reverse=True)
    items=[{'id':r['id'],'version':r['version'],'title':r['title'],'title_zh':r['title_zh'],'summary_zh':r['summary_zh'],
            'summary_en':r['metadata'].get('summary_en',r['summary']),'topics':r['topics'],
            'reason':r['metadata']['editorial']['importance'],'source_url':r['canonical_url']} for r in records[:12]]
    with get_db() as db:
        db.execute('INSERT INTO knowledge_briefs VALUES(?,?,?,?) ON CONFLICT(date) DO UPDATE SET items=excluded.items,generated_at=excluded.generated_at,scope=excluded.scope',(day,store.encode(items),store.now(),'AI-organized indexed events and papers with known publication dates; not exhaustive'))
    return {'date':day,'items':items,'generated_at':store.now()}


def briefs(day=None):
    with get_db() as db:
        rows=db.execute('SELECT * FROM knowledge_briefs'+(' WHERE date=?' if day else '')+' ORDER BY date DESC LIMIT 90',(day,) if day else ()).fetchall()
        visible={r['id'] for r in db.execute("SELECT id FROM knowledge_records WHERE status='published'").fetchall()}
    result=[]
    for row in rows:
        item=dict(row); item['items']=[]
        for previous in store.decode(row['items'],[]):
            if previous['id'] not in visible: continue
            current=store.get_record(previous['id'])
            if current['metadata'].get('merged_into'): continue
            # Preserve the edition's version, but propagate corrections to that same version.
            if current['version']==previous.get('version',''):
                previous.update(title=current['title'],title_zh=current['title_zh'],summary_zh=current['summary_zh'],
                    summary_en=current['metadata'].get('summary_en',current['summary']))
            item['items'].append(previous)
        result.append(item)
    return {'items':result,'ai_generated':True}


def import_batch(batch):
    if not isinstance(batch,dict) or not isinstance(batch.get('items'),list) or not 1<=len(batch['items'])<=100:
        raise ValueError('A batch contains 1–100 organized records')
    generator=batch.get('generator','Assistant import')
    if not isinstance(generator,str) or len(generator)>120: raise ValueError('Invalid generator label')
    results=[]
    for entry in batch['items']:
        if not isinstance(entry,dict) or not isinstance(entry.get('output'),dict): raise ValueError('Invalid batch entry')
        rid=entry.get('record_id')
        record=store.get_record(rid,include_body=True)
        if not record: raise ValueError('Import record not found: '+str(rid))
        output=entry.get('output',{})
        # Portable imports can locate a citation by exact URL and quote instead of a database-specific ID.
        for citation in [*output.get('citations',[]),*output.get('facts',[])]:
            if not isinstance(citation,dict): raise ValueError('Invalid citation entry')
            if not citation.get('evidence_id') and citation.get('source_url'):
                match=next((e for e in record['evidence'] if e['url']==citation['source_url'] and normalized(citation.get('quote','')) in normalized(e['body'])),None)
                if match: citation['evidence_id']=match['id']
        results.append(apply_organization(rid,output,{'model':generator,'generated_at':store.now(),'ai_generated':True,'input_truncated':True,'mode':'assistant_batch_import'}))
        fingerprint=evidence_fingerprint(store.get_record(rid,include_body=True))
        with get_db() as db:
            db.execute("INSERT INTO knowledge_jobs(record_id,stage,status,input_hash,finished_at) VALUES(?,'organize','success',?,?) ON CONFLICT(record_id,stage) DO UPDATE SET status='success',input_hash=excluded.input_hash,finished_at=excluded.finished_at,error=''",(rid,fingerprint,store.now()))
    return {'items':results}


if __name__=='__main__':
    import argparse,json
    from pathlib import Path
    from backend.db import init_db
    parser=argparse.ArgumentParser();parser.add_argument('--import-batch',required=True);args=parser.parse_args()
    init_db();print(json.dumps(import_batch(json.loads(Path(args.import_batch).read_text())),ensure_ascii=False))
