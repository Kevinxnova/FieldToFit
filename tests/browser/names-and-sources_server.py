"""Isolated browser fixture for name reviews and service-source coverage."""
import os,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()));sys.path.insert(0,str(Path.cwd()/'tests'))
os.environ.update(PYTHON_DOTENV_DISABLED='1',ADMIN_PASSWORD='names-fixture-only',ALLOWED_ORIGINS='http://127.0.0.1:18057',FRONTEND_URL='http://127.0.0.1:18057')
import backend.config as config,backend.db as database
root=Path(tempfile.mkdtemp(prefix='fieldtofit-names-browser-'))
config.DB_PATH=root/'fixture.db';config.DATA_DIR=root;database.DATA_DIR=root;database.TURSO_URL='';database.TURSO_TOKEN=''
from backend.api.main import app
from backend.knowledge import content_workspace as ws,discovery_names as names
from test_discovery_names import lead,group,investigation
database.init_db();ws.migrate()
lead('Introducing Jev and System One','https://typesafe.ai/blog/introducing-system-one-models-and-jev',642)
lead('Jev independent review','https://example.org/jev-review')
lead('Jevons paradox','https://example.org/jevons',180)
names.prepare();g=group('Jev');names.review(g['id'],investigation(g))
app.run(host='127.0.0.1',port=18057)
