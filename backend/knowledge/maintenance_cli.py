"""Explicit local maintenance commands; never loads .env or remote DB credentials."""
import argparse
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', required=True)
    parser.add_argument('action', choices=['register', 'collect', 'export', 'review', 'publish'])
    parser.add_argument('--file')
    parser.add_argument('--source')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    os.environ.update(PYTHON_DOTENV_DISABLED='1', TURSO_DATABASE_URL='', TURSO_AUTH_TOKEN='',
                      FIELDTOFIT_DATA_DIR=str(Path(args.data_dir).resolve()))
    from backend.db import init_db
    from backend.knowledge import platform_maintenance as maintenance
    from backend.knowledge.sources import run_daily, list_sources
    init_db()
    if args.action == 'register':
        data = json.loads(Path(args.file).read_text())
        result = {'sources': [maintenance.register(**entry) for entry in data['objects']]}
    elif args.action == 'collect':
        ids = [s['id'] for s in list_sources() if s['adapter'] == 'platform_repository' and (not args.source or s['id'] == args.source)]
        result = {'results': [run_daily(sid, force=args.force) for sid in ids]}
    elif args.action == 'export':
        result = maintenance.jobs(100)
    else:
        data = json.loads(Path(args.file).read_text())
        result = {'results': [], 'errors': []}
        for draft in data['drafts']:
            try:
                reviewed = maintenance.apply(draft, publish=args.action == 'publish')
                result['results'].append({'id': reviewed['object']['id'], 'name': reviewed['object']['name'],
                                          'state': reviewed['selection']['state'], 'ready': reviewed['gate']['ready']})
            except (ValueError, TypeError) as exc:
                result['errors'].append({'id': draft.get('id'), 'error': str(exc)})
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.action == 'export' and args.file:
        Path(args.file).write_text(output)
        print(json.dumps({'path': str(Path(args.file).resolve()), 'jobs': len(result['items'])}))
    else:
        print(output)
    if result.get('errors'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
