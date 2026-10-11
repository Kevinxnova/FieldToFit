"""Serve the built watch UI with disposable data and no production credentials."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
root = Path(tempfile.mkdtemp(prefix='fieldtofit-watch-reading-'))
os.environ.update(PYTHON_DOTENV_DISABLED='1', FIELDTOFIT_DATA_DIR=str(root),
                  ADMIN_PASSWORD='watch-reading-fixture-only',
                  ALLOWED_ORIGINS='http://127.0.0.1:18061', FRONTEND_URL='http://127.0.0.1:18061',
                  FIELDTOFIT_ANALYTICS_ENABLED='0', FIELDTOFIT_READ_TOKEN='')
import backend.db as database
database.TURSO_URL = ''
database.TURSO_TOKEN = ''
from backend.api.main import app
from backend.knowledge import content_workspace as workspace

database.init_db()
workspace.migrate()
app.run(host='127.0.0.1', port=18061)
