"""Save locally authored translations by immutable inventory position."""
import argparse
import json
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('queue');parser.add_argument('start',type=int);parser.add_argument('batch');parser.add_argument('target')
args=parser.parse_args();source=json.loads(Path(args.queue).read_text());translated=json.loads(Path(args.batch).read_text());path=Path(args.target)
assert args.start+len(translated)<=len(source)
assert all(isinstance(s,str) and s for s in translated)
data=json.loads(path.read_text()) if path.exists() else {}
data.update(dict(zip(source[args.start:args.start+len(translated)],translated)))
path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'batch':len(translated),'total':len(data)}))
