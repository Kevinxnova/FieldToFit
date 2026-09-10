"""Daily registered-source collection for local deployments."""
import argparse
import json
import time
from dotenv import load_dotenv
load_dotenv()


def run_all():
    from backend.knowledge.platform_maintenance import run_daily
    from backend.db import init_db
    init_db()
    return run_daily(budget_seconds=3600)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true", help="Repeat once per day")
    args = parser.parse_args()
    while True:
        started = time.monotonic()
        print(json.dumps(run_all(), ensure_ascii=False), flush=True)
        if not args.daemon:
            break
        time.sleep(max(1, 86400 - (time.monotonic() - started)))
