"""Append-only private dispositions for reviewed CW differences.

Identity follows the claim and its cited evidence, not a whole-page hash or the
current dossier's old value. Unrelated source edits cannot undo a disposition.
"""
import json
import uuid

from backend.knowledge import content_workspace as ws, stewardship as s
from backend.knowledge.corrections import public_item, value_at
from backend.knowledge.platform import integer, text
from backend.knowledge.workspace_transactions import editorial_transaction

TABLE = 'fieldtofit_object_check_decisions'
CLOSED = {'declined', 'evidence_withdrawn'}
PROPOSAL_SUMMARY = '官方证据与当前已审资料存在差异；具体上站文案确认后再创建草稿。'


def is_check_proposal(proposal):
    return 'object_check' in proposal or (proposal.get('summary') == PROPOSAL_SUMMARY
                                         and str(proposal.get('target_id', '')).startswith('CW-'))


def identity(change):
    return s.digest([change['field'], change['after'], change['source_url'],
                     change.get('quote', ''), change.get('source_date'),
                     change.get('upstream_version', '')])


def claim(change):
    return ws.dump([change['field'], change['after'], change['source_url']])


def available(db):
    return bool(db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (TABLE,)).fetchone())


def events(db, ident=None):
    if not available(db):
        return []
    where, args = (' WHERE object_id=?', (ident,)) if ident else ('', ())
    return [{**dict(r), 'data':json.loads(r['data'])} for r in db.execute(
        'SELECT * FROM '+TABLE+where+' ORDER BY created_at,id', args).fetchall()]


def states(history):
    latest = {}
    for row in history:
        key = row['difference_id']
        if key not in latest or row['version'] > latest[key]['version']:
            latest[key] = row
    return latest


def prior_changes(db, ident):
    rows = db.execute("SELECT json_extract(data,'$.changes') changes FROM fieldtofit_object_check_attempts WHERE object_id=? ORDER BY created_at DESC,id DESC", (ident,)).fetchall()
    return [change for row in rows for change in json.loads(row['changes'] or '[]')]


def pending(changes, baseline, history):
    latest = states(history)
    seen = set(); result = []
    for change in changes:
        key = claim(change)
        if key in seen:
            continue
        seen.add(key)
        try:
            before = value_at(baseline, change['field'])
        except ws.PlatformError:
            continue
        if before == change['after']:
            continue
        ident = identity(change); event = latest.get(ident)
        if event and event['data']['status'] in CLOSED:
            continue
        closed = [e['difference_id'] for e in latest.values()
                  if e['data']['status'] in CLOSED and claim(e['data']['change']) == key]
        result.append({**change, 'before':before, 'difference_id':ident,
                       'handling_version':event['version'] if event else 0,
                       'new_evidence_after_handling':bool(closed)})
    return result


def handled(history, baseline, changes):
    preferred = {}
    for change in changes:
        preferred.setdefault(claim(change), identity(change))
    result = []
    for event in states(history).values():
        data = event['data']
        if data['status'] not in CLOSED:
            continue
        change = data['change']; why = ''
        try:
            if value_at(baseline, change['field']) == change['after']:
                why = '当前公开档案已采用此值，无需恢复待办。'
        except ws.PlatformError:
            why = '当前公开档案已无此字段，请重新核对。'
        if preferred.get(claim(change), identity(change)) != identity(change):
            why = '已有较新的定位证据，请处理对应的新差异。'
        result.append({**event, 'can_reopen':not why, 'reopen_notice':why})
    return sorted(result, key=lambda e:(e['created_at'], e['id']), reverse=True)


def handle(day, ident, data):
    if day != ws.today():
        ws.fail('按实际当日处理差异，不补造历史')
    status = data.get('status')
    if status not in CLOSED | {'pending'}:
        ws.fail('请选择不采纳、证据已撤回或恢复待处理')
    reason = text(data.get('reason'), '处理理由', 2000)
    condition = text(data.get('recheck_condition', ''), '复查条件', 2000, status in CLOSED)
    version = integer(data.get('version'), '处理版本')
    difference_id = text(data.get('difference_id'), '差异编号', 64)
    with editorial_transaction() as db:
        if not available(db):
            ws.fail('请先初始化维护记录并重试', 'upgrade_required', 503)
        attempt = db.execute('SELECT * FROM fieldtofit_object_check_attempts WHERE day=? AND object_id=? ORDER BY created_at DESC,id DESC LIMIT 1', (day, ident)).fetchone()
        if not attempt or attempt['id'] != data.get('attempt_id'):
            ws.fail('来源尝试已变化，请重新读取', 'attempt_conflict', 409)
        observed = json.loads(attempt['data']); baseline = public_item(ident, db)
        if s.digest(baseline) != observed['baseline_hash']:
            ws.fail('已审档案已变化，请重新获取并核对', 'baseline_conflict', 409)
        history = events(db, ident); previous = states(history).get(difference_id)
        if version != (previous['version'] if previous else 0):
            ws.fail('差异处理已变化，请重新读取', 'handling_conflict', 409)
        candidates = prior_changes(db, ident)
        active = pending(candidates, baseline, history)
        if status in CLOSED:
            change = next((c for c in active if c['difference_id'] == difference_id), None)
            if not change:
                ws.fail('该差异已处理或已失效，请重新读取', 'difference_conflict', 409)
        else:
            entry = next((e for e in handled(history, baseline, candidates)
                          if e['difference_id'] == difference_id), None)
            if not entry or not entry['can_reopen']:
                ws.fail('只能恢复尚未采纳且没有更新证据替代的已处理差异', 'difference_conflict', 409)
            change = {**entry['data']['change'], 'before':value_at(baseline, entry['data']['change']['field'])}
        # The evidence snapshot is retained forever; every action adds a new version.
        change = {k:v for k,v in change.items() if k not in ('difference_id', 'handling_version', 'new_evidence_after_handling')}
        payload = {'status':status, 'previous_status':previous['data']['status'] if previous else 'pending',
                   'reason':reason, 'recheck_condition':condition or previous['data']['recheck_condition'],
                   'day':day, 'attempt_id':attempt['id'], 'change':change,
                   'actor':'authenticated_admin'}
        db.execute('INSERT INTO '+TABLE+' VALUES(?,?,?,?,?,?)',
                   (uuid.uuid4().hex, ident, difference_id, version+1, ws.dump(payload), ws.stamp()))
    from backend.knowledge.object_checks import overview
    return overview(day)


def validate_proposal(db, proposal):
    guard = proposal.get('object_check')
    if not is_check_proposal(proposal):
        return
    if 'object_check' in proposal and (not isinstance(guard, dict) or not guard.get('object_id') or not guard.get('baseline_hash')):
        ws.fail('缺少提案关联的差异核对基线')
    changes = proposal.get('changes')
    if not isinstance(changes, list) or not changes:
        ws.fail('提案须包含当前待处理差异')
    ident = guard['object_id'] if guard else proposal['target_id']
    if ident != proposal.get('target_id'):
        ws.fail('提案须关联核对的原档案')
    if any(not isinstance(c, dict) or not {'field', 'before', 'after', 'source_url'} <= c.keys()
           or not isinstance(c['field'], str) or not isinstance(c['source_url'], str)
           for c in changes):
        ws.fail('提案须包含完整的差异证据')
    baseline = public_item(ident, db)
    current = pending(prior_changes(db, ident), baseline, events(db, ident))
    expected = sorted((identity(c), c.get('handling_version', 0)) for c in changes)
    actual = sorted((c['difference_id'], c['handling_version']) for c in current)
    baseline_changed = s.digest(baseline) != guard['baseline_hash'] if guard else any(value_at(baseline,c['field']) != c['before'] for c in changes)
    if baseline_changed or not actual or actual != expected:
        ws.fail('提案差异或处理状态已变化，请从当前待办重新准备提案', 'difference_conflict', 409)
