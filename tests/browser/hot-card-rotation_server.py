"""Isolated local rotation fixture. No production credentials, database or writes."""
import json
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / 'tests'))
root = Path(tempfile.mkdtemp(prefix='fieldtofit-card-rotation-'))
os.environ.update(PYTHON_DOTENV_DISABLED='1', FIELDTOFIT_AUTO_INIT_DB='0', FIELDTOFIT_DATA_DIR=str(root),
    ADMIN_PASSWORD='card-rotation-local-only', FIELDTOFIT_READ_TOKEN='', FIELDTOFIT_ANALYTICS_ENABLED='0',
    ALLOWED_ORIGINS='http://127.0.0.1:18118', FRONTEND_URL='http://127.0.0.1:18118')
import pytest
from flask import send_from_directory
import backend.db as database
database.TURSO_URL = ''; database.TURSO_TOKEN = ''
from backend.api.main import app
from backend.knowledge import hot_cards
import test_content_workspace
test_content_workspace.ADMIN = {"X-Admin-Password":"card-rotation-local-only"}
from test_hot_card_rotation import fourth
patch = pytest.MonkeyPatch()
database.init_db()
ident = fourth.__wrapped__(app.test_client(), root, patch)
app.view_functions['serve_hot_card'] = lambda filename: send_from_directory(hot_cards.ASSETS, filename)
state = {'new_card': ident, 'base':'http://127.0.0.1:18118'}
output = Path(os.environ['ROTATION_FIXTURE'])
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(state))
app.run(host='127.0.0.1', port=18118)
