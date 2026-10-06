#!/usr/bin/env python3
"""Read-only scheduled MCP client; cache/checkpoint writes stay on the client."""
import argparse
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit
import httpx


class SyncError(RuntimeError):
    pass


def sync(endpoint, state_path, group='all', limit=50, client=None):
    state_path = Path(state_path)
    previous = json.loads(state_path.read_text()) if state_path.exists() else {}
    matching = previous.get('endpoint') == endpoint and previous.get('group') == group and previous.get('limit') == limit
    cursor = previous.get('cursor') if matching else None
    cached = dict(previous.get('items', {})) if matching else {}
    own_client = client is None
    if own_client:
        client = httpx.Client(timeout=90, follow_redirects=False,
                             trust_env=urlsplit(endpoint).hostname not in ('localhost','127.0.0.1','::1'))
    try:
        headers = {'Accept':'application/json, text/event-stream', 'DNT':'1'}
        token = os.getenv('FIELDTOFIT_READ_TOKEN', '')
        if token:headers['Authorization']='Bearer '+token
        def call(method, params):
            response=client.post(endpoint,headers=headers,json={'jsonrpc':'2.0','id':1,'method':method,'params':params})
            response.raise_for_status();data=response.json()
            if 'error' in data:raise SyncError(str(data['error']))
            return data['result']
        init=call('initialize',{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'fieldtofit-codex-daily-sync','version':'1'}})
        headers['MCP-Protocol-Version']=init['protocolVersion']
        initialized=client.post(endpoint,headers=headers,json={'jsonrpc':'2.0','method':'notifications/initialized'})
        if initialized.status_code!=202:raise SyncError('Initialization acknowledgement failed')
        changes, pages, full, seen = [], 0, cursor is None, set()
        while True:
            if cursor in seen:raise SyncError('Repeated pagination cursor; checkpoint unchanged')
            seen.add(cursor)
            args={'group':group,'limit':limit}
            if cursor:args['cursor']=cursor
            result=call('tools/call',{'name':'codex_updates','arguments':args})
            if result.get('isError'):
                if result.get('structuredContent',{}).get('code')=='snapshot_expired' and not full:
                    cursor=None;seen.clear();full=True;changes=[];pages=0;continue
                raise SyncError(str(result.get('structuredContent') or result.get('content')))
            data=result['structuredContent']
            if data['mode']=='full' and pages==0:cached={};full=True
            for event in data['items']:
                ident=event['object_id']
                if event['kind']=='removed':cached.pop(ident,None)
                else:
                    if event['item']['id']!=ident:raise SyncError('Mismatched item identity')
                    cached[ident]=event['item']
                changes.append(event)
            pages+=1
            if pages>1000:raise SyncError('Pagination limit exceeded; checkpoint unchanged')
            if data['has_more']:
                cursor=data['next_cursor'];continue
            if not data.get('resume_cursor'):raise SyncError('Missing completed checkpoint')
            state={'schema_version':'fieldtofit.codex-client.v1','endpoint':endpoint,'group':group,'limit':limit,
                   'cursor':data['resume_cursor'],'revision':data['revision'],'items':cached}
            # Commit cache and checkpoint together only after every page succeeds.
            state_path.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile('w',dir=state_path.parent,delete=False,encoding='utf-8') as out:
                os.chmod(out.name,0o600);json.dump(state,out,ensure_ascii=False);name=out.name
            os.replace(name,state_path)
            before=previous.get('items',{}) if matching else {}
            meaningful=[e for e in changes if (e['kind']=='removed' and e['object_id'] in before) or
                        (e['kind']!='removed' and e['item']!=before.get(e['object_id']))]
            # Full expiry recovery also removes old cached IDs absent from all pages.
            if full:
                present={e['object_id'] for e in meaningful}
                meaningful += [{'object_id':i,'kind':'removed'} for i in sorted(set(before)-set(cached)) if i not in present]
            return {'mode':'full' if full else 'delta','pages':pages,'cached':len(cached),
                    'revision':data['revision'],'topic_changed':data['topic_changed'],
                    'changes':meaningful,'checkpoint_saved':True}
    finally:
        if own_client:client.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--endpoint',default='https://fieldtofit.top/api/mcp/codex')
    parser.add_argument('--state',required=True)
    parser.add_argument('--group',choices=['all','codex','other_openai'],default='all')
    parser.add_argument('--limit',type=int,default=50)
    args=parser.parse_args()
    print(json.dumps(sync(args.endpoint,args.state,args.group,args.limit),ensure_ascii=False))


if __name__=='__main__':main()
