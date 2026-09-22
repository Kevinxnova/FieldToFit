const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
const base=process.env.READING_BASE_URL||'http://127.0.0.1:18054';
const out=process.env.READING_OUTPUT||'/tmp/fieldtofit-search-browser';
(async()=>{
 fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:process.env.READING_CHROMIUM||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const errors=[];let checks=0;
 const ctx=await browser.newContext({viewport:{width:1440,height:1000},permissions:['clipboard-read','clipboard-write']});
 const p=await ctx.newPage();p.on('pageerror',e=>errors.push(e.message));
 const news=await (await ctx.request.get(base+'/api/v1/platform/news')).json();
 const watch=await (await ctx.request.get(base+'/api/v1/platform/watch')).json();
 const n=news.items[0],w=watch.items[0];
 const ready=async(page,path,title)=>{
  await page.goto(base+path);await page.locator('.published-detail .news-card, .published-detail .watch-card').waitFor();
  await page.waitForFunction(title=>document.title===title,title);
  assert.equal(await page.locator('link[rel=canonical]').getAttribute('href'),'https://fieldtofit.top'+path);
  assert.equal(await page.locator('meta[property="og:title"]').count(),1);checks+=2;
 };
 try{
  // Core article, version tables and sources remain readable without JavaScript.
  const nojs=await browser.newContext({javaScriptEnabled:false});const raw=await nojs.newPage();
  for(const [path,title] of [['/news/'+n.id,n.title],['/watch/'+w.id,w.name]]){
   const r=await raw.goto(base+path);assert.equal(r.status(),200);assert.equal(await raw.locator('h1').innerText(),title);
   assert.ok(await raw.locator('article a[href^="https://"]').count()>0);checks+=3;
  }
  assert.ok(await raw.locator('table').count()>0);checks++;
  for(const path of ['/for-you','/for-your-ai','/about','/community','/sources']){assert.equal((await raw.goto(base+path)).status(),200);assert.ok((await raw.locator('h1').innerText()).length);checks+=2;}
  assert.equal((await raw.goto(base+'/news/D-99999')).status(),404);checks++;
  await nojs.close();
  await ready(p,'/news/'+n.id,n.title+' · FieldToFit');
  assert.equal(await p.locator('h1').innerText(),n.title);assert.equal(await p.locator('details[data-auto-expand]').getAttribute('open'),'');checks+=2;
  await p.getByRole('button',{name:'分享动态',exact:true}).click();assert.equal(await p.evaluate(()=>navigator.clipboard.readText()),base+'/news/'+n.id);checks++;
  await p.evaluate(()=>scrollTo(0,0));await p.screenshot({path:out+'/desktop-news.png'});
  await ready(p,'/watch/'+w.id,w.name+' · FieldToFit');
  assert.equal(await p.locator('meta[name=description]').getAttribute('content'),w.introduction);checks++;
  await p.getByRole('button',{name:'分享此项',exact:true}).click();assert.equal(await p.evaluate(()=>navigator.clipboard.readText()),base+'/watch/'+w.id);checks++;
  await p.evaluate(()=>scrollTo(0,0));await p.screenshot({path:out+'/desktop-watch.png'});
  // Existing anchors still navigate within the complete long page and expand notes.
  await p.goto(base+'/for-you#news-'+n.id.toLowerCase());await p.locator('#news-'+n.id.toLowerCase()+' details[open]').waitFor();checks++;
  await p.locator('#news-'+n.id.toLowerCase()+' h4 a').click();
  await p.waitForURL('**/news/'+n.id);await p.waitForFunction(title=>document.title===title,n.title+' · FieldToFit');checks++;
  await p.goBack();await p.waitForURL('**/for-you#news-*');await p.waitForFunction(()=>document.title==='FieldToFit · For you');checks++;
  await p.goForward();await p.waitForURL('**/news/'+n.id);await p.waitForFunction(title=>document.title===title,n.title+' · FieldToFit');checks++;
  // A failed SPA read clears old content and marks the page noindex.
  await p.goto(base+'/for-you');await p.locator('#news-'+n.id.toLowerCase()+' h4 a').waitFor();
  await p.route('**/api/v1/platform/news?id=*',r=>r.fulfill({status:404,contentType:'application/json',body:'{"detail":"Not found"}'}));
  await p.locator('#news-'+n.id.toLowerCase()+' h4 a').click();await p.locator('.published-detail [role=alert]').waitFor();
  assert.equal(await p.locator('.published-detail .news-card').count(),0);assert.equal(await p.locator('meta[name=robots]').getAttribute('content'),'noindex');checks+=2;
  await p.unroute('**/api/v1/platform/news?id=*');
  const mobile=await browser.newContext({viewport:{width:390,height:844},isMobile:true});const mp=await mobile.newPage();mp.on('pageerror',e=>errors.push(e.message));
  await ready(mp,'/watch/'+w.id,w.name+' · FieldToFit');
  assert.ok(await mp.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));checks++;
  await mp.screenshot({path:out+'/mobile-watch.png'});
  await mp.evaluate(()=>{localStorage.setItem('fieldtofit-workspace-zh','false');localStorage.setItem('fieldtofit-workspace-dark','true');});
  await ready(mp,'/news/'+n.id,n.title+' · FieldToFit');assert.equal(await mp.locator('html').getAttribute('data-theme'),'dark');checks++;
  await mp.screenshot({path:out+'/mobile-news-dark.png'});
  assert.deepEqual(errors,[]);checks++;
  fs.writeFileSync(out+'/result.json',JSON.stringify({checks,pageErrors:errors,news:n.id,watch:w.id,scope:'isolated SQLite, local browser; no search engine submission'},null,2));console.log(JSON.stringify({checks,pageErrors:errors,out}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
