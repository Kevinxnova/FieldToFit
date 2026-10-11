"""Difference dispositions on isolated data: persistence, re-entry and privacy."""
import copy
import json
from contextlib import contextmanager
from datetime import date, timedelta

import pytest

from test_knowledge import client, ADMIN, MCP
from test_content_workspace import call, publish
from test_reviewed_maintenance import configured, review, ID, URL
from backend.db import get_db
from backend.knowledge import content_workspace as ws, object_checks as checks, check_decisions as decisions
from backend.knowledge import editorial_batches as batches, stewardship
from backend.knowledge.platform import PlatformError


def target(board=None):
    return next(r for r in (board or checks.overview())['items'] if r['id'] == ID)


def finding(client, monkeypatch):
    fetched = configured(client, monkeypatch)
    return target(checks.review(ws.today(), ID, review(fetched)))


def payload(row, status='declined', change=None):
    change = change or row['latest']['changes'][0]
    return {'day':ws.today(), 'attempt_id':row['attempt_id'], 'difference_id':change['difference_id'],
            'version':change['handling_version'], 'status':status, 'reason':'PRIVATE: not relevant to the supported version.',
            'recheck_condition':'PRIVATE: review when upstream documents a supported release.'}


@pytest.mark.parametrize('status', ['declined', 'evidence_withdrawn'])
def test_closed_evidence_remains_in_history_but_not_cross_day_work(client, monkeypatch, status):
    row = finding(client, monkeypatch)
    before_public = client.get('/api/v1/platform/watch').json
    before_totals = checks.overview()['totals']
    data = payload(row, status)
    board = decisions.handle(ws.today(), ID, data)
    assert board['totals'] == before_totals
    closed = target(board)
    assert closed['latest']['changes'] == []
    event = closed['handled_changes'][0]
    assert event['data']['change']['quote'] == 'New verified feature.'
    assert event['data']['change']['content_hash']
    assert event['data']['attempt_id'] == row['attempt_id'] and event['data']['status'] == status
    with get_db() as db:
        original = json.loads(db.execute('SELECT data FROM fieldtofit_object_check_attempts WHERE id=?', (row['attempt_id'],)).fetchone()['data'])
    assert original['changes'][0]['quote'] == 'New verified feature.'
    tomorrow = (date.fromisoformat(ws.today()) + timedelta(days=1)).isoformat()
    monkeypatch.setattr(ws, 'today', lambda:tomorrow)
    checks.start()
    fresh = checks.scan(tomorrow, ID)
    assert fresh['changes'] == []
    assert target(checks.review(tomorrow, ID, review(fresh, False)))['latest']['changes'] == []
    assert client.get('/api/v1/platform/watch').json == before_public
    assert len(target()['handling_history']) == 1


def test_whole_page_hash_and_quote_offset_changes_do_not_reopen(client, monkeypatch):
    row = finding(client, monkeypatch)
    old_id = row['latest']['changes'][0]['difference_id']
    decisions.handle(ws.today(), ID, payload(row))
    monkeypatch.setattr('backend.knowledge.sources.fetch', lambda url, **kw:(b'Unrelated new header.\nNew verified feature.\nOther edits.', url, 'text/plain'))
    fresh = checks.scan(ws.today(), ID)
    assert fresh['observations'][0]['content_hash'] != row['latest']['observations'][0]['content_hash']
    closed = target(checks.review(ws.today(), ID, review(fresh)))
    assert closed['latest']['changes'] == []
    assert closed['handled_changes'][0]['difference_id'] == old_id


@pytest.mark.parametrize('kind', ['quote', 'upstream_version', 'source_date', 'after'])
def test_new_reviewed_evidence_reenters_without_rewriting_old_decision(client, monkeypatch, kind):
    row = finding(client, monkeypatch)
    old_change = copy.deepcopy(row['latest']['changes'][0])
    decisions.handle(ws.today(), ID, payload(row, 'evidence_withdrawn'))
    monkeypatch.setattr('backend.knowledge.sources.fetch', lambda url, **kw:(b'New verified feature.\nCorrected official statement.', url, 'text/plain'))
    fresh = checks.scan(ws.today(), ID)
    assert fresh['changes'] == []  # fetching alone cannot claim a new semantic finding
    data = review(fresh)
    data['changes'][0][kind] = {'quote':'Corrected official statement.', 'upstream_version':'v2',
                               'source_date':ws.today(), 'after':'A different newly reviewed value.'}[kind]
    updated = target(checks.review(ws.today(), ID, data))
    assert len(updated['latest']['changes']) == 1
    assert updated['latest']['changes'][0]['difference_id'] != old_change['difference_id']
    assert updated['latest']['changes'][0]['new_evidence_after_handling'] == (kind != 'after')
    assert updated['handling_history'][0]['data']['change']['quote'] == old_change['quote']
    assert updated['handling_history'][0]['data']['status'] == 'evidence_withdrawn'


def test_manual_reopen_and_second_closure_have_append_only_versions(client, monkeypatch):
    row = finding(client, monkeypatch)
    closed = target(decisions.handle(ws.today(), ID, payload(row)))
    # The same finding remains recoverable even after a fresh scan omits it.
    checks.scan(ws.today(), ID)
    closed = target()
    event = closed['handled_changes'][0]
    data = payload(closed, 'pending', {**event['data']['change'], 'difference_id':event['difference_id'], 'handling_version':event['version']})
    data.update(reason='PRIVATE: recheck condition now satisfied.', recheck_condition='')
    reopened = target(decisions.handle(ws.today(), ID, data))
    assert reopened['latest']['changes'][0]['handling_version'] == 2
    assert reopened['handled_changes'] == []
    final = target(decisions.handle(ws.today(), ID, payload(reopened, 'evidence_withdrawn')))
    assert [e['version'] for e in final['handling_history']] == [1, 2, 3]
    assert [e['data']['status'] for e in final['handling_history']] == ['declined', 'pending', 'evidence_withdrawn']
    assert final['handling_history'][1]['data']['recheck_condition'] == final['handling_history'][0]['data']['recheck_condition']


@pytest.mark.parametrize('bad', [{'reason':''}, {'recheck_condition':''}, {'status':'deleted'}, {'difference_id':'invented'}, {'version':True}])
def test_invalid_or_invented_disposition_cannot_clear_evidence(client, monkeypatch, bad):
    row = finding(client, monkeypatch)
    response = call(client, '/object-checks/'+ID+'/handle', {**payload(row), **bad})
    assert response.status_code in (400, 409), response.json
    assert len(target()['latest']['changes']) == 1 and not target()['handling_history']


def test_stale_action_baseline_and_attempt_are_rejected(client, monkeypatch):
    row = finding(client, monkeypatch); data = payload(row)
    decisions.handle(ws.today(), ID, data)
    with pytest.raises(PlatformError) as conflict:decisions.handle(ws.today(), ID, data)
    assert conflict.value.code == 'handling_conflict'
    closed = target(); event = closed['handled_changes'][0]
    reopen = payload(closed, 'pending', {**event['data']['change'], 'difference_id':event['difference_id'], 'handling_version':1})
    checks.scan(ws.today(), ID)
    with pytest.raises(PlatformError) as conflict:decisions.handle(ws.today(), ID, reopen)
    assert conflict.value.code == 'attempt_conflict'
    reopen['attempt_id'] = target()['attempt_id']
    draft = ws.detail('watch', ID); draft['draft']['introduction'] = 'A changed official feature.'
    ws.save('watch', ID, draft); publish(client, 'watch', ID)
    with pytest.raises(PlatformError) as conflict:decisions.handle(ws.today(), ID, reopen)
    assert conflict.value.code == 'baseline_conflict'
    assert not target()['handled_changes'][0]['can_reopen']
    assert len(target()['handling_history']) == 1


def test_one_of_two_findings_closes_and_stale_proposal_cannot_continue_or_attach(client, monkeypatch):
    fetched = configured(client, monkeypatch)
    data = review(fetched)
    data['changes'].append({**data['changes'][0], 'field':'name', 'before':fetched['baseline']['name'], 'after':'New reviewed name'})
    row = target(checks.review(ws.today(), ID, data))
    proposal = call(client, '/object-checks/'+ID+'/proposal', {'day':ws.today()})
    assert proposal.status_code == 200, proposal.json
    topic = batches.detail('brief-'+ws.today())['items'][0]
    batches.decide(topic['id'], {'decision':'continue', 'version':topic['version']})
    approved = batches.detail('brief-'+ws.today())['items'][0]
    with pytest.raises(PlatformError):batches.attach(topic['id'], {'version':approved['version'], 'kind':'news', 'target_id':ID})
    with pytest.raises(PlatformError):batches.attach(topic['id'], {'version':approved['version'], 'kind':'watch', 'target_id':'CW-T02'})
    decisions.handle(ws.today(), ID, payload(row))
    assert len(target()['latest']['changes']) == 1
    with pytest.raises(PlatformError):batches.attach(topic['id'], {'version':approved['version'], 'kind':'watch', 'target_id':ID})
    with pytest.raises(PlatformError):batches.decide(topic['id'], {'decision':'continue', 'version':approved['version']})
    assert batches.detail('brief-'+ws.today())['items'][0]['decision'] == 'continue'  # retain the owner's historical decision
    current = call(client, '/object-checks/'+ID+'/proposal', {'day':ws.today()})
    assert current.status_code == 200, current.json
    new_topic = batches.detail('brief-'+ws.today())['items'][0]
    assert len(new_topic['proposal']['changes']) == 1
    batches.decide(new_topic['id'], {'decision':'continue', 'version':new_topic['version']})
    new_topic = batches.detail('brief-'+ws.today())['items'][0]
    assert batches.attach(new_topic['id'], {'version':new_topic['version'], 'kind':'watch', 'target_id':ID})['id'] == ID


def test_invalid_check_proposal_evidence_and_target_are_rejected_before_writing(client, monkeypatch):
    row = finding(client, monkeypatch)
    batch = batches.create({'day':ws.today()})
    proposal = {'title':'Dossier update', 'reason':'Verified official evidence', 'target_id':ID,
                'summary':decisions.PROPOSAL_SUMMARY, 'changes':row['latest']['changes'],
                'object_check':{'object_id':ID, 'baseline_hash':row['latest']['baseline_hash']}}
    for invalid in ([None], [{}], [{'field':'name', 'after':'New name', 'source_url':URL}],
                    [{**row['latest']['changes'][0], 'field':None}]):
        with pytest.raises(PlatformError):
            batches.propose(batch['id'], {'event_url':URL, 'fingerprint':'invalid', 'proposal':{**proposal, 'changes':invalid}})
    with pytest.raises(PlatformError):
        batches.propose(batch['id'], {'event_url':URL, 'fingerprint':'invalid', 'proposal':{**proposal, 'target_id':'CW-T02'}})
    assert batches.detail(batch['id'])['items'] == []


def test_actions_are_private_and_backup_upgrade_preserves_legacy_history(client, monkeypatch):
    row = finding(client, monkeypatch); data = payload(row)
    path = '/api/v1/admin/workspace/object-checks/'+ID+'/handle'
    assert client.post(path, json=data).status_code == 401
    assert client.post(path, json=data, headers={'Authorization':'Bearer reader'}).status_code == 401
    response = client.post(path, json=data, headers=ADMIN)
    assert response.status_code == 200 and response.headers['Cache-Control'] == 'private, no-store'
    backup = call(client, '/backup', method='get').json['tables']
    assert len(backup['fieldtofit_object_check_decisions']) == 1
    for url in ['/api/v1/platform/watch', '/api/v1/platform/news', '/api/v1/platform/content/'+ID+'/revisions']:
        assert 'PRIVATE' not in client.get(url).text
    rpc = client.post('/api/mcp/curated', headers=MCP, json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'curated_watch','arguments':{}}})
    assert 'PRIVATE' not in rpc.text
    stewardship.upgrade(); stewardship.upgrade()
    assert call(client, '/backup', method='get').json['tables'] == backup


def test_legacy_check_proposal_cannot_bypass_a_later_disposition(client, monkeypatch):
    row = finding(client, monkeypatch)
    batch = batches.create({'day':ws.today()})
    legacy = {'title':'Legacy dossier update', 'target_id':ID, 'reason':'Previously verified evidence',
              'summary':decisions.PROPOSAL_SUMMARY,
              'changes':[{k:v for k,v in c.items() if k not in ('difference_id','handling_version','new_evidence_after_handling')}
                         for c in row['latest']['changes']]}
    topic = batches.propose(batch['id'], {'event_url':URL, 'event_version':'legacy', 'fingerprint':'legacy', 'proposal':legacy})
    old = next(t for t in batches.detail(batch['id'])['items'] if t['id'] == topic['id'])
    batches.decide(old['id'], {'decision':'continue', 'version':old['version']})
    old = next(t for t in batches.detail(batch['id'])['items'] if t['id'] == topic['id'])
    decisions.handle(ws.today(), ID, payload(row))
    with pytest.raises(PlatformError):batches.attach(old['id'], {'version':old['version'], 'kind':'watch', 'target_id':ID})


def test_missing_incremental_table_has_explicit_upgrade_and_legacy_findings_recover(client, monkeypatch):
    row = finding(client, monkeypatch)
    with get_db() as db:db.execute('DROP TABLE fieldtofit_object_check_decisions')
    assert checks.overview()['handling_available'] is False
    response = call(client, '/object-checks/'+ID+'/handle', payload(row))
    assert response.status_code == 503 and response.json['code'] == 'upgrade_required'
    stewardship.upgrade()
    row = target(); assert row['latest']['changes'][0]['handling_version'] == 0
    decisions.handle(ws.today(), ID, payload(row))
    assert target()['latest']['changes'] == []


@pytest.mark.parametrize('race', [False, True])
def test_remote_atomic_disposition_detects_concurrent_attempt_change(client, monkeypatch, race):
    from backend.db import TursoConnection, TursoCursor
    from backend.knowledge import workspace_transactions as tx
    row = finding(client, monkeypatch)
    class RemoteSQL(TursoConnection):
        def __init__(self, db):self.db = db
        def execute(self, sql, params=()):return TursoCursor(self.db.execute(sql, params).fetchall(), 0, None)
        def atomic_statements(self, statements):
            if race:
                self.db.execute("UPDATE fieldtofit_object_check_attempts SET data=json_set(data,'$.reason','Concurrent reviewer') WHERE id=?", (row['attempt_id'],))
                self.db.commit()
            self.db.execute('BEGIN IMMEDIATE')
            try:
                result=[]
                for sql, args in statements:
                    cursor=self.db.execute(sql, args);result.append(TursoCursor(cursor.fetchall(), cursor.rowcount, None))
                self.db.commit();return result
            except Exception:self.db.rollback();raise
    @contextmanager
    def remote():
        with get_db() as db:yield RemoteSQL(db)
    monkeypatch.setattr(tx, 'get_db', remote)
    if race:
        with pytest.raises(PlatformError) as conflict:decisions.handle(ws.today(), ID, payload(row))
        assert conflict.value.code == 'workspace_conflict'
        assert len(target()['latest']['changes']) == 1 and target()['handling_history'] == []
    else:
        decisions.handle(ws.today(), ID, payload(row))
        assert target()['latest']['changes'] == []
