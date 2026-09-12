"""Small reviewed chart snapshots. Source checks never publish or rewrite them."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import time
from urllib.parse import urlsplit
import httpx

CONTENT_PATH = Path(__file__).parent / 'content' / 'model-landscape.json'
HOSTS = {'artificialanalysis.ai', 'arena.ai'}


def snapshot():
    from backend.knowledge.content_workspace import load_published
    raw = load_published('charts', None)
    if raw is None:
        raw = {'landscape':json.loads(CONTENT_PATH.read_text()), 'flagships':None}
    return build_snapshot(raw['landscape'], raw['flagships'])


def build_snapshot(data, catalog):
    # Editable private drafts must not expand the public field contract.
    data = json.loads(json.dumps(data))
    top=('schema_version','revision','year','interval_days','companies','sources')
    source_fields=('checked_at','coverage','id','name','not_plotted','note','note_en','points','price_label','price_label_en','price_unit','score_label','source_sha256','source_updated_at','source_url','undated')
    point_fields=('configuration','configuration_en','date_basis','date_url','deprecated','estimated','id','missing','model_url','name','organization','price','price_url','release_date','score','score_high','score_low','score_url','source_organization','votes')
    coverage_fields=('missing_coordinates','outside_year','plotted','released_2026','source_models','unconfirmed_date')
    data={k:v for k,v in data.items() if k in top}
    data['sources']=[{k:v for k,v in s.items() if k in source_fields} for s in data['sources']]
    for source in data['sources']:
        source['coverage']={k:v for k,v in source['coverage'].items() if k in coverage_fields}
        for group in ('points','not_plotted','undated'):
            source[group]=[{k:v for k,v in p.items() if k in point_fields} for p in source[group]]
    assert data['schema_version'] == 'fieldtofit.model-landscape.v1'
    assert [s['id'] for s in data['sources']] == ['artificial-analysis', 'arena']
    assert data['year'] == 2026
    companies = ['OpenAI', 'Anthropic', 'Google', 'xAI', 'Meta', 'Kimi', 'GLM', 'Qwen', 'MIMO', 'MiniMax', 'DeepSeek', '其他']
    assert data['companies'] == companies
    for source in data['sources']:
        checked = date.fromisoformat(source['checked_at'])
        if source['source_updated_at']:
            assert date.fromisoformat(source['source_updated_at']) <= checked
        assert source['price_unit'] == ('usd_per_task' if source['id'] == 'artificial-analysis' else 'usd_per_million_output_tokens')
        points = source['points']; missing = source['not_plotted']; undated = source['undated']
        rows = points + missing + undated
        assert points and len({p['id'] for p in rows}) == len(rows)
        def finite(value):
            return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
        for point in rows:
            assert point['name'] and point['organization'] in companies and point['configuration']
            assert point['score'] is None or finite(point['score'])
            assert point['price'] is None or finite(point['price'])
            if point['release_date'] is not None:
                day = date.fromisoformat(point['release_date'])
                assert day.year == data['year'] and day <= checked
                assert point['date_basis'] in {'source_release_date', 'matched_model_release', 'source_version_date', 'official_release'}
                parsed = urlsplit(point['date_url'])
                assert parsed.scheme == 'https' and parsed.hostname in HOSTS | {'openai.com', 'ernie.baidu.com', 'help.aliyun.com'} and not parsed.username and not parsed.password and parsed.port in (None, 443)
            if 'score_low' in point:
                assert finite(point['score_low']) and finite(point['score_high'])
                assert point['score_low'] <= point['score'] <= point['score_high']
        for point in points:
            assert point['release_date'] and finite(point['score']) and finite(point['price']) and point['price'] > 0
        for point in missing:
            expected = []
            if point['score'] is None: expected.append('missing_score')
            if point['price'] is None: expected.append('missing_price')
            elif point['price'] <= 0: expected.append('nonpositive_price')
            assert point['release_date'] and expected and point['missing'] == expected
        assert all(p['release_date'] is None for p in undated)
        coverage = source['coverage']
        assert coverage['plotted'] == len(points) and coverage['missing_coordinates'] == len(missing)
        assert coverage['released_2026'] == len(points) + len(missing)
        assert coverage['unconfirmed_date'] == len(undated)
        assert coverage['source_models'] == coverage['released_2026'] + coverage['outside_year'] + len(undated)
        for url in [source['source_url']] + [p[k] for p in rows for k in ('score_url', 'price_url')]:
            parsed = urlsplit(url)
            assert parsed.scheme == 'https' and parsed.hostname in HOSTS and not parsed.username and not parsed.password and parsed.port in (None, 443)
    if catalog is None:catalog=json.loads((CONTENT_PATH.parent / 'model-landscape-flagships.json').read_text())
    assert date.fromisoformat(catalog['reviewed_at']) <= date.today()
    assert [m['company'] for m in catalog['models']] == companies[:-1]
    for source in data['sources']:
        rows = {p['id']:p for p in source['points'] + source['not_plotted'] + source['undated']}
        plotted = {p['id'] for p in source['points']}
        selections = []
        for model in catalog['models']:
            ident = model['ids'][source['id']]
            if ident is not None:
                assert ident in rows and rows[ident]['organization'] == model['company']
            url = urlsplit(model['evidence_url'])
            assert url.scheme == 'https' and url.hostname in HOSTS and not url.username and not url.password and url.port in (None, 443)
            selections.append({'company':model['company'], 'family':model['family'], 'id':ident,
                               'evidence_url':model['evidence_url'],
                               'status':'plotted' if ident in plotted else 'missing_coordinates' if ident in rows and rows[ident]['release_date'] else 'unconfirmed_date' if ident in rows else 'not_listed'})
        source['flagship'] = {'reviewed_at':catalog['reviewed_at'], 'policy':catalog['policy'], 'policy_en':catalog['policy_en'], 'models':selections}
    return data


def check_sources(record=True):
    """Daily reachability/content-change signals; editorial review remains required.

    Bounded public GETs, no credentials, redirects, model calls or automatic publishing.
    A 200 response is NOT a verification of chart values or a new source update date.
    """
    from backend.knowledge.store import now
    data = snapshot()
    entries = [(s['id'], s['source_url']) for s in data['sources']]
    def check(entry):
        ident, url = entry
        result = {'source': ident, 'url': url, 'checked_at': now()}
        start = time.monotonic()
        try:
            with httpx.stream('GET', url, timeout=5, follow_redirects=False, headers={'User-Agent':'FieldToFit-source-check/1.0'}) as response:
                if response.status_code != 200:
                    return result | {'status':'unavailable', 'http_status':response.status_code}
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > 4_000_000 or time.monotonic()-start > 8:
                        return result | {'status':'incomplete'}
            lower = bytes(body).lower()
            marker = {'artificial-analysis':b'intelligence', 'arena':b'text arena'}[ident]
            if marker not in lower or b'<title>just a moment' in lower:
                return result | {'status':'unreadable'}
            return result | {'status':'available_review_required', 'page_sha256':hashlib.sha256(body).hexdigest()}
        except (httpx.HTTPError, OSError):
            return result | {'status':'unavailable'}
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(check, entries))
    report = {'status':'success' if all(r['status']=='available_review_required' for r in results) else 'partial',
              'interval_days':1, 'snapshot_revision':data['revision'], 'results':results,
              'scope':'Public source availability only. Review scores, configuration, price and source dates before publishing a new version; snapshot unchanged.'}
    if record:
        from backend.knowledge.operations import track_run
        with track_run('model_landscape_daily') as stored:
            stored.update(report)
    return report
