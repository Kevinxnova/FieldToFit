"""Isolated graph/history/management fixture; no production data or upstream calls."""
import os,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
os.environ.update(PYTHON_DOTENV_DISABLED='1',ADMIN_PASSWORD='maps-fixture-only',ALLOWED_ORIGINS='http://127.0.0.1:18058',FRONTEND_URL='http://127.0.0.1:18058')
import backend.config as config,backend.db as database
root=Path(tempfile.mkdtemp(prefix='fieldtofit-map-browser-'));config.DB_PATH=root/'fixture.db';config.DATA_DIR=root;database.DATA_DIR=root;database.TURSO_URL='';database.TURSO_TOKEN=''
from backend.api.main import app
from backend.knowledge import content_workspace as ws
database.init_db();ws.migrate()
if os.getenv('FIELDTOFIT_MAP_PREVIEW')!='1':
    d=ws.detail('news','D-90');d['draft']['technical_map']['change_summary']='夹具修订：补充条件对照';d['draft']['technical_map']['caution']='三项资源分别比较，不能推断 API 费用变化。浏览器修订夹具。'
    ws.save('news','D-90',{'draft':d['draft'],'draft_version':d['draft_version']});p=ws.preview('news','D-90');assert p['ready'],p
    ws.publish('news','D-90',{**p,'reason':'PRIVATE-BROWSER-FIXTURE','confirmed':True})
app.run(host='127.0.0.1',port=18058)
