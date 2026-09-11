"""Reviewed release-file news, shared by web and MCP; separate from database drafts.

Editors review this small, versioned collection through Git. Only published entries
are exposed. Sources are link-only: editorial summaries never pretend to be full text.
"""
import hashlib
import json
import re
from pathlib import Path
from datetime import date
from urllib.parse import urlsplit
from backend.knowledge.platform import PlatformError, text

CONTENT_PATH = Path(__file__).parent / 'content' / 'news.json'


def validate(data):
    if data.get('schema_version') != 'fieldtofit.news.v1' or not isinstance(data.get('items'), list):
        raise ValueError('Invalid news collection')
    for key in ('edition', 'title', 'reviewed_at'):
        text(data[key], key, 200)
    date.fromisoformat(data['reviewed_at'])
    ids = set()
    for item in data['items']:
        if not re.fullmatch(r'D-\d{2,}', item['id']) or item['id'] in ids:
            raise ValueError('Duplicate or invalid news identity')
        ids.add(item['id'])
        if item['state'] not in ('draft', 'published', 'withdrawn'):
            raise ValueError('Invalid news publication state')
        if item['state'] != 'published':
            continue
        if not isinstance(item['highlight'], bool) or not isinstance(item['note'], str) or not isinstance(item['related'], list):
            raise ValueError('Invalid public news fields')
        for source in item['sources']:
            for key in ('id', 'title', 'url', 'coverage'):
                text(source[key], key, 1600)
        for ref in item['related']:
            for key in ('id', 'name', 'url'):
                text(ref[key], key, 1600)
        for key in ('name', 'organization', 'title', 'summary', 'editor'):
            text(item[key], key, 1000)
        for key in ('checked_at', 'source_published_at', 'event_date'):
            if item.get(key):
                date.fromisoformat(item[key])
        if not item.get('checked_at') or not item.get('interpretation') or not item.get('sources'):
            raise ValueError('Published news needs sources, review date and interpretation')
        sources = {s['id'] for s in item['sources']}
        if len(sources) != len(item['sources']):
            raise ValueError('Duplicate source identity')
        for source in item['sources'] + item.get('related', []):
            parsed = urlsplit(source['url'])
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError('Sources must be public HTTPS links')
        if any(s.get('coverage') != 'link_only' for s in item['sources']):
            raise ValueError('Release-file sources must declare link-only coverage')
        for point in item['interpretation']:
            for key in ('title', 'text', 'locator'):
                text(point[key], key, 1600)
            if not point.get('source_ids') or not set(point['source_ids']) <= sources:
                raise ValueError('Each interpretation point needs a registered source')
    return data


def news(q='', id='', revision=''):
    q, id = text(q, 'q', 200, False).casefold(), text(id, 'id', 100, False)
    try:
        data = validate(json.loads(CONTENT_PATH.read_text()))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise PlatformError('News collection is temporarily unavailable', 'news_unavailable', 503) from exc
    fields = ('id', 'name', 'organization', 'title', 'summary', 'source_published_at', 'event_date',
              'checked_at', 'interpretation', 'sources', 'related', 'note', 'editor', 'highlight')
    published = []
    for item in data['items']:
        if item['state'] != 'published':
            continue
        obj = {k: item[k] for k in fields}
        obj['interpretation'] = [{k: point[k] for k in ('title', 'text', 'source_ids', 'locator')} for point in item['interpretation']]
        obj['sources'] = [{k: source[k] for k in ('id', 'title', 'url', 'coverage')} for source in item['sources']]
        obj['related'] = [{k: ref[k] for k in ('id', 'name', 'url')} for ref in item['related']]
        published.append(obj)
    fingerprint = hashlib.sha256(json.dumps({'items': published, **{k: data[k] for k in ('schema_version', 'edition', 'title', 'reviewed_at')}}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    if revision and revision != fingerprint:
        raise PlatformError('News revision changed; read the current collection', 'news_revision_changed', 409)
    entries = [item for item in published if (not id or item['id'] == id) and
               (not q or q in ' '.join([item['title'], item['name'], item['organization'], item['summary']]).casefold())]
    if id and not entries:
        raise PlatformError('News item not found or withdrawn', 'not_found', 404)
    return {'schema_version': data['schema_version'], 'edition': data['edition'], 'title': data['title'],
            'reviewed_at': data['reviewed_at'], 'revision': fingerprint, 'total': len(entries),
            'scope': 'reviewed release news; sources are link-only, interpretation is FieldToFit editorial',
            'items': [{k: item[k] for k in fields} for item in entries]}
