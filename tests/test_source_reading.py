"""Original excerpts across reviewed publication, reports, SSR and AI interfaces."""
import copy
import json
import pytest
from bs4 import BeautifulSoup
from test_knowledge import client
from test_search_pages import site
from test_content_workspace import call, migrate, publish
from backend.knowledge import content_workspace as ws
from backend.knowledge.source_reading import metadata, SCHEMA
from backend.knowledge.locale import source_hash


def source_copy(item):
    item=copy.deepcopy(item)
    item.update(title='Original release title',summary='An original announcement.',interpretation=[],note='OLD-EDITORIAL-MUST-NOT-LEAK')
    item['source_reading']={'schema_version':SCHEMA,'blocks':[
        {'id':'intro','kind':'quote','source_id':item['sources'][0]['id'],'locator':'Introduction','author':item['organization'],
         'checked_at':'2026-11-09','original_language':'en','quote':'An original announcement.','translation_zh':'原始公告。','reuse_basis':'Short attributed excerpt'},
        {'id':'figure','kind':'figure','source_id':item['sources'][0]['id'],'locator':'Figure 1','author':item['organization'],
         'checked_at':'2026-11-09','original_url':'https://example.org/original.png','display':'link','quote':'Original figure.','translation_zh':'原图。'}]}
    return item


def base():
    return next(i for i in ws.seeds()['news']['items'] if i['id']=='D-321')


@pytest.mark.parametrize('change',[
 {'source_id':'unregistered'}, {'checked_at':'2999-01-01'}, {'quote':''}, {'translation_zh':''}, {'original_language':'fr'}, {'reuse_basis':''}, {'kind':'html'}])
def test_missing_provenance_rejected(change):
    item=source_copy(base());item['source_reading']['blocks'][0].update(change)
    with pytest.raises(ValueError):metadata(item)


@pytest.mark.parametrize('url',['http://example.org/a','https://127.0.0.1/a','https://user:pass@example.org/a','https://[::1]/a','javascript:alert(1)'])
def test_unsafe_figures_rejected(url):
    item=source_copy(base());item['source_reading']['blocks'][1]['original_url']=url
    with pytest.raises(ValueError):metadata(item)


def test_redraw_cannot_be_relabelled_as_original():
    item=source_copy(base());block=item['source_reading']['blocks'][1]
    block.update(display='embedded',image_url='/report-figures/biobasicsbench-results.png',reuse_basis='Claimed permission',alt='Example')
    with pytest.raises(ValueError,match='重绘图'):metadata(item)


def test_quote_and_translation_both_invalidate_review():
    original=source_copy(base());before=source_hash('news',original)
    for field in ('quote','translation_zh','locator','checked_at'):
        changed=copy.deepcopy(original);changed['source_reading']['blocks'][0][field]+=' edited'
        # Date validation is checked separately; authored source mode validates map metadata.
        if field=='checked_at':changed['source_reading']['blocks'][0][field]='2026-11-08'
        assert source_hash('news',changed)!=before


@pytest.mark.parametrize('ident',['D-321','D-324'])
def test_save_bilingual_preview_publish_and_all_surfaces(site,ident):
    migrate(site)
    current=call(site,f'/content/news/{ident}',method='get').json
    original=copy.deepcopy(current['published'])
    draft=source_copy(current['draft'])
    # Reports can use only source reading, without fabricating graph nodes or opinions.
    draft['technical_map']={k:v for k,v in draft['technical_map'].items() if k in ('slug','reports')}
    saved=call(site,f'/content/news/{ident}',{'draft_version':current['draft_version'],'draft':draft},'patch')
    assert saved.status_code==200,saved.json
    preview=call(site,f'/content/news/{ident}/preview').json
    assert preview['ready'],preview
    for key in ('preview','preview_en'):
        obj=next(i for i in preview[key]['items'] if i['id']==ident)
        assert obj['source_reading']['blocks'][0]['quote']=='An original announcement.'
        assert obj['source_reading']['blocks'][0]['translation_zh']=='原始公告。'
        assert not obj['interpretation'] and not obj['note'] and not obj.get('media')
        assert obj['technical_map']['question']=='Original release title'
        assert obj['technical_map']['nodes']==[]
        assert 'OLD-EDITORIAL-MUST-NOT-LEAK' not in json.dumps(obj)
    assert call(site,f'/content/news/{ident}',method='get').json['published']==original
    publish(site,'news',ident)
    from test_mcp_reading import call as mcp
    for lang,prefix in [('zh',''),('en','/en')]:
        news=site.get('/api/v1/platform/news',query_string={'id':ident,'lang':lang}).json
        item=news['items'][0];slug=item['technical_map']['slug']
        maps=site.get('/api/v1/platform/maps',query_string={'slug':slug,'lang':lang}).json
        assert maps['items'][0]['source_reading']==item['source_reading']
        result=mcp(site,'curated_news',id=ident,lang=lang)
        assert result['structuredContent']['items'][0]['source_reading']==item['source_reading']
        for path in ('/news/'+ident,'/maps/'+slug):
            response=site.get(prefix+path);assert response.status_code==200
            dom=BeautifulSoup(response.text,'html.parser');section=dom.select_one('.source-reading')
            assert section and '原始公告。' in section.text and 'An original announcement.' in section.text
            assert not section.select('img')
            assert 'OLD-EDITORIAL-MUST-NOT-LEAK' not in response.text
            assert ('Source excerpts' if lang=='en' else '原文摘录') in section.text
        topic=site.get('/api/v1/platform/news',query_string={'company': 'openai' if ident=='D-321' else 'anthropic','lang':lang}).json
        assert next(i for i in topic['items'] if i['id']==ident)['title']=='Original release title'
    # Any later edit makes the old preview token unusable and the bilingual review stale.
    d=call(site,f'/content/news/{ident}',method='get').json
    d['draft']['source_reading']['blocks'][0]['translation_zh']='修改后的译文。'
    changed=call(site,f'/content/news/{ident}',{'draft_version':d['draft_version'],'draft':d['draft']},'patch')
    assert changed.status_code==200
    assert changed.json['english']['state']!='reviewed'
    stale=call(site,f'/content/news/{ident}/publish',{'draft_version':preview['draft_version'],'review_token':preview['review_token'],'confirmed':True,'reason':'stale'})
    assert stale.status_code!=200
    assert call(site,f'/content/news/{ident}',method='get').json['published']['source_reading']['blocks'][0]['translation_zh']=='原始公告。'


def test_original_asset_registration_and_license_binding(monkeypatch):
    from pathlib import Path
    item=source_copy(base());b=item['source_reading']['blocks'][1]
    b.update(display='embedded',image_url='/report-figures/test-original.png',alt='Fixture original',reuse_basis='Fixture permission')
    asset={'kind':'original','original_url':b['original_url'],'source_urls':[item['sources'][0]['url']],
           'license':'Fixture permission','rights_url':'https://example.org/permission'}
    read=Path.read_text
    monkeypatch.setattr(Path,'read_text',lambda p,*a,**k: json.dumps({b['image_url']:asset}) if p.name=='report-figures.json' else read(p,*a,**k))
    out=metadata(item);assert out['blocks'][1]['image_url']==b['image_url']
    assert out['blocks'][1]['rights_url']==asset['rights_url']
    for key,value in [('license','wrong'),('kind','redraw'),('original_url','https://example.org/another.png'),('rights_url','http://example.org/permission')]:
        old=asset[key];asset[key]=value
        with pytest.raises(ValueError):metadata(item)
        asset[key]=old


def test_incomplete_source_draft_saves_without_publishing(client):
    migrate(client);d=call(client,'/content/news/D-321',method='get').json
    published = client.get('/api/v1/platform/news?id=D-321').json
    d['draft']['source_reading']={'schema_version':SCHEMA,'blocks':[]}
    saved=call(client,'/content/news/D-321',{'draft_version':d['draft_version'],'draft':d['draft']},'patch')
    assert saved.status_code==200
    assert not call(client,'/content/news/D-321/preview').json['ready']
    assert client.get('/api/v1/platform/news?id=D-321').json == published


def test_html_quote_is_escaped_not_executed(site):
    migrate(site);d=call(site,'/content/news/D-321',method='get').json
    d['draft']=source_copy(d['draft']);d['draft']['source_reading']['blocks'][0]['quote']='<script>alert(1)</script>'
    saved=call(site,'/content/news/D-321',{'draft_version':d['draft_version'],'draft':d['draft']},'patch');assert saved.status_code==200
    publish(site,'news','D-321')
    page=site.get('/en/news/D-321');dom=BeautifulSoup(page.text,'html.parser');excerpt=dom.select_one('.source-reading')
    assert '<script>alert(1)</script>' in excerpt.text
    assert not excerpt.select('script')
