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
HOSTS = {'artificialanalysis.ai', 'arena.ai', 'epoch.ai'}


def snapshot():
    data = json.loads(CONTENT_PATH.read_text())
    assert data['schema_version'] == 'fieldtofit.model-landscape.v1'
    assert [s['id'] for s in data['sources']] == ['artificial-analysis', 'arena', 'epoch']
    for source in data['sources']:
        date.fromisoformat(source['checked_at'])
        if source['source_updated_at']:
            assert date.fromisoformat(source['source_updated_at']) <= date.fromisoformat(source['checked_at'])
        assert source['price_unit'] in {'usd_per_task', 'usd_per_million_output_tokens'}
        assert source['points'] and len({p['name'] for p in source['points']}) == len(source['points'])
        for point in source['points']:
            assert all(isinstance(point[k], (int, float)) and not isinstance(point[k], bool) and math.isfinite(point[k]) for k in ('score', 'price'))
            assert point['price'] > 0 and point['configuration']
            if 'score_low' in point:
                assert point['score_low'] <= point['score'] <= point['score_high']
        for url in [source['source_url']] + [p[k] for p in source['points'] for k in ('score_url', 'price_url')]:
            parsed = urlsplit(url)
            assert parsed.scheme == 'https' and parsed.hostname in HOSTS and not parsed.username and not parsed.password and parsed.port in (None, 443)
    return data


def check_sources(record=True):
    """Daily reachability/content-change signals; editorial review remains required.

    Bounded public GETs, no credentials, redirects, model calls or automatic publishing.
    A 200 response is NOT a verification of chart values or a new source update date.
    """
    from backend.knowledge.store import now
    data = snapshot()
    entries = [(s['id'], url) for s in data['sources'] for url in sorted({s['source_url']} | {p['score_url'] for p in s['points']} | {p['price_url'] for p in s['points']})]
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
            marker = {'artificial-analysis':b'intelligence', 'arena':b'text arena', 'epoch':b'epoch capabilities index'}[ident]
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
