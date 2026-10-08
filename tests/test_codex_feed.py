"""Real reviewed lifecycle + checkpoint races, isolated from production."""
import copy
import json
from datetime import datetime, timezone
import pytest
from test_knowledge import client, MCP
from test_content_workspace import call, migrate, publish, make
from backend.db import get_db
from backend.knowledge import codex_feed as feed, platform_news as news


def rpc(client, args=None, method='tools/call', name='codex_updates', endpoint='/api/mcp/codex'):
    params={'name':name,'arguments':args or {}} if method=='tools/call' else {}
    response=client.post(endpoint,headers=MCP,json={'jsonrpc':'2.0','id':1,'method':method,'params':params})
    assert response.status_code==200, response.json
    return response.json['result']


def read(client, **args):
    result=rpc(client,args);assert not result['isError'],result
    return result['structuredContent']


def edit(client, ident, change):
    cur=call(client,'/content/news/'+ident,method='get').json
    change(cur['draft'])
    saved=call(client,'/content/news/'+ident,cur,'patch');assert saved.status_code==200,saved.json
    return publish(client,'news',ident)


def new_draft(client):
    ident,_=make(client,'news');cur=call(client,'/content/news/'+ident,method='get').json
    clone=copy.deepcopy(next(i for i in news.news()['items'] if i['id']=='D-79'))
    clone.update(id=ident,state='published',event_date=None,source_published_at='2026-10-05',highlight=False)
    clone.pop('publication',None)
    url='https://github.com/openai/codex/releases/tag/isolated-backfill'
    clone['sources'].append({'id':'isolated','title':'Isolated official release','url':url,'coverage':'link_only'})
    clone['codex_28_days'].update(event_key=url,announced_at=None,date_precision='source_date',timestamp_basis='source_date')
    saved=call(client,'/content/news/'+ident,{'draft_version':cur['draft_version'],'draft':clone},'patch')
    assert saved.status_code==200,saved.json
    return ident


def test_full_same_publication_single_tool_and_empty_delta(client):
    public=client.get('/api/v1/platform/news').json
    first=read(client)
    assert first['mode']=='full' and first['total']==16 and first['topic']==public['codex_progress']
    assert first['publication_revision']==public['revision']
    assert {e['object_id']:e['item'] for e in first['items']}=={i['id']:i for i in public['items'] if i.get('codex_28_days')}
    assert next(e['item'] for e in first['items'] if e['object_id']=='D-78')['codex_28_days']['source_posts'][0]['avatar']
    delta=read(client,cursor=first['resume_cursor'])
    assert delta['mode']=='delta' and delta['items']==[] and delta['revision']==first['revision']
    assert len(rpc(client,method='tools/list')['tools'])==1
    assert len(rpc(client,method='tools/list',endpoint='/api/mcp/curated')['tools'])==18
    assert rpc(client,name='curated_news')['isError']
    assert rpc(client,endpoint='/api/mcp/curated')['isError']
    assert rpc(client,method='initialize')['serverInfo']['name']=='fieldtofit-codex'


def test_private_edits_unrelated_news_and_topic_only_corrections(client):
    migrate(client);first=read(client)
    cur=call(client,'/content/news/D-78',method='get').json
    cur['draft']['codex_28_days']['private_note']='SECRET'
    assert call(client,'/content/news/D-78',cur,'patch').status_code==200
    assert read(client,cursor=first['resume_cursor'])['items']==[]
    edit(client,'D-01',lambda i:i.update(title=i['title']+' unrelated correction'))
    empty=read(client,cursor=first['resume_cursor'])
    assert empty['items']==[] and empty['revision']==first['revision'] and empty['publication_revision']!=first['publication_revision']
    edit(client,'D-78',lambda i:i['codex_28_days'].update(overview_zh='已审核摘要修正'))
    changed=read(client,cursor=empty['resume_cursor'])
    assert len(changed['items'])==1 and changed['items'][0]['kind']=='updated'
    assert changed['items'][0]['item']['codex_28_days']['date']=='2026-10-06'
    assert 'SECRET' not in json.dumps(changed)
    repeated=read(client,cursor=empty['resume_cursor'])
    assert repeated['items']==changed['items']
    assert read(client,cursor=changed['resume_cursor'])['items']==[]


def test_backfill_group_move_removal_and_withdrawal(client):
    migrate(client);main=read(client,group='codex');assert main['total']==7
    ident=new_draft(client);publish(client,'news',ident)
    new=read(client,group='codex',cursor=main['resume_cursor'])
    assert new['total']==1 and new['items'][0]['object_id']==ident
    assert new['items'][0]['item']['codex_28_days']['date']=='2026-10-05'
    edit(client,ident,lambda i:i['codex_28_days'].update(group='other_openai'))
    removed=read(client,group='codex',cursor=new['resume_cursor'])['items'][0]
    assert removed['kind']=='removed' and 'item' not in removed
    whole=read(client)
    cur=call(client,'/content/news/D-78',method='get').json
    assert call(client,'/content/news/D-78/withdraw',{'draft_version':cur['draft_version'],'reason':'Isolated removal'}).status_code==200
    removed=read(client,cursor=whole['resume_cursor'])['items'][0]
    assert removed['object_id']=='D-78' and removed['kind']=='removed' and 'item' not in removed
    before=read(client)
    edit(client,'D-79',lambda i:i.pop('codex_28_days'))
    assert read(client,cursor=before['resume_cursor'])['items'][0]['kind']=='removed'


def test_initial_baseline_publication_race_and_page_permission_recheck(client,monkeypatch):
    migrate(client);ident=new_draft(client);original=feed.u._snapshot
    def race(db,kind,query,data):
        monkeypatch.setattr(feed.u,'_snapshot',original)
        publish(client,'news',ident)
        return original(db,kind,query,data)
    monkeypatch.setattr(feed.u,'_snapshot',race)
    first=read(client)
    assert ident not in {e['object_id'] for e in first['items']}
    assert read(client,cursor=first['resume_cursor'])['items'][0]['object_id']==ident
    page=read(client,limit=1);assert page['has_more'] and page['resume_cursor'] is None
    removed_id='D-78' if page['items'][0]['object_id']!='D-78' else 'D-79'
    cur=call(client,'/content/news/'+removed_id,method='get').json
    call(client,'/content/news/'+removed_id+'/withdraw',{'draft_version':cur['draft_version'],'reason':'Withdraw during pages'})
    events=[]
    while page['has_more']:
        page=read(client,limit=1,cursor=page['next_cursor']);events+=page['items']
    tomb=next(e for e in events if e['object_id']==removed_id)
    assert tomb['kind']=='removed' and 'item' not in tomb


@pytest.mark.parametrize('args',[{'limit':0},{'limit':101},{'limit':True},{'group':'wrong'},{'cursor':'bad'},{'unknown':1}])
def test_invalid_arguments(client,args):
    assert rpc(client,args)['isError']


def test_scope_expiry_recovery_and_transport_permissions(client,monkeypatch):
    first=read(client,limit=1)
    assert rpc(client,{'group':'codex','limit':1,'cursor':first['next_cursor']})['structuredContent']['code']=='cursor_scope_mismatch'
    with get_db() as db:db.execute('UPDATE knowledge_read_snapshots SET expires_at=?',('2000-01-01',))
    assert rpc(client,{'limit':1,'cursor':first['next_cursor']})['structuredContent']['code']=='snapshot_expired'
    assert read(client)['mode']=='full'
    assert client.get('/api/mcp/codex').status_code==405
    assert client.post('/api/mcp/codex',headers={**MCP,'Origin':'https://bad.invalid'},json={}).status_code==403
    monkeypatch.setenv('FIELDTOFIT_READ_TOKEN','isolated-token')
    assert client.post('/api/mcp/codex',headers=MCP,json={}).status_code==401
    assert client.post('/api/mcp/codex',headers={**MCP,'Authorization':'Bearer isolated-token'},json={'jsonrpc':'2.0','id':1,'method':'ping'}).status_code==200


def test_no_script_calendar_uses_native_disclosure(client):
    html=client.get('/for-you').text
    assert '<details class="codex-calendar-fold">' in html and '10-12 — 11-01' in html
    assert 'https://fieldtofit.top/api/mcp/codex' in html


def test_reviewed_merge_and_undo_reconcile_cached_ids(client):
    from backend.knowledge import stewardship as s
    from test_stewardship import ready
    migrate(client);before=read(client)
    data,preview=ready({'action':'merge','source':'D-79','target':'D-01','reason':'Isolated identity reconciliation'})
    result=s.apply({**data,'review_token':preview['review_token'],'confirmed':True})
    delta=read(client,cursor=before['resume_cursor'])
    assert any(e['object_id']=='D-79' and e['kind']=='removed' and 'item' not in e for e in delta['items'])
    undo={'action':'undo','source':'D-79','target':'D-01','merge_id':result['id'],'restore_target':True,'reason':'Isolated reversal'}
    preview=s.preview(undo);assert preview['ready'],preview
    s.apply({**undo,'review_token':preview['review_token'],'confirmed':True})
    assert any(e['object_id']=='D-79' and e['kind']=='added' for e in read(client,cursor=delta['resume_cursor'])['items'])
