"""Public CW history and comparisons. Private history reasons are never projected."""
import copy
import json
from backend.db import get_db
from backend.knowledge import content_workspace as ws, stewardship as s
from backend.knowledge.platform import integer

FIELDS = ('name', 'type', 'introduction', 'aliases', 'blocks', 'interpretation', 'sources', 'attention', 'submission', 'materials')


def projection(item):
    public = ws.render('watch', {**ws.seeds()['watch'], 'items': [copy.deepcopy(item)]})['items'][0]
    return {key: public[key] for key in ('id', *FIELDS) if key in public}


def snapshots(ident, db):
    if not isinstance(ident, str) or not ident.startswith('CW-'): ws.fail('首期仅支持CW持续关注档案')
    if s.resolve(ident, db) != ident: ws.fail('对象已归并，请打开当前档案', 'object_merged', 409)
    raw = s.raw_items(db); current = raw.get(ident)
    if not current or current.get('state') != 'published': ws.fail('档案未公开或已撤回', 'not_found', 404)
    rows = db.execute("SELECT seq,action,snapshot,created_at FROM fieldtofit_content_history WHERE kind='watch' AND item_id=? AND action IN ('import','publish') AND seq>COALESCE((SELECT MAX(seq) FROM fieldtofit_content_history WHERE kind='watch' AND item_id=? AND action='withdraw'),0) ORDER BY seq DESC", (ident, ident)).fetchall()
    allowed = {m['id'] for m in current.get('reading_materials', []) if m.get('coverage') in ('full_text', 'excerpt')}
    output = []
    for row in rows:
        item = json.loads(row['snapshot'])
        if item.get('state') != 'published': continue
        data = projection(item)
        # Removed/withdrawn material metadata and body are not resurrected through history.
        if 'materials' in data:
            data['materials'] = [m if m['id'] in allowed else {'id': m['id'], 'coverage': 'withdrawn', 'reason': '当前读取权限已撤回'} for m in data['materials']]
        entry = {'revision': row['seq'], 'recorded_at': row['created_at'], 'date_basis': 'migration_baseline' if row['action']=='import' else 'FieldToFit_publication',
                 'object': data}
        if not output or output[-1]['object'] != data: output.append(entry)
    return current, output


def history(ident, limit=20, offset=0):
    limit = integer(limit, 'limit', 1, 100); offset = integer(offset, 'offset', 0)
    with get_db() as db:
        current, rows = snapshots(ident, db)
    return {'id': ident, 'name': current['name'], 'items': [{k:v for k,v in r.items() if k!='object'} for r in rows[offset:offset+limit]],
            'total': len(rows), 'next_offset': offset+limit if offset+limit<len(rows) else None,
            'scope': 'Recorded public CW revisions; migration time is not the original publication date. Earlier unrecorded history is unavailable.'}


def compare(ident, from_revision=None, to_revision=None, include_unchanged=False):
    if not isinstance(include_unchanged, bool): ws.fail('include_unchanged必须为布尔值')
    with get_db() as db:
        _, rows = snapshots(ident, db)
    if len(rows) < 2: ws.fail('尚未保存两次可公开修订，无法对照', 'history_unavailable', 409)
    to_revision = integer(to_revision, 'to_revision', 1) if to_revision is not None else rows[0]['revision']
    from_revision = integer(from_revision, 'from_revision', 1) if from_revision is not None else rows[1]['revision']
    if from_revision >= to_revision: ws.fail('请选择时间较早和较新的两个不同修订')
    before = next((r for r in rows if r['revision']==from_revision), None)
    after = next((r for r in rows if r['revision']==to_revision), None)
    if not before or not after: ws.fail('修订不属于此对象，或当前权限不允许读取', 'revision_unavailable', 409)
    fields = []
    for key in FIELDS:
        old, new = before['object'].get(key), after['object'].get(key)
        changed = old != new
        if changed or include_unchanged:
            fields.append({'field': key, 'kind': 'added' if old is None else 'removed' if new is None else 'modified' if changed else 'unchanged',
                           'evidence_scope': 'dossier_sources',
                           'classification': 'editorial' if key in ('name','introduction','interpretation','aliases') else 'source_data',
                           'before': old, 'after': new, 'before_sources': before['object']['sources'], 'after_sources': after['object']['sources']})
    return {'id': ident, 'from': {k:v for k,v in before.items() if k!='object'}, 'to': {k:v for k,v in after.items() if k!='object'},
            'fields': fields, 'scope': 'FieldToFit dossier revisions, not a claim of upstream product changes. Citations belong to each dossier snapshot, not automatically matched to individual claims. No private reasons or daily check timestamps.',
            'share_path': '/watch/'+ident+'?compare_from='+str(from_revision)+'&compare_to='+str(to_revision)}
