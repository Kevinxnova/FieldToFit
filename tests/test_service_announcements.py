"""Entry identity/date precision, historical baseline, partial runs and retries."""
import json
from datetime import date,timedelta
import pytest
from test_knowledge import client
from backend.db import get_db
from backend.knowledge import source_catalog,service_announcements as s,discovery,store
from backend.knowledge.paging import progress


def source(prefix):return next(x for x in source_catalog.definitions() if x['id']=='daily-'+prefix+'-announcements')


def table(day,body='Served third-party model',model='vendor/model-v1'):
    return '<h1>Updates</h1><h4 id="beijing">华北2（北京）</h4><table><tr><th>模型类型</th><th>时间</th><th>模型ID</th><th>功能说明</th></tr><tr><td>文本</td><td>'+day+'</td><td><code>'+model+'</code></td><td>'+body+'</td></tr></table>'


def test_twelve_sources_coverage_and_shell_rejected(client):
    services=[x for x in source_catalog.definitions() if x['config']['mode']=='service']
    assert len(services)==12
    assert len({x['url'] for x in services})==12 and all(x['config']['limit']==5 for x in services)
    registry=source_catalog.registry();byte=next(x for x in registry['tracked'] if x['id']=='bytedance')
    assert len([x for x in byte['channels'] if x['mode']=='service'])==5
    assert any('Android' in x for x in byte['planned'])
    for x in services:
        with pytest.raises((ValueError,KeyError,TypeError)):s.parse(x,'<script>loading</script>')


def test_baseline_repeat_body_correction_and_date_preservation(client,monkeypatch):
    from backend.knowledge import sources
    src=source('bailian-models');day=(date.today()-timedelta(days=3)).isoformat();body=table(day)
    monkeypatch.setattr(sources,'fetch',lambda *a,**k:(body,src['url'],'text/html'))
    assert s.collect(src)==(1,1);assert s.collect(src)==(0,0)
    with get_db() as db:
        old=dict(db.execute('SELECT * FROM fieldtofit_discoveries').fetchone());meta=store.decode(old['metadata'],{})
        assert meta['baseline'] and meta['platform']=='百炼' and old['published_at']==day
        assert meta['fields']['模型ID']=='vendor/model-v1' and '平台提供' in meta['service_role']
        assert meta['models']==['vendor/model-v1']
    body=table(day,'Corrected regional service scope')
    assert s.collect(src)==(1,1)
    with get_db() as db:
        new=dict(db.execute('SELECT * FROM fieldtofit_discoveries').fetchone())
        assert new['id']==old['id'] and not store.decode(new['metadata'],{})['baseline']
        assert db.execute('SELECT count(*) FROM fieldtofit_discovery_versions').fetchone()[0]==1
    monkeypatch.setattr(sources,'fetch',lambda *a,**k:(_ for _ in ()).throw(TimeoutError()))
    with pytest.raises(TimeoutError):s.collect(src)
    with get_db() as db:assert db.execute('SELECT materials FROM fieldtofit_discoveries').fetchone()[0]==new['materials']


def test_backlog_drains_five_at_a_time_and_new_versions_distinct(client,monkeypatch):
    from backend.knowledge import sources
    src=source('mimo-api-models');day=date.today().isoformat()
    body=''.join('<h2 id="release'+str(i)+'">'+day+' mimo-v'+str(i)+' Released</h2><p>Model ID mimo-v'+str(i)+'; API usage and changes.</p>' for i in range(12))
    monkeypatch.setattr(sources,'fetch',lambda *a,**k:(body,src['url'],'text/html'))
    with pytest.raises(sources.PartialSourceError) as exc:s.collect(src)
    assert exc.value.found==5 and len(progress(src['id'])['pending'])==7
    with pytest.raises(sources.PartialSourceError):s.collect(src)
    assert s.collect(src)==(2,2) and s.collect(src)==(0,0)
    with get_db() as db:assert db.execute('SELECT count(*) FROM fieldtofit_discoveries').fetchone()[0]==12


def test_ark_public_document_identity_month_and_different_deadlines(client):
    src=source('ark-models')
    md='# 202609\n|提供方|模型 ID|模型类型|版本说明|其它说明|\n|---|---|---|---|---|\n|字节|doubao-v2-260915|思考|新发布|Released model with API|'
    raw=json.dumps({'Result':{'DocumentCode':src['config']['document_code'],'LibraryCode':'ark','MDContent':md}})
    e=s.parse(src,raw)[0];assert e['published_at'] is None and e['metadata']['declared_date']=='2026-09'
    assert e['metadata']['fields']['模型 ID']=='doubao-v2-260915'
    assert e['metadata']['models']==['doubao-v2-260915']
    with pytest.raises(ValueError):s.parse(src,raw.replace('"ark"','"another"'))
    src=source('ark-deprecation');md='# 第十批模型下线说明\n## Schedule\n模型a EOM 2026-09-24 10:00 UTC+8；EOS 2026-11-24 14:00 UTC+8。模型b例外：2026-10-22 14:00 UTC+8。'
    e=s.parse(src,json.dumps({'Result':{'DocumentCode':src['config']['document_code'],'LibraryCode':'ark','MDContent':md}}))[0]
    assert e['published_at'] is None and e['metadata']['effective_dates']==['2026-09-24','2026-11-24','2026-10-22']
    assert '模型b例外' in e['metadata']['schedule_text']


def test_models_exclude_link_paths_attributes_and_document_names():
    body='doubao-seed-2-1-lite-260915 [调用指南](https://ark.volcengine.com/region:cn-beijing/docs/ark/deep-thinking) <span data-tips-type="model-deprecation-notice">EOS</span> deepseek-v3.2'
    assert s.model_ids(body)==['doubao-seed-2-1-lite-260915','deepseek-v3.2']
    assert s.model_ids('API 支持 [web-search-claude-code](https://docs.example.org/web-search-claude-code)')==[]
    assert s.model_ids('deepseek\\-v3\\-2\\-251201 doubao\\-seed\\-evolving')==['deepseek-v3-2-251201','doubao-seed-evolving']
    assert s.dates('EOM 2026-10-10, qwen-flash-2025-07-28-us')==['2026-10-10']


def test_bailian_notice_embedded_full_table_and_identity_required():
    body='<h2>影响时间</h2><p>2026-10-10</p><p>'+('官方停用计划说明。'*12)+'</p><table><tr><th>模型名称</th><th>推荐替换模型</th></tr><tr><td>aitryon-parsing-v1</td><td>qwen-image-3.0</td></tr></table>'
    detail={'id':118434,'publishTime':1783666493000,'detailList':[{'bulletinId':118434,'language':'zh','website':'cn','contentHtml':body}]}
    script='renderer({httpDatas: '+json.dumps({'public-notice':{'detailInfo':detail}})+'});'
    result=s.bailian_notice_payload(script,'https://www.aliyun.com/notice/118434')
    assert result['deprecated_models']==['aitryon-parsing-v1'] and result['replacement_models']==['qwen-image-3.0']
    assert result['declared_date']=='2026-07-10' and result['effective_dates']==['2026-10-10']
    with pytest.raises(ValueError):s.bailian_notice_payload(script,'https://www.aliyun.com/notice/118177')
    with pytest.raises(ValueError):s.bailian_notice_payload('仅有标题和页面更新时间','https://www.aliyun.com/notice/118434')
    detail['detailList'][0]['contentHtml']=body.replace('模型名称','快照模型名称').replace('<td>aitryon-parsing-v1</td><td>qwen-image-3.0</td>','<td rowspan="2">aitryon-parsing-v1 qwen3-8b</td><td rowspan="2">qwen-image-3.0</td>').replace('</table>','<tr></tr></table>')
    script='httpDatas: '+json.dumps({'public-notice':{'detailInfo':detail}})
    assert s.bailian_notice_payload(script,'https://www.aliyun.com/notice/118434')['deprecated_models']==['aitryon-parsing-v1','qwen3-8b']
    detail['detailList'][0]['contentHtml']='<p>具体下线清单如下：</p><ul><li>qwen-turbo</li><li>qwen-vl-max</li></ul><p>'+('完整官方停用安排。'*12)+'</p>'
    script='httpDatas: '+json.dumps({'public-notice':{'detailInfo':detail}})
    assert s.bailian_notice_payload(script,'https://www.aliyun.com/notice/118434')['deprecated_models']==['qwen-turbo','qwen-vl-max']


def test_html_rowspan_missing_region_and_original_year(client):
    src=source('bailian-models');raw='<h4>新加坡</h4><table><tr><th>模型类型</th><th>时间</th><th>服务部署范围</th><th>模型ID</th><th>功能说明</th></tr><tr><td>文本</td><td>2026-09-24</td><td><code>vendor/model-v2</code></td><td>Scope not filled upstream</td></tr></table>'
    e=s.parse(src,raw)[0];assert e['metadata']['region']=='原文未填写'
    src=source('bailian-platform');raw='<h4>2025 年</h4><table><tr><th>日期</th><th>功能模块</th><th>功能点</th><th>功能说明</th></tr><tr><td rowspan="2">9月22日</td><td>API</td><td>Change A</td><td>A</td></tr><tr><td>API</td><td>Change B</td><td>B</td></tr></table>'
    es=s.parse(src,raw);assert len(es)==2 and all(e['published_at']=='2025-09-22' for e in es)


def test_client_versions_are_individual_events(client):
    src=source('doubao-ios');items=[{'primarySubtitle':v,'secondarySubtitle':'Mon Sep 28 2026 03:16:46 GMT+0000 (Coordinated Universal Time)','text':'修复体验问题'} for v in ['15.2.1','15.2.0']]
    payload={'data':[{'data':{'shelfMapping':{'mostRecentVersion':{'items':items}}}}]}
    es=s.parse(src,'<script id="serialized-server-data">'+json.dumps(payload)+'</script>')
    assert len(es)==2 and es[0]['version']!=es[1]['version'] and es[0]['published_at']=='2026-09-28T03:16:46Z'


def test_hot_hn_query_has_no_ai_keyword_filter(client,monkeypatch):
    from backend.knowledge import sources
    src=next(x for x in source_catalog.definitions() if x['config']['mode']=='hn_hot');urls=[]
    def fetch(url):
        urls.append(url);return {'hits':[{'title':'Introducing Jev','url':'https://example.org/jev','objectID':'123','points':180,'num_comments':52}]}
    monkeypatch.setattr(sources,'fetch_json',fetch)
    assert discovery.collect(src)==(1,1) and 'query=' not in urls[0]
    assert len(urls)==2 and 'num_comments' in urls[1]
    with get_db() as db:assert store.decode(db.execute('SELECT metadata FROM fieldtofit_discoveries').fetchone()[0],{})['ai_relevance']=='pending'


def test_beijing_calendar_date_survives_previous_utc_day(client,monkeypatch):
    from backend.knowledge import content_workspace,sources
    src=source('bailian-models');day=(date.today()+timedelta(days=1)).isoformat()
    monkeypatch.setattr(content_workspace,'today',lambda:day)
    monkeypatch.setattr(sources,'fetch',lambda *a,**k:(table(day),src['url'],'text/html'))
    assert s.collect(src)==(1,1)
    with get_db() as db:assert db.execute('SELECT published_at FROM fieldtofit_discoveries').fetchone()[0]==day


def test_linked_notice_failure_keeps_last_identity_dates_and_body(client,monkeypatch):
    from backend.knowledge import sources
    src=source('bailian-deprecation');day=date.today().isoformat();url='https://www.aliyun.com/notice/118434'
    raw='<h2>'+day+'将下线</h2><p><a href="'+url+'">官方完整停用公告</a></p>'
    monkeypatch.setattr(sources,'fetch',lambda *a,**k:(raw,src['url'],'text/html'))
    notice={'body':'具体停用安排。'*30,'published_at':day+'T06:54:53Z','declared_date':day,'deprecated_models':['qwen3-8b'],'replacement_models':['qwen3.7-plus'],'schedule_records':[],'effective_dates':[day]}
    monkeypatch.setattr(s,'read_bailian_notice',lambda u:dict(notice))
    assert s.collect(src)==(1,1)
    with get_db() as db:old=dict(db.execute('SELECT * FROM fieldtofit_discoveries').fetchone())
    monkeypatch.setattr(s,'read_bailian_notice',lambda u:(_ for _ in ()).throw(TimeoutError()))
    with pytest.raises(sources.PartialSourceError) as exc:s.collect(src)
    assert exc.value.changed==0
    with get_db() as db:assert dict(db.execute('SELECT * FROM fieldtofit_discoveries').fetchone())==old
    notice['body']+='官方已更正替换方案。'
    monkeypatch.setattr(s,'read_bailian_notice',lambda u:dict(notice))
    assert s.collect(src)==(1,1)
    with get_db() as db:
        assert db.execute('SELECT id FROM fieldtofit_discoveries').fetchone()[0]==old['id']
        assert db.execute('SELECT count(*) FROM fieldtofit_discovery_versions').fetchone()[0]==1
