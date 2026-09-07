"""Behavioral acceptance checks for processing, evidence and task workflows."""
import json
from datetime import datetime, timezone

import pytest
from test_knowledge import client, seed, ADMIN
from backend.db import get_db
from backend.knowledge import store, processing, models, tasks


def fact(value, version='v1', **extra):
    return {'value':value,'source_url':'https://example.org/docs','status':'documented','version':version,**extra}


def test_source_refresh_retains_corrections_and_invalidates_version(client):
    rid=seed(version='v1',facts={'license':fact('MIT')},metadata={'editorial':{'human':'retained'}},summary_zh='已整理')
    store.save_discovery({'kind':'resource','canonical_url':'https://example.org/one','title':'PDF pipeline','version':'v1','summary':'updated source'})
    row=store.get_record(rid)
    assert row['summary_zh']=='已整理' and row['facts']['license']['value']=='MIT'
    assert row['metadata']['editorial']=={'human':'retained'}
    store.save_discovery({'kind':'resource','canonical_url':'https://example.org/one','title':'PDF pipeline','version':'v2'})
    row=store.get_record(rid)
    assert not row['facts'] and row['completeness']=='basic' and 'editorial' not in row['metadata']
    client.patch('/api/v1/admin/records/'+rid,json={'status':'withdrawn','reason':'Wrong identity'},headers=ADMIN)
    store.save_discovery({'kind':'resource','canonical_url':'https://example.org/one','title':'PDF pipeline','version':'v2'})
    assert store.get_record(rid) is None


def test_numeric_constraints_units_version_and_explicit_unknown(client):
    rid=seed(version='v1',facts={'hardware_vram_gb':fact(12,unit='GB',conditions='Quantized model, batch 1'),'deployment':fact('local')})
    record=store.get_record(rid)
    assert tasks.match_conditions(record,{'hardware_vram_gb':{'max':8,'unit':'GB'}})[0]['state']=='unmet'
    assert tasks.match_conditions(record,{'hardware_vram_gb':{'max':16,'unit':'GB'}})[0]['state']=='satisfied'
    assert tasks.match_conditions(record,{'deployment':'本地'})[0]['state']=='satisfied'
    record['facts']['hardware_vram_gb'].pop('conditions')
    assert tasks.match_conditions(record,{'hardware_vram_gb':{'max':16}})[0]['state']=='unknown'
    record['version']='v2'
    assert tasks.match_conditions(record,{'deployment':'local'})[0]['state']=='unknown'
    with pytest.raises(ValueError): tasks.match_conditions(store.get_record(rid),{'hardware_vram_gb':{'max':8,'unit':'TB'}})


def test_task_pack_is_specific_and_pages_candidates(client):
    for i in range(15):
        seed(suffix=f'pdf-{i}',version='v1',facts={'usage':fact('python extract.py input.pdf'),'license':fact('MIT')})
    one=client.post('/api/v1/task',json={'goal':'PDF','persona':'engineer','limit':10}).json
    two=client.post('/api/v1/task',json={'goal':'PDF','persona':'engineer','limit':10,'offset':10}).json
    assert one['total_candidates']==15 and len(two['candidates'])==5
    assert not {x['id'] for x in one['candidates']}&{x['id'] for x in two['candidates']}
    assert one['material_packets'][0]['steps'][0]['instruction']=='python extract.py input.pdf'
    graduate=client.post('/api/v1/task',json={'goal':'PDF','persona':'graduate'}).json
    assert one['deliverables']!=graduate['deliverables']
    assert one['material_packets'][0]['missing_materials']!=graduate['material_packets'][0]['missing_materials']
    exported=client.post('/api/v1/task/export',json={'goal':'PDF'}).text
    assert 'python extract.py input.pdf' in exported and 'https://example.org/docs' in exported


def test_task_negative_and_model_fallback(client,monkeypatch):
    seed(version='v1',facts={'deployment':fact('cloud',exhaustive=True)})
    packet=tasks.pack('PDF local',enhanced=True)
    assert packet['conclusion']=='known_candidates_unmet'
    assert packet['interpretation']['warning'] and packet['interpretation']['retrieval_mode']=='keywords_and_capability_tags'
    assert tasks.pack('nonexistent-speciality')['conclusion']=='not_found_in_scope'


def test_pdf_extraction_preserves_page_and_scan_limitations(client):
    from pypdf import PdfWriter
    from backend.knowledge.materials import extract
    import io
    writer=PdfWriter();writer.add_blank_page(width=100,height=100);writer.add_blank_page(width=100,height=100)
    buffer=io.BytesIO();writer.write(buffer)
    parts,_,info=extract(buffer.getvalue(),'application/pdf','https://example.org/paper.pdf')
    assert [p[0] for p in parts]==['Page 1','Page 2']
    assert info['unreadable_pages']==['Page 1','Page 2'] and info['coverage']=='excerpt'


def test_html_sections_and_explicit_relation(client,monkeypatch):
    from backend.knowledge.materials import retrieve
    from backend.knowledge import sources
    target=seed('Library',suffix='library')
    rid=seed('Paper',suffix='paper',kind='paper',version='v1')
    html=b'<html><nav>Skip this</nav><h1>Research question</h1><p>A sufficiently long description of the research question.</p><h2>Implementation</h2><p>The example uses an explicitly referenced <a href="/library">library</a>.</p></html>'
    monkeypatch.setattr(sources,'fetch',lambda *a,**kw:(html,'https://example.org/paper','text/html'))
    result=retrieve(rid);record=store.get_record(rid,include_body=True)
    assert len(result['evidence_ids'])==2
    assert record['relations'][0]['related_id']==target and record['relations'][0]['relation']=='related'
    assert all('Skip this' not in e['body'] for e in record['evidence'])
    assert record['completeness']=='basic'


def generated(eid,quote='The software is distributed under the MIT license.'):
    human={k:'来源描述' for k in ('what','changes','why','audience','limitations','next_step')}
    return {'title_zh':'PDF 工具','summary_zh':'一款有文档的工具','summary_en':'A documented tool','human':{'zh':human,'en':{k:'Source description' for k in human}},
            'facts':[{'key':'license','value':'MIT','evidence_id':eid,'quote':quote,'version':'v1'}],
            'citations':[{'evidence_id':eid,'quote':quote}],'importance':{'score':3,'reason_zh':'公开文档','reason_en':'Documented'},'research':{},'topics':['engineering']}


def test_organization_rejects_fabricated_citations_and_keeps_conflicts(client,monkeypatch):
    rid=seed(version='v1',facts={'license':fact('Apache-2.0')})
    eid=store.add_evidence(rid,'https://example.org/docs','README','The software is distributed under the MIT license.','License','v1','documented','full_text')
    monkeypatch.setattr(models,'generate_json',lambda *a,**k:(generated(eid,'This quotation does not exist in source material.'),{'model':'test','generated_at':store.now(),'ai_generated':True}))
    with pytest.raises(ValueError,match='quotation'): processing.organize(rid)
    assert store.get_record(rid)['summary_zh']==''
    monkeypatch.setattr(models,'generate_json',lambda *a,**k:(generated(eid),{'model':'test','generated_at':store.now(),'ai_generated':True}))
    processing.organize(rid);record=store.get_record(rid)
    assert record['facts']['license']['value']=='Apache-2.0' and record['facts']['license']['conflict']
    assert tasks.match_conditions(record,{'license':'apache-2.0'})[0]['state']=='unknown'
    assert record['metadata']['editorial']['review_status']=='ai_organized'
    conflict=record['conflicts'][0]
    result=client.post('/api/v1/admin/conflicts/'+conflict['id']+'/resolve',json={'choice':1,'reason':'Reviewed the license in cited document'},headers=ADMIN)
    assert result.status_code==200 and not store.get_record(rid)['conflicts']
    assert store.get_record(rid)['facts']['license']['value']=='MIT'


def test_jobs_retry_skips_completed_inputs(client,monkeypatch):
    rid=seed(version='v1')
    from backend.knowledge import materials
    calls=[]
    def retrieve(r):
        calls.append('material')
        store.add_evidence(r,'https://example.org/docs','README','The software is distributed under the MIT license.','License','v1','documented','full_text')
    monkeypatch.setattr(materials,'retrieve',retrieve)
    def generate(*a,**k):
        calls.append('organize')
        return generated(store.get_record(rid)['evidence'][0]['id']),{'model':'test','generated_at':store.now(),'ai_generated':True}
    monkeypatch.setattr(models,'generate_json',generate)
    processing.run_processing(record_id=rid)
    processing.run_processing(record_id=rid)
    assert calls==['material','organize']
    store.add_evidence(rid,'https://example.org/docs','README','A changed license section is explicitly recorded.','Change','v1','documented','excerpt')
    processing.run_processing(record_id=rid)
    assert calls==['material','organize','organize']


def test_read_scopes_cursors_and_tombstone(client):
    a=seed(suffix='follow',topics=['engineering']);b=seed(suffix='unfollow',topics=['business'])
    result=client.get('/api/v1/changes',query_string={'record_ids':a}).json
    assert {r['record_id'] for r in result['items']}=={a}
    empty=client.get('/api/v1/changes',query_string={'record_ids':''}).json
    assert empty['items']==[]
    by_topic=client.get('/api/v1/changes',query_string={'topics':'business'}).json
    assert {r['record_id'] for r in by_topic['items']}=={b}
    client.patch('/api/v1/admin/records/'+a,json={'status':'withdrawn','reason':'Withdrawn'},headers=ADMIN)
    result=client.get('/api/v1/changes',query_string={'record_ids':a}).json
    assert all('title' not in r['snapshot'] for r in result['items'])


def test_grouping_reversible_no_duplicate_search_and_preserves_links(client):
    a=seed('Same release',suffix='primary',kind='event',version='v1');b=seed('Same release',suffix='report',kind='event',version='v1')
    response=client.post('/api/v1/admin/merge',json={'target_id':a,'record_ids':[b],'reason':'Same official version announcement'},headers=ADMIN)
    assert response.status_code==200
    assert store.search_records(q='Same release')['total']==1
    assert store.get_record(b) and store.get_record(a)['grouped_sources'][0]['id']==b
    assert client.post('/api/v1/admin/actions/'+response.json['action_id']+'/undo',json={'reason':'Reports describe different changes'},headers=ADMIN).status_code==200
    assert store.search_records(q='Same release')['total']==2
    c=seed('Second release',suffix='second',kind='event',version='v2')
    assert client.post('/api/v1/admin/merge',json={'target_id':a,'record_ids':[c],'reason':'wrong'},headers=ADMIN).status_code==400


def test_brief_removes_withdrawn_sources(client,monkeypatch):
    day=datetime.now(timezone.utc).date().isoformat()
    rid=seed(kind='event',published_at=day,version='v1')
    eid=store.add_evidence(rid,'https://example.org/docs','News','The software is distributed under the MIT license.','Announcement','v1','official_claim','excerpt')
    monkeypatch.setattr(models,'generate_json',lambda *a,**k:(generated(eid),{'model':'test','generated_at':store.now(),'ai_generated':True}))
    processing.organize(rid);processing.build_brief(day)
    assert client.get('/api/v1/briefs').json['items'][0]['items'][0]['id']==rid
    client.patch('/api/v1/admin/records/'+rid,json={'status':'withdrawn','reason':'Incorrect'},headers=ADMIN)
    assert client.get('/api/v1/briefs').json['items'][0]['items']==[]


def test_model_configuration_and_admin_access(client,monkeypatch):
    assert client.get('/api/v1/admin/model').status_code==401
    for name in ('METIS_FIRST_API_KEY','METIS_SECOND_API_KEY'):
        monkeypatch.setenv(name,'private-test-credential')
        response=client.patch('/api/v1/admin/model',json={'model':name,'key_env':name,'base_url':'https://example.org/v1','enabled':True},headers=ADMIN)
        assert response.status_code==200 and response.json['credential_configured']
        assert 'private-test-credential' not in response.text
    assert client.patch('/api/v1/admin/model',json={'key_env':'TURSO_AUTH_TOKEN'},headers=ADMIN).status_code==400
    assert client.get('/api/v1/account').json['registration_enabled'] is False


def test_sources_feedback_and_experimental_comparison(client):
    response=client.post('/api/v1/admin/sources',json={'name':'Official','url':'https://example.org/feed','category':'official','adapter':'rss','config':{'owner':'Team'}},headers=ADMIN)
    assert response.status_code==201
    sid=response.json['id']
    assert client.patch('/api/v1/admin/sources/'+sid,json={'interval_days':2},headers=ADMIN).status_code==400
    fid=client.post('/api/v1/feedback',json={'category':'use_case','content':'Need a real workflow'}).json['id']
    assert client.patch('/api/v1/admin/feedback/'+str(fid),json={'status':'reviewing','resolution':'Reproduce the task'},headers=ADMIN).status_code==200
    assert client.get('/api/v1/admin/records',headers=ADMIN).json['feedback'][0]['handling_status']=='reviewing'
    a=seed(kind='paper',suffix='first',facts={'dataset':fact('A'),'metric':fact('accuracy')})
    b=seed(kind='paper',suffix='second',facts={'dataset':fact('B'),'metric':fact('accuracy')})
    compared=client.post('/api/v1/compare',json={'ids':[a,b]}).json['research_comparison']
    assert compared['comparable'] is False and 'dataset' in compared['different_settings'] and 'split' in compared['missing_settings']


def test_current_gpt_batch_bootstraps_without_provider(client):
    from examples.editorial.load import run
    result=run()
    assert len(result['items'])==6
    assert all(x['mode']=='assistant_batch_import' for x in result['items'])
    assert store.get_record('80bada030a39c91e2923059a')['published_at'] is None
    row=store.get_record(result['items'][0]['id'])
    assert row['metadata']['editorial']['review_status']=='ai_organized'
    with get_db() as db:
        assert db.execute("SELECT status FROM knowledge_jobs WHERE record_id=? AND stage='organize'",(row['id'],)).fetchone()[0]=='success'
    assert len(run()['items'])==6


def test_relation_changes_emit_once_for_both_followers(client):
    a=seed(suffix='a');b=seed(suffix='b')
    before=store.changes()['latest_cursor']
    store.relate(a,b,'related','https://example.org/docs','Explicit source link')
    changed=store.changes(after=before)
    assert {r['record_id'] for r in changed['items']}=={a,b}
    store.relate(a,b,'related','https://example.org/docs','Explicit source link')
    assert not store.changes(after=changed['latest_cursor'])['items']


def test_hub_pages_resume_backlog_and_recheck_head(client,monkeypatch):
    from backend.knowledge import sources,paging
    src={'id':'hf-models','adapter':'huggingface','url':'https://huggingface.co/api/models','config':{'limit':1,'pages_per_day':1,'history_days':30}}
    stamp=datetime.now(timezone.utc).isoformat();calls=[]
    def fetch(url,**kwargs):
        calls.append(url)
        older='cursor=older' in url
        entries=[{'id':'team/'+('older' if older else 'head'),'lastModified':stamp}]
        return json.dumps(entries).encode(),url,'application/json',{} if older else {'link':'<https://huggingface.co/api/models?cursor=older>; rel="next"'}
    monkeypatch.setattr(sources,'fetch',fetch)
    monkeypatch.setattr(sources,'ingest_huggingface',lambda s,e:(len(e),len(e)))
    with pytest.raises(sources.PartialSourceError):paging.collect_pages(src)
    assert paging.progress(src['id'])['status']=='backlog'
    src['config']['pages_per_day']=2
    assert paging.collect_pages(src)==(2,2)
    assert 'cursor=older' not in calls[1] and 'cursor=older' in calls[2]
    assert paging.progress(src['id'])['status']=='complete'


def test_two_generation_protocols_and_incomplete_response(client,monkeypatch):
    from types import SimpleNamespace
    import openai
    calls=[]
    def response(**kwargs):calls.append(kwargs);return SimpleNamespace(status='completed',output_text='{"ok":true}')
    def chat_create(**kwargs):calls.append(kwargs);return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok":true}'))])
    class Fake:
        responses=SimpleNamespace(create=response)
        chat=SimpleNamespace(completions=SimpleNamespace(create=chat_create))
        def __init__(self,**kwargs):self.http=kwargs['http_client']
        def __enter__(self):return self
        def __exit__(self,*args):self.http.close()
    monkeypatch.setattr(openai,'OpenAI',Fake)
    monkeypatch.setenv('METIS_TEST_API_KEY','not-a-real-secret')
    for style in ['responses','chat_completions']:
        models.configure({'enabled':True,'key_env':'METIS_TEST_API_KEY','model':'gpt-6-astra','base_url':'https://example.org/v1','api_style':style})
        assert models.generate_json('Return JSON',{'task':'test'})[0]=={'ok':True}
    assert calls[0]['store'] is False and 'max_output_tokens' in calls[0] and 'temperature' not in calls[0]
    assert 'messages' in calls[1]
    Fake.responses=SimpleNamespace(create=lambda **kwargs:SimpleNamespace(status='incomplete',output_text=''))
    models.configure({'api_style':'responses'})
    with pytest.raises(models.ModelUnavailable,match='incomplete'):models.generate_json('Return JSON',{})


def test_runtime_checks_bind_resource_and_actual_version(client,monkeypatch):
    from backend.knowledge import verification
    from types import SimpleNamespace
    rid=store.save_record({'kind':'resource','title':'pypdf','canonical_url':'https://github.com/py-pdf/pypdf','version':'999'})[0]
    monkeypatch.setattr(verification.subprocess,'run',lambda *a,**kw:SimpleNamespace(returncode=0,stdout='{"pypdf_version":"6.17.0"}',stderr=''))
    result=verification.run_check('engineer-pdf',rid)
    assert result['result']=='failed'
    assert store.get_record(rid)['verifications'][0]['version']=='6.17.0'
    with pytest.raises(ValueError,match='declared source'):verification.run_check('engineer-pdf',seed())


def test_task_subject_excludes_incidental_pdf_urls_and_locality(client):
    wanted=seed('PDF text extraction',suffix='pdf')
    seed('Local database manager',suffix='db',summary='Manage local databases in Chinese')
    seed('Robotic policy paper',suffix='robot',kind='paper',summary='Locally run robotic policies',metadata={'document_url':'https://example.org/paper.pdf'})
    assert [r['id'] for r in tasks.pack('本地中文 PDF 提取')['candidates']]==[wanted]
    assert store.search_records(q='pdf')['total']==1


def test_new_provider_does_not_reuse_legacy_provider_secret(client,monkeypatch):
    monkeypatch.setenv('MINIMAX_API_KEY','legacy-credential')
    monkeypatch.delenv('METIS_MODEL_API_KEY',raising=False)
    monkeypatch.setenv('METIS_MODEL_BASE_URL','https://api.openai.com/v1')
    cfg=models.configuration()
    assert cfg['key_env']=='METIS_MODEL_API_KEY' and not cfg['credential_configured'] and not cfg['enabled']


def test_explicit_document_subject_excludes_generic_extraction(client):
    wanted=seed('PDF text extraction',suffix='pdf')
    seed('网页数据提取',suffix='web',summary='TypeScript HTML extractor',summary_zh='从网页提取数据')
    assert [r['id'] for r in tasks.pack('本地中文 PDF 提取')['candidates']]==[wanted]
