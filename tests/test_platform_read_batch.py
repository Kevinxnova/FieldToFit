"""Remote batches preserve public visibility and avoid per-object roundtrips."""
import pytest
from test_knowledge import client
from test_platform_updates import selected, withdraw
from backend.db import get_db, TursoConnection
from backend.knowledge import platform as p
from backend.knowledge.platform_read_batch import prepare_publications


class RemoteReads(TursoConnection):
    def __init__(self, db):
        self.local = db
        self.batches = 0
        self.fallbacks = 0

    def atomic_statements(self, statements, read_only=False):
        assert read_only
        self.batches += 1
        return [self.local.execute(sql, params) for sql, params in statements]

    def execute(self, sql, params=()):
        self.fallbacks += 1
        return self.local.execute(sql, params)


def test_batch_matches_public_results_and_next_request_observes_withdrawal(client):
    pubs = [selected(str(i))[0] for i in range(8)]
    refs = [{'id': x['object']['id'], 'revision': x['revision']} for x in pubs]
    with get_db() as db:
        remote = RemoteReads(db)
        prepared = prepare_publications(remote, refs)
        actual = [p._get_object(prepared, r['id'], r['revision']) for r in refs]
        assert actual == pubs
        assert remote.batches <= 3 and remote.fallbacks == 0
    withdraw(refs[0]['id'])
    with get_db() as db:
        fresh = prepare_publications(RemoteReads(db), refs)
        with pytest.raises(p.PlatformError) as error:
            p._get_object(fresh, refs[0]['id'], refs[0]['revision'])
        assert error.value.status in (404, 410)
        assert p._get_object(fresh, refs[1]['id'], refs[1]['revision']) == pubs[1]
