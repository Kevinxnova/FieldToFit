"""Bounded, revision-checked public reading projections; never a publication store."""
import copy
import hashlib
import json
import time
from collections import OrderedDict
from pathlib import Path
from threading import RLock

from flask import g, has_request_context
from backend import __version__
from backend.db import get_db, TursoConnection
from backend.knowledge.platform import PlatformError

_CACHE = OrderedDict()
_LOCK = RLock()
MAX_BYTES = 24 * 1024 * 1024
TABLES = ('fieldtofit_steward_aliases', 'fieldtofit_steward_links', 'fieldtofit_steward_checks')


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def timed(name, started):
    if has_request_context():
        if not hasattr(g, 'reading_timings'): g.reading_timings = []
        g.reading_timings.append((name, (time.perf_counter() - started) * 1000))


def batch(db, statements):
    if isinstance(db, TursoConnection):
        cursors = db.atomic_statements(statements, read_only=True)
    else:
        db.execute('BEGIN')
        cursors = [db.execute(sql, args) for sql, args in statements]
    return [[dict(row) for row in cursor.fetchall()] for cursor in cursors]


def dependencies():
    """Always read current shared state. Failure never authorizes a stale cache hit."""
    started = time.perf_counter()
    with get_db() as db:
        names = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    queries = [('sets', 'SELECT kind,revision FROM fieldtofit_content_sets ORDER BY kind')]
    queries += [(t, 'SELECT * FROM '+t+' ORDER BY '+{'fieldtofit_steward_aliases':'source_id','fieldtofit_steward_checks':'object_id,material_id','fieldtofit_steward_links':'id'}[t]) for t in TABLES]
    queries += [('library', "SELECT p.seq FROM knowledge_publications p JOIN knowledge_selections s ON s.record_id=p.record_id AND s.state='published' AND s.revision=p.seq ORDER BY p.seq")]
    queries = [(key, sql) for key, sql in queries if ('fieldtofit_content_sets' if key == 'sets' else 'knowledge_publications' if key == 'library' else key) in names]
    from backend.daily_briefing.home import MANIFEST_SQL, clock
    if {'fieldtofit_daily_issues', 'fieldtofit_daily_publications'} <= names:
        queries.append(('daily', MANIFEST_SQL))
    with get_db() as db:
        results = batch(db, [(sql, ()) for _, sql in queries])
    dep = {key: rows for (key, _), rows in zip(queries, results)}
    dep['daily_clock'] = clock()
    # Source deployments and tests may use released files before a content migration.
    files = [(str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in sorted(Path(__file__).parent.joinpath('content').rglob('*.json'))]
    from backend import config, db as database
    identity = [str(config.DB_PATH), database.TURSO_URL, digest(database.TURSO_TOKEN)]
    revision = digest([__version__, identity, files, dep])
    timed('reading_revision', started)
    return revision, dep


def prepare(dep):
    started = time.perf_counter()
    raw = {}
    if 'sets' in dep:
        with get_db() as db:
            for row in db.execute('SELECT kind,published_json FROM fieldtofit_content_sets').fetchall():
                raw[row['kind']] = json.loads(row['published_json'])
    from backend.knowledge.content_workspace import CONTENT
    for kind in ('news', 'watch'):
        if kind not in raw: raw[kind] = json.loads((CONTENT/(kind+'.json')).read_text())
    raw.setdefault('charts', None)
    g.reading_raw = raw
    g.reading_tables = {t: dep.get(t, []) for t in TABLES}
    from backend.knowledge import locale
    if locale.is_english() and dep.get('library'):
        with get_db() as db:
            g.reading_library = [dict(r) for r in db.execute("SELECT p.snapshot FROM knowledge_publications p JOIN knowledge_selections s ON s.record_id=p.record_id AND s.state='published' AND s.revision=p.seq").fetchall()]
    else: g.reading_library = []
    timed('reading_database', started)
    return raw


def slim_news(collection):
    out = copy.deepcopy(collection)
    for item in out['items']:
        item.pop('materials', None)
        item.pop('materials_revision', None)
        item.pop('maintenance', None)
        if not item.get('codex_28_days'):
            item['interpretation'] = item['interpretation'][:1] if item.get('highlight') else []
            item['reading_summary'] = True
        graph = item.get('technical_map')
        if graph:
            # The first reviewed illustration is all the card needs.
            figures = [b for f in (graph.get('reading') or {}).get('findings', []) for b in f['blocks'] if b['kind']=='figure']
            item['technical_map'] = {k: graph[k] for k in ('slug','focus','question','takeaway','caution','change_summary','reports')}
            item['technical_map']['reading'] = {'findings': [{'blocks':figures[:1]}]}
    out['reading_summary'] = True
    return out


def slim_watch(collection):
    out = copy.deepcopy(collection)
    for item in out['items']:
        item['materials_count'] = len(item.get('materials', []))
        for key in ('materials', 'materials_revision', 'blocks', 'milestones', 'events'):
            item.pop(key, None)
        item['interpretation'] = item['interpretation'][:2]
        item['reading_summary'] = True
    out['reading_summary'] = True
    return out


def safety(raw, dep):
    # Changes in readable material availability and reviewed translation validity
    # invalidate old bodies even if a reader has deferred ordinary additions.
    from backend.knowledge.locale import source_hash, baseline
    values = []
    for kind in ('news', 'watch'):
        for item in raw[kind]['items']:
            if item['state'] != 'published': continue
            en = item.get('translations', {}).get('en', {})
            fingerprint = source_hash(kind, item)
            translated = (en.get('state') == 'reviewed' and en.get('source_hash') == fingerprint) or (not en and fingerprint in baseline().get(kind+':'+item['id'], []))
            values.append([item['id'], translated, [(m['id'], m['url'], m['coverage']) for m in item.get('reading_materials', [])], [key for key in ('technical_map','hot_card') if item.get(key)]])
    return {'items': values, 'aliases': dep.get('fieldtofit_steward_aliases', []),
            'daily': [row['day'] for row in dep.get('daily', [])]}


def build(revision, dep):
    raw = prepare(dep)
    started = time.perf_counter()
    from backend.knowledge.platform_news import news
    from backend.knowledge.platform_watch import watch
    from backend.knowledge.model_landscape import snapshot
    from backend.knowledge import locale
    n = news()
    g.reading_news = n
    w = watch()
    fields = locale.public_fields() if locale.is_english() else None
    project = lambda value: locale.project(value, fields) if fields is not None else value
    # Match the full-profile endpoint's search scope, including reviewed English.
    search = {i['id']: json.dumps(locale.searchable({k:v for k,v in i.items() if k!='maintenance'}), ensure_ascii=False).casefold() for i in w['items']}
    n, w, chart = project(n), project(w), project(snapshot())
    from backend.daily_briefing.home import preview
    daily = preview(dep.get('daily', []), dep['daily_clock'], 'en' if locale.is_english() else 'zh')
    result = {'revision': revision, 'safety': safety(raw, dep), 'news': slim_news(n), 'watch': slim_watch(w), 'charts': chart, 'daily': daily}
    timed('reading_projection', started)
    return result, search


def overview(q='', type='', after=''):
    from backend.knowledge import locale
    from backend.knowledge.platform import text
    q, type = text(q, 'q', 200, False), text(type, 'type', 200, False)
    if type not in ('', 'model', 'agent', 'tool', 'skill', 'harness'):
        raise PlatformError('Unknown watch type', 'invalid_type', 400)
    for attempt in range(2):
        try: revision, dep = dependencies()
        except Exception as exc: raise PlatformError('Current publication state is unavailable', 'reading_unavailable', 503) from exc
        if after == revision: return {'revision': revision, 'unchanged': True}
        key = (revision, locale.is_english())
        with _LOCK:
            cached = _CACHE.get(key)
            if cached: _CACHE.move_to_end(key)
        if cached:
            result, search, _ = cached
        else:
            result, search = build(revision, dep)
            try: current, _ = dependencies()
            except Exception as exc: raise PlatformError('Current publication state is unavailable', 'reading_unavailable', 503) from exc
            if current != revision:
                # Discard all request-local projections before a consistent retry.
                for name in ('reading_raw','reading_tables','reading_news','english_published_fields','public_read_memo','reading_library'):
                    g.pop(name, None)
                continue
            size = len(json.dumps([result, search], ensure_ascii=False).encode())
            if size <= MAX_BYTES:
                with _LOCK:
                    _CACHE[key] = (result, search, size)
                    while len(_CACHE)>4 or sum(v[2] for v in _CACHE.values())>MAX_BYTES: _CACHE.popitem(last=False)
        if after == revision:
            return {'revision': revision, 'unchanged': True}
        out = copy.deepcopy(result)
        all_items = out['watch']['items']
        out['projects'] = {**out['watch'], 'origin':'developer_submission', 'items':[i for i in all_items if i.get('origin')=='developer_submission']}
        out['projects']['total'] = len(out['projects']['items'])
        out['watch']['items'] = [i for i in all_items if (not type or i['type']==type) and (not q or q.casefold() in search[i['id']])]
        out['watch']['total'] = len(out['watch']['items'])
        out['watch']['groups'] = [{**group,'count':sum(i['type']==group['id'] for i in out['watch']['items'])} for group in out['watch']['groups']]
        return out
    raise PlatformError('Published content changed during reading; retry', 'reading_changed', 503)
