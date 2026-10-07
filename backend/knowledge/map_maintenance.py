"""Private daily research handoff and weekly consolidation, feeding the existing owner ledger."""
import json
import re
from datetime import date, timedelta
from urllib.parse import urlsplit
from backend.db import get_db
from backend.knowledge import store, technical_maps as tm, content_workspace as ws
from backend.knowledge.workspace_transactions import editorial_transaction

SUBSTANTIVE = ('method', 'experiment', 'correction')


def report_key(url):
    parsed = urlsplit(url)
    if parsed.hostname in ('arxiv.org','export.arxiv.org'):
        match = re.fullmatch(r'/(?:abs|html|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)(?:\.pdf)?', parsed.path)
        if match: return 'arxiv:'+match[1]
    return store.canonical_url(url)


def handoff():
    from backend.knowledge.candidate_priority import inputs, evaluation_context
    current = tm.maps()['items']; today = ws.today(); start = (date.fromisoformat(today)-timedelta(days=29)).isoformat()
    with get_db() as db:
        candidates = inputs(db); context = evaluation_context(db, candidates)
        checks = {r['url']: dict(r) for r in db.execute('SELECT * FROM fieldtofit_map_checks').fetchall()}
        decisions = [dict(r) for r in db.execute('SELECT event_url,fingerprint,decision,review_on,proposal FROM fieldtofit_editorial_topics').fetchall()]
    reports = {}; unknown = []; excluded = []
    for item in current:
        for r in item['reports']:
            source = next(s for s in item['sources'] if s['id'] == r['source_id'])
            key = store.canonical_url(source['url'])
            reports.setdefault(report_key(key), {'url': key, 'title': source['title'], 'ref': '', 'first_published_at': r['first_published_at'], 'map_slugs': []})['map_slugs'].append(item['slug'])
    for c in candidates:
        meta, materials = context['materials'].get(c['ref'], ({}, []))
        if c['inbox_status'] not in ('pending', 'selected'): continue
        host = (urlsplit(c['url']).hostname or '').lower()
        research = meta.get('report_type') in ('technical_report', 'paper') or host in ('arxiv.org','export.arxiv.org') or 'arxiv' in c['source'] or bool(meta.get('primary') and meta.get('change')=='official_article')
        if not research: continue
        key = store.canonical_url(c['url']); first = meta.get('first_published_at') or c.get('published_at')
        revised = meta.get('upstream_updated_at') if meta.get('revision_kind') in SUBSTANTIVE else None
        try:
            first = tm.day(first[:10]) if first else None
            activity = tm.day(revised[:10]) if revised else first
            if revised and (not first or revised[:10] < first): raise ValueError('日期顺序未核对')
        except (ValueError, TypeError): first = activity = None
        if not activity:
            unknown.append({'ref': c['ref'], 'title': c['title'], 'url': key, 'gap': '报告首次日期／实质修订日期未核对'}); continue
        uncertain_revision = meta.get('upstream_updated_at') if meta.get('revision_kind') == 'unclassified' else None
        try: potential_revision = tm.day(uncertain_revision[:10]) if uncertain_revision else None
        except (ValueError,TypeError): potential_revision = None
        if activity < start and not (potential_revision and potential_revision >= start):
            excluded.append({'ref': c['ref'], 'url': key, 'reason': '超过30日且没有实质修订日期'}); continue
        reports.setdefault(report_key(key), {'url': key, 'title': c['title'], 'ref': c['ref'], 'first_published_at': first, 'map_slugs': [],
                                 'activity_at': activity, 'potential_revision_at': potential_revision, 'revision_needs_review': bool(activity < start), 'source_primary': bool(meta.get('primary') or host == 'arxiv.org')})
    targets = []
    for identity, report in reports.items():
        url=report['url']
        check = checks.get(url, {})
        fingerprint = check.get('fingerprint')
        held = any((store.decode(d['proposal'],{}).get('report_fingerprints',{}).get(url)==fingerprint if fingerprint else False) and (d['decision'] in ('declined', 'continue', 'published') or d['decision'] == 'later' and (d['review_on'] or '') > today) for d in decisions)
        targets.append({**report, 'check_version': check.get('version', 0), 'last_checked_at': check.get('checked_at'),
                        'last_success_at': check.get('last_success_at'), 'last_status': check.get('status', 'unchecked'),
                        'fingerprint': fingerprint, 'change_kind': check.get('change_kind'), 'proposal_held': held,
                        'needs_check': check.get('checked_day') != today})
    targets.sort(key=lambda x: (not x['needs_check'], x['last_checked_at'] or '', x['url']))
    selected = [x for x in targets if x['needs_check']][:10]
    return {'day': today, 'lookback_start': start, 'targets': selected, 'reports': targets, 'backlog': max(0, sum(x['needs_check'] for x in targets)-10),
            'date_gaps': unknown[:100], 'excluded': excluded[:100], 'coverage': '现有官方研究／arXiv候选及已审地图的报告入口；不是全网覆盖',
            'weekly': {'review_due': date.fromisoformat(today).weekday() == 0, 'historical_maps': [m['slug'] for m in current if m['archived']],
                       'topics': [{'slug': m['slug'], 'question': m['question'], 'focus': m['focus']} for m in current],
                       'pending': sum(d['decision'] == 'pending' and store.decode(d['proposal'],{}).get('type')=='technical_map' for d in decisions)},
            'instructions': ['07:30读取原文并记录检查；08:00只交付提案，不自动创建草稿或发布。',
                             '先匹配已有技术问题；新报告方法、实验或更正附前后变化及位置。',
                             '每周整理重复问题、关系缺口与积压；目标1–2次有价值的更新，不凑数量。']}


def check(data):
    url = store.canonical_url(ws.text(data.get('url'), 'url', 1600))
    known = next((x for x in handoff()['reports'] if report_key(x['url']) == report_key(url)), None)
    if not known: ws.fail('入口不在研究报告队列中')
    url=known['url']
    if isinstance(data.get('version'),bool) or not isinstance(data.get('version'),int): ws.fail('检查版本须为整数')
    if data.get('version') != known['check_version']: ws.fail('检查已更新，请重新读取', 'map_check_conflict', 409)
    status = data.get('status')
    if status not in ('read', 'failed'): ws.fail('检查状态错误')
    stamp = ws.stamp(); change = data.get('change_kind', 'baseline'); fingerprint = None; proof = {}
    if status == 'read':
        if change not in ('baseline', 'unchanged', 'cosmetic', *SUBSTANTIVE): ws.fail('报告变化类型错误')
        body = ws.text(data.get('body'), 'body', 500000)
        if len(body) < 150: ws.fail('须实际读取足够的报告正文')
        fingerprint = tm.digest(body)
        first = tm.day(data.get('first_published_at'))
        revised = tm.day(data['revised_at']) if data.get('revised_at') else None
        if revised and revised < first: ws.fail('修订日期早于首次发表')
        proof = {'first_published_at': first, 'revised_at': revised,
                 'version': ws.text(data.get('report_version'), 'report_version', 100),
                 'locator': ws.text(data.get('locator'), 'locator', 300), 'note': ws.text(data.get('note'), 'note', 1600), 'excerpt': body[:2000]}
        if known.get('first_published_at') and first != known['first_published_at']: ws.fail('首次日期与登记报告不一致，请先核对来源')
        if change in SUBSTANTIVE and not revised: ws.fail('实质修订须有原文修订日期')
    else:
        proof = {'error': ws.text(data.get('error'), 'error', 1600)}
    with editorial_transaction() as db:
        previous = db.execute('SELECT * FROM fieldtofit_map_checks WHERE url=?', (url,)).fetchone()
        used = [r['url'] for r in db.execute('SELECT DISTINCT url FROM fieldtofit_map_check_events WHERE checked_day=?', (ws.today(),)).fetchall()]
        if url not in used and len(used)>=10: ws.fail('今日10份报告检查预算已用完，剩余项保留轮转', 'map_budget_reached', 409)
        if (previous['version'] if previous else 0) != data.get('version'): ws.fail('检查已更新', 'map_check_conflict', 409)
        if status == 'read' and previous and fingerprint == previous['fingerprint']: change = 'unchanged'
        if status == 'read' and previous and fingerprint != previous['fingerprint'] and change == 'unchanged': ws.fail('正文已变化，须说明变化类型')
        if status == 'read' and previous and fingerprint != previous['fingerprint'] and change == 'baseline': ws.fail('已有基线，须区分更正、方法、实验或文字调整')
        if status == 'read':
            previous_proof = store.decode(previous['proof'], {}) if previous else {}
            proof['revision_kind'] = previous_proof.get('revision_kind', 'baseline') if previous and fingerprint == previous['fingerprint'] else change
        successful = stamp if status == 'read' else previous['last_success_at'] if previous else None
        retained = fingerprint if status == 'read' else previous['fingerprint'] if previous else None
        saved = store.encode(proof) if status == 'read' else previous['proof'] if previous else '{}'
        db.execute('INSERT INTO fieldtofit_map_check_events(url,status,change_kind,proof,created_at,checked_day) VALUES(?,?,?,?,?,?)', (url, status, change if status == 'read' else 'failed', store.encode(proof), stamp, ws.today()))
        db.execute('INSERT INTO fieldtofit_map_checks(url,version,status,fingerprint,change_kind,proof,checked_at,last_success_at,error,checked_day) VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(url) DO UPDATE SET version=excluded.version,status=excluded.status,fingerprint=excluded.fingerprint,change_kind=excluded.change_kind,proof=excluded.proof,checked_at=excluded.checked_at,last_success_at=excluded.last_success_at,error=excluded.error,checked_day=excluded.checked_day',
                   (url, data['version']+1, status, retained, change if status == 'read' else previous['change_kind'] if previous else None, saved, stamp, successful, proof.get('error', ''), ws.today()))
    return {'saved': True, 'status': status, 'change_kind': change, 'public_changed': False}


def propose(data):
    candidate = data.get('content')
    if not isinstance(candidate, dict): ws.fail('须提交完整地图建议内容')
    try: graph = tm.metadata(candidate, enforce_dates=True)
    except (ValueError, KeyError, TypeError) as exc: ws.fail(str(exc))
    if not graph: ws.fail('缺少地图内容')
    current = tm.maps()['items']; target = next((m for m in current if m['slug'] == graph['slug']), None)
    duplicate = next((m for m in current if m['question'].strip().casefold() == graph['question'].strip().casefold() and m['slug'] != graph['slug']), None)
    if duplicate: ws.fail('此问题已有地图，请更新 '+duplicate['slug'])
    if data.get('base_revision') != (target['revision'] if target else None): ws.fail('公开地图已变化，请重新生成前后对照', 'map_revision_changed', 409)
    with get_db() as db:
        checks = {r['url']: dict(r) for r in db.execute('SELECT * FROM fieldtofit_map_checks').fetchall()}
    report_fingerprints = {}
    for report in graph['reports']:
        source = next(s for s in candidate['sources'] if s['id'] == report['source_id'])
        checked = next((check for url,check in checks.items() if report_key(url)==report_key(source['url'])), None)
        if not checked or checked['status'] != 'read' or checked['checked_day'] != ws.today(): ws.fail('报告须在今日实际读取成功后再建议更新')
        report_fingerprints[checked['url']] = checked['fingerprint']
        proof = store.decode(checked['proof'], {})
        if any(report[k] != proof.get(k) for k in ('first_published_at', 'revised_at')) or report['version'] != proof.get('version'): ws.fail('提案报告日期／版本与实际读取不一致')
        if report['substantive_revision'] and proof.get('revision_kind') not in SUBSTANTIVE: ws.fail('文字修订或基线检查不能冒充实质报告更新')
    if not target:
        activity = max(r['revised_at'] if r['substantive_revision'] else r['first_published_at'] for r in graph['reports'])
        if (date.fromisoformat(ws.today())-date.fromisoformat(activity)).days >= 30: ws.fail('新地图须有近30日报告或实质修订')
    changes = [{'field': k, 'before': target.get(k) if target else None, 'after': graph.get(k)} for k in tm.FIELDS if not target or target.get(k) != graph.get(k)]
    if not changes: ws.fail('没有地图内容变化，无须重复提案')
    from backend.knowledge import editorial_batches as batches
    batch = batches.create({})
    url = candidate['sources'][0]['url']; fingerprint = tm.digest([graph, candidate['sources'], report_fingerprints])
    proposal = {'title': graph['question'], 'reason': ws.text(data.get('reason'), 'reason', 2000), 'type': 'technical_map',
                'report_fingerprints':report_fingerprints, 'target_id': target['id'] if target else None, 'target_slug': graph['slug'], 'base_revision': data.get('base_revision'),
                'before_after': changes, 'website_copy': candidate, 'publication_requires_owner_review': True}
    ref = next((x['ref'] for x in handoff()['reports'] if report_key(x['url'])==report_key(url)), '')
    result = batches.propose(batch['id'], {'ref':ref, 'event_url': url, 'event_version': 'map:'+graph['slug'], 'fingerprint': fingerprint, 'proposal': proposal})
    return {**result, 'batch_id': batch['id'], 'draft_created': False, 'published': False}


def apply_proposal(topic_id, data):
    """A separate owner action after alignment; optimistic draft save, never publication."""
    from backend.knowledge import editorial_batches as batches
    with get_db() as db:
        topic = batches._topic(db, topic_id)
    proposal = topic['proposal']
    if topic['decision'] != 'continue' or topic['version'] != data.get('topic_version') or proposal.get('type') != 'technical_map':
        ws.fail('先确认当前地图提案再填入草稿', 'decision_required', 409)
    if topic['kind'] != 'news' or not topic['item_id']: ws.fail('请先将已确认提案关联近期动态')
    current = tm.maps()['items']; target = next((m for m in current if m['slug'] == proposal['target_slug']), None)
    if proposal.get('base_revision') != (target['revision'] if target else None): ws.fail('公开地图已变化，请重新对齐提案', 'map_revision_changed', 409)
    if target and target['id'] != topic['item_id']: ws.fail('已有地图须更新原条目')
    content = {**proposal['website_copy'], 'id': topic['item_id'], 'state': 'published'}
    # One concrete approved map replaces only the explicitly linked draft at the
    # caller's expected version. Source text is still governed by material gates.
    saved = ws.save('news', topic['item_id'], {'draft': content, 'draft_version': data.get('draft_version')}, approved_topic={'id':topic_id,'version':data['topic_version']})
    return {'saved': True, 'id': saved['id'], 'published': False, 'draft_version': saved['draft_version']}
