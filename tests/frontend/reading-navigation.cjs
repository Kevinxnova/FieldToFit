/** Use the actual localized Link and detail return control with React Router. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {createRequire}=require('node:module');
const root=path.resolve(__dirname,'../..'),fr=createRequire(path.join(root,'frontend/package.json'));
const React=fr('react'),{create,act}=fr('react-test-renderer'),ts=fr('typescript'),rr=fr('react-router');
global.IS_REACT_ACT_ENVIRONMENT=true;
global.document={getElementById:()=>null};
function load(file,imports){const m={exports:{}};const code=ts.transpileModule(fs.readFileSync(path.join(root,file),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX}}).outputText;new Function('require','module','exports',code)(name=>imports[name]||fr(name),m,m.exports);return m.exports;}
const router=load('frontend/src/locale/router.tsx',{'../components/workspace/readingPosition':{saveReadingPosition:()=>{}},'./language':{canonicalPath:x=>x,languagePath:x=>x,useLanguage:()=> 'zh'},'./jsx-runtime':{DisplayText:({children})=>children}});
const empty=()=>null;
const {PublishedDetail}=load('frontend/src/pages/PublishedDetail.tsx',{'@fieldtofit/locale/router':router,'../api/reading':{useReadingRemote:()=>({data:null,loading:true,error:'',reload:()=>{}})},'../components/workspace/TechnicalMaps':{RelatedMaps:empty},'../components/workspace/NewsReading':{NewsReading:empty},'../components/workspace/ContinuousWatch':{ContinuousWatch:empty},'../components/workspace/SiteVisits':{VisitReady:empty},'../components/workspace/UI':{useWorkspace:()=>({pick:zh=>zh})},'../search':{PageMetadata:empty,contentPath:id=>'/news/'+id}});
let location,renderer;
function App(){location=rr.useLocation();return React.createElement(rr.Routes,null,React.createElement(rr.Route,{path:'/for-you',element:React.createElement(router.Link,{to:'/news/D-01'},'Read a Codex detail')}),React.createElement(rr.Route,{path:'/news/:id',element:React.createElement(PublishedDetail,{kind:'news'})}));}
async function click(){const link=renderer.root.findByType('a');await act(async()=>link.props.onClick({button:0,defaultPrevented:false,currentTarget:{getAttribute:()=>null},preventDefault(){this.defaultPrevented=true;}}));}
(async()=>{
 const source='/for-you?news_type=agent&news_page=2&codex_date=2026-10-12#news-codex-28-days';
 await act(async()=>{renderer=create(React.createElement(rr.MemoryRouter,{initialEntries:[source]},React.createElement(App)));});
 await click();assert.equal(location.pathname,'/news/D-01');assert.equal(location.state.readingReturn.url,source);assert.equal(location.state.readingReturn.id,undefined);
 await click();assert.equal(location.pathname+location.search+location.hash,source);assert.equal(location.state.restoreReading,true);
 await act(async()=>renderer.unmount());console.log('PASS detail return without an item-anchor ID preserves all filters, date, fragment and requests position restoration');
})().catch(error=>{console.error(error);process.exitCode=1;});
