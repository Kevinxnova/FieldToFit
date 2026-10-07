"""Reviewed question maps are an optional projection of news, never a second publication store."""
import copy
import hashlib
import json
import math
import re
from datetime import date, timedelta
from backend.db import get_db
from backend.knowledge.platform import PlatformError

RELATIONS = ('inheritance', 'baseline', 'parallel')
FIELDS = ('question', 'focus', 'takeaway', 'caution', 'change_summary', 'reports', 'nodes', 'edges')


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def day(value, enforce_dates=True):
    if not isinstance(value, str): raise ValueError('报告日期须为明确的日历日期')
    result = date.fromisoformat(value)
    from backend.knowledge.content_workspace import today
    if enforce_dates and result > date.fromisoformat(today()): raise ValueError('报告日期不能在未来')
    return result.isoformat()


def metadata(item, enforce_dates=False):
    value = item.get('technical_map')
    if value is None: return None
    if not isinstance(value, dict): raise ValueError('技术地图须为对象')
    from backend.knowledge.platform import text
    def words(obj, key, maximum=1600): return text(obj.get(key), key, maximum)
    slug = words(value, 'slug', 80)
    if not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', slug): raise ValueError('地图入口须为英文小写短名称')
    out = {'slug': slug, **{key: words(value, key) for key in FIELDS[:5]}}
    sources = {s['id']: s for s in item.get('sources', [])}
    from urllib.parse import urlsplit
    import ipaddress
    for source in sources.values():
        parsed = urlsplit(source.get('url','')); host = (parsed.hostname or '').lower()
        if parsed.scheme != 'https' or not host or parsed.username or parsed.password or host == 'localhost' or host.endswith(('.local','.localhost')):
            raise ValueError('地图出处须为公开 HTTPS 链接')
        try: address = ipaddress.ip_address(host)
        except ValueError: address = None
        if address and not address.is_global: raise ValueError('地图出处不能使用私有地址')
    def evidence(obj):
        points = obj.get('evidence')
        if not isinstance(points, list) or not 1 <= len(points) <= 8: raise ValueError('每个节点和关系须有报告位置')
        result = []
        for point in points:
            if not isinstance(point,dict): raise ValueError('报告位置须为对象')
            source = words(point, 'source_id', 100)
            if source not in sources: raise ValueError('地图依据须引用已登记出处')
            fragment = point.get('fragment', '')
            if not isinstance(fragment, str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{0,100}', fragment): raise ValueError('原文锚点格式错误')
            result.append({'source_id': source, 'locator': words(point, 'locator', 300), 'fragment': fragment})
        return result
    reports = value.get('reports')
    if not isinstance(reports, list) or not 1 <= len(reports) <= 30: raise ValueError('地图须登记1至30份报告')
    out['reports'] = []
    for report in reports:
        if not isinstance(report,dict): raise ValueError('报告须为对象')
        source = words(report, 'source_id', 100)
        if source not in sources: raise ValueError('报告须引用已登记出处')
        first = day(report.get('first_published_at'), enforce_dates)
        revised = day(report['revised_at'], enforce_dates) if report.get('revised_at') else None
        if revised and revised < first: raise ValueError('报告修订不能早于首次发布')
        substantive = report.get('substantive_revision', False)
        if not isinstance(substantive, bool): raise ValueError('实质修订标记须为布尔值')
        note = report.get('revision_note', '')
        if not isinstance(note, str) or len(note) > 1600: raise ValueError('报告修订说明错误')
        if substantive and (not revised or not note.strip()): raise ValueError('实质修订须注明日期和新增实验／方法')
        out['reports'].append({'source_id': source, 'version': words(report, 'version', 100), 'first_published_at': first,
                               'revised_at': revised, 'substantive_revision': substantive, 'revision_note': note})
    if len({r['source_id'] for r in out['reports']}) != len(reports): raise ValueError('报告出处重复')
    report_ids = {r['source_id'] for r in out['reports']}
    nodes = value.get('nodes')
    if not isinstance(nodes, list) or not 2 <= len(nodes) <= 40: raise ValueError('地图须有2至40个节点')
    out['nodes'] = []; ids = set()
    for node in nodes:
        if not isinstance(node,dict): raise ValueError('节点须为对象')
        ident = words(node, 'id', 80)
        if not re.fullmatch(r'[a-z][a-z0-9-]*', ident) or ident in ids: raise ValueError('节点编号无效或重复')
        ids.add(ident)
        stage = node.get('stage')
        if isinstance(stage, bool) or not isinstance(stage, int) or not 0 <= stage <= 8: raise ValueError('节点列须为0至8的整数')
        kind = node.get('kind')
        if kind not in ('baseline', 'method', 'result'): raise ValueError('节点须区分基线、方法和结果')
        entry = {'id': ident, 'kind': kind, 'stage': stage, **{key: words(node, key) for key in ('label', 'mechanism', 'setting', 'result', 'limitation')}, 'evidence': evidence(node)}
        if not any(e['source_id'] in report_ids for e in entry['evidence']): raise ValueError('每个节点至少引用一份原始报告')
        metrics = node.get('metrics', [])
        if not isinstance(metrics, list) or len(metrics) > 8: raise ValueError('指标列表无效')
        entry['metrics'] = []
        for metric in metrics:
            if not isinstance(metric,dict): raise ValueError('指标须为对象')
            number = metric.get('value')
            if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number): raise ValueError('指标须为有限数字')
            entry['metrics'].append({'value': number, **{key: words(metric, key, 1000) for key in ('label', 'unit', 'baseline', 'conditions')}})
        out['nodes'].append(entry)
    edges = value.get('edges')
    if not isinstance(edges, list) or not 1 <= len(edges) <= 100: raise ValueError('地图须登记关系')
    out['edges'] = []; pairs = set(); graph = {ident: [] for ident in ids}
    for edge in edges:
        if not isinstance(edge,dict): raise ValueError('关系须为对象')
        a, b, relation = edge.get('from'), edge.get('to'), edge.get('relation')
        if a not in ids or b not in ids or a == b or relation not in RELATIONS or (a, b, relation) in pairs: raise ValueError('关系端点、类型或重复项错误')
        pairs.add((a, b, relation))
        entry = {'from': a, 'to': b, 'relation': relation, 'label': words(edge, 'label', 300), 'evidence': evidence(edge)}
        if not any(e['source_id'] in report_ids for e in entry['evidence']): raise ValueError('关系须有原始报告依据')
        out['edges'].append(entry)
        if relation == 'inheritance': graph[a].append(b)
    visiting, visited = set(), set()
    def visit(ident):
        if ident in visiting: raise ValueError('方法继承关系不能形成循环')
        if ident in visited: return
        visiting.add(ident)
        for target in graph[ident]: visit(target)
        visiting.remove(ident); visited.add(ident)
    for ident in ids: visit(ident)
    connected = {e[k] for e in out['edges'] for k in ('from', 'to')}
    if connected != ids: raise ValueError('每个节点须有明确关系，不能留下孤立节点')
    return out


def project(item):
    graph = metadata(item)
    if not graph: return None
    sources = [{k: s[k] for k in ('id', 'title', 'url', 'coverage')} for s in item['sources']]
    publication = item.get('publication') or {}
    obj = {**graph, 'id': item['id'], 'title': item['title'], 'summary': item['summary'], 'sources': sources,
           'related': [{k: r[k] for k in ('id', 'name', 'url')} for r in item.get('related', [])],
           'publication': {key: publication.get(key) for key in ('first_published_at', 'updated_at')},
           'path': '/maps/' + graph['slug'], 'evidence_scope': '作者技术报告与FieldToFit解读；未声称独立复现'}
    obj['revision'] = digest(obj)
    fresh = max(r['revised_at'] if r['substantive_revision'] else r['first_published_at'] for r in graph['reports'])
    obj['report_activity_at'] = fresh
    from backend.knowledge.content_workspace import today
    obj['archived'] = (date.fromisoformat(today()) - date.fromisoformat(fresh)).days >= 30
    return obj


def maps(slug='', q='', revision='', archive='all'):
    from backend.knowledge.platform_news import news
    from backend.knowledge.platform import text
    slug = text(slug, 'slug', 80, False); q = text(q, 'q', 200, False); revision = text(revision, 'revision', 128, False)
    if archive not in ('all', 'recent', 'historical'): raise PlatformError('Invalid archive filter', 'invalid_request', 400)
    items = [project(item) for item in news()['items'] if item.get('technical_map')]
    items.sort(key=lambda x: (x['report_activity_at'], x['publication']['updated_at'] or '', x['slug']), reverse=True)
    items = [x for x in items if (not slug or x['slug'] == slug) and (not q or q.casefold() in (x['question']+' '+x['focus']).casefold()) and (archive == 'all' or x['archived'] == (archive == 'historical'))]
    if slug and not items: raise PlatformError('地图未公开或已撤回', 'not_found', 404)
    rev = items[0]['revision'] if slug else digest([x['revision'] for x in items])
    if revision and revision != rev: raise PlatformError('地图已修订，请重新读取', 'map_revision_changed', 409)
    return {'schema_version': 'fieldtofit.technical-maps.v1', 'items': items, 'total': len(items), 'revision': rev,
            'scope': '同一个技术问题的已审路线；报告日期与地图修订日期分开；不包含私密检查或审核理由'}


def history(slug):
    current = maps(slug=slug)['items'][0]
    with get_db() as db:
        rows = db.execute("SELECT seq,action,snapshot,created_at FROM fieldtofit_content_history WHERE kind='news' AND item_id=? AND action IN ('import','publish') AND seq>COALESCE((SELECT MAX(seq) FROM fieldtofit_content_history WHERE kind='news' AND item_id=? AND action='withdraw'),0) ORDER BY seq DESC", (current['id'], current['id'])).fetchall()
    entries = []
    for row in rows:
        item = json.loads(row['snapshot'])
        if item.get('state') != 'published' or not item.get('technical_map'): continue
        obj = project(item)
        if obj['slug'] != slug: continue
        # Hash public content only; daily checks and private reasons cannot create revisions.
        if entries and entries[-1]['object']['revision'] == obj['revision']: continue
        entries.append({'revision': row['seq'], 'recorded_at': row['created_at'], 'date_basis': 'migration_baseline' if row['action'] == 'import' else 'FieldToFit_publication',
                        'change_summary': obj['change_summary'], 'object': obj})
    return {'slug': slug, 'items': entries, 'total': len(entries), 'scope': '已记录公开修订；导入基线时间不代表首次发表；私密理由不公开'}


def compare(slug, from_revision=None, to_revision=None):
    from backend.knowledge.platform import integer
    entries = history(slug)['items']
    if len(entries) < 2: raise PlatformError('尚无两次公开修订可对照', 'history_unavailable', 409)
    before = integer(from_revision, 'from_revision', 1) if from_revision is not None else entries[1]['revision']
    after = integer(to_revision, 'to_revision', 1) if to_revision is not None else entries[0]['revision']
    old = next((x for x in entries if x['revision'] == before), None); new = next((x for x in entries if x['revision'] == after), None)
    if not old or not new or before >= after: raise PlatformError('请选择同一地图的前后公开修订', 'revision_unavailable', 409)
    return {'slug': slug, 'from': before, 'to': after, 'fields': [{'field': k, 'before': old['object'].get(k), 'after': new['object'].get(k)} for k in (*FIELDS, 'sources', 'related') if old['object'].get(k) != new['object'].get(k)]}
