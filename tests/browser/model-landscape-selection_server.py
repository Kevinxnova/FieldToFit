"""Serve the built chart UI with a disposable database and no project credentials."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
root = Path(tempfile.mkdtemp(prefix='fieldtofit-chart-selection-'))
os.environ.update(
    PYTHON_DOTENV_DISABLED='1', FIELDTOFIT_DATA_DIR=str(root),
    ADMIN_PASSWORD='chart-selection-fixture-only',
    ALLOWED_ORIGINS='http://127.0.0.1:18059', FRONTEND_URL='http://127.0.0.1:18059',
    FIELDTOFIT_ANALYTICS_ENABLED='0',
)
import backend.db as database

database.TURSO_URL = ''
database.TURSO_TOKEN = ''
from backend.api.main import app
from backend.knowledge import content_workspace as ws

database.init_db()
ws.migrate()
app.run(host='127.0.0.1', port=18059)
