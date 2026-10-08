import copy
import json
from pathlib import Path
import pytest
from test_knowledge import client
from backend.knowledge import model_landscape as charts


def test_public_snapshot_has_reproducible_independent_metrics(client):
    response = client.get('/api/v1/platform/model-landscape')
    assert response.status_code == 200
    body = response.json
    assert [len(s['points']) for s in body['sources']] == [161, 94]
    aa, arena = body['sources']
    assert aa['price_unit'] == 'usd_per_task'
    assert arena['source_updated_at'] == '2026-10-02'
    assert aa['source_updated_at'] is None
    assert arena['points'][0]['score_low'] < arena['points'][0]['score'] < arena['points'][0]['score_high']
    assert 'v4.3' in aa['score_label']
    assert 'Style Control' in arena['score_label']
    assert aa['coverage']['released_2026'] == 313 and arena['coverage']['released_2026'] == 108
    assert len(aa['not_plotted']) == 152 and len(arena['not_plotted']) == 14
    assert len(arena['undated']) == 183
    assert all(p['release_date'].startswith('2026-') for s in body['sources'] for p in s['points'])
    assert set(p['organization'] for p in aa['points']) == set(body['companies'])


@pytest.mark.parametrize('mutate', [
    lambda d: d['sources'][0]['points'][0].update(price=0),
    lambda d: d['sources'][0]['points'][0].update(date_url='https://huggingface.co.evil.example/model'),
    lambda d: d['sources'][0]['points'][0].update(date_url='https://user@huggingface.co/model'),
    lambda d: d['sources'][0]['points'][0].update(score=float('nan')),
    lambda d: d['sources'][0]['points'][0].update(score_url='https://127.0.0.1/private'),
    lambda d: d['sources'][0].update(source_updated_at='2099-01-01'),
    lambda d: d['sources'][1]['points'][0].update(score_low=2000),
    lambda d: d['sources'][0]['points'][0].update(release_date='2025-12-31'),
    lambda d: d['sources'][0]['points'][0].update(release_date=None),
    lambda d: d['sources'][0]['points'][0].update(organization='Unknown'),
    lambda d: d['sources'][0]['coverage'].update(released_2026=999),
    lambda d: d['sources'][0]['not_plotted'][0].update(missing=[]),
    lambda d: d['sources'][1]['undated'][0].update(release_date='2026-01-01'),
])
def test_invalid_data_not_published(tmp_path, monkeypatch, mutate):
    data=copy.deepcopy(charts.snapshot());mutate(data)
    path=tmp_path/'charts.json';path.write_text(json.dumps(data));monkeypatch.setattr(charts,'CONTENT_PATH',path)
    with pytest.raises((AssertionError,ValueError)):
        charts.snapshot()


def test_source_checks_do_not_publish_or_refresh_dates(monkeypatch):
    original=charts.CONTENT_PATH.read_bytes()
    class Response:
        def __init__(self,url): self.status_code=403 if 'arena.ai' in url else 200
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def iter_bytes(self): yield b'<html>intelligence</html>'
    seen=[]
    def fetch(method,url,**kwargs):
        seen.append(url);assert kwargs['follow_redirects'] is False;assert 'Authorization' not in kwargs['headers'];return Response(url)
    monkeypatch.setattr(charts.httpx,'stream',fetch)
    result=charts.check_sources(record=False)
    assert result['status']=='partial'
    assert any(r.get('http_status')==403 for r in result['results'])
    assert any(r['status']=='available_review_required' for r in result['results'])
    assert len(seen)==2
    assert charts.CONTENT_PATH.read_bytes()==original


def test_source_names_and_missing_coordinates_remain_explicit():
    aa, arena = charts.snapshot()['sources']
    assert any(p['name'] == 'DeepSeek V4.1 Flash (max)' for p in aa['points'])
    assert any(p['name'] == 'gpt-5.5-instant' and p['release_date'] == '2026-05-05' for p in arena['points'])
    assert any(p['organization'] == 'Kimi' and p['source_organization'] == 'Moonshot' for p in arena['points'])
    for source in (aa, arena):
        for point in source['not_plotted']:
            assert point['score'] is None or point['price'] is None or point['price'] <= 0
        assert all(p['release_date'] is None for p in source['undated'])


def test_candidate_parser_and_company_aliases_do_not_invent_numbers():
    from scripts.maintenance.prepare_model_landscape import objects, number, company
    stream = '1:' + json.dumps({'name':'original-name', 'price':'$undefined'}) + '\n'
    html = '<script>self.__next_f.push(' + json.dumps([1, stream]) + ')</script>'
    assert objects(html) == [{'name':'original-name', 'price':'$undefined'}]
    assert number('$undefined') is None and number(float('nan')) is None and number(True) is None
    assert number(0) == 0  # kept as missing log coordinate, never changed to a tiny fake cost
    assert [company(x) for x in ['Moonshot', 'SpaceXAI', 'Z AI', 'Alibaba', 'Xiaomi', 'NVIDIA']] == ['Kimi', 'xAI', 'GLM', 'Qwen', 'MIMO', '其他']


def test_flagships_are_reviewed_series_not_per_company_score_winners():
    aa, arena = charts.snapshot()['sources']
    assert len(aa['points']) == 161 and len(arena['points']) == 94
    assert sum(m['status']=='plotted' for m in aa['flagship']['models']) == 11
    assert sum(m['status']=='plotted' for m in arena['flagship']['models']) == 9
    chosen = {m['company']:m for m in arena['flagship']['models']}
    assert chosen['OpenAI']['status']=='missing_coordinates' and chosen['OpenAI']['id']=='gpt-6-astra-max-text'
    assert chosen['Meta']['status']=='plotted' and chosen['Meta']['id']=='muse-spark-1-3-max-bhma-text'
    assert chosen['Kimi']['status']=='missing_coordinates'
    assert chosen['Google']['status']=='plotted' and chosen['Google']['id']=='barium-bb-wlqc-text'
    # New selected flagship series remains selected even when an older model scored higher.
    assert chosen['Anthropic']['status']=='plotted' and chosen['Anthropic']['family']=='Claude Opus 5.5'
    assert chosen['xAI']['status']=='plotted' and chosen['xAI']['family']=='Grok 4.7'
    assert len({m['company'] for m in aa['flagship']['models']}) == 11


@pytest.mark.parametrize('value,expected', [
    (1.0564, 1.0564), ({'cost': {'total': .071}}, .071),
    (0, 0), (None, None), (True, None), (float('nan'), None),
    ('$undefined', None), ({'cost': None}, None), ({'cost': {}}, None),
    ({'price1mInputTokens': 2}, None),
])
def test_task_cost_handles_both_source_formats_without_token_price_substitution(value, expected):
    from scripts.maintenance.prepare_model_landscape import task_cost
    assert task_cost(value) == expected


def test_source_release_mapping_and_missing_metrics_are_not_guessed():
    from scripts.maintenance.prepare_model_landscape import build
    def html(obj):
        return '<script>self.__next_f.push('+json.dumps([1,'1:'+json.dumps(obj)+'\n'])+')</script>'
    releases=[dict(slug='release',name='Family',releaseDate='2026-01-01',creator={'name':'Google'})]
    configs=[dict(slug='variant-'+str(i),name='Config '+str(i),releaseSlug='release') for i in range(202)]
    metrics=[dict(slug=c['slug'],name=c['name'],shortName=c['name'],modelCreatorName='Google',intelligenceIndex=10,intelligenceIndexCostPerTask=1) for c in configs[:-1]]
    arena=html(dict(leaderboardSlug='overall',params={'styleControl':True},entries=[],voteCutoffISOString='2026-01-01T00:00:00Z'))
    result=build(html([*releases,*configs,*metrics]),arena,{},'2026-10-02')['sources'][0]
    assert result['coverage']['source_models']==202
    assert len(result['points'])==201 and len(result['not_plotted'])==1
    assert all(p['release_date']=='2026-01-01' and p['date_basis']=='matched_model_release' for p in result['points'])
    missing=result['not_plotted'][0]
    assert missing['id']=='variant-201' and missing['price'] is None and missing['score'] is None
    assert missing['missing']==['missing_score','missing_price']
    assert result['points'][0]['configuration'].startswith('Config ')
    configs[0]['releaseSlug']='unknown-release'
    with pytest.raises(ValueError,match='Missing AA release metadata'):
        build(html([*releases,*configs,*metrics]),arena,{},'2026-10-02')


@pytest.mark.parametrize('url', [
    'https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-argon/',
    'https://www.anthropic.com/claude-sonnet-5-5',
])
def test_official_launch_dates_accept_exact_reviewed_hosts(url):
    data=copy.deepcopy(charts.snapshot())
    data['sources'][1]['points'][0].update(date_url=url,date_basis='official_release')
    assert charts.build_snapshot(data,None)['sources'][1]['points'][0]['date_url']==url


@pytest.mark.parametrize('url', [
    'https://blog.google.evil.example/launch',
    'https://www.anthropic.com.evil.example/launch',
    'https://user@blog.google/launch',
    'http://www.anthropic.com/launch',
    'https://blog.google:8443/launch',
])
def test_official_launch_date_hosts_do_not_accept_lookalikes_or_unsafe_urls(url):
    data=copy.deepcopy(charts.snapshot())
    data['sources'][1]['points'][0]['date_url']=url
    with pytest.raises(AssertionError):charts.build_snapshot(data,None)
