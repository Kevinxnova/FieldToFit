"""Reviewed report text follows the existing publication boundary and history."""
import copy
import hashlib
import json
from pathlib import Path
import pytest
from test_knowledge import client, MCP
from test_content_workspace import call, migrate, make, publish
from backend.knowledge import technical_maps as tm, content_workspace as ws

ROOT = Path(__file__).resolve().parents[1]

def case():
    item = json.loads((ROOT/'backend/knowledge/content/map-reading-bottle.json').read_text())
    # Reviewed reports now exist in the seed; give this new-publication fixture its own identity.
    item['technical_map']['slug'] = 'reading-fixture-artifacts'
    item['technical_map']['question'] += '（隔离格式验收）'
    return item

def prepare(client):
    migrate(client); ident, _ = make(client, 'news'); d=ws.detail('news',ident); item=case(); item['id']=ident
    ws.save('news',ident,{'draft':item,'draft_version':d['draft_version']})
    return ident


def test_reading_publication_ai_no_js_revision_and_restore(client):
    before=tm.maps();ident=prepare(client)
    assert tm.maps()==before
    preview=ws.preview('news',ident);assert preview['ready']
    assert preview['preview']['items'][0]['technical_map']['reading']==case()['technical_map']['reading']
    publish(client,'news',ident);slug=case()['technical_map']['slug'];first=tm.maps(slug=slug)
    assert first['items'][0]['reading']==case()['technical_map']['reading']
    assert 'reading' not in tm.maps(slug='agent-context-cost')['items'][0]
    rpc=client.post('/api/mcp/curated',headers=MCP,json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'curated_maps','arguments':{'slug':slug}}}).json['result']
    assert rpc['structuredContent']==first
    html=client.get('/maps/'+slug).data.decode()
    assert 'argument-point-4' in html and '47/60' in html and '#page=9' in html and 'CC BY 4.0' in html
    d=ws.detail('news',ident);d['draft']['technical_map']['reading']['findings'][0]['summary']='Reviewed correction, not a new report date'
    ws.save('news',ident,{'draft':d['draft'],'draft_version':d['draft_version']});assert tm.maps(slug=slug)==first
    publish(client,'news',ident);second=tm.maps(slug=slug)
    assert second['revision']!=first['revision'] and second['items'][0]['reports']==first['items'][0]['reports']
    assert [x['field'] for x in tm.compare(slug)['fields']]==['reading']
    old=tm.history(slug)['items'][1];d=ws.detail('news',ident)
    assert call(client,f'/content/news/{ident}/restore',{'seq':old['revision'],'draft_version':d['draft_version']}).status_code==200
    assert tm.maps(slug=slug)==second
    d=ws.detail('news',ident);call(client,f'/content/news/{ident}/withdraw',{'draft_version':d['draft_version'],'reason':'isolated withdrawal'})
    assert client.get('/maps/'+slug).status_code==404


@pytest.mark.parametrize('change',[
    lambda r:r['findings'][0].update(node_ids=['missing']),
    lambda r:r['findings'][1].update(id=r['findings'][0]['id']),
    lambda r:r['findings'][0].update(evidence=[{'source_id':'submission','locator':'abstract'}]),
    lambda r:r['findings'][0]['blocks'][2].update(image_url='/report-figures/missing.png'),
    lambda r:r['findings'][0]['blocks'][2].update(image_url='https://127.0.0.1/private.png'),
    lambda r:r['findings'][0]['blocks'][2].update(license='unverified'),
    lambda r:r['findings'][0]['blocks'][2].update(evidence=[{'source_id':'submission','locator':'abstract'}]),
    lambda r:r['findings'][0]['blocks'][3].update(label='editorial'),
    lambda r:r['findings'][0]['blocks'][0].update(kind='html',text='<script>alert(1)</script>'),
])
def test_unreviewable_reading_cannot_publish(client,change):
    ident=prepare(client);before=tm.maps();d=ws.detail('news',ident);change(d['draft']['technical_map']['reading'])
    ws.save('news',ident,{'draft':d['draft'],'draft_version':d['draft_version']})
    assert not ws.preview('news',ident)['ready'] and tm.maps()==before


def test_assets_match_verified_captures_and_escaped_text(client):
    manifest=json.loads((ROOT/'backend/knowledge/content/report-figures.json').read_text())
    for url,asset in manifest.items():
        assert hashlib.sha256((ROOT/'frontend/public'/url.lstrip('/')).read_bytes()).hexdigest()==asset['sha256']
    ident=prepare(client);d=ws.detail('news',ident);d['draft']['technical_map']['reading']['findings'][0]['summary']='<script>unsafe()</script>'
    ws.save('news',ident,{'draft':d['draft'],'draft_version':d['draft_version']});publish(client,'news',ident)
    html=client.get('/maps/reading-fixture-artifacts').data.decode()
    assert '<script>unsafe()' not in html and '&lt;script&gt;unsafe()' in html


def test_consumer_analysis_preserves_panel_scope_redraw_provenance_and_publication_boundary(client):
    item=json.loads((ROOT/'backend/knowledge/content/map-reading-a16z-consumer.json').read_text())
    item['technical_map']['slug']='consumer-fixture-analysis'
    item['technical_map']['question']+='（隔离消费分析验收）'
    manifest=json.loads((ROOT/'backend/knowledge/content/report-figures.json').read_text())
    chart=manifest['/report-figures/a16z-20261005-ranking-gap.png']['statistics']
    assert chart['spend_top_50_absent_from_both_traffic_lists']+chart['spend_top_50_in_at_least_one_traffic_list']==50
    assert all(e['relation']=='parallel' for e in item['technical_map']['edges'])
    migrate(client);ident,_=make(client,'news');d=ws.detail('news',ident);item['id']=ident
    before=tm.maps();ws.save('news',ident,{'draft':item,'draft_version':d['draft_version']})
    assert tm.maps()==before and ws.preview('news',ident)['ready']
    publish(client,'news',ident);data=tm.maps(slug='consumer-fixture-analysis');public=data['items'][0]
    assert public['reports'][0]['first_published_at']=='2026-10-05'
    assert len(public['reading']['findings'])==4 and '美国面板' in public['caution']
    for f in public['reading']['findings']:
        fig=next(b for b in f['blocks'] if b['kind']=='figure')
        assert '本站重绘' in fig['attribution'] and 'CC BY' not in fig['license']
        assert manifest[fig['image_url']]['origin']=='fieldtofit-redraw'
    html=client.get('/maps/consumer-fixture-analysis').data.decode()
    assert '2026-10-05' in html and '2026年8月' in html and 'argument-ranking-gap' in html
    assert '19.5%' in html and '16.6%' in html and '50减29' in html
    rpc=client.post('/api/mcp/curated',headers=MCP,json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'curated_maps','arguments':{'slug':'consumer-fixture-analysis'}}}).json['result']
    assert rpc['structuredContent']==data
    assert len(tm.history('consumer-fixture-analysis')['items'])==1
