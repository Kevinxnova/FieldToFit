"""Read-only, deployment-local release history generated from CHANGELOG.md."""
import json
from pathlib import Path
from flask import Blueprint, jsonify, request
from backend import __version__

DATA = Path(__file__).parent / 'seo' / 'changelog.json'
bp = Blueprint('site_changelog', __name__)


def history(language='zh'):
    data = json.loads(DATA.read_text())
    if data['version'] != __version__:
        raise ValueError('Changelog does not match the running application')
    items = []
    for entry in data['items']:
        if tuple(map(int, entry['version'].split('.'))) > tuple(map(int, __version__.split('.'))):
            continue
        items.append({key: value for key, value in entry.items() if key != 'copy'} | entry['copy'][language] |
                     {'status': 'current' if entry['version'] == __version__ else 'deployed' if entry['deployed_on'] else 'unverified'})
    return {'version': __version__, 'revision': data['revision'], 'language': language, 'items': items,
            'archive_url': 'https://github.com/Kevinxnova/FieldToFit/blob/main/CHANGELOG.md#附录metis-历史更新记录'}


@bp.get('/api/changelog')
def changelog():
    language = request.args.get('lang', 'zh')
    if language not in ('zh', 'en'):
        response = jsonify({'detail': 'Unsupported language'})
        response.status_code = 400
    else:
        try:
            data = history(language)
            response = jsonify({k: data[k] for k in ('version', 'revision', 'language')} if request.args.get('metadata') == '1' else data)
        except (OSError, ValueError, KeyError, TypeError):
            response = jsonify({'detail': 'Changelog temporarily unavailable' if language == 'en' else '更新日志暂时无法读取'})
            response.status_code = 503
    response.headers['Cache-Control'] = 'no-store'
    return response
