"""Explicit, reviewed excerpts and original figures; never derive quotations from notes."""
import ipaddress
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from backend.knowledge.platform import text

SCHEMA = 'fieldtofit.source-reading.v1'


def public_url(value):
    text(value, '原始地址', 2000)
    parsed = urlsplit(value)
    host = (parsed.hostname or '').lower()
    if parsed.scheme != 'https' or not host or parsed.username or parsed.password or host == 'localhost' or host.endswith(('.local', '.localhost')):
        raise ValueError('原文与原图须使用公开HTTPS地址')
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address and not address.is_global:
        raise ValueError('原文与原图不能使用私有地址')
    return value


def metadata(item):
    value = item.get('source_reading')
    if value is None:
        return None
    if not isinstance(value, dict) or value.get('schema_version') != SCHEMA:
        raise ValueError('原文阅读格式错误')
    blocks = value.get('blocks')
    if not isinstance(blocks, list) or not 1 <= len(blocks) <= 30:
        raise ValueError('原文阅读须有1至30段摘录或原图')
    sources = {s['id']: s for s in item.get('sources', [])}
    out = {'schema_version': SCHEMA, 'blocks': []}
    ids = set()
    for block in blocks:
        if not isinstance(block, dict):
            raise ValueError('摘录须为对象')
        ident = text(block.get('id'), '段落编号', 80)
        if not re.fullmatch(r'[a-z][a-z0-9-]*', ident) or ident in ids:
            raise ValueError('原文段落编号无效或重复')
        ids.add(ident)
        source_id = block.get('source_id')
        if source_id not in sources:
            raise ValueError('原文段落须引用本条已登记来源')
        public_url(sources[source_id]['url'])
        entry = {key: text(block.get(key), key, 400) for key in ('id', 'kind', 'source_id', 'locator', 'author', 'checked_at')}
        from backend.knowledge.content_workspace import today
        if date.fromisoformat(entry['checked_at']) > date.fromisoformat(today()):
            raise ValueError('原文核对日期不能在未来')
        if block['kind'] == 'quote':
            if block.get('original_language') not in ('en', 'zh'):
                raise ValueError('本版原文语言须为en或zh')
            entry.update(original_language=block['original_language'],
                         quote=text(block.get('quote'), '逐字原文', 12000),
                         translation_zh=text(block.get('translation_zh'), '中文译文', 12000, False),
                         reuse_basis=text(block.get('reuse_basis'), '摘录使用依据', 2000))
            if entry['original_language'] == 'en' and not entry['translation_zh']:
                raise ValueError('英文原文须附核对后的中文译文')
            if entry['original_language'] == 'zh' and entry['translation_zh']:
                raise ValueError('中文原文不另填中文译文')
        elif block['kind'] == 'figure':
            entry['original_url'] = public_url(block.get('original_url'))
            if block.get('display') not in ('link', 'embedded'):
                raise ValueError('原图须明确链接或嵌入')
            entry['display'] = block['display']
            entry['quote'] = text(block.get('quote'), '原始图注', 4000)
            entry['translation_zh'] = text(block.get('translation_zh'), '图注中文译文', 4000)
            if entry['display'] == 'embedded':
                url = text(block.get('image_url'), '已登记原图', 300)
                registry = json.loads((Path(__file__).parent/'content'/'report-figures.json').read_text())
                asset = registry.get(url, {})
                # Legacy redraws cannot be relabelled as upstream figures.
                if not re.fullmatch(r'/report-figures/[a-z0-9-]+\.png', url) or asset.get('kind') != 'original' or asset.get('original_url') != entry['original_url'] or sources[source_id]['url'].split('#')[0] not in asset.get('source_urls', []):
                    raise ValueError('嵌入须使用已登记的原图，不能使用重绘图')
                if not asset.get('license') or block.get('reuse_basis') != asset['license'] or not asset.get('rights_url'):
                    raise ValueError('原图须有已核对的复用依据')
                entry.update(image_url=url, reuse_basis=asset['license'], rights_url=public_url(asset['rights_url']),
                             alt=text(block.get('alt'), '原图替代文字', 2000))
        else:
            raise ValueError('原文阅读只接受摘录或原图')
        out['blocks'].append(entry)
    if not any(b['kind'] == 'quote' for b in out['blocks']):
        raise ValueError('原文阅读至少保留一段原始文字')
    return out
