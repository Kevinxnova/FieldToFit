/** Exercise the real useRemote hook with deferred responses, without a browser or live data. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {createRequire}=require('node:module');
const root=path.resolve(__dirname,'../..');
const frontendRequire=createRequire(path.join(root,'frontend/package.json'));
const React=frontendRequire('react');
const {create,act}=frontendRequire('react-test-renderer');
const ts=frontendRequire('typescript');
global.IS_REACT_ACT_ENVIRONMENT=true;
global.sessionStorage={getItem:()=>''};
const Language=React.createContext('zh');
let selected='zh',restored=[],pending=[];
global.fetch=(url,options)=>new Promise(resolve=>pending.push({url,options,resolve}));
const locale={currentLanguage:()=>selected,useLanguage:()=>React.useContext(Language),english:s=>s,restoreLanguageScroll:lang=>restored.push(lang)};
const source=fs.readFileSync(path.join(root,'frontend/src/api/knowledge.ts'),'utf8').replace('import.meta.env.VITE_API_URL','""');
const compiled=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const loaded={exports:{}};
new Function('require','module','exports',compiled)(name=>name==='../locale/language'?locale:frontendRequire(name),loaded,loaded.exports);
const {useRemote}=loaded.exports;
async function surface(admin=false){
  selected='zh';pending=[];restored=[];let result;const snapshots=[];
  function Read(){result=useRemote('/v1/platform/watch',admin);snapshots.push({language:selected,...result});return null;}
  const element=()=>React.createElement(Language.Provider,{value:selected},React.createElement(Read));
  let renderer;await act(async()=>{renderer=create(element());});
  return {get result(){return result;},snapshots,async switch(lang){selected=lang;await act(async()=>renderer.update(element()));},async close(){await act(async()=>renderer.unmount());}};
}
async function respond(index,body,ok=true){await act(async()=>{pending[index].resolve({ok,status:ok?200:503,json:async()=>body});});}
function scrollChecks(){
  let frames=[],events={},anchorCalls=0,scrolls=[];
  const location={pathname:'/for-you',search:'?q=REA',hash:'#watch-cw-t16'};
  global.location=location;
  global.window={location,scrollX:0,scrollY:830,confirm:()=>true,history:{state:{},replaceState(_state,_title,value){const url=new URL(value,'http://isolated');Object.assign(location,{pathname:url.pathname,search:url.search,hash:url.hash});}},addEventListener(name,fn){(events[name]??=[]).push(fn);},dispatchEvent(){},scrollTo(...value){scrolls.push(value);}};
  global.document={getElementById:id=>id==='watch-cw-t16'?{scrollIntoView(){anchorCalls++;}}:null};
  global.PopStateEvent=class{};
  global.requestAnimationFrame=fn=>{frames.push(fn);return frames.length;};
  const source=fs.readFileSync(path.join(root,'frontend/src/locale/language.ts'),'utf8');
  const compiled=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true}}).outputText;
  const module={exports:{}};
  new Function('require','module','exports',compiled)(name=>name==='./en.json'?frontendRequire('./src/locale/en.json'):frontendRequire(name),module,module.exports);
  const flush=()=>{while(frames.length)frames.shift()();};
  module.exports.changeLanguage('en');flush();
  assert.equal(location.pathname,'/en/for-you');assert.equal(location.search,'?q=REA');assert.equal(location.hash,'#watch-cw-t16');
  module.exports.restoreLanguageScroll('en');flush();assert.equal(anchorCalls,1);
  console.log('PASS: delayed restoration keeps the query and fragment and returns to the reading anchor');
  module.exports.restoreLanguageScroll('en');events.pointerdown.forEach(fn=>fn());flush();assert.equal(anchorCalls,1);
  location.hash='';module.exports.changeLanguage('zh');flush();module.exports.restoreLanguageScroll('zh');flush();assert.deepEqual(scrolls.at(-1),[0,830]);
  console.log('PASS: reader input cancels pending restoration; unanchored reading retains the numeric position');
}
(async()=>{
  let s=await surface();
  await respond(0,{title:'中文正文'});assert.equal(s.result.data.title,'中文正文');
  const start=s.snapshots.length;await s.switch('en');
  assert(s.snapshots.slice(start).every(x=>x.data===null),'Every English render must reject cached Chinese data, including the render before effects');
  assert.equal(s.result.loading,true);assert.match(pending[1].url,/lang=en/);
  await respond(1,{title:'Reviewed English body'});
  assert.equal(s.result.data.title,'Reviewed English body');assert.equal(s.result.loading,false);assert.deepEqual(restored,['en']);await s.close();
  console.log('PASS: pending English reads expose no Chinese data and restore reading position only after success');

  s=await surface();await respond(0,{title:'中文正文'});await s.switch('en');
  await respond(1,{detail:'English review is stale'},false);
  assert.equal(s.result.data,null);assert.equal(s.result.loading,false);assert.equal(s.result.error,'English review is stale');assert.deepEqual(restored,[]);await s.close();
  console.log('PASS: failed English reads cannot fall back to Chinese or enable data-based copies');

  s=await surface();await respond(0,{title:'中文正文'});await s.switch('en');await s.switch('zh');
  assert.equal(pending[1].options.signal.aborted,true);
  await respond(1,{title:'Late English body'});assert.equal(s.result.data,null);
  await respond(2,{title:'最新中文正文'});assert.equal(s.result.data.title,'最新中文正文');assert.deepEqual(restored,['zh']);await s.close();
  console.log('PASS: rapid switches ignore an aborted response from the previous language');

  s=await surface(true);await respond(0,{draft:'尚未保存的原稿'});await s.switch('en');
  assert.equal(pending.length,1);assert.equal(s.result.data.draft,'尚未保存的原稿');assert.equal(s.result.loading,false);assert.deepEqual(restored,[]);await s.close();
  console.log('PASS: private canonical editor data survives language changes without another request');
  scrollChecks();
})().catch(error=>{console.error(error);process.exitCode=1;});
