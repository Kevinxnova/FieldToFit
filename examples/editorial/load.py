"""Import the explicitly curated GPT batch, without a model service or network call.

Run: python -m examples.editorial.load
Uses the configured database; set FIELDTOFIT_DATA_DIR to choose an isolated preview.
Only creates missing records. Existing source documents and corrections are retained.
"""
import json
from pathlib import Path
from backend.db import init_db, get_db
from backend.knowledge import store, processing


def run():
    init_db()
    batch=json.loads(Path(__file__).with_name('gpt-reviewed-batch.json').read_text())
    for entry in batch['items']:
        rid=entry['record_id']; record=store.get_record(rid)
        if not record:
            with get_db() as db:
                existing=db.execute('SELECT id FROM knowledge_records WHERE id=?',(rid,)).fetchone()
            if existing: raise ValueError('Refusing to republish a withdrawn record: '+rid)
            rid,_=store.save_record(entry['record'],'Imported source-linked GPT example',rid)
            entry['record_id']=rid
        for excerpt in [entry['source_excerpt'],*entry.get('extra_excerpts',[])]:
            full=store.get_record(rid,include_body=True)
            if not any(e['url']==excerpt['url'] and processing.normalized(excerpt['body']) in processing.normalized(e['body']) for e in full['evidence']):
                store.add_evidence(rid,**excerpt)
    result=processing.import_batch(batch)
    days={e['record']['published_at'][:10] for e in batch['items'] if e['record'].get('published_at') and e['record']['kind'] in {'event','paper'}}
    for day in days: processing.build_brief(day)
    return result


if __name__=='__main__':
    print(json.dumps(run(),ensure_ascii=False))
