"""Disposable daily-preview browser fixture; no production credentials or writes."""
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
root = Path(tempfile.mkdtemp(prefix='fieldtofit-daily-preview-'))
os.environ.update(PYTHON_DOTENV_DISABLED='1', FIELDTOFIT_DATA_DIR=str(root),
                  ADMIN_PASSWORD='daily-preview-fixture-only',
                  ALLOWED_ORIGINS='http://127.0.0.1:18065', FRONTEND_URL='http://127.0.0.1:18065',
                  FIELDTOFIT_ANALYTICS_ENABLED='0', FIELDTOFIT_READ_TOKEN='')
import backend.config as config
import backend.db as database
config.DB_PATH = root / 'fixture.db'
config.DATA_DIR = database.DATA_DIR = root
database.TURSO_URL = database.TURSO_TOKEN = ''
from backend.api.main import app
from backend.knowledge import content_workspace
from backend.daily_briefing import service
from backend.daily_briefing.schema import instant

database.init_db()
content_workspace.migrate()
issue = json.loads(Path('tests/fixtures/daily-2026-10-13.json').read_text())
issue.pop('image', None)


def renderer(data, lang, image=None):
    # The fixture exercises preview navigation, not PDF layout or downloading.
    content = ('%PDF-1.4\n' + data['headline'][lang]).encode()
    return {'bytes': content, 'sha256': hashlib.sha256(content).hexdigest(), 'pages': 1}


version = service.save(issue)['draft_version']
service.approve(issue['date'], version, {'approved': True, 'method': 'owner'}, renderer)
service.publish(issue['date'], version, {'zh': '隔离测试样刊。', 'en': 'Isolated browser fixture.'},
                now=instant('2026-10-14T09:05:00+08:00'))
app.run(host='127.0.0.1', port=18065)
