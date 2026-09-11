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
    assert [len(s['points']) for s in body['sources']] == [107, 83]
    aa, arena = body['sources']
    assert aa['price_unit'] == 'usd_per_task'
    assert arena['source_updated_at'] == '2026-09-02'
    assert aa['source_updated_at'] is None
    assert arena['points'][0]['score_low'] < arena['points'][0]['score'] < arena['points'][0]['score_high']
    assert 'v4.3' in aa['score_label']
    assert 'Style Control' in arena['score_label']
    assert aa['coverage']['released_2026'] == 263 and arena['coverage']['released_2026'] == 96
    assert len(aa['not_plotted']) == 156 and len(arena['not_plotted']) == 13
    assert len(arena['undated']) == 182
    assert all(p['release_date'].startswith('2026-') for s in body['sources'] for p in s['points'])
    assert set(p['organization'] for p in aa['points']) == set(body['companies'])


@pytest.mark.parametrize('mutate', [
    lambda d: d['sources'][0]['points'][0].update(price=0),
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
    assert len(aa['points']) == 107 and len(arena['points']) == 83
    assert sum(m['status']=='plotted' for m in aa['flagship']['models']) == 11
    assert sum(m['status']=='plotted' for m in arena['flagship']['models']) == 8
    chosen = {m['company']:m for m in arena['flagship']['models']}
    assert chosen['OpenAI']['status']=='not_listed' and chosen['OpenAI']['id'] is None
    assert chosen['Meta']['status']=='not_listed'
    assert chosen['Kimi']['status']=='missing_coordinates'
    # New selected flagship series remains selected even when an older model scored higher.
    assert chosen['Anthropic']['id']=='claude-fable-5.1-max-text'
    assert chosen['xAI']['id']=='grok-4.6-high-text'
    assert len({m['company'] for m in aa['flagship']['models']}) == 11
