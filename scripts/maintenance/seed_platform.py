"""Copy curated content into an empty platform namespace, preserving public IDs.

Never replaces existing platform records. Existing legacy tables are untouched.
Requires an explicit source SQLite and destination environment file. Back up the
destination first with remote_snapshot.py. This is an initial seed, not a sync.
"""
import argparse
import json
import sqlite3
from pathlib import Path


def seed(source_path):
    from backend.db import get_db
    source_path=Path(source_path).resolve(strict=True)
    with sqlite3.connect(source_path.as_uri()+'?mode=ro',uri=True) as source:
        source.row_factory=sqlite3.Row
        ids=[r[0] for r in source.execute("SELECT record_id FROM knowledge_selections WHERE state='published'")]
        if not ids:
            raise ValueError('Source has no published objects')
        marks=','.join('?' for _ in ids)
        tables={}
        for name,column in [('knowledge_records','id'),('knowledge_evidence','record_id'),('knowledge_changes','record_id'),
                            ('knowledge_platform_profiles','record_id'),('knowledge_selections','record_id'),('knowledge_publications','record_id')]:
            tables[name]=[dict(r) for r in source.execute(f'SELECT * FROM {name} WHERE {column} IN ({marks})',ids)]
        # Historical snapshots can refer to previous source identities.
        for name in ['knowledge_sources','knowledge_editions','knowledge_edition_publications',
                     'knowledge_platform_intake','knowledge_platform_material_checks']:
            tables[name]=[dict(r) for r in source.execute('SELECT * FROM '+name)]
    schema=(Path(__file__).resolve().parents[2]/'backend/knowledge/schema.sql').read_text()
    with get_db() as db:
        statements=[]
        for statement in schema.split(';'):
            if statement.strip(): statements.append((statement,()))
        statements.append(('CREATE TEMP TABLE metis_seed_guard (n INTEGER CHECK(n=0))',()))
        for name in tables:
            statements.append(('INSERT INTO metis_seed_guard SELECT count(*) FROM '+name,()))
        order=['knowledge_sources','knowledge_records','knowledge_evidence','knowledge_changes',
               'knowledge_platform_profiles','knowledge_selections','knowledge_publications',
               'knowledge_editions','knowledge_edition_publications','knowledge_platform_intake','knowledge_platform_material_checks']
        for name in order:
            rows=tables[name]
            if not rows: continue
            columns=list(rows[0])
            sql='INSERT INTO '+name+' ('+','.join(columns)+') VALUES('+','.join('?' for _ in columns)+')'
            statements.extend((sql,[r[k] for k in columns]) for r in rows)
        if hasattr(db,'atomic_statements'): db.atomic_statements(statements)
        else:
            db.execute('BEGIN IMMEDIATE')
            for stmt,params in statements: db.execute(stmt,params)
        for name,rows in tables.items():
            if db.execute('SELECT count(*) FROM '+name).fetchone()[0]!=len(rows):
                raise ValueError('Seed verification failed: '+name)
    return {'published_objects':len(ids),'counts':{k:len(v) for k,v in tables.items()},'legacy_tables_replaced':False}


if __name__=='__main__':
    from dotenv import load_dotenv
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',required=True)
    p.add_argument('--env-file',required=True)
    a=p.parse_args()
    load_dotenv(a.env_file,override=True)
    print(json.dumps(seed(a.source),ensure_ascii=False,indent=2))
