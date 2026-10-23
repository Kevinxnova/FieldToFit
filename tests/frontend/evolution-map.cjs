/** Actual maps: identity-safe comparison, sourced edges, keyboard/focus and legacy URLs. */
const assert=require('node:assert/strict');
const {React,rr,create,act,state,session,load,mock,raw}=require('./evolution-harness.cjs');
const layout=load('frontend/src/features/evolution/atlasLayout.ts'),f=load('frontend/src/features/evolution/flagships.ts');
const {AtlasMap}=load('frontend/src/features/evolution/AtlasMap.tsx');
let renderer,location;function App(){location=rr.useLocation();return React.createElement(AtlasMap,{navigation:null,footer:null});}
const root=()=>renderer.root,track=id=>root().findByProps({id:'track-'+id});
const nodes=()=>root().findAllByType('button').filter(b=>b.props['data-node']);
const button=(id,name)=>track(id).findAllByType('button').find(b=>b.props.children===name);
(async()=>{
 for(const all of [true,false])for(const t of raw.tracks){const graph=layout.buildAtlas(t.id,all);assert.equal(graph.models.length,25);for(const [i,a]of graph.items.entries()){
  assert(a.rect.x>=0&&a.rect.y>=0&&a.rect.x+a.rect.width<graph.modelX&&a.rect.y+a.rect.height<=graph.height);
  for(const b of graph.items.slice(i+1))assert(a.rect.x+a.rect.width<=b.rect.x||b.rect.x+b.rect.width<=a.rect.x||a.rect.y+a.rect.height<=b.rect.y||b.rect.y+b.rect.height<=a.rect.y,'overlap');
 }for(const e of raw.flagships.adoptions.filter(e=>e.track===t.id))assert(graph.byId[e.node],'adoption source missing from graph');}
 assert.deepEqual(f.validModels('bad,__proto__,constructor,toString,argon,argon,gpt6-astra,opus55'),['argon','gpt6-astra']);
 assert(f.compareModels('argon','gpt6-astra','train').common.includes('reasoning_rl-o1'));
 assert.equal(f.modelEdges('minimax31').length,0);
 session.set('fieldtofit:evolution:atlas-view:v2','{broken');
 await act(async()=>renderer=create(React.createElement(rr.MemoryRouter,{initialEntries:['/for-you/evolution?period=recent&track=systems&node=latent_kv-v3']},React.createElement(App)),{createNodeMock:mock}));
 await act(async()=>new Promise(r=>setTimeout(r,15)));
 assert.equal(new Set(nodes().map(n=>n.props['data-node'])).size,raw.routes.flatMap(r=>r.nodes).length);
 assert.equal(nodes().find(n=>n.props['data-node']==='latent_kv-v3').props['aria-expanded'],true);assert.equal(state.focused,'latent_kv-v3');
 await act(async()=>button('inference','全屏').props.onClick());assert.equal(document.body.style.overflow,'hidden');
 await act(async()=>button('inference','退出全屏').props.onClick());assert.equal(document.body.style.overflow,'');
 await act(async()=>track('inference').findByProps({'aria-label':'关闭节点详情'}).props.onClick());
 await act(async()=>root().findByProps({'aria-label':'查看型号'}).props.onChange({target:{value:'argon'}}));
 await act(async()=>root().findByProps({'aria-label':'对比型号'}).props.onChange({target:{value:'gpt6-astra'}}));
 assert.equal(new URLSearchParams(location.search).get('evolution_models'),'argon,gpt6-astra');
 assert.equal(root().findAllByProps({className:'flagship-comparison'}).length,1);
 assert.equal(root().findAllByType('path').filter(p=>p.props['data-adoption']).length,5);
 const before=nodes().length;await act(async()=>button('train','收起次要节点').props.onClick());assert(nodes().length<before);
 await act(async()=>button('train','展开全部节点').props.onClick());assert.equal(nodes().length,before);
 // A shared cross-map node opens exactly one inspector in its selected map.
 const projected=track('systems').findByProps({'data-node':'context-csa2'});
 await act(async()=>projected.props.onClick());await act(async()=>new Promise(r=>setTimeout(r,10)));
 assert.equal(new URLSearchParams(location.search).get('evolution_map'),'systems');assert.equal(root().findAllByType('aside').length,1);
 assert.equal(root().findAllByProps({'aria-label':'关闭节点详情'}).length,1);
 state.denied=true;await act(async()=>button('systems','适合阅读').props.onClick());state.denied=false;
 await act(async()=>root().findAllByType('button').find(b=>b.props.children==='清除选择').props.onClick());assert.equal(root().findAllByType('path').filter(p=>p.props['data-adoption']).length,0);
 await act(async()=>renderer.unmount());assert.equal(document.body.style.overflow,'');
 await act(async()=>renderer=create(React.createElement(rr.MemoryRouter,{initialEntries:['/for-you/evolution?node=constructor&evolution_models=__proto__']},React.createElement(App)),{createNodeMock:mock}));
 assert.equal(root().findAllByType('aside').length,0);assert(root().findAllByProps({role:'status'}).length);
 await act(async()=>renderer.unmount());
 console.log('PASS flagship maps: all nodes, key view, non-overlap, 25 endpoints per map, exact evidence, comparison, legacy URLs, focus, full screen, cross-map detail, blocked storage');
})().catch(e=>{console.error(e);process.exitCode=1});
