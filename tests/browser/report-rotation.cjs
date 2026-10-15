const {chromium}=require(process.env.PLAYWRIGHT_PATH||'/Users/kevin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('node:fs'),assert=require('node:assert/strict');
const base=process.env.CHECK_BASE||'http://127.0.0.1:18116';assert.equal(new URL(base).hostname,'127.0.0.1','Synthetic publications are local-only');
const out=process.env.OUTPUT||'/Users/kevin/fieldtofit/output/operations/report-rotation-2026-10-15/browser';fs.mkdirSync(out,{recursive:true});
(async()=>{
 const b=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--no-proxy-server']});const results=[],errors=[];
 const request=await b.newContext();
 async function api(path,body,method='GET') {const r=await request.request.fetch(base+path,{method,data:body,headers:{'X-Admin-Password':'rotation-local-only'}});const d=await r.json();assert.ok(r.ok(),path+' '+JSON.stringify(d));return d;}
 async function reading(lang){return api('/api/v1/platform/maps?lang='+lang);}
 async function verify(lang,width,label){
  const c=await b.newContext({viewport:{width,height:1000},hasTouch:width<600,reducedMotion:'reduce'}),p=await c.newPage();p.on('pageerror',e=>errors.push(e.message));const prefix=lang==='en'?'/en':'';
  const data=await reading(lang),selected=data.report_selection.ids,expected=data.items.filter(m=>selected.includes(m.id));assert.equal(selected.length,4);
  await p.goto(base+prefix+'/for-you');const section=p.locator('.technical-maps:visible').first();await section.locator('h4').first().waitFor();await section.scrollIntoViewIfNeeded();
  assert.deepEqual(await section.locator('h4 a').evaluateAll(es=>es.map(e=>e.getAttribute('href'))),expected.map(m=>m.path));assert.equal(await section.locator('.map-cards>article').count(),4);
  assert.equal(await section.getByText(lang==='zh'?'精选原始报告，读懂核心结论、证据和适用边界。':'Read selected original reports for their core findings, evidence and limits.',{exact:true}).count(),1);
  for(const im of await section.locator('.map-card-figure img').all()){await im.scrollIntoViewIfNeeded();await im.evaluate(e=>e.decode());assert.ok(await im.evaluate(e=>e.naturalWidth>0));}assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await section.screenshot({path:out+'/'+label+'-'+lang+'-'+width+'-home.png'});
  await section.getByRole('link',{name:lang==='zh'?'全部精选与历史索引 →':'All reports and history →',exact:true}).click();
  const cards=p.locator('.maps-page:visible .map-cards>article');await cards.last().waitFor();assert.equal(await cards.count(),data.total);
  assert.deepEqual(await cards.locator('h2 a').evaluateAll(es=>es.map(e=>e.getAttribute('href'))),data.items.map(m=>m.path));assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await p.screenshot({path:out+'/'+label+'-'+lang+'-'+width+'-index.png'});
  results.push({label,lang,width,homepage:4,index:data.total,same_order:true,overflow:false,ids:selected});await c.close();
 }
 async function publishCopy(template,identity,title,summary){
  const path='/api/v1/admin/workspace/content/news/'+identity;const current=await api(path);const draft=structuredClone(template.draft);draft.id=identity;draft.title=title;draft.summary=summary;
  if(identity!==template.id){draft.name='Isolated report rotation verification';draft.technical_map.slug='isolated-browser-rotation';draft.technical_map.question='Isolated browser rotation verification';}
  let d=await api(path,{draft,draft_version:current.draft_version,materials_fingerprint:current.materials_fingerprint},'PATCH');const fields=Object.fromEntries(Object.entries(d.english.fields).map(([source,value])=>[source,value||template.english.fields[source]]));assert.ok(Object.values(fields).every(Boolean),'Reuse only already-reviewed identical source strings');
  d=await api(path+'/english-review',{draft_version:d.draft_version,source_hash:d.english.source_hash,fields,confirmed:true,reason:'Local-only reuse of already reviewed translations for unchanged source text.'},'POST');
  const preview=await api(path+'/preview',{},'POST');assert.ok(preview.ready,JSON.stringify(preview.errors));
  const review={draft_version:preview.draft_version,review_token:preview.review_token};await api(path+'/submit-review',review,'POST');return api(path+'/publish',{...review,confirmed:true,reason:'Isolated browser verification only; no production publication.'},'POST');
 }
 try{
  for(const lang of ['zh','en'])for(const width of [1440,390,320])await verify(lang,width,'baseline');
  const before=await reading('zh'),template=await api('/api/v1/admin/workspace/content/news/D-153');
  const candidate=await api('/api/v1/admin/workspace/inbox',{title:'Isolated browser rotation verification',url:'https://example.org/isolated-report-rotation-'+Date.now(),summary:'Local synthetic publication fixture',source:'local verification',type:'paper'},'POST');
  const selected=await api('/api/v1/admin/workspace/select',{ref:candidate.ref,action:'select',kind:'news',type:'tool',note:'Local-only fixture'},'POST');
  const result=await publishCopy(template,selected.id,'Isolated new report for browser verification','Local-only verification of the four-report window.');
  assert.deepEqual(result.report_rotation.entered.map(i=>i.id),[selected.id]);const evicted=before.report_selection.ids.at(-1);assert.deepEqual(result.report_rotation.index_only.map(i=>i.id),[evicted]);
  await verify('zh',390,'published');await verify('en',1440,'published');
  const all=await reading('zh');assert.equal(all.total,before.total+1);assert.deepEqual(all.report_selection.ids,[selected.id,...before.report_selection.ids.slice(0,3)]);
  const old=await api('/api/v1/admin/workspace/content/news/'+evicted);const corrected=await publishCopy(old,evicted,old.draft.title,'Isolated copy clarification does not promote this older report.');assert.equal(corrected.report_rotation.changed,false);assert.deepEqual((await reading('zh')).report_selection.ids,all.report_selection.ids);
  const retained=await request.request.get(base+result.report_rotation.index_only[0].url);assert.equal(retained.status(),200);
  await verify('zh',320,'copy-correction');assert.deepEqual(errors,[]);
  fs.writeFileSync(out+'/results.json',JSON.stringify({passed:true,results,errors,new_report:selected.id,evicted,copy_correction_does_not_promote:true,old_report_retained:true,production_writes:false},null,2));console.log('Verified',results.length,'local browser scenarios, real isolated publication and non-promoting copy correction.');
 }finally{await request.close();await b.close();}
})().catch(e=>{console.error(e);process.exit(1)});
