const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),crypto=require('node:crypto');
const base=process.env.READING_BASE_URL||'http://127.0.0.1:18072';
const out=process.env.READING_OUTPUT||'output/daily-v1.12-validation/browser';fs.mkdirSync(out,{recursive:true});
const order=['highlights','companies','products','chips','robotics','infrastructure','policy','business','markets'];
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.READING_CHROMIUM||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 try{
  const context=await browser.newContext({acceptDownloads:true}),p=await context.newPage(),errors=[];
  p.on('pageerror',e=>errors.push(e.message));await p.route('https://**/*',r=>r.abort());
  let checks=0;
  for(const lang of ['zh','en'])for(const width of [1440,1024,390,320]){
   await p.setViewportSize({width,height:1000});const url=base+(lang==='en'?'/en':'')+'/for-you/daily/2026-10-14';
   await p.goto(url);await p.locator('#daily-business').waitFor();
   assert.deepEqual(await p.locator('.dj-index a').evaluateAll(els=>els.map(e=>e.hash.replace('#daily-',''))),order);
   assert.deepEqual(await p.locator('.daily-journal > section').evaluateAll(els=>els.map(e=>e.id.replace('daily-',''))),order);
   assert.equal(await p.locator('#daily-companies .dj-products').count(),0);
   assert.equal(await p.locator('#daily-products .dj-product').count(),5);
   assert.equal(await p.locator('#daily-business .dj-story').count(),1);
   assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   if(lang==='en')assert(!/[\u3400-\u9fff]/.test(await p.locator('.daily-journal').innerText()));
   await p.screenshot({path:`${out}/${lang}-${width}-top.png`});
   await p.locator('.dj-index a[href="#daily-products"]').click();
   await p.waitForFunction(()=>Math.abs(document.getElementById('daily-products').getBoundingClientRect().top)<100);
   await p.locator('#daily-products').screenshot({path:`${out}/${lang}-${width}-products.png`});
   await p.locator('#daily-business').screenshot({path:`${out}/${lang}-${width}-business.png`});
   checks++;
  }
  for(const lang of ['zh','en']){
   await p.setViewportSize({width:390,height:1000});await p.goto(base+(lang==='en'?'/en':'')+'/for-you/daily/2026-10-14#daily-products');
   await p.waitForFunction(()=>document.activeElement?.id==='daily-products');await p.reload();
   await p.waitForFunction(()=>document.activeElement?.id==='daily-products');checks++;
   for(const [i,count] of [[0,7],[1,3],[2,5]]){await p.locator('.dj-market-tabs button').nth(i).click();assert.equal(await p.locator('.dj-market-table tbody tr').count(),count);checks++;}
   const payload=await (await context.request.get(base+'/api/v1/daily/2026-10-14?lang='+lang)).json();
   const pending=p.waitForEvent('download');await p.locator('.dj-download').click();const download=await pending;
   const path=await download.path();assert.equal(crypto.createHash('sha256').update(fs.readFileSync(path)).digest('hex'),payload.pdf[lang].sha256);checks++;
   await p.goto(base+(lang==='en'?'/en':'')+'/for-you/daily/2026-10-13');await p.locator('.daily-journal').waitFor();
   assert.equal(await p.locator('.dj-index a').count(),7);assert.equal(await p.locator('#daily-companies .dj-products').count(),1);assert.equal(await p.locator('#daily-business').count(),0);checks++;
  }
  await p.route('**/api/v1/daily/2026-10-14?*',async r=>{
   const response=await r.fetch(),data=await response.json();data.stories=[];data.products=[];return r.fulfill({response,json:data});
  });
  await p.goto(base+'/en/for-you/daily/2026-10-14#daily-business');await p.locator('#daily-business').waitFor();
  assert.equal(await p.locator('.dj-index a').count(),9);assert.equal(await p.locator('.dj-story').count(),0);
  assert((await p.locator('#daily-products').innerText()).includes('No verified version changes'));
  assert((await p.locator('#daily-business').innerText()).includes('no business event'));checks++;
  assert.deepEqual(errors,[]);fs.writeFileSync(out+'/result.json',JSON.stringify({passed:true,checks,errors,widths:[1440,1024,390,320],languages:['zh','en']},null,2));console.log(`PASS ${checks} nine-section browser scenarios`);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
