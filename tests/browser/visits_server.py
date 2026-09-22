"""Isolated visit-counter browser fixture, with no project credentials or production DB."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
port = int(os.getenv('FIELDTOFIT_TEST_PORT', '18053'))
os.environ.update(PYTHON_DOTENV_DISABLED='1', FIELDTOFIT_AUTO_INIT_DB='0',
                  ADMIN_PASSWORD='visits-test-only', ALLOWED_ORIGINS=f'http://127.0.0.1:{port}',
                  FRONTEND_URL=f'http://127.0.0.1:{port}', FIELDTOFIT_ANALYTICS_ENABLED='1',
                  FIELDTOFIT_ANALYTICS_ORIGIN=f'http://127.0.0.1:{port}')
import backend.config as config
import backend.db as database
root = Path(tempfile.mkdtemp(prefix='fieldtofit-visits-'))
config.DB_PATH = root / 'acceptance.db'
config.DATA_DIR = root
database.DATA_DIR = root
database.TURSO_URL = ''
database.TURSO_TOKEN = ''
from backend.api.main import app

database.init_db()
app.run(host='127.0.0.1', port=port)
