const fs=require('node:fs'),path=require('node:path'),{createRequire}=require('node:module');
const root=path.resolve(__dirname,'../..'),fr=createRequire(path.join(root,'frontend/package.json')),ts=fr('typescript'),React=fr('react'),rr=fr('react-router'),{create,act}=fr('react-test-renderer');
global.IS_REACT_ACT_ENVIRONMENT=true;
const local=new Map(),session=new Map(),state={zh:true,focused:'',scrolled:'',denied:false,renders:0};
global.localStorage={getItem:k=>local.get(k)||null,setItem:(k,v)=>local.set(k,v)};
global.sessionStorage={getItem:k=>{if(state.denied)throw Error('blocked');return session.get(k)||null},setItem:(k,v)=>{if(state.denied)throw Error('blocked');session.set(k,v)}};
global.window={innerWidth:1280,addEventListener(){},removeEventListener(){},dispatchEvent(){},matchMedia:()=>({matches:false,addEventListener(){},removeEventListener(){}})};
global.document={body:{style:{overflow:''}},getElementById:id=>({scrollIntoView(){state.scrolled=id}})};
global.ResizeObserver=class{observe(){}disconnect(){}};
global.requestAnimationFrame=fn=>setTimeout(fn,0);global.cancelAnimationFrame=clearTimeout;
const ui={useWorkspace:()=>{if(++state.renders>10000)throw Error('Render loop');return {zh:state.zh,pick:(z,e)=>state.zh?z:e}}};
let router;const cache=new Map();
function load(file){file=path.resolve(root,file);if(cache.has(file))return cache.get(file).exports;const m={exports:{}};cache.set(file,m);const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true}}).outputText;new Function('require','module','exports',code)(id=>{
 if(id.endsWith('.css'))return {};
 if(id==='@fieldtofit/locale/router')return router;
 if(id.endsWith('components/workspace/UI'))return ui;
 if(id==='../../search')return {PageMetadata:()=>null};
 if(file.endsWith('/locale/router.tsx')){if(id.endsWith('readingPosition'))return {saveReadingPosition(){}};if(id==='./language')return {canonicalPath:x=>x,languagePath:x=>x,useLanguage:()=>state.zh?'zh':'en'};if(id==='./jsx-runtime')return {DisplayText:({children})=>children};}
 if(id.startsWith('.')){let target=path.resolve(path.dirname(file),id);if(target.endsWith('.json'))return JSON.parse(fs.readFileSync(target));for(const ext of ['.ts','.tsx'])if(fs.existsSync(target+ext))return load(target+ext);}
 return fr(id);
},m,m.exports);return m.exports;}
router=load('frontend/src/locale/router.tsx');
function mock(el){return {open:false,isConnected:true,clientWidth:1000,clientHeight:650,scrollLeft:0,scrollTop:0,showModal(){this.open=true},close(){this.open=false},focus(){state.focused=el.props['data-node']||el.props.id||'control'},scrollIntoView(){state.scrolled=el.props.id},querySelector(selector){return {focus(){state.focused=selector.match(/data-node="([^"]+)"/)?.[1]}}}};}
module.exports={root,React,rr,create,act,state,session,local,load,mock,raw:JSON.parse(fs.readFileSync(path.join(root,'backend/llm_evolution/catalog.json')))};
