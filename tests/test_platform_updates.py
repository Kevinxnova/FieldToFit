"""Read snapshots and editorial editions under concurrent source/publication changes."""
import sqlite3
from contextlib import contextmanager

import pytest
from test_knowledge import client, ADMIN, MCP
from test_platform import example, publish
from backend.db import get_db
from backend.knowledge import platform as p, platform_updates as u, store


def selected(suffix='one'):
    rid, mid, profile, body = example(suffix)
    publish(rid, profile)
    return p.get_object(rid), mid, profile


def draft_for(pub, mid, title='A sourced overview'):
    return {'title': title, 'period_start': '2026-09-08', 'period_end': '2026-09-09', 'entries': [
        {'object_id': pub['object']['id'], 'revision': pub['revision'], 'summary': 'An agent harness with tools.',
         'significance': 'Documents a concrete model requirement.', 'material_id': mid, 'quote': 'Requires a tool-calling model.'}]}


def edition_for(pub, mid):
    preview = u.save_edition(draft_for(pub, mid))
    return u.publish_edition(preview['id'], preview['review_token'], 'Original checked')


def withdraw(rid):
    preview = p.preview(rid)
    p.transition(rid, 'withdrawn', preview['review_token'], 'Private admin reason, must not be public')


def test_search_snapshot_survives_insert_update_and_repeated_pages(client):
    first, mid, profile = selected('one')
    second, _, _ = selected('two')
    page = p.search(limit=1)
    assert page['items'][0]['object']['id'] == second['object']['id']
    profile['introduction'] += ' Revised.'
    publish(first['object']['id'], profile)
    selected('three')
    later = p.search(limit=1, cursor=page['next_cursor'])
    assert later['total'] == 2 and not later['has_more']
    assert later['items'][0]['revision'] == first['revision']
    assert later['items'][0]['is_current'] is False
    assert p.search(limit=1, cursor=page['next_cursor']) == later
    assert p.search()['total'] == 3


def test_snapshot_withdrawal_redacts_but_preserves_position(client):
    first, _, _ = selected('one')
    selected('two')
    page = p.search(limit=1)
    withdraw(first['object']['id'])
    later = p.search(limit=1, cursor=page['next_cursor'])
    assert later['total'] == 2
    tombstone = later['items'][0]
    assert tombstone['unavailable'] and tombstone['object'] == {'id':first['object']['id']}
    assert 'An agent' not in store.encode(later)


def test_cursor_scope_malformed_and_expiration_have_api_errors(client):
    selected()
    page = p.search(q='harness', limit=1)
    cursor = page['page_cursor']
    response = client.get('/api/v1/platform/objects', query_string={'cursor':cursor,'limit':1,'q':'other'})
    assert response.status_code == 400 and response.json['code'] == 'cursor_scope_mismatch'
    assert client.get('/api/v1/platform/objects?cursor=broken').json['code'] == 'invalid_cursor'
    with get_db() as db:
        db.execute("UPDATE knowledge_read_snapshots SET expires_at='2000-01-01T00:00:00+00:00'")
    response = client.get('/api/v1/platform/objects', query_string={'cursor':cursor,'q':'harness','limit':1})
    assert response.status_code == 410 and response.json['code'] == 'snapshot_expired'
    mcp = client.post('/api/mcp', headers=MCP, json={'jsonrpc':'2.0','id':1,'method':'tools/call',
        'params':{'name':'curated_search','arguments':{'cursor':cursor,'q':'harness','limit':1}}}).json['result']
    assert mcp['isError'] and mcp['structuredContent']['code'] == 'snapshot_expired'


def test_changes_window_and_checkpoint_omit_private_drafts(client):
    pub, mid, profile = selected()
    rid = pub['object']['id']
    unpub, _, draft, _ = example('private')
    p.save_profile(unpub, draft, 0, 'Private pending notes')
    first = u.changes(limit=1)
    assert first['total'] == 1 and first['items'][0]['kind'] == 'added'
    checkpoint = first['resume_cursor']
    # A check-only update must not generate an event.
    record = store.get_record(rid); record['checked_at'] = store.now()
    store.save_record(record, 'Check only', rid)
    assert not u.changes(limit=1, cursor=checkpoint)['items']
    profile['introduction'] += ' Corrected.'
    draft = p.save_profile(rid, profile, p.preview(rid)['profile_revision'], 'Private correction notes')
    p.transition(rid, 'review', draft['review_token'], 'Review')
    p.transition(rid, 'published', p.preview(rid)['review_token'], 'Approved')
    window = u.changes(limit=1, cursor=checkpoint)
    assert window['items'][0]['kind'] == 'needs_review' and window['has_more']
    withdraw(rid)  # Must stay out of the existing window, even though read access is redacted now.
    last = u.changes(limit=1, cursor=window['next_cursor'])
    assert last['items'][0]['kind'] == 'updated' and 'introduction' in last['items'][0]['changed_fields']
    assert last['items'][0]['availability'] == 'unavailable'
    following = u.changes(limit=1, cursor=last['resume_cursor'])
    assert [x['kind'] for x in following['items']] == ['withdrawn']
    all_events = store.encode(u.changes())
    assert 'Private' not in all_events and unpub not in all_events


def test_changes_filters_bound_to_checkpoint_and_source_withdrawal(client):
    pub, _, _ = selected()
    other, _, _ = selected('other')
    rid = pub['object']['id']
    page = u.changes(object_ids=[rid])
    assert len(page['items']) == 1
    with pytest.raises(p.PlatformError, match='another query'):
        u.changes(cursor=page['resume_cursor'], object_ids=[other['object']['id']])
    record = store.get_record(rid); record['status'] = 'withdrawn'
    store.save_record(record, 'Source removed', rid)
    assert u.changes(object_ids=[rid], cursor=page['resume_cursor'])['items'][0]['kind'] == 'withdrawn'
    with pytest.raises(p.PlatformError):
        u.changes(after=999999)
    with pytest.raises(p.PlatformError):
        u.changes(object_ids='')


def test_grouped_selection_emits_withdrawal_and_undo_requires_review(client):
    from backend.knowledge.editorial import merge, undo
    pub, _, _ = selected()
    other, _, _ = selected('other')
    rid = pub['object']['id']
    action = merge(other['object']['id'], [rid], 'Same upstream identity')
    assert u.changes(object_ids=[rid])['items'][-1]['kind'] == 'withdrawn'
    undo(action['action_id'], 'Incorrect grouping')
    assert p.preview(rid)['selection']['state'] == 'withdrawn'
    with pytest.raises(p.PlatformError):
        p.get_object(rid, pub['revision'])


def test_edition_draft_is_private_and_human_ai_share_published_revision(client):
    pub, mid, _ = selected()
    preview = u.save_edition(draft_for(pub, mid))
    assert u.editions()['total'] == 0
    assert client.get('/api/v1/platform/editions/' + preview['id']).status_code == 404
    done = u.publish_edition(preview['id'], preview['review_token'], 'Checked')
    current = client.get('/api/v1/platform/editions/' + preview['id']).json
    assert current['revision'] == done['published_revision']
    assert current['entries'][0]['source_url'].endswith('/README.md')
    mcp = client.post('/api/mcp', headers=MCP, json={'jsonrpc':'2.0','id':1,'method':'tools/call',
        'params':{'name':'curated_edition','arguments':{'id':preview['id']}}}).json['result']['structuredContent']
    assert current == mcp
    data = draft_for(pub, mid, 'A corrected edition')
    edited = u.save_edition(data, preview['id'], done['revision'])
    assert u.edition(preview['id'])['title'] == 'A sourced overview'
    new = u.publish_edition(preview['id'], edited['review_token'], 'Title corrected')
    assert u.edition(preview['id'])['title'] == 'A corrected edition'
    assert u.edition(preview['id'], done['published_revision'])['title'] == 'A sourced overview'
    assert new['published_revision'] != done['published_revision']


def test_edition_rechecks_materials_and_handles_conflicts(client):
    pub, mid, profile = selected()
    draft = u.save_edition(draft_for(pub, mid))
    data = draft_for(pub, mid, 'Changed by another editor')
    edited = u.save_edition(data, draft['id'], draft['revision'])
    with pytest.raises(p.PlatformError) as err:
        u.save_edition(data, draft['id'], draft['revision'])
    assert err.value.code == 'revision_conflict'
    with pytest.raises(p.PlatformError) as err:
        u.publish_edition(draft['id'], draft['review_token'], 'Stale preview')
    assert err.value.code == 'revision_conflict'
    profile['introduction'] += ' Needs another review.'
    p.save_profile(pub['object']['id'], profile, p.preview(pub['object']['id'])['profile_revision'], 'Changed source')
    with pytest.raises(p.PlatformError):
        u.publish_edition(draft['id'], edited['review_token'], 'Source changed meanwhile')
    fresh = u.edition_preview(draft['id'])
    assert not fresh['gate']['ready']
    with pytest.raises(p.PlatformError) as err:
        u.publish_edition(draft['id'], fresh['review_token'], 'Publish anyway')
    assert err.value.status == 422


def test_edition_requires_quoted_primary_material_and_nonempty_entries(client):
    pub, mid, _ = selected()
    data = draft_for(pub, mid)
    data['entries'][0]['quote'] = 'Not in the source'
    draft = u.save_edition(data)
    assert not draft['gate']['ready']
    data['entries'] = []
    assert not u.save_edition(data)['gate']['ready']
    data['period_end'] = '2020-01-01'
    with pytest.raises(p.PlatformError):
        u.save_edition(data)


def test_edition_history_warns_on_source_change_and_redacts_withdrawal(client):
    pub, mid, profile = selected()
    done = edition_for(pub, mid)
    rid = pub['object']['id']
    profile['introduction'] += ' Changed.'
    publish(rid, profile)
    old = u.edition(done['id'])
    assert old['needs_review'] and old['entries'][0]['status'] == 'needs_review'
    withdraw(rid)
    old = u.edition(done['id'])
    assert old['entries'] == [{'object_id':rid,'revision':pub['revision'],'status':'unavailable'}]
    assert 'tool-calling' not in store.encode(old)


def test_edition_archive_pages_freeze_order_and_withdrawals(client):
    pub, mid, _ = selected()
    one = edition_for(pub, mid)
    two = edition_for(pub, mid)
    first = u.editions(limit=1)
    assert first['items'][0]['id'] == two['id']
    edition_for(pub, mid)
    u.publish_edition(one['id'], one['review_token'], 'Remove this edition', 'withdrawn')
    last = u.editions(limit=1, cursor=first['next_cursor'])
    assert last['total'] == 2 and last['items'][0]['unavailable']
    with pytest.raises(p.PlatformError) as err:
        u.edition(one['id'], one['published_revision'])
    assert err.value.status == 410


def test_edition_publication_and_pointer_roll_back_together(client, monkeypatch):
    pub, mid, _ = selected()
    preview = u.save_edition(draft_for(pub, mid))
    original = u.get_db
    @contextmanager
    def failing(*args, **kwargs):
        with original(*args, **kwargs) as db:
            class Proxy:
                def execute(self, sql, params=()):
                    if sql.startswith('UPDATE knowledge_editions SET published_revision'):
                        raise sqlite3.OperationalError('Injected pointer failure')
                    return db.execute(sql, params)
            yield Proxy()
    monkeypatch.setattr(u, 'get_db', failing)
    with pytest.raises(sqlite3.OperationalError):
        u.publish_edition(preview['id'], preview['review_token'], 'Transaction test')
    with get_db() as db:
        assert db.execute('SELECT COUNT(*) FROM knowledge_edition_publications').fetchone()[0] == 0
        assert db.execute('SELECT published_revision FROM knowledge_editions').fetchone()[0] is None


def test_read_token_cannot_write_or_read_edition_drafts(client, monkeypatch):
    pub, mid, _ = selected()
    draft = u.save_edition(draft_for(pub, mid))
    monkeypatch.setenv('FIELDTOFIT_READ_TOKEN', 'test-read-only')
    read = {'Authorization':'Bearer test-read-only'}
    path = '/api/v1/admin/platform/editions/' + draft['id']
    assert client.get(path, headers=read).status_code == 401
    assert client.post('/api/v1/admin/platform/editions', headers=read, json={'draft':draft['draft']}).status_code == 401
    assert client.get(path, headers=ADMIN).status_code == 200
    assert client.get('/api/v1/platform/editions', headers=read).json['total'] == 0


def test_material_loss_redacts_overview_entry_without_rewriting_history(client):
    pub, mid, _ = selected()
    done = edition_for(pub, mid)
    with get_db() as db:
        db.execute('DELETE FROM knowledge_evidence WHERE id=?', (mid,))
    result = u.edition(done['id'])
    assert result['needs_review'] and result['entries'][0]['status'] == 'unavailable'
    assert 'Supporting' not in store.encode(result)
    assert not u.edition_preview(done['id'])['gate']['ready']


def test_stable_previous_page_and_empty_change_checkpoint(client):
    selected()
    selected('other')
    first = p.search(limit=1)
    second = p.search(limit=1, cursor=first['next_cursor'])
    previous = p.search(limit=1, cursor=second['previous_cursor'])
    assert previous == first
    events = u.changes(object_ids=['not-curated'])
    assert not events['items']
    resumed = u.changes(object_ids=['not-curated'], cursor=events['resume_cursor'])
    assert not resumed['items'] and resumed['snapshot'] != events['snapshot']


def test_check_only_does_not_refresh_edition_or_create_duplicate_publication(client):
    pub, mid, _ = selected()
    done = edition_for(pub, mid)
    before = u.edition(done['id'])
    record = store.get_record(pub['object']['id'])
    record['checked_at'] = store.now()
    store.save_record(record, 'Daily check, same material', record['id'])
    preview = u.edition_preview(done['id'])
    u.publish_edition(done['id'], preview['review_token'], 'No changes')
    assert u.edition(done['id']) == before
    with get_db() as db:
        assert db.execute('SELECT COUNT(*) FROM knowledge_edition_publications').fetchone()[0] == 1


def test_explicit_reopening_of_published_review_is_visible_as_selection_exit(client):
    pub, _, _ = selected()
    rid = pub['object']['id']
    checkpoint = u.changes()['resume_cursor']
    p.transition(rid, 'review', p.preview(rid)['review_token'], 'Reopen published review')
    assert p.search()['total'] == 0
    events = u.changes(cursor=checkpoint)['items']
    assert len(events) == 1 and events[0]['kind'] == 'needs_review'
    assert events[0]['from_revision'] == pub['revision']


def test_change_checkpoint_excludes_publication_between_queries(client, monkeypatch):
    selected('before-checkpoint')
    inserted = []

    class InterleavedRead:
        def __init__(self, db):
            self.db = db

        def execute(self, sql, params=()):
            cursor = self.db.execute(sql, params)
            if sql == 'SELECT COALESCE(MAX(seq),0) FROM knowledge_publications' and not inserted:
                upper = cursor.fetchone()
                inserted.append(selected('after-checkpoint')[0])
                class FrozenMaximum:
                    def fetchone(self):
                        return upper
                return FrozenMaximum()
            return cursor

    @contextmanager
    def interleaved_db(*args, **kwargs):
        with get_db(*args, **kwargs) as db:
            yield InterleavedRead(db)

    monkeypatch.setattr(u, 'get_db', interleaved_db)
    first = u.changes()
    assert all(item['id'] <= first['until'] for item in first['items'])
    assert inserted[0]['object']['id'] not in {item['object_id'] for item in first['items']}
    following = u.changes(after=first['until'])
    assert inserted[0]['object']['id'] in {item['object_id'] for item in following['items']}
