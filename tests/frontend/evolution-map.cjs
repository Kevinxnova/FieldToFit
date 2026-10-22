/** Actual map component with the locale router's intentionally unstable search setter. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {createRequire}=require('node:module');const root=path.resolve(__dirname,'../..'),fr=createRequire(path.join(root,'frontend/package.json'));
const React=fr('react'),{create,act}=fr('react-test-renderer'),ts=fr('typescript'),rr=fr('react-router');
global.IS_REACT_ACT_ENVIRONMENT=true;
let focused='',scrolled='',dialogOpen=false,renderCount=0;const storage=new Map();
global.sessionStorage={getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)};
global.document={body:{style:{overflow:''}},getElementById:id=>({scrollIntoView:()=>scrolled=id,focus:()=>focused=id})};
function load(file,imports){const m={exports:{}};const code=ts.transpileModule(fs.readFileSync(path.join(root,file),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true}}).outputText;new Function('require','module','exports',code)(id=>imports[id]||fr(id),m,m.exports);return m.exports;}
const router=load('frontend/src/locale/router.tsx',{'../components/workspace/readingPosition':{saveReadingPosition:()=>{}},'./language':{canonicalPath:x=>x,languagePath:x=>x,useLanguage:()=> 'zh'},'./jsx-runtime':{DisplayText:({children})=>children}});
const raw=JSON.parse(fs.readFileSync(path.join(root,'backend/llm_evolution/catalog.json')));
const data=load('frontend/src/features/evolution/data.ts',{'../../../../backend/llm_evolution/catalog.json':raw});
const {AtlasMap}=load('frontend/src/features/evolution/AtlasMap.tsx',{'@fieldtofit/locale/router':router,'./data':data,'../../components/workspace/UI':{useWorkspace:()=>{if(++renderCount>2000)throw Error('Unbounded map render loop');return {zh:true,pick:z=>z};}},'../../search':{PageMetadata:()=>null}});
let location,renderer;
function App(){location=rr.useLocation();return React.createElement(AtlasMap,{navigation:null,footer:null});}
const button=name=>renderer.root.findAllByType('button').find(b=>b.props.children===name);
const selected=id=>renderer.root.findAllByType('article').find(a=>a.props.id==='node-'+id);
const toggle=id=>selected(id).findAllByType('button')[0];
(async()=>{
 await act(async()=>{renderer=create(React.createElement(rr.MemoryRouter,{initialEntries:['/for-you/evolution?period=recent&view=key&track=systems&node=latent_kv-v3']},React.createElement(App)),{createNodeMock:element=>element.type==='dialog'?{showModal:()=>dialogOpen=true,close:()=>dialogOpen=false}:{focus:()=>focused='fullscreen-button'}});});
 await act(async()=>{await new Promise(r=>setTimeout(r,130));});
 assert.equal(new URLSearchParams(location.search).get('period'),'all');assert.equal(new URLSearchParams(location.search).get('track'),'inference');
 assert.equal(toggle('latent_kv-v3').props['aria-expanded'],true);assert.equal(scrolled,'node-latent_kv-v3');assert.equal(focused,'node-latent_kv-v3');
 await act(async()=>toggle('latent_kv-v3').props.onClick());assert.equal(toggle('latent_kv-v3').props['aria-expanded'],false);
 await act(async()=>button('全屏阅读大图 ↗').props.onClick());assert.equal(dialogOpen,true);assert.equal(toggle('latent_kv-v3').props['aria-expanded'],false);assert.equal(document.body.style.overflow,'hidden');
 await act(async()=>renderer.root.findByType('dialog').props.onCancel());assert.equal(dialogOpen,false);assert.equal(document.body.style.overflow,'');assert.equal(toggle('latent_kv-v3').props['aria-expanded'],false);
 await act(async()=>renderer.unmount());
 console.log('PASS atlas component: conflicting legacy URL normalization, bounded renders, focus/scroll, fullscreen and collapsed-detail persistence');
})().catch(e=>{console.error(e);process.exitCode=1;});
