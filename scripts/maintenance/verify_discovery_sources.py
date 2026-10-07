"""Public HTTP source smoke test and immutable-body replay in a temporary DB."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile


def run(output):
    os.environ['PYTHON_DOTENV_DISABLED']='1'
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    import backend.config as config
    import backend.db as database
    root=Path(tempfile.mkdtemp(prefix='ftf-official-sources-'))
    config.DB_PATH=root/'isolated.db';config.DATA_DIR=root;database.DATA_DIR=root
    database.TURSO_URL='';database.TURSO_TOKEN=''
    from backend.knowledge import source_catalog,service_announcements as service,sources,store
    from backend.knowledge.paging import progress
    database.init_db()
    cache={};original=sources.fetch
    def snapshot_fetch(url,**kwargs):
        key=(url,tuple(sorted(kwargs.items())))
        if key not in cache:cache[key]=original(url,**kwargs)
        return cache[key]
    sources.fetch=snapshot_fetch
    definitions=[s for s in source_catalog.definitions() if s['config']['mode']=='service']
    results=[];replay=[]
    try:
        for turn in range(8):
            outcomes=[]
            for src in definitions:
                try:found,changed=service.collect(src);status='success';error=''
                except sources.PartialSourceError as e:found,changed=e.found,e.changed;status='partial';error=str(e)
                except Exception as e:found=changed=0;status='failed';error=type(e).__name__+': '+str(e)[:200]
                row={'id':src['id'],'url':src['url'],'status':status,'found':found,'changed':changed,'error':error,'progress':progress(src['id'])}
                outcomes.append(row)
                if turn==0:
                    with database.get_db() as db:
                        items=[dict(r) for r in db.execute('SELECT * FROM fieldtofit_discoveries WHERE source_id=? ORDER BY published_at DESC,id',(src['id'],)).fetchall()]
                    row['examples']=[{'title':r['title'],'published_at':r['published_at'],'metadata':store.decode(r['metadata'],{}),'material_hashes':[m['content_hash'] for m in store.decode(r['materials'],[])]} for r in items[:2]]
                    results.append(row)
                    print(src['id'],status,found,changed,flush=True)
            if turn:replay.append({'pass':turn+1,'changes':sum(r['changed'] for r in outcomes),'statuses':[{k:r[k] for k in ('id','status','changed','error')} for r in outcomes]})
        with database.get_db() as db:
            total=db.execute('SELECT count(*) FROM fieldtofit_discoveries').fetchone()[0]
        result={'checked_at':store.now(),'scope':'Actual public HTTP, cached response replay, temporary SQLite; no production credentials/database/publications',
            'results':results,'snapshot_replay':replay,'total_private_entries':total,'final_replay_new_entries':replay[-1]['changes'],
            'public_http_responses':len(cache)}
        result['passed']=len(results)==12 and total>=12 and replay[-1]['changes']==0 and all(r['status']=='success' for r in outcomes)
        path=Path(output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,ensure_ascii=False,indent=2));path.chmod(0o600)
        print(json.dumps({'output':str(path),'entries':total,'final_replay_new_entries':result['final_replay_new_entries']},ensure_ascii=False))
        return result
    finally:sources.fetch=original


if __name__=='__main__':
    os.umask(0o077)
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True)
    args=parser.parse_args();result=run(args.output)
    if not result['passed']:sys.exit(1)
