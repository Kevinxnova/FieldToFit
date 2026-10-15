"""One read-only homepage window; selection timestamps are owned by publication."""
from datetime import datetime

LIMIT = 4


def _moment(value):
    try:
        value = datetime.fromisoformat(value)
        return value.timestamp() if value.tzinfo else None
    except (ValueError, TypeError):
        return None


def selected_at(item):
    pub = item.get('publication') or {}
    value = pub.get('report_selected_at') or pub.get('first_published_at')
    return value if _moment(value) is not None else None


def key(item):
    value = _moment(selected_at(item))
    graph = item.get('technical_map') or item
    return (value is not None, value or 0, graph.get('slug', ''))


def ordered(items):
    return sorted((i for i in items if i.get('technical_map') and i.get('state', 'published') == 'published'), key=key, reverse=True)


def selection(items):
    return {'limit': LIMIT, 'ids': [i['id'] for i in ordered(items)[:LIMIT]],
            'basis': 'site_publication_or_reviewed_substantive_revision'}


def substantive_update(previous, current):
    """Only new report evidence qualifies, never copy, links or check timestamps."""
    before = (previous or {}).get('technical_map')
    after = current.get('technical_map')
    if not after:
        return False
    if not before:
        return True
    old = {r['source_id']: r for r in before['reports']}
    old_urls = {s['url']: old[s['id']] for s in previous.get('sources', []) if s['id'] in old}
    new_urls = {s['id']: s['url'] for s in current.get('sources', [])}
    for report in after['reports']:
        prior = old.get(report['source_id']) or old_urls.get(new_urls.get(report['source_id']))
        if prior is None:
            return True
        # A persistent substantive flag or a renamed version is not a new event.
        if report.get('substantive_revision') and report.get('revised_at') and report['revised_at'] != prior.get('revised_at'):
            if not prior.get('substantive_revision') or report['version'] != prior['version']:
                return True
    return False


def publication_date(previous, current, now):
    if substantive_update(previous, current):
        return now
    return selected_at(previous or {})


def rotation(before, after):
    def brief(item):
        graph = item['technical_map']
        return {'id': item['id'], 'title': graph['question'], 'url': '/maps/' + graph['slug'], 'selected_at': selected_at(item)}
    old = [brief(i) for i in ordered(before)[:LIMIT]]
    new = [brief(i) for i in ordered(after)[:LIMIT]]
    old_ids = {i['id'] for i in old}; new_ids = {i['id'] for i in new}
    visible = {i['id'] for i in ordered(after)}
    return {'status': 'published', 'limit': LIMIT, 'before': old, 'after': new,
            'changed': [i['id'] for i in old] != [i['id'] for i in new],
            'entered': [i for i in new if i['id'] not in old_ids],
            'left': [i for i in old if i['id'] not in new_ids],
            'index_only': [i for i in old if i['id'] not in new_ids and i['id'] in visible]}
