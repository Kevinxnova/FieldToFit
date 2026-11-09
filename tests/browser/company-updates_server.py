"""Disposable topic fixture with >20 entries/company; never uses production data services."""
import copy
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
root=Path(tempfile.mkdtemp(prefix='fieldtofit-company-topics-'))
os.environ.update(PYTHON_DOTENV_DISABLED='1',FIELDTOFIT_DATA_DIR=str(root),ADMIN_PASSWORD='company-fixture-only',
                  ALLOWED_ORIGINS='http://127.0.0.1:18069',FRONTEND_URL='http://127.0.0.1:18069',
                  FIELDTOFIT_ANALYTICS_ENABLED='0',FIELDTOFIT_READ_TOKEN='')
import backend.db as database
database.TURSO_URL=database.TURSO_TOKEN=''
from backend.api.main import app
from backend.knowledge import content_workspace as workspace
from backend.knowledge.locale import source_hash
database.init_db();workspace.migrate()
with database.get_db() as db:
    raw=json.loads(db.execute("SELECT published_json FROM fieldtofit_content_sets WHERE kind='news'").fetchone()[0])
    for company,base in [('OpenAI','D-315'),('Anthropic','D-318')]:
        source=next(i for i in raw['items'] if i['id']==base)
        for n in range(25):
            item=copy.deepcopy(source);item['id']='D-'+str(9000+n+(100 if company=='Anthropic' else 0))
            item['highlight']=False;item['event_date']='2026-11-03'
            item['translations']['en']['source_hash']=source_hash('news',item)
            raw['items'].append(item)
    db.execute("UPDATE fieldtofit_content_sets SET published_json=?,revision=revision+1 WHERE kind='news'",(json.dumps(raw),))
app.run(host='127.0.0.1',port=18069)
