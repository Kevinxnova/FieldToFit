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
    assert [len(s['points']) for s in body['sources']] == [8, 8, 6]
    aa, arena, epoch = body['sources']
    assert aa['price_unit'] == 'usd_per_task'
    assert arena['source_updated_at'] == '2026-09-02'
    assert aa['source_updated_at'] is None and epoch['source_updated_at'] is None
    assert all(p['score_url'] == p['price_url'] for p in epoch['points'])
    assert arena['points'][0]['score_low'] < arena['points'][0]['score'] < arena['points'][0]['score_high']
    assert 'v4.3' in aa['score_label']


@pytest.mark.parametrize('mutate', [
    lambda d: d['sources'][0]['points'][0].update(price=0),
    lambda d: d['sources'][0]['points'][0].update(score=float('nan')),
    lambda d: d['sources'][0]['points'][0].update(score_url='https://127.0.0.1/private'),
    lambda d: d['sources'][0].update(source_updated_at='2099-01-01'),
    lambda d: d['sources'][1]['points'][0].update(score_low=2000),
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
        def iter_bytes(self): yield b'<html>intelligence epoch capabilities index</html>'
    seen=[]
    def fetch(method,url,**kwargs):
        seen.append(url);assert kwargs['follow_redirects'] is False;assert 'Authorization' not in kwargs['headers'];return Response(url)
    monkeypatch.setattr(charts.httpx,'stream',fetch)
    result=charts.check_sources(record=False)
    assert result['status']=='partial'
    assert any(r.get('http_status')==403 for r in result['results'])
    assert any(r['status']=='available_review_required' for r in result['results'])
    assert len(seen)==9
    assert charts.CONTENT_PATH.read_bytes()==original
