"""Reviewed English projections. Original evidence and default Chinese contracts stay intact."""
import copy
import hashlib
import json
import re
from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache
from pathlib import Path
from backend.knowledge.platform import PlatformError

ROOT=Path(__file__).parent/'content'/'locale'
HAN=re.compile(r'[\u3400-\u9fff]')
ORIGINAL={'body','quote','quoted_text','excerpt','notice','text_en','translation_zh','context_en','context_zh','markdown','goal','background','task_spec','inputs','constraints'}
UNOWNED={'translations','publication','state','_position','private_note','submission_review'}
READ_LANGUAGE=ContextVar('fieldtofit_read_language',default='zh')

def is_english():
    from flask import has_request_context,request
    return READ_LANGUAGE.get()=='en' or has_request_context() and (request.args.get('lang')=='en' or request.path=='/en' or request.path.startswith('/en/'))

@contextmanager
def read_language(value):
    token=READ_LANGUAGE.set(language(value))
    try:yield
    finally:READ_LANGUAGE.reset(token)

def searchable(value):
    return project(value,public_fields()) if is_english() else value
OWNED={
    'news':('id','name','organization','title','summary','source_published_at','event_date','checked_at','interpretation','sources','related','note','editor','highlight','reading_materials','media','category','codex_28_days','technical_map','aliases'),
    'watch':('id','name','type','introduction','checked_at','evidence_status','sources','interpretation','blocks','attention','origin','submission','reading_materials','aliases'),
    'charts':('landscape','flagships'),
    'library':('id','name','original_name','aliases','types','roles','introduction','official_url','upstream_version','source_published_at','source_id','collected_at','checked_at','source_revision','facts','attention','materials','coverage','unknown_fields','limitations'),
}

def authored(kind,item):
    def clean(value):
        if isinstance(value,dict):return {k:clean(v) for k,v in value.items() if k not in UNOWNED}
        if isinstance(value,list):return [clean(v) for v in value]
        return value
    value={k:item[k] for k in OWNED[kind] if k in item}
    if kind=='news':
        from backend.knowledge.codex_progress import metadata
        from backend.knowledge.technical_maps import metadata as map_metadata
        if 'codex_28_days' in value:value['codex_28_days']=metadata(item)
        if 'technical_map' in value:value['technical_map']=map_metadata(item)
    return clean(value)

def language(value=None):
    if value is None or value=='': return 'zh'
    if value not in ('zh','en'): raise PlatformError('Use lang=zh or lang=en','invalid_language',400)
    return value

def reviewed_note(source,data,field='public_note_en'):
    """Public operational notes require the same explicit bilingual check as prose."""
    if not HAN.search(source):return source
    translated=data.get(field)
    if data.get('english_confirmed') is not True or not isinstance(translated,str) or not translated.strip() or HAN.search(translated):
        raise PlatformError('Complete and confirm the English public note','english_review_required',409)
    protected=lambda v:re.findall(r'https?://[^\s)\]<>]+|[A-Za-z][A-Za-z0-9._-]*\d[A-Za-z0-9._-]*|(?<![\w])\d+(?:[.,]\d+)*(?:%|[kKmMbB])?',v)
    if sorted(protected(source))!=sorted(protected(translated)):
        raise PlatformError('Preserve source numbers, versions and URLs in the English public note','english_fact_mismatch',409)
    return translated.strip()

def source_hash(kind, item):
    # Include facts, dates, configuration and URLs, excluding private/server-owned fields.
    value=copy.deepcopy(authored(kind,item))
    if kind=='charts':value['landscape'].pop('revision',None)
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

@lru_cache(maxsize=1)
def catalog():
    path=ROOT/'en.json'
    return json.loads(path.read_text()) if path.exists() else {}

@lru_cache(maxsize=1)
def baseline():
    path=ROOT/'baseline.json'
    return json.loads(path.read_text()) if path.exists() else {}

@lru_cache(maxsize=1)
def fragment_pattern():
    return re.compile('|'.join(re.escape(s) for s in sorted(catalog(),key=len,reverse=True) if HAN.search(s)))

def text(value, fields=None, strict=False):
    if not isinstance(value,str) or not HAN.search(value): return value
    entries=catalog();fields=fields or {}
    if value in fields: return fields[value]
    if value in entries: return entries[value]
    stripped=value.strip()
    if stripped in fields or stripped in entries: return value.replace(stripped,fields.get(stripped,entries.get(stripped)))
    page=re.fullmatch(r'文件第 (\d+) 页',value)
    if page:return 'Physical page '+page[1]
    paragraph=re.fullmatch(r'段落 (\d+)',value)
    if paragraph:return 'Paragraph '+paragraph[1]
    if strict: raise PlatformError('The reviewed English text is missing or out of date','english_unavailable',503)
    # UI/errors/exports contain authored fragments around variable numbers or IDs.
    if fields:
        for source in sorted(fields,key=len,reverse=True):
            if isinstance(fields[source],str):value=value.replace(source,fields[source])
    return fragment_pattern().sub(lambda m:entries[m[0]],value)

def project(value, fields=None, key='', strict=True):
    if key in ORIGINAL: return copy.deepcopy(value)
    if isinstance(value,str):
        if key=='image_url' and value in ('/report-figures/anthropic-20261009-boundaries.png','/report-figures/anthropic-20261009-defenses.png'):
            return value[:-4]+'-en.svg'
        if value.startswith(('/news/','/watch/','/maps/','/for-you','/for-your-ai')):
            return '/en'+value
        # Material Markdown keeps original citations and offsets; only authored prose is translated.
        return text(value,fields,strict=strict and key!='markdown')
    if isinstance(value,list): return [project(v,fields,key,strict) for v in value]
    if isinstance(value,dict):
        if fields and '__objects__' in fields:
            ident=value.get('id') or value.get('object_id') or value.get('news_id') or value.get('target_id')
            scoped=fields['__objects__'].get(ident,{}) if isinstance(ident,(str,int)) else {}
            fields={**fields,**scoped}
        source_heading=isinstance(value.get('id'),str) and value['id'].startswith('section-') and 'start' in value and 'end' in value
        result={k:copy.deepcopy(v) if (k=='title' and source_heading) or (k=='text' and value.get('content_role')=='source_material') else project(v,fields,k,strict) for k,v in value.items() if k!='translations'}
        if isinstance(result.get('arguments'),dict) and (result.get('tool','').startswith('curated_')):result['arguments']['lang']='en'
        for url_key in ('endpoint','read_url'):
            if isinstance(result.get(url_key),str) and result[url_key].startswith('/api/'):
                url=result[url_key];result[url_key]=url+('&' if '?' in url else '?')+'lang=en' if not re.search(r'[?&]lang=',url) else url
        return result
    return value

def strings(value, key=''):
    if key in ORIGINAL: return set()
    if isinstance(value,str): return {value} if HAN.search(value) else set()
    if isinstance(value,list): return set().union(*(strings(v,key) for v in value)) if value else set()
    if isinstance(value,dict):
        source_heading=isinstance(value.get('id'),str) and value['id'].startswith('section-') and 'start' in value and 'end' in value
        return set().union(*(strings(v,k) for k,v in value.items() if k!='translations' and not (k=='title' and source_heading))) if value else set()
    return set()

def status(kind,item):
    fingerprint=source_hash(kind,item)
    en=item.get('translations',{}).get('en',{})
    approved=not en and fingerprint in baseline().get(kind+':'+item['id'],[])
    fields=en.get('fields',{}) if isinstance(en,dict) else {}
    public=authored(kind,item)
    missing=sorted(s for s in strings(public) if not isinstance(fields.get(s,catalog().get(s)),str) or not fields.get(s,catalog().get(s)) or HAN.search(fields.get(s,catalog().get(s))))
    return {'state':'reviewed' if not missing and (approved or en.get('state')=='reviewed' and en.get('source_hash')==fingerprint) else 'stale' if en.get('source_hash') and en['source_hash']!=fingerprint else 'draft',
            'source_hash':fingerprint,'missing':missing,'fields':{s:fields.get(s,catalog().get(s,'')) for s in sorted(strings(public))}}

def require_review(kind,item):
    result=status(kind,item)
    if result['state']!='reviewed': raise PlatformError('Complete and confirm the English review before publication','english_review_required',409)
    return result['fields']

def review_fingerprint(item):
    """Public translation changes affect revisions; private review reasons do not."""
    en=item.get('translations',{}).get('en',{})
    if en.get('state')!='reviewed':return None
    # A confirmation or check-date refresh alone does not change public prose.
    # Catalog-equivalent approvals have the same reading output as the baseline.
    overrides={s:v for s,v in en.get('fields',{}).items() if v!=catalog().get(s)}
    return {'fields':overrides} if overrides else None

def public_snapshot(kind,source,payload):
    """Use the English approval of this exact historical publication."""
    return project(payload,require_review(kind,source) if strings(authored(kind,source)) else {}) if is_english() else {k:v for k,v in payload.items() if k!='translations'}

def public_fields():
    """Current published translations only; never reads unreviewed draft text."""
    from flask import has_request_context,g
    if has_request_context() and hasattr(g,'english_published_fields'):return g.english_published_fields
    from backend.knowledge.content_workspace import load_published, CONTENT
    fields={'__objects__':{}}
    for kind in ('news','watch','charts'):
        if kind=='charts':
            from backend.knowledge.content_workspace import seeds
            data=load_published(kind,None) or seeds()['charts']
            items=[{'id':'snapshot',**data}]
        else:
            data=load_published(kind,CONTENT/(kind+'.json'));items=data['items']
        for item in items:
            if kind!='charts' and item.get('state')!='published': continue
            en=item.get('translations',{}).get('en',{})
            if en.get('state')=='reviewed' and en.get('source_hash')==source_hash(kind,item):fields['__objects__'][item['id']]=en.get('fields',{})
    from backend.db import get_db
    with get_db() as db:
        rows=db.execute("SELECT p.snapshot FROM knowledge_publications p JOIN knowledge_selections s ON s.record_id=p.record_id AND s.state='published' AND s.revision=p.seq").fetchall()
        for row in rows:
            item=json.loads(row['snapshot']);en=item.get('translations',{}).get('en',{})
            if en.get('state')=='reviewed' and en.get('source_hash')==source_hash('library',item):fields['__objects__'][item['id']]=en.get('fields',{})
    if has_request_context():g.english_published_fields=fields
    return fields
