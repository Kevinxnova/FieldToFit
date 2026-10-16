"""Homepage previews derived only from the current reviewed reading snapshot."""
import base64
import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


VIEWS = ('full', 'home', 'news', 'watch', 'models', 'hot-cards', 'codex')


def event_date(item):
    return (item.get('event_date') or item.get('source_published_at') or '')[:10]


def chart_preview(source):
    """Original plot coordinates plus a legacy thumbnail for older preview clients."""
    points = source['points']
    image = None
    if points:
        lo = min(p.get('score_low', p['score']) for p in points)
        hi = max(p.get('score_high', p['score']) for p in points)
        pad = max((hi-lo)*.12, 1)
        lo, hi = lo-pad, hi+pad
        xmin = math.floor(math.log10(min(p['price'] for p in points)))
        xmax = max(xmin+1, math.ceil(math.log10(max(p['price'] for p in points))))
        x = lambda v: 48+(math.log10(v)-xmin)/(xmax-xmin)*604
        y = lambda v: 170-(v-lo)/(hi-lo)*150
        marks = []
        for fraction in (0, .5, 1):
            yy = 170-fraction*150
            marks.append(f'<path d="M48 {yy}H652" stroke="#a3b0a4" opacity=".35"/><text x="40" y="{yy+4}" text-anchor="end">{lo+fraction*(hi-lo):.1f}</text>')
            value = 10**(xmin+fraction*(xmax-xmin))
            marks.append(f'<text x="{x(value):.2f}" y="194" text-anchor="middle">${value:g}</text>')
        for p in points:
            if 'score_low' in p and 'score_high' in p:
                marks.append(f'<path d="M{x(p["price"]):.2f} {y(p["score_low"]):.2f}V{y(p["score_high"]):.2f}" stroke="#668e73" opacity=".6"/>')
            marks.append(f'<circle cx="{x(p["price"]):.2f}" cy="{y(p["score"]):.2f}" r="3" fill="#668e73"/>')
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 210"><g font-family="sans-serif" font-size="13" fill="#718476">'+''.join(marks)+'</g></svg>'
        image = 'data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode()
    return {k: source[k] for k in ('id','name','source_url','source_updated_at','checked_at','score_label','price_label','price_label_en','coverage')} | {'image': image, 'plot_points': [{k: p[k] for k in ('id', 'name', 'organization', 'score', 'price', 'score_low', 'score_high', 'estimated') if k in p} for p in points]}


def project(data, view):
    if view == 'full':
        return data
    news, watch = data['news'], data['watch']
    items = news['items']
    if view == 'home':
        highlights = [i['id'] for i in items if i.get('highlight')][:3]
        hot = sorted((i for i in items if i.get('hot_card', {}).get('featured_rank', 0)>0), key=lambda i: i['hot_card']['featured_rank'])[:3]
        reports = news.get('report_selection', {}).get('ids', [])[:4]
        logs = sorted((i for i in items if i.get('codex_28_days')), key=lambda i: (i['codex_28_days']['date'], i.get('publication', {}).get('updated_at') or '', int(i['id'].split('-')[-1])), reverse=True)[:3]
        # A review/check timestamp is not an event. Never fill empty slots with old profiles.
        today = datetime.now(ZoneInfo('Asia/Shanghai')).date()
        start = (today-timedelta(days=29)).isoformat()
        by_id = {i['id']: i for i in watch['items']}
        recent = {}
        for item in sorted(items, key=lambda i: (event_date(i), int(i['id'].split('-')[-1])), reverse=True):
            if not start <= event_date(item) <= today.isoformat():
                continue
            for relation in item.get('related', []):
                if relation['id'] in by_id and relation['id'] not in recent:
                    recent[relation['id']] = {'watch_id': relation['id'], 'news_id': item['id'], 'date': event_date(item)}
        events = list(recent.values())[:3]
        ids = set(highlights+reports+[i['id'] for i in hot+logs]+[e['news_id'] for e in events])
        news['items'] = [i for i in items if i['id'] in ids]
        data['home_preview'] = {'highlights':highlights, 'hot_cards':[i['id'] for i in hot], 'reports':reports, 'codex':[i['id'] for i in logs], 'watch_events':events}
        data['chart_previews'] = [chart_preview(s) for s in data['charts']['sources']]
        watch['items'] = [{k:i[k] for k in ('id','name','type','introduction','checked_at')} for e in events for i in [by_id[e['watch_id']]]]
        # Only metadata used by the preview components crosses this boundary.
        keep = ('id','name','organization','title','summary','source_published_at','event_date','checked_at','highlight','media','publication','hot_card','technical_map','codex_28_days')
        for index, item in enumerate(news['items']):
            small = {k:item[k] for k in keep if k in item}
            small.update(interpretation=[], related=[], sources=[])
            if item.get('hot_card'):
                evidence_ids = {e['source_id'] for e in item['hot_card']['evidence']}
                small['sources'] = [s for s in item['sources'] if s['id'] in evidence_ids]
            if item.get('codex_28_days'):
                small['codex_28_days'] = {k:item['codex_28_days'][k] for k in ('date','group','type','official_day','overview_zh','overview_en') if k in item['codex_28_days']}
            news['items'][index] = small
    elif view == 'codex':
        news['items'] = [i for i in items if i.get('codex_28_days')]
    elif view == 'hot-cards':
        news['items'] = [i for i in items if i.get('hot_card')]
        news['total'] = len(news['items'])
    elif view == 'watch':
        # Preserve the complete column's related-news/report guide without shipping
        # the unrelated news archive or its detail bodies.
        ids = {item['id'] for item in watch['items']}
        related = [i for i in items if any(r['id'] in ids for r in i.get('related', []))]
        today = datetime.now(ZoneInfo('Asia/Shanghai')).date()
        recent = sorted((i for i in related if (today-timedelta(days=6)).isoformat() <= event_date(i) <= today.isoformat()), key=event_date, reverse=True)[:2]
        selected = {i['id'] for i in recent} | {i['id'] for i in related if i.get('technical_map')}
        news['items'] = [i for i in related if i['id'] in selected]
    elif view == 'models':
        news['items'] = []
    if view != 'codex':
        news.pop('codex_progress', None)
        news.pop('referenced_items', None)
        for item in news['items']:
            if view != 'home':
                item.pop('codex_28_days', None)
                item['interpretation'] = []
                item['reading_summary'] = True
    if view not in ('home', 'watch'):
        watch['items'] = []
    if view != 'models':
        data['charts'] = {**data['charts'], 'sources': []}
    data['projects']['items'] = []
    data['view'] = view
    return data
