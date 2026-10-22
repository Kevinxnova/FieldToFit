"""Information cards use the real isolated publication and bilingual review gates."""
import copy
import hashlib
import json
from pathlib import Path
import pytest
from test_knowledge import client, MCP
from backend.knowledge import content_workspace as ws, hot_cards, locale, platform_news

FIXTURE=Path(__file__).parent/'fixtures/hot-cards.json'


@pytest.fixture(autouse=True)
def uncarded_article_baseline(tmp_path, monkeypatch):
    """Keep card-creation tests independent of already published production cards."""
    data=json.loads(platform_news.CONTENT_PATH.read_text())
    for item in data['items']:
        if item.pop('hot_card', None) is not None:
            en=item.get('translations', {}).get('en', {})
            en['source_hash']=locale.source_hash('news', item)
            required=locale.strings(locale.authored('news', item))
            en['fields']={k:v for k,v in en.get('fields', {}).items() if k in required}
    path=tmp_path/'uncarded-news.json'
    path.write_text(json.dumps(data, ensure_ascii=False))
    monkeypatch.setattr(platform_news, 'CONTENT_PATH', path)
    seeds=ws.seeds();seeds['news']=data
    monkeypatch.setattr(ws, 'seeds', lambda:copy.deepcopy(seeds))


def samples():
    return json.loads(FIXTURE.read_text())


def save_card(sample):
    current=ws.detail('news',sample['id'])
    # Keep all existing article fields; the new card is one optional addition.
    draft={**current['draft'],'hot_card':copy.deepcopy(sample['hot_card'])}
    saved=ws.save('news',sample['id'],{'draft_version':current['draft_version'],'draft':draft})
    # Preserve reviewed article translations when production copy evolves;
    # this fixture supplies the optional card, not a replacement article.
    fields={**current['english']['fields'], **sample['translations']['en']['fields']}
    return ws.english_review('news',sample['id'],{'draft_version':saved['draft_version'],
        'source_hash':saved['english']['source_hash'],'fields':{k:v for k,v in fields.items() if k in saved['english']['fields']},
        'confirmed':True,'reason':'Isolated manually reviewed card copy'})


def publish(ident):
    preview=ws.preview('news',ident)
    assert preview['ready'],preview
    return ws.publish('news',ident,{'draft_version':preview['draft_version'],'review_token':preview['review_token'],
        'confirmed':True,'reason':'Isolated card acceptance'})


def test_card_lifecycle_web_mcp_english_assets_and_withdrawal(client):
    original=client.get('/api/v1/platform/news?id=D-83').json
    assert 'hot_card' not in original['items'][0]
    ws.migrate()
    for sample in samples():
        save_card(sample)
        assert 'hot_card' not in client.get('/api/v1/platform/news?id='+sample['id']).json['items'][0]
        preview=ws.preview('news',sample['id'])
        assert preview['ready'],preview
        assert not locale.HAN.search(json.dumps(preview['preview_en']['items'][0]['hot_card'],ensure_ascii=False))
        publish(sample['id'])
    zh=client.get('/api/v1/platform/news').json
    rpc=client.post('/api/mcp/curated',headers=MCP,json={'jsonrpc':'2.0','id':1,'method':'tools/call',
        'params':{'name':'curated_news','arguments':{}}}).json['result']
    assert rpc['structuredContent']==zh
    en=client.get('/api/v1/platform/news?lang=en&id=D-83').json
    assert client.get('/api/v1/platform/news?q=合上电脑').json['items'][0]['id']=='D-83'
    assert client.get('/api/v1/platform/news?q=Close%20your%20laptop&lang=en').json['items'][0]['id']=='D-83'
    card=en['items'][0]['hot_card'];assert card['headline']=='Close your laptop. Cloud tasks keep running.'
    for sample in samples():
        for lang in ('zh','en'):
            asset=sample['hot_card']['share'][lang]
            assert hashlib.sha256((hot_cards.ASSETS/asset['url'].split('/')[-1]).read_bytes()).hexdigest()==asset['sha256']
    page=client.get('/en/news/D-83');assert page.status_code==200 and card['headline'] in page.text
    current=ws.detail('news','D-83');current['draft']['hot_card'].update(status='needs_update',update_note='Awaiting updated plan conditions')
    saved=ws.save('news','D-83',{'draft_version':current['draft_version'],'draft':current['draft']})
    from english_fixtures import approve_fixture
    approve_fixture('news','D-83');publish('D-83')
    pending=client.get('/api/v1/platform/news?id=D-83').json['items'][0]['hot_card']
    assert pending['status']=='needs_update' and 'share' not in pending
    current=ws.detail('news','D-83')
    ws.publish('news','D-83',{'draft_version':current['draft_version'],'reason':'Isolated withdrawal'},withdraw=True)
    assert client.get('/api/v1/platform/news?id=D-83').status_code==404
    assert 'D-83' not in [i['id'] for i in client.get('/api/v1/platform/news').json['items']]


def test_selection_and_check_only_changes_do_not_manufacture_publication_dates(client):
    ws.migrate();sample=samples()[0];save_card(sample);publish(sample['id'])
    before=client.get('/api/v1/platform/news?id=D-83').json['items'][0]
    sample['hot_card']['featured_rank']=0
    save_card(sample);publish(sample['id'])
    after=client.get('/api/v1/platform/news?id=D-83').json['items'][0]
    assert after['publication']==before['publication']
    assert after['hot_card']['featured_rank']==0
    current=ws.detail('news',sample['id']);current['draft']['checked_at']='2026-10-12'
    saved=ws.save('news',sample['id'],{'draft_version':current['draft_version'],'draft':current['draft']})
    from english_fixtures import approve_fixture
    approve_fixture('news',sample['id']);publish(sample['id'])
    assert client.get('/api/v1/platform/news?id=D-83').json['items'][0]['publication']==before['publication']


def test_static_card_files_and_serverless_manifest(client,tmp_path,monkeypatch):
    import backend.api.main as main
    monkeypatch.setattr(main,'CLIENT_DIST',hot_cards.ASSETS.parent)
    sample=samples()[0]
    asset=sample['hot_card']['share']['zh']
    response=client.get(asset['url'])
    assert response.status_code==200 and response.mimetype=='image/png'
    assert hashlib.sha256(response.data).hexdigest()==asset['sha256']
    assert client.get('/hot-cards/missing.png').status_code==404
    # Serverless API uses the deployed registry while images are hosted as static files.
    monkeypatch.setattr(hot_cards,'ASSETS',tmp_path/'not-in-api-bundle')
    assert hot_cards.metadata(sample,enforce_assets=True)


@pytest.mark.parametrize('broken',['source','date','rank','copy','asset','english_image','translation','draft_shape'])
def test_card_rejects_invalid_review_and_stale_images(client,broken):
    ws.migrate();sample=samples()[0]
    if broken=='source':sample['hot_card']['evidence'][0]['source_id']='missing'
    if broken=='date':sample['hot_card']['revised_at']='2099-01-01'
    if broken=='rank':sample['hot_card']['featured_rank']=True
    if broken=='copy':sample['hot_card']['headline']='New text with an old image'
    if broken=='asset':sample['hot_card']['share']['zh']['sha256']='0'*64
    if broken=='english_image':sample['hot_card']['share']['en']['text_revision']='0'*64
    if broken=='translation':sample['translations']['en']['fields'][sample['hot_card']['headline']]='A different translated conclusion'
    if broken=='draft_shape':
        current=ws.detail('news',sample['id']);current['draft']['hot_card']={'changes':'bad'}
        with pytest.raises(ValueError):ws.save('news',sample['id'],{'draft_version':current['draft_version'],'draft':current['draft']})
        return
    save_card(sample)
    assert not ws.preview('news',sample['id'])['ready']


def test_card_whitelist_revision_and_old_article_compatibility(client):
    data=json.loads(platform_news.CONTENT_PATH.read_text());before=platform_news.news(_data=data)
    sample=samples()[0];target=next(i for i in data['items'] if i['id']==sample['id'])
    target['hot_card']={**sample['hot_card'],'private_note':'NEVER-PUBLIC'}
    target['hot_card']['audiences'][0]['internal_note']='NEVER-PUBLIC'
    after=platform_news.news(_data=data)
    assert after['revision']!=before['revision'] and 'NEVER-PUBLIC' not in json.dumps(after)
    assert len(after['items'])==len(before['items'])
    assert all(a==b for a,b in zip(before['items'],after['items']) if a['id']!=sample['id'])
    revision=after['revision'];target['hot_card']['featured_rank']=0
    assert platform_news.news(_data=data)['revision']!=revision
    assert hot_cards.metadata(target)['revision']==sample['hot_card']['share']['content_revision']
