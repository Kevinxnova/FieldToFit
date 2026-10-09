"""Disposable reviewed-reading fixture. Never uses production credentials or database."""
import json, os, sys, tempfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
os.environ.update(PYTHON_DOTENV_DISABLED='1',ADMIN_PASSWORD='reading-fixture-only',ALLOWED_ORIGINS='http://127.0.0.1:18059',FRONTEND_URL='http://127.0.0.1:18059')
import backend.config as config, backend.db as database
root=Path(tempfile.mkdtemp(prefix='fieldtofit-reading-browser-'));config.DB_PATH=root/'fixture.db';config.DATA_DIR=root;database.DATA_DIR=root;database.TURSO_URL='';database.TURSO_TOKEN=''
from backend.api.main import app
from backend.knowledge import content_workspace as ws
database.init_db();ws.migrate()
client=app.test_client();headers={'X-Admin-Password':'reading-fixture-only'}
base='/api/v1/admin/workspace'
item=json.loads(Path('backend/knowledge/content/map-reading-bottle.json').read_text())
ref=client.post(base+'/inbox',headers=headers,json={'title':item['name'],'url':item['sources'][0]['url'],'summary':item['summary']}).json['ref']
ident=client.post(base+'/select',headers=headers,json={'ref':ref,'action':'select','kind':'news'}).json['id'];item['id']=ident
d=ws.detail('news',ident);ws.save('news',ident,{'draft':item,'draft_version':d['draft_version']});preview=ws.preview('news',ident);assert preview['ready'],preview
ws.publish('news',ident,{**preview,'confirmed':True,'reason':'Isolated reviewed case fixture'})
app.run(host='127.0.0.1',port=18059)
