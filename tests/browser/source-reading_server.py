"""Local source-reading preview, isolated from all production stores and credentials."""
import copy
import json
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd()/'tests'))
root=Path(tempfile.mkdtemp(prefix='fieldtofit-source-reading-'))
os.environ.update(PYTHON_DOTENV_DISABLED='1',FIELDTOFIT_DATA_DIR=str(root),ADMIN_PASSWORD='source-reading-fixture',
 ALLOWED_ORIGINS='http://127.0.0.1:18070',FRONTEND_URL='http://127.0.0.1:18070',FIELDTOFIT_ANALYTICS_ENABLED='0',FIELDTOFIT_READ_TOKEN='')
import backend.db as database
database.TURSO_URL=database.TURSO_TOKEN=''
from backend.api.main import app
from backend.knowledge import content_workspace as ws
from backend.knowledge.locale import source_hash
from english_fixtures import fixture_fields
from test_source_reading import source_copy
database.init_db();ws.migrate()
path=os.environ.get('SOURCE_READING_EXAMPLES')
with database.get_db() as db:
 raw=json.loads(db.execute("SELECT published_json FROM fieldtofit_content_sets WHERE kind='news'").fetchone()[0])
 examples=json.loads(Path(path).read_text()) if path else [source_copy(i) for i in raw['items'] if i['id'] in ('D-321','D-324')]
 for item in examples:
  en=item['translations']['en'];en['source_hash']=source_hash('news',item)
  raw['items']=[item if i['id']==item['id'] else i for i in raw['items']]
  db.execute("UPDATE fieldtofit_content_items SET draft_json=?,published_json=? WHERE kind='news' AND id=?",(json.dumps(item),json.dumps(item),item['id']))
 db.execute("UPDATE fieldtofit_content_sets SET published_json=?,revision=revision+1 WHERE kind='news'",(json.dumps(raw),))
app.run(host='127.0.0.1',port=18070)
