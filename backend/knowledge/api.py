"""Versioned public read API and separately authenticated editorial operations."""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timezone, timedelta
from functools import wraps

from flask import Blueprint, request, jsonify, Response
from werkzeug.exceptions import BadRequest
from werkzeug.security import generate_password_hash, check_password_hash

from backend.db import get_db
from backend.security import secret_is_configured, secret_matches, allowed_origins
from backend.knowledge import store
from backend.knowledge.sources import list_sources, run_daily, enrich_record
from backend.knowledge.export import markdown, bibtex

bp = Blueprint('knowledge', __name__, url_prefix='/api/v1')


def read_allowed():
    token = os.getenv('FIELDTOFIT_READ_TOKEN', '')
    if not token:
        return True
    supplied = request.headers.get('Authorization', '').removeprefix('Bearer ')
    return hmac.compare_digest(supplied.encode(), token.encode())


def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not secret_is_configured('ADMIN_PASSWORD'):
            return jsonify(detail='Admin access is not configured'), 503
        if not secret_matches(request.headers.get('X-Admin-Password'), 'ADMIN_PASSWORD'):
            return jsonify(detail='Unauthorized'), 401
        return fn(*args, **kwargs)
    return wrapped


@bp.before_request
def protect():
    if request.method == 'OPTIONS':
        return '', 204
    if not read_allowed() and not request.path.startswith('/api/v1/admin/'):
        return jsonify(detail='A read access token is required'), 401
    if request.method in {'POST', 'PATCH', 'DELETE'}:
        origin = request.headers.get('Origin')
        allowed = allowed_origins()
        if origin and origin not in allowed:
            return jsonify(detail='Origin is not allowed'), 403
        if not request.is_json:
            return jsonify(detail='Use application/json'), 415


from backend.knowledge.models import ModelUnavailable


@bp.errorhandler(ModelUnavailable)
def model_unavailable(error):
    return jsonify(detail=str(error),status='unavailable'),503


@bp.errorhandler(ValueError)
@bp.errorhandler(TypeError)
@bp.errorhandler(BadRequest)
def invalid_input(error):
    return jsonify(detail=str(error) if isinstance(error, ValueError) else 'Invalid request data', api_version='1'), 400


def body():
    data = request.get_json()
    if not isinstance(data, dict):
        raise ValueError('A JSON object is required')
    return data


def required_text(data, key, maximum=2000):
    value = data.get(key, '')
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f'{key} must contain 1–{maximum} characters')
    return value.strip()


@bp.get('/overview')
def overview():
    return jsonify(store.overview())


@bp.get('/records')
def records():
    args = {k: request.args[k] for k in ('q', 'kind', 'topic', 'source', 'since', 'until', 'object_type', 'limit', 'offset', 'sort', 'capability') if k in request.args}
    if 'ids' in request.args:
        args['ids'] = request.args['ids'].split(',')
    return jsonify(store.search_records(**args))


@bp.get('/catalog')
def catalog():
    return jsonify(store.catalog())


@bp.get('/records/<rid>')
def record(rid):
    data = store.get_record(rid)
    return (jsonify(data), 200) if data else (jsonify(detail='Record not found or withdrawn'), 404)


@bp.get('/records/<rid>/history/<int:sequence>')
def revision(rid, sequence):
    if not store.get_record(rid):
        return jsonify(detail='Record not found'), 404
    with get_db() as db:
        row = db.execute('SELECT * FROM knowledge_changes WHERE record_id=? AND seq=?', (rid, sequence)).fetchone()
    if not row:
        return jsonify(detail='Revision not found'), 404
    data = dict(row); data['snapshot'] = store.decode(data['snapshot'], {})
    if data['snapshot'].get('status') != 'published':
        return jsonify(detail='Revision is not publicly available'), 404
    return jsonify(data)


def evidence_data(eid, offset=0, limit=12000):
    offset, limit = int(offset), int(limit)
    if offset < 0 or not 1 <= limit <= 100000:
        raise ValueError('Invalid material offset or limit')
    with get_db() as db:
        row = db.execute("SELECT e.* FROM knowledge_evidence e JOIN knowledge_records r ON r.id=e.record_id WHERE e.id=? AND r.status='published'", (eid,)).fetchone()
    if not row:
        raise ValueError('Evidence not found or withdrawn')
    data = dict(row)
    total = len(data['body'])
    data.update(body=data['body'][offset:offset + limit], total_characters=total, offset=offset,
                next_offset=offset + limit if offset + limit < total else None,
                truncated=offset + limit < total, api_version='1')
    return data


@bp.get('/evidence/<eid>')
def evidence(eid):
    return jsonify(evidence_data(eid, request.args.get('offset', 0), request.args.get('limit', 12000)))


@bp.get('/records/<rid>/export')
def export(rid):
    data = store.get_record(rid)
    if not data:
        return jsonify(detail='Record not found'), 404
    fmt = request.args.get('format', 'markdown')
    if fmt == 'json':
        return jsonify(data)
    if fmt not in {'markdown', 'bibtex'}:
        raise ValueError('Supported formats: markdown, bibtex, json')
    content = bibtex(data) if fmt == 'bibtex' else markdown(data)
    return Response(content, content_type='text/plain; charset=utf-8', headers={
        'Content-Disposition': f'attachment; filename="fieldtofit-{rid}.{ "bib" if fmt == "bibtex" else "md"}"'})


def compare_data(ids, constraints=None):
    if not isinstance(ids, list) or not 2 <= len(set(ids)) <= 4 or any(not isinstance(x, str) for x in ids):
        raise ValueError('Choose 2–4 distinct record IDs')
    items = [store.get_record(rid) for rid in dict.fromkeys(ids)]
    if any(item is None for item in items):
        raise ValueError('A selected record is missing or withdrawn')
    for item in items:
        item['constraint_matches'] = store.constraint_match(item, constraints or {})
    from backend.knowledge.tasks import research_compare
    return {'research_comparison': research_compare(items) if any(i['kind']=='paper' for i in items) else None, 'items': items, 'constraints': constraints or {}, 'note': 'Compare only equivalent task and evaluation settings; missing facts are unknown.', 'api_version': '1'}


@bp.post('/compare')
def compare():
    data = body()
    return jsonify(compare_data(data.get('ids'), data.get('constraints')))


@bp.post('/task')
def task():
    data = body()
    return jsonify(store.task_pack(required_text(data, 'goal', 2000), data.get('constraints'), data.get('persona', 'engineer'), limit=data.get('limit',12), offset=data.get('offset',0), background=data.get('background',''), enhanced=data.get('enhanced',False), task_spec=data.get('task_spec'),object_type=data.get('object_type',''),capability=data.get('capability','')))


@bp.get('/changes')
def changes():
    return jsonify(store.changes(request.args.get('after', 0), request.args.get('limit', 100), request.args.get('since', ''), request.args.get('record_id', ''), record_ids=request.args['record_ids'].split(',') if 'record_ids' in request.args and request.args['record_ids'] else ([] if 'record_ids' in request.args else None), topics=request.args['topics'].split(',') if request.args.get('topics') else None, until_cursor=request.args.get('until_cursor')))


@bp.get('/sources')
def sources():
    return jsonify(items=[{k: s[k] for k in ('id', 'name', 'category', 'url', 'enabled', 'interval_days', 'last_attempt_at', 'last_success_at', 'status')} for s in list_sources()], interval_days=1)


@bp.get('/cases')
def cases():
    with get_db() as db:
        rows = [dict(r) for r in db.execute("SELECT v.*,r.title AS record_title,r.kind FROM knowledge_verifications v JOIN knowledge_records r ON r.id=v.record_id WHERE r.status='published' ORDER BY v.checked_at DESC LIMIT 100").fetchall()]
    return jsonify(items=rows, scope='Recorded task checks only; not blanket certification')


@bp.post('/feedback')
def feedback():
    data = body()
    content = required_text(data, 'content')
    category = data.get('category', 'correction')
    if category not in {'correction', 'missing', 'use_case', 'success', 'failure', 'reuse'}:
        raise ValueError('Invalid feedback category')
    rid = data.get('record_id')
    if rid and not store.get_record(rid):
        raise ValueError('Record not found')
    with get_db() as db:
        fid = db.execute('INSERT INTO knowledge_feedback(record_id,category,content,created_at) VALUES(?,?,?,?)', (rid, category, content, store.now())).lastrowid
    return jsonify(ok=True, id=fid), 201


@bp.get('/admin/sources')
@admin_required
def admin_sources():
    with get_db() as db:
        runs = [dict(r) for r in db.execute('SELECT * FROM knowledge_runs ORDER BY id DESC LIMIT 100').fetchall()]
        feedback_rows = [dict(r) for r in db.execute('SELECT * FROM knowledge_feedback ORDER BY id DESC LIMIT 100').fetchall()]
    return jsonify(items=list_sources(), runs=runs, feedback=feedback_rows)


@bp.patch('/admin/sources/<sid>')
@admin_required
def update_source(sid):
    from backend.knowledge.editorial import sources_save
    return jsonify(sources_save(body(),sid))


@bp.post('/admin/sources/<sid>/run')
@admin_required
def retry_source(sid):
    if not any(s['id'] == sid for s in list_sources()):
        return jsonify(detail='Source not found'), 404
    return jsonify(run_daily(sid, force=True))


@bp.post('/admin/records')
@admin_required
def new_record():
    data = body()
    for key in ('title', 'canonical_url'):
        required_text(data, key)
    rid, changed = store.save_record(data, required_text(data, 'reason'))
    return jsonify(id=rid, changed=changed), 201


@bp.patch('/admin/records/<rid>')
@admin_required
def update_record(rid):
    previous = store.get_record(rid, include_withdrawn=True)
    if not previous:
        return jsonify(detail='Record not found'), 404
    data = body(); reason = required_text(data, 'reason')
    allowed = {'title', 'title_zh', 'summary', 'summary_zh', 'topics', 'facts', 'status', 'version', 'completeness', 'object_type'}
    previous.update({k: v for k, v in data.items() if k in allowed})
    previous['metadata']['editorial_override'] = True
    previous['checked_at'] = store.now()
    store.save_record(previous, reason, rid)
    return jsonify(ok=True, record=store.get_record(rid, include_withdrawn=True))


@bp.post('/admin/records/<rid>/enrich')
@admin_required
def enrich(rid):
    return jsonify(enrich_record(rid))


@bp.post('/admin/records/<rid>/evidence')
@admin_required
def add_evidence(rid):
    if not store.get_record(rid, include_withdrawn=True):
        return jsonify(detail='Record not found'), 404
    data = body()
    eid = store.add_evidence(rid, required_text(data, 'url'), required_text(data, 'title'),
                             data.get('body', ''), data.get('locator', ''), data.get('version', ''),
                             data.get('evidence_type', 'documented'), data.get('coverage', 'excerpt'))
    return jsonify(id=eid), 201


@bp.post('/admin/relations')
@admin_required
def relation():
    data = body()
    store.relate(required_text(data, 'from_id'), required_text(data, 'to_id'), required_text(data, 'relation'),
                 required_text(data, 'evidence_url'), data.get('note', ''))
    return jsonify(ok=True), 201


@bp.post('/admin/records/<rid>/verify')
@admin_required
def verify(rid):
    record = store.get_record(rid)
    if not record:
        return jsonify(detail='Record not found'), 404
    data = body()
    if data.get('result') not in {'passed', 'failed', 'not_run'}:
        raise ValueError('Invalid verification result')
    fields = [required_text(data, k, 20000) for k in ('title', 'method', 'environment', 'steps', 'expected')]
    vid = secrets.token_hex(12)
    with get_db() as db:
        db.execute('INSERT INTO knowledge_verifications VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                   (vid, rid, fields[0], fields[1], data.get('version', record['version']), fields[2], fields[3], fields[4],
                    data['result'], required_text(data, 'output', 50000), required_text(data, 'limitations', 10000), store.now()))
    return jsonify(id=vid), 201


def current_user():
    token = request.cookies.get('metis_session', '')
    if not token:
        return None
    with get_db() as db:
        row = db.execute('SELECT u.id,u.username FROM knowledge_users u JOIN knowledge_sessions s ON s.user_id=u.id WHERE s.token_hash=? AND s.expires_at>?',
                         (hashlib.sha256(token.encode()).hexdigest(), store.now())).fetchone()
    return dict(row) if row else None


@bp.get('/account')
def account():
    return jsonify(user=current_user(), registration_enabled=os.getenv('FIELDTOFIT_PUBLIC_ACCOUNTS') == '1')


@bp.post('/account/<action>')
def account_action(action):
    data = body()
    if action == 'logout':
        token = request.cookies.get('metis_session', '')
        with get_db() as db:
            db.execute('DELETE FROM knowledge_sessions WHERE token_hash=?', (hashlib.sha256(token.encode()).hexdigest(),))
        response = jsonify(ok=True); response.delete_cookie('metis_session'); return response
    if action not in {'login', 'register'}:
        raise ValueError('Invalid account action')
    username = required_text(data, 'username', 80).lower()
    password = required_text(data, 'password', 200)
    with get_db() as db:
        if action == 'register':
            if os.getenv('FIELDTOFIT_PUBLIC_ACCOUNTS') != '1':
                return jsonify(detail='Account registration is disabled; local collections remain available'), 403
            if len(password) < 10:
                raise ValueError('Use a password with at least 10 characters')
            if db.execute('SELECT id FROM knowledge_users WHERE username=?', (username,)).fetchone():
                return jsonify(detail='Username unavailable'), 409
            db.execute('INSERT INTO knowledge_users VALUES(?,?,?,?)', (secrets.token_hex(12), username, generate_password_hash(password), store.now()))
        user = db.execute('SELECT * FROM knowledge_users WHERE username=?', (username,)).fetchone()
        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify(detail='Invalid username or password'), 401
        token = secrets.token_urlsafe(32)
        expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat().replace('+00:00', 'Z')
        db.execute('INSERT INTO knowledge_sessions VALUES(?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), user['id'], expires))
    response = jsonify(user={'id': user['id'], 'username': user['username']})
    response.set_cookie('metis_session', token, httponly=True, secure=request.is_secure, samesite='Strict', max_age=30 * 86400)
    return response


@bp.route('/collection', methods=['GET', 'POST', 'DELETE'])
def collection():
    user = current_user()
    if not user:
        return jsonify(detail='Sign in to sync your collection'), 401
    with get_db() as db:
        if request.method == 'GET':
            return jsonify(items=[dict(r) for r in db.execute('SELECT record_id,action,created_at FROM knowledge_collections WHERE user_id=?', (user['id'],)).fetchall()])
        data = body(); rid = required_text(data, 'record_id'); action = data.get('action', 'save')
        if action not in {'save', 'follow'}:
            raise ValueError('Invalid collection action')
        if not rid.startswith('topic:') and not store.get_record(rid):
            raise ValueError('Record not found')
        if rid.startswith('topic:') and rid[6:] not in store.TOPICS:
            raise ValueError('Invalid topic')
        if request.method == 'DELETE':
            db.execute('DELETE FROM knowledge_collections WHERE user_id=? AND record_id=? AND action=?', (user['id'], rid, action))
        else:
            db.execute('INSERT OR IGNORE INTO knowledge_collections VALUES(?,?,?,?)', (user['id'], rid, action, store.now()))
    return jsonify(ok=True)


@bp.get('/briefs')
def brief_list():
    from backend.knowledge.processing import briefs
    return jsonify(briefs(request.args.get('date')))


@bp.post('/task/export')
def export_task():
    from backend.knowledge.tasks import pack,task_markdown
    data=body()
    packet=pack(required_text(data,'goal'),data.get('constraints'),data.get('persona','engineer'),limit=data.get('limit',50),offset=data.get('offset',0),background=data.get('background',''),task_spec=data.get('task_spec'),enhanced=data.get('enhanced',False),object_type=data.get('object_type',''),capability=data.get('capability',''))
    return Response(task_markdown(packet),content_type='text/markdown; charset=utf-8')


@bp.post('/research')
def research():
    from backend.knowledge.tasks import reading_list
    data=body(); ids=data.get('ids')
    if ids is not None and (not isinstance(ids,list) or not 1<=len(ids)<=20 or any(not isinstance(i,str) for i in ids)):
        raise ValueError('Choose 1–20 record IDs')
    return jsonify(reading_list(required_text(data,'goal'),ids,data.get('background',''),data.get('enhanced',False)))


@bp.get('/capabilities')
def capabilities():
    from backend.knowledge.models import configuration
    cfg=configuration()
    return jsonify(generation_available=cfg['enabled'] and cfg['credential_configured'], accounts_available=False, interval_days=1)


@bp.get('/admin/processing')
@admin_required
def processing_list():
    from backend.knowledge.processing import processing_status
    return jsonify(processing_status())


@bp.post('/admin/processing')
@admin_required
def processing_run():
    from backend.knowledge.processing import run_processing,build_brief
    data=body(); limit=int(data.get('limit',5))
    if not 1<=limit<=30: raise ValueError('Process 1–30 records at a time')
    result=run_processing(limit=limit,record_id=data.get('record_id'),force=bool(data.get('force')),budget_seconds=240)
    build_brief()
    return jsonify(result)


@bp.post('/admin/briefs')
@admin_required
def make_brief():
    from backend.knowledge.processing import build_brief
    return jsonify(build_brief(body().get('date')))


@bp.route('/admin/model',methods=['GET','PATCH','POST'])
@admin_required
def model_settings():
    from backend.knowledge.models import configuration,configure,generate_json
    if request.method=='GET': return jsonify(configuration())
    if request.method=='PATCH': return jsonify(configure(body()))
    result,generation=generate_json('Return {"ok":true,"zh":"连接成功","en":"Connected"}.',{},max_tokens=500)
    return jsonify(result=result,generation=generation)


@bp.get('/admin/records')
@admin_required
def review_records():
    from backend.knowledge.editorial import review_queue
    return jsonify(review_queue(request.args.get('status',''),request.args.get('q',''),request.args.get('need',''),request.args.get('limit',30),request.args.get('offset',0)))


@bp.get('/admin/records/<rid>')
@admin_required
def read_editor_record(rid):
    item=store.get_record(rid,include_withdrawn=True)
    return (jsonify(item),200) if item else (jsonify(detail='Record not found'),404)


@bp.post('/admin/sources')
@admin_required
def create_source():
    from backend.knowledge.editorial import sources_save
    return jsonify(sources_save(body())),201


@bp.post('/admin/sources/<sid>/backfill')
@admin_required
def source_backfill(sid):
    from backend.knowledge.paging import save_progress
    data=body(); since=required_text(data,'since')
    datetime.fromisoformat(since.replace('Z','+00:00'))
    if not any(s['id']==sid for s in list_sources()): raise ValueError('Source not found')
    save_progress(sid,{'watermark':since,'offset':0,'status':'backfill_requested'})
    return jsonify(ok=True)


@bp.get('/admin/duplicates')
@admin_required
def duplicate_candidates():
    from backend.knowledge.editorial import suggestions
    return jsonify(suggestions())


@bp.post('/admin/merge')
@admin_required
def merge_records():
    from backend.knowledge.editorial import merge
    data=body()
    return jsonify(merge(required_text(data,'target_id'),data.get('record_ids'),required_text(data,'reason')))


@bp.post('/admin/actions/<aid>/undo')
@admin_required
def undo_editor_action(aid):
    from backend.knowledge.editorial import undo
    return jsonify(undo(aid,required_text(body(),'reason')))


@bp.post('/admin/conflicts/<cid>/resolve')
@admin_required
def resolve_conflict(cid):
    from backend.knowledge.editorial import resolve
    data=body()
    return jsonify(resolve(cid,data.get('choice'),required_text(data,'reason')))


@bp.patch('/admin/feedback/<int:fid>')
@admin_required
def triage_feedback(fid):
    data=body()
    if data.get('status') not in {'pending','reviewing','resolved','declined'}: raise ValueError('Invalid feedback state')
    note=required_text(data,'resolution'); rid=data.get('record_id')
    if rid and not store.get_record(rid,include_withdrawn=True): raise ValueError('Linked record not found')
    with get_db() as db:
        if not db.execute('SELECT id FROM knowledge_feedback WHERE id=?',(fid,)).fetchone(): raise ValueError('Feedback not found')
        db.execute('INSERT INTO knowledge_feedback_actions VALUES(?,?,?,?,?) ON CONFLICT(feedback_id) DO UPDATE SET status=excluded.status,resolution=excluded.resolution,record_id=excluded.record_id,updated_at=excluded.updated_at',(fid,data['status'],note,rid,store.now()))
    return jsonify(ok=True)



@bp.get('/admin/checks')
@admin_required
def checks_list():
    from backend.knowledge.verification import available_checks
    return jsonify(items=available_checks())


@bp.post('/admin/checks/<check_id>/run')
@admin_required
def check_run(check_id):
    from backend.knowledge.verification import run_check
    return jsonify(run_check(check_id,required_text(body(),'record_id')))


@bp.post('/admin/organization/import')
@admin_required
def import_organization():
    from backend.knowledge.processing import import_batch
    return jsonify(import_batch(body()))


@bp.get('/admin/operations')
@admin_required
def operations_status():
    from backend.knowledge.operations import snapshot
    return jsonify(snapshot())


# The curated platform is additive: legacy workspaces and /records remain compatible.
from backend.knowledge import platform, platform_updates


@bp.errorhandler(platform.PlatformError)
def platform_error(error):
    return jsonify(detail=str(error), code=error.code, schema_version=platform.SCHEMA_VERSION), error.status


@bp.get('/platform/objects')
def platform_objects():
    return jsonify(platform.search(**{k: request.args[k] for k in ('q', 'object_type', 'limit', 'offset', 'cursor', 'source', 'since', 'until') if k in request.args}))


@bp.get('/platform/objects/<rid>')
def platform_object(rid):
    return jsonify(platform.get_object(rid, request.args.get('revision')))


@bp.get('/platform/objects/<rid>/materials/<mid>')
def platform_material(rid, mid):
    return jsonify(platform.read_material(rid, mid, **{k: request.args[k] for k in ('revision', 'offset', 'limit') if k in request.args}))


@bp.get('/platform/objects/<rid>/export')
def platform_export(rid):
    result = platform.export(rid, request.args.get('revision'))
    fmt = request.args.get('format', 'markdown')
    if fmt == 'json':
        return jsonify(result)
    if fmt != 'markdown':
        raise platform.PlatformError('Choose markdown or json')
    return Response(result['markdown'], content_type='text/markdown; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename="fieldtofit-publication-{result["revision"]}.md"'})


@bp.get('/admin/platform/objects/<rid>')
@admin_required
def platform_preview(rid):
    return jsonify(platform.preview(rid))


@bp.patch('/admin/platform/objects/<rid>')
@admin_required
def platform_profile(rid):
    data = body()
    return jsonify(platform.save_profile(rid, data.get('profile'), data.get('expected_revision'), required_text(data, 'reason')))


@bp.post('/admin/platform/objects/<rid>/transition')
@admin_required
def platform_transition(rid):
    data = body()
    return jsonify(platform.transition(rid, required_text(data, 'state'), required_text(data, 'review_token'), required_text(data, 'reason')))


@bp.get('/platform/changes')
def platform_changes():
    args = {k: request.args[k] for k in ('after', 'limit', 'cursor') if k in request.args}
    if 'object_id' in request.args:
        args['object_ids'] = request.args.getlist('object_id')
    return jsonify(platform_updates.changes(**args))


@bp.get('/platform/editions')
def platform_editions():
    return jsonify(platform_updates.editions(**{k: request.args[k] for k in ('limit', 'cursor') if k in request.args}))


@bp.get('/platform/editions/<eid>')
def platform_edition(eid):
    return jsonify(platform_updates.edition(eid, request.args.get('revision')))


@bp.get('/admin/platform/editions')
@admin_required
def platform_edition_drafts():
    return jsonify(platform_updates.edition_drafts())


@bp.post('/admin/platform/editions')
@admin_required
def platform_edition_create():
    return jsonify(platform_updates.save_edition(body().get('draft')))


@bp.get('/admin/platform/editions/<eid>')
@admin_required
def platform_edition_preview(eid):
    return jsonify(platform_updates.edition_preview(eid))


@bp.patch('/admin/platform/editions/<eid>')
@admin_required
def platform_edition_save(eid):
    data = body()
    return jsonify(platform_updates.save_edition(data.get('draft'), eid, data.get('expected_revision')))


@bp.post('/admin/platform/editions/<eid>/transition')
@admin_required
def platform_edition_publish(eid):
    data = body()
    return jsonify(platform_updates.publish_edition(eid, required_text(data, 'review_token'), required_text(data, 'reason'), required_text(data, 'state')))


@bp.get('/admin/platform/selections')
@admin_required
def platform_admin_selections():
    return jsonify(platform.search(**{k: request.args[k] for k in ('q', 'object_type', 'limit', 'cursor', 'source', 'since', 'until') if k in request.args}))


@bp.post('/platform/bundle')
def platform_bundle():
    from backend.knowledge.platform_bundle import build
    data = body()
    if set(data) - {'objects', 'max_characters', 'format'}:
        raise platform.PlatformError('Unsupported package fields')
    return jsonify(build(data.get('objects'), data.get('max_characters', 200000), data.get('format', 'json')))


@bp.get('/platform/sources')
def platform_sources():
    from backend.knowledge.platform_sources import sources
    return jsonify(sources())


@bp.get('/platform/objects/<rid>/history')
def platform_history(rid):
    return jsonify(platform_updates.history(rid, **{k:request.args[k] for k in ('revision','limit','cursor') if k in request.args}))


@bp.get('/admin/platform/intake')
@admin_required
def platform_intake():
    from backend.knowledge.platform_maintenance import jobs
    response = jsonify(jobs(request.args.get('limit', 30)))
    response.headers['Cache-Control'] = 'no-store'
    return response


@bp.post('/admin/platform/intake/review')
@admin_required
def platform_intake_review():
    from backend.knowledge.platform_maintenance import apply
    return jsonify(apply(body(), publish=False))


@bp.post('/admin/platform/intake/publish')
@admin_required
def platform_intake_publish():
    from backend.knowledge.platform_maintenance import apply
    return jsonify(apply(body(), publish=True))


@bp.get("/platform/news")
def platform_news():
    from backend.knowledge.platform_news import news
    return jsonify(news(**{k: request.args[k] for k in ("q", "id", "revision") if k in request.args}))


@bp.get("/platform/watch")
def platform_watch():
    from backend.knowledge.platform_watch import watch
    return jsonify(watch(**{k: request.args[k] for k in ("q", "id", "type", "revision", "origin") if k in request.args}))


@bp.get('/platform/model-landscape')
def platform_model_landscape():
    from backend.knowledge.model_landscape import snapshot
    return jsonify(snapshot())
