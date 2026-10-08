// Reads only the disposable fixture; expected models come from its reviewed API snapshot.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{
 const base=process.env.READING_BASE_URL||'http://127.0.0.1:18059';
 assert.equal(new URL(base).hostname,'127.0.0.1');assert.equal(new URL(base).port,'18059');
 const out=process.env.READING_OUTPUT||'/tmp/fieldtofit-chart-selection';fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:process.env.READING_CHROMIUM||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const context=await browser.newContext({viewport:{width:1440,height:1000},extraHTTPHeaders:{DNT:'1'}});
 const page=await context.newPage(),errors=[],checks=[];page.on('pageerror',e=>errors.push(e.message));
 const panel=page.locator('.landscape-panel'),legend=panel.locator(':scope > .chart-company-legend');
 const mainPlot=panel.locator(':scope > .landscape-plot');
 const companyButton=(scope,name)=>scope.getByRole('button',{name:new RegExp('^'+name+'\\s*\\d')});
 const search=panel.locator(':scope > .chart-search input');
 const all=()=>legend.getByRole('button',{name:'全部公司',exact:true}).click();
 const urlCompanies=()=>new URL(page.url()).searchParams.getAll('company');
 async function visit(path){await page.goto(base+path);await legend.waitFor();}
 function expected(source,names,query=''){
  const matches=p=>(!names.length||names.includes(p.organization))&&p.name.toLowerCase().includes(query.toLowerCase());
  return {points:source.points.filter(matches),missing:source.not_plotted.filter(matches),undated:source.undated.filter(matches)};
 }
 async function verify(source,names,query='',flagship=false){
  const rows=expected(source,names,query);
  if(flagship){const ids=source.flagship.models.map(m=>m.id);for(const key of Object.keys(rows))rows[key]=rows[key].filter(p=>ids.includes(p.id));}
  const ids=rows.points.map(p=>p.id);
  await page.waitForFunction(expected=>JSON.stringify([...document.querySelectorAll('.landscape-panel > .landscape-plot .chart-point')].map(n=>n.dataset.modelId))===JSON.stringify(expected),ids);
  assert.deepEqual(await mainPlot.locator('.chart-model-name').allTextContents(),rows.points.map(p=>p.name));
  const values=panel.locator(':scope > .landscape-data:not(.landscape-coverage) tbody tr th');
  const gaps=panel.locator(':scope > .landscape-coverage tbody tr th');
  const namesOnly=nodes=>nodes.map(n=>n.childNodes[0].textContent);
  assert.deepEqual(await values.evaluateAll(namesOnly),rows.points.map(p=>p.name));
  assert.deepEqual(await gaps.evaluateAll(namesOnly),[...rows.missing,...rows.undated].map(p=>p.name));
  for(const name of snapshot.companies)assert.equal(await companyButton(legend,name).getAttribute('aria-pressed'),String(names.includes(name)));
  return rows;
 }
 let snapshot;
 try{
  snapshot=await (await context.request.get(base+'/api/v1/platform/model-landscape')).json();
  for(const source of snapshot.sources){
   await visit('/for-you?chart='+source.id+'&topic=preserved#model-landscape');await verify(source,[]);
   const coordinates=await mainPlot.locator('.chart-point').evaluateAll(nodes=>Object.fromEntries(nodes.map(n=>{const c=n.querySelector('circle');return [n.dataset.modelId,[c.getAttribute('cx'),c.getAttribute('cy'),c.getAttribute('fill'),c.getAttribute('stroke')]];})));
   // Exercise every selectable company and every cardinality through all twelve groups.
   const chosen=[];
   for(const name of snapshot.companies){await companyButton(legend,name).click();chosen.push(name);await verify(source,chosen);assert.deepEqual(urlCompanies(),chosen);}
   assert.equal(await legend.getByRole('button',{name:'全部公司',exact:true}).getAttribute('aria-pressed'),'false');
   for(const name of [...snapshot.companies].reverse()){await companyButton(legend,name).click();chosen.pop();await verify(source,chosen);}
   assert.equal(await legend.getByRole('button',{name:'全部公司',exact:true}).getAttribute('aria-pressed'),'true');
   assert.deepEqual(urlCompanies(),[]);checks.push(source.id+': all companies and cardinalities 1–12, removal to all');
   for(const pair of [['OpenAI','Anthropic'],['Google','xAI'],['Meta','Kimi'],['GLM','Qwen'],['MIMO','MiniMax'],['DeepSeek','其他'],['OpenAI','其他']]){
    await all();for(const name of pair)await companyButton(legend,name).click();await verify(source,pair);
   }checks.push(source.id+': seven arbitrary pairs, exact point/value/missing/undated unions');
   await all();for(const name of ['DeepSeek','OpenAI','其他'])await companyButton(legend,name).click();
   await verify(source,['OpenAI','DeepSeek','其他']);assert.deepEqual(urlCompanies(),['OpenAI','DeepSeek','其他']);assert.equal(new URL(page.url()).searchParams.get('topic'),'preserved');assert.equal(new URL(page.url()).hash,'#model-landscape');
   const unchanged=await mainPlot.locator('.chart-point').evaluateAll(nodes=>Object.fromEntries(nodes.map(n=>{const c=n.querySelector('circle');return [n.dataset.modelId,[c.getAttribute('cx'),c.getAttribute('cy'),c.getAttribute('fill'),c.getAttribute('stroke')]];})));
   for(const [id,position] of Object.entries(unchanged))assert.deepEqual(position,coordinates[id]);
   await search.fill('DeepSeek');await verify(source,['OpenAI','DeepSeek','其他'],'DeepSeek');
   await search.fill('no-matching-model-REQ-7-6');await verify(source,['OpenAI','DeepSeek','其他'],'no-matching-model-REQ-7-6');await panel.locator(':scope > .landscape-empty').waitFor();
   await page.getByRole('button',{name:'放大查看',exact:true}).click();const dialog=page.getByRole('dialog');await dialog.locator('.landscape-empty').waitFor();
   await dialog.getByRole('searchbox').fill('DeepSeek');await verify(source,['OpenAI','DeepSeek','其他'],'DeepSeek');assert.equal(await search.inputValue(),'DeepSeek');
   await dialog.getByRole('searchbox').fill('');await companyButton(dialog,'Anthropic').click();await verify(source,['OpenAI','Anthropic','DeepSeek','其他']);
   assert.deepEqual(await dialog.locator('.chart-point').evaluateAll(ns=>ns.map(n=>n.dataset.modelId)),expected(source,['OpenAI','Anthropic','DeepSeek','其他']).points.map(p=>p.id));
   await dialog.getByRole('combobox').selectOption('2');assert(await dialog.locator('.landscape-zoom-scroll').evaluate(n=>n.scrollWidth>n.clientWidth));
   await dialog.getByRole('button',{name:'重置筛选',exact:true}).click();await verify(source,[]);assert.deepEqual(urlCompanies(),[]);
   await page.keyboard.press('Escape');assert.equal(await page.evaluate(()=>document.activeElement.textContent),'放大查看');
   for(let attempt=0;attempt<5;attempt++){
    await all();await verify(source,[]);
    await companyButton(legend,'OpenAI').focus();await page.keyboard.press('Space');await companyButton(legend,'Anthropic').focus();await page.keyboard.press('Enter');
    await verify(source,['OpenAI','Anthropic']);
   }checks.push(source.id+': five rapid keyboard pairs preserve both companies');
   await all();await verify(source,[]);
   await companyButton(legend,'OpenAI').focus();await page.keyboard.press('Space');await verify(source,['OpenAI']);await companyButton(legend,'Anthropic').focus();await page.keyboard.press('Enter');await verify(source,['OpenAI','Anthropic']);
   const point=mainPlot.locator('.chart-point').first();await point.focus();await page.keyboard.press('Enter');await panel.locator(':scope > .landscape-point-detail').waitFor();
   await companyButton(legend,'OpenAI').click();await verify(source,['Anthropic']);assert.equal(await panel.locator(':scope > .landscape-point-detail').count(),0);
   await search.fill('no-match');await legend.getByRole('button',{name:/^各家旗舰模型/}).click();assert.equal(await search.inputValue(),'');await verify(source,[], '',true);assert.deepEqual(urlCompanies(),['flagship']);
   await companyButton(legend,'OpenAI').click();await verify(source,['OpenAI']);assert.equal(await panel.locator('.chart-flagship-note').count(),0);
   await companyButton(legend,'Anthropic').click();await page.reload();await legend.waitFor();await verify(source,['OpenAI','Anthropic']);
   await panel.locator(':scope > .landscape-data:not(.landscape-coverage) > summary').click();await panel.locator(':scope > .landscape-coverage > summary').click();
   await page.locator('.model-landscape').screenshot({path:out+'/'+source.id+'-desktop.png'});
   checks.push(source.id+': fixed coordinates/colors, query and empty states, shared modal controls, keyboard, reset, flagships and reload');
  }
  // Legacy, malformed and repeated URL inputs must recover without an empty or false selection.
  const aa=snapshot.sources[0],arena=snapshot.sources[1];
  for(const [params,names,flagship] of [
   ['company=OpenAI',['OpenAI'],false],['company=flagship',[],true],['company=all',[],false],
   ['company=Unknown',[],false],['company=Unknown&company=OpenAI&company=OpenAI',['OpenAI'],false],
   ['company=flagship&company=all&company=Anthropic',['Anthropic'],false],
  ]){await visit('/for-you?chart=artificial-analysis&'+params);await verify(aa,names,'',flagship);}
  await visit('/for-you?company=Anthropic&company=OpenAI');await verify(aa,['OpenAI','Anthropic']);
  await page.getByRole('tab',{name:'Arena',exact:true}).click();await verify(arena,['OpenAI','Anthropic']);
  const shared=page.url();const other=await context.newPage();await other.goto(shared);await other.locator('.landscape-panel > .chart-company-legend').waitFor();
  assert.deepEqual(await other.locator('.landscape-panel > .landscape-plot .chart-point').evaluateAll(ns=>ns.map(n=>n.dataset.modelId)),expected(arena,['OpenAI','Anthropic']).points.map(p=>p.id));await other.close();
  await page.getByRole('tab',{name:'Arena',exact:true}).focus();await page.keyboard.press('ArrowRight');await verify(aa,['OpenAI','Anthropic']);
  checks.push('legacy/malformed/duplicate URLs, source switch by click and keyboard, shared URL in new page');
  for(const width of [390,320])for(const source of snapshot.sources){
   await page.setViewportSize({width,height:844});await visit('/for-you?chart='+source.id+'&company=OpenAI&company=Anthropic#model-landscape');await verify(source,['OpenAI','Anthropic']);
   await companyButton(legend,'Google').click();await verify(source,['OpenAI','Anthropic','Google']);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
   await page.locator('.landscape-tabs').scrollIntoViewIfNeeded();await page.screenshot({path:out+'/'+source.id+'-'+width+'.png'});
   await page.getByRole('button',{name:'放大查看',exact:true}).click();const dialog=page.getByRole('dialog');
   await companyButton(dialog,'其他').click();await verify(source,['OpenAI','Anthropic','Google','其他']);
   await dialog.locator('.landscape-zoom-scroll').evaluate(n=>{n.scrollTop=100;n.scrollLeft=120;});assert(await dialog.locator('.landscape-zoom-scroll').evaluate(n=>n.scrollTop>0&&n.scrollLeft>0));
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await page.screenshot({path:out+'/'+source.id+'-'+width+'-enlarged.png'});
   await dialog.getByRole('button',{name:'关闭',exact:true}).click();await verify(source,['OpenAI','Anthropic','Google','其他']);
   checks.push(source.id+': '+width+'px selection, modal pan/sync, no page overflow');
  }
  for(const dark of [false,true]){
   await page.evaluate(dark=>{localStorage.setItem('fieldtofit-workspace-zh','false');localStorage.setItem('fieldtofit-workspace-dark',JSON.stringify(dark));},dark);
   await visit('/for-you?chart=arena&company=OpenAI&company='+encodeURIComponent('其他'));
   assert.equal(await page.getByRole('button',{name:/^Other\s*\d/}).first().getAttribute('aria-pressed'),'true');
   assert.equal(await page.locator('html').getAttribute('data-theme'),dark?'dark':'light');assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
   await page.locator('.landscape-tabs').scrollIntoViewIfNeeded();
   await page.screenshot({path:out+'/arena-320-en-'+(dark?'dark':'light')+'.png'});
  }checks.push('English/light/dark at 320px');
  assert.deepEqual(await (await context.request.get(base+'/api/v1/platform/model-landscape')).json(),snapshot);
  const health=await (await context.request.get(base+'/api/health')).json();assert.equal(health.version,process.env.EXPECTED_VERSION||'v1.8.10');
  assert.deepEqual(errors,[]);fs.writeFileSync(out+'/results.json',JSON.stringify({passed:true,version:health.version,checks,errors,coverage:snapshot.sources.map(s=>({source:s.id,points:s.points.length,missing:s.not_plotted.length,undated:s.undated.length}))},null,2));console.log(JSON.stringify({passed:true,checks,errors,output:out}));
 }catch(error){
  console.error(JSON.stringify({url:page.url(),selected:await legend.locator('[aria-pressed="true"]').allTextContents(),focus:await page.evaluate(()=>document.activeElement?.textContent),completed:checks}));
  await page.screenshot({path:out+'/failure.png'});throw error;
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
