"""One bounded daily collection pass; never calls a model or publishes drafts."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, jsonify, request
from backend.security import bearer_matches, secret_is_configured

app = Flask(__name__)


@app.get('/api/cron/platform')
def platform_daily():
    if not secret_is_configured('CRON_SECRET'):
        return jsonify(error='Cron access is not configured'), 503
    if not bearer_matches(request.headers.get('Authorization')):
        return jsonify(error='Unauthorized'), 401
    from backend.db import init_db
    from backend.knowledge.platform_maintenance import run_daily
    if os.getenv('FIELDTOFIT_AUTO_INIT_DB', '1') != '0':
        init_db()
    return jsonify(run_daily(budget_seconds=180))
