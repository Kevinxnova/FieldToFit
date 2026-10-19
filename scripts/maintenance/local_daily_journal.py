#!/usr/bin/env python3
"""Local Codex handoff; no model API, direct database write, or cloud cron."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys

import requests
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from backend.daily_briefing import service
from backend.daily_briefing.schema import TZ, day_key, digest, project, validate
from backend.daily_briefing.schedule import PUBLISH_AT, local_time
from backend.daily_briefing.editorial import research_plan, validate_editorial

BASE = 'https://fieldtofit.top'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))
    temp.chmod(0o600)
    temp.replace(path)


@contextmanager
def locked(directory):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / '.lock').open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Another local journal phase is running') from None
        yield


class Website:
    def __init__(self, env_file):
        password = dotenv_values(env_file).get('ADMIN_PASSWORD')
        if not password:
            raise ValueError('Local ADMIN_PASSWORD is unavailable')
        self.session = requests.Session()
        self.session.trust_env = False
        self.password = password

    def call(self, path, data=None, binary=False, missing=False):
        if not path.startswith('/api/v1/') or '://' in path:
            raise ValueError('Only the FieldToFit API is permitted')
        headers = {'X-Admin-Password': self.password} if path.startswith('/api/v1/admin/') else {}
        try:
            response = self.session.request('POST' if data is not None else 'GET', BASE + path,
                headers=headers, json=data, timeout=150, allow_redirects=False)
        except requests.RequestException:
            raise RuntimeError('Website request incomplete; inspect remote state before retrying') from None
        if response.status_code == 404 and missing:
            return None
        if response.status_code != 200:
            raise RuntimeError('Journal API HTTP ' + str(response.status_code) + '; no blind write retry')
        return response.content if binary else response.json()


def load_bundle(directory, day, now):
    data = validate(json.loads((directory / 'issue.json').read_text()), now=now)
    if data['date'] != day or data['kind'] != 'daily' or day != now.astimezone(TZ).date().isoformat():
        raise ValueError('Automation accepts only the current Beijing daily edition')
    evidence = json.loads((directory / 'evidence.json').read_text())
    report = json.loads((directory / 'review.json').read_text())
    if evidence.get('date') != day or report.get('evidence_hash') != digest(evidence):
        raise ValueError('Evidence changed after editorial review')
    checks = evidence.get('source_checks', [])
    if not checks or any(not isinstance(c, dict) for c in checks):
        raise ValueError('Original-source checks are required')
    indexed = {c.get('source_id'): c for c in checks}
    for source in data['sources']:
        check = indexed.get(source['id'], {})
        if (check.get('url') != source['url'] or check.get('checked_at') != source['checked_at']
                or not isinstance(check.get('excerpt'), str) or len(check['excerpt'].strip()) < 20):
            raise ValueError('Each original source needs a dated quotation in the evidence file')
    service.local_review(report, data)
    validate_editorial(data, evidence, now)
    if any(c['state'] != 'checked' for c in data['coverage']):
        raise ValueError('All eleven dimensions require an actual check')
    if any(m['state'] == 'unavailable' or not any(r['state'] in ('verified','partial') for r in m['rows']) for m in data['markets']):
        raise ValueError('A complete market is missing; keep the previous edition')
    return data, report


def verify_public(site, directory, data):
    public = service._public_copy(data)
    expected = digest(public)
    publication = None
    pdfs = {}
    for lang in ('zh', 'en'):
        live = site.call('/api/v1/daily/' + data['date'] + '?lang=' + lang)
        if live['publication']['content_hash'] != expected:
            raise ValueError('Public edition differs from the reviewed copy')
        if any(live.get(k) != v for k, v in project(public, lang).items()):
            raise ValueError('Published language differs from the reviewed copy')
        if publication:
            for key in ('revision', 'content_hash', 'published_at'):
                if live['publication'][key] != publication[key]:
                    raise ValueError('Bilingual publication identity differs')
        publication = live['publication']
        meta = live['pdf'][lang]
        path = meta['url']
        if not path.startswith('/api/v1/daily/' + data['date'] + '/pdf?'):
            raise ValueError('Unexpected PDF URL')
        raw = site.call(path, binary=True)
        if not raw.startswith(b'%PDF-') or hashlib.sha256(raw).hexdigest() != meta['sha256']:
            raise ValueError('PDF does not match its publication receipt')
        (directory / ('published-' + lang + '.pdf')).write_bytes(raw)
        pdfs[lang] = {'sha256': meta['sha256'], 'pages': meta['pages']}
    receipt = {'date': data['date'], 'state': 'published', 'publication': publication,
               'pdfs': pdfs, 'verified_at': datetime.now(timezone.utc).isoformat()}
    write(directory / 'publication.json', receipt)
    return receipt


def check_layout(directory, data, pages):
    path=directory/'layout-review.json'
    if not path.exists():raise ValueError('Both PDF proofs need a recorded visual review')
    review=json.loads(path.read_text())
    if review.get('approved') is not True or review.get('content_hash')!=digest(data):
        raise ValueError('PDF visual review is stale')
    for lang in ('zh','en'):
        proof=directory/('proof-'+lang+'.pdf')
        entry=review.get('proofs',{}).get(lang,{})
        if (not proof.exists() or entry.get('sha256')!=hashlib.sha256(proof.read_bytes()).hexdigest()
                or entry.get('checked_pages')!=list(range(1,pages[lang]+1))):
            raise ValueError('Every page of both current PDF proofs must be reviewed')
    return {lang:review['proofs'][lang]['sha256'] for lang in ('zh','en')}


def run(phase, day, directory, site=None, now=None):
    day_key(day)
    now = now or datetime.now(timezone.utc)
    if phase == 'plan':
        return research_plan(day)
    if phase == 'status':
        status = site.call('/api/v1/admin/daily')
        result = {'date': day, 'local_gpt_supported': status['configuration'].get('local_gpt_supported', False),
                  'supported_layout_versions': status['configuration'].get('supported_layout_versions', [1]),
                  'cloud_pipeline_enabled': status['configuration']['enabled'],
                  'edition': site.call('/api/v1/admin/daily/' + day, missing=True)}
        write(directory / 'remote-status.json', result)
        return {k: v for k, v in result.items() if k != 'edition'} | {'edition_exists': result['edition'] is not None}
    with locked(directory):
        data, report = load_bundle(directory, day, now)
        if phase == 'validate':
            return {'date': day, 'state': 'validated', 'content_hash': digest(data)}
        status = site.call('/api/v1/admin/daily')
        if not status['configuration'].get('local_gpt_supported'):
            raise ValueError('Deploy local GPT support before sending an edition')
        remote = site.call('/api/v1/admin/daily/' + day, missing=True)
        if remote:
            receipt_path=directory/'draft-receipt.json'
            previous=json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
            owned=(remote['state']=='draft' and remote['published_revision'] is None
                   and previous.get('content_hash')==digest(remote['draft'])
                   and previous.get('draft_version')==remote['draft_version'])
            if remote['state']=='withdrawn' or (remote['draft']!=data and not (phase=='stage' and owned)):
                raise ValueError('An existing draft, correction or withdrawal requires owner inspection')
        if remote and remote['state'] == 'published':
            return verify_public(site, directory, data)
        layouts = status['configuration'].get('supported_layout_versions', [1])
        if data.get('layout_version', 1) not in layouts:
            raise ValueError('Deploy nine-section support before sending a new-format edition')
        if phase in ('stage', 'publish') and max(layouts)>=2 and data.get('layout_version') != max(layouts):
            raise ValueError('New local editions require the latest supported layout and editorial evidence')
        if phase == 'stage':
            # Exact same draft can safely resume after an uncertain save/review response.
            if remote is None or remote['draft']!=data:
                result = site.call('/api/v1/admin/daily', {'issue': data, 'draft_version': remote['draft_version'] if remote else 0})
                version = result['draft_version']
            else:
                version = remote['draft_version']
            write(directory/'draft-receipt.json',{'date':day,'content_hash':digest(data),'draft_version':version})
            if not remote or remote['draft']!=data or not remote['reviewed'] or remote['review'].get('method') != 'local_gpt' or remote['review'].get('evidence_hash') != report['evidence_hash']:
                site.call('/api/v1/admin/daily/' + day + '/review', {'draft_version': version, 'review_report': report, **({'evidence':json.loads((directory/'evidence.json').read_text())} if data.get('layout_version')==3 else {})})
            ready = site.call('/api/v1/admin/daily/' + day)
            if not ready['reviewed'] or ready['draft'] != data or ready['review'].get('evidence_hash') != report['evidence_hash']:
                raise ValueError('Remote preparation changed; inspect before publication')
            for lang in ('zh','en'):
                raw=site.call('/api/v1/admin/daily/'+day+'/pdf?lang='+lang,binary=True)
                if not raw.startswith(b'%PDF-'):raise ValueError('Private proof is not a PDF')
                (directory/('proof-'+lang+'.pdf')).write_bytes(raw)
            receipt = {'date': day, 'state': 'prepared', 'draft_version': version,
                       'content_hash': digest(data), 'evidence_hash': report['evidence_hash'], 'review': ready['review']}
            write(directory / 'prepared.json', receipt)
            return receipt
        if phase == 'publish':
            if local_time(now) < PUBLISH_AT:
                return {'date': day, 'state': 'not_due'}
            if not remote or not remote['reviewed'] or remote['review'].get('method') != 'local_gpt' or remote['review'].get('evidence_hash') != report['evidence_hash']:
                raise ValueError('A matching local GPT review and both PDFs must be prepared first')
            proof_hashes=check_layout(directory,data,remote['review']['pages'])
            site.call('/api/v1/admin/daily/' + day + '/publish', {'draft_version': remote['draft_version'],
                'automatic': True, 'proof_hashes':proof_hashes, 'reason': {'zh': '按已确认规则，由本地 GPT 核验后自动出刊。',
                                             'en': 'Automatically published after local GPT review under the approved editorial rules.'}})
        elif phase != 'check':
            raise ValueError('Unknown local phase')
        return verify_public(site, directory, data)


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('plan', 'status', 'validate', 'stage', 'publish', 'check'))
    parser.add_argument('--day', default=datetime.now(TZ).date().isoformat())
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--env-file', type=Path, default=ROOT / '.env')
    args = parser.parse_args()
    directory = args.directory or ROOT / 'output' / 'daily-journal' / day_key(args.day)
    try:
        site = None if args.phase in ('plan', 'validate') else Website(args.env_file)
        result = run(args.phase, args.day, directory, site)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        # Never print provider replies, credentials or exception text from a request.
        message = str(exc) if isinstance(exc, (ValueError, RuntimeError)) else type(exc).__name__
        print(json.dumps({'date': args.day, 'state': 'blocked', 'reason': message}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())
