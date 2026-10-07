"""Isolated maintenance browser fixture; credentials and official services are unused."""
import os,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()));sys.path.insert(0,str(Path.cwd()/'tests'))
os.environ.update(PYTHON_DOTENV_DISABLED='1',ADMIN_PASSWORD='maintenance-fixture-only',ALLOWED_ORIGINS='http://127.0.0.1:18056',FRONTEND_URL='http://127.0.0.1:18056')
import backend.config as config,backend.db as database
root=Path(tempfile.mkdtemp(prefix='fieldtofit-reviewed-maintenance-'))
config.DB_PATH=root/'fixture.db';config.DATA_DIR=root;database.DATA_DIR=root;database.TURSO_URL='';database.TURSO_TOKEN=''
from backend.api.main import app
from backend.knowledge import content_workspace as ws,object_checks as checks,content_materials as cm
from test_editorial_v130 import mat
from test_reviewed_maintenance import pdf_bytes
from backend.knowledge.material_locations import extract_pdf
import backend.knowledge.sources as sources

def fake_fetch(url,**kwargs):
    if url!='https://example.org/guide':raise ValueError('Fixture accepts only its isolated source')
    return b'# Fixture guide\n\nNew verified feature.\n',url,'text/plain'
sources.fetch=fake_fetch
database.init_db();ws.migrate()
d=ws.detail('watch','CW-T01');d['draft']['name']='隔离验收档案';d['draft']['introduction']='已审介绍：用于原文定位与修订对照验收。'
m=mat(body='# Guide\n\nOriginal evidence 🧭.\n\n## Install\n\nFirst step.\n\n## Usage\n\nSecond step.\n',locator='README.md');m.update(id='guide',title='定位验收原文',url='https://example.org/guide')
pdf=mat();pdf.update(extract_pdf(pdf_bytes()));pdf.update(id='pdf',title='PDF页码验收',url='https://example.org/fixture.pdf')
d['draft']['reading_materials']=[m,pdf]
ws.save('watch','CW-T01',d);p=ws.preview('watch','CW-T01');ws.publish('watch','CW-T01',{**p,'confirmed':True,'reason':'Isolated browser fixture, never production'})
checks.configure('CW-T01',{'entries':[{'url':'https://example.org/guide','title':'隔离官方入口','required':True,'scope':'版本与接入'}]})
app.run(host='127.0.0.1',port=18056)
