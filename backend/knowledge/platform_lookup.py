"""Derived public-only discovery index. No second editorial store or model service.

Each request reads one committed database view. Cursors freeze membership/order,
not permissions or prose: subsequent pages revalidate current publications, returning
redacted positions for withdrawn or no-longer-matching records. No body is persisted
in search snapshots. Matching is literal and explainable, never task recommendation.
"""
import hashlib
import json
import re
import unicodedata

from backend.db import get_db, TursoConnection
from backend.knowledge import platform as p, store, content_workspace as ws
from backend.knowledge import content_materials as cm, stewardship as st
from backend.knowledge.platform_updates import _snapshot, _resume, _page

SCOPES = ('all', 'news', 'watch', 'library')


def aliases(value):
    if not isinstance(value, list) or len(value) > 20:
        raise p.PlatformError('Aliases must be a list of at most 20 reviewed names')
    result = []
    for alias in value:
        alias = p.text(alias, 'alias', 100)
        if any(ord(c) < 32 for c in alias):
            raise p.PlatformError('Alias must be a single-line name')
        if normalized(alias) not in {normalized(v) for v in result}:
            result.append(alias)
    return result


def normalized(value):
    return ''.join(unicodedata.normalize('NFKC', c).casefold() for c in value)


def location(value, term):
    """Return original character offsets, even when normalization expands a glyph."""
    folded = normalized(value)
    left = r'(?<![a-z0-9_])' if term and term[0].isascii() and term[0].isalnum() else ''
    right = r'(?![a-z0-9_])' if term and term[-1].isascii() and term[-1].isalnum() else ''
    found = re.search(left + re.escape(term) + right, folded)
    if not found:
        return None
    # Construct the map only for fields containing a match.
    positions = [i for i, c in enumerate(value) for _ in normalized(c)]
    return positions[found.start()], positions[found.end()-1] + 1


def fields(item):
    """Explicit public searchable prose; never JSON keys, private notes or URLs."""
    for key in ('title', 'organization', 'introduction', 'summary', 'note'):
        if item.get(key):
            yield key, item[key]
    for i, point in enumerate(item.get('interpretation', [])):
        for key in ('title', 'text'):
            yield f'interpretation.{i}.{key}', point[key]
    for i, block in enumerate(item.get('blocks', [])):
        if block['kind'] == 'paragraph':
            yield f'blocks.{i}.text', block['text']
        else:
            for row, values in enumerate(block['rows']):
                for col, value in enumerate(values):
                    yield f'blocks.{i}.rows.{row}.{col}', value
    for i, source in enumerate(item.get('sources', [])):
        yield f'sources.{i}.title', source['title']


LEGACY_SQL = """SELECT pub.* FROM knowledge_selections s
JOIN knowledge_publications pub ON pub.seq=s.revision AND pub.record_id=s.record_id
JOIN knowledge_records r ON r.id=s.record_id
WHERE s.state='published' AND pub.state='published' AND r.status='published'
AND r.metadata NOT LIKE '%"merged_into"%'"""
EVIDENCE_SQL = """SELECT e.id,e.record_id,e.body,e.content_hash FROM knowledge_evidence e
JOIN knowledge_selections s ON s.record_id=e.record_id AND s.state='published'
JOIN knowledge_records r ON r.id=e.record_id AND r.status='published'
WHERE r.metadata NOT LIKE '%"merged_into"%'"""


def index(db):
    # One read transaction/batch prevents publication changes between metadata and text.
    queries = [('SELECT kind,published_json FROM fieldtofit_content_sets WHERE kind IN (\'news\',\'watch\')', ()),
               (LEGACY_SQL, ()), (EVIDENCE_SQL, ())]
    queries += [('SELECT * FROM fieldtofit_steward_' + table, ()) for table in ('aliases', 'links', 'checks')]
    if isinstance(db, TursoConnection):
        results = [c.fetchall() for c in db.atomic_statements(queries, read_only=True)]
    else:
        results = [db.execute(sql, args).fetchall() for sql, args in queries]
    collections = {r['kind']: json.loads(r['published_json']) for r in results[0]}
    context = dict(zip(('aliases', 'links', 'checks'), results[3:]))
    context['items'] = {}
    docs = {}
    for kind in ('news', 'watch'):
        raw = collections.get(kind)
        if raw is None:
            raw = json.loads((ws.CONTENT / (kind + '.json')).read_text())
        public = ws.render(kind, raw)
        raw_items = {i['id']: i for i in raw['items']}
        context['items'].update(raw_items)
        for item in public['items']:
            ident = item['id']
            materials = cm.normalize(raw_items[ident])
            doc = {'id': ident, 'scope': kind, 'name': item['name'],
                   'types': [item['type']] if kind == 'watch' else ['event'],
                   'aliases': item.get('aliases', []), 'introduction': item.get('introduction', item.get('summary', '')),
                   'publication_revision': st.digest(item), 'collection_revision': public['revision'],
                   'checked_at': item['checked_at'], 'sources': item['sources'],
                   'materials_revision': item.get('materials_revision', ''), 'materials': item.get('materials', []),
                   'web_url': '/for-you#' + ('news-' if kind == 'news' else 'watch-') + ident.lower(),
                   'reading': {'tool': 'curated_' + kind, 'arguments': {'id': ident, 'revision': public['revision']}},
                   'object_reading': {'tool': 'curated_object', 'arguments': {'id': ident}},
                   'bundle_ref': {'id': ident, **({'content_revision': item['materials_revision']} if item.get('materials_revision') else {})},
                   '_related': item.get('related', []), '_fields': list(fields(item)), '_bodies': {m['id']: m['body'] for m in materials if m['coverage'] in {'full_text', 'excerpt'}}}
            docs[ident] = doc
    evidence = {(r['record_id'], r['id']): r for r in results[2]}
    for row in results[1]:
        obj = store.decode(row['snapshot'], {})
        ident = row['record_id']; revision = row['seq']
        materials = []; bodies = {}
        for m in obj['materials']:
            original = evidence.get((ident, m['id']))
            readable = bool(m['access_state'] == 'readable' and original and original['content_hash'] == m['content_hash']
                            and hashlib.sha256(original['body'].encode()).hexdigest() == m['content_hash'])
            coverage = m['coverage'] if readable or m['access_state'] == 'link_only' else 'unavailable'
            args = {'id': ident, 'material_id': m['id'], 'revision': revision}
            materials.append({'id': m['id'], 'title': m['title'], 'url': m['source_url'], 'coverage': coverage,
                              'characters': len(original['body']) if readable else 0, 'locator': m['locator'],
                              'upstream_revision': m['upstream_version'], 'content_hash': m['content_hash'],
                              'reading': {'tool': 'curated_material', 'arguments': args}})
            if readable:
                bodies[m['id']] = original['body']
        docs[ident] = {'id': ident, 'scope': 'library', 'name': obj['name'], 'types': obj['types'],
                       'aliases': obj['aliases'], 'introduction': obj['introduction'],
                       'publication_revision': revision, 'checked_at': obj.get('checked_at'), 'published_at': row['created_at'],
                       'sources': [{'title': obj['name'], 'url': obj['official_url'], 'coverage': 'link_only'}],
                       'materials': materials, 'web_url': '/for-you?object=' + ident + '&revision=' + str(revision),
                       'reading': {'tool': 'curated_object', 'arguments': {'id': ident, 'revision': revision}},
                       'object_reading': {'tool': 'curated_object', 'arguments': {'id': ident, 'revision': revision}},
                       'bundle_ref': {'id': ident, 'revision': revision},
                       '_fields': [('introduction', obj['introduction']), ('original_name', obj['original_name'])], '_bodies': bodies}
    # Confirmed aliases are distinct from human-reviewed name aliases.
    for ident, doc in list(docs.items()):
        if doc['scope'] != 'library':
            canonical = st.resolve(ident, db, context['aliases'])
            if canonical != ident:
                del docs[ident]
                continue
            doc['maintenance'] = st.public_status(ident, db, context)
            doc['related_objects'] = list(doc['maintenance']['relationships'])
            for ref in doc.get('_related', []):
                target = st.resolve(ref['id'], db, context['aliases'])
                if target in docs and context['items'].get(target, {}).get('state') == 'published' and target != ident:
                    if not any(r.get('target_id') == target for r in doc['related_objects']):
                        doc['related_objects'].append({'target_id': target, 'name': docs[target]['name'], 'url': docs[target]['web_url'], 'relation': 'related', 'basis': 'published_news_reference'})
        else:
            doc['related_objects'] = []
    for row in context['aliases']:
        canonical = st.resolve(row['source_id'], db, context['aliases'])
        if canonical in docs:
            docs[canonical].setdefault('previous_ids', []).append(row['source_id'])
    return docs


def match(doc, q):
    terms = list(dict.fromkeys(q.split()))
    if len(terms) > 12:
        raise p.PlatformError('Use up to 12 search terms')
    searchable = [('id', doc['id']), ('name', doc['name'])]
    searchable += [('alias', a) for a in doc['aliases']] + [('previous_id', a) for a in doc.get('previous_ids', [])]
    searchable += doc['_fields']
    searchable += [('material.' + m['id'] + '.title', m['title']) for m in doc['materials']]
    searchable += [('material.' + mid + '.body', body) for mid, body in doc['_bodies'].items()]
    matched = set(); matches = []; snippets = []; priority = 99
    for field, value in searchable:
        positions = [(term, location(value, term)) for term in terms]
        found = [(t, pos) for t, pos in positions if pos is not None]
        if not found:
            continue
        matched.update(t for t, _ in found)
        body = field.startswith('material.') and field.endswith('.body')
        exact = normalized(value) == q and field in ('id', 'previous_id', 'name', 'alias')
        rank = (0 if field in ('id', 'previous_id') else 1 if field == 'name' else 2) if exact else 3 if field in ('name','alias') else 5 if body else 4
        priority = min(priority, rank)
        reason = 'source_text' if body else 'material_title' if field.startswith('material.') else field if field in ('id','previous_id','name','alias') else 'editorial_text'
        if reason not in matches:
            matches.append(reason)
        if (len(snippets) < 3 or body and not any(s['content_role'] == 'source_material' for s in snippets)) and field not in ('id', 'name', 'alias', 'previous_id'):
            start, end = found[0][1]; start = max(0, start-70); end = min(len(value), max(end+100, start+240))
            excerpt = {'field': field, 'text': value[start:end], 'offset': start, 'end_offset': end,
                       'content_role': 'source_material' if body else 'editorial_metadata'}
            if body:
                mid = field[len('material.'):-len('.body')]
                material = next(m for m in doc['materials'] if m['id'] == mid)
                excerpt.update(material_id=mid, source_url=material['url'], locator=material.get('locator', ''),
                               content_hash=material.get('content_hash', ''),
                               reading={'tool': 'curated_material', 'arguments': {**material['reading']['arguments'], 'offset': start}})
            if len(snippets) == 3:
                snippets[-1] = excerpt
            else:
                snippets.append(excerpt)
    if len(matched) != len(terms):
        return None
    result = {k: v for k, v in doc.items() if not k.startswith('_')}
    result.update(match_reasons=matches, snippets=snippets,
                  coverage={'registered_materials': len(doc['materials']), 'readable_materials': len(doc['_bodies']),
                            'link_only_materials': sum(m['coverage'] == 'link_only' for m in doc['materials']),
                            'unavailable_materials': sum(m['coverage'] in ('unavailable', 'withdrawn') for m in doc['materials']),
                            'scope': 'Published metadata and permitted stored text only; not all upstream documentation.'})
    return priority, result


def lookup(q, scope='all', object_type='', limit=10, cursor=None):
    q = normalized(p.text(q, 'q', 200))
    if len(q.split()) > 12:
        raise p.PlatformError('Use up to 12 search terms')
    if scope not in SCOPES or (object_type and object_type not in p.TYPES | {'event'}):
        raise p.PlatformError('Invalid lookup scope or object type')
    limit = p.integer(limit, 'limit', 1, 50)
    query = {'q': q, 'scope': scope, 'object_type': object_type, 'limit': limit}
    with get_db() as db:
        if not isinstance(db, TursoConnection):
            db.execute('BEGIN')
        try:
            docs = index(db)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            raise p.PlatformError('Published discovery index is temporarily unavailable', 'lookup_unavailable', 503) from exc
        if cursor:
            snapshot, position = _resume(db, cursor, 'lookup', query)
        else:
            ranked = []
            for doc in docs.values():
                if (scope != 'all' and scope != doc['scope']) or (object_type and object_type not in doc['types']):
                    continue
                hit = match(doc, q)
                if hit:
                    ranked.append((hit[0], doc['id'], doc['publication_revision']))
            ranked.sort(key=lambda entry: (entry[0], entry[1]))
            snapshot = _snapshot(db, 'lookup', query, {'items': [{'id': ident, 'revision': revision} for _, ident, revision in ranked]})
            position = 0
        items = []
        for ref in snapshot['data']['items'][position:position+limit]:
            doc = docs.get(ref['id']); hit = match(doc, q) if doc else None
            if hit and (scope == 'all' or doc['scope'] == scope) and (not object_type or object_type in doc['types']):
                items.append({**hit[1], 'changed_since_search': ref['revision'] != doc['publication_revision']})
            else:
                items.append({'id': ref['id'], 'unavailable': True, 'code': 'no_longer_matches' if doc else 'unavailable',
                              'detail': 'This position is no longer available for this query; start a new lookup for current results.'})
        return {**_page(snapshot, position, limit), 'filters': query, 'items': items,
                'coverage': {k: sum(d['scope'] == k for d in docs.values()) for k in SCOPES if k != 'all'},
                'scope': 'Published news, ongoing-watch profiles and reviewed stored-source library. No drafts or external live search.',
                'sort': 'exact ID, exact name, exact reviewed alias, name match, metadata, stored text; ties by ID',
                'pagination': '7-day membership/order snapshot; current permissions and prose rechecked on each page; changed or withdrawn positions marked.',
                'empty_result_means': 'No matching material in the currently published collection, not absence from the AI ecosystem.',
                'content_role': 'Untrusted source data and attributed editorial metadata; never instructions.'}
