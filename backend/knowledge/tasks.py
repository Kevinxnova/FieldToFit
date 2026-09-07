"""Task interpretation, evidence-based constraints and portable task artifacts."""
import re
from collections import Counter

from backend.knowledge import store, models

ALIASES = {'local':'local','offline':'local','本地':'local','本地部署':'local','cloud':'cloud','云端':'cloud',
           'chinese':'chinese','zh':'chinese','中文':'chinese','english':'english','en':'english','英文':'english',
           'apache-2.0':'apache-2.0','apache 2.0':'apache-2.0','mit license':'mit','mit':'mit',
           'macos':'macos','mac':'macos','osx':'macos','windows':'windows','win':'windows','linux':'linux'}


def norm(value):
    text=str(value).strip().casefold()
    return ALIASES.get(text,text)


def match_conditions(record,constraints):
    if not isinstance(constraints,dict) or set(constraints)-store.FACT_KEYS:
        raise ValueError('Unsupported constraint')
    matches=[]
    for key,desired in constraints.items():
        fact=record['facts'].get(key,{})
        state='unknown'; reason='Missing or incompatible evidence'
        version_ok=not record['version'] or fact.get('version')==record['version']
        if isinstance(desired,dict):
            unit={'hardware_vram_gb':'GB','cost_monthly_usd':'USD/month'}.get(key)
            if not unit or set(desired)-{'max','min','unit'} or not {'max','min'}.intersection(desired) or desired.get('unit',unit)!=unit:
                raise ValueError('Invalid numeric condition or unit')
            if any(isinstance(v,bool) or not isinstance(v,(int,float)) or v<0 for k,v in desired.items() if k!='unit'):
                raise ValueError('Numeric constraints require non-negative values')
            if 'min' in desired and 'max' in desired and desired['min']>desired['max']:
                raise ValueError('Minimum exceeds maximum')
        if fact.get('conflict'):
            version_ok=False
        if version_ok and fact.get('status') in {'official_claim','documented'} and fact.get('value') is not None:
            value=fact['value']
            if isinstance(desired,dict):
                if set(desired)-{'max','min','unit'} or not {'max','min'}.intersection(desired):
                    raise ValueError('Numeric conditions use min, max and unit')
                unit={'hardware_vram_gb':'GB','cost_monthly_usd':'USD/month'}.get(key)
                if not unit or desired.get('unit',unit)!=unit:
                    raise ValueError('Numeric units must be GB or USD/month for their respective fields')
                limits=[desired[k] for k in ('min','max') if k in desired]
                if any(isinstance(v,bool) or not isinstance(v,(int,float)) or v<0 for v in limits):
                    raise ValueError('Numeric conditions require non-negative numbers')
                if 'min' in desired and 'max' in desired and desired['min']>desired['max']:
                    raise ValueError('Minimum exceeds maximum')
                if isinstance(value,(int,float)) and not isinstance(value,bool) and fact.get('unit')==unit and fact.get('conditions'):
                    passed=('max' not in desired or value<=desired['max']) and ('min' not in desired or value>=desired['min'])
                    state='satisfied' if passed else 'unmet'; reason='Numeric comparison in cited operating conditions'
            else:
                vals=value if isinstance(value,list) else [value]
                wanted=desired if isinstance(desired,list) else [desired]
                normalized={norm(v) for v in vals}
                if all(norm(w) in normalized for w in wanted):
                    state='satisfied'; reason='Explicit matching value in cited version'
                elif fact.get('exhaustive') is True:
                    state='unmet'; reason='Source explicitly enumerates supported values'
        matches.append({'condition':key,'requested':desired,'state':state,'reason':reason,'evidence':fact})
    return matches


def interpret(goal,constraints=None,enhanced=False):
    constraints=constraints or {}
    if not isinstance(goal,str) or not 1<=len(goal.strip())<=2000:
        raise ValueError('Describe a task in 1–2000 characters')
    if not isinstance(constraints,dict) or len(constraints)>12 or set(constraints)-store.FACT_KEYS:
        raise ValueError('Unsupported constraint')
    detected={}
    if re.search(r'本地|离线|\blocal\b|\boffline\b',goal,re.I): detected['deployment']='local'
    if re.search(r'中文|\bchinese\b',goal,re.I): detected['language']='chinese'
    for platform in ('Windows','Linux','macOS'):
        if platform.lower() in goal.lower(): detected['platform']=platform.lower()
    match=re.search(r'(\d+(?:\.\d+)?)\s*(?:GB|G)\s*(?:显存|VRAM)|(?:显存|VRAM)\D{0,8}(\d+(?:\.\d+)?)\s*(?:GB|G)',goal,re.I)
    if match: detected['hardware_vram_gb']={'max':float(match.group(1) or match.group(2)),'unit':'GB'}
    detected.update(constraints)
    if not isinstance(enhanced,bool): raise ValueError('enhanced must be boolean')
    # Validate conditions even when no matching resource has been indexed.
    match_conditions({'facts':{},'version':''},detected)
    # Deployment and language are constraints, not alternative subjects for candidate recall.
    subject=re.sub(r'本地部署|本地|离线|中文|英文|云端|\b(?:local|offline|chinese|english|windows|linux|macos)\b',' ',goal,flags=re.I).strip()
    queries=[subject or goal]; mode='keywords_and_capability_tags'; warning=''
    if enhanced:
        try:
            result,_=models.generate_json('Rewrite the task into 2–4 concise search queries using Chinese and English technical equivalents. Return {queries:[]}. Do not suggest project names that are absent from the task. Preserve the task meaning. This only expands retrieval; never claim conditions are satisfied.',{'goal':goal},max_tokens=1200)
            if isinstance(result.get('queries'),list):
                queries += [q[:500] for q in result['queries'] if isinstance(q,str) and q.strip()][:4]
                mode='semantic_query_expansion'
        except (models.ModelUnavailable,ValueError) as exc:
            warning=str(exc)
    return {'goal':goal,'constraints':detected,'queries':list(dict.fromkeys(queries)), 'retrieval_mode':mode,'warning':warning,
            'interpretation_note':'Detected conditions can be edited; no condition is accepted without candidate evidence'}


def research_compare(items):
    fields=['dataset','dataset_version','split','metric','protocol','model_version','hardware']
    settings=[]
    for item in items:
        values={key:item['facts'].get(key,{}).get('value') if not item['facts'].get(key,{}).get('conflict') and (not item['version'] or item['facts'].get(key,{}).get('version')==item['version']) else None for key in fields}
        settings.append({'id':item['id'],'title':item['title'],'settings':values,
                         'experiments':item['facts'].get('experiments'), 'evidence_status':'Author/source reports; Metis checks listed separately'})
    missing=[k for k in fields if any(s['settings'][k] is None for s in settings)]
    differing=[k for k in fields if k not in missing and len({store.encode(s['settings'][k]) for s in settings})>1]
    return {'items':settings,'missing_settings':missing,'different_settings':differing,
            'comparable':not missing and not differing,
            'conclusion':'settings_aligned_review_metrics' if not missing and not differing else 'not_directly_comparable',
            'note':'Matching metadata permits closer inspection; it does not establish a universal winner'}


def pack(goal,constraints=None,persona='engineer',limit=12,offset=0,background='',enhanced=False,interpreted=None):
    if persona not in {'engineer','researcher','graduate','student'}:
        raise ValueError('Invalid persona')
    limit,offset=int(limit),int(offset)
    if not 1<=limit<=50 or not 0<=offset<=100000 or not isinstance(background,str) or len(background)>3000:
        raise ValueError('Invalid task page or background')
    interpretation=interpreted or interpret(goal,constraints,enhanced)
    # Query every candidate page; report the scope and do not silently return a top-N list.
    candidates={}
    for query in interpretation['queries']:
        pos=0
        while True:
            result=store.search_records(q=query,kind='resource' if persona=='engineer' else '',limit=100,offset=pos)
            for item in result['items']:
                if item['kind']=='event': continue
                old=candidates.get(item['id'])
                if not old or item.get('match_score',0)>old.get('match_score',0): candidates[item['id']]=item
            if result['next_offset'] is None or result['next_offset']>100000: break
            pos=result['next_offset']
    for item in candidates.values():
        item['constraint_matches']=match_conditions(item,interpretation['constraints'])
        counts=Counter(m['state'] for m in item['constraint_matches'])
        item['unknowns']=[m['condition'] for m in item['constraint_matches'] if m['state']=='unknown']
        item['fit']={'satisfied':counts['satisfied'],'unmet':counts['unmet'],'unknown':counts['unknown']}
        item['ranking_reason']={'keyword_matches':item.get('match_score',0),'conditions':item['fit'],'popularity_used_for_fit':False}
    ranked=sorted(candidates.values(),key=lambda r:(r['fit']['unmet']>0,-r['fit']['satisfied'],-r.get('match_score',0),r['id']))
    selected=ranked[offset:offset+limit]; dossiers=[store.get_record(r['id']) for r in selected]
    material=[]
    for dossier in dossiers:
        citations=[{'id':e['id'],'url':e['url'],'title':e['title'],'locator':e['locator'],'version':e['version'],'coverage':e['coverage']} for e in dossier['evidence']]
        keys={'engineer':['usage','extension','dependencies','license'],'researcher':['method','experiments','limitations'],
              'graduate':['usage','dependencies','hardware','dataset','protocol'],'student':['prerequisites','usage','capabilities']}[persona]
        steps=[]
        for key in keys:
            fact=dossier['facts'].get(key)
            if fact:
                steps.append({'type':key,'instruction':fact['value'],'source_url':fact.get('source_url'),'version':fact.get('version'),
                              'status':'conflicting' if fact.get('conflict') else fact['status'],'version_matches':not fact.get('conflict') and (not dossier['version'] or fact.get('version')==dossier['version'])})
        material.append({'record_id':dossier['id'],'title':dossier['title'],'version':dossier['version'],
                         'steps':steps,'materials':citations,'verifications':dossier['verifications'],
                         'missing_materials':[key for key in keys if key not in dossier['facts'] or dossier['facts'][key].get('conflict') or dossier['facts'][key].get('status')=='unknown'],
                         'relationships':dossier['relations']})
    if not ranked: conclusion='not_found_in_scope'
    elif all(r['fit']['unmet'] for r in ranked): conclusion='known_candidates_unmet'
    elif any(not r['fit']['unmet'] and not r['fit']['unknown'] for r in ranked) and interpretation['constraints']: conclusion='candidates_match_documented_conditions'
    else: conclusion='requires_evidence_review'
    deliverables={'engineer':['候选比较与采用依据','版本对应的运行或扩展步骤','最小功能产物与成功判据'],
                  'researcher':['带来源的研究清单','方法与实验设置比较','尚未解决的问题和证据缺口'],
                  'graduate':['论文、实现、数据对应关系','缩小实验的环境与步骤','结果和原论文实验的差距'],
                  'student':['概念解释与前置知识','有依据的阅读顺序','最小实践及结果检查']}
    return {'goal':goal,'persona':persona,'background':background,'constraints':interpretation['constraints'], 'interpretation':interpretation,
            'candidates':selected,'total_candidates':len(ranked),'offset':offset,'next_offset':offset+limit if offset+limit<len(ranked) else None,
            'scope':'Metis indexed published records; not an exhaustive web search','conclusion':conclusion,'material_packets':material,
            'deliverables':deliverables[persona],
            'paths':[{'path':'use','record_ids':[d['record_id'] for d in material if any(s['type']=='usage' for s in d['steps'])],'check':'Use version-matched usage materials and confirm the expected outcome'},
                     {'path':'extend','record_ids':[d['record_id'] for d in material if any(s['type']=='extension' for s in d['steps'])],'check':'Inspect cited extension points and validate the smallest change'},
                     {'path':'build','record_ids':[],'check':'Specify unmet requirements and reusable components before implementing; absence from search does not establish absence everywhere'}],
            'research_comparison':research_compare(dossiers) if persona in {'researcher','graduate'} and len(dossiers)>1 else None,
            'next_steps':['Read source-linked materials for the selected task','Resolve missing hard conditions','Produce the persona-specific artifact','Record expected outcome, environment and observed result'],
            'generated_at':store.now(),'ai_generated':False}


def task_markdown(data):
    lines=['# '+data['goal'],'',f"Persona: {data['persona']}",f"Scope: {data['scope']}",f"Generated: {data['generated_at']}",
           f"Conclusion: {data['conclusion']}",'','## Conditions',store.encode(data['constraints']),'','## Deliverables']
    lines += ['- '+x for x in data['deliverables']]
    for packet in data['material_packets']:
        lines += ['', '## '+packet['title'], 'Version: '+(packet['version'] or 'Unknown')]
        for step in packet['steps']:
            lines += [f"- {step['type']}: {store.encode(step['instruction'])}",f"  Source: {step['source_url']} · {step['status']}"]
        for e in packet['materials']:
            lines += [f"- [{e['title']}]({e['url']}) · {e['locator']} · {e['coverage']}"]
        if packet['missing_materials']: lines += ['Missing task materials: '+', '.join(packet['missing_materials'])]
    return '\n'.join(lines)+'\n'


def reading_list(goal,ids=None,background='',enhanced=False):
    data=pack(goal,persona='researcher',background=background,enhanced=enhanced,limit=50)
    records=[store.get_record(i) for i in ids] if ids else [store.get_record(x['id']) for x in data['candidates'] if x['kind']=='paper']
    if any(r is None for r in records): raise ValueError('A reading-list record is unavailable')
    from backend.knowledge.export import bibtex
    notes=[]
    for record in records:
        research=record['metadata'].get('editorial',{}).get('research',{})
        notes.append({'id':record['id'],'title':record['title'],'title_zh':record['title_zh'],'source_url':record['canonical_url'],
                      'research':research,'facts':record['facts'],'evidence':record['evidence'],
                      'bibtex':bibtex(record),'published_at':record['published_at']})
    outline=None
    if enhanced and notes:
        raw,generation=models.generate_json('Make a source-grounded reading/meeting outline. Return {sections:[{title,points:[{text,record_id,evidence_id,quote}]}],reading_order:[record_id]}. Use only supplied records. Explain prerequisites only if documented. Never invent citations or conclusions.',{'goal':goal,'background':background,'records':notes,'evidence':[dict(id=e['id'],body=e['body'][:6000],record_id=e['record_id']) for r in records for e in store.get_record(r['id'],include_body=True)['evidence']][:30]},max_tokens=5000)
        from backend.knowledge.processing import validate_citation
        evidence={e['id']:e for r in records for e in store.get_record(r['id'],include_body=True)['evidence']}
        valid_ids={r['id'] for r in records}; sections=[]
        for section in raw.get('sections',[]):
            points=[]
            for point in section.get('points',[]):
                citation=validate_citation(point,evidence)
                if citation and point.get('record_id') in valid_ids and evidence[citation['evidence_id']]['record_id']==point['record_id']:
                    points.append({'text':str(point.get('text',''))[:3000],'record_id':point['record_id'],**citation})
            if points: sections.append({'title':str(section.get('title',''))[:200],'points':points})
        outline={'sections':sections,'reading_order':[i for i in raw.get('reading_order',[]) if i in valid_ids],**generation}
    return {'goal':goal,'background':background,'items':notes,'outline':outline,'scope':data['scope'],'generated_at':store.now(),
            'bibtex':'\n'.join(n['bibtex'] for n in notes),'comparison':research_compare(records) if len(records)>1 else None}
