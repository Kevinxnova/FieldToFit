"""Manually authored information cards, attached to an existing reviewed news item."""
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from backend.knowledge.platform import text

ASSETS = Path(__file__).resolve().parents[2] / 'frontend' / 'public' / 'hot-cards'
MANIFEST = Path(__file__).parent / 'content' / 'hot-card-assets.json'
PROSE = ('headline', 'scope', 'changes', 'audiences', 'limits', 'next_step', 'evidence', 'verification')


def fingerprint(item, card):
    """Layout, selection and check-only refreshes do not change the reading revision."""
    sources = {s['id']: s for s in item.get('sources', [])}
    value = {k: card[k] for k in PROSE}
    value.update(id=item['id'], name=item['name'], event_date=item.get('event_date'), source_published_at=item.get('source_published_at'),
                 revised_at=card['revised_at'], checked_at=card['checked_at'],
                 sources=[sources[e['source_id']] for e in card['evidence']])
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def metadata(item, enforce_assets=False):
    raw = item.get('hot_card')
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError('Hot information card must be an object')
    card = {}
    for key, maximum in (('headline', 90), ('scope', 220), ('next_step', 300), ('verification', 200)):
        card[key] = text(raw.get(key), 'hot_card.' + key, maximum)
    for key, minimum, maximum in (('changes', 3, 3), ('audiences', 2, 2), ('limits', 1, 5)):
        rows = raw.get(key)
        if not isinstance(rows, list) or not minimum <= len(rows) <= maximum or any(not isinstance(r, dict) for r in rows):
            raise ValueError('Invalid hot_card.' + key)
        card[key] = [{k: text(r.get(k), 'hot_card.' + key + '.' + k, 60 if k == 'title' else 300)
                      for k in ('title', 'detail')} for r in rows]
    sources = {s['id'] for s in item.get('sources', [])}
    evidence = raw.get('evidence')
    if not isinstance(evidence, list) or not 1 <= len(evidence) <= 5 or any(not isinstance(e, dict) for e in evidence):
        raise ValueError('Card requires official evidence and a locator')
    card['evidence'] = []
    for e in evidence:
        if e.get('source_id') not in sources:
            raise ValueError('Card evidence must reference a registered source')
        card['evidence'].append({'source_id': e['source_id'], 'locator': text(e.get('locator'), 'evidence.locator', 300)})
    for key in ('revised_at', 'checked_at'):
        value = text(raw.get(key), 'hot_card.' + key, 10)
        date.fromisoformat(value)
        if enforce_assets:
            from backend.knowledge.content_workspace import today
            if value > today():
                raise ValueError('Card dates cannot be in the future')
        card[key] = value
    rank = raw.get('featured_rank', 0)
    if type(rank) is not int or rank not in (0, 1, 2, 3):
        raise ValueError('Card selection must be 0 (archive) or 1–3')
    card['featured_rank'] = rank
    card['status'] = raw.get('status', 'current')
    if card['status'] not in ('current', 'needs_update'):
        raise ValueError('Invalid card maintenance status')
    card['update_note'] = text(raw.get('update_note', ''), 'hot_card.update_note', 300, card['status'] == 'needs_update')
    card['revision'] = fingerprint(item, card)
    share = raw.get('share') if card['status'] == 'current' else None
    if share is not None:
        if not isinstance(share, dict) or share.get('content_revision') != card['revision']:
            raise ValueError('Card text changed: remake and review both share images')
        card['share'] = {'content_revision': card['revision']}
        for lang in ('zh', 'en'):
            asset = share.get(lang)
            if not isinstance(asset, dict):
                raise ValueError('Both reviewed share images are required')
            url = text(asset.get('url'), 'share.' + lang, 240)
            if not re.fullmatch(r'/hot-cards/[a-z0-9][a-z0-9-]*-' + lang + r'\.png', url):
                raise ValueError('Share images must be local, versioned PNGs')
            digest = text(asset.get('sha256'), 'share.sha256', 64)
            if not re.fullmatch('[a-f0-9]{64}', digest):
                raise ValueError('Share image checksum required')
            if enforce_assets:
                registered = json.loads(MANIFEST.read_text()).get(url, {})
                if registered.get('sha256') != digest or registered.get('content_revision') != card['revision'] or registered.get('news_id') != item['id']:
                    raise ValueError('Share image is not registered for this reviewed card revision')
                if lang == 'en' and registered.get('text_revision') != asset.get('text_revision'):
                    raise ValueError('English share image does not match the registered copy')
                path = ASSETS / url.rsplit('/', 1)[1]
                # Production serves static files separately. The deployed manifest
                # pins approved bytes; local/release checks additionally inspect files.
                if ASSETS.exists() and (not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest):
                    raise ValueError('Share image missing or changed; review it again')
            card['share'][lang] = {'url': url, 'sha256': digest}
            if lang == 'en':
                revision = text(asset.get('text_revision'), 'share.en.text_revision', 64)
                if not re.fullmatch('[a-f0-9]{64}', revision):
                    raise ValueError('English image must reference the reviewed English copy')
                card['share'][lang]['text_revision'] = revision
    if card['status'] == 'current' and not share:
        raise ValueError('A current card requires manually reviewed share images')
    # No download is advertised while a known factual correction is pending.
    if card['status'] == 'needs_update':
        card.pop('share', None)
    return card


def validate_english_image(item, fields):
    from backend.knowledge.locale import project
    card = metadata(item)
    if card and card.get('share'):
        translated = project(item, fields)
        if fingerprint(translated, translated['hot_card']) != card['share']['en']['text_revision']:
            raise ValueError('English card text changed: remake and review the English image')


def validate_selection(items):
    ranks = []
    for item in items:
        card = item.get('hot_card')
        if item.get('state') != 'published' or card is None:
            continue
        if not isinstance(card, dict) or type(card.get('featured_rank', 0)) is not int or card.get('featured_rank', 0) not in (0, 1, 2, 3):
            raise ValueError('Invalid information card selection')
        ranks.append(card.get('featured_rank', 0))
    selected = [r for r in ranks if r]
    if len(selected) > 3 or len(set(selected)) != len(selected):
        raise ValueError('Choose at most three cards with distinct positions; unselect the replaced card first')
