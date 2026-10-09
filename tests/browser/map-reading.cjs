const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright'),assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{
 const base=process.env.READING_BASE||'http://127.0.0.1:18059',out=process.env.READING_OUTPUT||'/tmp/fieldtofit-reading-browser';fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'}),checks=[],errors=[];
 try{
  for(const [width,dark] of [[1440,false],[390,false],[320,false],[390,true]]){
   const c=await browser.newContext({viewport:{width,height:950},hasTouch:width<600,permissions:['clipboard-read','clipboard-write'],extraHTTPHeaders:{DNT:'1'}});const p=await c.newPage();p.on('pageerror',e=>errors.push(e.message));
   await p.addInitScript(d=>localStorage.setItem('fieldtofit-workspace-dark',JSON.stringify(d)),dark);
   await p.goto(base+'/maps/reusable-agent-artifacts');const reading=p.locator('.map-report-reading').first();await reading.locator('.map-core-findings').waitFor();
   const api=(await (await p.request.get(base+'/api/v1/platform/maps?slug=reusable-agent-artifacts')).json()).items[0];
   assert.equal(await reading.locator('.map-core-findings>li').count(),4);assert.equal(await reading.locator('.map-report-argument').count(),4);
   assert.equal(await p.locator('.map-graph svg path').first().isVisible(),true);
   const title=await p.locator('.platform-hero h1').evaluate(e=>({align:getComputedStyle(e.parentElement).textAlign,size:parseFloat(getComputedStyle(e).fontSize)}));assert.ok((await p.locator('.map-heading-dates').textContent()).includes('2026-10-06'));assert.equal(title.align,'center');assert.ok(title.size>=28);
   await p.screenshot({path:out+`/title-${width}-${dark?'dark':'light'}.png`});const text=await reading.textContent();const node=p.locator('.map-overview .map-node').last();await node.scrollIntoViewIfNeeded();const y=await p.evaluate(()=>scrollY);await node.click();assert.equal(await reading.textContent(),text);assert.ok(Math.abs(await p.evaluate(()=>scrollY)-y)<100,'node selection must not jump to report');
   for(let i=0;i<4;i++){
    const f=api.reading.findings[i],section=reading.locator('#argument-'+f.id);assert.equal(await section.locator('h3').textContent(),`${i+1}. ${f.title}`);
    await reading.locator('.map-core-findings>li').nth(i).locator('a').first().click();assert.ok(await section.evaluate(e=>Math.abs(e.getBoundingClientRect().top-90)<5));
    await section.getByRole('link',{name:/^回到这条结论/}).click();assert.equal(await p.evaluate(()=>location.hash),'#finding-'+f.id);
   }
   await reading.locator('#argument-point-4').getByRole('link',{name:/^回到路线全貌/}).click();assert.equal(await p.locator('.map-overview .map-node[aria-pressed="true"]').getAttribute('class'),'map-node method');const images=reading.locator('.map-report-figure img');assert.equal(await images.count(),4);for(const img of await images.all()){await img.scrollIntoViewIfNeeded();await img.evaluate(e=>e.decode());assert.equal(await img.evaluate(e=>e.naturalWidth),778);}
   const button=reading.getByRole('button',{name:'放大原图',exact:true}).first();await button.focus();await p.keyboard.press('Enter');await p.locator('dialog[open]').waitFor();assert.equal(await p.locator('dialog[open] img').evaluate(e=>e.naturalWidth),778);await p.keyboard.press('Escape');assert.equal(await p.locator('dialog[open]').count(),0);await p.locator('.map-figure-dialog').waitFor({state:'detached'});assert.equal(await button.evaluate(e=>document.activeElement===e),true);
   await reading.locator('#argument-point-2').scrollIntoViewIfNeeded();await p.screenshot({path:out+`/argument-2-${width}-${dark?'dark':'light'}.png`});const original=reading.locator('a[href="https://arxiv.org/pdf/2610.08775v1#page=6"]');assert.equal(await original.count(),1);
   assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await p.locator('#report-findings').scrollIntoViewIfNeeded();await p.screenshot({path:out+`/reading-${width}-${dark?'dark':'light'}.png`});
   await p.getByRole('button',{name:'把地图交给 AI',exact:true}).click();assert.deepEqual(JSON.parse(await p.evaluate(()=>navigator.clipboard.readText())).map,api);
   await p.goto(base+'/maps/reusable-agent-artifacts#argument-point-4');await reading.locator('#argument-point-4').waitFor();await p.waitForTimeout(100);assert.ok(await reading.locator('#argument-point-4').evaluate(e=>Math.abs(e.getBoundingClientRect().top-90)<10));
   await p.goto(base+'/maps/agent-context-cost');await p.locator('.map-node').first().waitFor();assert.equal(await p.locator('.map-report-reading').count(),0);assert.ok(await p.locator('.map-graph svg path').first().isVisible());
   await p.goto(base+'/for-you');await p.locator('#technical-evolution-maps').waitFor();await p.locator('#technical-evolution-maps').scrollIntoViewIfNeeded();const thumbnail=p.locator('a[href="/maps/reusable-agent-artifacts"] img');await thumbnail.waitFor();await thumbnail.evaluate(e=>e.decode());assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
   checks.push(`title/findings/arguments/route/zoom/keyboard/source/deep-link/AI/old-map/entry ${width} ${dark?'dark':'light'}`);await c.close();
  }
  if(!process.env.READING_BASE){
   const c=await browser.newContext({viewport:{width:390,height:950}}),p=await c.newPage();p.on('pageerror',e=>errors.push(e.message));await p.goto(base+'/admin');await p.locator('.management-login input').fill('reading-fixture-only');await p.locator('.management-login button').last().click();await p.getByRole('button',{name:'内容库',exact:true}).click();await p.getByLabel('查找内容').fill('百万次重复判断');await p.locator('.management-library-item').first().click();const editTitle='浏览器验证：核心结论 '+Date.now();await p.getByLabel('报告阅读标题',{exact:true}).fill(editTitle);await p.getByRole('button',{name:'保存草稿',exact:true}).click();await p.getByText('草稿已保存，网站内容未改变。',{exact:true}).waitFor();const api=await (await p.request.get(base+'/api/v1/platform/maps?slug=reusable-agent-artifacts')).json();assert.equal(api.items[0].reading.title,'这份报告的核心观点');await p.getByRole('button',{name:'生成双端预览',exact:true}).click();await p.locator('.management-preview').getByText(editTitle,{exact:true}).waitFor();assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));checks.push('mobile editor saves private reading and renders reviewed preview');await c.close();
  }
  assert.deepEqual(errors,[]);fs.writeFileSync(out+'/results.json',JSON.stringify({passed:true,checks,errors},null,2));console.log(JSON.stringify({passed:true,checks,errors}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
