"""Public search pages read the same reviewed publications as HTTP and MCP.

No crawler-specific rendering and no retained page cache: a withdrawal takes
effect on the next request, including sitemap and error responses.
"""
import html
import json
import os
import re
from pathlib import Path
from xml.etree import ElementTree as ET

from flask import Blueprint, Response, redirect, render_template, request
from markupsafe import Markup

from backend.knowledge.platform import PlatformError
from backend.knowledge.platform_news import news
from backend.knowledge.platform_watch import watch

ROOT = Path(__file__).parent
ORIGIN = 'https://fieldtofit.top'
PAGES = json.loads((ROOT / 'pages.json').read_text())
bp = Blueprint('search', __name__, template_folder='templates')
DETAIL = re.compile(r'^/(news/D-\d{2,}|watch/CW-[MATSH]\d{2,})$')
LEGACY = {'/information', '/apps', '/legacy/information', '/legacy/apps', '/tasks',
          '/briefs', '/collection', '/compare', '/cases', '/account', '/feedback',
          '/admin', '/admin/curation', '/discover', '/daily-news'}


def detail_url(ident):
    return ('/news/' if ident.startswith('D-') else '/watch/') + ident


def public_link(value):
    match = re.fullmatch(r'/for-you#(?:news|watch)-((?:d-\d+|cw-[matsh]\d+))', value, re.I)
    return detail_url(match[1].upper()) if match else value


def inline(value):
    """Same limited reviewed Markdown as WatchText; escape before adding tags."""
    pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*|`([^`]+)`')
    parts, end = [], 0
    for match in pattern.finditer(value):
        parts.append(html.escape(value[end:match.start()]))
        label, url, bold, code = match.groups()
        if url:
            url = public_link(url)
            parts.append(f'<a href="{html.escape(url, quote=True)}">{html.escape(label)}</a>'
                         if url.startswith(('https://', '/watch/', '/news/')) else html.escape(label))
        elif bold:
            parts.append('<strong>' + html.escape(bold) + '</strong>')
        else:
            parts.append('<code>' + html.escape(code) + '</code>')
        end = match.end()
    parts.append(html.escape(value[end:]))
    return Markup(''.join(parts))


bp.add_app_template_filter(inline, 'search_inline')
bp.add_app_template_filter(public_link, 'search_link')


def preview():
    return os.getenv('VERCEL_ENV') == 'preview' or request.host != 'fieldtofit.top'


@bp.after_app_request
def search_headers(response):
    if request.path in ('/api/v1/platform/news', '/api/v1/platform/watch', '/', '/connect') or request.path.rstrip('/') in PAGES or request.path.startswith(('/news/', '/watch/')):
        response.headers['Cache-Control'] = 'no-store'
    if preview() or request.path.startswith('/api/') or request.path in LEGACY or request.path.startswith('/records/') or response.status_code >= 400:
        response.headers['X-Robots-Tag'] = 'noindex, nofollow' if preview() else 'noindex'
    return response


@bp.get('/robots.txt')
def robots():
    body = ('User-agent: *\nDisallow: /\n' if preview() else
            'User-agent: *\nAllow: /\nSitemap: ' + ORIGIN + '/sitemap.xml\n')
    return Response(body, content_type='text/plain; charset=utf-8', headers={'Cache-Control': 'no-store'})


def published_dates_query():
    # Never use mutable draft timestamps, migration dates or reachability checks.
    # Compare only public fields; unchanged publications don't manufacture freshness.
    fields = ('state','name','organization','title','summary','introduction','type',
              'source_published_at','event_date','checked_at','interpretation','blocks',
              'sources','related','note','editor','highlight','attention','origin',
              'submission','reading_materials','aliases')
    projection = 'json_array(' + ','.join("json_extract(snapshot,'$."+key+"')" for key in fields) + ')'
    return f"""WITH revisions AS (
        SELECT kind,item_id,action,created_at,{projection} body,
          LAG({projection}) OVER (PARTITION BY kind,item_id ORDER BY seq) previous
        FROM fieldtofit_content_history
        WHERE kind IN ('news','watch') AND item_id!='*'
          AND action IN ('import','publish','withdraw','merge_source','restore_draft'))
        SELECT kind,item_id,MAX(created_at) changed FROM revisions
        WHERE action='publish' AND (previous IS NULL OR body!=previous)
        GROUP BY kind,item_id"""


def sitemap_entries():
    """One fresh public snapshot; omit unrelated material-health/relationship reads."""
    from backend.db import get_db, TursoConnection
    from backend.knowledge import content_workspace as workspace
    from backend.knowledge.stewardship import resolve

    queries = [("SELECT kind,published_json FROM fieldtofit_content_sets WHERE kind IN ('news','watch')", ()),
               ('SELECT source_id,target_id FROM fieldtofit_steward_aliases', ()),
               (published_dates_query(), ())]
    with get_db() as db:
        if isinstance(db, TursoConnection):
            rows = [cursor.fetchall() for cursor in db.atomic_statements(queries, read_only=True)]
        else:
            db.execute('BEGIN')
            rows = [db.execute(sql, params).fetchall() for sql, params in queries]
        raw = {row['kind']: json.loads(row['published_json']) for row in rows[0]}
        dates = {(row['kind'], row['item_id']): row['changed'] for row in rows[2]}
        entries = []
        for kind in ('news', 'watch'):
            data = raw.get(kind)
            if data is None:
                data = json.loads((workspace.CONTENT / (kind + '.json')).read_text())
            # Reuse the public validator/projection, without fetching maintenance
            # decorations. Reviewed aliases come from the same database snapshot.
            for item in workspace.render(kind, data)['items']:
                if resolve(item['id'], db, rows[1]) == item['id']:
                    entries.append((detail_url(item['id']), dates.get((kind, item['id']))))
        return entries


@bp.get('/sitemap.xml')
def sitemap():
    try:
        entries = sitemap_entries()
        namespace = 'http://www.sitemaps.org/schemas/sitemap/0.9'
        ET.register_namespace('', namespace)
        root = ET.Element('{'+namespace+'}urlset')
        def add(path, changed=None):
            node = ET.SubElement(root, 'url')
            ET.SubElement(node, 'loc').text = ORIGIN + path
            if changed:
                ET.SubElement(node, 'lastmod').text = changed
        for path in PAGES:
            add(path)
        for path, changed in entries:
            add(path, changed)
        return Response(ET.tostring(root, encoding='utf-8', xml_declaration=True),
                        content_type='application/xml; charset=utf-8', headers={'Cache-Control': 'no-store'})
    except Exception:
        return Response('Sitemap temporarily unavailable', status=503,
                        content_type='text/plain; charset=utf-8', headers={'Cache-Control': 'no-store'})


def shell_path(dist):
    return dist / 'index.html' if (dist / 'index.html').exists() else ROOT / 'client.html'


def document(dist, title, description, path, body='', status=200, index=True):
    source = shell_path(dist)
    if not source.exists():
        return Response('Frontend build unavailable', status=503, headers={'Cache-Control': 'no-store'})
    content = source.read_text()
    # Replace, never append conflicting canonical or Open Graph tags.
    content = re.sub(r'<title>.*?</title>', '', content, flags=re.S)
    content = re.sub(r'<meta\s+(?:name="(?:description|robots)"|property="og:(?:title|description|url)")[^>]*>', '', content)
    content = re.sub(r'<link\s+rel="canonical"[^>]*>', '', content)
    escape = lambda s: html.escape(s, quote=True)
    url = ORIGIN + path
    meta = (f'<title>{escape(title)}</title><meta name="description" content="{escape(description)}">'
            f'<meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(description)}">'
            f'<meta property="og:url" content="{escape(url)}"><link rel="canonical" href="{escape(url)}">'
            f'<meta name="robots" content="{"index, follow" if index and not preview() else "noindex"}">')
    content = content.replace('</head>', meta + '</head>')
    content = content.replace('<div id="root"></div>', '<div id="root">' + body + '</div>')
    if status >= 400:
        # Do not turn an actual 404/503 into a cached client success or leak a stale body.
        content = re.sub(r'<script\b[^>]*>.*?</script>', '', content, flags=re.S)
    return Response(content, status=status, content_type='text/html; charset=utf-8',
                    headers={'Cache-Control': 'no-store', **({'X-Robots-Tag': 'noindex'} if not index else {})})


def page(path, dist):
    if path == '/':
        return redirect('/for-you' + ('?' + request.query_string.decode('utf-8', errors='replace') if request.query_string else ''), 308)
    if path == '/connect':
        return redirect('/for-your-ai', 308)
    if path.endswith('/') and (path.rstrip('/') in PAGES or DETAIL.fullmatch(path.rstrip('/'))):
        return redirect(path.rstrip('/'), 308)
    if path not in PAGES and not DETAIL.fullmatch(path):
        return None
    try:
        item = None
        collections = {}
        catalog = None
        revision = ''
        if path == '/for-you' and request.args.get('object'):
            return document(dist, PAGES[path]['title'][0], PAGES[path]['description'][0], path, index=False)
        if path in PAGES:
            info = PAGES[path]
            title, description, heading = info['title'][0], info['description'][0], info['heading'][0]
            if path in ('/for-you', '/for-your-ai'):
                collections = {'news': news(), 'watch': watch(q=request.args.get('q', '') if path == '/for-you' else '', type=request.args.get('type', '') if path == '/for-you' else '')}
            elif path == '/community':
                collections = {'watch': watch(origin='developer_submission')}
            elif path == '/sources':
                from backend.knowledge.source_catalog import registry
                catalog = registry()
        else:
            kind, ident = path.strip('/').split('/')
            collection = (news if kind == 'news' else watch)(id=ident)
            item = collection['items'][0]
            if item['id'] != ident:
                return redirect(detail_url(item['id']), 308)
            revision = collection['revision']
            title = item.get('title', item['name']) + ' · FieldToFit'
            heading = item.get('title', item['name'])
            description = item.get('summary', item.get('introduction', ''))
        body = render_template('search.html', pages=PAGES, path=path, heading=heading,
                               description=description, item=item, collections=collections,
                               catalog=catalog, revision=revision)
        return document(dist, title, description, path, body)
    except PlatformError as exc:
        status = exc.status if exc.status in (400, 404) else 503
    except Exception:
        status = 503
    heading = '资料不存在或已下架' if status == 404 else '资料暂时无法读取'
    body = render_template('search.html', pages=PAGES, path=path, heading=heading,
                           description='', item=None, collections={}, catalog=None, revision='')
    return document(dist, 'FieldToFit · '+heading, '', path, body, status, False)
