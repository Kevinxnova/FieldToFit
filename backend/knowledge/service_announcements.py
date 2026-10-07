"""Official event records, bounded baselines and corrections; never publishes."""
import hashlib
import json
import re
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote, urlencode, urljoin, urlsplit
from bs4 import BeautifulSoup
from backend.knowledge import store


def digest(value):
    return hashlib.sha256(store.encode(value).encode()).hexdigest()


def dates(text, year=None):
    text=re.sub(r'\\([.\-])',r'\1',text)
    patterns=[r'(?<![A-Za-z0-9_.\-/])(20\d{2})\s*[年.\-/]\s*(\d{1,2})\s*[月.\-/]\s*(\d{1,2})(?:日)?']
    values=[]
    for m in re.finditer(patterns[0],text):
        try: values.append(date(*map(int,m.groups())).isoformat())
        except ValueError: pass
    if not values and year:
        for m in re.finditer(r'(\d{1,2})\s*月\s*(\d{1,2})\s*日',text):
            try:values.append(date(year,*map(int,m.groups())).isoformat())
            except ValueError:pass
    return list(dict.fromkeys(values))


def clean(value):
    return re.sub(r'\s+',' ',value).strip()


def model_ids(body, explicit=None):
    # URLs, document anchors and HTML attributes are not model identifiers.
    value=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',explicit if explicit is not None else body)
    value=re.sub(r'\\([.\-_/])',r'\1',value)
    value=re.sub(r'https?://\S+',' ',value)
    value=BeautifulSoup(value,'html.parser').get_text(' ',strip=True)
    if explicit is not None:
        candidates=re.findall(r'(?<![\w/])[A-Za-z][\w]*(?:[./\-][\w]+)*(?![\w/])',value)
        return list(dict.fromkeys(candidates))[:100]
    families='qwen|qwq|qvq|wan|doubao|deepseek|glm|mimo|minimax|abab|llama|gpt|claude|gemini|moonshot|kimi|seed|bge|gte|flux|text-embedding|multimodal-embedding|paraformer|cosyvoice|sambert|fun-asr|z-image'
    candidates=re.findall(r'(?<![\w/.\-])(?:'+families+r')[\d._\-][\w.\-]*(?![\w/])',value,re.I)
    named={'qwen-max','qwen-plus','qwen-turbo','qwen-long','qwen-image','qwen-mt-plus','qwen-mt-turbo','qwen-audio-turbo','deepseek-chat','deepseek-reasoner','moonshot-auto','doubao-seed-evolving'}
    return list(dict.fromkeys(x for x in candidates if re.search(r'\d',x) or x.casefold() in named))[:100]


def entry(source, key, title, body, locator, declared=None, effective=None, **meta):
    from backend.knowledge.discovery import material, iso
    fields=meta.get('fields',{})
    models=model_ids(body,fields.get('模型 ID',fields.get('模型ID')))
    gaps=[] if declared and re.fullmatch(r'\d{4}-\d{2}-\d{2}',declared) else ['公告未提供完整发布日期；页面更新时间和型号日期不作发布日期']
    # Entry keys survive body corrections and row reordering. A provider page
    # can contain many events at the same URL; fragments alone are not identity.
    version='notice:'+key
    mat=material(source['url'],body,title='官方公告条目');mat['locator']=locator
    return {'url':source['url'],'version':version,'title':title,'summary':body[:1200],
        'type':'news','published_at':iso(declared),'materials':[mat],
        'metadata':{'primary':True,'change':'service_announcement','entry_key':key,
        'declared_date':declared,'date_precision':'day' if declared and len(declared)==10 else 'month' if declared else 'unknown',
        'effective_dates':effective or [],'models':models,'platform':source['config']['platform'],
        'service_role':'客户端开发者的版本说明；模型归属以原公告为准' if source['config']['provider']=='apple' else '平台提供模型服务；模型作者以原公告为准','gaps':gaps,**meta}}


def sections(soup, levels):
    nodes=list(soup.find_all(True))
    for i,h in enumerate(nodes):
        if h.name not in levels:continue
        end=next((j for j in range(i+1,len(nodes)) if nodes[j].name in levels and int(nodes[j].name[1])<=int(h.name[1])),len(nodes))
        # Serialize top-level siblings, preserving tables, links and source IDs.
        out=[]
        for n in nodes[i+1:end]:
            if n.parent is h.parent:out.append(str(n))
        yield h,BeautifulSoup(''.join(out),'html.parser')


def bailian_notice_payload(script, url):
    # Decode the public page's embedded data; never execute its JavaScript.
    ident=int(urlsplit(url).path.rstrip('/').split('/')[-1])
    marker=re.search(r'\bhttpDatas:\s*',script)
    if not marker:raise ValueError('Official notice data unavailable')
    payload,_=json.JSONDecoder().raw_decode(script[marker.end():])
    detail=next((x['detailInfo'] for x in payload.values() if isinstance(x,dict) and isinstance(x.get('detailInfo'),dict) and x['detailInfo'].get('id')==ident),None)
    if not detail:raise ValueError('Official notice identity mismatch')
    records=[x for x in detail.get('detailList',[]) if x.get('bulletinId')==ident and x.get('language')=='zh' and x.get('website')=='cn']
    if not records:raise ValueError('Official notice language/body unavailable')
    blocks=[BeautifulSoup(x.get('contentHtml',''),'html.parser') for x in records]
    body='\n'.join(x.get_text('\n',strip=True) for x in blocks)
    if len(body)<100:raise ValueError('Official notice body unavailable')
    schedules=[]
    for block in blocks:
        for listing in block.find_all('ul'):
            label=listing.find_previous(['p','h2','h3','h4'])
            if not label or '下线清单' not in label.get_text():continue
            names=[clean(li.get_text(' ',strip=True)) for li in listing.find_all('li',recursive=False)]
            if any(not re.fullmatch(r'[A-Za-z][\w.\-]*',x) for x in names):raise ValueError('Official model list changed')
            schedules.extend({'模型名称':x} for x in names)
        for table in block.find_all('table'):
            rows=table.find_all('tr')
            headers=[clean(x.get_text(' ',strip=True)) for x in rows[0].find_all(['td','th'])] if rows else []
            if not any('模型名称' in x or x=='模型ID' for x in headers):continue
            carried={}
            for row in rows[1:]:
                cells={};col=0
                for td in row.find_all(['td','th'],recursive=False):
                    while col in carried:
                        value,left=carried[col];cells[col]=value
                        if left<=1:del carried[col]
                        else:carried[col]=(value,left-1)
                        col+=1
                    value=clean(td.get_text(' ',strip=True));span=int(td.get('colspan',1))
                    for step in range(span):
                        cells[col]=value if step==0 else ''
                        if int(td.get('rowspan',1))>1:carried[col]=(cells[col],int(td['rowspan'])-1)
                        col+=1
                while col in carried:
                    value,left=carried[col];cells[col]=value
                    if left<=1:del carried[col]
                    else:carried[col]=(value,left-1)
                    col+=1
                if len(cells)!=len(headers):raise ValueError('Official notice model table changed')
                schedules.append(dict(zip(headers,[cells[i] for i in range(len(headers))])))
    if not schedules:raise ValueError('Official model deprecation table unavailable')
    deprecated=[next((v for k,v in x.items() if '模型名称' in k or k.replace(' ','')=='模型ID'),'') for x in schedules]
    replaced=[next((v for k,v in x.items() if '替换模型' in k),'') for x in schedules]
    if not all(deprecated):raise ValueError('Official model identifiers unavailable')
    ms=detail.get('publishTime')
    if type(ms)!=int:raise ValueError('Official notice publication date unavailable')
    timestamp=datetime.fromtimestamp(ms/1000,timezone.utc)
    from zoneinfo import ZoneInfo
    return {'body':body,'published_at':timestamp.isoformat().replace('+00:00','Z'),
        'declared_date':timestamp.astimezone(ZoneInfo('Asia/Shanghai')).date().isoformat(),
        'deprecated_models':list(dict.fromkeys(m for value in deprecated for m in model_ids('',value))),
        'replacement_models':list(dict.fromkeys(x for x in replaced if x and x!='/')),
        'schedule_records':schedules,'effective_dates':dates(body)}


def read_bailian_notice(url):
    from backend.knowledge.sources import fetch
    raw,_,_=fetch(url);soup=BeautifulSoup(raw,'html.parser')
    script=next((x['src'] for x in soup.select('script[src]') if re.fullmatch(r'https://cloud-assets\.alicdn\.com/lowcode/entry/prod/[0-9a-f]+\.js',x['src'])),None)
    if not script:raise ValueError('Official notice embedded data link unavailable')
    raw,_,_=fetch(script,max_bytes=5_000_000)
    return bailian_notice_payload(raw.decode('utf-8'),url)


def parse(source, raw):
    cfg=source['config'];provider=cfg['provider'];kind=cfg['notice_kind'];results=[]
    if provider=='ark':
        payload=json.loads(raw);r=payload.get('Result',{})
        if r.get('DocumentCode')!=cfg['document_code'] or r.get('LibraryCode')!='ark':raise ValueError('Official document identity mismatch')
        md=r.get('MDContent','')
        if len(md)<100:raise ValueError('Official document body unavailable')
        if kind=='deprecation':
            # A deprecation batch contains different model deadlines and exceptions;
            # retain the entire schedule, never assign the first deadline to all IDs.
            blocks=re.split(r'(?m)^# ',md)[1:]
            for block in blocks:
                title=block.splitlines()[0].strip()
                if not dates(block):continue
                key=digest([cfg['document_code'],title])[:24]
                results.append(entry(source,key,title,block,'Markdown heading: '+title,
                    effective=dates(block),schedule_text=block[:12000]))
        else:
            section='';headers=[];slot={}
            for line in md.splitlines():
                if re.match(r'^# ',line):section=line[2:].strip();slot={}
                if not line.startswith('|'):continue
                cells=[re.sub(r'\\([\-.*_/])',r'\1',x.strip()).replace('**','') for x in re.split(r'(?<!\\)\|',line)[1:-1]]
                if all(re.fullmatch(r'[:\- ]+',x or '-') for x in cells):continue
                if any(x in ('模型 ID','功能模块') for x in cells):headers=cells;continue
                if not headers or len(cells)!=len(headers):raise ValueError('Official Markdown table structure changed')
                data=dict(zip(headers,cells));label=data.get('模型 ID') or data.get('功能模块')
                if not label:continue
                # Multiple changes in the same module use their actual linked docs
                # or change label, not a positional row number.
                identity=label if data.get('模型 ID') else [label,re.findall(r'\]\(([^)]+)\)',line)]
                key=digest([section,identity])[:24]
                slot[key]=True
                ds=dates(section);month=re.fullmatch(r'(20\d{2})(\d{2})',section)
                declared=ds[0] if ds else month[1]+'-'+month[2] if month else None
                results.append(entry(source,key,label+' · '+section,' | '.join(cells),'Markdown section '+section+' / '+label,declared=declared,
                    provider=data.get('提供方',''),region='原文未单列地域',fields=data))
    else:
        soup=BeautifulSoup(raw,'html.parser')
        if provider=='apple':
            script=soup.find('script',id='serialized-server-data')
            if not script:raise ValueError('App Store version records unavailable')
            data=json.loads(script.string)['data'][0]['data']
            shelf=data['shelfMapping']['mostRecentVersion']
            shelves=shelf.get('seeAllAction',{}).get('pageData',{}).get('shelves',[])
            items=[x for s in shelves for x in s.get('items',[])] or shelf['items']
            for x in items:
                v=x.get('primarySubtitle','').removeprefix('版本 ').strip();body=x.get('text','')
                if not v:raise ValueError('Incomplete App Store release record')
                body=body or '开发者未提供此版本发布说明'
                value=x.get('secondarySubtitle','')
                try:declared=datetime.strptime(value.split(' GMT')[0],'%a %b %d %Y %H:%M:%S').replace(tzinfo=timezone.utc).isoformat().replace('+00:00','Z')
                except ValueError:raise ValueError('App Store release date unavailable')
                e=entry(source,v,'豆包 '+cfg['platform']+' '+v,body,'App Store version history / '+v,declared=declared[:10],client_version=v,developer=data.get('developerAction',{}).get('title','原文未提供开发者名称'))
                e['published_at']=declared;results.append(e)
        elif kind=='deprecation':
            for h,block in sections(soup,('h2','h3')):
                title=clean(h.get_text(' ',strip=True));ds=dates(title)
                if not ds:continue
                body=clean(block.get_text(' ',strip=True));links=[urljoin(source['url'],a['href']) for a in block.select('a[href]')]
                if not body:continue
                if provider=='bailian':
                    for link in links:
                        if not link.startswith('https://www.aliyun.com/notice/'):continue
                        e=entry(source,digest(link)[:24],title,body,'Heading '+title+' / '+link,effective=ds,follow_url=link)
                        e['metadata']['gaps'].append('型号与具体停用范围需继续读取链接的官方公告');results.append(e)
                else:results.append(entry(source,h.get('id') or digest(title)[:24],title,body,'Heading '+title,effective=dates(body) or ds,schedule_text=body))
        elif provider=='mimo':
            for h,block in sections(soup,('h2',)):
                title=clean(h.get_text(' ',strip=True));ds=dates(title)
                if not ds:continue
                body=clean(block.get_text(' ',strip=True))
                if not body:raise ValueError('MiMo release body unavailable')
                results.append(entry(source,h.get('id') or digest(title)[:24],title,body,'Heading '+title,declared=ds[0]))
        else:
            for table in soup.find_all('table'):
                heading=table.find_previous(['h2','h3','h4']);section=clean(heading.get_text(' ',strip=True)) if heading else ''
                year_match=table.find_all_previous(['h2','h3','h4'])
                year=next((int(m[1]) for h in year_match if (m:=re.search(r'(20\d{2})\s*年',h.get_text()))),None)
                trs=table.find_all('tr');headers=[clean(x.get_text(' ',strip=True)).replace(' ','') for x in trs[0].find_all(['th','td'])] if trs else []
                carried={}
                for tr in trs[1:]:
                    cells={};col=0
                    for td in tr.find_all(['td','th'],recursive=False):
                        while col in carried:
                            val,left=carried[col];cells[col]=val
                            if left<=1:del carried[col]
                            else:carried[col]=(val,left-1)
                            col+=1
                        value=clean(td.get_text(' ',strip=True));cells[col]=value
                        if int(td.get('rowspan',1))>1:carried[col]=(value,int(td['rowspan'])-1)
                        col+=1
                    while col in carried:
                        val,left=carried[col];cells[col]=val
                        if left<=1:del carried[col]
                        else:carried[col]=(val,left-1)
                        col+=1
                    # Some official rows omit only the deployment-range cell;
                    # the explicit code element identifies the model column.
                    if len(cells)==len(headers)-1 and '服务部署范围' in headers and tr.find('code'):
                        missing=headers.index('服务部署范围');values=[cells[i] for i in range(len(cells))];values.insert(missing,'原文未填写');cells=dict(enumerate(values))
                    if len(cells)!=len(headers):raise ValueError('Official HTML table structure changed')
                    fields=dict(zip(headers,[cells[i] for i in range(len(headers))]));date_text=fields.get('时间') or fields.get('日期','');ds=dates(date_text,year)
                    label=fields.get('模型ID') or fields.get('功能点')
                    if not label:continue
                    key=digest([year,section,date_text,label,fields.get('功能模块',''),fields.get('服务部署范围','')])[:24]
                    body=' | '.join(fields.values());region=fields.get('服务部署范围') or section
                    results.append(entry(source,key,label+' · '+region,body,'Table '+section+' / '+date_text+' / '+label,declared=ds[0] if ds else None,region=region,fields=fields))
    if not results:raise ValueError('No readable official event records; a reachable shell is not coverage')
    unique={}
    for e in results:
        key=e['metadata']['entry_key']
        if key in unique:
            old=unique[key]
            if e['materials'][0]['body'] not in old['materials'][0]['body']:
                old['materials'][0]['body']+='\n'+e['materials'][0]['body']
                old['materials'][0]['content_hash']=hashlib.sha256(old['materials'][0]['body'].encode()).hexdigest()
                old['summary']=old['materials'][0]['body'][:1200]
                old['metadata']['gaps'].append('同一时期同一型号/功能有多条说明，原文合并保留；确切事件边界待核实')
        else:unique[key]=e
    return list(unique.values())


def collect(source):
    from backend.knowledge import sources
    from backend.knowledge.discovery import capture, Article, material
    from backend.knowledge.paging import progress,save_progress
    cfg=source['config'];state=progress(source['id']);url=source['url']
    if cfg['provider']=='ark':url='https://docs.volcengine.com/api/doc/getDocDetail?'+urlencode({'LibraryCode':'ark','DocumentCode':cfg['document_code']})
    raw,_,_=sources.fetch(url,max_bytes=5_000_000);entries=parse(source,raw)
    from backend.knowledge.content_workspace import today as beijing_day
    today=date.fromisoformat(beijing_day());cutoff=(today-timedelta(days=30)).isoformat()
    eligible=[]
    for e in entries:
        m=e['metadata'];d=m['declared_date'];effective=m['effective_dates']
        if d and d[:7]>today.isoformat()[:7]:continue
        if d and len(d)==10 and d>today.isoformat():continue
        recent=not d or (d[:7]>=cutoff[:7] if len(d)==7 else d>=cutoff)
        if cfg['notice_kind']=='deprecation' and not d:
            # A missing publication date does not make every expired plan recent.
            recent=bool(effective and max(effective)>=cutoff)
        if recent or any(x>=today.isoformat() for x in effective):eligible.append(e)
    if not eligible and not state.get('initialized'):
        # A quiet client still has a verifiable latest historical release.
        eligible=entries[:1]
    seen=state.get('seen_entries',{});pending=state.get('pending',[]);bykey={e['metadata']['entry_key']:e for e in eligible}
    queue=[x for x in pending if x['key'] in bykey]
    for key,e in bykey.items():
        fp=digest([e['title'],e['materials'][0]['body']])
        if seen.get(key)!=fp and not any(x['key']==key for x in queue):queue.append({'key':key,'baseline':not state.get('initialized')})
    found=changed=0;errors=[];remaining=[]
    for pos,item in enumerate(queue):
        if pos>=5:remaining.append(item);continue
        e=bykey[item['key']];meta=e['metadata'];meta['baseline']=item['baseline']
        if item['baseline']:meta['gaps'].append('首次历史基线，保留原日期，不作为今日新增公告')
        if meta.get('follow_url'):
            try:
                notice=read_bailian_notice(meta['follow_url']);body=notice.pop('body')
                e['published_at']=notice.pop('published_at');meta.update(notice,date_precision='day',notice_text=body)
                meta['models']=meta['deprecated_models']
                m=material(meta['follow_url'],body);m['locator']='Official notice embedded contentHtml / model table';e['materials'].append(m)
                e['summary']=body[:1200]
                meta['gaps']=[x for x in meta['gaps'] if '需继续读取' not in x and '未提供完整发布日期' not in x]
            except Exception as exc:
                errors.append(type(exc).__name__+': '+str(exc)[:180]);remaining.append(item)
                # A failed linked-body recheck is not a correction. Preserve the
                # complete last successful record, including model/date metadata.
                if item['key'] in seen:
                    found+=1
                    continue
        # The linked notice is rechecked in subsequent cycles, even without index changes.
        changed+=capture(source,e);found+=1
        if item not in remaining:seen[item['key']]=digest([e['title'],e['materials'][0]['body']])
    # Linked notices can be corrected without any index change. Round-robin them
    # within the same five-entry budget after completing the initial queue.
    if not remaining:
        linked=[k for k,e in bykey.items() if e['metadata'].get('follow_url')]
        remaining=[{'key':k,'baseline':False} for k in linked]
    save_progress(source['id'],{'initialized':True,'pending':remaining,'seen_entries':seen,'last_page_at':store.now(),
        'status':'backlog' if remaining else 'complete','errors':errors,'baseline_cutoff':cutoff,'readable_entries':len(entries)})
    if errors or len(queue)>5:raise sources.PartialSourceError(found,changed,'官方条目已保存；'+str(len(remaining))+' 条待续；'+'、'.join(errors))
    return found,changed
