"""Public, script-independent homepage and section documents."""
import re
from datetime import datetime, timedelta
from urllib.parse import urlencode
from zoneinfo import ZoneInfo
from flask import request, render_template
from backend.knowledge.platform import PlatformError

SECTIONS = {'news':'recent-news', 'hot-cards':'hot-information-cards', 'codex':'news-codex-28-days', 'models':'model-landscape', 'watch':'resource-dossiers'}


def news_archive(items, args, hot_cards=False):
    """Honor shared archive links even when scripts are unavailable."""
    today = datetime.now(ZoneInfo('Asia/Shanghai')).date()
    span = args.get('news_range', 'all' if hot_cards else '7')
    if span not in ('7', '30', 'all'):
        span = 'all' if hot_cards else '7'
    start = (today-timedelta(days=int(span)-1)).isoformat() if span != 'all' else ''
    updated = args.get('news_sort') == 'updated'
    kind, query = args.get('news_type', 'all'), args.get('news_q', '').lower()

    def day(item):
        if not updated:
            return (item.get('event_date') or item.get('source_published_at') or '')[:10]
        stamp = item.get('publication', {}).get('updated_at')
        return datetime.fromisoformat(stamp.replace('Z', '+00:00')).astimezone(ZoneInfo('Asia/Shanghai')).date().isoformat() if stamp else ''

    def category(item):
        if item.get('category') in ('model','agent','tool','skill','harness','research','industry','other'):
            return item['category']
        linked = next((r['id'][3] for r in item.get('related', []) if re.fullmatch(r'CW-[MATSH]\d+', r['id'])), '')
        return dict(M='model', A='agent', T='tool', S='skill', H='harness').get(linked, 'other')

    def matches(item):
        hot = item.get('hot_card', {})
        text = ' '.join(str(item.get(k) or '') for k in ('name','organization','title','summary'))+' '+hot.get('headline','')+' '+hot.get('scope','')+' '+' '.join(r['name'] for r in item.get('related', []))
        return ((not hot_cards and args.get('news_cards') != '1' or bool(hot))
                and (kind == 'all' or category(item) == kind) and query in text.lower()
                and (not start or start <= day(item) <= today.isoformat()))

    found = sorted((i for i in items if matches(i)), key=lambda i: int(i['id'].split('-')[-1]))
    found.sort(key=day, reverse=True)
    pages = max(1, (len(found)+9)//10)
    try:
        page = min(pages, max(1, int(args.get('news_page', '1'))))
    except ValueError:
        page = 1
    def link(number):
        params = args.to_dict(flat=False)
        params['news_page'] = [str(number)]
        return '?'+urlencode(params, doseq=True)+'#news-releases'
    return {'items':found[(page-1)*10:page*10], 'total':len(found), 'page':page, 'pages':pages,
            'previous':link(page-1) if page>1 else None, 'next':link(page+1) if page<pages else None}


def page(path, dist, english):
    from backend.seo import PAGES, document, calendar_month, calendar_rows
    from backend.knowledge.api import read_allowed
    from backend.knowledge.reading import overview
    info = PAGES[path]
    index = int(english)
    if not read_allowed():
        return document(dist, info['title'][index], info['description'][index], path, status=401, index=False)
    view = path.split('/')[-1] if path != '/for-you' else 'home'
    q, kind = (request.args.get('q',''), request.args.get('type','')) if view == 'watch' else ('','')
    try:
        data = overview(q=q, type=kind, view=view)
    except PlatformError as exc:
        status = exc.status if exc.status in (400,404) else 503
        return document(dist, info['title'][index], '', path, '<p>'+('Content is temporarily unavailable.' if english else '内容暂时无法读取。')+'</p>', status=status, index=False)
    topic = data['news'].get('codex_progress', {})
    month = topic.get('days', [{}])[0].get('date', '')[:7] if topic.get('days') else ''
    cells = calendar_month(*map(int, month.split('-')), topic) if month else []
    items = {i['id']:i for i in data['news'].get('referenced_items', [])+data['news']['items']}
    targets = []
    if request.args.get('codex_date'): targets.append('codex')
    if any(k.startswith('news_') for k in request.args): targets.append('news')
    if any(k in request.args for k in ('chart','company')): targets.append('models')
    if any(k in request.args for k in ('q','type')): targets.append('watch')
    from backend.llm_evolution import CATALOG as evolution_catalog, HOME_PREVIEW, NODE_BY_ID
    body = render_template('for_you.html', evolution=evolution_catalog, evolution_preview=HOME_PREVIEW, evolution_nodes=NODE_BY_ID, data=data, view=view, english=english, heading=info['heading'][index], description=info['description'][index],
                           section_anchor=SECTIONS.get(view, ''), items=items, daily_preview=data['daily'], sections=SECTIONS, pages=PAGES,
                           legacy_targets=targets, legacy_query=request.query_string.decode('utf-8',errors='replace'),
                           calendar_items=items, calendar_cells=cells, calendar_rows=calendar_rows(cells), calendar_title=month,
                           archive=news_archive(data['news']['items'], request.args, view=='hot-cards') if view in ('news','hot-cards') else None)
    boot = {'language':'en' if english else 'zh', 'q':q, 'type':kind, 'view':view, 'data':data}
    return document(dist, info['title'][index], info['description'][index], path, body, bootstrap=boot)
