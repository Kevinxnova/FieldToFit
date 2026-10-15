/** Deferred real-hook tests: bootstrap, bounded cache, updates and revocation races. */
const assert=require('node:assert/strict'), fs=require('node:fs'), path=require('node:path');
const {createRequire}=require('node:module');
const root=path.resolve(__dirname,'../..'), fr=createRequire(path.join(root,'frontend/package.json'));
const React=fr('react'),{create,act}=fr('react-test-renderer'),ts=fr('typescript');
global.IS_REACT_ACT_ENVIRONMENT=true;
const Language=React.createContext('zh');
const source=ts.transpileModule(fs.readFileSync(path.join(root,'frontend/src/api/reading.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const home=(revision='1',ids=['D-01'])=>({revision,safety:{items:ids.map(id=>[id,true,[['m','https://example.org','full_text']]]),aliases:[]},news:{items:ids.map(id=>({id})),revision},watch:{items:[]},projects:{items:[]},charts:{}});
const body=(id='D-01')=>({items:[{id,materials:[{id:'m'}]}]});
function setup(bootstrap){
 let language='zh',token='',pending=[],removed=false,events=[];
 global.window={dispatchEvent:event=>events.push(event.type),addEventListener:()=>{},removeEventListener:()=>{}};
 global.document={visibilityState:'visible',addEventListener:()=>{},removeEventListener:()=>{},getElementById:()=>bootstrap?{textContent:JSON.stringify({language:'zh',q:'',type:'',view:bootstrap.view,data:bootstrap}),remove:()=>{removed=true;}}:null};
 const loaded={exports:{}};
 new Function('require','module','exports',source)(name=>name==='./knowledge'?{readToken:()=>token,request:url=>new Promise((resolve,reject)=>pending.push({url,language,resolve,reject}))}:name==='../locale/language'?{restoreLanguageScroll:()=>{},useLanguage:()=>React.useContext(Language),currentLanguage:()=>language}:fr(name),loaded,loaded.exports);
 const api=loaded.exports;
 async function mount(paths=['/v1/platform/news?id=D-01']){
  let values=[],update;
  function Read({url,index}){values[index]=api.useReadingRemote(url);return null;}
  function Updates(){update=api.useReadingUpdates(false);return null;}
  const element=()=>React.createElement(Language.Provider,{value:language},React.createElement(React.Fragment,null,...paths.map((url,index)=>React.createElement(Read,{key:index,url,index})),React.createElement(Updates)));
  let renderer;await act(async()=>{renderer=create(element());});
  return {get values(){return values;},get update(){return update;},async language(next){language=next;await act(async()=>renderer.update(element()));},async paths(next){paths=next;await act(async()=>renderer.update(element()));},async token(next){token=next;await act(async()=>renderer.update(element()));},async close(){await act(async()=>renderer.unmount());}};
 }
 return {api,mount,pending,events,get removed(){return removed;},resolve:async(i,data)=>act(async()=>pending[i].resolve(data)),reject:async(i,status)=>act(async()=>pending[i].reject(Object.assign(new Error('Failure '+status),{status})))};
}
let completed=false;process.on('beforeExit',()=>{if(!completed){console.error('FAIL: unresolved async test');process.exitCode=1;}});
const HOME='/v1/platform/reading?q=&type=';
(async()=>{
 let s=setup(home()),v=await s.mount([HOME]);assert(s.removed);assert.equal(s.pending.length,0);assert.equal(v.values[0].data.revision,'1');await v.close();
 v=await s.mount([HOME]);assert.match(s.pending[0].url,/after=1/);assert.equal(v.values[0].loading,false);await s.resolve(0,{unchanged:true});await v.close();
 console.log('PASS bootstrap has no duplicate request; returning keeps data during a revision check');
 s=setup();v=await s.mount(['/v1/platform/news?id=D-01','/v1/platform/news?id=D-01']);assert.equal(s.pending.length,1);await s.resolve(0,body());await v.close();
 v=await s.mount();assert.equal(v.values[0].loading,false);await s.reject(1,503);assert(v.values[0].data);assert(v.values[0].refreshError);await v.close();
 v=await s.mount();await s.reject(2,404);assert.equal(v.values[0].data,null);assert(v.values[0].error);await v.close();
 console.log('PASS duplicate detail reads merge; temporary failures retain content; 404 removes retained content');
 s=setup(home());v=await s.mount([HOME,'/v1/platform/news?id=D-01']);await s.resolve(0,body());
 let check;await act(async()=>{check=s.api.checkReading();});await s.resolve(1,home('2',['D-01','D-02']));await check;
 assert.equal(v.values[0].data.revision,'1');assert(v.update.pending);
 await act(async()=>s.api.applyReadingUpdate());assert.equal(v.values[0].data.revision,'2');assert.equal(v.values[1].data,null);assert(s.events.includes('fieldtofit:restore-reading'));
 await s.resolve(2,body());
 await act(async()=>{check=s.api.checkReading();});await s.resolve(3,home('3',['D-02']));await check;
 assert.equal(v.values[0].data.revision,'3');assert.equal(v.values[1].data,null);assert.equal(v.update.notice,'withdrawn');await s.reject(4,410);await v.close();
 console.log('PASS normal updates wait for application; withdrawal automatically clears details');
 s=setup(home());v=await s.mount([HOME]);await act(async()=>{check=s.api.checkReading();});await s.reject(0,503);await check;assert(v.values[0].data);assert.equal(v.update.notice,'offline');
 await act(async()=>{check=s.api.checkReading();});await s.reject(1,401);await check;assert.equal(v.values[0].data,null);assert(v.values[0].error);assert.equal(s.pending.length,2);await v.close();
 console.log('PASS failed checks stay readable; permission loss clears data without a request loop');
 s=setup();v=await s.mount();await v.language('en');assert.equal(v.values[0].data,null);await s.resolve(0,body('CHINESE'));assert.equal(v.values[0].data,null);await s.resolve(1,body('ENGLISH'));assert.equal(v.values[0].data.items[0].id,'ENGLISH');
 await v.token('different-reader');assert.equal(v.values[0].data,null);await s.resolve(2,body('NEW IDENTITY'));await v.close();
 console.log('PASS language responses and token identities are isolated');
 s=setup();v=await s.mount(['/v1/platform/news?id=one']);await s.resolve(0,body('one'));
 // Keep one component mounted while filling the ten-entry LRU with other reads.
 for(let i=0;i<11;i++){let job;await act(async()=>{job=s.api.readComplete('/v1/platform/news?id='+i);});await s.resolve(i+1,body(String(i)));await job;}
 assert.equal(v.values[0].data.items[0].id,'one');assert.equal(s.pending.length,12);await v.close();
 v=await s.mount(['/v1/platform/news?id=0']);assert.equal(v.values[0].data,null);await s.resolve(12,body('0'));await v.close();
 v=await s.mount(['/v1/platform/news?id=huge']);await s.resolve(13,{text:'x'.repeat(8*1024*1024+1)});assert.equal(v.values[0].data,null);assert(v.values[0].error);await v.close();
 console.log('PASS bounded LRU evicts old entries without refetching mounted cards; oversized data is rejected');

 for(const mutate of [h=>h.safety.items[0][2][0][2]='withdrawn',h=>h.safety.items[0][1]=false,h=>h.safety.aliases.push({source_id:'D-99',target_id:'D-01'})]){
  s=setup(home());v=await s.mount([HOME]);let changed=home('2');mutate(changed);
  await act(async()=>{check=s.api.checkReading();});await s.resolve(0,changed);await check;assert.equal(v.update.notice,'withdrawn');assert.equal(v.values[0].data.revision,'2');await v.close();
 }
 s=setup(home());v=await s.mount([HOME]);document.visibilityState='hidden';await s.api.checkReading();assert.equal(s.pending.length,0);document.visibilityState='visible';
 await act(async()=>{check=s.api.checkReading();});await act(async()=>s.pending[0].reject(Object.assign(new Error('Missing English review'),{status:503,code:'english_unavailable'})));await check;assert.equal(v.values[0].data,null);await s.reject(1,503);await v.close();
 console.log('PASS material restrictions, aliases and invalid English reviews purge prior content; hidden pages skip polling');
 s=setup();v=await s.mount([HOME]);await v.paths([HOME+'GPT']);await s.resolve(1,home('filtered'));await s.resolve(0,home('old'));assert.equal(v.values[0].data.revision,'filtered');
 await act(async()=>{check=s.api.checkReading();});assert.match(s.pending[2].url,/type=GPT&after=filtered/);await s.resolve(2,{unchanged:true});await check;await v.close();
 console.log('PASS late filter responses cannot replace the active revision-check context');
 s=setup(home());v=await s.mount([HOME]);await act(async()=>{check=s.api.checkReading();});await s.resolve(0,home('2'));await check;assert(v.update.pending);await v.paths([HOME+'GPT']);await s.resolve(1,home('2'));assert.equal(v.update.pending,false);await v.close();
 console.log('PASS changing filters discards pending results for the previous selection');
 s=setup();v=await s.mount();await s.resolve(0,body());let job;await act(async()=>{job=s.api.readComplete('/v1/platform/news?id=D-01').catch(e=>e);});await s.reject(1,503);assert(await job instanceof Error);await v.close();
 console.log('PASS exports revalidate and never silently return stale data after failure');
 const dailyHome=(revision,day,available)=>({...home(revision),daily:{issue:{date:day}},safety:{...home().safety,daily:available}});
 s=setup(dailyHome('1','2026-10-14',['2026-10-14']));v=await s.mount([HOME]);
 await act(async()=>{check=s.api.checkReading();});await s.resolve(0,dailyHome('2','2026-10-15',['2026-10-15','2026-10-14']));await check;
 assert.equal(v.values[0].data.daily.issue.date,'2026-10-14');assert(v.update.pending);assert.notEqual(v.update.notice,'withdrawn');
 await act(async()=>{check=s.api.checkReading();});await s.resolve(1,dailyHome('3','2026-10-15',['2026-10-15']));await check;
 assert.equal(v.values[0].data.daily.issue.date,'2026-10-15');assert.equal(v.update.notice,'withdrawn');await v.close();
 console.log('PASS a new daily issue waits for adoption; withdrawal of a retained issue forces safe replacement');
 s=setup({...home(),view:'home'});v=await s.mount([HOME+'&view=home']);assert.equal(s.pending.length,0);
 await v.paths([HOME+'&view=news']);assert.equal(v.values[0].data,null);assert.equal(s.pending[0].url,HOME+'&view=news');
 await s.resolve(0,{...home(),view:'news'});assert.equal(v.values[0].data.view,'news');
 await v.paths([HOME+'&view=home']);assert.equal(v.values[0].data.view,'home');assert.equal(v.values[0].loading,false);
 assert.equal(s.pending[1].url,HOME+'&view=home&after=1');await s.resolve(1,{unchanged:true});await v.close();
 console.log('PASS lightweight bootstrap and full columns remain separate; returning reuses the correct view');completed=true;
})().catch(error=>{console.error(error);process.exitCode=1;});
