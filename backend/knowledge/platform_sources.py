"""Public collection-source status; never implies per-document revalidation."""
from datetime import datetime, timezone

from backend.db import get_db
from backend.knowledge import store


def source_id(db, obj):
    if 'source_id' in obj:
        return obj['source_id']
    # Older publication snapshots omit source_id. Resolve their own historical
    # record snapshot, never the mutable current record or a guessed hostname.
    row = db.execute('SELECT snapshot FROM knowledge_changes WHERE record_id=? AND seq<=? ORDER BY seq DESC LIMIT 1',
                     (obj['id'], obj.get('source_revision', 0))).fetchone()
    return store.decode(row['snapshot'], {}).get('source_id') if row else None


def _stamp(value):
    try:
        stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if stamp.tzinfo is None or stamp > datetime.now(timezone.utc):
            return None
        return stamp.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
    except (AttributeError, ValueError, TypeError):
        return None


def status(db, sid):
    row = db.execute('SELECT id,name,enabled,status,last_attempt_at,last_success_at FROM knowledge_sources WHERE id=?', (sid,)).fetchone() if sid else None
    result = {'id': sid, 'name': row['name'] if row else sid or 'Unknown source', 'registered': bool(row),
              'enabled': bool(row['enabled']) if row else None, 'interval_days': 1,
              'last_attempt_at': _stamp(row['last_attempt_at']) if row else None,
              'last_success_at': _stamp(row['last_success_at']) if row else None,
              'scope': 'Collection adapter only; not a successful check of every object or original document'}
    success = result['last_success_at']
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(success.replace('Z', '+00:00'))).total_seconds() if success else None
    result['freshness'] = 'unknown' if age is None else 'current' if age <= 86400 else 'stale'
    run = row['status'] if row else 'unknown'
    result['last_run_status'] = run if run in ('success', 'failed', 'partial', 'running', 'pending', 'error') else 'unknown'
    result['state'] = ('unregistered' if not row else 'paused' if not row['enabled'] else
                       run if run in ('running', 'failed', 'partial', 'error') else result['freshness'])
    return result


def current_sources(db):
    rows = db.execute("SELECT pub.snapshot FROM knowledge_selections s JOIN knowledge_publications pub ON pub.seq=s.revision "
                      "JOIN knowledge_records r ON r.id=s.record_id WHERE s.state='published' AND r.status='published' "
                      "AND r.metadata NOT LIKE '%\"merged_into\"%'").fetchall()
    counts = {}
    for row in rows:
        sid = source_id(db, store.decode(row['snapshot'], {}))
        counts[sid] = counts.get(sid, 0) + 1
    from backend.knowledge.platform_read_batch import prepare_sources
    db = prepare_sources(db, counts)
    return [{**status(db, sid), 'objects': count} for sid, count in sorted(counts.items(), key=lambda item: item[0] or '')]


def sources():
    from backend.knowledge.platform import SCHEMA_VERSION
    with get_db() as db:
        items = current_sources(db)
    return {'schema_version': SCHEMA_VERSION, 'items': items, 'observed_at': store.now(), 'interval_days': 1,
            'scope': 'Sources attached to currently published selections; not the entire source registry'}
