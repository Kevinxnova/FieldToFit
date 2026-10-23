/** Shared selection geometry and actual homepage interactions, including existing records. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {createRequire}=require('node:module'),root=path.resolve(__dirname,'../..'),fr=createRequire(path.join(root,'frontend/package.json'));
const React=fr('react'),{create,act}=fr('react-test-renderer'),ts=fr('typescript'),rr=fr('react-router');
global.IS_REACT_ACT_ENVIRONMENT=true;
const store=new Map(),session=new Map();let focused='',zh=true;
global.localStorage={getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v)};
global.sessionStorage={getItem:k=>session.get(k)||null,setItem:(k,v)=>session.set(k,v)};
global.ResizeObserver=class{observe(){} disconnect(){}};
global.window={addEventListener(){},removeEventListener(){},dispatchEvent(){}};
global.document={body:{style:{overflow:''}}};
function load(file,imports={}){const m={exports:{}};const code=ts.transpileModule(fs.readFileSync(path.join(root,file),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true}}).outputText;new Function('require','module','exports',code)(id=>imports[id]??fr(id),m,m.exports);return m.exports;}
const ui={useWorkspace:()=>({zh,pick:(a,b)=>zh?a:b})};
const router=load('frontend/src/locale/router.tsx',{'../components/workspace/readingPosition':{saveReadingPosition(){}},'./language':{canonicalPath:x=>x,languagePath:x=>x,useLanguage:()=>zh?'zh':'en'},'./jsx-runtime':{DisplayText:({children})=>children}});
const raw=JSON.parse(fs.readFileSync(path.join(root,'backend/llm_evolution/catalog.json'))),preview=JSON.parse(fs.readFileSync(path.join(root,'backend/llm_evolution/home_preview.json')));
const data=load('frontend/src/features/evolution/data.ts',{'../../../../backend/llm_evolution/catalog.json':raw});
const layout=load('frontend/src/features/evolution/homeLayout.ts',{'./data':data,'../../../../backend/llm_evolution/home_preview.json':preview});
const progress=load('frontend/src/features/evolution/progress.ts');
store.set(progress.PROGRESS_KEY,JSON.stringify({version:1,records:{T01:{read:true,revision:1,at:'2026-10-22T00:00:00Z'}}}));session.set('fieldtofit:evolution:current','T01');
const hooks=load('frontend/src/features/evolution/useProgress.ts',{'./progress':progress});
const base={'@fieldtofit/locale/router':router,'../../components/workspace/UI':ui,'../../search':{PageMetadata:()=>null},'./data':data};
const atlas=load('frontend/src/features/evolution/AtlasMap.tsx',{...base,'./atlasLayout':{},'./atlas.css':{}});
const home=load('frontend/src/features/evolution/HomeAtlas.tsx',{...base,'./AtlasMap':atlas,'./homeLayout':layout,'./home.css':{}});
const evolution=load('frontend/src/features/evolution/Evolution.tsx',{...base,'./AtlasMap':atlas,'./HomeAtlas':home,'./progress':progress,'./useProgress':hooks,'./evolution.css':{}});
function mock(){return {open:false,isConnected:true,showModal(){this.open=true},close(){this.open=false},focus(){focused='node'}};}
(async()=>{
 for(const width of [600,625,840])for(const lang of [true,false])for(const track of raw.tracks){
  const graph=layout.homeLayout(track.id,lang,width);
  assert.equal(graph.items.length,7);
  for(const [i,a]of graph.items.entries()){
   assert.equal(a.route.track,track.id);assert(a.y+a.height<=graph.height);
   const year=+a.node.date.slice(0,4),column=preview[track.id].find(n=>n.id===a.id).column;
   assert(column===0?year<=2021:column===1?year>=2022&&year<=2023:column===2?year===2024:column<=4?year===2025:year===2026);
   for(const b of graph.items.slice(i+1))assert(a.x+a.width<=b.x||b.x+b.width<=a.x||a.y+a.height<=b.y||b.y+b.height<=a.y,'overlap');
  }
  const ids=new Set(graph.items.map(n=>n.id));assert.deepEqual(graph.paths.map(p=>p.relation),raw.relations.filter(e=>ids.has(e.from_node)&&ids.has(e.to_node)));
 }
 let renderer;await act(async()=>renderer=create(React.createElement(rr.MemoryRouter,null,React.createElement(evolution.EvolutionHome)),{createNodeMock:mock}));
 const r=()=>renderer.root;
 assert.equal(r().findAllByType('button').filter(b=>b.props['data-home-node']).length,21);
 assert.equal(r().findByProps({className:'evolution-question-progress'}).findByType('span').props.children[0],1);
 const before=store.get(progress.PROGRESS_KEY);
 const node=r().findByProps({'data-home-node':'reasoning_rl-r1_paper'});
 await act(async()=>node.props.onClick({currentTarget:{isConnected:true,focus(){focused='r1'}}}));
 assert.equal(document.body.style.overflow,'hidden');assert.equal(node.props['aria-expanded'],true);
 assert(r().findAllByType('a').some(a=>a.props.href===raw.sources.r1_paper.url));
 await act(async()=>r().findByType('dialog').props.onCancel());assert.equal(document.body.style.overflow,'');assert.equal(focused,'r1');assert.equal(store.get(progress.PROGRESS_KEY),before);
 await act(async()=>r().findByProps({'aria-controls':'evolution-home-directory'}).props.onClick());
 assert.equal(r().findByProps({id:'evolution-home-directory'}).findAllByType('article').length,18);
 const q=r().findByProps({className:'evolution-question-copy'}).findAllByType('a')[0];assert.equal(q.props.href,'/for-you/evolution/questions/T01');
 const checkbox=r().findByProps({className:'evo-featured-question'}).findByType('input');await act(async()=>checkbox.props.onChange({target:{checked:false}}));assert.equal(JSON.parse(store.get(progress.PROGRESS_KEY)).records.T01.read,false);
 zh=false;await act(async()=>renderer.update(React.createElement(rr.MemoryRouter,null,React.createElement(evolution.EvolutionHome))));assert(r().findAllByType('h2').some(h=>h.props.children==='LLM technical evolution'));
 await act(async()=>renderer.unmount());assert.equal(document.body.style.overflow,'');
 console.log('PASS homepage: shared 21-node selection, year positions/non-overlap, sourced edges only, node evidence/Esc/focus, no automatic read writes, 18-question directory, existing manual records, bilingual render');
})().catch(e=>{console.error(e);process.exitCode=1});
