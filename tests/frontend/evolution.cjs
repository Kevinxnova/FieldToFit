const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {createRequire}=require('node:module');const root=path.resolve(__dirname,'../..'),fr=createRequire(path.join(root,'frontend/package.json')),ts=fr('typescript');
function load(name,imports={}){const m={exports:{}};new Function('module','exports','require',ts.transpileModule(fs.readFileSync(path.join(root,'frontend/src/features/evolution/'+name+'.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true}}).outputText)(m,m.exports,id=>imports[id]??fr(id));return m.exports;}
const p=load('progress');const at='2026-10-21T00:00:00Z';const saved={T01:{read:true,revision:1,at},I01:{read:false,revision:1,at}};
assert.deepEqual(p.decodeProgress(null),{});
assert.throws(()=>p.decodeProgress('{bad'));
assert.throws(()=>p.decodeProgress('{"version":2,"records":{}}'));
assert.deepEqual(p.decodeProgress(JSON.stringify({version:1,records:{...saved,T02:{read:true,revision:-1,at},S01:null}})),saved);
assert.equal(p.statusFor(saved,'T01',1),'read');assert.equal(p.statusFor(saved,'T01',2),'updated');assert.equal(p.statusFor(saved,'I01',1),'unread');assert.equal(p.statusFor(saved,'S01',1),'unread');
const qs=[{id:'T01',revision:1},{id:'I01',revision:1}];assert.equal(p.chooseQuestion(qs,saved,'T01',()=>0).id,'I01');assert.equal(p.chooseQuestion(qs,{T01:saved.T01,I01:{...saved.T01}},'T01',()=>0).id,'I01');assert.equal(p.chooseQuestion([qs[0]],saved,'T01',()=>1).id,'T01');assert.equal(p.chooseQuestion([],saved),undefined);
let stored=JSON.stringify({version:1,records:saved}),denied=false,listener,subscriber,getSnapshot,notify=0;
global.localStorage={getItem:()=>{if(denied)throw Error('denied');return stored;},setItem:(_k,v)=>{if(denied)throw Error('denied');stored=v;}};
global.window={addEventListener:(_n,fn)=>listener=fn,removeEventListener:()=>{}};
const hook=load('useProgress',{'./progress':p,react:{useSyncExternalStore:(sub,get)=>{subscriber=sub;getSnapshot=get;return get();}}});
assert.deepEqual(hook.useProgress().records,saved);const unsub=subscriber(()=>notify++);
hook.markRead('T02',1,true);assert.equal(getSnapshot().records.T02.read,true);assert.equal(JSON.parse(stored).records.T01.read,true);
hook.markRead('T01',2,true);assert.equal(p.statusFor(getSnapshot().records,'T01',2),'read');hook.markRead('T01',2,false);assert.equal(getSnapshot().records.T01.read,false);
stored=JSON.stringify({version:1,records:{S01:saved.T01}});listener({key:p.PROGRESS_KEY});assert.equal(getSnapshot().records.S01.read,true);assert.equal(getSnapshot().records.T02,undefined);
stored='{broken';listener({key:p.PROGRESS_KEY});assert.equal(getSnapshot().warning,true);assert.equal(getSnapshot().records.S01.read,true);
denied=true;hook.markRead('I02',1,true);assert.equal(getSnapshot().records.I02.read,true);assert.equal(getSnapshot().warning,true);denied=false;stored=null;listener({key:null});assert.deepEqual(getSnapshot().records,{});assert.equal(getSnapshot().warning,false);assert(notify>=6);unsub();
const catalog=JSON.parse(fs.readFileSync(path.join(root,'backend/llm_evolution/catalog.json')));const d=load('data',{'../../../../backend/llm_evolution/catalog.json':catalog});assert.equal(d.kvMiB(1,32,4096,8,128,2),512);assert.equal(d.kvMiB(8,32,4096,8,128,2),4096);assert.equal(d.kvMiB(0,32,4096,8,128,2),null);assert.equal(d.kvMiB(NaN,32,4096,8,128,2),null);
assert.equal(d.kvMiB(1e200,1e200,4096,8,128,2),null);
console.log('PASS evolution: revisions, manual marks, refresh serialization, tab changes, corrupted/blocked storage, all-read selection and KV units');
// Filters operate on nodes, retain date precision, and link across filtered tracks.
for(const route of catalog.routes){
 assert.deepEqual(d.visibleNodes(route,true,'all'),route.nodes);
 assert(d.visibleNodes(route,false,'recent').every(n=>n.highlight&&n.date>='2025'));
 for(const node of route.nodes){
  const dest=new URL(d.nodeDestination(node.id),'https://example.test');
  assert.equal(dest.searchParams.get('node'),node.id);assert.equal(dest.searchParams.get('track'),route.track);
  assert.equal(dest.searchParams.get('view'),'all');
  assert.equal(dest.searchParams.get('period'),node.date>='2025'?'recent':'all');
  assert(d.nodeCases(route,node.id).every(c=>c.nodes.includes(node.id)));
 }
}
assert.equal(d.timeBand('2025'),'2025');assert.equal(d.timeBand('2025-12-31'),'2025 H2');assert.equal(d.timeBand('2026-01-12'),'2026 H1');assert.equal(d.timeBand('2024-12-27'),'2023–2024');
assert.equal(d.nodeDestination('missing'),d.ROOT);
assert(d.visibleNodes(catalog.routes.find(r=>r.id==='hybrid'),false,'recent').some(n=>n.id==='hybrid-q35'));
console.log('PASS atlas: node filters, historical and cross-track destinations, company evidence and date precision');
