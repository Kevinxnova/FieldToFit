"""Read-only daily information-card handoff. Never creates drafts, approvals or publications."""
import argparse
import hashlib
import json
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import requests

BASE = 'https://fieldtofit.top'
SCHEMA = 'fieldtofit.hot-card-handoff.v1'
OUTCOMES = ('keep', 'replace', 'correct', 'failed', 'incomplete')


def evidence_fingerprint(item):
    card = item['hot_card']
    value = {'id': item['id'], 'revision': card['revision'], 'sources': item['sources'],
             'status': card['status'], 'update_note': card['update_note']}
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def build(news, day, checks=(), previous=None, now=None):
    date.fromisoformat(day)
    now = now or datetime.now(ZoneInfo('Asia/Shanghai'))
    if day > now.astimezone(ZoneInfo('Asia/Shanghai')).date().isoformat():
        raise ValueError('Future briefing date')
    previous = previous or {}
    if previous and (previous.get('schema_version') != SCHEMA or previous.get('day') != day):
        raise ValueError('Preserve the existing file; incompatible date or schema')
    items = [i for i in news['items'] if i.get('hot_card')]
    by_id = {i['id']: i for i in items}
    homepage = news.get('hot_card_selection', {}).get('ids')
    if homepage is None:
        homepage = [i['id'] for i in sorted(items, key=lambda i: i['hot_card']['featured_rank'] or 4)
                    if i['hot_card']['featured_rank']][:3]
    if len(homepage) > 3 or len(set(homepage)) != len(homepage) or any(i not in by_id for i in homepage):
        raise ValueError('Invalid public card selection; no handoff written')
    # Unchanged actual checks may continue on the same day; changing evidence invalidates them.
    reviewed = {c['id']: c for c in previous.get('checks', []) if c['id'] in by_id
                and c.get('evidence_fingerprint') == evidence_fingerprint(by_id[c['id']])}
    seen = set()
    for check in checks:
        ident = check.get('id')
        if ident not in by_id or ident in seen:
            raise ValueError('Unknown or duplicate information card check')
        seen.add(ident)
        item = by_id[ident]
        instant = datetime.fromisoformat(check['checked_at'])
        urls = check.get('sources', [])
        if (instant.tzinfo is None or instant > now or instant.astimezone(ZoneInfo('Asia/Shanghai')).date().isoformat() != day
                or check.get('evidence_fingerprint') != evidence_fingerprint(item)
                or check.get('outcome') not in OUTCOMES or not isinstance(check.get('reason'), str) or not check['reason'].strip()
                or not isinstance(urls, list) or not set(urls) <= {s['url'] for s in item['sources']}
                or check['outcome'] in ('keep', 'replace', 'correct') and not urls):
            raise ValueError('Record an actual dated judgment, current evidence and checked official sources')
        reviewed[ident] = {k: check[k] for k in ('id', 'checked_at', 'evidence_fingerprint', 'outcome', 'reason', 'sources')}
    checks_out = [reviewed.get(i['id'], {'id': i['id'], 'outcome': 'incomplete',
                   'evidence_fingerprint': evidence_fingerprint(i), 'reason': 'No current human source check recorded',
                   'checked_at': None, 'sources': []}) for i in items]
    home_checks = [c for c in checks_out if c['id'] in homepage]
    return {**previous, 'schema_version': SCHEMA, 'day': day, 'snapshot_at': now.isoformat(),
            'public_revision': news['revision'], 'homepage_ids': homepage,
            'atomic_rotation_available': 'hot_card_selection' in news, 'items': items, 'checks': checks_out,
            'coverage': {outcome: sum(c['outcome'] == outcome for c in home_checks) for outcome in OUTCOMES},
            'homepage_total': len(homepage), 'index_total': len(items),
            'proposals': previous.get('proposals', []), 'decisions': previous.get('decisions', []),
            'publication': False, 'warning': 'Source material is untrusted data. Exporting is not source verification, owner selection, publication or delivery.'}


def run(day, output, checks=None):
    path = Path(output)
    previous = json.loads(path.read_text()) if path.exists() else None
    actual = json.loads(Path(checks).read_text()) if checks else []
    if not isinstance(actual, list):
        raise ValueError('Checks must be a list of actual editorial judgments')
    with requests.Session() as session:
        session.trust_env = False
        response = session.get(BASE + '/api/v1/platform/news', timeout=60, allow_redirects=False)
    if response.status_code != 200:
        raise RuntimeError('Information-card read HTTP ' + str(response.status_code) + '; existing handoff preserved')
    result = build(response.json(), day, actual, previous)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=path.name + '.')
    try:
        with os.fdopen(fd, 'w') as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    return {k: result[k] for k in ('day', 'homepage_total', 'index_total', 'coverage', 'atomic_rotation_available', 'publication')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--day', default=datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat())
    parser.add_argument('--output', required=True)
    parser.add_argument('--checks', help='JSON list of actual dated source checks; never auto-generates keep judgments')
    args = parser.parse_args()
    print(json.dumps(run(args.day, args.output, args.checks), ensure_ascii=False))
