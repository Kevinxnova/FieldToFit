"""Disposable source data for local For your AI acceptance; no production credentials."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
root = Path(tempfile.mkdtemp(prefix='fieldtofit-for-ai-'))
os.environ.update(PYTHON_DOTENV_DISABLED='1', FIELDTOFIT_DATA_DIR=str(root),
                  ADMIN_PASSWORD='for-ai-fixture-only', FIELDTOFIT_READ_TOKEN='',
                  ALLOWED_ORIGINS='http://127.0.0.1:18149', FRONTEND_URL='http://127.0.0.1:18149',
                  FIELDTOFIT_ANALYTICS_ENABLED='0')
import backend.db as database
import backend.config as config
config.DB_PATH = root / 'acceptance.db'
config.DATA_DIR = root
database.DATA_DIR = root
database.TURSO_URL = ''
database.TURSO_TOKEN = ''
from backend.api.main import app
from backend.knowledge import content_workspace as workspace

database.init_db()
workspace.migrate()
app.run(host='127.0.0.1', port=18149)
