"""Reading projection and invalidation against isolated publications, never live data."""
import copy
import json
import re

import pytest
from test_knowledge import client
from test_content_workspace import migrate, make, valid, publish, call
from test_search_pages import site
from backend.knowledge import reading
from backend.db import get_db

PATH = '/api/v1/platform/reading'


def test_summary_preserves_default_reading_and_full_search(client):
    full = {k: client.get('/api/v1/platform/'+k).json for k in ('news','watch','model-landscape')}
    response = client.get(PATH)
    assert response.status_code == 200, response.json
    data = response.json
    assert data['news']['revision'] == full['news']['revision']
    assert data['watch']['revision'] == full['watch']['revision']
    assert data['news']['codex_progress'] == full['news']['codex_progress']
    assert data['charts'] == full['model-landscape']
    for original, slim in zip(full['news']['items'], data['news']['items']):
        assert slim == {**{k:v for k,v in original.items() if k not in ('materials','materials_revision','maintenance','technical_map','interpretation')}, 'interpretation':original['interpretation'] if original.get('codex_28_days') else original['interpretation'][:1] if original.get('highlight') else [], **({'reading_summary':True} if not original.get('codex_28_days') else {}), **({'technical_map':slim['technical_map']} if 'technical_map' in slim else {})}
    for original, slim in zip(full['watch']['items'],data['watch']['items']):
        for key in ('id','name','introduction','sources','overview'):
            assert slim.get(key) == original.get(key)
        assert slim['interpretation'] == original['interpretation'][:2]
        assert 'blocks' not in slim and 'materials' not in slim
    for q in ('GPT','runtime','CW-T01','Docker','部署'):
        full_ids = [i['id'] for i in client.get('/api/v1/platform/watch',query_string={'q':q}).json['items']]
        slim_ids = [i['id'] for i in client.get(PATH,query_string={'q':q}).json['watch']['items']]
        assert slim_ids == full_ids
    assert len(response.data) < sum(len(client.get('/api/v1/platform/'+k).data) for k in full)*.5


def test_warm_cache_validates_dependencies_and_never_poisoned(client, monkeypatch):
    migrate(client)
    first = client.get(PATH).json
    real = reading.build
    calls=[]
    monkeypatch.setattr(reading,'build',lambda *args: (calls.append(True),real(*args))[1])
    assert client.get(PATH).json == first
    assert client.get(PATH,query_string={'after':first['revision']}).json == {'revision':first['revision'],'unchanged':True}
    assert calls == []
    with client.application.test_request_context(PATH):
        value = reading.overview();value['news']['items'].clear()
    assert client.get(PATH).json == first
    def broken(): raise RuntimeError('PRIVATE DATABASE ERROR')
    monkeypatch.setattr(reading,'dependencies',broken)
    response=client.get(PATH)
    assert response.status_code==503 and 'PRIVATE' not in response.text and 'items' not in response.json


@pytest.mark.parametrize('kind', ['news','watch'])
def test_publish_draft_withdraw_and_material_revision_invalidate(client,kind):
    migrate(client)
    initial=client.get(PATH).json
    ident,_=make(client,kind);draft=valid(client,kind,ident)
    assert client.get(PATH).json==initial
    published=publish(client,kind,ident)
    new=client.get(PATH).json
    assert new['revision']!=initial['revision']
    assert ident in [i['id'] for i in new[kind]['items']]
    d=call(client,f'/content/{kind}/{ident}',method='get').json
    d['draft']['private_note']='SECRET';call(client,f'/content/{kind}/{ident}',d,'patch')
    assert client.get(PATH).json==new
    result=call(client,f'/content/{kind}/{ident}/withdraw',{'draft_version':d['draft_version']+1,'reason':'Isolated withdrawal'})
    assert result.status_code==200,result.json
    withdrawn=client.get(PATH).json
    assert withdrawn['revision']!=new['revision']
    assert ident not in [i[0] for i in withdrawn['safety']['items']]
    assert client.get('/api/v1/platform/'+kind+'?id='+ident).status_code==404


def test_auxiliary_dependency_changes_invalidate_cached_reading(client):
    migrate(client)
    before=client.get(PATH).json
    with get_db() as db:
        db.execute('INSERT INTO fieldtofit_steward_aliases VALUES(?,?,?)',('D-999','D-01','test'))
    after=client.get(PATH).json
    assert before['revision']!=after['revision']
    assert after['safety']['aliases']!=before['safety']['aliases']
    # Raw published snapshot + revision represent an already reviewed material withdrawal.
    with get_db() as db:
        raw=json.loads(db.execute("SELECT published_json FROM fieldtofit_content_sets WHERE kind='watch'").fetchone()[0])
        item=next(i for i in raw['items'] if i.get('reading_materials'))
        material=item['reading_materials'][0]
        material.update(coverage='withdrawn',body='',reason='Withdrawn in isolated fixture')
        db.execute("UPDATE fieldtofit_content_sets SET published_json=?,revision=revision+1 WHERE kind='watch'",(json.dumps(raw),))
    latest=client.get(PATH).json
    assert latest['revision']!=after['revision']
    row=next(i for i in latest['safety']['items'] if i[0]==item['id'])
    assert row[2][0][2]=='withdrawn'


def test_bootstrap_matches_api_and_escapes_untrusted_json(site,monkeypatch):
    response=site.get('/for-you?q=GPT&type=model')
    assert response.status_code==200
    match=re.search(r'<script type="application/json" id="fieldtofit-reading">(.*?)</script>',response.text,re.S)
    boot=json.loads(match[1]);assert boot['language']=='zh'
    assert boot['view']=='home'
    assert boot['data']==site.get(PATH+'?view=home').json
    assert '/for-you/watch?q=GPT&amp;type=model' in response.text
    assert 'reading_revision;dur=' in response.headers['Server-Timing']
    from backend import seo
    with site.application.test_request_context('/for-you'):
        value=seo.document(__import__('backend.api.main',fromlist=['CLIENT_DIST']).CLIENT_DIST,'x','y','/for-you',bootstrap={'test':'</script><script>alert(1)</script>&\u2028'})
    assert '<script>alert(1)</script>' not in value.get_data(as_text=True)
    escaped=re.search(r'id="fieldtofit-reading">(.*?)</script>',value.get_data(as_text=True),re.S)[1]
    assert json.loads(escaped)['test'].startswith('</script>')
    monkeypatch.setenv('FIELDTOFIT_READ_TOKEN','isolated-token')
    assert site.get(PATH).status_code==401
    protected=site.get('/for-you')
    assert protected.status_code==401 and 'fieldtofit-reading' not in protected.text


def test_english_projection_cache_is_separate_and_search_equivalent(client):
    zh=client.get(PATH).json
    en=client.get(PATH+'?lang=en')
    assert en.status_code==200,en.json
    assert en.json['news']['revision']==zh['news']['revision']
    assert en.json['news']['items'][0]['summary']!=zh['news']['items'][0]['summary']
    assert client.get(PATH).json==zh
    for q in ('runtime','reasoning','GPT'):
        expected=client.get('/api/v1/platform/watch',query_string={'lang':'en','q':q}).json
        actual=client.get(PATH,query_string={'lang':'en','q':q}).json
        assert [i['id'] for i in actual['watch']['items']]==[i['id'] for i in expected['items']]


def test_warm_english_html_reuses_reviewed_projection_without_body_reads(site,monkeypatch):
    from backend.knowledge import locale
    first=site.get('/en/for-you')
    assert first.status_code==200
    actual=reading.dependencies;checks=[]
    def dependencies():
        checks.append(True)
        return actual()
    def unexpected_body_read():
        raise AssertionError('A warm homepage must not reload translation bodies')
    monkeypatch.setattr(reading,'dependencies',dependencies)
    monkeypatch.setattr(locale,'public_fields',unexpected_body_read)
    warm=site.get('/en/for-you')
    assert warm.status_code==200 and warm.data==first.data
    assert checks==[True]


def test_concurrent_publication_never_caches_mixed_projection(client,monkeypatch):
    reading._CACHE.clear()
    actual=reading.dependencies;calls=[]
    def changing():
        revision,dep=actual();calls.append(True)
        return revision+str(len(calls)),dep
    monkeypatch.setattr(reading,'dependencies',changing)
    response=client.get(PATH)
    assert response.status_code==503 and len(calls)==4
    assert not reading._CACHE


def test_changed_english_review_has_explicit_error_not_old_projection(client):
    migrate(client)
    before=client.get(PATH+'?lang=en').json
    with get_db() as db:
        raw=json.loads(db.execute("SELECT published_json FROM fieldtofit_content_sets WHERE kind='watch'").fetchone()[0])
        raw['items'][0]['introduction']='新增但尚未审核英文的隔离测试文本'
        db.execute("UPDATE fieldtofit_content_sets SET published_json=?,revision=revision+1 WHERE kind='watch'",(json.dumps(raw),))
    failed=client.get(PATH,query_string={'lang':'en','after':before['revision']})
    assert failed.status_code==503 and failed.json['code']=='english_unavailable'
    assert 'items' not in failed.json


def test_failed_final_dependency_check_discards_new_projection(client,monkeypatch):
    reading._CACHE.clear()
    actual=reading.dependencies;calls=[]
    def unstable():
        calls.append(True)
        if len(calls)>1:raise RuntimeError('PRIVATE CONNECTION ERROR')
        return actual()
    monkeypatch.setattr(reading,'dependencies',unstable)
    response=client.get(PATH)
    assert response.status_code==503 and response.json['code']=='reading_unavailable'
    assert 'PRIVATE' not in response.text and not reading._CACHE


def test_current_public_maintenance_remains_visible_and_invalidates(client):
    migrate(client)
    before=client.get(PATH).json
    full=client.get('/api/v1/platform/watch?id=CW-M01').json['items'][0]
    material=full['materials'][0]
    observation={'availability':'check_failed','needs_review':True,'last_checked_at':'2026-10-14','last_success_at':'','failure_days':1,'error':'Source unavailable','public_note':'Reviewed public note'}
    with get_db() as db:
        db.execute('INSERT INTO fieldtofit_steward_checks VALUES(?,?,?,?)',(full['id'],material['id'],material['url'],json.dumps(observation)))
    after=client.get(PATH).json
    assert after['revision']!=before['revision']
    slim=next(i for i in after['watch']['items'] if i['id']==full['id'])
    current=client.get('/api/v1/platform/watch?id=CW-M01').json['items'][0]
    assert slim['maintenance']==current['maintenance']
    assert slim['maintenance']['materials'][0]['needs_review'] is True
