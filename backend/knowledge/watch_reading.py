"""Public, source-backed reading projection of existing reviewed content."""
from datetime import date, timedelta
import re

from backend.knowledge.watch_reading_data import CATEGORIES, MILESTONES, PROFILES, SNAPSHOTS, UPDATES, PRODUCT_NAMES


def zh(value):
    return value[0] if isinstance(value, tuple) else value


def event_date(item):
    return item.get('event_date') or item.get('source_published_at') or ''


def recent_event(events):
    """Editorial emphasis within 30 days of the newest reviewed event, then date.

    highlight is editorial selection, NOT measured popularity. Older records
    remain available when there is no newly reviewed event for this subject.
    """
    dated = [e for e in events if event_date(e)]
    if not dated:
        return events[0] if events else None
    newest = max(date.fromisoformat(event_date(e)) for e in dated)
    recent = [e for e in dated if date.fromisoformat(event_date(e)) >= newest - timedelta(days=30)]
    return max(recent, key=lambda e: (bool(e.get('highlight')), event_date(e), e['id']))


def direct_match(item, event):
    """Require an existing reviewed relationship AND an explicit subject name.

    Broad further-reading links alone must not turn a competitor's launch into
    this project's event. Explicit reviewed selections cover historical aliases.
    """
    if not any(ref['id'] == item['id'] for ref in event['related']):
        return False
    names = [item['name'], *item.get('aliases', [])]
    if item['id'] == 'CW-M01': names = ['GPT', 'ChatGPT']
    haystack = event['name'] + ' ' + event['title']
    return any(re.search(r'(?<![\w])' + re.escape(name) + r'(?![\w])', haystack, re.I) for name in names if isinstance(name, str) and name)


def fallback_event(item):
    update = UPDATES.get(item['id'])
    if update:
        day, kind, title, url = update
    else:
        day, kind = item['checked_at'], 'review'
        title = SNAPSHOTS.get(item['id'], item['interpretation'][0]['title'])
        url = item['sources'][0]['url']
    return {'date': day, 'date_kind': kind, 'title': zh(title), 'url': url,
            'profile_id': item['id'], 'basis': 'reviewed_profile'}


def enrich(items, events):
    """No draft loading, writes, network fetches or automatic publication."""
    by_id = {e['id']: e for e in events}
    for item in items:
        ident = item['id']
        developer, category, purpose, selected_ids = PROFILES.get(ident, ('-', '', '-', []))
        direct = [e for e in events if e['id'] in selected_ids or direct_match(item, e)]
        latest = recent_event(direct)
        recent = fallback_event(item)
        # A specific dossier update can be newer than an independent article.
        # Review snapshots are not upstream events and never displace articles.
        if latest and (recent['date_kind'] == 'review' or not event_date(latest) or event_date(latest) >= recent['date']):
            recent = {'date': event_date(latest) or None,
                      'date_kind': 'release' if latest.get('event_date') else 'source',
                      'title': latest['title'], 'news_id': latest['id'],
                      'basis': 'editorial_highlight' if latest.get('highlight') else 'latest_reviewed'}
        item['overview'] = {'developer': developer, 'category': zh(CATEGORIES.get(category, '-')),
                            'purpose': zh(purpose), 'recent_event': recent}
        if ident == 'CW-M01' and item['name'] == 'GPT':
            item['name'] = 'ChatGPT'
        if ident not in MILESTONES:
            continue
        milestones = []
        for index, (news_id, model, price, condition) in enumerate(MILESTONES[ident]):
            event = by_id.get(news_id)
            if not event or not event_date(event):
                continue  # Withdrawals disappear; an unknown release date is not guessed.
            milestones.append({'id': ident + '-' + str(index), 'news_id': news_id,
                               'date': event_date(event), 'date_kind': 'release' if event.get('event_date') else 'source',
                               'kind': 'model' if model else 'product', 'name': model or zh(PRODUCT_NAMES.get(news_id, event['title'])),
                               'price': price, 'price_condition': zh(condition),
                               'summary': event['summary'],
                               'points': event['interpretation'][1:3] if news_id == 'D-49' else event['interpretation'][:2],
                               'sources': event['sources']})
        item['milestones'] = sorted(milestones, key=lambda e: (e['date'], e['id']))
        required_ids = {m['news_id'] for m in milestones}
        ordered = sorted([e for e in events if e['id'] in required_ids or e in direct or
                                 any(ref['id'] == ident for ref in e['related'])],
                                key=lambda e: (event_date(e), e['id']), reverse=True)
        # The feed contains editorial reading fields, not source-post bodies or
        # nested material manifests. Full evidence remains in each original D-.
        fields = ('id', 'name', 'organization', 'category', 'title', 'summary',
                  'source_published_at', 'event_date', 'checked_at', 'note',
                  'editor', 'highlight', 'interpretation', 'sources', 'related', 'publication')
        item['events'] = [{k: e[k] for k in fields if k in e} for e in ordered]
    # Stable pinning does not reinsert objects excluded by filtering/withdrawal.
    return sorted(items, key=lambda i: {'CW-M01': 0, 'CW-M02': 1}.get(i['id'], 2))
