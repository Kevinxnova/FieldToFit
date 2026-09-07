"""Daily workflow. No email or account side effects."""
from datetime import datetime, timezone
import argparse
import json
import os


def run(limit=None,collect=True,record_id=None,force=False):
    from backend.db import init_db
    from backend.knowledge.sources import run_daily
    from backend.knowledge.processing import run_processing,build_brief,processing_status
    init_db()
    collection=run_daily() if collect else {'status':'skipped'}
    organized=run_processing(limit=limit or int(os.getenv("METIS_DAILY_RECORD_LIMIT","300")),budget_seconds=int(os.getenv("METIS_DAILY_PROCESS_SECONDS","3600")),record_id=record_id,force=force)
    brief=build_brief()
    from backend.knowledge.verification import run_due_checks
    checks=run_due_checks()
    return {'collection':collection,'processing':organized,'brief':brief,'checks':checks,'interval_days':1}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--no-collect',action='store_true')
    parser.add_argument('--limit',type=int)
    parser.add_argument('--record')
    parser.add_argument('--force',action='store_true')
    args=parser.parse_args()
    print(json.dumps(run(args.limit,not args.no_collect,args.record,args.force),ensure_ascii=False))
