"""Read-only operational metrics and durable run history. All time spans use days."""
from contextlib import contextmanager
from datetime import datetime, timezone
from math import ceil

from backend.db import get_db
from backend.knowledge import store


@contextmanager
def track_run(kind):
    with get_db() as db:
        rid = db.execute('INSERT INTO knowledge_workflow_runs(kind,started_at) VALUES(?,?)', (kind, store.now())).lastrowid
    result = {}
    try:
        yield result
    except Exception as exc:
        result.update(status='error', error=type(exc).__name__)
        raise
    finally:
        with get_db() as db:
            db.execute('UPDATE knowledge_workflow_runs SET finished_at=?,status=?,summary=? WHERE id=?',
                       (store.now(), result.get('status', 'partial'), store.encode(result), rid))


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (ValueError, AttributeError, TypeError):
        return None


def latency(pairs):
    values = sorted((end-start).total_seconds()/86400 for a,b in pairs
                    if (start:=timestamp(a)) and (end:=timestamp(b)) and end >= start)
    return {'sample_count':len(values), 'p50_days':round(values[ceil(len(values)*.5)-1],4) if values else None,
            'p95_days':round(values[ceil(len(values)*.95)-1],4) if values else None}


def snapshot():
    visible = "r.status='published' AND json_extract(r.metadata,'$.merged_into') IS NULL"
    with get_db() as db:
        records = [dict(r) for r in db.execute('SELECT r.id,r.published_at,r.collected_at,r.metadata FROM knowledge_records r WHERE '+visible).fetchall()]
        counts = [dict(r) for r in db.execute('SELECT j.stage,j.status,COUNT(*) AS count FROM knowledge_jobs j JOIN knowledge_records r ON r.id=j.record_id WHERE '+visible+' GROUP BY j.stage,j.status').fetchall()]
        sources = [dict(r) for r in db.execute('SELECT id,name,status,last_success_at,error FROM knowledge_sources WHERE enabled=1').fetchall()]
        progress = [dict(r) for r in db.execute('SELECT * FROM knowledge_source_progress').fetchall()]
        runs = [dict(r) for r in db.execute('SELECT * FROM knowledge_workflow_runs ORDER BY id DESC LIMIT 30').fetchall()]
        days = [r['day'] for r in db.execute("SELECT DISTINCT substr(started_at,1,10) AS day FROM knowledge_workflow_runs WHERE kind='daily' AND status='success' ORDER BY day DESC").fetchall()]
        throughput = db.execute("SELECT COUNT(*) AS count FROM knowledge_jobs j JOIN knowledge_records r ON r.id=j.record_id WHERE "+visible+" AND j.stage='organize' AND j.status='success' AND datetime(j.finished_at)>=datetime('now','-1 day')").fetchone()['count']
    for r in records:
        r['metadata'] = store.decode(r['metadata'], {})
    pending = [r for r in records if not r['metadata'].get('organized_at')]
    ages = [(datetime.now(timezone.utc)-t).total_seconds()/86400 for r in pending if (t:=timestamp(r['collected_at']))]
    for run in runs:
        run['summary'] = store.decode(run['summary'], {})
        run['duration_days'] = latency([(run['started_at'],run['finished_at'])])['p50_days']
        started=timestamp(run['started_at'])
        if run['status']=='running' and started and (datetime.now(timezone.utc)-started).total_seconds()>=86400:
            run['status']='stale'
    for p in progress:
        p['state'] = store.decode(p['state'], {})
    return {'interval_days':1,'time_unit':'day','generated_at':store.now(),'records':len(records),
            'organization_pending':len(pending),'oldest_pending_days':round(max(ages),4) if ages else None,
            'organized_last_day':throughput,'job_counts':counts,'sources':sources,'source_progress':progress,
            'publication_to_collection':latency([(r['published_at'],r['collected_at']) for r in records]),
            'collection_to_organization':latency([(r['collected_at'],r['metadata'].get('organized_at')) for r in records]),
            'runs':runs,'successful_daily_dates_utc':days,
            'scope':'Distinct successful full-workflow UTC dates; manual retries on one date do not count as multiple days. Source and content acceptance remain separate.'}
