// Built application against an isolated fixture; never targets production by default.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),crypto=require('node:crypto');
const base=process.env.READING_BASE_URL||'http://127.0.0.1:18078';
const out=process.env.READING_OUTPUT||'output/daily-v1.18-validation';fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.READING_CHROMIUM||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 try{
  const ctx=await browser.newContext(),p=await ctx.newPage(),errors=[],checks=[];
  p.on('pageerror',e=>errors.push(e.message));await p.route('https://**/*',r=>r.abort());
  for(const lang of ['zh','en']){
   const prefix=lang==='en'?'/en':'',data=await (await ctx.request.get(base+'/api/v1/daily/latest?lang='+lang)).json();
   const stories=data.stories,companies=stories.filter(s=>s.section==='companies');
   for(const width of [1440,1024,390,320]){
    await p.setViewportSize({width,height:1000});await p.goto(base+prefix+'/for-you');await p.locator('.dp-story').last().waitFor();
    assert.equal(await p.locator('.dp-lead,.dp-intro').count(),0);
    const highlights=stories.filter(s=>s.highlight);
    assert.equal(await p.locator('.dp-story').count(),highlights.length);
    for(const s of highlights)assert((await p.locator('.daily-preview').innerText()).includes(s.highlight_title));
    assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await p.locator('.daily-preview').screenshot({path:`${out}/home-${lang}-${width}.png`});
    await p.locator('.dp-story h4 a').first().click();
    await p.waitForFunction(id=>document.activeElement?.id==='daily-story-'+id,highlights[0].id);
    assert.equal(await p.locator('.dj-story').count(),stories.length);
    assert.equal(await p.locator('#daily-companies .dj-story').count(),companies.length);
    assert.equal(await p.locator('.dj-intro,.dj-analysis').count(),0);
    assert.equal(await p.locator('.dj-market-table tbody tr').count(),30);
    assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    const boxes=await p.locator('#daily-companies .dj-story').evaluateAll(es=>es.map(e=>({x:e.getBoundingClientRect().x,b:e.getBoundingClientRect().bottom,t:e.getBoundingClientRect().top})));
    assert(boxes.every((b,i)=>!i||(Math.abs(b.x-boxes[0].x)<2&&b.t>=boxes[i-1].b)));
    if(lang==='en')assert(!/[\u3400-\u9fff]/.test(await p.locator('.daily-journal').innerText()));
    await p.locator('.daily-journal').screenshot({path:`${out}/daily-${lang}-${width}.png`});
    checks.push(`${lang}-${width}: highlights, anchor, single column, all stories, 30 quotes, no overflow`);
   }
   const pending=p.waitForEvent('download');await p.locator('.dj-download').click();const download=await pending;
   const downloaded=await download.path();assert.equal(crypto.createHash('sha256').update(fs.readFileSync(downloaded)).digest('hex'),data.pdf[lang].sha256);
   checks.push(`${lang}: actual PDF download hash matches publication`);
   await p.locator('.dj-download').focus();await p.keyboard.press('Tab');assert(await p.evaluate(()=>document.activeElement?.tagName==='A'));
   await p.locator('.dj-market-tabs button').last().click();assert.equal(await p.locator('.dj-market-table tbody tr').count(),2);
   await p.locator('.dj-market-tabs button').first().click();assert.equal(await p.locator('.dj-market-table tbody tr').count(),30);
   await p.evaluate(()=>document.documentElement.dataset.theme='dark');await p.locator('.dj-masthead').screenshot({path:`${out}/dark-${lang}.png`});
   checks.push(`${lang}: keyboard, market filters, dark theme`);
  }
  assert.deepEqual(errors,[]);fs.writeFileSync(out+'/browser-result.json',JSON.stringify({passed:true,checks,errors},null,2));console.log('PASS '+checks.length+' event-first browser groups');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
