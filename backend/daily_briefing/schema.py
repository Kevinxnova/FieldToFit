"""Strict daily snapshot validation; facts and evidence cannot be translated away."""
import hashlib
import ipaddress
import json
import math
import re
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
from backend.knowledge.platform import PlatformError

from .schedule import TZ, CUTOFF_AT, local_time
from .watchlist import securities, TICKER_GROUP
LEGACY_SECTIONS = ('companies', 'chips', 'robotics', 'infrastructure', 'policy')
SECTIONS = (*LEGACY_SECTIONS, 'business')
EDITION_ORDER = ('highlights', 'companies', 'products', 'chips', 'robotics', 'infrastructure', 'policy', 'business', 'markets')
DIMENSIONS = ('global_companies', 'china_companies', 'chips', 'open_source', 'coding', 'agents_robotics', 'infrastructure', 'research', 'policy', 'business', 'markets')
LABELS = {'highlights': ('今日重点', 'Highlights'), 'companies': ('AI公司', 'AI companies'), 'products': ('热点 AI 产品追踪', 'AI product tracker'), 'chips': ('AI芯片', 'AI chips'), 'robotics': ('具身智能', 'Embodied AI'), 'infrastructure': ('基础设施', 'Infrastructure'), 'policy': ('监管政策', 'Policy'), 'business': ('商业动态', 'Business'), 'markets': ('AI股市', 'AI markets')}

def news_sections(issue):
    return SECTIONS if issue.get('layout_version') in (2, 3) else LEGACY_SECTIONS

def edition_sections(issue):
    """Old snapshots retain their original layout and content hash."""
    keys = EDITION_ORDER if issue.get('layout_version') in (2, 3) else ('highlights', *LEGACY_SECTIONS, 'markets')
    return [(key, *LABELS[key]) for key in keys]
SECURITIES = {
 'us': [('NVDA','NVIDIA','NVIDIA'),('AMD','AMD','AMD'),('INTC','Intel','Intel'),('MSFT','微软','Microsoft'),('GOOGL','Alphabet','Alphabet'),('META','Meta','Meta'),('AMZN','亚马逊','Amazon')],
 'cn': [('688256','寒武纪','Cambricon'),('002230','科大讯飞','iFlytek'),('688041','海光信息','Hygon')],
 'hk': [('09888','百度','Baidu'),('09988','阿里巴巴','Alibaba'),('00700','腾讯','Tencent'),('00020','商汤','SenseTime'),('00981','中芯国际','SMIC')],
}
CURRENCIES = {'us':'USD', 'cn':'CNY', 'hk':'HKD', 'kr':'KRW'}

def fail(message, code='daily_invalid', status=400):
    raise PlatformError(message, code, status)

def stamp(value=None):
    return (value or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')

def instant(value):
    try:
        result = datetime.fromisoformat(value.replace('Z','+00:00'))
        if result.tzinfo is None: raise ValueError()
        return result
    except (ValueError, TypeError, AttributeError): fail('A timestamp with timezone is required')

def day_key(value):
    if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value): fail('Use YYYY-MM-DD')
    try: date.fromisoformat(value)
    except ValueError: fail('Invalid calendar date')
    return value

def text(value, label, maximum=2000):
    if not isinstance(value,str) or not value.strip() or len(value)>maximum: fail('Missing or invalid '+label)
    # Public copy is plain text, with source links represented structurally.
    if re.search(r'<\s*/?\s*(script|iframe|style)\b',value,re.I): fail('Markup is not permitted in '+label)
    return value.strip()

def bilingual(value,label,maximum=2000):
    if not isinstance(value,dict) or set(value)!= {'zh','en'}: fail('Both languages are required: '+label)
    for lang in ('zh','en'): text(value[lang],label+'.'+lang,maximum)
    if re.search(r'[\u3400-\u9fff]',value['en']): fail('English copy cannot fall back to Chinese: '+label)
    return value

def public_url(value):
    text(value,'source URL',1800)
    p=urlsplit(value)
    if p.scheme!='https' or not p.hostname or p.username or p.password: fail('Public HTTPS source URL required')
    host=p.hostname.lower()
    if host=='localhost' or host.endswith(('.local','.localhost','.internal')): fail('Local source URL is forbidden')
    try: address=ipaddress.ip_address(host)
    except ValueError: address=None
    if address and not address.is_global: fail('Private source URL is forbidden')
    return value

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def project(value,lang='zh'):
    if lang not in ('zh','en'): fail('Unsupported language')
    if isinstance(value,dict):
        if set(value)=={'zh','en'}: return value[lang]
        return {k:project(v,lang) for k,v in value.items()}
    if isinstance(value,list): return [project(v,lang) for v in value]
    return value

def validate(raw, now=None):
    if not isinstance(raw,dict): fail('Issue must be an object')
    now=now or datetime.now(timezone.utc)
    required={'schema_version','date','kind','window_start','cutoff_at','headline','intro','takeaway','closing','stories','products','sources','markets','coverage','section_notes'}
    if raw.get('layout_version') == 3: required.add('market_overview')
    if set(raw)-required-{'image','layout_version'} or required-set(raw): fail('Invalid daily snapshot fields')
    if 'layout_version' in raw and (type(raw['layout_version']) is not int or raw['layout_version'] not in (2, 3)): fail('Unknown daily layout')
    if raw['schema_version']!='fieldtofit.daily.v1': fail('Unknown daily schema')
    day=day_key(raw['date']);cutoff=instant(raw['cutoff_at']);start=instant(raw['window_start'])
    if cutoff>now or start>=cutoff or cutoff-start>timedelta(days=2): fail('Invalid or future news window')
    if cutoff.astimezone(TZ).date().isoformat()!=day: fail('Cutoff must belong to the issue date in Beijing')
    if raw['kind'] not in ('daily','review_sample'): fail('Invalid edition kind')
    if raw['kind']=='daily' and local_time(cutoff)!=CUTOFF_AT: fail('Daily cutoff is '+CUTOFF_AT.strftime('%H:%M')+' Asia/Shanghai')
    if raw.get('layout_version') in (2, 3) and raw['kind'] == 'daily' and cutoff-start != timedelta(days=1): fail('Nine-section daily news window must be exactly 24 hours')
    for k in ('headline','intro','takeaway','closing'): bilingual(raw[k],k,1600 if k!='headline' else 160)
    if not isinstance(raw['sources'],list) or len(raw['sources'])>100: fail('At most 100 sources')
    source_ids=set()
    for s in raw['sources']:
        if set(s)!={'id','title','url','published_at','checked_at'}: fail('Invalid source fields')
        text(s['id'],'source id',80);bilingual(s['title'],'source title',300);public_url(s['url'])
        if s['id'] in source_ids: fail('Duplicate source id')
        source_ids.add(s['id'])
        if instant(s['checked_at'])>now: fail('Future source check')
        if s['published_at']:
            try:
                published=instant(s['published_at']) if 'T' in s['published_at'] else datetime.combine(date.fromisoformat(day_key(s['published_at'])),datetime.min.time(),TZ)
            except (TypeError,ValueError): fail('Invalid original publication date')
            if published>cutoff: fail('Post-cutoff source belongs in the next issue')
    def refs(v):
        if not isinstance(v,list) or not v or len(set(v))!=len(v) or not set(v)<=source_ids: fail('Every claim needs registered source references')
    if not isinstance(raw['stories'],list) or len(raw['stories'])>20: fail('At most 20 distinct news events')
    ids=set();keys=set();highlights=0
    for s in raw['stories']:
        expected={'id','event_key','section','dimensions','event_date','title','summary','analysis','source_ids','highlight'}
        if raw.get('layout_version') == 3:
            expected.update(('freshness','date_label'))
            if s.get('highlight'): expected.update(('highlight_title','highlight_summary'))
            if s.get('freshness') not in ('new','recent','watch'): fail('State news freshness')
            bilingual(s.get('date_label'),'original date label',200)
            for k in ('highlight_title','highlight_summary'):
                if s.get('highlight'): bilingual(s.get(k),k,240)
            age=(cutoff.astimezone(TZ).date()-date.fromisoformat(day_key(s.get('event_date')))).days
            if age < 0 or age > {'new':1,'recent':3,'watch':7}[s['freshness']]: fail('Event date is outside its freshness window')
        if set(s)-expected-{'metric'} or expected-set(s): fail('Invalid story fields')
        if not re.fullmatch(r'[a-z][a-z0-9-]{0,60}',s['id']) or s['id'] in ids: fail('Duplicate or invalid story id')
        ids.add(s['id']);text(s['event_key'],'event identity',200)
        if s['event_key'] in keys: fail('Duplicate event; use a cross-reference')
        keys.add(s['event_key'])
        if s['section'] not in news_sections(raw): fail('Unknown public section')
        if not isinstance(s['dimensions'],list) or not s['dimensions'] or not set(s['dimensions'])<=set(DIMENSIONS): fail('Invalid coverage dimensions')
        if day_key(s['event_date'])>day: fail('Future event date')
        for k in ('title','summary','analysis'): bilingual(s[k],k,200 if k=='title' else 1800)
        refs(s['source_ids'])
        if type(s['highlight']) is not bool: fail('Highlight must be boolean')
        highlights+=s['highlight']
        if 'metric' in s:
            m=s['metric']
            if set(m)!={'value','label','note'}: fail('Invalid key figure')
            text(m['value'],'key figure',24);bilingual(m['label'],'figure label',160);bilingual(m['note'],'figure qualification',240)
    if highlights>3: fail('At most three highlights')
    if raw['stories'] and not highlights: fail('Choose at least one highlight')
    notes=raw['section_notes']
    if not isinstance(notes,dict) or set(notes)!=set(news_sections(raw)): fail('All news sections need a coverage note')
    for k,v in notes.items(): bilingual(v,'section note '+k,400)
    if not isinstance(raw['products'],list) or len(raw['products'])>30: fail('At most 30 products')
    product_ids=set()
    for p in raw['products']:
        product_fields={'id','name','organization','version','release_date','checked_at','changes','source_ids','is_new'}
        if raw.get('layout_version') == 3:
            product_fields.add('release_channel')
            if p.get('release_channel') not in ('stable','alpha','beta','nightly','preview','announced'): fail('Product channel is required')
        if set(p)!=product_fields: fail('Invalid product fields')
        text(p['id'],'product id',80)
        if p['id'] in product_ids: fail('Duplicate product')
        product_ids.add(p['id'])
        for k in ('name','organization','version','changes'): bilingual(p[k],k,900 if k=='changes' else 180)
        if day_key(p['release_date'])>day or instant(p['checked_at'])>now: fail('Invalid product date')
        if type(p['is_new']) is not bool: fail('Product grouping required')
        refs(p['source_ids'])
    coverage=raw['coverage']
    if not isinstance(coverage,list) or {v.get('dimension') for v in coverage}!=set(DIMENSIONS) or len(coverage)!=11: fail('All eleven dimensions must have a coverage record')
    for v in coverage:
        if set(v)!={'dimension','state','checked_at','source_ids','note'}: fail('Invalid coverage fields')
        if v['state'] not in ('checked','limited','failed'): fail('Invalid coverage state')
        bilingual(v['note'],'coverage note',500)
        if instant(v['checked_at'])>now: fail('Future coverage date')
        if v['state']=='checked': refs(v['source_ids'])
        elif not isinstance(v['source_ids'],list) or not set(v['source_ids'])<=source_ids: fail('Unknown coverage source')
    if raw.get('layout_version') == 3:
        overview=raw['market_overview']
        if not isinstance(overview,dict) or set(overview)!={'title','summary','note'}: fail('Market overview is required')
        for k,v in overview.items(): bilingual(v,'market '+k,1600)
    markets=raw['markets']
    watchlist=securities(SECURITIES,raw.get('layout_version'))
    if not isinstance(markets,list) or len(markets)!=len(watchlist) or {m.get('id') for m in markets}!=set(watchlist): fail('All configured market snapshots are required')
    for m in markets:
        if set(m)!={'id','currency','trade_date','closed_at','state','note','rows'}: fail('Invalid market fields')
        key=m['id']
        if m['currency']!=CURRENCIES[key] or m['state'] not in ('closed','holiday','unavailable'): fail('Invalid currency or market state')
        bilingual(m['note'],'market time/coverage note',600)
        if m['trade_date'] is not None:
            if day_key(m['trade_date'])>day or (not m['closed_at'] and raw['kind']!='review_sample') or (m['closed_at'] and instant(m['closed_at'])>cutoff): fail('Only completed sessions before cutoff may be used')
            market_tz=ZoneInfo('America/New_York') if key=='us' else ZoneInfo('Asia/Seoul') if key=='kr' else TZ
            if m['closed_at'] and instant(m['closed_at']).astimezone(market_tz).date().isoformat()!=m['trade_date']: fail('Trading date and close timestamp disagree')
        elif m['state']!='unavailable' or m['closed_at'] is not None: fail('Missing trading date must be unavailable')
        if not isinstance(m['rows'],list) or len(m['rows'])!=len(watchlist[key]) or {r.get('ticker') for r in m['rows']}!={s[0] for s in watchlist[key]}: fail('Market watchlist is incomplete or duplicated')
        for r in m['rows']:
            expected_row={'ticker','name','price','change_pct','state','source_ids','as_of','delay_minutes'}
            if raw.get('layout_version') == 3:
                expected_row.add('group')
                if r.get('group')!=TICKER_GROUP[r['ticker']]: fail('Security industry group is incorrect')
            if set(r)!=expected_row: fail('Invalid quote fields')
            bilingual(r['name'],'security name',100)
            if r['state'] not in (('verified','partial','missing','suspended') if raw.get('layout_version') == 3 else ('verified','missing','suspended')): fail('Invalid quote state')
            if r['state'] in ('verified','partial'):
                if m['state']=='unavailable': fail('Unavailable market cannot have verified prices')
                if r['state']=='partial' and r['change_pct'] is not None: fail('Partial quote must leave unverified change empty')
                for field in (('price',) if r['state']=='partial' else ('price','change_pct')):
                    n=r[field]
                    if type(n) not in (int,float) or not math.isfinite(n): fail('Quotes must be finite numbers')
                if r['price']<=0 or (r['change_pct'] is not None and r['change_pct'] < -100): fail('Invalid price or percentage')
                refs(r['source_ids'])
                if r['as_of']!=m['closed_at']: fail('Quote must match the stated complete close')
            elif r['price'] is not None or r['change_pct'] is not None or r['as_of'] is not None: fail('Missing quotes must be empty, never stale prices')
            elif not isinstance(r['source_ids'],list) or not set(r['source_ids'])<=source_ids: fail('Unknown quote source')
            if r['delay_minutes'] is not None and (type(r['delay_minutes']) is not int or r['delay_minutes']<0): fail('Unknown delay must remain null')
    if raw.get('image'):
        im=raw['image']
        if set(im)!={'url','source_id','alt','caption','credit','reuse_basis'}: fail('Invalid image fields')
        public_url(im['url']);refs([im['source_id']]);bilingual(im['alt'],'image description',300);bilingual(im['caption'],'image caption',300);text(im['credit'],'image credit',200);text(im['reuse_basis'],'image reuse basis',600)
    # Round-trip strips subclasses and disallows NaN, but never leaks arbitrary fields.
    return json.loads(json.dumps(raw,ensure_ascii=False,allow_nan=False))
