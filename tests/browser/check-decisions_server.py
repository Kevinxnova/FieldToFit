"""Local-only browser fixture for private difference handling; no real credentials."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
os.environ.update(PYTHON_DOTENV_DISABLED='1', ADMIN_PASSWORD='decisions-fixture-only',
                  ALLOWED_ORIGINS='http://127.0.0.1:18057', FRONTEND_URL='http://127.0.0.1:18057')
import backend.config as config
import backend.db as database
fixture_root = Path(tempfile.mkdtemp(prefix='fieldtofit-check-decisions-'))
config.DB_PATH=fixture_root/'fixture.db';config.DATA_DIR=fixture_root
database.DATA_DIR=fixture_root;database.TURSO_URL='';database.TURSO_TOKEN=''
from backend.api.main import app
from backend.knowledge import content_workspace as ws, object_checks as checks
import backend.knowledge.sources as sources

URL='https://example.org/decisions-fixture'
def fetch(url, **kwargs):
    if url != URL:raise ValueError('This fixture accepts only its isolated source')
    return b'# Official fixture\nOriginal reviewed evidence.\nNew independently reviewed evidence.\n',url,'text/plain'
sources.fetch=fetch
database.init_db();ws.migrate()
draft=ws.detail('watch','CW-T01')
draft['draft']['name']='差异处置隔离验收'
draft['draft']['introduction']='已审介绍，差异处置不会改变此内容。'
ws.save('watch','CW-T01',draft)
preview=ws.preview('watch','CW-T01')
ws.publish('watch','CW-T01',{**preview,'confirmed':True,'reason':'Local-only browser fixture'})
checks.configure('CW-T01',{'entries':[{'url':URL,'title':'隔离官方入口','required':True,'scope':'版本和功能'}]})
checks.start();fetched=checks.scan(ws.today(),'CW-T01')
checks.review(ws.today(),'CW-T01',{'attempt_id':fetched['attempt_id'],'reason':'隔离夹具实际逐字段核对。','completed':True,
    'changes':[{'field':field,'before':fetched['baseline'][field],'after':after,'source_url':URL,'quote':'Original reviewed evidence.'}
               for field,after in [('introduction','建议的新功能介绍'),('name','建议的新名称')]]})
app.run(host='127.0.0.1',port=18057)
