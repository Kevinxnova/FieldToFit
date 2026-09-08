"""Operational acceptance: backlog, review pagination, exports and transaction failures."""
import sqlite3

import pytest

from test_knowledge import client, seed, ADMIN, MCP
from backend.knowledge import store, processing, operations, editorial


def test_review_filters_before_paging_and_admin_scope(client):
    for i in range(205):
        seed('Queue '+str(i), suffix='queue'+str(i), status='withdrawn' if i==0 else 'published')
    page=client.get('/api/v1/admin/records?status=withdrawn',headers=ADMIN).json
    assert page['total']==1 and page['records'][0]['title']=='Queue 0'
    first=client.get('/api/v1/admin/records?need=missing_evidence&limit=100',headers=ADMIN).json
    second=client.get('/api/v1/admin/records?need=missing_evidence&limit=100&offset=100',headers=ADMIN).json
    assert first['total']==205 and second['next_offset']==200
    assert not {r['id'] for r in first['records']} & {r['id'] for r in second['records']}
    assert client.get('/api/v1/admin/records?need=invalid',headers=ADMIN).status_code==400
    assert client.get('/api/v1/admin/operations').status_code==401


def test_processing_reports_unfinished_work_and_daily_dates(client,monkeypatch):
    for i in range(3): seed('Queue '+str(i),suffix='job'+str(i))
    from backend.knowledge import materials
    monkeypatch.setattr(materials,'retrieve',lambda rid:None)
    def organize(rid):
        r=store.get_record(rid);r['metadata']['organized_at']=store.now();store.save_record(r,record_id=rid)
    monkeypatch.setattr(processing,'organize',organize)
    result=processing.run_processing(limit=1)
    assert result['status']=='partial' and result['processed_records']==1 and result['remaining_records']==2
    result=processing.run_processing(limit=10)
    assert result['status']=='success' and result['remaining_records']==0
    for _ in range(3):
        with operations.track_run('daily') as result: result['status']='success'
    with pytest.raises(RuntimeError):
        with operations.track_run('daily'): raise RuntimeError('Simulated worker failure')
    snapshot=client.get('/api/v1/admin/operations',headers=ADMIN).json
    assert snapshot['organization_pending']==0 and snapshot['organized_last_day']==3
    assert len(snapshot['successful_daily_dates_utc'])==1
    assert snapshot['runs'][0]['status']=='error'
    assert snapshot['publication_to_collection']['p95_days'] is None
    assert snapshot['collection_to_organization']['sample_count']==3


def test_task_filter_and_complete_research_export(client,monkeypatch):
    from backend.knowledge import models
    rid=seed('Document Skill',suffix='filtered',object_type='skill',metadata={'capability_tags':['documents']})
    seed('Document tool',suffix='excluded',object_type='tool')
    args={'goal':'Document','object_type':'skill','capability':'documents'}
    packet=client.post('/api/v1/task',json=args).json
    assert [r['id'] for r in packet['candidates']]==[rid] and packet['filters']['capability']=='documents'
    assert 'documents' in client.post('/api/v1/task/export',json=args).text
    assert client.post('/api/v1/task',json={**args,'object_type':{}}).status_code==400
    mcp=client.post('/api/mcp',json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'task_context','arguments':args}},headers=MCP).json
    assert mcp['result']['structuredContent']['filters']==packet['filters']
    papers=[seed('Study '+str(i),suffix='study'+str(i),kind='paper',object_type='paper') for i in range(2)]
    quote='The authors report results under different evaluation conditions.'
    evidence=store.add_evidence(papers[0],'https://example.com/paper','Original paper',quote,'page 2','v1',coverage='full_text')
    def generate(*args,**kwargs):
        return {'sections':[{'title':'Discussion','points':[{'text':'Compare evaluation conditions','record_id':papers[0],'evidence_id':evidence,'quote':quote}]}], 'reading_order':[papers[1],papers[1]]},{'ai_generated':True}
    monkeypatch.setattr(models,'generate_json',generate)
    result=client.post('/api/v1/research',json={'goal':'Study','ids':papers,'enhanced':True}).json
    assert result['reading_order']==[papers[1],papers[0]]
    text=result['markdown']
    for value in ['Discussion','Compare evaluation conditions',quote,'page 2','not_directly_comparable','BibTeX','https://example.com/paper']:
        assert value in text


def test_daily_retry_does_not_hide_failed_sources(client,monkeypatch):
    from backend.knowledge import daily,sources,verification
    monkeypatch.setattr(sources,'run_daily',lambda:{'status':'success','results':[]})
    monkeypatch.setattr(processing,'run_processing',lambda **kwargs:{'status':'success'})
    monkeypatch.setattr(processing,'build_brief',lambda:{'items':[]})
    monkeypatch.setattr(verification,'run_due_checks',lambda:[])
    # An empty source run can mean sources were skipped after a same-day failure.
    result=daily.run()
    assert result['status']=='partial' and result['unhealthy_sources']
    assert not operations.snapshot()['successful_daily_dates_utc']


def test_remote_editorial_failure_rolls_back_without_partial_group(client,monkeypatch):
    """A simulated Hrana transport executes real SQLite SQL with stream transactions."""
    import backend.db as database
    from backend import config
    primary=seed('Primary',suffix='primary')
    other=seed('Other',suffix='other')
    streams={}; serial=0; fail=True; sqls=[]
    def post(self,payload):
        nonlocal serial,fail
        baton=payload.get('baton')
        conn=streams.pop(baton) if baton else sqlite3.connect(config.DB_PATH,isolation_level=None)
        results=[]; closed=False
        for req in payload['requests']:
            if req['type']=='close':
                conn.close();closed=True;results.append({'type':'ok','response':{'type':'close'}});continue
            sql=req['stmt']['sql'];sqls.append(sql)
            try:
                if fail and sql.startswith('INSERT INTO knowledge_changes'):
                    fail=False;raise sqlite3.OperationalError('Injected history write failure')
                params=[None if p['type']=='null' else int(p['value']) if p['type']=='integer' else p['value'] for p in req['stmt'].get('args',[])]
                cur=conn.execute(sql,params)
                rows=cur.fetchall()
                results.append({'type':'ok','response':{'type':'execute','result':{
                    'cols':[{'name':d[0]} for d in (cur.description or [])],
                    'rows':[[{'type':'null'} if v is None else {'type':'integer','value':str(v)} if isinstance(v,int) else {'type':'text','value':v} for v in row] for row in rows],
                    'affected_row_count':cur.rowcount,'last_insert_rowid':str(cur.lastrowid)}}})
            except sqlite3.Error as exc:
                results.append({'type':'error','error':{'message':str(exc)}})
        serial+=1; baton=None if closed else str(serial)
        if baton:streams[baton]=conn
        return {'baton':baton,'base_url':None,'results':results}
    monkeypatch.setattr(database,'TURSO_URL','https://test.turso.io')
    monkeypatch.setattr(database,'TURSO_TOKEN','test-token')
    monkeypatch.setattr(database.TursoConnection,'_post',post)
    with pytest.raises(RuntimeError,match='Injected'):
        editorial.merge(primary,[other],'Test source evidence')
    assert 'COMMIT' not in sqls and not streams
    assert not store.get_record(other)['metadata'].get('merged_into')
    assert not editorial.review_queue()['actions']
    success=editorial.merge(primary,[other],'Test source evidence')
    assert store.get_record(other)['metadata']['merged_into']==primary
    editorial.undo(success['action_id'],'Grouping is incorrect')
    assert not store.get_record(other)['metadata'].get('merged_into')
    assert not streams


@pytest.mark.parametrize('response',[
    {'baton':None,'results':[{'type':'ok','response':{'result':{}}}]},
    {'baton':'stream','base_url':'https://attacker.example','results':[{'type':'ok','response':{'result':{}}}]},
])
def test_remote_expired_or_redirected_transaction_never_reopens(monkeypatch,response):
    from backend.db import TursoConnection
    calls=[]
    def post(self,payload): calls.append(payload);return response
    monkeypatch.setattr(TursoConnection,'_post',post)
    conn=TursoConnection()
    with pytest.raises(RuntimeError):conn.begin()
    with pytest.raises(RuntimeError):conn.execute('INSERT INTO records VALUES (1)')
    assert len(calls)==1
