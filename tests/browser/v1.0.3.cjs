const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.READING_CHROMIUM});
 try{
  const base=process.env.READING_BASE_URL||'http://127.0.0.1:18005',out=process.env.READING_OUTPUT||'/tmp/fieldtofit-v103';fs.mkdirSync(out,{recursive:true});
  const context=await browser.newContext({viewport:{width:1440,height:1100}}),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  const snapshot=await(await context.request.get(base+'/api/v1/platform/model-landscape')).json();
  const plot=page.locator('.landscape-plot');
  const waitPoints=n=>page.waitForFunction(expected=>document.querySelectorAll('.landscape-plot .chart-point').length===expected,n);
  await page.goto(base+'/for-you?chart=epoch');await plot.locator('.chart-point').first().waitFor();
  assert.equal(await page.getByRole('tab').count(),2);assert.equal(await page.getByRole('tab',{name:'Artificial Analysis',exact:true}).getAttribute('aria-selected'),'true');assert.equal(await page.getByText('Epoch AI',{exact:true}).count(),0);
  assert.equal(await page.locator('.chart-company-legend button').count(),14);
  const colors=[];
  for(const source of snapshot.sources){
   await page.getByRole('tab',{name:source.name,exact:true}).click();await page.waitForFunction(id=>document.querySelector('#chart-tab-'+id)?.getAttribute('aria-selected')==='true',source.id);
   const names=await plot.locator('.chart-model-name').allTextContents();assert.deepEqual(names,source.points.map(p=>p.name));
   assert.equal(await plot.locator('.chart-point').count(),source.points.length);
   assert.equal(await page.locator('[data-source-date]').textContent(),source.source_updated_at||'来源未标注');
   const overlap=await plot.locator('.chart-model-name').evaluateAll(nodes=>{let count=0;const boxes=nodes.map(n=>n.getBBox());for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++){const a=boxes[i],b=boxes[j];if(a.x<b.x+b.width&&a.x+a.width>b.x&&a.y<b.y+b.height&&a.y+a.height>b.y)count++;}return count;});assert.equal(overlap,0,'Model labels overlap');
   colors.push(await page.locator('.chart-company-legend i').evaluateAll(ns=>ns.map(n=>n.style.background)));
   const p=source.points.find(p=>p.organization==='DeepSeek');const dot=plot.locator(`[data-model-id="${p.id}"] circle`);const position=[await dot.getAttribute('cx'),await dot.getAttribute('cy')];
   await page.locator('.chart-company-legend button').filter({hasText:'DeepSeek'}).click();await waitPoints(source.points.filter(p=>p.organization==='DeepSeek').length);assert.equal(await plot.locator('.chart-point').count(),source.points.filter(p=>p.organization==='DeepSeek').length);assert.deepEqual([await dot.getAttribute('cx'),await dot.getAttribute('cy')],position);
   await plot.locator(`[data-model-id="${p.id}"]`).focus();await page.keyboard.press('Enter');assert.match(await page.locator('.landscape-panel > .landscape-point-detail').textContent(),new RegExp(p.name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));
   await page.getByRole('searchbox').fill('no-such-model-2026');await page.locator('.landscape-empty').waitFor();assert.equal(await plot.count(),0);
   await page.getByRole('button',{name:'重置筛选',exact:true}).click();await waitPoints(source.points.length);assert.equal(await plot.locator('.chart-point').count(),source.points.length);
   await page.locator('.model-landscape').screenshot({path:out+'/'+source.id+'.png'});
   await page.locator('.landscape-coverage > summary').click();assert.equal(await page.locator('.landscape-coverage tbody tr').count(),source.not_plotted.length+source.undated.length);await page.locator('.landscape-coverage > summary').click();
  }
  await page.getByRole('button',{name:/^各家旗舰模型/}).click();
  await waitPoints(8);assert.equal(await plot.locator('.chart-point').count(),8);assert(page.url().includes('company=flagship'));
  await page.getByText('查看旗舰名单与缺项',{exact:true}).click();assert.equal(await page.locator('.chart-flagship-note li').count(),11);assert.match(await page.locator('.chart-flagship-note').textContent(),/暂未绘制/);
  await page.getByRole('tab',{name:'Artificial Analysis',exact:true}).click();await page.waitForFunction(()=>document.querySelectorAll('.landscape-plot .chart-point').length===11);
  assert.equal(await page.getByRole('button',{name:/^各家旗舰模型/}).getAttribute('aria-pressed'),'true');
  assert.deepEqual((await plot.locator('.chart-model-name').allTextContents()).sort(),snapshot.sources[0].points.filter(p=>snapshot.sources[0].flagship.models.some(m=>m.id===p.id)).map(p=>p.name).sort());
  await page.reload();await plot.locator('.chart-point').first().waitFor();assert.equal(await plot.locator('.chart-point').count(),11);
  await page.getByRole('searchbox').fill('GPT-5.6');await page.locator('.landscape-empty').waitFor();assert.equal(await plot.count(),0);
  await page.getByRole('button',{name:'重置筛选',exact:true}).click();await waitPoints(107);assert.equal(await plot.locator('.chart-point').count(),107);
  await page.getByRole('button',{name:/^各家旗舰模型/}).click();await waitPoints(11);await page.locator('.model-landscape').screenshot({path:out+'/flagships.png'});
  await page.getByRole('button',{name:'重置筛选',exact:true}).click();await page.getByRole('tab',{name:'Arena',exact:true}).click();
  assert.deepEqual(colors[0],colors[1]);assert.equal(new Set(colors[0]).size,12);
  await page.getByRole('tab',{name:'Arena',exact:true}).focus();await page.keyboard.press('ArrowRight');await page.waitForFunction(()=>document.querySelector('#chart-tab-artificial-analysis')?.getAttribute('aria-selected')==='true');assert.equal(await page.getByRole('tab',{name:'Artificial Analysis',exact:true}).getAttribute('aria-selected'),'true');await page.keyboard.press('End');await page.waitForURL('**/*chart=arena*');assert(page.url().includes('chart=arena'));await page.reload();await plot.locator('.chart-point').first().waitFor();assert.equal(await page.getByRole('tab',{name:'Arena',exact:true}).getAttribute('aria-selected'),'true');
  await page.getByText('如何理解这两个来源？',{exact:true}).click();assert.equal(await page.locator('.landscape-explanation li').count(),4);
  await page.getByRole('button',{name:'放大查看',exact:true}).click();const dialog=page.locator('dialog');assert(await dialog.isVisible());await dialog.getByRole('combobox').selectOption('2');assert(await dialog.locator('.landscape-zoom-scroll').evaluate(n=>n.scrollWidth>n.clientWidth));await page.keyboard.press('Escape');assert(!(await dialog.isVisible()));assert.equal(await page.evaluate(()=>document.activeElement.textContent),'放大查看');
  await page.setViewportSize({width:390,height:844});await page.goto(base+'/for-you?chart=arena#model-landscape');await plot.locator('.chart-point').first().waitFor();assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.locator('.landscape-tabs').scrollIntoViewIfNeeded();await page.screenshot({path:out+'/mobile-arena.png'});
  await page.getByRole('button',{name:'放大查看',exact:true}).click();assert(await dialog.locator('.landscape-zoom-scroll').evaluate(n=>n.scrollWidth>n.clientWidth));await dialog.locator('.landscape-zoom-scroll').evaluate(n=>{n.scrollTop=100;n.scrollLeft=120;});assert(await dialog.locator('.landscape-zoom-scroll').evaluate(n=>n.scrollTop>0&&n.scrollLeft>0));await page.screenshot({path:out+'/mobile-enlarged.png'});await dialog.getByRole('button',{name:'关闭',exact:true}).click();
  const health=await(await context.request.get(base+'/api/health')).json();assert.equal(health.version,'v1.0.3');await page.goto(base+'/about');assert.match(await page.locator('.platform-eyebrow').first().textContent(),/v1\.0\.3/);
  await page.route('**/api/v1/platform/model-landscape',r=>r.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:'unavailable'})}));await page.goto(base+'/for-you');await page.getByText('图表暂时无法读取，近期动态仍可继续阅读。',{exact:true}).waitFor();await page.locator('.news-card').last().waitFor();assert.equal(await page.locator('.news-card').count(),10);assert.equal(await page.locator('.watch-card').count(),27);
  assert.deepEqual(errors,[]);fs.writeFileSync(out+'/result.json',JSON.stringify({passed:true,base,version:health.version,checks:['flagship 11/8 points / explicit 3 gaps / source switch / URL refresh / search / reset','two sources / Epoch URL fallback','190 exact source model labels / no overlaps','12 consistent company colors','fixed coordinates during filters / search / empty / reset','keyboard tabs / URL reload / point evidence','coverage lists / genuine dates','zoom / Escape focus / mobile pan / no page overflow','about and health version','chart failure preserves news and watch'],coverage:snapshot.sources.map(s=>({source:s.id,...s.coverage}))},null,2));console.log('v1.0.3 browser acceptance passed');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
