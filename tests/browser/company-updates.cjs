const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
const base='http://127.0.0.1:18069',out=process.env.COMPANY_OUTPUT||'output/operations/company-topics-2026-11-09';fs.mkdirSync(out,{recursive:true});
(async()=>{const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});let checks=0;const errors=[];
try{for(const lang of ['zh','en'])for(const width of [1440,390,320]){
 const ctx=await browser.newContext({viewport:{width,height:1000}}),page=await ctx.newPage();page.on('pageerror',e=>errors.push(e.message));
 const prefix=lang==='en'?'/en':'';
 await page.goto(base+prefix+'/for-you',{waitUntil:'domcontentloaded'});await page.locator('.company-updates').first().waitFor();
 assert.equal(await page.locator('.historical-topics details').evaluate(e=>e.open),false);checks++;
 for(const company of ['openai','anthropic']){
  const section=page.locator('section.company-updates').filter({has:page.locator('#'+company+'-updates')});
  assert.equal(await section.locator('li').count(),3);await section.locator('button[aria-expanded]').click();await section.locator('li').nth(9).waitFor();assert.equal(await section.locator('li').count(),10);checks+=2;
 }
 await page.reload();await page.locator('.company-updates').first().waitFor();assert.equal(await page.locator('.company-updates li').count(),20);checks++;
 const expandedUrl=page.url();await page.locator('.company-updates li strong a').first().click();await page.locator('.published-detail h1').waitFor();await page.locator('.published-detail>p a').click();await page.locator('.company-updates li').first().waitFor();assert.equal(page.url(),expandedUrl);assert.equal(await page.locator('.company-updates li').count(),20);checks++;
 await page.locator('.historical-topics summary').click();assert(await page.locator('.historical-topics a').isVisible());checks++;
 await page.screenshot({path:out+`/home-${lang}-${width}.png`,fullPage:true});
 await page.goto(base+prefix+'/for-you/anthropic?product=claude-code&month=2026-11');await page.locator('.company-topic li').first().waitFor();assert.equal(await page.locator('.company-topic li').count(),20);checks++;
 await page.locator('.company-topic nav button').last().click();await page.waitForFunction(()=>document.querySelector('.company-topic nav span')?.textContent.startsWith('2 /'));assert(page.url().includes('topic_page=2'));const url=page.url();const ids=await page.locator('.company-topic li').evaluateAll(es=>es.map(e=>e.id));
 await page.locator('.company-topic li strong a').first().click();await page.locator('.published-detail h1').waitFor();await page.locator('.published-detail>p a').click();await page.locator('.company-topic li').first().waitFor();assert.equal(page.url(),url);assert.deepEqual(await page.locator('.company-topic li').evaluateAll(es=>es.map(e=>e.id)),ids);checks++;
 await page.locator('.company-topic input').fill('not-a-real-match');await page.locator('.company-topic form button').click();await page.waitForFunction(()=>document.querySelectorAll('.company-topic li').length===0);assert.equal(await page.locator('.company-topic li').count(),0);await page.locator('.company-topic>button').click();await page.locator('.company-topic li').first().waitFor();checks++;
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow ${lang} ${width}`);checks++;
 await page.evaluate(()=>document.documentElement.dataset.theme='dark');await page.waitForFunction(()=>getComputedStyle(document.querySelector('.company-topic-filters .button')).backgroundColor==='rgb(32, 42, 36)');await page.screenshot({path:out+`/topic-dark-${lang}-${width}.png`,fullPage:true});
 await page.goto(base+prefix+'/for-you#news-codex-28-days');await page.waitForURL('**/for-you/codex**');await page.locator('.codex-progress').waitFor();checks++;
 assert.equal(await page.locator('.codex-progress').count(),1);await ctx.close();
}assert.deepEqual(errors,[]);fs.writeFileSync(out+'/browser-result.json',JSON.stringify({passed:true,checks,errors,fixture:'disposable SQLite; 25 extra entries per company'},null,2));console.log('PASS '+checks+' browser checks');}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
