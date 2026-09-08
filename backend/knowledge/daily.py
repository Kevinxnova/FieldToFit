"""Daily workflow. No email or account side effects."""
import argparse
import json
import os
from datetime import datetime, timezone


def run(limit=None,collect=True,record_id=None,force=False):
    from backend.db import init_db
    init_db()
    from backend.knowledge.operations import track_run
    with track_run('daily') as result:
        result.update(_workflow(limit,collect,record_id,force))
    return result


def _workflow(limit,collect,record_id,force):
    from backend.knowledge.sources import run_daily, list_sources
    from backend.knowledge.operations import timestamp
    from backend.knowledge.processing import run_processing,build_brief
    collection=run_daily() if collect else {'status':'skipped'}
    organized=run_processing(limit=limit if limit is not None else int(os.getenv("METIS_DAILY_RECORD_LIMIT","300")),budget_seconds=int(os.getenv("METIS_DAILY_PROCESS_SECONDS","3600")),record_id=record_id,force=force)
    brief=build_brief()
    from backend.knowledge.verification import run_due_checks
    checks=run_due_checks()
    enabled=[s for s in list_sources() if s['enabled']]
    unhealthy=[s['id'] for s in enabled if s['status']!='success' or not (stamp:=timestamp(s['last_success_at']))
               or not 0<=(datetime.now(timezone.utc)-stamp).total_seconds()<=86400]
    complete=collect and not record_id and bool(enabled) and not unhealthy and collection.get('status')=='success' and organized['status']=='success' and all(c.get('result')=='passed' for c in checks)
    return {'status':'success' if complete else 'partial','collection':collection,'unhealthy_sources':unhealthy,
            'processing':organized,'brief':brief,'checks':checks,'interval_days':1}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--no-collect',action='store_true')
    parser.add_argument('--limit',type=int)
    parser.add_argument('--record')
    parser.add_argument('--force',action='store_true')
    args=parser.parse_args()
    print(json.dumps(run(args.limit,not args.no_collect,args.record,args.force),ensure_ascii=False))
