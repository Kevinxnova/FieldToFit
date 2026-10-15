"""Small homepage projection of the same immutable, published daily edition."""
import json
from datetime import datetime, timezone

from backend.db import get_db
from .schema import TZ, project, fail
from .schedule import PUBLISH_AT, local_time


MANIFEST_SQL = """SELECT p.day,p.revision,p.content_hash,p.published_at,
 (SELECT first.published_at FROM fieldtofit_daily_publications first
  WHERE first.day=p.day ORDER BY first.revision LIMIT 1) AS first_published_at
 FROM fieldtofit_daily_publications p JOIN fieldtofit_daily_issues i
 ON i.day=p.day AND i.published_revision=p.revision
 WHERE i.state='published' ORDER BY p.day DESC"""


def clock(now=None):
    now = now or datetime.now(timezone.utc)
    return {'today': now.astimezone(TZ).date().isoformat(),
            'due': local_time(now) >= PUBLISH_AT, 'timezone': 'Asia/Shanghai'}


def preview(rows, timing, lang='zh'):
    result = {**timing, 'status': 'delayed' if timing['due'] else 'scheduled', 'issue': None}
    selected = next((row for row in rows if row['day'] <= timing['today']), None)
    if selected is None:
        return result
    with get_db() as db:
        row = db.execute("""SELECT p.snapshot_json FROM fieldtofit_daily_publications p
          JOIN fieldtofit_daily_issues i ON i.day=p.day AND i.published_revision=p.revision
          WHERE i.state='published' AND p.day=? AND p.revision=? AND p.content_hash=?""",
          (selected['day'], selected['revision'], selected['content_hash'])).fetchone()
    if row is None:
        fail('Daily publication changed during reading; retry', 'reading_changed', 503)
    raw = json.loads(row['snapshot_json'])
    issue = project({key: raw[key] for key in ('date', 'kind', 'headline', 'intro')}, lang)
    issue['highlights'] = project([
        {key: story[key] for key in ('id', 'section', 'title', 'summary')}
        for story in raw['stories'] if story['highlight']
    ][:3], lang)
    issue['publication'] = {key: selected[key] for key in
                           ('revision', 'content_hash', 'published_at', 'first_published_at')}
    issue['path'] = '/for-you/daily/' + issue['date']
    result['issue'] = issue
    if issue['date'] == timing['today'] and issue['kind'] == 'daily':
        result['status'] = 'published'
    return result
