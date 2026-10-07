"""Local AI handoff for private names: exact mentions, source text, then review."""
import argparse
import json
import os
from pathlib import Path
import requests
from dotenv import dotenv_values


def run(base,env_file,output,extractions=None,reviews=None):
    headers={'X-Admin-Password':dotenv_values(env_file)['ADMIN_PASSWORD']}
    session=requests.Session();session.trust_env=False
    def call(path,data=None):
        r=session.request('POST' if data is not None else 'GET',base.rstrip('/')+'/api/v1/admin/workspace/names'+path,headers=headers,json=data,timeout=90,allow_redirects=False)
        if r.status_code!=200:raise RuntimeError('Name API HTTP '+str(r.status_code)+'; no automatic retry or publication')
        return r.json()
    # Extract before freezing the ten daily groups. Repeating preparation cannot
    # reset the daily quota; changed evidence waits for the next day.
    if extractions:
        items=json.loads(Path(extractions).read_text())
        if not isinstance(items,list) or not 1<=len(items)<=500:raise ValueError('Expected 1–500 extracted candidates')
        for start in range(0,len(items),50):call('/extract',{'items':items[start:start+50]})
    # Plain export lets AI extract first; freeze the daily queue only once
    # extracted names or actual reviews are ready.
    if extractions or reviews:call('/prepare',{})
    if reviews:
        for record in json.loads(Path(reviews).read_text()):
            call('/'+record['id']+'/review',record)
    result=call('/handoff')
    path=Path(output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,ensure_ascii=False,indent=2));path.chmod(0o600)
    return {'day':result['day'],'groups':len(result['groups']),'candidates':len(result['candidates']),'candidate_backlog':result['candidate_backlog'],'scope':'Private name leads and actual local investigations; no draft or public identity writes'}


if __name__=='__main__':
    os.umask(0o077)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',default='https://fieldtofit.top');parser.add_argument('--env-file',default='.env');parser.add_argument('--output',required=True)
    parser.add_argument('--extractions',help='JSON exact source mentions: ref, fingerprint, mentions(name, field, start, end, quote, version)')
    parser.add_argument('--reviews',help='JSON actual source-backed investigations: id, fingerprint, outcome, reason, searches, materials, identities')
    a=parser.parse_args();print(json.dumps(run(a.base,a.env_file,a.output,a.extractions,a.reviews),ensure_ascii=False))
