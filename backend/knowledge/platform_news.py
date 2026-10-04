"""Reviewed news shared by web and MCP; workspace publications override released seed files."""
import hashlib
import json
import re
from pathlib import Path
from datetime import date, datetime
from urllib.parse import urlsplit
from backend.knowledge.platform import PlatformError, text

CONTENT_PATH = Path(__file__).parent / 'content' / 'news.json'


MEDIA_FIELDS = ('url', 'full_url', 'alt', 'caption', 'source_url', 'credit', 'reuse_basis', 'version', 'reviewed_at', 'fit')
NEWS_CATEGORIES = ('model', 'agent', 'tool', 'skill', 'harness', 'research', 'industry', 'other')


def reading_fields(item):
    """Optional reviewed media; nothing is scraped or fetched during publication."""
    result = {}
    if 'category' in item:
        if item['category'] not in NEWS_CATEGORIES:
            raise ValueError('Invalid news category')
        result['category'] = item['category']
    if item.get('media') is not None:
        media = item['media']
        if not isinstance(media, dict):
            raise ValueError('Media must be an object')
        for key in MEDIA_FIELDS:
            text(media.get(key), 'media.' + key, 2000)
        for key in ('url', 'full_url', 'source_url'):
            parsed = urlsplit(media[key])
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError('Media requires public HTTPS URLs')
            import ipaddress
            host = parsed.hostname.lower()
            if host == 'localhost' or host.endswith(('.localhost', '.local')):
                raise ValueError('Media cannot use local hosts')
            try:
                address = ipaddress.ip_address(host)
            except ValueError:
                address = None
            if address and not address.is_global:
                raise ValueError('Media cannot use private addresses')
        if media['fit'] not in ('contain', 'cover'):
            raise ValueError('Media fit must be contain or cover')
        date.fromisoformat(media['reviewed_at'])
        result['media'] = {key: media[key] for key in MEDIA_FIELDS}
    if item.get('publication') is not None:
        pub = item['publication']
        if not isinstance(pub, dict):
            raise ValueError('Invalid publication dates')
        result['publication'] = {}
        for key in ('first_published_at', 'updated_at'):
            value = pub.get(key)
            if value is not None:
                parsed = datetime.fromisoformat(value)
                if parsed.tzinfo is None:
                    raise ValueError('Publication timestamp requires a timezone')
            result['publication'][key] = value
    return result


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
        reading_fields(item)
        from backend.knowledge.platform_lookup import aliases
        aliases(item.get('aliases', []))
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


def news(q='', id='', revision='', _data=None):
    requested_id=id
    if id and _data is None:
        from backend.knowledge.stewardship import resolve
        id=resolve(id)
    q, id = text(q, 'q', 200, False).casefold(), text(id, 'id', 100, False)
    try:
        from backend.knowledge.content_workspace import load_published
        data = validate(_data if _data is not None else load_published('news', CONTENT_PATH))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise PlatformError('News collection is temporarily unavailable', 'news_unavailable', 503) from exc
    fields = ('id', 'name', 'organization', 'title', 'summary', 'source_published_at', 'event_date',
              'checked_at', 'interpretation', 'sources', 'related', 'note', 'editor', 'highlight')
    published = []
    for item in data['items']:
        if item['state'] != 'published':
            continue
        obj = {k: item[k] for k in fields}
        obj.update(reading_fields(item))
        if item.get('aliases'):
            from backend.knowledge.platform_lookup import aliases
            obj['aliases'] = aliases(item['aliases'])
        obj['interpretation'] = [{k: point[k] for k in ('title', 'text', 'source_ids', 'locator')} for point in item['interpretation']]
        obj['sources'] = [{k: source[k] for k in ('id', 'title', 'url', 'coverage')} for source in item['sources']]
        obj['related'] = [{k: ref[k] for k in ('id', 'name', 'url')} for ref in item['related']]
        from backend.knowledge.content_materials import manifest
        obj.update(manifest(item))
        published.append(obj)
    fingerprint = hashlib.sha256(json.dumps({'items': published, **{k: data[k] for k in ('schema_version', 'edition', 'title', 'reviewed_at')}}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    if revision and revision != fingerprint:
        raise PlatformError('News revision changed; read the current collection', 'news_revision_changed', 409)
    entries = [item for item in published if (not id or item['id'] == id) and
               (not q or q in ' '.join([item['title'], item['name'], item['organization'], item['summary']]).casefold())]
    if id and not entries:
        raise PlatformError('News item not found or withdrawn', 'not_found', 404)
    from backend.knowledge.stewardship import decorate
    return {'schema_version': data['schema_version'], 'edition': data['edition'], 'title': data['title'],
            'reviewed_at': data['reviewed_at'], 'revision': fingerprint, 'total': len(entries),
            'scope': 'reviewed release news; source links and optional reviewed materials have explicit coverage; interpretation is FieldToFit editorial',
            'items': entries if _data is not None else decorate(entries),
            **({'resolved_from':requested_id,'canonical_id':id} if requested_id and requested_id!=id else {})}
