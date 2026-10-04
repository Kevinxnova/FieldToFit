"""Explicit, one-hop watch scope shared by browser and MCP. No personal server state."""
import json
from backend.db import get_db
from backend.knowledge import stewardship as s, platform_updates as u, content_workspace as ws
from backend.knowledge.platform import integer


def changes(after=0, object_ids=None, limit=20, cursor=None, initialize=False):
    ids = u._ids(object_ids or [])
    if not ids or any(not i.startswith('CW-') for i in ids):
        ws.fail('Follow scope requires 1–100 CW- object IDs', 'invalid_follow_scope')
    limit, after = integer(limit, 'limit', 1, 100), integer(after, 'after')
    if cursor and (after or initialize):
        ws.fail('Use cursor without after or initialize', 'invalid_cursor')
    with get_db() as db:
        upper = db.execute('SELECT COALESCE(MAX(seq),0) FROM fieldtofit_steward_events').fetchone()[0]
        if after > upper:
            ws.fail('Checkpoint exceeds this database; retain unread entries and establish a new baseline', 'invalid_checkpoint')
        items, aliases, links = s.raw_items(db), s.rows(db, 'fieldtofit_steward_aliases'), s.rows(db, 'fieldtofit_steward_links')
        canonical = {i: s.resolve(i, db, aliases) for i in ids}
        family = {i: {i, canonical[i]} | {a['source_id'] for a in aliases if s.resolve(a['source_id'], db, aliases) == canonical[i]} for i in ids}
        related = {i: set() for i in ids}
        for ident, item in items.items():
            if not ident.startswith('D-'): continue
            refs = {r['id'] for r in item.get('related', [])}
            for i in ids:
                if refs & family[i]: related[i].add(ident)
        for row in links:
            a, b = row['source_id'], row['target_id']
            for i in ids:
                if a in family[i] and b.startswith('D-'): related[i].add(b)
                if b in family[i] and a.startswith('D-'): related[i].add(a)
        query = {'object_ids': ids, 'limit': limit, 'include_related': True,
                 'range_revision': s.digest([canonical, {i: sorted(related[i]) for i in ids}])}
        pos = 0
        if cursor:
            snap, pos = u._resume(db, cursor, 'follow_changes', query)
            if pos == len(snap['data']['items']):
                after, cursor, pos = snap['data']['until'], None, 0
        if not cursor:
            events = []
            if not initialize:
                records = db.execute('SELECT * FROM fieldtofit_steward_events WHERE seq>? AND seq<=? ORDER BY seq', (after, upper)).fetchall()
                for row in records:
                    data = json.loads(row['data']); ident = row['object_id']
                    refs = set(data.get('related_watch_ids', [])) | {data.get('target_id'), data.get('related_id')}
                    matches = [i for i in ids if ident in family[i] or (ident in related[i] and 'related_watch_ids' not in data) or (refs & family[i] and (ident.startswith('D-') or row['kind'] in ('merged','merge_reversed','relationship_updated','relationship_removed')))]
                    if matches:
                        events.append({'id': 'workspace:'+str(row['seq']), 'object_id': ident, 'kind': row['kind'],
                                       'observed_at': row['created_at'], **data, 'followed_ids': matches})
            snap = u._snapshot(db, 'follow_changes', query, {'items': events, 'after': upper if initialize else after, 'until': upper})
        result = u._page(snap, pos, limit)
        context = {'items': items, 'aliases': aliases, 'links': links, 'checks': s.rows(db,'fieldtofit_steward_checks')}
        objects = []
        for i in ids:
            status = s.public_status(i, db, context); item = items.get(status['canonical_id'], {})
            objects.append({'id': i, 'canonical_id': status['canonical_id'], 'availability': status['availability'],
                            'name': item.get('name', i) if status['availability'] != 'unavailable' else i})
        events = []
        for e in snap['data']['items'][pos:pos+limit]:
            live = s.public_status(e['object_id'], db, context)
            public = {k: v for k,v in e.items() if k in ('id','object_id','kind','observed_at','material_id','followed_ids','target_id')}
            if live['availability'] != 'unavailable':
                item = items.get(live['canonical_id'], {})
                public.update({k:v for k,v in e.items() if k in ('from_revision','to_revision','changed_fields')})
                public.update(name=item.get('name', e['object_id']), sources=[{'title':x.get('title',''), 'url':x['url']} for x in item.get('sources',[])], source_published_at=item.get('source_published_at'), checked_at=item.get('checked_at'))
            events.append({**public, 'current_availability': live['availability'], 'canonical_id': live['canonical_id']})
        result.update(items=events, objects=objects, scope='workspace', include_related=True, initialized=initialize,
                      after=snap['data']['after'], until=snap['data']['until'],
                      resume_cursor=f"{snap['id']}:{min(pos+limit,result['total'])}",
                      retention='Recorded events only; no automatic purge. Cursors expire after 7 days. Resume with the last fully saved numeric until after expiry or scope change; deduplicate event IDs. Browser and AI read positions are independent.')
        return result
