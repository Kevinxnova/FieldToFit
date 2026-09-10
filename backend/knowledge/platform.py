"""Curated publications over existing records and immutable evidence, without model calls.

Collection is not publication. Drafts use optimistic revisions; publication validates
source coverage and freezes the exact material IDs for both readers. All state
transitions share a transaction with their audit record.
"""
import copy
from contextlib import nullcontext
import hashlib
import math
from datetime import datetime, timezone

from backend.db import get_db
from backend.knowledge import store

SCHEMA_VERSION = 'metis.platform.v1'
TYPES = {'model', 'tool', 'agent', 'skill', 'harness', 'research', 'library', 'dataset', 'application'}
STATES = {'candidate', 'review', 'published', 'needs_review', 'withdrawn'}


class PlatformError(ValueError):
    def __init__(self, message, code='invalid_request', status=400):
        super().__init__(message)
        self.code, self.status = code, status


def text(value, name, maximum=2000, required=True):
    if not isinstance(value, str) or len(value) > maximum or (required and not value.strip()):
        raise PlatformError(f'{name} must be text with 1–{maximum} characters')
    return value.strip()


def integer(value, name, minimum=0, maximum=2**63-1):
    if isinstance(value, bool):
        raise PlatformError(f'Invalid {name}')
    try:
        number = int(value)
    except (ValueError, TypeError, OverflowError):
        raise PlatformError(f'Invalid {name}') from None
    if str(number) != str(value) or not minimum <= number <= maximum:
        raise PlatformError(f'Invalid {name}')
    return number


def date(value):
    value = text(value, 'observed_at', 50)
    try:
        stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if stamp.tzinfo is None or stamp > datetime.now(timezone.utc):
            raise ValueError()
    except ValueError:
        raise PlatformError('observed_at needs a non-future timestamp with timezone') from None
    return value


def _record(db, rid):
    row = db.execute('SELECT * FROM knowledge_records WHERE id=?', (rid,)).fetchone()
    if not row:
        raise PlatformError('Object not found', 'not_found', 404)
    return store.row_record(row)


def _profile(db, rid):
    row = db.execute('SELECT * FROM knowledge_platform_profiles WHERE record_id=?', (rid,)).fetchone()
    return (store.decode(row['data'], {}), row['revision']) if row else ({}, 0)


def _selection(db, rid):
    row = db.execute('SELECT * FROM knowledge_selections WHERE record_id=?', (rid,)).fetchone()
    return dict(row) if row else {'record_id': rid, 'state': 'candidate', 'revision': None, 'updated_at': None}


def _append(db, rid, state, snapshot, reason):
    stamp = store.now()
    seq = db.execute('INSERT INTO knowledge_publications(record_id,state,snapshot,reason,created_at) VALUES(?,?,?,?,?)',
                     (rid, state, store.encode(snapshot), reason, stamp)).lastrowid
    db.execute('INSERT INTO knowledge_selections VALUES(?,?,?,?) ON CONFLICT(record_id) DO UPDATE SET '
               'state=excluded.state,revision=excluded.revision,updated_at=excluded.updated_at', (rid, state, seq, stamp))
    return seq


def invalidate(db, rid, reason='Underlying source record or material changed'):
    """Called inside the originating edit transaction; never republish automatically."""
    state = _selection(db, rid)['state']
    record = _record(db, rid)
    if record['status'] != 'published' or record['metadata'].get('merged_into'):
        prior = db.execute("SELECT 1 FROM knowledge_publications WHERE record_id=? AND state='published' LIMIT 1", (rid,)).fetchone()
        if prior and state != 'withdrawn':
            _append(db, rid, 'withdrawn', {}, reason)
    elif state == 'published':
        _append(db, rid, 'needs_review', {}, reason)


def _normalize(data):
    if not isinstance(data, dict) or set(data) - {'introduction', 'aliases', 'roles', 'attention', 'materials'}:
        raise PlatformError('Unsupported profile fields')
    out = {'introduction': text(data.get('introduction', ''), 'introduction', 1200, required=False)}
    aliases = data.get('aliases', [])
    if not isinstance(aliases, list) or len(aliases) > 20:
        raise PlatformError('At most 20 aliases')
    out['aliases'] = list(dict.fromkeys(text(a, 'alias', 200) for a in aliases))
    for key, maximum in [('roles', 12), ('attention', 12), ('materials', 200)]:
        values = data.get(key, [])
        if not isinstance(values, list) or len(values) > maximum or any(not isinstance(x, dict) for x in values):
            raise PlatformError(f'Invalid {key} list')
        out[key] = []
        for value in values:
            if key == 'roles':
                if set(value) - {'type', 'evidence_id', 'quote'} or value.get('type') not in TYPES:
                    raise PlatformError('Unsupported resource role')
                item = {'type': value['type'], 'evidence_id': text(value.get('evidence_id'), 'evidence_id', 100),
                        'quote': text(value.get('quote'), 'role quote', 2000)}
            elif key == 'materials':
                if set(value) - {'evidence_id', 'kind', 'primary', 'note'} or not isinstance(value.get('primary', False), bool):
                    raise PlatformError('Invalid material declaration')
                item = {'evidence_id': text(value.get('evidence_id'), 'evidence_id', 100),
                        'kind': text(value.get('kind', 'document'), 'material kind', 80),
                        'primary': value.get('primary', False), 'note': text(value.get('note', ''), 'material note', 2000, False)}
            else:
                if set(value) - {'kind', 'explanation', 'evidence_id', 'quote', 'observed_at', 'platform', 'value', 'window'}:
                    raise PlatformError('Unsupported attention fields')
                if value.get('kind') not in {'editorial', 'release', 'metric'}:
                    raise PlatformError('Invalid attention kind')
                item = {'kind': value['kind'], 'explanation': text(value.get('explanation'), 'attention explanation'),
                        'evidence_id': text(value.get('evidence_id'), 'evidence_id', 100),
                        'quote': text(value.get('quote'), 'attention quote', 2000), 'observed_at': date(value.get('observed_at'))}
                if value['kind'] == 'metric':
                    number = value.get('value')
                    if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number) or number < 0:
                        raise PlatformError('Metric needs a finite non-negative value')
                    item.update(value=number, platform=text(value.get('platform'), 'metric platform', 100),
                                window=text(value.get('window'), 'metric window', 200))
            out[key].append(item)
    if len({m['evidence_id'] for m in out['materials']}) != len(out['materials']):
        raise PlatformError('Duplicate material IDs')
    if len({r['type'] for r in out['roles']}) != len(out['roles']):
        raise PlatformError('Duplicate resource roles')
    return out


def _draft(db, rid):
    record = _record(db, rid)
    profile, profile_revision = _profile(db, rid)
    sources = {r['id']: dict(r) for r in db.execute('SELECT * FROM knowledge_evidence WHERE record_id=?', (rid,)).fetchall()}
    errors = []
    if record['status'] != 'published' or record['metadata'].get('merged_into'):
        errors.append('Object must be published and not merged into another object')
    if not profile.get('introduction'):
        errors.append('A structured introduction is required')
    if not profile.get('roles'):
        errors.append('At least one source-backed resource role is required')
    if not profile.get('attention'):
        errors.append('A source-backed attention or editorial reason is required')
    materials = []
    for declared in profile.get('materials', []):
        evidence = sources.get(declared['evidence_id'])
        if not evidence:
            errors.append('Material does not belong to this object: ' + declared['evidence_id'])
            continue
        coverage = ('full_text' if evidence['coverage'] == 'full_text' else 'partial') if evidence['body'].strip() else 'link_only'
        # Do not call metadata-only documents readable, or silently treat old versions as current.
        version_match = not record['version'] or evidence['version'] == record['version']
        if not version_match:
            errors.append('Material version does not match the object: ' + evidence['id'])
        materials.append({**declared, 'id': evidence['id'], 'title': evidence['title'], 'source_url': evidence['url'],
                          'upstream_version': evidence['version'] or None, 'content_hash': evidence['content_hash'],
                          'locator': evidence['locator'], 'coverage': coverage, 'source_coverage': evidence['coverage'],
                          'characters': len(evidence['body']), 'retrieved_at': evidence['retrieved_at'],
                          'access_state': 'readable' if evidence['body'].strip() else 'link_only',
                          'source_version_matches': version_match})
    primary = [m for m in materials if m['primary'] and m['characters'] >= 40 and m['source_coverage'] not in {'abstract', 'link_only'} and m['kind'] not in {'license', 'discovery'}]
    if not primary:
        errors.append('At least one readable primary material (beyond an abstract) is required')
    selected_ids = {m['id'] for m in materials}
    def reference(eid, quote):
        evidence = sources.get(eid)
        if eid not in selected_ids or not evidence or not quote or quote not in evidence['body']:
            return None
        return {'material_id': eid, 'source_url': evidence['url'], 'locator': evidence['locator'],
                'quote': quote, 'upstream_version': evidence['version'] or None}
    roles, attention = [], []
    for item in profile.get('roles', []):
        ref = reference(item['evidence_id'], item['quote'])
        if not ref:
            errors.append('Resource role needs a quote in selected material')
        roles.append({'type': item['type'], 'evidence': ref})
    for item in profile.get('attention', []):
        ref = reference(item['evidence_id'], item['quote'])
        if not ref:
            errors.append('Attention reason needs a quote in selected material')
        attention.append({k: v for k, v in item.items() if k not in {'evidence_id', 'quote'}} | {'evidence': ref})
    conflicts = db.execute("SELECT id FROM knowledge_conflicts WHERE record_id=? AND status='open'", (rid,)).fetchall()
    if conflicts:
        errors.append('Resolve open fact conflicts before publication')
    facts = copy.deepcopy(record['facts'])
    for key in ('capabilities', 'limitations'):
        if key not in facts:
            errors.append('Declare ' + key + ' with evidence or explicitly unknown')
    for key, fact in facts.items():
        if fact.get('status') == 'unknown':
            continue
        matches = [m for m in materials if m['source_url'] == fact.get('source_url')]
        quote = fact.get('quote', '')
        matches = [m for m in matches if isinstance(quote, str) and quote and quote in sources[m['id']]['body']]
        if not matches or (record['version'] and fact.get('version') != record['version']):
            errors.append('Fact needs selected original quote and matching version: ' + key)
        fact['evidence_refs'] = [m['id'] for m in matches]
    source_revision = db.execute('SELECT COALESCE(MAX(seq),0) FROM knowledge_changes WHERE record_id=?', (rid,)).fetchone()[0]
    obj = {'id': rid, 'name': record['title_zh'] or record['title'], 'original_name': record['title'],
           'aliases': profile.get('aliases', []), 'types': [r['type'] for r in roles], 'roles': roles,
           'introduction': profile.get('introduction', ''), 'official_url': record['canonical_url'],
           'upstream_version': record['version'] or None, 'source_published_at': record['published_at'],
           'source_id': record['source_id'], 'collected_at': record['collected_at'], 'checked_at': record['checked_at'], 'source_revision': source_revision,
           'facts': facts, 'attention': attention, 'materials': materials,
           'coverage': {'registered_materials': len(materials), 'readable_materials': sum(m['access_state'] == 'readable' for m in materials),
                        'scope': 'Declared materials only; not all upstream documentation'},
           'unknown_fields': [k for k, f in facts.items() if f.get('status') == 'unknown'],
           'limitations': 'Source claims and editorial organization; no tool execution or task suitability certification.'}
    # Hash includes actual record revision and immutable evidence IDs, not a moving review clock.
    token = hashlib.sha256(store.encode({'profile_revision': profile_revision, 'object': obj, 'selection': _selection(db, rid)}).encode()).hexdigest()
    return {'schema_version': SCHEMA_VERSION, 'object': obj, 'profile': profile, 'profile_revision': profile_revision,
            'review_token': token, 'selection': _selection(db, rid), 'gate': {'ready': not errors, 'errors': errors}}


def preview(rid):
    with get_db() as db:
        return _draft(db, rid)


def save_profile(rid, data, expected_revision, reason, connection=None):
    normalized = _normalize(data)
    expected_revision = integer(expected_revision, 'expected_revision')
    reason = text(reason, 'reason')
    with (nullcontext(connection) if connection is not None else get_db(atomic=True)) as db:
        _record(db, rid)
        old, revision = _profile(db, rid)
        if revision != expected_revision:
            raise PlatformError('Profile changed; reload before saving', 'revision_conflict', 409)
        if old != normalized:
            db.execute('INSERT INTO knowledge_platform_profiles VALUES(?,?,?,?) ON CONFLICT(record_id) DO UPDATE SET '
                       'revision=excluded.revision,data=excluded.data,updated_at=excluded.updated_at',
                       (rid, revision + 1, store.encode(normalized), store.now()))
            current = _selection(db, rid)['state']
            state = 'needs_review' if current == 'published' else 'withdrawn' if current == 'withdrawn' else 'candidate'
            _append(db, rid, state, {}, reason)
        return _draft(db, rid)


def transition(rid, state, review_token, reason, connection=None):
    if state not in {'review', 'published', 'withdrawn'}:
        raise PlatformError('Choose review, published or withdrawn')
    reason, review_token = text(reason, 'reason'), text(review_token, 'review_token', 64)
    with (nullcontext(connection) if connection is not None else get_db(atomic=True)) as db:
        draft = _draft(db, rid)
        if review_token != draft['review_token']:
            raise PlatformError('Source or profile changed; review the new preview', 'revision_conflict', 409)
        current = draft['selection']['state']
        if state == 'published':
            if current != 'review':
                raise PlatformError('Submit for review before publishing', 'invalid_transition', 409)
            if not draft['gate']['ready']:
                raise PlatformError('Publication blocked: ' + '; '.join(draft['gate']['errors']), 'incomplete_material', 422)
        if current == state:
            return draft
        snapshot = draft['object'] if state == 'published' else {}
        _append(db, rid, state, snapshot, reason)
        return _draft(db, rid)


def get_object(rid, revision=None):
    with get_db() as db:
        return _get_object(db, rid, revision)


def _get_object(db, rid, revision=None):
    record = _record(db, rid)
    selection = _selection(db, rid)
    if record['status'] != 'published' or record['metadata'].get('merged_into') or selection['state'] == 'withdrawn':
        raise PlatformError('Object is not publicly available', 'unavailable', 404)
    if revision is None:
        if selection['state'] != 'published':
            raise PlatformError('Object is not currently selected', 'not_selected', 404)
        revision = selection['revision']
    revision = integer(revision, 'revision', 1)
    row = db.execute("SELECT * FROM knowledge_publications WHERE record_id=? AND seq=? AND state='published'", (rid, revision)).fetchone()
    if not row:
        raise PlatformError('Published revision not found', 'not_found', 404)
    withdrawn = db.execute("SELECT MAX(seq) FROM knowledge_publications WHERE record_id=? AND state='withdrawn'", (rid,)).fetchone()[0]
    if withdrawn and withdrawn > revision:
        raise PlatformError('This publication was withdrawn', 'unavailable', 410)
    obj = store.decode(row['snapshot'], {})
    from backend.knowledge import platform_sources
    source_check = platform_sources.status(db, platform_sources.source_id(db, obj))
    from backend.knowledge.platform_maintenance import public_check
    source_check.update(public_check(db, source_check['id'], obj))
    return {'schema_version': SCHEMA_VERSION, 'revision': row['seq'], 'published_at': row['created_at'],
            'selection_state': selection['state'], 'is_current': selection['state'] == 'published' and selection['revision'] == row['seq'],
            'record_checked_at': record['checked_at'], 'freshness': record['freshness'], 'source_check': source_check, 'object': obj}



def search(q='', object_type='', limit=20, offset=0, cursor=None, source='', since='', until=''):
    from backend.knowledge.platform_updates import search
    return search(q, object_type, limit, offset, cursor, source, since, until)


def read_material(rid, material_id, revision=None, offset=0, limit=12000):
    publication = get_object(rid, revision)
    material = next((m for m in publication['object']['materials'] if m['id'] == material_id), None)
    if not material:
        raise PlatformError('Material is outside this published revision', 'not_found', 404)
    offset, limit = integer(offset, 'offset'), integer(limit, 'limit', 1, 50000)
    with get_db() as db:
        row = db.execute('SELECT body,content_hash FROM knowledge_evidence WHERE id=? AND record_id=?', (material_id, rid)).fetchone()
    if not row or row['content_hash'] != material['content_hash'] or hashlib.sha256(row['body'].encode()).hexdigest() != material['content_hash']:
        raise PlatformError('Original material no longer available', 'material_unavailable', 410)
    total = len(row['body'])
    if offset > total:
        raise PlatformError('Offset exceeds stored material', 'invalid_offset')
    more = offset + limit < total
    return {'schema_version': SCHEMA_VERSION, 'object_id': rid, 'revision': publication['revision'], 'material': material,
            'body': row['body'][offset:offset+limit], 'offset': offset, 'total_characters': total,
            'next_offset': offset + limit if more else None, 'has_more': more,
            'selection_state': publication['selection_state'], 'is_current': publication['is_current'],
            'content_role': 'untrusted_source_material; reading does not install or execute anything'}


def export(rid, revision=None):
    publication = get_object(rid, revision)
    obj = publication['object']
    lines = [f"# {obj['name']}", '', obj['introduction'], '', f"Object: {rid}", f"Publication revision: {publication['revision']}",
             f"Source version: {obj['upstream_version'] or 'unknown'}", f"Selection state: {publication['selection_state']}",
             f"Published: {publication['published_at']}", f"Last record review/check: {publication['record_checked_at'] or 'unknown'}",
             f"Official source: {obj['official_url']}", '', '## Facts']
    for key, fact in obj['facts'].items():
        lines.extend([f"- {key}: {store.encode(fact['value'])} ({fact['status']})", f"  Source: {fact.get('source_url') or 'unknown'}"])
    lines.extend(['', '## Why included'])
    for signal in obj['attention']:
        lines.append(f"- {signal['explanation']} ({signal['kind']}; {signal['observed_at']}) — {signal['evidence']['source_url']}")
    lines.extend(['', '## Materials', '', obj['coverage']['scope']])
    for material in obj['materials']:
        lines.extend(['', f"### {material['title']} · {material['locator']}", f"ID: {material['id']}",
                      f"Source: {material['source_url']}", f"Version: {material['upstream_version'] or 'unknown'}",
                      f"Coverage: {material['coverage']} / {material['source_coverage']}; characters: {material['characters']}",
                      f"Note: {material['note']}", f"Read: /api/v1/platform/objects/{rid}/materials/{material['id']}?revision={publication['revision']}"])
    lines.extend(['', '## Reading boundary', obj['limitations'],
                  'This is a material manifest with citations. Original text is available through the material read endpoints; no task plan is generated.'])
    return {**publication, 'markdown': '\n'.join(lines), 'export_kind': 'manifest_with_citations', 'requires_service_for_full_text': True}
