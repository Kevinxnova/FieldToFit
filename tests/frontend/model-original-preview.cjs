/** Original geometry, complete labels, and read-only homepage accessibility. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {createRequire}=require('node:module');
const root=path.resolve(__dirname,'../..'),fr=createRequire(path.join(root,'frontend/package.json'));
const React=fr('react'),{create,act}=fr('react-test-renderer'),ts=fr('typescript');
global.IS_REACT_ACT_ENVIRONMENT=true;
global.document={createElement:()=>({getContext:()=>({measureText:text=>({width:text.length*7})})})};
let zh=true;
function load(file){const m={exports:{}};const js=ts.transpileModule(fs.readFileSync(path.join(root,'frontend/src/components/workspace',file),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX}}).outputText;
new Function('require','module','exports',js)(name=>name==='./UI'?{useWorkspace:()=>({zh,pick:(a,b)=>zh?a:b})}:name==='./chartLabels'?load('chartLabels.ts'):fr(name),m,m.exports);return m.exports;}
const {ModelChart,companyColors}=load('ModelChart.tsx');
const source={name:'Example',score_label:'Score',price_label:'每项任务成本（美元）',price_label_en:'Cost per task (USD)',source_updated_at:null,checked_at:'2026-10-08',points:[
 {id:'low',name:'A <reviewed> & model',organization:'OpenAI',score:10,price:.001},
 {id:'mid',name:'B model',organization:'Google',score:35,score_low:30,score_high:40,price:.3,estimated:true},
 {id:'high',name:'C model',organization:'Anthropic',score:60,price:8}]};
const points=tree=>tree.root.findAll(n=>n.type==='g'&&n.props['data-model-id']);
const coords=tree=>points(tree).map(n=>{let c=n.findByType('circle'),t=n.findByType('text');return [n.props['data-model-id'],c.props.cx,c.props.cy,c.props.fill,t.props.x,t.props.y,t.children.join('')];});
(async()=>{
 let preview,full,selected;
 await act(async()=>{preview=create(React.createElement(ModelChart,{source}));full=create(React.createElement(ModelChart,{source,onSelect:id=>selected=id}));});
 assert.deepEqual(coords(preview),coords(full));assert.equal(points(preview).length,3);
 assert.equal(preview.root.findByType('svg').props.role,'img');assert(points(preview).every(n=>!n.props.role&&n.props.tabIndex===undefined&&!n.props.onClick));
 assert.equal(full.root.findByType('svg').props.viewBox,'0 0 1400 1200');
 assert.equal(coords(full)[0][3],companyColors.OpenAI);assert.equal(coords(full)[1][3],'white');
 assert.equal(full.root.findAll(n=>n.props.className==='chart-interval').length,1);
 const before=coords(full).find(c=>c[0]==='mid');
 await act(async()=>{full.update(React.createElement(ModelChart,{source,points:[source.points[1]],onSelect:id=>selected=id}));});
 assert.deepEqual(coords(full)[0].slice(1,3),before.slice(1,3));
 const point=points(full)[0];await act(async()=>point.props.onKeyDown({key:'Enter',preventDefault(){}}));assert.equal(selected,'mid');
 zh=false;await act(async()=>preview.update(React.createElement(ModelChart,{source})));
 const text=preview.root.findAllByType('text').map(n=>n.children.join('')).join(' ');
 assert(text.includes('Cost per task (USD)'));assert(text.includes('Not provided by source'));assert(text.includes('2026-10-08'));
 await act(async()=>{preview.unmount();full.unmount();});
 console.log('PASS shared original geometry/labels, source-fixed filtering, company colors/intervals, keyboard selection, non-interactive preview, bilingual units and genuine dates');
})().catch(e=>{console.error(e);process.exitCode=1;});
