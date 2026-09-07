"""Bounded source pagination with persisted backlog and overlapping daily head checks."""
import json
import re
import time
from datetime import datetime, timezone, timedelta
from urllib.parse import quote, urlencode, urlsplit

import feedparser
from backend.db import get_db
from backend.knowledge import store


def progress(source_id):
    with get_db() as db:
        row=db.execute('SELECT state FROM knowledge_source_progress WHERE source_id=?',(source_id,)).fetchone()
    return store.decode(row['state'],{}) if row else {}


def save_progress(sid,state):
    with get_db() as db:
        db.execute('INSERT INTO knowledge_source_progress VALUES(?,?,?) ON CONFLICT(source_id) DO UPDATE SET state=excluded.state,updated_at=excluded.updated_at',(sid,store.encode(state),store.now()))


def collect_pages(source):
    from backend.knowledge.sources import fetch, ingest_arxiv, ingest_huggingface, ingest_openreview, PartialSourceError
    adapter=source['adapter']; cfg=source['config']; state=progress(source['id'])
    size=min(max(int(cfg.get('limit',100)),1),100)
    pages=min(max(int(cfg.get('pages_per_day',5)),1),20)
    offset=int(state.get('offset',0)); continuation=state.get('next_url')
    boundary=state.get('watermark') or (datetime.now(timezone.utc)-timedelta(days=int(cfg.get('history_days',30)))).isoformat()
    def timestamp(value):
        return datetime.fromisoformat(value.replace('Z','+00:00')).astimezone(timezone.utc).isoformat()
    boundary=timestamp(boundary)
    newest=state.get('newest') or boundary; found=changed=0; complete=False
    # Fetch the head before resuming an older page so newly published entries remain visible.
    positions=[0] if offset or continuation else []
    for number in range(pages):
        head=bool(positions); current=positions.pop(0) if head else offset
        if adapter=='arxiv':
            categories=' OR '.join('cat:'+c for c in cfg.get('categories',['cs.AI','cs.LG','cs.CL','cs.CV','cs.RO','stat.ML']))
            query={'search_query':categories,'sortBy':'lastUpdatedDate','sortOrder':'descending','max_results':size,'start':current}
            raw=fetch(source['url']+'?'+urlencode(query))[0]; feed=feedparser.parse(raw); entries=feed.entries
            dates=[entry.get('updated') or entry.get('published') for entry in entries]
            dates=[d for d in dates if d]
            if entries: a,b=ingest_arxiv(source,raw)
            else: a=b=0
            total=int(feed.feed.get('opensearch_totalresults',current+len(entries)))
            next_url=None; exhausted=not entries or current+len(entries)>=total
        elif adapter=='huggingface':
            url=source['url']+'?'+urlencode({'sort':'lastModified','direction':-1,'limit':size,'full':'true'}) if head or not continuation else continuation
            if urlsplit(url).hostname!=urlsplit(source['url']).hostname: raise ValueError('Pagination changed source host')
            raw,_,_,headers=fetch(url,with_headers=True); entries=json.loads(raw)
            if not isinstance(entries,list): raise ValueError('Hub did not return a resource list')
            a,b=ingest_huggingface(source,entries)
            dates=[e.get('lastModified') for e in entries if e.get('lastModified')]
            match=re.search(r'<([^>]+)>;\s*rel="?next"?',headers.get('link',''))
            next_url=match.group(1) if match else None; exhausted=not next_url
        else:
            url=source['url']+'?'+urlencode({'content.venueid':cfg['venue'],'limit':size,'offset':current,'sort':'tmdate:desc'})
            raw=fetch(url)[0]; payload=json.loads(raw); entries=payload.get('notes',[])
            a,b=ingest_openreview(source,payload)
            dates=[datetime.fromtimestamp(e.get('tmdate',e.get('mdate',0))/1000,timezone.utc).isoformat() for e in entries]
            next_url=None; exhausted=not entries or current+len(entries)>=int(payload.get('count',current+len(entries)+1)) or len(entries)<size
        found+=a;changed+=b
        dates=[timestamp(d) for d in dates]
        newest=max([timestamp(newest),*dates])
        reached=bool(dates) and min(dates)<=boundary
        if head:
            # The head check does not advance or erase a previously saved backlog cursor.
            if exhausted or reached:
                complete=True; break
            continue
        offset=current+len(entries); continuation=next_url
        if exhausted or reached:
            complete=True
        state={'offset':0 if complete else offset,'next_url':None if complete else continuation,
               'watermark':newest if complete else boundary,'newest':newest,'status':'complete' if complete else 'backlog',
               'coverage_start':boundary,'last_page_at':store.now()}
        save_progress(source['id'],state)
        if complete: break
        if adapter=='arxiv': time.sleep(3)
    if complete:
        save_progress(source['id'],{**state,'offset':0,'next_url':None,'watermark':newest,'newest':newest,'status':'complete'})
    else:
        raise PartialSourceError(found,changed,'More source pages remain; saved progress will resume in the next daily cycle')
    return found,changed
