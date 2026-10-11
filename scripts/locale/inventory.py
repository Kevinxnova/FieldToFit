"""Build a public-only translation inventory from an isolated editorial snapshot.

Never exports draft bodies, private reasons, credentials or original source text.
"""
import argparse
import ast
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
HAN = re.compile(r'[\u3400-\u9fff]')
ORIGINAL = {'body', 'quote', 'excerpt', 'notice', 'text_en', 'translation_zh', 'context_en', 'context_zh'}

def collect(value, output, path='', key=''):
    if key in ORIGINAL: return
    if isinstance(value, str) and HAN.search(value): output.setdefault(value, []).append(path)
    elif isinstance(value, list):
        for i, entry in enumerate(value): collect(entry, output, f'{path}/{i}', key)
    elif isinstance(value, dict):
        for name, entry in value.items(): collect(entry, output, f'{path}/{name}', name)

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--snapshot', required=True); parser.add_argument('--output', required=True)
    args = parser.parse_args()
    os.environ['PYTHON_DOTENV_DISABLED']='1'
    import backend.config as config
    import backend.db as database
    config.DB_PATH=Path(args.snapshot); database.TURSO_URL=''; database.TURSO_TOKEN=''
    from backend.knowledge import content_workspace as ws, content_revisions, technical_maps, source_catalog
    output = {}; approvals = {}; public = {}
    with database.get_db() as db:
        for kind in ('news','watch','charts'):
            row=db.execute('SELECT published_json FROM fieldtofit_content_sets WHERE kind=?',(kind,)).fetchone()
            raw=json.loads(row['published_json']) if row else ws.seeds()[kind]
            public[kind]=ws.render(kind, raw); collect(public[kind], output, kind)
            entries=[{'id':'snapshot',**raw}] if kind=='charts' else raw['items']
            for entry in entries:
                if kind!='charts' and entry['state']!='published': continue
                # Baseline approvals contain hashes only, never private fields.
                from backend.knowledge.locale import source_hash
                approvals.setdefault(kind+':'+entry['id'], []).append(source_hash(kind,entry))
        for entry in public['watch']['items']:
            _, revisions=content_revisions.snapshots(entry['id'],db)
            for revision in revisions: collect(revision['object'],output,'history/'+entry['id'])
            rows=db.execute("SELECT snapshot FROM fieldtofit_content_history WHERE kind='watch' AND item_id=? AND action IN ('import','publish') AND seq>COALESCE((SELECT MAX(seq) FROM fieldtofit_content_history WHERE kind='watch' AND item_id=? AND action='withdraw'),0)",(entry['id'],entry['id'])).fetchall()
            for row in rows:
                item=json.loads(row['snapshot'])
                if item.get('state')=='published':approvals.setdefault('watch:'+entry['id'],[]).append(source_hash('watch',item))
        # Only currently accessible map revisions, after the latest withdrawal.
        for entry in public['news']['items']:
            if entry.get('technical_map'):
                for revision in technical_maps.history(entry['technical_map']['slug'])['items']: collect(revision,output,'map-history/'+entry['id'])
                rows=db.execute("SELECT snapshot FROM fieldtofit_content_history WHERE kind='news' AND item_id=? AND action IN ('import','publish') AND seq>COALESCE((SELECT MAX(seq) FROM fieldtofit_content_history WHERE kind='news' AND item_id=? AND action='withdraw'),0)",(entry['id'],entry['id'])).fetchall()
                for row in rows:
                    item=json.loads(row['snapshot'])
                    if item.get('state')=='published' and item.get('technical_map'):approvals.setdefault('news:'+entry['id'],[]).append(source_hash('news',item))
        # Legacy stored-source publications remain readable under their original permissions.
        from backend.knowledge import platform
        rows=db.execute("""SELECT p.record_id,p.seq FROM knowledge_publications p
            JOIN knowledge_records r ON r.id=p.record_id AND r.status='published'
            JOIN knowledge_selections s ON s.record_id=p.record_id AND s.state!='withdrawn'
            WHERE p.state='published' AND p.seq>COALESCE((SELECT MAX(w.seq) FROM knowledge_publications w
                WHERE w.record_id=p.record_id AND w.state='withdrawn'),0)""").fetchall()
        public['library']=[]
        for row in rows:
            try:value=platform._get_object(db,row['record_id'],row['seq'])
            except ValueError:continue
            public['library'].append(value);collect(value,output,'library/'+row['record_id'])
            approvals.setdefault('library:'+row['record_id'],[]).append(source_hash('library',value['object']))
    collect(source_catalog.registry(), output, 'sources')
    ui=json.loads((ROOT/'output/operations/req23-english/ui-inventory.json').read_text())
    for text, files in ui['strings'].items(): output.setdefault(text,[]).extend(files)
    for file in (ROOT/'backend').rglob('*.py'):
        try: tree=ast.parse(file.read_text())
        except (SyntaxError,UnicodeError): continue
        for node in ast.walk(tree):
            if isinstance(node,ast.Constant) and isinstance(node.value,str) and HAN.search(node.value) and len(node.value)<5000: output.setdefault(node.value,[]).append(str(file.relative_to(ROOT)))
    for folder in ('backend/seo/templates','frontend/public'):
        for file in (ROOT/folder).rglob('*'):
            if file.suffix not in ('.html','.svg'): continue
            # HTML strings around template expressions are individually authored text.
            for value in re.findall(r'>([^<>]+)<|(?:alt|title|aria-label)=["\']([^"\']+)',file.read_text()):
                text=next((s for s in value if s),'').strip()
                for fragment in re.split(r'\{[{%].*?[%}]\}',text):
                    fragment=fragment.strip()
                    if HAN.search(fragment): output.setdefault(fragment,[]).append(str(file.relative_to(ROOT)))
    target=Path(args.output); target.mkdir(parents=True,exist_ok=True)
    for name,value in [('inventory',output),('baseline',approvals),('public',public),('existing-ui',ui['pairs'])]:
        (target/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'strings':len(output),'characters':sum(map(len,output)),'objects':len(approvals)},ensure_ascii=False))

if __name__=='__main__': main()
