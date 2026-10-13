#!/usr/bin/env python3
"""Run one resumable daily phase. Use the deployment's database/environment."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=['tick','collect','prepare','publish','check'],default='tick')
    parser.add_argument('--init-db',action='store_true',help='Apply additive database schema before running')
    args=parser.parse_args()
    if args.init_db:
        from backend.db import init_db
        init_db()
    from backend.daily_briefing.pipeline import run
    result=run(args.phase);print(json.dumps(result,ensure_ascii=False))
    return 1 if result['state'] in ('failed','blocked') else 0
if __name__=='__main__':sys.exit(main())
