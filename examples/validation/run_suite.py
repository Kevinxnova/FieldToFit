"""Run the eight reviewed examples against the configured local database.

Install requirements.txt and examples/validation/requirements.txt, then load the
explicit examples with `python -m examples.editorial.load` before running this.
No source documents, user input or model outputs are executed as code.
"""
import argparse
import json
from pathlib import Path
from importlib.metadata import version
from backend.db import init_db,get_db
from backend.knowledge import store,verification


def run():
    init_db();results=[]
    for check in verification.available_checks():
        with get_db() as db:
            row=db.execute("SELECT id FROM knowledge_records WHERE canonical_url=? AND status='published'",(check['source_url'],)).fetchone()
        if not row: raise ValueError('Import the example records before running the suite')
        result=verification.run_check(check['id'],row['id'])
        result.update(persona=check['persona'],title=check['title'],source_url=check['source_url'],expected=check['expected'],limitations=check['limitations'])
        results.append(result)
    return {'checked_at':store.now(),'scope':'8 scoped runtime checks. This does not establish product demand, whole-project quality, paper reproduction or superiority over ordinary search.',
            'dependencies':{p:version(p) for p in ('pypdf','reportlab','scikit-learn')},'items':results}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output');args=parser.parse_args()
    report=run()
    if args.output:Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'passed':sum(x['result']=='passed' for x in report['items']),'total':len(report['items'])}))
    raise SystemExit(any(x['result']!='passed' for x in report['items']))
