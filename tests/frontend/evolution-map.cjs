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
const layout=load('frontend/src/features/evolution/atlasLayout.ts',{'./data':data});
global.window={matchMedia:()=>({matches:false,addEventListener(){},removeEventListener(){}})};
global.ResizeObserver=class {observe(){} disconnect(){}};
global.requestAnimationFrame=f=>setTimeout(f,0);global.cancelAnimationFrame=clearTimeout;
const {AtlasMap}=load('frontend/src/features/evolution/AtlasMap.tsx',{'@fieldtofit/locale/router':router,'./data':data,'./atlasLayout':layout,'./atlas.css':{},'../../components/workspace/UI':{useWorkspace:()=>{if(++renderCount>2000)throw Error('Unbounded map render loop');return {zh:true,pick:z=>z};}},'../../search':{PageMetadata:()=>null}});
let location,renderer;
function App(){location=rr.useLocation();return React.createElement(AtlasMap,{navigation:null,footer:null});}
const nodes=()=>renderer.root.findAllByType('button').filter(b=>b.props['data-node']);
const node=id=>nodes().find(b=>b.props['data-node']===id);
const track=id=>renderer.root.findAllByType('section').find(b=>b.props.id==='track-'+id);
const button=(id,name)=>track(id).findAllByType('button').find(b=>b.props.children===name);
function mock(element){return {open:false,clientWidth:1000,clientHeight:650,scrollLeft:0,scrollTop:0,showModal(){this.open=true;if(element.props.className==='atlas-fullscreen')dialogOpen=true;},close(){this.open=false;if(element.props.className==='atlas-fullscreen')dialogOpen=false;},focus(){focused=element.props.id||'control';},scrollIntoView(){scrolled=element.props.id;},querySelector(selector){const id=selector.match(/data-node="([^"]+)"/)?.[1];return {focus:()=>focused=id,scrollIntoView:()=>scrolled=id};}};}
(async()=>{
 for(const graph of Object.values(layout.atlasLayouts)){
   assert.equal(graph.items.length,raw.routes.filter(r=>r.track===graph.track).flatMap(r=>r.nodes).length);
   for(const [i,a] of graph.items.entries()){
     assert(a.rect.x>=0&&a.rect.y>=0&&a.rect.x+a.rect.width<=graph.width&&a.rect.y+a.rect.height<=graph.height);
     assert(graph.bands.some(b=>+a.node.date.slice(0,4)>=b.start&&+a.node.date.slice(0,4)<=b.end&&a.rect.x>=b.x&&a.rect.x+a.rect.width<=b.x+b.width));
     for(const b of graph.items.slice(i+1))assert(a.rect.x+a.rect.width<=b.rect.x||b.rect.x+b.rect.width<=a.rect.x||a.rect.y+a.rect.height<=b.rect.y||b.rect.y+b.rect.height<=a.rect.y,'nodes overlap');
   }
   assert.equal(graph.paths.filter(p=>p.evidence).length,raw.relations.filter(e=>graph.byId[e.from_node]&&graph.byId[e.to_node]).length);
 }
 assert.deepEqual(layout.boundedViewport({zoom:Infinity,left:-7,top:NaN,mode:'bad'}),{zoom:.7,left:0,top:0,mode:'all'});
 storage.set('fieldtofit:evolution:atlas-view:v2','{bad json');
 await act(async()=>{renderer=create(React.createElement(rr.MemoryRouter,{initialEntries:['/for-you/evolution?period=recent&view=key&track=systems&node=latent_kv-v3']},React.createElement(App)),{createNodeMock:mock});});
 await act(async()=>{await new Promise(r=>setTimeout(r,10));});
 assert.equal(nodes().length,93);assert.equal(renderer.root.findAllByProps({className:'atlas-track-definition'}).length,3);
 assert.equal(node('latent_kv-v3').props['aria-expanded'],true);assert.equal(focused,'latent_kv-v3');
 // Legacy filters remain valid links without hiding historical nodes or other tracks.
 assert.equal(new URLSearchParams(location.search).get('period'),'recent');
 await act(async()=>button('inference','全屏').props.onClick());assert.equal(dialogOpen,true);assert.equal(document.body.style.overflow,'hidden');assert.equal(node('latent_kv-v3').props['aria-expanded'],true);assert.equal(nodes().length,93);
 await act(async()=>button('inference','退出全屏').props.onClick());assert.equal(document.body.style.overflow,'');
 await act(async()=>track('inference').findAllByType('button').find(b=>b.props['aria-label']==='关闭节点详情').props.onClick());assert.equal(node('latent_kv-v3').props['aria-expanded'],false);
 await act(async()=>node('latent_kv-v3').props.onClick());assert.equal(new URLSearchParams(location.search).get('track'),'inference');
 assert.equal(node('latent_kv-v3').props['aria-expanded'],true);
 await act(async()=>button('inference','全屏').props.onClick());
 await act(async()=>node('dense-transformer').props.onClick());
 assert.equal(document.body.style.overflow,'');assert.equal(node('dense-transformer').props['aria-expanded'],true);
 await act(async()=>button('systems','全屏').props.onClick());assert.equal(document.body.style.overflow,'hidden');
 await act(async()=>button('systems','退出全屏').props.onClick());
 await act(async()=>renderer.unmount());assert.equal(document.body.style.overflow,'');
 console.log('PASS atlas: all 93 nodes, date bands/non-overlap, sourced paths, bounded viewport, malformed storage, legacy URLs, selection, focus, full screen and cleanup');
})().catch(e=>{console.error(e);process.exitCode=1;});
