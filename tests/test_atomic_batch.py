"""Execute Hrana batch conditions against SQLite to verify rollback semantics."""
import sqlite3
import pytest
from backend.db import TursoConnection


@pytest.fixture
def remote(monkeypatch):
    db=sqlite3.connect(':memory:',isolation_level=None)
    db.execute('CREATE TABLE entries (id INTEGER PRIMARY KEY, value TEXT)')
    def post(self,payload):
        results=[];errors=[]
        def ok(cond):
            if cond['type']=='ok':return results[cond['step']] is not None
            return not ok(cond['cond'])
        for step in payload['requests'][0]['batch']['steps']:
            if step.get('condition') and not ok(step['condition']):
                results.append(None);errors.append(None);continue
            try:
                values=[None if a['type']=='null' else int(a['value']) if a['type']=='integer' else a['value'] for a in step['stmt'].get('args',[])]
                cur=db.execute(step['stmt']['sql'],values)
                rows=cur.fetchall()
                results.append({'cols':[{'name':c[0]} for c in cur.description or []],
                    'rows':[[{'type':'integer','value':str(v)} if isinstance(v,int) else {'type':'text','value':v} for v in row] for row in rows]})
                errors.append(None)
            except sqlite3.Error as error:
                results.append(None);errors.append({'message':str(error)})
        return {'results':[{'type':'ok','response':{'result':{'step_results':results,'step_errors':errors}}}]}
    monkeypatch.setattr(TursoConnection,'_post',post)
    return TursoConnection(),db


def test_atomic_batch_rolls_back_every_write_on_middle_failure(remote):
    conn,db=remote
    with pytest.raises(RuntimeError):
        conn.atomic_statements([('INSERT INTO entries VALUES (?,?)',(1,'first')),
                                ('INSERT INTO entries VALUES (?,?)',(1,'duplicate')),
                                ('INSERT INTO entries VALUES (?,?)',(2,'must not execute'))])
    assert db.execute('SELECT count(*) FROM entries').fetchone()[0]==0
    assert not db.in_transaction


def test_atomic_batch_commit_and_read_restore(remote):
    conn,db=remote
    conn.atomic_statements([('INSERT INTO entries VALUES (?,?)',(1,'value'))])
    rows=conn.atomic_statements([('SELECT id,value FROM entries',())],read_only=True)[0].fetchall()
    assert rows==[(1,'value')]
    assert not db.in_transaction
