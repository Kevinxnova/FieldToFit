"""Bounded read snapshots, public selection changes and reviewed overview editions.

Snapshots freeze membership and order, never permissions. Withdrawal always wins.
No draft prose or private review reasons are returned through public endpoints.
"""
import hashlib
import re
import uuid
from datetime import date as calendar_date, datetime, timedelta, timezone

from backend.db import get_db
from backend.knowledge import platform as p, store, platform_sources

SNAPSHOT_DAYS = 7


def _snapshot(db, kind, query, data):
    now = datetime.now(timezone.utc)
    stamp, expires = now.isoformat(), (now + timedelta(days=SNAPSHOT_DAYS)).isoformat()
    db.execute('DELETE FROM knowledge_read_snapshots WHERE expires_at<?', (stamp,))
    sid = uuid.uuid4().hex
    db.execute('INSERT INTO knowledge_read_snapshots VALUES(?,?,?,?,?,?)',
               (sid, kind, store.encode(query), store.encode(data), stamp, expires))
    return {'id': sid, 'data': data, 'expires_at': expires}


def _resume(db, cursor, kind, query):
    if not isinstance(cursor, str) or not re.fullmatch(r'[0-9a-f]{32}:[0-9]+', cursor) or len(cursor) > 60:
        raise p.PlatformError('Invalid cursor; restart this query', 'invalid_cursor')
    sid, position = cursor.split(':')
    row = db.execute('SELECT * FROM knowledge_read_snapshots WHERE id=?', (sid,)).fetchone()
    if not row or row['expires_at'] <= datetime.now(timezone.utc).isoformat():
        raise p.PlatformError('Read snapshot expired; restart the full query and retain object/revision IDs for deduplication', 'snapshot_expired', 410)
    if row['kind'] != kind or store.decode(row['query'], {}) != query:
        raise p.PlatformError('Cursor belongs to another query or page size; repeat its original filters', 'cursor_scope_mismatch')
    data = store.decode(row['data'], {})
    position = p.integer(position, 'cursor position', 0, len(data['items']))
    return {'id': sid, 'data': data, 'expires_at': row['expires_at']}, position


def _page(snapshot, position, limit):
    total = len(snapshot['data']['items'])
    end = min(position + limit, total)
    more = end < total
    return {'schema_version': p.SCHEMA_VERSION, 'snapshot': snapshot['id'], 'expires_at': snapshot['expires_at'],
            'offset': position, 'total': total, 'has_more': more,
            'next_offset': end if more else None,
            'previous_cursor': f"{snapshot['id']}:{max(0, position-limit)}" if position else None,
            'next_cursor': f"{snapshot['id']}:{end}" if more else None,
            'page_cursor': f"{snapshot['id']}:{position}"}


def _readable(db, rid, revision):
    try:
        return p._get_object(db, rid, revision)
    except p.PlatformError as error:
        if error.status not in (404, 410):
            raise
        return {'revision': revision, 'object': {'id': rid}, 'unavailable': True,
                'code': error.code, 'detail': 'This publication is no longer publicly available'}


def search(q='', object_type='', limit=20, offset=0, cursor=None, source='', since='', until=''):
    q = p.text(q, 'q', 200, False).casefold()
    if object_type and object_type not in p.TYPES:
        raise p.PlatformError('Invalid resource type')
    limit, offset = p.integer(limit, 'limit', 1, 100), p.integer(offset, 'offset')
    source = p.text(source, 'source', 100, False)
    since, until = _day(since, 'since') if since else '', _day(until, 'until') if until else ''
    if since and until and since > until:
        raise p.PlatformError('since must not follow until')
    query = {'q': q, 'object_type': object_type, 'limit': limit}
    # Keep existing unfiltered cursors compatible.
    query.update({k: v for k, v in {'source': source, 'since': since, 'until': until}.items() if v})
    if cursor and offset:
        raise p.PlatformError('Use cursor without offset', 'invalid_cursor')
    with get_db(atomic=True) as db:
        if cursor:
            snapshot, offset = _resume(db, cursor, 'objects', query)
        else:
            rows = db.execute("SELECT pub.* FROM knowledge_selections s JOIN knowledge_publications pub ON pub.seq=s.revision "
                              "JOIN knowledge_records r ON r.id=s.record_id WHERE s.state='published' AND r.status='published' "
                              "AND r.metadata NOT LIKE '%\"merged_into\"%' ORDER BY pub.seq DESC").fetchall()
            refs = []
            for row in rows:
                obj = store.decode(row['snapshot'], {})
                day = datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')).astimezone(timezone.utc).date().isoformat()
                if (source and source != platform_sources.source_id(db, obj)) or (since and day < since) or (until and day > until):
                    continue
                haystack = ' '.join([obj['name'], obj['original_name'], obj['introduction'], *obj['aliases']]).casefold()
                if (q and q not in haystack) or (object_type and object_type not in obj['types']):
                    continue
                refs.append({'id': row['record_id'], 'revision': row['seq']})
            # Offset is retained for old clients; only continuation cursors preserve this snapshot.
            snapshot = _snapshot(db, 'objects', query, {'items': refs})
        result = _page(snapshot, offset, limit)
        result.update(scope='curated publications at snapshot creation', sort='published_revision_desc', filters=query, date_basis='FieldToFit publication date in UTC, inclusive; not upstream release date',
                      pagination='snapshot cursor; unavailable publications retain redacted positions',
                      items=[_readable(db, ref['id'], ref['revision']) for ref in snapshot['data']['items'][offset:offset+limit]])
        return result


def _ids(ids):
    if not isinstance(ids, list) or len(ids) > 100:
        raise p.PlatformError('object_ids must be a list of at most 100 IDs')
    return sorted(set(p.text(item, 'object ID', 100) for item in ids))


def _events(db, after, ids, through=None):
    # Scan the immutable selection log so private draft edits cannot become public changes.
    previous, events = {}, []
    upper = db.execute('SELECT COALESCE(MAX(seq),0) FROM knowledge_publications').fetchone()[0]
    clauses, args = [], []
    if ids:
        clauses.append('record_id IN (' + ','.join('?' for _ in ids) + ')')
        args.extend(ids)
    if through is not None:
        clauses.append('seq<=?')
        args.append(through)
    rows = db.execute('SELECT * FROM knowledge_publications' + (' WHERE ' + ' AND '.join(clauses) if clauses else '') + ' ORDER BY seq', args).fetchall()
    if after > upper:
        raise p.PlatformError('Checkpoint exceeds this database; restart from zero', 'invalid_checkpoint')
    for row in rows:
        rid, seq, state = row['record_id'], row['seq'], row['state']
        if ids and rid not in ids:
            continue
        old = previous.get(rid)
        event = None
        if state == 'published':
            obj = store.decode(row['snapshot'], {})
            changed = [field for field in ('name', 'aliases', 'roles', 'facts', 'materials', 'attention', 'introduction', 'types', 'upstream_version', 'official_url', 'source_id')
                       if old and old['object'].get(field) != obj.get(field)]
            event = {'id': seq, 'object_id': rid, 'kind': 'updated' if old else 'added',
                     'from_revision': old['revision'] if old else None, 'to_revision': seq,
                     'changed_fields': changed, 'published_at': row['created_at']}
            previous[rid] = {'revision': seq, 'object': obj, 'state': state}
        elif old and ((state in ('needs_review', 'withdrawn') and old['state'] != state)
                      or (state == 'review' and old['state'] == 'published')):
            event = {'id': seq, 'object_id': rid, 'kind': 'needs_review' if state == 'review' else state, 'from_revision': old['revision'],
                     'to_revision': None, 'changed_fields': [], 'published_at': row['created_at']}
            old['state'] = state
        if event and seq > after:
            events.append(event)
    return events, upper


def _public_event(db, event):
    event = dict(event)
    pub = _readable(db, event['object_id'], event['to_revision'] or event['from_revision'])
    event['availability'] = 'unavailable' if pub.get('unavailable') else 'readable'
    if not pub.get('unavailable'):
        event['name'] = pub['object']['name']
        event['official_url'] = pub['object']['official_url']
        event['selection_state'] = pub['selection_state']
        if event['to_revision']:
            event['read_url'] = f'/api/v1/platform/objects/{event["object_id"]}?revision={event["to_revision"]}'
    return event


def _history(db, rid, revision, limit=20):
    """Bounded export history, with a real snapshot cursor for omitted older events."""
    events, _ = _events(db, 0, [rid], through=revision)
    events.reverse()
    query = {'id': rid, 'revision': revision, 'limit': limit}
    snapshot = _snapshot(db, 'history', query, {'items': events, 'revision': revision})
    return _history_page(db, rid, snapshot, 0, limit)


def history_summary(db, rid, revision, limit=20):
    events, _ = _events(db, 0, [rid], through=revision)
    if len(events) > limit:
        return _history(db, rid, revision, limit)
    return {'object_id':rid, 'revision':revision, 'total':len(events), 'has_more':False,
            'continuation':None, 'sort':'event_id_desc',
            'scope':'Public selection events through the chosen publication revision; no private review notes or later events',
            'items':[_public_event(db, event) for event in reversed(events)]}


def _history_page(db, rid, snapshot, position, limit):
    result = _page(snapshot, position, limit)
    result.update(object_id=rid, revision=snapshot['data']['revision'], sort='event_id_desc',
                  scope='Public selection events through the chosen publication revision; no private review notes or later events',
                  items=[_public_event(db, e) for e in snapshot['data']['items'][position:position+limit]])
    result['continuation'] = {'tool': 'curated_history', 'arguments': {
        'id': rid, 'revision': result['revision'], 'limit': limit, 'cursor': result['next_cursor']}} if result['has_more'] else None
    return result


def history(rid, revision=None, limit=20, cursor=None):
    rid, limit = p.text(rid, 'object ID', 100), p.integer(limit, 'limit', 1, 100)
    revision = p.integer(revision, 'revision', 1) if revision is not None else None
    if cursor and revision is None:
        raise p.PlatformError('Continue history with its returned publication revision', 'cursor_scope_mismatch')
    with get_db(atomic=True) as db:
        pub = p._get_object(db, rid, revision)
        if cursor:
            snapshot, position = _resume(db, cursor, 'history', {'id':rid, 'revision':pub['revision'], 'limit':limit})
            return _history_page(db, rid, snapshot, position, limit)
        return _history(db, rid, pub['revision'], limit)


def changes(after=0, object_ids=None, limit=20, cursor=None):
    ids, limit = _ids([] if object_ids is None else object_ids), p.integer(limit, 'limit', 1, 100)
    after = p.integer(after, 'after')
    if cursor and after:
        raise p.PlatformError('Use cursor without after', 'invalid_cursor')
    query = {'object_ids': ids, 'limit': limit}
    with get_db(atomic=True) as db:
        position = 0
        if cursor:
            snapshot, position = _resume(db, cursor, 'changes', query)
            if position == len(snapshot['data']['items']):
                # Completed checkpoint starts a new bounded window on the next poll.
                after = snapshot['data']['until']
                cursor = None
        if not cursor:
            events, upper = _events(db, after, ids)
            snapshot = _snapshot(db, 'changes', query, {'items': events, 'after': after, 'until': upper})
            position = 0
        result = _page(snapshot, position, limit)
        items = [_public_event(db, event) for event in snapshot['data']['items'][position:position+limit]]
        result.update(items=items, after=snapshot['data']['after'], until=snapshot['data']['until'],
                      scope='published selections and their review/withdrawal changes',
                      resume_cursor=f"{snapshot['id']}:{min(position+limit, result['total'])}",
                      retention='Read cursors expire after 7 days; retained publication logs have no automatic purge yet')
        return result


def _day(value, field):
    value = p.text(value, field, 10)
    try:
        if calendar_date.fromisoformat(value).isoformat() != value:
            raise ValueError()
    except ValueError:
        raise p.PlatformError(f'{field} must be YYYY-MM-DD') from None
    return value


def _edition_data(data):
    if not isinstance(data, dict) or set(data) - {'title', 'period_start', 'period_end', 'entries'}:
        raise p.PlatformError('Invalid edition fields')
    result = {'title': p.text(data.get('title', ''), 'title', 160, False),
              'period_start': _day(data.get('period_start'), 'period_start'),
              'period_end': _day(data.get('period_end'), 'period_end')}
    if result['period_start'] > result['period_end']:
        raise p.PlatformError('Period end must follow its start')
    entries = data.get('entries', [])
    if not isinstance(entries, list) or len(entries) > 5:
        raise p.PlatformError('An edition can contain at most 5 entries')
    result['entries'] = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {'object_id', 'revision', 'summary', 'significance', 'material_id', 'quote'}:
            raise p.PlatformError('Each entry needs an object/revision, summary, significance and source quotation')
        result['entries'].append({'object_id': p.text(entry['object_id'], 'object_id', 100),
                                  'revision': p.integer(entry['revision'], 'revision', 1),
                                  'summary': p.text(entry['summary'], 'summary', 800, False),
                                  'significance': p.text(entry['significance'], 'significance', 800, False),
                                  'material_id': p.text(entry['material_id'], 'material_id', 100, False),
                                  'quote': p.text(entry['quote'], 'quote', 2000, False)})
    if len({e['object_id'] for e in result['entries']}) != len(entries):
        raise p.PlatformError('Use one entry per object in an edition')
    return result


def _edition_preview(db, eid):
    row = db.execute('SELECT * FROM knowledge_editions WHERE id=?', (eid,)).fetchone()
    if not row:
        raise p.PlatformError('Edition draft not found', 'not_found', 404)
    data = store.decode(row['data'], {})
    errors, bindings = [], []
    if not data['title'] or not data['entries']:
        errors.append('A title and at least one reviewed entry are required')
    for entry in data['entries']:
        pub = _readable(db, entry['object_id'], entry['revision'])
        bindings.append(pub)
        if pub.get('unavailable') or not pub.get('is_current'):
            errors.append('Entry must reference a currently published selection: ' + entry['object_id'])
            continue
        material = next((m for m in pub['object']['materials'] if m['id'] == entry['material_id']), None)
        evidence = db.execute('SELECT body,content_hash FROM knowledge_evidence WHERE id=? AND record_id=?',
                              (entry['material_id'], entry['object_id'])).fetchone()
        if not material or not evidence or not entry['quote'] or entry['quote'] not in evidence['body'] or hashlib.sha256(evidence['body'].encode()).hexdigest() != material['content_hash']:
            errors.append('Entry needs a quotation from its published original material: ' + entry['object_id'])
        if not entry['summary'] or not entry['significance']:
            errors.append('Each entry needs a concise summary and reason for attention')
    token = hashlib.sha256(store.encode({'draft': dict(row), 'bindings': bindings}).encode()).hexdigest()
    return {'schema_version': p.SCHEMA_VERSION, 'id': eid, 'revision': row['revision'], 'draft': data,
            'published_revision': row['published_revision'], 'updated_at': row['updated_at'],
            'review_token': token, 'gate': {'ready': not errors, 'errors': errors}}


def edition_preview(eid):
    with get_db() as db:
        return _edition_preview(db, eid)


def save_edition(data, eid=None, expected_revision=0):
    data = _edition_data(data)
    expected_revision = p.integer(expected_revision, 'expected_revision')
    with get_db(atomic=True) as db:
        if eid:
            current = _edition_preview(db, eid)
            if current['revision'] != expected_revision:
                raise p.PlatformError('Edition changed; reload before saving', 'revision_conflict', 409)
            if current['draft'] != data:
                db.execute('UPDATE knowledge_editions SET data=?, revision=revision+1,updated_at=? WHERE id=?', (store.encode(data), store.now(), eid))
        else:
            if expected_revision:
                raise p.PlatformError('New edition needs revision zero')
            eid = uuid.uuid4().hex
            db.execute('INSERT INTO knowledge_editions VALUES(?,1,?,NULL,?)', (eid, store.encode(data), store.now()))
        return _edition_preview(db, eid)


def publish_edition(eid, review_token, reason, state='published'):
    reason = p.text(reason, 'review reason')
    if state not in ('published', 'withdrawn'):
        raise p.PlatformError('Invalid edition publication state')
    with get_db(atomic=True) as db:
        preview = _edition_preview(db, eid)
        if review_token != preview['review_token']:
            raise p.PlatformError('Edition or referenced materials changed; review again', 'revision_conflict', 409)
        if state == 'published' and not preview['gate']['ready']:
            raise p.PlatformError('; '.join(preview['gate']['errors']), 'incomplete_material', 422)
        old = db.execute('SELECT state,data FROM knowledge_edition_publications WHERE seq=?', (preview['published_revision'],)).fetchone()
        if old and old['state'] == state and (state == 'withdrawn' or store.decode(old['data'], {}) == preview['draft']):
            return preview
        if not old and state == 'withdrawn':
            raise p.PlatformError('An unpublished edition cannot be withdrawn')
        data = preview['draft'] if state == 'published' else {}
        revision = db.execute('INSERT INTO knowledge_edition_publications(edition_id,state,data,reason,created_at) VALUES(?,?,?,?,?)',
                              (eid, state, store.encode(data), reason, store.now())).lastrowid
        db.execute('UPDATE knowledge_editions SET published_revision=?,updated_at=? WHERE id=?', (revision, store.now(), eid))
        return _edition_preview(db, eid)


def _edition(db, eid, revision=None):
    draft = db.execute('SELECT published_revision FROM knowledge_editions WHERE id=?', (eid,)).fetchone()
    if not draft or not draft['published_revision']:
        raise p.PlatformError('Published edition not found', 'not_found', 404)
    revision = p.integer(revision if revision is not None else draft['published_revision'], 'edition revision', 1)
    withdrawn = db.execute("SELECT MAX(seq) FROM knowledge_edition_publications WHERE edition_id=? AND state='withdrawn'", (eid,)).fetchone()[0]
    if withdrawn and withdrawn >= revision:
        raise p.PlatformError('This edition was withdrawn', 'unavailable', 410)
    row = db.execute("SELECT * FROM knowledge_edition_publications WHERE edition_id=? AND seq=? AND state='published'", (eid, revision)).fetchone()
    if not row:
        raise p.PlatformError('Edition revision not found', 'not_found', 404)
    data = store.decode(row['data'], {})
    entries, needs_review = [], False
    for entry in data['entries']:
        pub = _readable(db, entry['object_id'], entry['revision'])
        evidence = db.execute('SELECT body FROM knowledge_evidence WHERE id=? AND record_id=?', (entry['material_id'], entry['object_id'])).fetchone()
        material = next((m for m in pub['object'].get('materials', []) if m['id'] == entry['material_id']), None)
        readable = evidence and material and hashlib.sha256(evidence['body'].encode()).hexdigest() == material['content_hash']
        if pub.get('unavailable') or not readable:
            entries.append({'object_id': entry['object_id'], 'revision': entry['revision'], 'status': 'unavailable'})
            needs_review = True
        else:
            status = 'current' if pub['is_current'] else 'needs_review'
            needs_review |= status != 'current'
            material = next(m for m in pub['object']['materials'] if m['id'] == entry['material_id'])
            entries.append({**entry, 'name': pub['object']['name'], 'status': status, 'source_url': material['source_url']})
    return {'schema_version': p.SCHEMA_VERSION, 'id': eid, 'revision': revision, 'published_at': row['created_at'],
            'title': data['title'], 'period_start': data['period_start'], 'period_end': data['period_end'],
            'entries': entries, 'needs_review': needs_review, 'is_latest_revision': revision == draft['published_revision']}


def edition(eid, revision=None):
    with get_db() as db:
        return _edition(db, eid, revision)


def editions(limit=10, cursor=None):
    limit = p.integer(limit, 'limit', 1, 100)
    with get_db(atomic=True) as db:
        if cursor:
            snapshot, position = _resume(db, cursor, 'editions', {'limit': limit})
        else:
            refs = [dict(row) for row in db.execute("SELECT e.id, pub.seq AS revision FROM knowledge_editions e "
                    "JOIN knowledge_edition_publications pub ON pub.seq=e.published_revision WHERE pub.state='published' ORDER BY pub.seq DESC").fetchall()]
            snapshot, position = _snapshot(db, 'editions', {'limit': limit}, {'items': refs}), 0
        items = []
        for ref in snapshot['data']['items'][position:position+limit]:
            try:
                items.append(_edition(db, ref['id'], ref['revision']))
            except p.PlatformError as error:
                if error.status not in (404, 410):
                    raise
                items.append({**ref, 'unavailable': True})
        return {**_page(snapshot, position, limit), 'items': items}


def edition_drafts():
    with get_db() as db:
        return {'items': [{'id': row['id'], 'revision': row['revision'], 'published_revision': row['published_revision'],
                           'title': store.decode(row['data'], {})['title'], 'updated_at': row['updated_at']}
                          for row in db.execute('SELECT * FROM knowledge_editions ORDER BY updated_at DESC LIMIT 100').fetchall()]}
