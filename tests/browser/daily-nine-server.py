"""Isolated real nine-section web/PDF sample. Never reads production credentials."""
import json
import os
from pathlib import Path
import sys
import tempfile
sys.path[:0]=[str(Path.cwd()),str(Path.cwd()/'tests')]
root=Path(tempfile.mkdtemp(prefix='fieldtofit-nine-'))
os.environ.update(PYTHON_DOTENV_DISABLED='1',FIELDTOFIT_DATA_DIR=str(root),ADMIN_PASSWORD='nine-layout-fixture-only',
                  ALLOWED_ORIGINS='http://127.0.0.1:18072',FRONTEND_URL='http://127.0.0.1:18072',FIELDTOFIT_ANALYTICS_ENABLED='0',FIELDTOFIT_READ_TOKEN='')
import backend.config as config
import backend.db as database
config.DB_PATH=root/'fixture.db';config.DATA_DIR=database.DATA_DIR=root
database.TURSO_URL=database.TURSO_TOKEN=''
from backend.api.main import app
from backend.knowledge import content_workspace
from backend.daily_briefing import service
from daily_editorial_helpers import layout_sample
from backend.daily_briefing.schema import instant

database.init_db();content_workspace.migrate()
# Store a genuine legacy layout before adding the new isolated sample.
old=json.loads(Path('tests/fixtures/daily-2026-10-13.json').read_text());old.pop('image',None)
version=service.save(old)['draft_version'];service.approve(old['date'],version,{'approved':True,'method':'owner'})
service.publish(old['date'],version,{'zh':'隔离历史样刊','en':'Isolated historical sample'})
issue=layout_sample();issue['date']='2026-10-14';issue['window_start']='2026-10-13T08:30:00+08:00';issue['cutoff_at']='2026-10-14T08:30:00+08:00'
version=service.save(issue)['draft_version'];service.approve(issue['date'],version,{'approved':True,'method':'owner'})
service.publish(issue['date'],version,{'zh':'本地版式验收，非今日新闻。','en':'Local layout validation, not current news.'})
out=Path('output/pdf');out.mkdir(parents=True,exist_ok=True)
receipt={}
for lang in ('zh','en'):
    raw,sha,revision=service.pdf_bytes(issue['date'],lang)
    (out/f'FieldToFit-v1.12.0-layout-{lang}.pdf').write_bytes(raw)
    receipt[lang]={'sha256':sha,'revision':revision,'pages':service.read(issue['date'],lang)['pdf'][lang]['pages']}
Path('output/daily-v1.12-validation/pdf-receipt.json').write_text(json.dumps(receipt,indent=2))
app.run(host='127.0.0.1',port=18072)
