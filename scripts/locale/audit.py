"""Audit every public English collection/detail against an isolated SQLite snapshot."""
import argparse
import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))

class Visible(HTMLParser):
    def __init__(self):super().__init__();self.stack=[];self.chinese=[]
    def handle_starttag(self,tag,attrs):
        original=(self.stack[-1][1] if self.stack else False) or tag in ('script','style') or any(k=='data-original-language' or k=='lang' and (v or '').startswith('zh') for k,v in attrs)
        if tag not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):self.stack.append((tag,original))
        if not original:
            for k,v in attrs:
                if k in ('alt','title','aria-label','placeholder','content') and v and re.search('[\u3400-\u9fff]',v):self.chinese.append(v)
    def handle_endtag(self,tag):
        if self.stack and self.stack[-1][0]==tag:self.stack.pop()
    def handle_data(self,value):
        if not (self.stack and self.stack[-1][1]) and re.search('[\u3400-\u9fff]',value):self.chinese.append(value)

def main():
    p=argparse.ArgumentParser();p.add_argument('--snapshot',required=True);p.add_argument('--output',required=True);args=p.parse_args()
    os.environ.update(PYTHON_DOTENV_DISABLED='1',FIELDTOFIT_AUTO_INIT_DB='0')
    import backend.config as config
    import backend.db as database
    config.DB_PATH=Path(args.snapshot);database.TURSO_URL='';database.TURSO_TOKEN=''
    from backend.api.main import app
    from backend.knowledge import locale
    app.config['TESTING']=True;client=app.test_client();errors=[];checks=[];counts={}
    def get(path):
        r=client.get(path,base_url='https://fieldtofit.top');checks.append({'path':path,'status':r.status_code})
        if r.status_code!=200:errors.append({'path':path,'error':r.get_json() if r.is_json else r.text[:180]})
        elif r.is_json:
            remaining=locale.strings(r.get_json())
            if remaining:errors.append({'path':path,'chinese':sorted(remaining)[:15]})
        else:
            parser=Visible();parser.feed(r.text)
            if parser.chinese:errors.append({'path':path,'chinese':parser.chinese[:15]})
            if '/en/' in path and ('<html lang="en"' not in r.text or 'hreflang="en"' not in r.text):errors.append({'path':path,'error':'English lang/hreflang missing'})
        return r
    for k in ('news','watch'):
        zh=client.get('/api/v1/platform/'+k).json;en=get('/api/v1/platform/'+k+'?lang=en').get_json();counts[k]=zh['total']
        if en and [i['id'] for i in zh['items']]!=[i['id'] for i in en.get('items',[])]:errors.append({'path':k,'error':'English item IDs differ'})
        if en and zh['revision']!=en.get('revision'):errors.append({'path':k,'error':'English revision differs'})
        for i in zh['items']:
            get('/en/'+k+'/'+i['id'])
            get('/api/v1/platform/content/'+i['id']+'/status?lang=en')
            get('/api/v1/platform/content/'+i['id']+'/corrections?lang=en')
            if k=='watch':
                history=get('/api/v1/platform/content/'+i['id']+'/revisions?lang=en').get_json()
                if history and history.get('total',0)>1:get('/api/v1/platform/content/'+i['id']+'/compare?lang=en')
    maps=client.get('/api/v1/platform/maps').json;counts['maps']=maps['total']
    for m in maps['items']:
        get('/en'+m['path']);get('/api/v1/platform/maps?slug='+m['slug']+'&lang=en')
        history=get('/api/v1/platform/maps/'+m['slug']+'/history?lang=en').get_json()
        if history and history.get('total',0)>1:get('/api/v1/platform/maps/'+m['slug']+'/compare?lang=en')
    from backend.db import get_db
    from backend.knowledge import platform
    with get_db() as db:
        rows=db.execute("SELECT p.record_id,p.seq FROM knowledge_publications p JOIN knowledge_records r ON r.id=p.record_id AND r.status='published' JOIN knowledge_selections s ON s.record_id=p.record_id AND s.state!='withdrawn' WHERE p.state='published'").fetchall()
        readable=[]
        for row in rows:
            try:platform._get_object(db,row['record_id'],row['seq']);readable.append(dict(row))
            except platform.PlatformError:continue
    counts['readable_library_revisions']=len(readable)
    for row in readable:
        get('/api/v1/platform/objects/'+row['record_id']+'?revision='+str(row['seq'])+'&lang=en')
        get('/api/v1/platform/objects/'+row['record_id']+'/export?revision='+str(row['seq'])+'&lang=en')
    from backend.seo import PAGES
    for path in [*PAGES,'/maps']:get('/en'+path)
    for path in ('/api/v1/platform/model-landscape?lang=en','/api/v1/platform/source-catalog?lang=en','/api/v1/platform/watch/summary?lang=en','/api/v1/platform/content-changes?lang=en','/api/v1/platform/sources?lang=en','/api/v1/platform/changes?lang=en'):
        # The exact routes are verified below, without treating absent paths as coverage.
        if any(rule.rule==path.split('?')[0] for rule in app.url_map.iter_rules()):get(path)
    out={'counts':counts,'checks':checks,'errors':errors};Path(args.output).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'counts':counts,'checks':len(checks),'errors':len(errors)}))
    if errors:sys.exit(1)
if __name__=='__main__':main()
