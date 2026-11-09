"""Isolated layout fixture server; no production credentials or publication writes.

DAILY_LAYOUT_SAMPLE optionally loads an ignored, owner-approved private demo.
The fixture-only owner approval exercises rendering, not editorial verification.
"""
import json
import os
from pathlib import Path
import sys
import tempfile

sys.path[:0]=[str(Path.cwd()),str(Path.cwd()/'tests')]
root=Path(tempfile.mkdtemp(prefix='fieldtofit-event-first-'))
os.environ.update(PYTHON_DOTENV_DISABLED='1',FIELDTOFIT_DATA_DIR=str(root),ADMIN_PASSWORD='isolated-layout-only',
                  ALLOWED_ORIGINS='http://127.0.0.1:18078',FRONTEND_URL='http://127.0.0.1:18078',FIELDTOFIT_ANALYTICS_ENABLED='0',FIELDTOFIT_READ_TOKEN='')
import backend.config as config
import backend.db as database
config.DB_PATH=root/'fixture.db';config.DATA_DIR=database.DATA_DIR=root
database.TURSO_URL=database.TURSO_TOKEN=''
from backend.api.main import app
from backend.knowledge import content_workspace
from backend.daily_briefing import service
from daily_editorial_helpers import layout_sample
from test_daily_quality import quality

database.init_db();content_workspace.migrate()
issue=json.loads(Path(os.environ['DAILY_LAYOUT_SAMPLE']).read_text()) if os.environ.get('DAILY_LAYOUT_SAMPLE') else quality(layout_sample())
issue['layout_version']=4
assert issue['kind']=='review_sample', 'Only review samples are accepted by this local fixture'
version=service.save(issue)['draft_version']
service.approve(issue['date'],version,{'approved':True,'method':'owner'})
service.publish(issue['date'],version,{'zh':'隔离版式测试，不代表编辑通过或正式出刊。','en':'Isolated layout test, not editorial approval or a public edition.'})
out=Path(os.environ.get('READING_OUTPUT','output/daily-v1.18-validation'));out.mkdir(parents=True,exist_ok=True)
receipt={'kind':'isolated_layout_fixture','content_hash':service.read(issue['date'])['publication']['content_hash'],'date':issue['date'],'pdf':{}}
for lang in ('zh','en'):
    raw,sha,revision=service.pdf_bytes(issue['date'],lang)
    (out/f'layout-{lang}.pdf').write_bytes(raw)
    receipt['pdf'][lang]={'sha256':sha,'revision':revision,'pages':service.read(issue['date'],lang)['pdf'][lang]['pages']}
(out/'pdf-receipt.json').write_text(json.dumps(receipt,indent=2))
app.run(host='127.0.0.1',port=18078)
