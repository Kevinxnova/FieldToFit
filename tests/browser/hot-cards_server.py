"""Disposable local server. No production database, credentials or publications."""
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
sys.path.insert(0,str(Path.cwd()/'tests'))
os.environ.update(PYTHON_DOTENV_DISABLED='1',FIELDTOFIT_AUTO_INIT_DB='0',
    FIELDTOFIT_DATA_DIR=tempfile.mkdtemp(prefix='fieldtofit-hot-cards-'),
    ADMIN_PASSWORD='hot-cards-fixture-only',FIELDTOFIT_READ_TOKEN='',
    ALLOWED_ORIGINS='http://127.0.0.1:18062',FRONTEND_URL='http://127.0.0.1:18062',FIELDTOFIT_ANALYTICS_ENABLED='0')
import backend.db as database
database.TURSO_URL='';database.TURSO_TOKEN=''
from backend.api.main import app
from backend.knowledge import content_workspace as ws
from test_hot_cards import samples,save_card,publish
database.init_db();ws.migrate()
for item in samples():save_card(item);publish(item['id'])
app.run(host='127.0.0.1',port=18062)
