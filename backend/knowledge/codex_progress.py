"""A date projection of reviewed news, with no separate event store or review states."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

START = date(2026, 10, 5)
END = START + timedelta(days=27)
TYPES = ('feature', 'model', 'speed', 'fix', 'reset', 'announcement')
TOPIC = {
    'id': 'codex-28-days', 'title': 'Codex 28天进化日志',
    'title_en': 'Codex: 28 Days of Progress',
    'subtitle': '每天一项改进，或一次额度重置',
    'subtitle_en': 'An improvement each day, or a usage reset',
    'start_date': START.isoformat(), 'end_date': END.isoformat(), 'timezone': 'Asia/Shanghai',
    'pledge': {
        'url': 'https://x.com/thsottiaux/status/2106845241357824205',
        'evidence_url': 'https://community.openai.com/t/day-1-of-28-days-of-quality-of-life-improvements-or-a-full-reset/1403525',
        'announced_at': '2026-10-04T20:33:43.488Z', 'timestamp_basis': 'post_id_derived',
        'summary': 'Tibo宣布，接下来28天每天提供一项与多数Codex／Work用户相关的明确改进，或一次完整额度重置。',
        'summary_en': 'Tibo announced 28 days of clear improvements relevant to most Codex / Work users, or full usage resets.',
    },
}


def instant(value):
    if not isinstance(value, str):
        raise ValueError('专题发布时间需要带时区的 ISO 时间')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('专题发布时间必须包含时区')
    return parsed


def metadata(item):
    raw = item.get('codex_28_days')
    if raw is None:
        return None
    if not isinstance(raw, dict) or raw.get('group') not in ('codex', 'other_openai') or raw.get('type') not in TYPES:
        raise ValueError('专题分组或更新类型无效')
    sources = {s['url'] for s in item.get('sources', [])}
    if raw.get('event_key') not in sources:
        raise ValueError('专题事件标识必须是已登记的官方出处链接')
    official = raw.get('official_day')
    if official is not None and (isinstance(official, bool) or not isinstance(official, int) or not 1 <= official <= 28 or raw['group'] != 'codex'):
        raise ValueError('官方 Day 编号须为 1–28，仅用于 Codex 主线')
    precision, basis = raw.get('date_precision'), raw.get('timestamp_basis')
    if precision == 'instant':
        if basis not in ('official_timestamp', 'post_id_derived'):
            raise ValueError('记录专题时间依据')
        day = instant(raw.get('announced_at')).astimezone(ZoneInfo('Asia/Shanghai')).date()
        if item.get('event_date') != day.isoformat():
            raise ValueError('事件日期须与专题时间换算出的北京日期一致')
    elif precision == 'source_date':
        if basis != 'source_date' or raw.get('announced_at') is not None:
            raise ValueError('仅有来源日期时不填推测时刻')
        day = date.fromisoformat(item['source_published_at'])
        if item.get('event_date') is not None:
            raise ValueError('来源日期不能推造为北京事件日期')
    else:
        raise ValueError('专题日期精度无效')
    # The final official announcement can cross midnight into Beijing Nov 2.
    if not START <= day <= END + timedelta(days=1) or day > datetime.now(ZoneInfo('Asia/Shanghai')).date():
        raise ValueError('专题记录日期超出窗口或位于未来')
    if day > END and official != 28:
        raise ValueError('末日跨日补录需有官方 Day 28 依据')
    result = {k: raw.get(k) for k in ('event_key', 'group', 'type', 'official_day', 'date_precision', 'announced_at', 'timestamp_basis')}
    result.update(date=day.isoformat(), calendar_day=(day - START).days + 1)
    if raw['type'] == 'reset':
        reset = raw.get('reset')
        if raw['group'] != 'codex' or not isinstance(reset, dict):
            raise ValueError('额度重置需要确认的适用范围')
        from backend.knowledge.platform import text
        for key in ('scope', 'plans', 'source_url'):
            text(reset.get(key), 'reset.' + key, 1600)
        if reset['source_url'] not in sources or instant(reset.get('effective_at')) > datetime.now(ZoneInfo('Asia/Shanghai')):
            raise ValueError('重置须有已生效时间和登记出处')
        result['reset'] = {k: reset[k] for k in ('scope', 'plans', 'source_url', 'effective_at')}
    return result


def projection(items):
    days, seen = {}, set()
    for item in items:
        meta = item.get('codex_28_days')
        if not meta:
            continue
        if meta['event_key'] in seen:
            raise ValueError('专题事件重复，请复用已有动态')
        seen.add(meta['event_key'])
        day = days.setdefault(meta['date'], {'date': meta['date'], 'calendar_day': meta['calendar_day'], 'codex_ids': [], 'other_openai_ids': []})
        day['codex_ids' if meta['group'] == 'codex' else 'other_openai_ids'].append(item['id'])
    by_id = {i['id']: i for i in items}
    for day in days.values():
        for group in ('codex_ids', 'other_openai_ids'):
            day[group].sort(key=lambda ident: (by_id[ident]['codex_28_days'].get('announced_at') or '', ident), reverse=True)
    return {**TOPIC, 'days': [days[key] for key in sorted(days, reverse=True)], 'total': len(seen)}
