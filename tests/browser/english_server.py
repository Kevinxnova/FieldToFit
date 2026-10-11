"""Isolated local bilingual acceptance server. Never connects to production."""
import os
import shutil
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
os.environ.update(PYTHON_DOTENV_DISABLED='1',FIELDTOFIT_AUTO_INIT_DB='0',ADMIN_PASSWORD='isolated-english-check',TURSO_DATABASE_URL='',TURSO_AUTH_TOKEN='',ALLOWED_ORIGINS='http://127.0.0.1:5051')
os.environ.pop('FIELDTOFIT_READ_TOKEN',None)
folder=ROOT/'output/operations/req23-english'
target=folder/'browser.sqlite3'
if not target.exists():shutil.copy2(folder.parent/'v1.8.25-release/before.sqlite3',target)
import backend.config as config
import backend.db as database
config.DB_PATH=target;database.TURSO_URL='';database.TURSO_TOKEN=''
from backend.api.main import app
from flask import request,Response
@app.get('/__english_viewport')
def viewport():
    width=request.args.get('width','390')
    if width not in ('320','390','1440'):width='390'
    path=request.args.get('path','/en/for-you')
    if not path.startswith('/en/') or any(c in path for c in '\"<>'):path='/en/for-you'
    return Response(f'<!doctype html><html lang="en"><title>Isolated English viewport</title><body style="margin:0;background:#ddd"><iframe title="English website at {width}px" src="{path}" style="width:{width}px;height:900px;border:0;display:block"></iframe></body></html>',mimetype='text/html')
if __name__=='__main__':app.run(host='127.0.0.1',port=5051,debug=False)
