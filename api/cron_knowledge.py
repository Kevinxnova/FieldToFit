"""Daily, bounded knowledge-processing continuation for serverless deployments."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from flask import Flask,jsonify,request
from backend.security import bearer_matches,secret_is_configured
app=Flask(__name__)

@app.get('/api/cron/knowledge')
def knowledge():
    if not secret_is_configured('CRON_SECRET'):return jsonify(error='Cron access is not configured'),503
    if not bearer_matches(request.headers.get('Authorization')):return jsonify(error='Unauthorized'),401
    from backend.db import init_db
    from backend.knowledge.processing import run_processing,build_brief
    init_db()
    # Retain unfinished work for the next daily run; never report a whole backlog as processed.
    return jsonify(processing=run_processing(limit=max(1,min(100,int(os.getenv('FIELDTOFIT_CRON_RECORD_LIMIT','30')))),budget_seconds=180),brief=build_brief(),interval_days=1)
