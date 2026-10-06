"""Current reviewed topic + resumable net changes; never a second news store.

Each checkpoint keeps only public IDs/hashes. Page membership is bounded, while
every response rechecks the current publication. A later change is replayed in
the next window and can be deduplicated by event_id/content_revision.
"""
import hashlib
import json

from backend.db import get_db
from backend.knowledge import platform as p, platform_news as news, platform_updates as u
from backend.knowledge.codex_progress import projection


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def current(db, group):
    # One SELECT supplies the whole publication; baseline hashes and full read
    # come from that same collection, without a separate event-head race.
    row = db.execute("SELECT published_json FROM fieldtofit_content_sets WHERE kind='news'").fetchone()
    data = json.loads(row['published_json']) if row else json.loads(news.CONTENT_PATH.read_text())
    public = news.news(_data=data)
    items = {i['id']: i for i in public['items'] if i.get('codex_28_days') and
             (group == 'all' or i['codex_28_days']['group'] == group)}
    topic = projection(list(items.values()))
    hashes = {ident: digest(item) for ident, item in items.items()}
    return public['revision'], topic, items, hashes


def updates(group='all', limit=50, cursor=None):
    if group not in ('all', 'codex', 'other_openai'):
        raise p.PlatformError('Use group all, codex or other_openai')
    limit = p.integer(limit, 'limit', 1, 100)
    query = {'group': group, 'limit': limit}
    with get_db() as db:
        publication_revision, topic, live, hashes = current(db, group)
        topic_revision = digest(topic)
        position, mode, old, old_topic = 0, 'full', {}, None
        snap = None
        if cursor:
            snap, position = u._resume(db, cursor, 'codex_updates', query)
            if position == len(snap['data']['items']):
                old = snap['data']['baseline']
                old_topic = snap['data']['topic_revision']
                mode, snap, position = 'delta', None, 0
        if snap is None:
            changed = []
            for ident in sorted(hashes):
                if old.get(ident) != hashes[ident]:
                    changed.append({'object_id': ident, 'kind': 'updated' if ident in old else 'added',
                                    'from_revision': old.get(ident), 'content_revision': hashes[ident]})
            for ident in sorted(set(old) - set(hashes)):
                changed.append({'object_id': ident, 'kind': 'removed', 'from_revision': old[ident], 'content_revision': None})
            # Each item contains the latest published state, coalescing edits
            # between polls. A correction belongs to its original event date.
            changed.sort(key=lambda e: ((live.get(e['object_id'], {}).get('publication') or {}).get('updated_at') or '', e['object_id']))
            snap = u._snapshot(db, 'codex_updates', query, {'items': changed, 'baseline': hashes,
                                'topic_revision': topic_revision, 'mode': mode,
                                'topic_changed': mode == 'delta' and old_topic != topic_revision})
        result = u._page(snap, position, limit)
        events = []
        for ref in snap['data']['items'][position:position + limit]:
            ident = ref['object_id']
            event = {**ref}
            if ident not in live:
                event.update(kind='removed', content_revision=None)
            else:
                event.update(content_revision=hashes[ident], item=live[ident])
                # A removal reversed during pagination must restore the item.
                if event['kind'] == 'removed':
                    event['kind'] = 'updated'
            event['event_id'] = digest([group, ident, event['kind'], event['content_revision'], event['from_revision']])
            events.append(event)
        end = min(position + limit, result['total'])
        result.update(schema_version='fieldtofit.codex-updates.v1', mode=snap['data']['mode'], group=group,
                      revision=digest([topic, hashes]), publication_revision=publication_revision,
                      topic=topic, topic_changed=snap['data']['topic_changed'], items=events,
                      resume_cursor=f"{snap['id']}:{end}" if not result['has_more'] else None,
                      semantics='Latest published state since the last completed checkpoint; intermediate edits are coalesced. Recheck permissions on every page; deduplicate event_id and content_revision. Save every page before advancing; after the final page retain resume_cursor. Polling does not mark website logs read.',
                      recovery='Cursors expire after 7 days. On snapshot_expired, start without cursor, complete all pages and replace the cached scope, removing cached IDs absent from the full result. Changing group or limit requires a new full read.',
                      schedule={'timezone': 'Asia/Shanghai', 'suggested_client_time': '22:30',
                                'website_check_time': '22:00', 'publication_requires_review': True,
                                'delivery': 'Client schedules polling; connection alone does not schedule delivery.'})
        return result
