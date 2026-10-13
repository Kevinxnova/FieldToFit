"""Authenticated daily phase runner; scheduler configuration is deployment-specific."""
import os
import sys
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from flask import Flask,jsonify,request
from backend.security import bearer_matches,secret_is_configured
app=Flask(__name__)
@app.get('/api/cron/daily-journal')
def daily_journal():
    if not secret_is_configured('CRON_SECRET'):return jsonify(error='Cron access is not configured'),503
    if not bearer_matches(request.headers.get('Authorization')):return jsonify(error='Unauthorized'),401
    from backend.db import init_db
    from backend.daily_briefing.pipeline import run
    from backend.knowledge.platform import PlatformError
    if os.getenv('FIELDTOFIT_AUTO_INIT_DB','1')!='0':init_db()
    try:
        result=run(request.args.get('phase','tick'))
        return jsonify(result),503 if result['state'] in ('failed','blocked') else 200
    except PlatformError as e:return jsonify(code=e.code),e.status
    except Exception:return jsonify(code='daily_processing_failed'),503
