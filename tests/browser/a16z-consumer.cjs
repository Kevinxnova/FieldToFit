const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{
 const base=process.env.READING_BASE||'http://127.0.0.1:18059',out=process.env.READING_OUTPUT||'/tmp/fieldtofit-consumer-browser';fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'}),checks=[],errors=[];
 try{
  for(const [width,lang,dark] of [[1440,'zh',false],[390,'zh',false],[320,'zh',false],[390,'zh',true],[1440,'en',false],[320,'en',false]]){
   const c=await browser.newContext({viewport:{width,height:950},hasTouch:width<600,permissions:['clipboard-read','clipboard-write'],extraHTTPHeaders:{DNT:'1'}}),p=await c.newPage();p.on('pageerror',e=>errors.push(e.message));
   await p.addInitScript(({lang,dark})=>{localStorage.setItem('fieldtofit-workspace-dark',JSON.stringify(dark));localStorage.setItem('fieldtofit-workspace-zh',JSON.stringify(lang==='zh'));},{lang,dark});
   await p.goto(base+'/maps/consumer-ai-spending');const reading=p.locator('.map-report-reading').first();await reading.locator('.map-core-findings').waitFor();assert.equal(await p.locator('html').getAttribute('lang'),lang==='zh'?'zh-CN':'en');
   const api=(await (await p.request.get(base+'/api/v1/platform/maps?slug=consumer-ai-spending')).json()).items[0];
   assert.equal(api.reports[0].first_published_at,'2026-10-05');assert.equal(await reading.locator('.map-core-findings>li').count(),4);assert.equal(await reading.locator('.map-report-argument').count(),4);
   assert.equal(await p.locator('.map-overview .map-node').count(),3);assert.equal(await p.locator('.map-overview .map-graph svg path').count(),2);assert.ok(api.edges.every(e=>e.relation==='parallel'));
   const title=await p.locator('.platform-hero h1').evaluate(e=>({align:getComputedStyle(e.parentElement).textAlign,size:parseFloat(getComputedStyle(e).fontSize)}));assert.equal(title.align,'center');assert.ok(title.size>=28);
   assert.match(await p.locator('.map-heading-dates').textContent(),/2026-10-05.*2026年8月/);await p.screenshot({path:out+`/title-${width}-${lang}-${dark?'dark':'light'}.png`});
   const before=await reading.textContent();await p.locator('.map-overview .map-node').last().click();assert.equal(await reading.textContent(),before);
   for(let i=0;i<4;i++){
    const f=api.reading.findings[i],section=reading.locator('#argument-'+f.id);assert.equal(await section.locator('h3').textContent(),`${i+1}. ${f.title}`);
    await reading.locator('.map-core-findings>li').nth(i).locator('a').first().click();assert.ok(await section.evaluate(e=>Math.abs(e.getBoundingClientRect().top-90)<6));
    await section.locator('nav a').first().click();assert.equal(await p.evaluate(()=>location.hash),'#finding-'+f.id);
    const img=section.locator('.map-report-figure img');await img.scrollIntoViewIfNeeded();await img.evaluate(e=>e.decode());assert.equal(await img.evaluate(e=>e.naturalWidth),1500);
    assert.match(await section.locator('figcaption').textContent(),/本站重绘/);assert.equal(await section.locator('.map-report-highlight').count(),1);
    await section.screenshot({path:out+`/argument-${i+1}-${width}-${lang}-${dark?'dark':'light'}.png`});
   }
   const button=reading.locator('figcaption button').first();await button.focus();await p.keyboard.press('Enter');await p.locator('dialog[open]').waitFor();assert.equal(await p.locator('dialog[open] img').evaluate(e=>e.naturalWidth),1500);
   assert.match(await p.locator('dialog[open]').textContent(),/本站重绘/);await p.screenshot({path:out+`/zoom-${width}-${lang}-${dark?'dark':'light'}.png`});await p.keyboard.press('Escape');await p.locator('.map-figure-dialog').waitFor({state:'detached'});assert.ok(await button.evaluate(e=>document.activeElement===e));
   assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));assert.equal(await reading.locator('figcaption a[href="https://a16z.com/100-gen-ai-apps-7/"]').count(),4);
   await p.locator('.platform-actions button').nth(1).click();assert.deepEqual(JSON.parse(await p.locator('.maps-page details textarea').inputValue()).map,api);
   await p.goto(base+'/maps/consumer-ai-spending#argument-ranking-gap');await reading.locator('#argument-ranking-gap').waitFor();await p.waitForTimeout(100);assert.ok(await reading.locator('#argument-ranking-gap').evaluate(e=>Math.abs(e.getBoundingClientRect().top-90)<10));
   await p.goto(base+'/for-you');const thumb=p.locator('a[href="/maps/consumer-ai-spending"] img');await thumb.waitFor();await thumb.scrollIntoViewIfNeeded();await thumb.evaluate(e=>e.decode());await p.locator('#technical-evolution-maps').scrollIntoViewIfNeeded();await p.screenshot({path:out+`/entry-${width}-${lang}-${dark?'dark':'light'}.png`});assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
   await p.goto(base+'/maps');await p.locator('.map-cards a[href="/maps/consumer-ai-spending"]').first().waitFor();
   await p.goto(base+'/maps/agent-context-cost');await p.locator('.map-node').first().waitFor();assert.equal(await p.locator('.map-report-reading').count(),0);
   checks.push({width,lang,dark,findings:4,figures:4,passed:true});console.log(JSON.stringify({checked:{width,lang,dark}}));await c.close();
  }
  assert.deepEqual(errors,[]);const result={passed:true,checks,errors};fs.writeFileSync(out+'/results.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
