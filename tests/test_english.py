"""Bilingual publication and public projections, using isolated data only."""
import copy
import json
import re
import pytest
from test_knowledge import client, ADMIN, MCP
from backend.knowledge import content_workspace as ws, locale

SOURCE='已核对官方材料；未独立运行。'
FIELDS={SOURCE:'Official materials reviewed; not independently run.',
        '未独立运行。':'Not independently run.',
        '版本 1.0；2 个入口。':'Version 1.0; 2 entries.'}

def draft(client):
    ws.migrate();current=ws.detail('watch','CW-T01')
    current['draft']={'id':'CW-T01','state':'published','name':'Isolated bilingual fixture','type':'tool',
        'introduction':SOURCE,'checked_at':ws.today(),'evidence_status':'official_materials_reviewed_not_runtime_tested',
        'sources':[{'title':'Official fixture','url':'https://example.org/english','coverage':'link_only'}],
        'interpretation':[{'title':'Limitations','text':'未独立运行。'}],
        'blocks':[{'kind':'paragraph','text':'版本 1.0；2 个入口。'}]}
    return ws.save('watch','CW-T01',current)

def review(current,confirmed=True,fields=None):
    return ws.english_review('watch','CW-T01',{'draft_version':current['draft_version'],
        'source_hash':locale.source_hash('watch',current['draft']),
        'fields':fields or FIELDS,'confirmed':confirmed,'reason':'Checked source, facts, numbers and limitations'})

def test_missing_draft_review_stale_and_conflicts(client):
    current=draft(client)
    assert ws.preview('watch','CW-T01')['ready'] is False
    current=review(current,False)
    assert current['english']['state']=='draft'
    assert ws.preview('watch','CW-T01')['ready'] is False
    with pytest.raises(Exception,match='Preserve source numbers'):
        review(current,True,{**FIELDS,'版本 1.0；2 个入口。':'Version 1.0; 3 entries.'})
    current=review(current)
    assert current['english']['state']=='reviewed'
    with pytest.raises(Exception,match='Draft changed'):review({**current,'draft_version':current['draft_version']-1})
    current['draft']['checked_at']='2026-10-10' if ws.today()!='2026-10-10' else '2026-10-09'
    current=ws.save('watch','CW-T01',current)
    assert current['english']['state']=='stale'
    assert ws.preview('watch','CW-T01')['ready'] is False

def test_review_preview_publish_http_mcp_and_withdrawal(client):
    current=review(draft(client));preview=ws.preview('watch','CW-T01')
    assert preview['ready'],preview
    en=preview['preview_en'];zh=preview['preview']
    assert en['items'][0]['introduction']==FIELDS[SOURCE]
    assert zh['items'][0]['introduction']==SOURCE
    ws.publish('watch','CW-T01',{**preview,'confirmed':True,'reason':'Isolated bilingual publication'})
    chinese=client.get('/api/v1/platform/watch?id=CW-T01').json
    english=client.get('/api/v1/platform/watch?id=CW-T01&lang=en')
    assert english.status_code==200,english.json
    assert english.json['revision']==chinese['revision']
    rpc=client.post('/api/mcp/curated',headers=MCP,json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'curated_watch','arguments':{'id':'CW-T01','lang':'en'}}}).json['result']
    assert not rpc['isError'];assert rpc['structuredContent']==english.json
    assert client.get('/api/v1/platform/watch?id=CW-T01&lang=fr').status_code==400
    current=ws.detail('watch','CW-T01');ws.publish('watch','CW-T01',{'draft_version':current['draft_version'],'reason':'Isolated withdrawal'},True)
    assert client.get('/api/v1/platform/watch?id=CW-T01&lang=en').status_code==404

def test_originals_ids_urls_and_dates_are_preserved():
    value={'id':'CW-T01','url':'https://example.org/raw','date':'2026-10-11','body':'原始材料123','quote':'原文引文',
           'excerpt':'中文摘录','summary':SOURCE,'path':'/watch/CW-T01'}
    en=locale.project(value,FIELDS)
    for key in ('id','url','date','body','quote','excerpt'):assert en[key]==value[key]
    assert en['summary']==FIELDS[SOURCE];assert en['path']=='/en/watch/CW-T01'
    assert locale.project({'summary':'完全未登记的测试译文'},FIELDS,strict=False)['summary']
    with pytest.raises(Exception,match='missing or out of date'):locale.project({'summary':'完全未登记的测试译文'})

def test_default_wire_and_mcp_schema_remain_compatible(client):
    from backend.knowledge.platform_watch import watch
    assert client.get('/api/v1/platform/watch').json==watch()
    from backend.knowledge.mcp import TOOLS,CODEX_TOOL
    assert all(tool['inputSchema']['properties']['lang']['enum']==['zh','en'] for tool in [*TOOLS,CODEX_TOOL])
    assert all('lang' not in tool['inputSchema']['required'] for tool in [*TOOLS,CODEX_TOOL])

def test_object_scoping_schema_and_original_source_locations():
    value={'items':[{'id':'A','summary':SOURCE},{'id':'B','summary':SOURCE}],
           'schema':{'properties':{'id':{'type':'string'}}},
           'location':{'id':'section-1','title':'未经改写的原始小节','start':0,'end':20},
           'pages':[{'id':'page-1','title':'文件第 1 页','page':1}],
           'rights':{'notice':'原始许可文字 & <原文>'}}
    scoped={'__objects__':{'A':{SOURCE:'Review A.'},'B':{SOURCE:'Review B.'}}}
    en=locale.project(value,scoped)
    assert [i['summary'] for i in en['items']]==['Review A.','Review B.']
    assert en['schema']==value['schema'] and en['location']==value['location']
    assert en['rights']==value['rights'] and en['pages'][0]['title']=='Physical page 1'
    from backend.seo.locale import english_html
    html=english_html('<h2>技术报告精选&amp;分析</h2><pre data-original-language="source">原文 &lt;tag&gt; &amp; 引文</pre>')
    assert 'Selected Technical Reports &amp; Analysis' in html
    assert '原文 &lt;tag&gt; &amp; 引文' in html

def test_english_revisions_use_their_own_review_and_hide_private_notes(client):
    current=review(draft(client));p=ws.preview('watch','CW-T01')
    ws.publish('watch','CW-T01',{**p,'confirmed':True,'reason':'First isolated publication'})
    first=client.get('/api/v1/platform/watch?id=CW-T01').json['revision']
    current=ws.detail('watch','CW-T01')
    revised={**FIELDS,SOURCE:'Official sources checked; no independent execution.'}
    current=review(current,fields=revised);p=ws.preview('watch','CW-T01')
    ws.publish('watch','CW-T01',{**p,'confirmed':True,'reason':'Second isolated publication'})
    latest=client.get('/api/v1/platform/watch?id=CW-T01&lang=en').json
    assert latest['revision']!=first
    assert latest['items'][0]['introduction']==revised[SOURCE]
    result=client.get('/api/v1/platform/content/CW-T01/compare?lang=en')
    assert result.status_code==200,result.json
    changed=next(f for f in result.json['fields'] if f['field']=='introduction')
    assert changed['before']==FIELDS[SOURCE] and changed['after']==revised[SOURCE]
    assert 'review_note' not in json.dumps(result.json)
    assert 'Checked source, facts, numbers and limitations' not in json.dumps(latest)
    # Source edits cannot forge an approval by uploading translation metadata.
    current=ws.detail('watch','CW-T01');current['draft']['introduction']='改变后的来源。'
    current['draft']['translations']['en']['source_hash']=locale.source_hash('watch',current['draft'])
    current=ws.save('watch','CW-T01',current)
    assert current['english']['state']=='stale' and not ws.preview('watch','CW-T01')['ready']

def test_english_material_markdown_keeps_original_bytes_and_citations(client):
    from test_stewardship import with_material
    from english_fixtures import approve_fixture
    from backend.knowledge import content_materials as cm
    ws.migrate();with_material(client,'CW-M01')
    approve_fixture('watch','CW-M01');p=ws.preview('watch','CW-M01')
    ws.publish('watch','CW-M01',{**p,'confirmed':True,'reason':'Isolated bilingual material'})
    original=cm.read('CW-M01','readme')
    with locale.read_language('en'):
        package=cm.bundle([{'id':'CW-M01'}],200000,format='markdown')
        read=cm.read('CW-M01','readme')
    assert original['body'] in package['markdown']
    assert read['body']==original['body'] and read['offset']==original['offset']
    assert not locale.HAN.search(package['markdown'].replace(original['body'],''))

def test_merge_requires_review_of_the_final_combined_source(client):
    from test_stewardship import pair
    from backend.knowledge import stewardship as st
    from english_fixtures import reviewed_merge
    source,target=pair(client)
    data={'action':'merge','source':source,'target':target,'reason':'Isolated merge'}
    p=st.preview(data)
    assert not p['ready'] and p['english_reviews'][target]['state']!='reviewed'
    data['choices']={c['field']:'target' for c in p['conflicts']}
    data,p=reviewed_merge(data)
    assert p['ready'],p['errors']
    st.apply({**data,'review_token':p['review_token'],'confirmed':True})
    result=client.get('/api/v1/platform/watch?id='+target+'&lang=en')
    assert result.status_code==200,result.json
    assert not locale.strings(result.json)

def test_english_direct_routes_metadata_and_filters(client):
    for path in ('/en/for-you','/en/for-your-ai','/en/about','/en/news/D-01','/en/watch/CW-T01','/en/maps'):
        r=client.get(path,base_url='https://fieldtofit.top')
        assert r.status_code==200,(path,r.status_code)
        assert '<html lang="en"' in r.text and 'hreflang="zh-CN"' in r.text and 'hreflang="en"' in r.text
        assert 'https://fieldtofit.top'+path in r.text
    r=client.get('/api/v1/platform/news?q=document&lang=en')
    assert r.status_code==200 and r.json['total']>0

def test_intake_bilingual_review_is_stable_and_atomic(client,monkeypatch):
    from test_platform_maintenance import sample,draft as intake_draft
    from backend.knowledge import platform_maintenance as maintenance,store,platform
    sample();data=intake_draft();first=maintenance.apply(data)
    monkeypatch.setattr(store,'now',lambda:'2026-11-01T12:00:00+00:00')
    assert maintenance.apply(data)['english']['source_hash']==first['english']['source_hash']
    with pytest.raises(platform.PlatformError,match='Source changed'):
        maintenance.apply({**data,'introduction':'源文已修改。'},publish=True)
    assert maintenance.jobs()['items'] and platform.search()['total']==0
    assert maintenance.apply(data,publish=True)['gate']['ready']

def test_english_correction_context_preserves_canonical_source(client):
    from backend.knowledge import corrections
    ws.migrate()
    response=client.get('/api/v1/platform/content/CW-T01/correction-context?lang=en')
    assert response.status_code==200 and response.json['language']=='en'
    assert not locale.HAN.search(response.json['value'])
    submitted=client.post('/api/v1/feedback?lang=en',json={'context':response.json,'content':'Check this statement','contact':''})
    assert submitted.status_code==201,submitted.json
    canonical=corrections.detail(submitted.json['id'])['context']
    assert canonical['value']==corrections.context('CW-T01')['value']
    assert locale.HAN.search(canonical['value'])

def test_roundup_corrections_validate_with_referenced_events(client,tmp_path,monkeypatch):
    from test_codex_roundup import install,with_roundup
    install(with_roundup(),tmp_path,monkeypatch);ws.migrate()
    receipts=client.get('/api/v1/platform/content/D-85/corrections')
    assert receipts.status_code==200,receipts.json
    context=client.get('/api/v1/platform/content/D-85/correction-context?field=summary')
    assert context.status_code==200,context.json
    assert context.json['object_id']=='D-85'

def test_roundup_preview_keeps_each_objects_reviewed_english(client,tmp_path,monkeypatch):
    from test_codex_roundup import install,with_roundup
    install(with_roundup(),tmp_path,monkeypatch);ws.migrate()
    for ident,translation in [('D-84','Published object English.'),('D-85','Current draft English.')]:
        current=ws.detail('news',ident);current['draft']['summary']=SOURCE
        current=ws.save('news',ident,current)
        fields={**current['english']['fields'],SOURCE:translation}
        ws.english_review('news',ident,{'draft_version':current['draft_version'],'source_hash':current['english']['source_hash'],
                                      'fields':fields,'confirmed':True,'reason':'Check individual source and English'})
        if ident=='D-84':
            preview=ws.preview('news',ident)
            ws.publish('news',ident,{**preview,'confirmed':True,'reason':'Publish isolated dependency'})
    preview=ws.preview('news','D-85');assert preview['ready'],preview
    assert preview['preview_en']['items'][0]['summary']=='Current draft English.'
    dependency=next(i for i in preview['preview_en']['referenced_items'] if i['id']=='D-84')
    assert dependency['summary']=='Published object English.'

def test_public_notes_and_translation_scale_require_review():
    from backend.knowledge.platform import PlatformError
    from scripts.locale.check import numbers
    with pytest.raises(PlatformError):locale.reviewed_note('修订 2 项',{})
    assert locale.reviewed_note('修订 2 项',{'public_note_en':'Corrected 2 items','english_confirmed':True})=='Corrected 2 items'
    with pytest.raises(PlatformError):locale.reviewed_note('修订 2 项',{'public_note_en':'Corrected 3 items','english_confirmed':True})
    assert numbers('约 2.8 亿参数')==numbers('about 280 million parameters')
    assert numbers('约 2.8 亿参数')!=numbers('about 2.8 billion parameters')
    assert numbers('10月11日11:58')==numbers('10/11 11:58')
