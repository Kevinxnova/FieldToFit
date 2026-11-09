"""Company topics are projections of reviewed news, never a second content store."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

START = '2026-11-02'
COMPANIES = {'openai': 'OpenAI', 'anthropic': 'Anthropic'}


def metadata(item, today=None):
    company = next((key for key, name in COMPANIES.items() if item.get('organization') == name), None)
    if not company or item.get('state', 'published') != 'published':
        return None
    topic = item.get('codex_28_days') or {}
    stamp = topic.get('announced_at')
    day = topic.get('date') or item.get('event_date') or item.get('source_published_at') or ''
    today = today or datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat()
    try:
        date.fromisoformat(day)
    except (ValueError, TypeError):
        return None
    if not START <= day <= today:
        return None
    precision = topic.get('date_precision') or ('event_date' if item.get('event_date') else 'source_date')
    display = day
    if stamp:
        parsed = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
        if parsed.tzinfo:
            display = parsed.astimezone(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
    # Navigation labels only; never infer a new product fact from prose mentions.
    name = (item.get('name') or '').casefold()
    products = []
    if company == 'openai':
        if name.startswith('codex') or topic.get('group') == 'codex': products.append('codex')
        if name.startswith(('chatgpt', 'work')): products.append('chatgpt-work')
        if 'api' in name or name.startswith('gpt-'): products.append('models-api')
    else:
        if name.startswith('claude code'): products.append('claude-code')
        elif name.startswith('claude') and 'api' not in name: products.append('claude')
        if 'api' in name or name.startswith(('claude opus', 'claude sonnet', 'claude haiku')): products.append('models-api')
    return {'company': company, 'date': day, 'display_time': display, 'date_precision': precision,
            'products': products or ['other'], 'announced_at': stamp}


def ordered(items, company):
    return sorted((i for i in items if (i.get('company_update') or {}).get('company') == company),
                  key=lambda i: (i['company_update']['date'], i['company_update']['display_time'], int(i['id'].split('-')[-1])), reverse=True)


def projection(items):
    return {key: {'company': key, 'start_date': START, 'total': len(found), 'ids': [i['id'] for i in found],
                  'months': sorted({i['company_update']['date'][:7] for i in found}, reverse=True),
                  'products': sorted({p for i in found for p in i['company_update']['products']})}
            for key in COMPANIES for found in [ordered(items, key)]}


def filtered(items, company, product='', month='', query=''):
    return [i for i in ordered(items, company)
            if (not product or product in i['company_update']['products'])
            and (not month or i['company_update']['date'][:7] == month)
            and (not query or query.casefold() in ' '.join(str(i.get(k) or '') for k in ('title','summary','name')).casefold())]
