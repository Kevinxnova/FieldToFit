"""Reproduce the missed Jev lead without production writes or fabricated releases."""
import json
from datetime import datetime,timedelta,timezone
import pytest
from test_knowledge import client,ADMIN
from backend.db import get_db
from backend.db.queries import insert_tool
from backend.knowledge import candidate_priority as rank,content_workspace as ws,editorial_batches as b,briefing_review as review,store
from backend.knowledge.platform import PlatformError

URL='https://typesafe.ai/blog/introducing-system-one-models-and-jev'

def jev(points=642,comments=207):
    ident=insert_tool(URL,'jev-test','Introducing System One Models and Jev','Typed decisions for software','hackernews','https://news.ycombinator.com/',{'points':points,'comments':comments})
    with get_db() as db:
        if ident is None:ident=db.execute("SELECT id FROM tools WHERE dedup_key='jev-test'").fetchone()[0]
        db.execute('UPDATE tools SET first_seen=? WHERE id=?',((datetime.now(timezone.utc)-timedelta(days=5)).isoformat(),ident))
    return 'tool:'+str(ident)

def record(batch,c,outcome='investigate',reason='追查官方文档和限制；在日报列出待核验线索',**extra):
    return review.review(batch,{'ref':c['ref'],'evidence_fingerprint':c['evidence_fingerprint'],'outcome':outcome,'reason':reason,**extra})


def test_changed_old_candidate_refreshes_without_manual_override_loss(client):
    ref=jev();rank.refresh();rank.override({'ref':ref,'group':'follow','reason':'人工保留分组'})
    jev(1784,472);result=rank.refresh();assert result['assessed']==1
    item=ws.inbox(q=ref)['items'][0]
    assert item['priority']['group']=='follow' and item['priority']['automatic_group']=='verify'
    assert item['priority']['investigation']['urgent']
    assert next(s for s in item['priority']['signals'] if s['kind']=='points')['value']==1784
    assert rank.refresh()['assessed']==0
    assert ws.inbox(group='urgent')['items'][0]['ref']==ref


def test_legacy_observations_preserve_latest_lower_value_without_faking_growth(client):
    ref=jev();jev(500,190);rank.refresh()
    item=ws.inbox(q=ref)['items'][0]
    points=next(s for s in item['priority']['signals'] if s['kind']=='points')
    assert points['value']==500 and points['observed_at']
    assert item['metrics']['points']==500
    assert not any(s['kind']=='stars_change' for s in item['priority']['signals'])
    with get_db() as db:assert db.execute('SELECT COUNT(*) FROM fieldtofit_attention_observations').fetchone()[0]==1


def test_unassessed_hot_lead_is_visible_and_blocks_prepared_not_publication(client):
    ref=jev(1784,472);batch=b.create({});before=[client.get('/api/v1/platform/'+k).json for k in ('news','watch')]
    pre=review.preflight(batch['id']);assert pre['unreviewed']==1 and not pre['ready'];c=pre['items'][0];assert c['ref']==ref
    with pytest.raises(PlatformError) as e:b.delivery(batch['id'],{'version':batch['version'],'state':'prepared'})
    assert e.value.code=='selection_review_required'
    record(batch['id'],c)
    assert review.preflight(batch['id'])['ready']
    assert b.delivery(batch['id'],{'version':batch['version'],'state':'prepared'})['delivery_state']=='prepared'
    assert [client.get('/api/v1/platform/'+k).json for k in ('news','watch')]==before
    assert b.detail(batch['id'])['items']==[]
    assert ws.inbox(q=ref)['items'][0]['status']=='pending'


def test_reviews_have_real_reasons_and_sources_and_stale_evidence_rejected(client):
    jev();batch=b.create({})['id'];c=review.preflight(batch)['items'][0]
    with pytest.raises(PlatformError):record(batch,c,reason='')
    with pytest.raises(PlatformError):record(batch,c,outcome='recommend')
    record(batch,c,outcome='recommend',sources=[URL])
    assert record(batch,c,outcome='recommend',sources=[URL])['unchanged']
    jev(1784,472)
    assert review.preflight(batch)['unreviewed']==1
    with pytest.raises(PlatformError):record(batch,c)
    c=review.preflight(batch)['items'][0];record(batch,c,outcome='not_recommended',reason='已报道同一版本，需先核对本站条目')
    assert review.preflight(batch)['ready']


def test_no_time_only_observation_resets_selection_review(client):
    jev();batch=b.create({})['id'];c=review.preflight(batch)['items'][0];record(batch,c)
    jev();assert review.preflight(batch)['ready']


@pytest.mark.parametrize('action',['ignored','deferred'])
def test_user_inbox_decision_is_not_resurrected(client,action):
    ws.migrate();ref=jev();ws.select({'ref':ref,'action':action});batch=b.create({})['id']
    assert review.preflight(batch)['total']==0
    assert rank.refresh()['assessed']==0


def test_unknown_date_and_cumulative_stars_are_not_growth_or_quality(client):
    ref=jev();
    with get_db() as db:db.execute('UPDATE tools SET metrics=? WHERE id=?',(json.dumps({'stars':100000}),ref.split(':')[1]));db.execute('DELETE FROM fieldtofit_attention_observations')
    rank.refresh();item=ws.inbox()['items'][0]
    assert item['priority']['group']=='verify' and not item['priority']['investigation']['urgent']


def test_selection_api_auth_and_pagination_include_older_hot_items(client):
    ref=jev();batch=b.create({})['id']
    for i in range(33):client.post('/api/v1/admin/workspace/inbox',headers=ADMIN,json={'title':'New '+str(i),'url':'https://example.org/'+str(i),'summary':'Recent lead'})
    path='/api/v1/admin/workspace/batches/'+batch+'/selection'
    assert client.get(path).status_code==401
    page=client.get(path,headers=ADMIN).json;assert page['total']==34 and page['items'][0]['ref']==ref and page['next_offset']==30
    assert len(client.get(path+'?offset=30',headers=ADMIN).json['items'])==4


def test_refresh_rotates_backlog_and_preserves_changed_priority(client):
    ref=jev();rank.refresh()
    for i in range(6):insert_tool('https://example.org/'+str(i),'other'+str(i),'Other','Small','hackernews','',{'points':1})
    jev(1784,472);first=rank.refresh(limit=4);assert first['assessed']==4 and first['remaining']==3
    assert rank.refresh(limit=4)['remaining']==0
    assert rank.refresh(limit=4)['assessed']==0


def test_daily_review_capacity_is_finite_and_backlog_is_disclosed(client):
    for i in range(24):insert_tool('https://example.org/hot'+str(i),'hot'+str(i),'Hot '+str(i),'Lead','hackernews','',{'points':200+i})
    batch=b.create({})['id'];first=review.preflight(batch);assert first['required']==20 and first['backlog']==4
    records=[{'ref':c['ref'],'evidence_fingerprint':c['evidence_fingerprint'],'outcome':'investigate','reason':'需核对原始来源，日报说明缺口','sources':[]} for c in first['items'] if c['required']]
    review.review(batch,{'items':records})
    after=review.preflight(batch);assert after['ready'] and after['backlog']==4
    # Prior-day editorial work is reused; it is not an owner decision.
    with get_db() as db:db.execute("UPDATE fieldtofit_editorial_events SET topic_id='brief-previous' WHERE action='selection_review'")
    next_day=review.preflight(batch);assert next_day['unreviewed']==4 and next_day['required']==4


def test_new_material_invalidates_review_even_when_attention_is_unchanged(client):
    from test_daily_discovery import source,item
    from backend.knowledge import discovery
    discovery.capture(source(),item(metrics={'points':700}))
    batch=b.create({})['id'];c=review.preflight(batch)['items'][0];record(batch,c)
    changed=item(metrics={'points':700});changed['materials']=[discovery.material(changed['url'],'Changed original documentation '*20)]
    discovery.capture(source(),changed)
    assert review.preflight(batch)['unreviewed']==1
    with pytest.raises(PlatformError):record(batch,c)


def test_bulk_review_rejects_all_on_one_conflict(client):
    jev();batch=b.create({})['id'];c=review.preflight(batch)['items'][0]
    good={'ref':c['ref'],'evidence_fingerprint':c['evidence_fingerprint'],'outcome':'investigate','reason':'Original check pending','sources':[]}
    with pytest.raises(PlatformError):review.review(batch,{'items':[good,{**good,'ref':'tool:missing'}]})
    assert review.preflight(batch)['unreviewed']==1


def test_actual_delivery_receipt_survives_a_new_lead_after_preparation(client):
    batch=b.create({});batch=b.delivery(batch['id'],{'version':batch['version'],'state':'prepared'})
    jev();result=b.delivery(batch['id'],{'version':batch['version'],'state':'delivered','confirmed':True,'receipt':'Actual completed message after preparation'})
    assert result['delivery_state']=='delivered'


def test_urgent_inbox_uses_discussion_strength_not_just_discovery_date(client):
    ref=jev(1784,472)
    insert_tool('https://example.org/new','newer','Newer lead','A later discovery','hackernews','',{'points':101,'comments':51})
    rank.refresh()
    assert ws.inbox(group='urgent')['items'][0]['ref']==ref
    assert ws.inbox()['items'][0]['ref']==ref
    assert ws.inbox(order='date')['items'][0]['ref']!=ref


def test_remote_reassessment_commits_as_one_fresh_atomic_batch(client,monkeypatch):
    from contextlib import contextmanager
    from backend.db import TursoConnection
    ref=jev();calls=[]
    class Remote(TursoConnection):
        def __init__(self,db):self.db=db
        def execute(self,sql,params=()):return self.db.execute(sql,params)
        def execute_batch(self,statements):raise RuntimeError('Batch writes require an explicit transaction')
        def atomic_statements(self,statements,read_only=False):
            calls.append(len(statements))
            for sql,params in statements:self.db.execute(sql,params)
    @contextmanager
    def remote_db():
        with get_db() as db:yield Remote(db)
    monkeypatch.setattr(rank,'get_db',remote_db)
    assert rank.refresh()['assessed']==1
    assert calls==[1]
    assert ws.inbox(group='urgent')['items'][0]['ref']==ref
