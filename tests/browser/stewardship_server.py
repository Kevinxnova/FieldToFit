"""Isolated browser fixture. Run from repository root; never loads project credentials."""
import os,sys,tempfile,copy
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
os.environ.update(PYTHON_DOTENV_DISABLED='1',ADMIN_PASSWORD='stewardship-test-only',ALLOWED_ORIGINS='http://127.0.0.1:18050',FRONTEND_URL='http://127.0.0.1:18050')
import backend.config as config,backend.db as database
root=Path(tempfile.mkdtemp(prefix='fieldtofit-steward-'))
config.DB_PATH=root/'acceptance.db';config.DATA_DIR=root;database.DATA_DIR=root;database.TURSO_URL='';database.TURSO_TOKEN=''
from backend.api.main import app
from backend.knowledge import content_workspace as ws,stewardship as s
from datetime import datetime,timedelta,timezone
database.init_db();ws.migrate()
d=ws.detail('watch','CW-T01');template=copy.deepcopy(d['draft']);template['name']='隔离演示工具';template['introduction']='用于验收归并、关系与材料状态的本地测试工具。';template['reading_materials']=[{'id':'guide','title':'隔离原文材料','url':'https://example.org/guide','body':'Source material for isolated acceptance. '*50,'coverage':'full_text','checked_at':ws.today(),'approved':True,'rights':{'basis':'Test permission','url':'https://example.org/license','notice':'Isolated fixture'}}]
ws.save('watch','CW-T01',{'draft_version':d['draft_version'],'draft':template});p=ws.preview('watch','CW-T01');ws.publish('watch','CW-T01',{**p,'confirmed':True,'reason':'Isolated fixture'})
source=copy.deepcopy(template);source['id']='CW-T99';source['name']='隔离演示工具另一报道';source['introduction']='相同项目的第二份介绍，保留其原文与来源。'
with database.get_db() as db:db.execute('INSERT INTO fieldtofit_content_items VALUES(?,?,?,1,NULL,?,?)',('watch','CW-T99',ws.dump(source),'',ws.stamp()))
p=ws.preview('watch','CW-T99');ws.publish('watch','CW-T99',{**p,'confirmed':True,'reason':'Isolated duplicate fixture'})
candidate=copy.deepcopy(source);candidate['id']='CW-T98';candidate['name']='待审核候选';candidate['reading_materials'][0]['approved']=False
with database.get_db() as db:db.execute('INSERT INTO fieldtofit_content_items VALUES(?,?,?,1,NULL,?,?)',('watch','CW-T98',ws.dump(candidate),'',ws.stamp()))
for n in range(7):
 at=(datetime.now(timezone.utc)-timedelta(days=6-n)).isoformat()
 s.observe('CW-T01','guide','https://example.org/guide',{'ok':False,'error':'HTTP 429'},at)
app.run(host='127.0.0.1',port=18050)
