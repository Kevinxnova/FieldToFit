"""Isolated unified-lookup browser fixture; never reads project credentials."""
import os,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()));sys.path.insert(0,str(Path.cwd()/'tests'))
os.environ.update(PYTHON_DOTENV_DISABLED='1',ADMIN_PASSWORD='lookup-test-only',ALLOWED_ORIGINS='http://127.0.0.1:18051',FRONTEND_URL='http://127.0.0.1:18051')
import backend.config as config,backend.db as database
root=Path(tempfile.mkdtemp(prefix='fieldtofit-lookup-'))
config.DB_PATH=root/'acceptance.db';config.DATA_DIR=root;database.DATA_DIR=root;database.TURSO_URL='';database.TURSO_TOKEN=''
from backend.api.main import app
from backend.knowledge import content_workspace as ws
from test_platform_updates import selected
from test_editorial_v130 import mat
database.init_db();ws.migrate()
for n,ident in enumerate(['CW-M01','CW-M02','CW-M03','CW-M04','CW-M05','CW-M06','CW-M07','CW-M08','CW-M09','CW-T01','CW-T02','D-01']):
 kind='news' if ident.startswith('D-') else 'watch';d=ws.detail(kind,ident)
 d['draft']['aliases']=['UnifiedFixture'];d['draft']['private_note']='PRIVATE-EDITOR-SECRET'
 if ident=='CW-M01':d['draft']['reading_materials']=[mat(body='Ｕｎｉｃｏｄｅ SearchNeedle. '+('Original documented instructions. '*100),locator='README.md / source section')]
 ws.save(kind,ident,d);p=ws.preview(kind,ident);ws.publish(kind,ident,{**p,'confirmed':True,'reason':'Isolated browser fixture'})
selected('browser-source')
app.run(host='127.0.0.1',port=18051)
