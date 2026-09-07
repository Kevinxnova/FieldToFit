"""Run only maintainer-reviewed check scripts; never execute source text or user commands."""
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

from backend.db import get_db
from backend.knowledge import store

CHECK_ROOT=Path(__file__).resolve().parents[2]/'examples'/'validation'


def available_checks():
    manifest=CHECK_ROOT/'manifest.json'
    if not manifest.exists(): return []
    result=json.loads(manifest.read_text())
    return [{k:c[k] for k in ('id','title','persona','script','expected','limitations','source_url')} for c in result]


def run_check(check_id,record_id):
    check=next((c for c in available_checks() if c['id']==check_id),None)
    record=store.get_record(record_id)
    if not check or not record: raise ValueError('Reviewed check or published record not found')
    if store.canonical_url(record['canonical_url'])!=store.canonical_url(check['source_url']):
        raise ValueError('The check must be attached to its declared source resource')
    script=(CHECK_ROOT/check['script']).resolve()
    if script.parent!=CHECK_ROOT or script.suffix!='.py': raise ValueError('Check path is outside the reviewed directory')
    # Controlled interpreter, working directory, timeout and output; not a general OS/network sandbox.
    env={'PATH':str(Path(sys.executable).parent)+':/usr/bin:/bin','PYTHONIOENCODING':'utf-8','LANG':'en_US.UTF-8'}
    with tempfile.TemporaryDirectory(prefix='metis-check-') as folder:
        start=time.monotonic()
        observed_version=''
        try:
            result=subprocess.run([sys.executable,'-I',str(script),check_id],cwd=folder,env=env,capture_output=True,text=True,timeout=45)
            output=(result.stdout+'\n'+result.stderr)[-45000:]
            state='passed' if result.returncode==0 else 'failed'
            if state=='passed':
                try:
                    artifact=json.loads(result.stdout)
                    observed_version=artifact.get('version') or artifact.get('pypdf_version','')
                except (ValueError,AttributeError):
                    state='failed';output+='\nCheck did not return a structured runtime version.'
                if not observed_version or (record['version'] and observed_version!=record['version']):
                    state='failed';output+='\nInstalled runtime version does not match the indexed resource version.'
        except subprocess.TimeoutExpired:
            output='Check exceeded 45 seconds';state='failed'
        environment=f'Python {platform.python_version()} · {platform.system()} {platform.machine()} · temporary working directory · timeout 45s'
        vid=store.stable_id(check_id,record_id,store.now())
        with get_db() as db:
            db.execute('INSERT INTO knowledge_verifications VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                       (vid,record_id,check['title'],'Reviewed example execution',observed_version,environment,
                        f"Run {check['script']} {check_id}; source {check['source_url']}",check['expected'],state,output,
                        check['limitations']+'; not an OS/network-isolated sandbox and not a full-project certification',store.now()))
    return {'id':vid,'check_id':check_id,'result':state,'output':output,'seconds':round(time.monotonic()-start,3)}


def run_due_checks():
    result=[]
    for check in available_checks():
        with get_db() as db:
            record=db.execute("SELECT id,version FROM knowledge_records WHERE canonical_url=? AND status='published'",(store.canonical_url(check['source_url']),)).fetchone()
            if not record: continue
            last=db.execute('SELECT * FROM knowledge_verifications WHERE record_id=? AND title=? ORDER BY checked_at DESC LIMIT 1',(record['id'],check['title'])).fetchone()
            changed=db.execute("SELECT id FROM knowledge_records WHERE id=? AND (? IS NULL OR updated_at>?)",(record['id'],last['checked_at'] if last else None,last['checked_at'] if last else None)).fetchone()
        if changed or not last or last['version']!=record['version']:
            result.append(run_check(check['id'],record['id']))
    return result
