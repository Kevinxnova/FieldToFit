"""Bounded, source-backed discovery. No public record or editorial draft writes."""
import hashlib
import json
import re
import time
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, urlencode, quote, parse_qs, urlunsplit
import feedparser
from backend.db import get_db
from backend.knowledge import store
from backend.knowledge.workspace_transactions import editorial_transaction


def iso(value):
    try:
        if isinstance(value,str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):
            parsed=datetime.strptime(value,'%Y-%m-%d').date()
            return value if parsed<=datetime.now(timezone.utc).date() else None
        d=datetime.fromisoformat(value.replace('Z','+00:00'))
        if d.tzinfo is None or d>datetime.now(timezone.utc):return None
        return d.astimezone(timezone.utc).isoformat().replace('+00:00','Z')
    except (ValueError,TypeError,AttributeError):return None


def displayed_date(text):
    match=re.search(r'\b([A-Za-z]{3,9} \d{1,2}, \d{4})\b',text)
    if match:
        for fmt in ('%b %d, %Y','%B %d, %Y'):
            try:return iso(datetime.strptime(match[1],fmt).date().isoformat())
            except ValueError:pass
    return None


class Article(HTMLParser):
    def __init__(self):
        super().__init__();self.skip=0;self.main=0;self.in_title=False;self.parts=[];self.all=[];self.title=[];self.links=[];self.link_labels=[];self.active_link=None;self.date=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in ('script','style','nav','footer','header','noscript'):self.skip+=1
        if tag in ('article','main'):self.main+=1
        if tag=='h1':self.in_title=True
        if tag=='a' and a.get('href'):
            self.links.append(a['href']);self.active_link=[a['href'],[]]
        if tag=='meta' and a.get('property') in ('article:published_time','datePublished'):self.date=iso(a.get('content')) or self.date
        if tag=='time':self.date=iso(a.get('datetime')) or self.date
        if tag in ('p','h1','h2','h3','li','br','div'):self.handle_data('\n')
    def handle_endtag(self,tag):
        if tag=='a' and self.active_link:
            self.link_labels.append((self.active_link[0],' '.join(self.active_link[1])));self.active_link=None
        if tag in ('script','style','nav','footer','header','noscript'):self.skip=max(0,self.skip-1)
        if tag in ('article','main'):self.main=max(0,self.main-1)
        if tag=='h1':self.in_title=False
    def handle_data(self,data):
        if self.active_link:self.active_link[1].append(data)
        if not self.skip:
            self.all.append(data)
            if self.main:self.parts.append(data)
            if self.in_title:self.title.append(data)
    @property
    def body(self):return '\n'.join(x.strip() for x in ''.join(self.parts or self.all).splitlines() if x.strip())


def material(url,body,coverage='full_text',title='原始材料'):
    return {'url':url,'title':title,'body':body,'coverage':coverage,'locator':'Original source text',
            'content_hash':hashlib.sha256(body.encode()).hexdigest(),'retrieved_at':store.now()}


def capture(source,entry):
    url=store.canonical_url(entry['url']);stamp=store.now();version=str(entry.get('version') or '')
    ident=store.stable_id('daily',url,version)
    materials=list(entry.get('materials',[]));fresh_materials=list(materials);metadata={**entry.get('metadata',{}),'company':source['config'].get('company','')}
    metrics=entry.get('metrics',{})
    hashes=[(m['url'],m['content_hash']) for m in materials if m.get('title')!='Hub metadata']
    fp=hashlib.sha256(store.encode([entry['title'],entry.get('summary',''),version,hashes]).encode()).hexdigest()
    with editorial_transaction() as db:
        old=db.execute('SELECT * FROM fieldtofit_discoveries WHERE id=?',(ident,)).fetchone()
        # A discussion does not replace primary material already collected for the same object.
        primary=metadata.get('primary',False)
        old_primary=bool(old and store.decode(old['metadata'],{}).get('primary'))
        if old and metadata.get('gaps') and not any(m.get('coverage')=='full_text' for m in materials):
            retained=[m for m in store.decode(old['materials'],[]) if m.get('coverage')=='full_text']
            if retained:
                materials+=retained
                metadata['gaps'].append('保留上次可用正文；获取日期未刷新，本次正文未重新核对。')
                fp=old['fingerprint']
        replace=not old or primary or not old_primary
        changed=not old or (replace and old['fingerprint']!=fp)
        if changed and old and replace:
            db.execute('INSERT OR IGNORE INTO fieldtofit_discovery_versions VALUES(?,?,?,?)',(ident,old['fingerprint'],old['materials'],old['updated_at']))
        if replace:
            db.execute('INSERT INTO fieldtofit_discoveries VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET '
                'source_id=excluded.source_id,title=excluded.title,summary=excluded.summary,published_at=excluded.published_at,'
                'discovered_at=CASE WHEN fieldtofit_discoveries.fingerprint!=excluded.fingerprint THEN excluded.discovered_at ELSE fieldtofit_discoveries.discovered_at END,'
                'updated_at=excluded.updated_at,materials=excluded.materials,metrics=excluded.metrics,metadata=excluded.metadata,fingerprint=excluded.fingerprint',
                (ident,source['id'],entry['title'][:1000],entry.get('summary','')[:4000],url,entry.get('type','tool'),iso(entry.get('published_at')),stamp,stamp,version,store.encode(materials),store.encode(metrics),store.encode(metadata),fp))
        db.execute('INSERT INTO fieldtofit_discovery_origins VALUES(?,?,?,?) ON CONFLICT(discovery_id,source_id,url) DO UPDATE SET observed_at=excluded.observed_at',
                   (ident,source['id'],entry.get('origin_url') or url,stamp))
        if changed and old:
            db.execute("UPDATE fieldtofit_inbox SET status='pending',updated_at=? WHERE ref=? AND status='completed'",(stamp,'discovery:'+ident))
        from backend.knowledge.operation_board import event
        ref='discovery:'+ident
        if changed:event(db,source['id'],ref,'changed' if old else 'discovered',fp)
        for m in fresh_materials:
            if m.get('body') and m.get('coverage') in ('full_text','excerpt','abstract'):
                event(db,source['id'],ref,m['coverage'],m.get('content_hash',''))
        if metrics:
            db.execute('INSERT INTO fieldtofit_attention_observations VALUES(?,?,?,?,?) ON CONFLICT(url,source_id,day) DO UPDATE SET observed_at=excluded.observed_at,metrics=excluded.metrics',
                       (url,source['id'],stamp[:10],stamp,store.encode(metrics)))
    from backend.knowledge.candidate_priority import refresh
    refresh(['discovery:'+ident])
    return int(changed)


def collect(source):
    from backend.knowledge.sources import PartialSourceError
    counters=[0,0]
    try:return _collect(source,counters)
    except PartialSourceError:raise
    except Exception as exc:
        if counters[0]:raise PartialSourceError(counters[0],counters[1],'已保存已获取材料；本次检查中断：'+type(exc).__name__) from exc
        raise


def _collect(source,counters):
    from backend.knowledge import sources
    from backend.knowledge.paging import progress,save_progress
    cfg=source['config'];mode=cfg['mode'];limit=min(max(int(cfg.get('limit',8)),1),20)
    state=progress(source['id']);boundary=(None if cfg.get('recheck_body') else state.get('watermark')) or (datetime.now(timezone.utc)-timedelta(days=int(cfg.get('history_days',7)))).isoformat()
    earliest=datetime.fromisoformat(boundary.replace('Z','+00:00'))-timedelta(days=1)
    class Captured(list):
        def append(self,entry):
            counters[1]+=capture(source,entry);counters[0]+=1
            super().append(entry)
    entries=Captured();more=None;errors=[];found=changed=0;started=store.now()
    def error_kind(exc):
        status=getattr(getattr(exc,'response',None),'status_code',None)
        return ('HTTP '+str(status)) if status else ('读取超时' if isinstance(exc,TimeoutError) or 'Timeout' in type(exc).__name__ else str(exc)[:160] if isinstance(exc,ValueError) else type(exc).__name__)
    def recent(value):
        value=iso(value)
        return not value or datetime.fromisoformat(value.replace('Z','+00:00')).replace(tzinfo=timezone.utc)>=earliest
    if mode=='hub':
        # A failed card stays eligible even if its model revision predates the watermark.
        with get_db() as db:
            retry_names={r[0] for r in db.execute("SELECT title FROM fieldtofit_discoveries WHERE source_id=? AND json_array_length(json_extract(metadata,'$.gaps'))>0",(source['id'],)).fetchall()}
        query={'sort':'lastModified','direction':-1,'limit':limit,'full':'true'}
        if cfg.get('author'):query['author']=cfg['author']
        url='https://huggingface.co/api/models?'+urlencode(query)
        # Every cycle checks the head before any unfinished older page.
        pages=[url]
        if state.get('next_url'):pages.append(state['next_url'])
        seen=set()
        for page_url in pages:
            if urlsplit(page_url).hostname!='huggingface.co' or not urlsplit(page_url).path.startswith('/api/models'):raise ValueError('Invalid Hub continuation')
            raw,_,_,headers=sources.fetch(page_url,with_headers=True);items=json.loads(raw)
            if not isinstance(items,list):raise ValueError('Hub did not return models')
            match=re.search(r'<([^>]+)>;\s*rel="?next',headers.get('link',''))
            more=match.group(1) if match and items and all(recent(x.get('lastModified')) for x in items) else None
            for item in items:
                name=item.get('id')
                if not name or name in seen or (state and not recent(item.get('lastModified')) and name not in retry_names):continue
                if cfg.get('author') and name.split('/')[0].lower()!=cfg['author'].lower():raise ValueError('Hub author filter did not match')
                seen.add(name);original='https://huggingface.co/'+name;version=item.get('sha') or ''
                mats=[material(original,store.encode(item),'excerpt','Hub metadata')];gaps=[]
                try:
                    card_url=original+'/raw/'+quote(version or 'main',safe='')+'/README.md'
                    body,final,_=sources.fetch(card_url);mats.append(material(final,body.decode('utf-8'),'full_text','Model card'))
                except Exception as exc:
                    gaps.append('模型卡读取失败：'+error_kind(exc));errors.append(card_url+' · '+gaps[-1])
                entries.append({'url':original,'title':name,'summary':(item.get('cardData') or {}).get('description') or item.get('pipeline_tag') or '',
                    'type':'model','version':version,'published_at':item.get('createdAt'),'materials':mats,
                    'metrics':{k:item[k] for k in ('likes','downloads') if isinstance(item.get(k),int)},
                    'metadata':{'primary':True,'gaps':gaps,'upstream_updated_at':item.get('lastModified'),'change':'model_revision'}})
    elif mode=='qwen':
        # This public endpoint is used by qwen.ai/research itself. Ignore internal metadata URLs.
        raw,_,_=sources.fetch('https://qwen.ai/api/v2/article/retrieval?type=qwen_ai&language=zh-CN',max_bytes=8000000)
        payload=json.loads(raw)
        articles=payload.get('data',{}).get('articles')
        if payload.get('success') is not True or not isinstance(articles,list) or not articles:raise ValueError('Qwen public article list unavailable')
        articles=sorted([a for a in articles if recent(a.get('extra',{}).get('date'))],key=lambda a:a.get('extra',{}).get('date',''),reverse=True)
        visited=set(state.get('rechecked',[]));by_id={a['id']:a for a in articles}
        queue=list(dict.fromkeys([a['id'] for a in articles[:max(1,limit//2)]]+[i for i in state.get('pending_ids',[]) if i in by_id]+[a['id'] for a in articles if a['id'] not in visited]))
        for ident in queue[:limit]:
            a=by_id[ident];doc=Article();doc.feed(a.get('content',''));body=doc.body
            if len(body)<100:raise ValueError('Qwen article body missing')
            url='https://qwen.ai/blog?id='+quote(a['path'],safe='-')
            entries.append({'url':url,'title':a['title'],'summary':a.get('extra',{}).get('introduction','')[:1200],
                'type':'news','published_at':a.get('extra',{}).get('date'),'materials':[material(url,body)],
                'metadata':{'primary':True,'change':'official_article','gaps':[],'upstream_article_id':ident}})
            visited.add(ident)
        more=queue[limit:];qwen_visited=list(visited) if more else []
    elif mode=='document':
        raw,final,_=sources.fetch(source['url']);doc=Article();doc.feed(raw.decode('utf-8'))
        body=doc.body
        if len(body)<200:raise ValueError('Official page has no readable primary content')
        entries.append({'url':final,'title':''.join(doc.title).strip() or source['name'],'summary':body[:1200],'type':'news',
            'published_at':None,'materials':[material(final,body)],
            'metadata':{'primary':True,'change':'official_page_revision','gaps':['页面核对日期不是事件发布日期；需逐条核对正文中的事件。']}})
    elif mode in ('feed','index'):
        raw,final,_=sources.fetch(source['url']);pending=[]
        if mode=='feed':
            feed=feedparser.parse(raw)
            if not feed.entries:raise ValueError('No readable feed entries')
            pending=[{'url':e.link,'title':e.title,'published_at':sources.entry_date(e),'modified_at':sources.entry_date(e,'updated'),'excerpt':sources.plain_html(e.get('summary',''))} for e in feed.entries if e.get('link') and e.get('title') and recent(sources.entry_date(e))]
        else:
            prefix=cfg.get('path_prefix','/');urls={}
            index_pending=list(state.get('index_pending',[]));index_seen=set(state.get('index_seen',[]))
            base=urlsplit(final)
            def index_page(url):
                p=urlsplit(url)
                return p.hostname==base.hostname and p.path.rstrip('/')==base.path.rstrip('/')
            def parse_index(body,location):
                index=Article();index.feed(body.decode('utf-8'))
                for href,label in index.link_labels:
                    u=urljoin(location,href);parts=urlsplit(u);u=urlunsplit(parts._replace(fragment=''))
                    if parts.hostname!=base.hostname or not parts.path.startswith(prefix):continue
                    if index_page(u):
                        q=parse_qs(parts.query)
                        if len(q)==1 and q.get('page',[''])[0].isdigit() and int(q['page'][0])>1 and u not in index_seen and u not in index_pending:index_pending.append(u)
                        continue
                    date=displayed_date(label)
                    if u not in urls or date:urls[u]={'url':u,'published_at':date}
            # Older versions accidentally stored directory pages in the article queue.
            for x in state.get('pending',[]):
                if index_page(x['url']) and x['url'] not in index_seen and x['url'] not in index_pending:index_pending.append(x['url'])
            parse_index(raw,final)
            if index_pending and not any(not index_page(x['url']) for x in state.get('pending',[])):
                next_index=index_pending[0]
                parts=urlsplit(next_index);q=parse_qs(parts.query)
                if not index_page(next_index) or len(q)!=1 or not q.get('page',[''])[0].isdigit():raise ValueError('Invalid index continuation')
                try:
                    page_raw,page_final,_=sources.fetch(next_index)
                    if not index_page(page_final):raise ValueError('Index continuation redirected outside directory')
                    index_pending.pop(0);index_seen.add(next_index);parse_index(page_raw,page_final)
                except Exception as exc:errors.append(next_index+' · '+error_kind(exc))
            pending=sorted([x for x in urls.values() if recent(x['published_at'])],key=lambda x:x['published_at'] or '',reverse=True)
        if mode=='index' and cfg.get('company')=='bytedance' and not pending:
            # Public server-rendered router data, parsed as JSON only (never JavaScript).
            match=re.search(r'window\._ROUTER_DATA\s*=\s*(\{.*?\})\s*</script>',raw.decode('utf-8'),re.S)
            if match:
                loader=json.loads(match[1]).get('loaderData',{})
                for page in loader.values():
                    if not isinstance(page,dict):continue
                    for article in page.get('article_list',[]):
                        content=article.get('ArticleSubContentEn',{});meta=article.get('ArticleMeta',{})
                        slug=content.get('TitleKey');published=meta.get('PublishDate')
                        if not slug or not isinstance(published,(int,float)):continue
                        pending.append({'url':urljoin(final,'/en/blog/'+quote(slug,safe='-')),'title':content.get('Title',''),
                            'excerpt':content.get('Abstract',''),'published_at':iso(datetime.fromtimestamp(published/1000,timezone.utc).isoformat()),
                            'modified_at':meta.get('UpdateTime')})
                pending=sorted([x for x in pending if recent(x['published_at'])],key=lambda x:x['published_at'] or '',reverse=True)
        seen_entries=state.get('seen_entries',{})
        def signature(x):return hashlib.sha256(store.encode(x).encode()).hexdigest()
        if mode=='index' and not pending:raise ValueError('Official index has no readable article links')
        pending=[x for x in pending if cfg.get('recheck_body') or seen_entries.get(x['url'])!=signature(x)]
        previous=[x for x in state.get('pending',[]) if mode!='index' or not index_page(x['url'])]
        # One-slot runs must drain the previous queue instead of re-reading the head forever.
        head=pending[:max(1,limit//2)] if limit>1 or not previous else []
        rechecked=set(state.get('rechecked',[]))
        if cfg.get('recheck_body'):pending=[x for x in pending if x['url'] not in rechecked]
        pending=list({x['url']:x for x in head+previous+pending}.values())
        rest=pending[limit:]
        for pos,item in enumerate(pending[:limit]):
            deadline=sources.COLLECTION_DEADLINE.get()
            if deadline and deadline-time.monotonic()<2:
                rest.extend(pending[pos:limit]);errors.append('本次预算已用完，未开始的文章留待下次');break
            try:
                raw,final,_=sources.fetch(item['url']);doc=Article();doc.feed(raw.decode('utf-8'))
                body=doc.body
                if len(body)<100:raise ValueError('Article body unavailable')
                date=doc.date or item.get('published_at')
                if not date:
                    for line in body.splitlines()[:12]:
                        if re.fullmatch(r'[A-Za-z]{3,9} \d{1,2}, \d{4}',line):
                            for fmt in ('%b %d, %Y','%B %d, %Y'):
                                try:date=iso(datetime.strptime(line,fmt).date().isoformat());break
                                except ValueError:pass
                            if date:break
                if not recent(date):
                    seen_entries[item['url']]=signature(item);continue
                entries.append({'url':final,'title':''.join(doc.title).strip() or item.get('title') or urlsplit(final).path.rsplit('/',1)[-1],
                    'summary':body[:1200],'type':'news','published_at':date,'materials':[material(final,body)],
                    'metadata':{'primary':urlsplit(final).hostname==urlsplit(source['url']).hostname,'change':'official_article','gaps':[] if date else ['原文发布日期未知']}})
                seen_entries[item['url']]=signature(item);rechecked.add(item['url'])
            except Exception as exc:
                errors.append(item['url']+' · '+error_kind(exc));rest.append(item)
                if item.get('title'):
                    excerpt=item.get('excerpt','')
                    entries.append({'url':item['url'],'title':item['title'],'summary':excerpt,'type':'news','published_at':item.get('published_at'),
                        'materials':[material(item['url'],excerpt,'excerpt','官方订阅摘要')] if excerpt else [],
                        'metadata':{'primary':urlsplit(item['url']).hostname==urlsplit(source['url']).hostname,'change':'official_article','gaps':['文章正文读取失败：'+type(exc).__name__+'；当前只有订阅线索，等待重试。']}})
        more=rest
    elif mode=='github':
        query=cfg['query']+' pushed:>='+earliest.date().isoformat()
        page=int(state.get('page',1));urls=[1] if page==1 else [1,page]
        seen=set()
        for n in urls:
            data=sources.fetch_json('https://api.github.com/search/repositories?'+urlencode({'q':query,'sort':'stars','order':'desc','per_page':limit,'page':n}))
            if data.get('incomplete_results'):errors.append('GitHub search incomplete')
            if not isinstance(data.get('items'),list):raise ValueError('No GitHub repository list')
            more=n+1 if n*limit<min(data.get('total_count',0),1000) else None
            for item in data['items']:
                repo=item['full_name']
                if repo in seen:continue
                seen.add(repo);url=item['html_url'];mats=[];gaps=[]
                try:
                    import base64
                    readme=sources.fetch_json('https://api.github.com/repos/'+repo+'/readme')
                    body=base64.b64decode(readme['content']).decode('utf-8');mats=[material(readme['html_url'],body)]
                except Exception as exc:
                    gaps.append('README 读取失败：'+type(exc).__name__);errors.append(gaps[-1])
                entries.append({'url':url,'title':repo,'summary':item.get('description') or '',
                    'type':'skill' if 'skills' in cfg['query'] else 'agent','materials':mats,'published_at':item.get('created_at'),
                    'metrics':{'stars':item['stargazers_count']},'metadata':{'primary':bool(mats),'change':'repository','gaps':gaps,'archived':item.get('archived'), 'upstream_updated_at':item.get('pushed_at')}})
    elif mode=='hn':
        data=sources.fetch_json(source['url']+'?'+urlencode({'tags':'story','query':'AI','numericFilters':'created_at_i>'+str(int(earliest.timestamp())),'hitsPerPage':limit}))
        for x in data.get('hits',[]):
            if not x.get('url') or not store.relevant(x.get('title','')):continue
            entries.append({'url':x['url'],'origin_url':'https://news.ycombinator.com/item?id='+x['objectID'],'title':x['title'],'summary':sources.plain_html(x.get('story_text') or ''),'published_at':None,
                'metrics':{k:x[k] for k in ('points','num_comments') if isinstance(x.get(k),int)},
                'metadata':{'primary':False,'change':'discussion','discussion_at':x.get('created_at'),'gaps':['讨论线索，原始材料待核对']}})
    elif mode=='arxiv':
        terms=('DeepSeek','Qwen','Kimi','GLM','Gemini','Claude','agent','harness')
        query=' OR '.join('ti:'+x for x in terms)
        page=int(state.get('offset',0));fallback=False
        try:
            raw,_,_=sources.fetch(source['url']+'?'+urlencode({'search_query':query,'sortBy':'lastUpdatedDate','sortOrder':'descending','max_results':limit,'start':page}))
            feed=feedparser.parse(raw)
            if feed.bozo or not feed.version or (not feed.entries and str(feed.feed.get('opensearch_totalresults'))!='0'):raise ValueError('Invalid arXiv API feed')
            if any('/api/errors' in e.get('id','') for e in feed.entries):raise ValueError('arXiv returned an API error entry')
            more=page+limit if len(feed.entries)==limit and all(recent(e.get('updated')) for e in feed.entries) else None
            selected=feed.entries
        except Exception as exc:
            # Official daily feed is narrower than search; preserve the API failure and cursor.
            errors.append('arXiv API · '+error_kind(exc));fallback=True;more=page
            try:
                raw,_,_=sources.fetch('https://rss.arxiv.org/atom/cs.AI')
                feed=feedparser.parse(raw)
                if feed.bozo or not feed.version:raise ValueError('Invalid arXiv fallback feed')
            except Exception as fallback_error:
                errors.append('cs.AI 摘要补充 · '+error_kind(fallback_error))
                save_progress(source['id'],{**state,'offset':page,'status':'backlog','errors':errors,'last_page_at':store.now()})
                raise sources.PartialSourceError(counters[0],counters[1],'本次未取得论文材料；'+'；'.join(errors)) from fallback_error
            selected=[e for e in feed.entries if any(re.search(r'\b'+re.escape(t)+r'\w*',e.get('title',''),re.I) for t in terms)][:limit]
        for e in selected:
            if not recent(e.get('updated')):continue
            url=e.get('link') if fallback else e.get('id')
            if not url or urlsplit(url).hostname not in ('arxiv.org','export.arxiv.org') or not urlsplit(url).path.startswith('/abs/'):raise ValueError('Invalid arXiv article identity')
            url=url.replace('http://','https://');version=re.search(r'v\d+$',url)
            entries.append({'url':url,'title':' '.join(e.title.split()),'summary':' '.join(sources.plain_html(e.summary).split()),'type':'paper','version':version[0] if version else '',
                'published_at':None if fallback else e.get('published'),'materials':[material(url,sources.plain_html(e.summary),'abstract','论文摘要')],
                'metadata':{'primary':True,'change':'paper','gaps':['当前只有摘要，论文全文与同行评审状态未核实']+(['API 失败；仅补充 cs.AI 当日订阅中的相关标题，不代表检索与历史分页已恢复；订阅日期不作为论文发布日期'] if fallback else []),'acquisition':'official_cs_ai_feed' if fallback else 'arxiv_api'}})
    else:raise ValueError('Unsupported daily discovery mode')
    found,changed=counters
    saved={'watermark':state.get('watermark') or boundary,'last_page_at':store.now(),'status':'backlog' if more or errors or (mode=='index' and index_pending) else 'complete','errors':errors}
    if mode=='hub':saved['next_url']=more
    if mode in ('feed','index'):
        saved['pending']=more
        saved['seen_entries']=dict(list(seen_entries.items())[-500:])
        if mode=='index':saved.update(index_pending=index_pending,index_seen=list(index_seen) if more or index_pending else [])
        if cfg.get('recheck_body'):saved['rechecked']=list(rechecked) if more or (mode=='index' and index_pending) else []
    if mode=='qwen':saved.update(pending_ids=more,rechecked=qwen_visited)
    if mode=='github':saved['page']=more or 1
    if mode=='arxiv':saved['offset']=more or 0
    unfinished=bool(more or errors or (mode=='index' and index_pending))
    if not unfinished:saved['watermark']=started
    save_progress(source['id'],saved)
    if unfinished:raise sources.PartialSourceError(found,changed,'已保存材料；还有分页或失败待续跑。'+','.join(errors[:3]))
    return found,changed
