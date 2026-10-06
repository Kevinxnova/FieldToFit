"""Reviewed source-post snapshots, published inside their existing news revision."""
from datetime import date, datetime
import re
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from backend.knowledge.platform import text

KINDS = ('primary', 'supplement', 'reply', 'correction')
FIELDS = ('url', 'kind', 'author_name', 'author_handle', 'text_en', 'translation_zh',
          'text_scope', 'announced_at', 'timestamp_basis', 'evidence_url',
          'retrieval_method', 'checked_at', 'reuse_basis')


def post_identity(url):
    parsed = urlsplit(url)
    match = re.fullmatch(r'/([A-Za-z0-9_]{1,15})/status/(\d{1,20})', parsed.path)
    if parsed.scheme != 'https' or parsed.hostname not in ('x.com', 'twitter.com') or parsed.port not in (None, 443) or parsed.username or parsed.password or parsed.query or parsed.fragment or not match or int(match[2]) > 2**63 - 1:
        raise ValueError('原帖需要不含跟踪参数的 X / Twitter 状态链接')
    return match[1].lower(), match[2]


def reviewed_date(value):
    day = date.fromisoformat(value)
    if day > datetime.now(ZoneInfo('Asia/Shanghai')).date():
        raise ValueError('原帖核对日期不能在未来')
    return value


def normalize(posts, sources):
    from backend.knowledge.codex_progress import instant
    if not isinstance(posts, list) or len(posts) > 8:
        raise ValueError('原帖为至多八项的对象列表')
    result, seen = [], set()
    for raw in posts:
        if not isinstance(raw, dict):
            raise ValueError('原帖必须为对象')
        for key in FIELDS:
            text(raw.get(key), 'source_posts.' + key, 10000 if key in ('text_en', 'translation_zh') else 2000)
        handle, ident = post_identity(raw['url'])
        if handle != 'thsottiaux' or raw['author_handle'].lower().lstrip('@') != handle or raw['url'] not in sources:
            raise ValueError('Tibo原帖须匹配账号并登记在该动态出处中')
        if ident in seen or raw['kind'] not in KINDS:
            raise ValueError('原帖重复或关联类型无效')
        seen.add(ident)
        if raw['evidence_url'] not in sources or raw['text_scope'] not in ('excerpt', 'full') or raw['retrieval_method'] not in ('direct_x', 'official_embed'):
            raise ValueError('记录原帖获取出处、方式及正文完整度')
        timestamp = instant(raw['announced_at'])
        if raw['timestamp_basis'] not in ('official_timestamp', 'post_id_derived') or timestamp > datetime.now(timestamp.tzinfo):
            raise ValueError('原帖时刻需要已发生的真实依据')
        if raw['timestamp_basis'] == 'post_id_derived' and abs(timestamp.timestamp() * 1000 - ((int(ident) >> 22) + 1288834974657)) > 1:
            raise ValueError('原帖时刻与帖子 ID 推导不一致')
        reviewed_date(raw['checked_at'])
        obj = {key: raw[key] for key in FIELDS}
        obj['author_handle'] = handle
        if raw.get('avatar') is not None:
            avatar = raw['avatar']
            if not isinstance(avatar, dict):
                raise ValueError('头像资料必须为对象')
            for key in ('url', 'source_url', 'evidence_url', 'checked_at', 'retrieval_method'):
                text(avatar.get(key), 'avatar.' + key, 2000)
            source = urlsplit(avatar['source_url'])
            if source.scheme != 'https' or source.hostname not in ('pbs.twimg.com', 'us1.discourse-cdn.com') or source.port not in (None, 443) or source.username or source.password or source.fragment:
                raise ValueError('头像原图须来自 X 或官方社区原帖嵌入')
            display = urlsplit(avatar['url'])
            cached = re.fullmatch(r'/source-authors/[a-z0-9-]+\.(?:jpg|jpeg|png|webp)', avatar['url'])
            if not cached and avatar['url'] != avatar['source_url']:
                raise ValueError('头像使用原图或本站审核缓存')
            if display.scheme and display.scheme != 'https':
                raise ValueError('头像地址无效')
            if avatar['evidence_url'] not in sources or avatar['retrieval_method'] not in ('direct_x', 'official_embed'):
                raise ValueError('头像需要已登记的身份核对出处')
            reviewed_date(avatar['checked_at'])
            obj['avatar'] = {key: avatar[key] for key in ('url', 'source_url', 'evidence_url', 'checked_at', 'retrieval_method')}
        if raw.get('context') is not None:
            context = raw['context']
            if not isinstance(context, dict) or context.get('kind') not in ('reply', 'quote'):
                raise ValueError('引用／回复资料无效')
            for key in ('url', 'author_name', 'author_handle', 'text_en', 'translation_zh', 'text_scope'):
                text(context.get(key), 'context.' + key, 10000)
            context_handle, _ = post_identity(context['url'])
            if context['url'] not in sources or context['author_handle'].lower().lstrip('@') != context_handle or context['text_scope'] not in ('excerpt', 'full'):
                raise ValueError('引用须保留独立账号、完整度和登记出处')
            obj['context'] = {key: context[key] for key in ('kind', 'url', 'author_name', 'author_handle', 'text_en', 'translation_zh', 'text_scope')}
        result.append(obj)
    if result and sum(p['kind'] == 'primary' for p in result) != 1:
        raise ValueError('同一事件须有且只有一条主原帖')
    return sorted(result, key=lambda p: (p['kind'] != 'primary', instant(p['announced_at']), p['url']))
