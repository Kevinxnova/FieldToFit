"""Daily 07:30 private report handoff; local AI imports actual checks and 08:00 proposals."""
import argparse
import json
import os
from pathlib import Path
import requests
from dotenv import dotenv_values


def run(base, env_file, output, checks=None, proposals=None):
    headers = {'X-Admin-Password': dotenv_values(env_file)['ADMIN_PASSWORD']}
    session = requests.Session(); session.trust_env = False
    def call(path, data=None):
        response = session.request('POST' if data is not None else 'GET', base.rstrip('/')+'/api/v1/admin/workspace/maps'+path,
                                   headers=headers, json=data, timeout=45, allow_redirects=False)
        if response.status_code != 200: raise RuntimeError('Map API HTTP '+str(response.status_code)+'; no draft or publication attempted')
        return response.json()
    for path, source in (('/check', checks), ('/propose', proposals)):
        if source:
            items = json.loads(Path(source).read_text())
            if not isinstance(items, list) or len(items) > 10: raise ValueError('Expected at most 10 actual checks / proposals')
            for item in items: call(path, item)
    result = call('/handoff')
    path = Path(output); path.parent.mkdir(parents=True, exist_ok=True)
    # Create private exports from the outset; never print body or administrator headers.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as handle: json.dump(result, handle, ensure_ascii=False, indent=2)
    path.chmod(0o600)
    return {'day': result['day'], 'targets': len(result['targets']), 'backlog': result['backlog'], 'publication': False}


if __name__ == '__main__':
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='https://fieldtofit.top'); parser.add_argument('--env-file', default='.env'); parser.add_argument('--output', required=True)
    parser.add_argument('--checks', help='JSON list of actual report reads or failures'); parser.add_argument('--proposals', help='JSON list of source-backed before/after map proposals')
    args = parser.parse_args(); print(json.dumps(run(args.base, args.env_file, args.output, args.checks, args.proposals), ensure_ascii=False))
