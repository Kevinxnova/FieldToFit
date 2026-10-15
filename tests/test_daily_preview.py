"""Homepage edition identity, cache clock and withdrawal boundaries in isolated SQLite."""
from copy import deepcopy
import html
import json
import re

import pytest
from test_knowledge import client
from test_search_pages import site
from test_daily_journal import issue, publish, ready, renderer, REASON
from backend.daily_briefing import home, service
from backend.daily_briefing.schema import digest, instant
from backend.db import get_db
from backend.knowledge.mcp import invoke

PATH = '/api/v1/platform/reading'


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch):
    actual = home.clock
    current = ['2026-10-15T09:00:00+08:00']
    monkeypatch.setattr(home, 'clock', lambda: actual(instant(current[0])))
    return current


def frozen_publication(raw, day, *, kind='daily', state='published', revision=1):
    """Stored publication fixture; publication validation is covered by test_daily_journal."""
    raw = deepcopy(raw)
    raw.update(date=day, kind=kind)
    stamp = day + 'T09:03:00+08:00'
    encoded = json.dumps(raw, ensure_ascii=False)
    with get_db() as db:
        db.execute('INSERT OR REPLACE INTO fieldtofit_daily_issues VALUES(?,?,?,?,?,?,?,?,?)',
                   (day, encoded, revision, None, '{}', revision, state, stamp, stamp))
        db.execute('INSERT INTO fieldtofit_daily_publications VALUES(?,?,?,?,?,?)',
                   (day, revision, encoded, digest(raw), stamp, json.dumps(REASON)))
    return raw


def test_empty_and_beijing_clock_invalidate_after_without_a_publication(client, fixed_clock):
    fixed_clock[0] = '2026-10-15T08:59:59+08:00'
    early = client.get(PATH).json
    assert early['daily']['status'] == 'scheduled' and early['daily']['issue'] is None
    fixed_clock[0] = '2026-10-15T09:00:00+08:00'
    late = client.get(PATH, query_string={'after': early['revision']}).json
    assert late['daily']['status'] == 'delayed' and late['revision'] != early['revision']
    assert late['daily']['today'] == '2026-10-15'


def test_preview_matches_published_daily_and_mcp_without_heavy_or_private_data(client, issue):
    initial = client.get(PATH).json
    version = ready(issue)
    assert client.get(PATH).json == initial
    service.publish(issue['date'], version, REASON)
    zh = client.get(PATH).json
    for lang in ('zh', 'en'):
        daily = client.get(PATH, query_string={'lang': lang}).json['daily']
        complete = invoke('curated_daily', {'day': issue['date'], 'lang': lang})
        preview = daily['issue']
        assert preview['headline'] == complete['headline']
        assert preview['intro'] == complete['intro']
        assert preview['publication']['content_hash'] == complete['publication']['content_hash']
        assert preview['publication']['revision'] == complete['publication']['revision']
        assert preview['highlights'] == [{k:s[k] for k in ('id','section','title','summary')}
                                         for s in complete['stories'] if s['highlight']]
        assert not {'markets','products','pdf','coverage','review','sources'} & preview.keys()
        assert len(json.dumps(daily)) < len(json.dumps(complete)) / 3
        assert daily['status'] == 'delayed' and preview['kind'] == 'review_sample'
    issue['headline']['zh'] = 'PRIVATE UNPUBLISHED TITLE'
    service.save(issue, version)
    assert client.get(PATH).json == zh


def test_current_issue_correction_and_midnight_keep_original_dates(client, issue, fixed_clock):
    frozen_publication(issue, '2026-10-15')
    before = client.get(PATH).json
    assert before['daily']['status'] == 'published'
    issue['headline']['zh'] += ' 已更正'
    frozen_publication(issue, '2026-10-15', revision=2)
    with get_db() as db:
        db.execute("UPDATE fieldtofit_daily_publications SET published_at='2026-10-15T10:10:00+08:00' WHERE revision=2")
    after = client.get(PATH, query_string={'after':before['revision']}).json
    pub = after['daily']['issue']['publication']
    assert pub['first_published_at'] == '2026-10-15T09:03:00+08:00'
    assert pub['published_at'] == '2026-10-15T10:10:00+08:00' and pub['revision'] == 2
    fixed_clock[0] = '2026-10-15T16:00:00Z'  # Beijing midnight, not UTC midnight.
    next_day = client.get(PATH, query_string={'after':after['revision']}).json
    assert next_day['daily']['status'] == 'scheduled'
    assert next_day['daily']['today'] == '2026-10-16'
    assert next_day['daily']['issue']['date'] == '2026-10-15'


def test_withdrawal_falls_back_and_drafts_future_or_samples_never_become_today(client, issue):
    frozen_publication(issue, '2026-10-13', kind='review_sample')
    frozen_publication(issue, '2026-10-15')
    frozen_publication(issue, '2026-10-16')
    before = client.get(PATH).json
    assert before['daily']['issue']['date'] == '2026-10-15'
    service.withdraw('2026-10-15', 1, REASON)
    after = client.get(PATH, query_string={'after':before['revision']}).json
    assert '2026-10-15' not in after['safety']['daily']
    assert after['daily']['issue']['date'] == '2026-10-13'
    assert after['daily']['status'] == 'delayed'
    service.withdraw('2026-10-13', 1, REASON)
    assert client.get(PATH).json['daily']['issue'] is None
    frozen_publication(issue, '2026-10-14', state='draft')
    assert client.get(PATH).json['daily']['issue'] is None


@pytest.mark.parametrize('count', [0,1,2,3])
def test_actual_highlight_count_and_full_title_are_preserved(client, issue, count):
    for index, story in enumerate(issue['stories']):
        story['highlight'] = index < count
    issue['headline']['en'] = 'A long headline with conditions and dates that must remain completely readable. ' * 4
    frozen_publication(issue, '2026-10-15')
    data = client.get(PATH+'?lang=en').json['daily']['issue']
    assert len(data['highlights']) == count
    assert data['headline'] == issue['headline']['en']


def test_warm_home_reuses_daily_projection_but_rechecks_current_state(client, issue, monkeypatch):
    publish(issue)
    first = client.get(PATH).json
    def unexpected(*args):
        raise AssertionError('Warm homepage reloaded the whole issue')
    monkeypatch.setattr(home, 'preview', unexpected)
    assert client.get(PATH).json == first
    assert client.get(PATH, query_string={'after':first['revision']}).json['unchanged']


def test_daily_dependency_failure_never_returns_cached_publication(client, issue, monkeypatch):
    publish(issue)
    first = client.get(PATH).json
    monkeypatch.setattr(home, 'MANIFEST_SQL', 'SELECT private_database_error FROM fieldtofit_daily_issues')
    response = client.get(PATH, query_string={'after':first['revision']})
    assert response.status_code == 503
    assert 'private_database_error' not in response.text and 'daily' not in response.json


def test_direct_html_bootstrap_api_and_daily_anchors_are_same_edition(site, issue):
    publish(issue)
    for prefix, lang in (('', 'zh'), ('/en', 'en')):
        response = site.get(prefix+'/for-you')
        assert response.status_code == 200
        api = site.get(PATH, query_string={'lang':lang}).json
        boot = json.loads(re.search(r'id="fieldtofit-reading">(.*?)</script>', response.text, re.S)[1])
        assert boot['data']['daily'] == api['daily']
        section = response.text.split('<section id="daily-preview"',1)[1].split('</section>',1)[0]
        preview = api['daily']['issue']
        assert html.escape(preview['headline']) in section
        assert preview['publication']['content_hash'] in section
        detail = site.get(prefix+preview['path'])
        for story in preview['highlights']:
            assert prefix+preview['path']+'?revision=1#daily-story-'+story['id'] in section
            assert 'id="daily-story-'+story['id']+'"' in detail.text
        if lang == 'en':
            assert not re.search(r'[\u4e00-\u9fff]',section)
