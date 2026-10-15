// Real built UI and local server. Alternate display states modify only intercepted responses.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
const base=process.env.READING_BASE_URL||'http://127.0.0.1:18065';
const out=process.env.READING_OUTPUT||'/tmp/fieldtofit-daily-preview-ui';fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.READING_CHROMIUM||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1000}}),p=await context.newPage();
  const errors=[],reads=[];p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(r.url().includes('/api/v1/'))reads.push(r.url());});
  await p.clock.setFixedTime(new Date('2026-10-15T02:00:00Z'));
  await p.route('https://**/*',r=>r.abort());
  let mode='normal';
  function transform(data){
   if(mode==='empty')data.daily.issue=null;
   if(/^count/.test(mode))data.daily.issue.highlights=data.daily.issue.highlights.slice(0,Number(mode.slice(-1)));
   if(mode==='long')data.daily.issue.headline='A long daily headline with important conditions that must remain fully readable at every supported screen width. '.repeat(3);
   if(mode==='today'){data.daily.issue.kind='daily';data.daily.issue.date='2026-10-15';data.daily.today='2026-10-15';data.daily.status='published';}
   return data;
  }
  await p.route(/\/for-you(?:\?.*)?$/,async r=>{
   const response=await r.fetch();let body=await response.text();
   if(mode==='error')body=body.replace(/<script type="application\/json" id="fieldtofit-reading">.*?<\/script>/s,'');
   else body=body.replace(/(<script type="application\/json" id="fieldtofit-reading">)(.*?)(<\/script>)/s,(_,a,b,c)=>{const boot=JSON.parse(b);boot.data=transform(boot.data);return a+JSON.stringify(boot).replace(/</g,'\\u003c')+c;});
   await r.fulfill({response,body});
  });
  await p.route('**/api/v1/platform/reading?*',async r=>{
   if(mode==='error')return r.fulfill({status:503,json:{error:'Unavailable'}});
   const response=await r.fetch(),data=await response.json();
   return r.fulfill({response,json:data.unchanged?data:transform(data)});
  });
  let checks=0;
  for(const lang of ['zh','en'])for(const width of [1440,1024,390,320]){
   await p.setViewportSize({width,height:1000});await p.goto(base+(lang==='en'?'/en':'')+'/for-you');
   await p.locator('.daily-preview .dp-story').last().waitFor();
   assert.equal(await p.locator('.dp-story').count(),3);assert.equal(await p.locator('.daily-preview').getAttribute('data-state'),'previous');
   assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   const text=await p.locator('.daily-preview').innerText();assert(text.includes('2026 / 10'));assert(text.includes('13'));
   if(lang==='en')assert(!/[\u4e00-\u9fff]/.test(text));
   const boxes=await p.locator('.dp-story').evaluateAll(els=>els.map(e=>({x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y})));
   if(width>=1024)assert(boxes.every(b=>Math.abs(b.y-boxes[0].y)<2));else assert(boxes[1].y>boxes[0].y);
   await p.locator('.daily-preview').screenshot({path:out+`/${lang}-${width}.png`});checks++;
  }
  assert(!reads.some(url=>/\/daily(?:\/|\?)/.test(url)),'Homepage fetched a full daily edition');checks++;
  mode='normal';await p.setViewportSize({width:1440,height:1000});
  const source='/for-you?type=model&news_page=2#daily-preview';await p.goto(base+source);await p.locator('.dp-story').last().waitFor();
  await p.locator('.dp-story h4 a').first().click();await p.locator('#daily-story-event-1').waitFor();
  await p.waitForFunction(()=>document.activeElement?.id==='daily-story-event-1');assert(p.url().includes('/daily/2026-10-13?revision=1#daily-story-event-1'));checks++;
  await p.locator('.dj-breadcrumb a').first().click();await p.locator('.dp-story').last().waitFor();assert.equal(new URL(p.url()).pathname+new URL(p.url()).search+new URL(p.url()).hash,source);checks++;
  await p.waitForFunction(()=>Math.abs(document.getElementById('daily-preview').getBoundingClientRect().top)<190);checks++;
  await p.locator('.dp-read').click();await p.locator('.daily-journal').waitFor();assert(p.url().endsWith('/for-you/daily/2026-10-13?revision=1'));await p.locator('.dj-breadcrumb a').first().click();checks++;
  await p.locator('.dp-archive').click();await p.locator('.dj-archive').waitFor();assert(p.url().endsWith('/for-you/daily/archive'));checks++;
  await p.goto(base+'/en/for-you#daily-preview');await p.locator('.dp-story').last().waitFor();await p.locator('.dp-story h4 a').first().click();
  await p.waitForFunction(()=>document.activeElement?.id==='daily-story-event-1');assert(p.url().includes('/en/for-you/daily/2026-10-13?revision=1#'));checks++;
  await p.reload();await p.waitForFunction(()=>document.activeElement?.id==='daily-story-event-1');checks++;
  await p.locator('.dj-breadcrumb a').first().click();await p.locator('.dp-story').last().waitFor();assert(p.url().includes('/en/for-you#daily-preview'));checks++;
  for(mode of ['empty','count0','count1','count2','long','today','error']){
   await p.setViewportSize({width:320,height:1000});await p.goto(base+'/en/for-you');
   await p.locator('.daily-preview').waitFor();
   if(mode==='error'){await p.locator('.daily-preview [role="alert"]').waitFor();mode='normal';await p.locator('.daily-preview button').click();await p.locator('.dp-story').last().waitFor();}
   else if(mode==='empty'){assert.equal(await p.locator('.dp-story').count(),0);assert.equal(await p.locator('.daily-preview').getAttribute('data-state'),'empty');}
   else if(/^count/.test(mode))assert.equal(await p.locator('.dp-story').count(),Number(mode.slice(-1)));
   else if(mode==='today'){
    assert.equal(await p.locator('.daily-preview').getAttribute('data-state'),'today');
    await p.clock.setFixedTime(new Date('2026-10-15T16:01:00Z'));await p.evaluate(()=>window.dispatchEvent(new Event('focus')));
    await p.waitForFunction(()=>document.querySelector('.daily-preview').dataset.state==='previous');
   }
   assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));checks++;
  }
  mode='normal';await p.goto(base+'/for-you');await p.locator('.dp-story').last().waitFor();
  await p.evaluate(()=>document.documentElement.dataset.theme='dark');await p.locator('.daily-preview').screenshot({path:out+'/dark-320.png'});checks++;
  await p.locator('.dp-archive').focus();await p.keyboard.press('Tab');assert(await p.locator('.dp-read').evaluate(e=>e===document.activeElement&&getComputedStyle(e).outlineStyle!=='none'));checks++;
  assert.deepEqual(errors,[]);fs.writeFileSync(out+'/result.json',JSON.stringify({passed:true,checks,errors},null,2));console.log(`PASS ${checks} daily preview browser checks`);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
