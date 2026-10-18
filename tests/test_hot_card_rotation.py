"""Real isolated card publication; never writes to production."""
import copy
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from test_knowledge import client, MCP
from test_search_pages import site
from test_content_workspace import make
from test_hot_cards import samples
from english_fixtures import approve_fixture
from backend.knowledge import content_workspace as ws, hot_cards, locale
from scripts.maintenance import hot_information_cards as handoff


@pytest.fixture
def fourth(client, tmp_path, monkeypatch):
    ws.migrate()
    assets = tmp_path / 'cards'
    shutil.copytree(hot_cards.ASSETS, assets)
    registry = json.loads(hot_cards.MANIFEST.read_text())
    manifest = tmp_path / 'assets.json'
    monkeypatch.setattr(hot_cards, 'ASSETS', assets)
    monkeypatch.setattr(hot_cards, 'MANIFEST', manifest)
    ident, _ = make(client, 'news')
    sample = copy.deepcopy(samples()[0])
    sample.update(id=ident, highlight=False)
    sample.pop('translations', None)
    sample['publication'] = {k: '2999-01-01T00:00:00Z' for k in ('first_published_at', 'updated_at', 'hot_card_first_published_at', 'hot_card_selected_at')}
    card = sample['hot_card']
    card['featured_rank'] = 3  # All new selected cards still enter first.
    card['share']['content_revision'] = hot_cards.fingerprint(sample, card)
    fields = samples()[0]['translations']['en']['fields']
    for lang in ('zh', 'en'):
        asset = card['share'][lang]
        old = assets / asset['url'].split('/')[-1]
        asset['url'] = '/hot-cards/isolated-' + ident.lower() + '-' + lang + '.png'
        shutil.copy(old, assets / asset['url'].split('/')[-1])
        if lang == 'en':
            translated = locale.project(sample, fields)
            asset['text_revision'] = hot_cards.fingerprint(translated, translated['hot_card'])
        registry[asset['url']] = {**asset, 'news_id': ident, 'content_revision': card['share']['content_revision']}
    manifest.write_text(json.dumps(registry))
    current = ws.detail('news', ident)
    saved = ws.save('news', ident, {'draft_version': current['draft_version'], 'draft': sample})
    ws.english_review('news', ident, {'draft_version': saved['draft_version'], 'source_hash': saved['english']['source_hash'],
        'fields': {k: fields[k] for k in saved['english']['fields']}, 'confirmed': True, 'reason': 'Unchanged fixture translation, isolated card'})
    return ident


def publish(ident):
    preview = ws.preview('news', ident)
    assert preview['ready'], preview
    return ws.publish('news', ident, {**preview, 'confirmed': True, 'reason': 'Isolated card publication'})


def public(client):
    return client.get('/api/v1/platform/news').json


def test_publish_rotates_atomically_and_keeps_images_dates_private_drafts(client, fourth, monkeypatch):
    before = public(client)
    old_ids = before['hot_card_selection']['ids']
    old = ws.detail('news', old_ids[0])
    old['draft']['note'] += ' PRIVATE-PENDING-EDIT'
    ws.save('news', old_ids[0], old)
    saved_private = ws.detail('news', old_ids[0])
    assert saved_private['english']['state'] == 'stale'
    stale = ws.preview('news', old_ids[1])
    prepared = ws.detail('news', fourth)
    preview = ws.preview('news', fourth)
    assert preview['ready'] and preview['hot_card_rotation']['status'] == 'preview'
    assert preview['hot_card_rotation']['entered'][0]['id'] == fourth
    assert public(client) == before and ws.detail('news', fourth)['draft'] == prepared['draft']
    monkeypatch.setattr(ws, 'stamp', lambda: '2026-10-17T05:00:00+00:00')
    result = publish(fourth)
    after = public(client)
    assert after['hot_card_selection']['ids'] == [fourth, *old_ids[:2]]
    receipt = result['hot_card_rotation']
    assert receipt['status'] == 'published' and receipt['changed']
    assert [r['id'] for r in receipt['index_only']] == old_ids[2:]
    pub = result['published']['publication']
    assert pub['hot_card_selected_at'] == pub['hot_card_first_published_at'] == '2026-10-17T05:00:00+00:00'
    assert pub['first_published_at'] != '2999-01-01T00:00:00Z'
    private = ws.detail('news', old_ids[0])
    assert private['draft']['note'] == saved_private['draft']['note']
    assert private['english']['state'] == 'stale' and private['draft_version'] > saved_private['draft_version']
    assert private['draft']['hot_card']['featured_rank'] == private['published']['hot_card']['featured_rank'] == 2
    assert 'PRIVATE-PENDING-EDIT' not in json.dumps(after)
    for ident in old_ids:
        prior = next(i for i in before['items'] if i['id'] == ident)
        current = next(i for i in after['items'] if i['id'] == ident)
        assert current.get('publication') == prior.get('publication')
        assert current['hot_card']['revision'] == prior['hot_card']['revision']
        assert current['hot_card']['share'] == prior['hot_card']['share']
        assert locale.status('news', ws.detail('news', ident)['published'])['state'] == 'reviewed'
    with pytest.raises(Exception, match='Draft changed'):
        ws.publish('news', old_ids[1], {**stale, 'confirmed': True, 'reason': 'Old preview must fail'})
    assert client.get('/news/' + old_ids[-1]).status_code == 200
    assert client.get('/api/v1/platform/reading?view=hot-cards').json['news']['total'] == sum(bool(i.get('hot_card')) for i in before['items']) + 1


def test_failed_stale_or_invalid_preview_leaves_every_row_unchanged(client, fourth, monkeypatch):
    before = public(client)
    rows = {i: ws.detail('news', i) for i in [fourth, *before['hot_card_selection']['ids']]}
    preview = ws.preview('news', fourth)
    with pytest.raises(Exception, match='Preview is out of date'):
        ws.publish('news', fourth, {**preview, 'review_token': 'stale', 'confirmed': True, 'reason': 'Stale preview'})
    with monkeypatch.context() as m:
        def fail(*args): raise RuntimeError('Atomic failure')
        m.setattr(ws, 'execute_statements', fail)
        with pytest.raises(RuntimeError, match='Atomic failure'):
            ws.publish('news', fourth, {**preview, 'confirmed': True, 'reason': 'Transaction failure'})
    assert public(client) == before
    for ident, original in rows.items(): assert ws.detail('news', ident) == original
    current = ws.detail('news', fourth)
    current['draft']['hot_card']['share']['zh']['sha256'] = '0' * 64
    ws.save('news', fourth, current)
    approve_fixture('news', fourth)
    assert not ws.preview('news', fourth)['ready']
    assert public(client) == before


def test_copy_check_layout_do_not_promote_old_card_and_withdraw_is_distinct(client, fourth):
    before = public(client)
    old_ids = before['hot_card_selection']['ids']
    publish(fourth)
    ident = old_ids[-1]
    original = ws.detail('news', ident)
    current = copy.deepcopy(original)
    current['draft']['summary'] = 'Copy clarification only; not a new card event.'
    current['draft']['publication'] = {'hot_card_selected_at': '2999-01-01T00:00:00Z'}
    ws.save('news', ident, current)
    approve_fixture('news', ident)
    result = publish(ident)
    assert not result['hot_card_rotation']['changed']
    assert result['published']['hot_card']['featured_rank'] == 0
    assert result['published']['publication'].get('hot_card_selected_at') == original['published'].get('publication', {}).get('hot_card_selected_at')
    current = ws.detail('news', fourth)
    result = ws.publish('news', fourth, {'draft_version': current['draft_version'], 'reason': 'Isolated withdrawal'}, True)
    assert result['hot_card_rotation']['status'] == 'withdrawn' and not result['hot_card_rotation']['index_only']
    assert client.get('/news/' + fourth).status_code == 404
    assert client.get('/api/v1/platform/reading?view=hot-cards').json['news']['total'] == sum(bool(i.get('hot_card')) for i in before['items'])


def test_home_html_http_mcp_share_one_complete_selection(site, fourth):
    baseline = sum(bool(i.get('hot_card')) for i in public(site)['items'])
    publish(fourth)
    for lang in ('zh', 'en'):
        data = site.get('/api/v1/platform/news?lang=' + lang).json
        reading = site.get('/api/v1/platform/reading?view=home&lang=' + lang).json
        assert data['hot_card_selection'] == reading['news']['hot_card_selection']
        assert data['hot_card_selection']['ids'] == reading['home_preview']['hot_cards']
        prefix = '/en' if lang == 'en' else ''
        page = site.get(prefix + '/for-you')
        section = BeautifulSoup(page.data, 'html.parser').find(id='hot-information-cards')
        assert [a['href'].split('/news/')[-1].split('#')[0] for a in section.select('h3 a')] == data['hot_card_selection']['ids']
        index = site.get(prefix + '/for-you/hot-cards')
        for item in data['items']:
            if item.get('hot_card'): assert item['id'].encode() in index.data
        rpc = site.post('/api/mcp/curated', headers=MCP, json={'jsonrpc':'2.0','id':1,'method':'tools/call',
            'params':{'name':'curated_news','arguments':{'lang':lang}}}).json['result']
        assert rpc['structuredContent'] == data
        assert len([i for i in data['items'] if i.get('hot_card')]) == baseline + 1


def test_handoff_never_invents_checks_and_preserves_same_batch_proposals():
    now = datetime.fromisoformat('2026-10-17T05:00:00+00:00')
    item = {'id':'D-01','sources':[{'url':'https://example.org/official'}],
            'hot_card':{'revision':'abc','status':'current','update_note':'','featured_rank':1}}
    news = {'revision':'r1','items':[item]}
    first = handoff.build(news, '2026-10-17', now=now)
    assert first['coverage']['incomplete'] == 1 and not first['publication'] and not first['atomic_rotation_available']
    first.update(proposals=[{'label':'卡1','copy':'Complete private copy'}], decisions=[{'label':'卡1','decision':'selected'}])
    check = {'id':'D-01','checked_at':now.isoformat(),'evidence_fingerprint':handoff.evidence_fingerprint(item),
             'outcome':'keep','reason':'Compared named version and limits in the official source','sources':['https://example.org/official']}
    checked = handoff.build(news, '2026-10-17', [check], first, now)
    assert checked['coverage']['keep'] == 1 and checked['proposals'] == first['proposals'] and checked['decisions'] == first['decisions']
    changed = copy.deepcopy(news);changed['items'][0]['hot_card']['revision'] = 'new'
    renewed = handoff.build(changed, '2026-10-17', previous=checked, now=now)
    assert renewed['coverage']['incomplete'] == 1 and renewed['proposals'] == checked['proposals']
    with pytest.raises(ValueError): handoff.build(changed, '2026-10-17', [check], now=now)
    for bad in ({'reason':''}, {'sources':[]}, {'checked_at':'2026-10-18T05:00:00+00:00'}):
        with pytest.raises(ValueError): handoff.build(news, '2026-10-17', [{**check, **bad}], now=now)


def test_card_and_news_decisions_are_separate_on_the_same_event(client, fourth):
    from backend.knowledge import editorial_batches as batches
    batch = batches.create({})['id']
    selected = ws.detail('news', fourth)
    card = copy.deepcopy(selected['draft']['hot_card'])
    ordinary = batches.propose(batch, {'event_url':'https://example.org/same-event', 'event_version':'v1', 'fingerprint':'news-evidence',
        'proposal':{'title':'Ordinary update','reason':'Concrete verified product change'}})['id']
    card_topic = batches.propose(batch, {'event_url':'https://example.org/same-event', 'event_version':'v1', 'fingerprint':'card-evidence',
        'proposal':{'type':'hot_card','title':'Card1','reason':'Actionable reader interpretation','card':card}})['id']
    assert ordinary != card_topic
    def topic(ident): return next(t for t in batches.detail(batch)['items'] if t['id'] == ident)
    for ident in (ordinary, card_topic):
        batches.decide(ident, {'version':topic(ident)['version'], 'decision':'continue'})
        batches.attach(ident, {'version':topic(ident)['version'], 'kind':'news', 'target_id':fourth})
    selected['draft'].pop('hot_card')
    ws.save('news', fourth, selected);approve_fixture('news', fourth);publish(fourth)
    assert topic(ordinary)['decision'] == 'published' and topic(card_topic)['decision'] == 'continue'
    current = ws.detail('news', fourth);current['draft']['hot_card'] = card
    ws.save('news', fourth, current)
    fields = samples()[0]['translations']['en']['fields']
    saved = ws.detail('news', fourth)
    ws.english_review('news', fourth, {'draft_version':saved['draft_version'],'source_hash':saved['english']['source_hash'],
        'fields':{k:fields[k] for k in saved['english']['fields']},'confirmed':True,'reason':'Exact approved isolated card translation'})
    publish(fourth)
    assert topic(card_topic)['decision'] == 'published'


def test_rotation_keeps_a_partially_removed_private_card_draft(client, fourth):
    ident = public(client)['hot_card_selection']['ids'][0]
    current = ws.detail('news', ident)
    current['draft']['hot_card'] = None
    ws.save('news', ident, current)
    publish(fourth)
    after = ws.detail('news', ident)
    assert after['draft']['hot_card'] is None
    assert after['published']['hot_card']['featured_rank'] == 2
