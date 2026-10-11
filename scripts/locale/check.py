"""Check catalog coverage and literal factual tokens against the public inventory."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

HAN=re.compile(r'[\u3400-\u9fff]')
def numbers(value):
    value=re.sub(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日',r'\1-\2-\3 ',value)
    value=re.sub(r'(\d{1,2})\s*月\s*(\d{1,2})\s*日',r'\1/\2 ',value)
    value=re.sub(r'(\d+(?:\.\d+)?)\s*(万|亿)',lambda m:str(float(m[1])*(10000 if m[2]=='万' else 100000000)),value)
    value=re.sub(r'(\d+(?:\.\d+)?)\s*(million|billion)',lambda m:str(float(m[1])*(1000000 if m[2].lower()=='million' else 1000000000)),value,flags=re.I)
    for n,month in enumerate(('January','February','March','April','May','June','July','August','September','October','November','December'),1):
        value=re.sub(r'\b'+month+r'\b',str(n),value,flags=re.I)
    value=re.sub(r'(?<=\d),(?=\d{3}(?:\D|$))','',value)
    return Counter(float(n) for n in re.findall(r'\d+(?:\.\d+)?',value))

def main():
    p=argparse.ArgumentParser();p.add_argument('--inventory',required=True);p.add_argument('--catalog',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    inventory=json.loads(Path(a.inventory).read_text());catalog=json.loads(Path(a.catalog).read_text());errors=[];checked=0
    for source,locations in inventory.items():
        if source in (r'文件第 (\d+) 页',r'段落 (\d+)'):continue # Internal matching expressions, never UI copy.
        translated=catalog.get(source)
        if not translated or HAN.search(translated):errors.append({'source':source,'problem':'missing English'});continue
        # Only current public prose, not regexes, internal templates or copied licenses.
        if not any(x.startswith(('news/','watch/','charts/','history/','map-history/','library/')) for x in locations):continue
        checked+=1
        missing=numbers(source)-numbers(translated)
        if missing:errors.append({'source':source,'translation':translated,'missing_numbers':list(missing.elements())})
        for url in re.findall(r'https?://[^\s\u3400-\u9fff，。；）)\]、]+',source):
            if url not in translated:errors.append({'source':source,'problem':'source URL changed','url':url})
        for url in re.findall(r'\]\(([^)]+)\)',source):
            if ']('+url+')' not in translated:errors.append({'source':source,'problem':'Markdown destination changed','url':url})
        for token in re.findall(r'[A-Za-z0-9]{30,}',source):
            if token not in translated:errors.append({'source':source,'problem':'revision identifier changed','token':token})
    Path(a.output).write_text(json.dumps({'public_strings_checked':checked,'errors':errors},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'public_strings_checked':checked,'errors':len(errors)}))
    if errors:raise SystemExit(1)
if __name__=='__main__':main()
