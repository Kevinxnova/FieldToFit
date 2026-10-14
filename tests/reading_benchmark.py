"""Measure one isolated process: python tests/reading_benchmark.py /absolute/repo.

Uses disposable SQLite only; no production credentials, assets or network timing.
"""
import os,sys,tempfile,json,time,gzip
from pathlib import Path
repo=Path(sys.argv[1]);sys.path.insert(0,str(repo));os.chdir(repo)
root=Path(tempfile.mkdtemp(prefix='fieldtofit-reading-bench-'))
os.environ.update(PYTHON_DOTENV_DISABLED='1',FIELDTOFIT_DATA_DIR=str(root),ADMIN_PASSWORD='fixture-only',FIELDTOFIT_READ_TOKEN='',FIELDTOFIT_ANALYTICS_ENABLED='0')
import backend.db as db
db.TURSO_URL='';db.TURSO_TOKEN=''
from backend.api import main
from backend.knowledge import content_workspace as ws
db.init_db();ws.migrate()
dist=root/'dist';dist.mkdir();(dist/'index.html').write_text((repo/'frontend/index.html').read_text());main.CLIENT_DIST=dist
client=main.app.test_client()
original=db.sqlite3.connect;queries=[];connections=[]
def connect(*a,**kw):
    conn=original(*a,**kw);connections.append(True)
    conn.set_trace_callback(lambda sql:queries.append(sql) if sql.lstrip().upper().startswith('SELECT') else None)
    return conn
db.sqlite3.connect=connect
rows=[]
for i in range(6):
    queries.clear();connections.clear();start=time.perf_counter();r=client.get('/for-you');elapsed=(time.perf_counter()-start)*1000
    assert r.status_code==200,r.text[:200]
    rows.append({'ms':round(elapsed,2),'selects':len(queries),'connections':len(connections),'bytes':len(r.data),'gzip':len(gzip.compress(r.data))})
page=r.data
extra=[]
if not b'id="fieldtofit-reading"' in page:
    for path in ('news','watch','model-landscape','watch?origin=developer_submission'):
        queries.clear();connections.clear();r=client.get('/api/v1/platform/'+path);assert r.status_code==200
        extra.append({'path':path,'bytes':len(r.data),'gzip':len(gzip.compress(r.data)),'selects':len(queries),'connections':len(connections)})
print(json.dumps({'html':rows,'initial_extra':extra,'initial_bytes':len(page)+sum(r['bytes'] for r in extra),'initial_gzip':len(gzip.compress(page))+sum(r['gzip'] for r in extra),'news':client.get('/api/v1/platform/news').json['total'],'watch':client.get('/api/v1/platform/watch').json['total']},indent=2))
