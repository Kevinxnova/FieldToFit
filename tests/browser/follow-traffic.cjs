const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');const fs=require('node:fs');
const base=process.env.READING_BASE_URL||'http://127.0.0.1:18053';
const out=process.env.READING_OUTPUT||'/tmp/fieldtofit-v160-evidence';fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const errors=[];let checks=0;
 const context=await browser.newContext({viewport:{width:1440,height:1000},userAgent:'Mozilla/5.0 human browser'});
 await context.addInitScript(()=>Object.defineProperty(navigator,'webdriver',{get:()=>false}));
 const p=await context.newPage();p.on('pageerror',e=>errors.push(e.message));
 const headers={'X-Admin-Password':'visits-test-only'};
 const api=async(path,data,method='POST')=>{const r=await context.request.fetch(base+'/api/v1/admin/workspace'+path,{method,headers,data});assert.ok(r.ok(),await r.text());return r.json();};
 const total=async()=> (await (await context.request.get(base+'/api/analytics/total')).json()).total;
 try{
  await api('/migrate',{});
  const initial=await total();
  const before=await (await context.request.get(base+'/api/admin/analytics/summary',{headers})).json();
  const event=p.waitForResponse(r=>r.url().endsWith('/analytics/events')&&r.request().postDataJSON()?.kind==='page_view');
  await p.goto(base+'/for-you');assert.equal((await event).status(),204);assert.equal(await total(),initial+1);checks++;
  const watch=p.locator('#watch-cw-m01');await watch.locator('.follow-button').click();await watch.getByRole('button',{name:'✓ 已关注',exact:true}).waitFor();checks++;
  await p.getByRole('button',{name:/我关注的 ·/}).click();await p.getByText('已检查。获取更新不会自动标为已读。',{exact:true}).waitFor();
  assert.match(await p.locator('.follow-panel').innerText(),/0 条未读变化/);checks++;
  const data=await api('/content/watch/CW-M01',undefined,'GET');data.draft.introduction+=' Browser acceptance update '+Date.now()+'.';
  await api('/content/watch/CW-M01',{draft_version:data.draft_version,draft:data.draft},'PATCH');
  const preview=await api('/content/watch/CW-M01/preview',{});assert.equal(preview.ready,true);
  await api('/content/watch/CW-M01/publish',{draft_version:preview.draft_version,review_token:preview.review_token,confirmed:true,reason:'Isolated browser acceptance'});
  await p.getByRole('button',{name:'检查更新',exact:true}).click();await p.locator('.follow-events article').first().waitFor();checks++;
  await p.getByRole('button',{name:'查看变化',exact:true}).first().click();await p.getByRole('button',{name:'收起变化',exact:true}).waitFor();assert.match(await p.locator('.follow-panel').innerText(),/0 条未读变化/);checks++;
  const download=p.waitForEvent('download');await p.getByRole('button',{name:'导出关注清单',exact:true}).click();const file=await download;await file.saveAs(out+'/follows.json');const exported=JSON.parse(fs.readFileSync(out+'/follows.json','utf8'));assert.equal(exported.objects.length,1);assert.ok(!JSON.stringify(exported).includes('cursor'));checks++;
  await p.getByRole('button',{name:'复制给我的 AI',exact:true}).click();assert.match(await p.getByRole('textbox',{name:'关注清单 AI 交接'}).inputValue(),/include_related/);checks++;
  const tab=await context.newPage();const detailView=tab.waitForResponse(r=>r.url().endsWith('/analytics/events')&&r.request().postDataJSON()?.kind==='page_view');await tab.goto(base+'/watch/CW-M01');assert.equal((await detailView).status(),204);await tab.getByRole('button',{name:'✓ 已关注',exact:true}).waitFor();checks++;
  await tab.getByRole('button',{name:'✓ 已关注',exact:true}).click();await p.getByText('还没有关注对象。回到全部内容，选择模型或项目旁的「＋关注」。',{exact:true}).waitFor();checks++;
  await p.locator('input[type=file]').setInputFiles(out+'/follows.json');await p.getByRole('button',{name:'确认合并',exact:true}).waitFor();await p.getByRole('button',{name:'取消',exact:true}).click();assert.equal(await p.locator('.follow-panel .follow-button').count(),0);checks++;
  await p.locator('input[type=file]').setInputFiles(out+'/follows.json');await p.getByRole('button',{name:'确认合并',exact:true}).click();await p.getByRole('button',{name:'检查更新',exact:true}).click();await p.getByText('已检查。获取更新不会自动标为已读。',{exact:true}).waitFor();assert.match(await p.locator('.follow-panel').innerText(),/0 条未读变化/);checks++;
  await p.reload();await p.getByRole('button',{name:/我关注的 · 1/}).waitFor();checks++;
  await p.getByRole('button',{name:/我关注的 ·/}).click();await p.waitForTimeout(200);await p.screenshot({path:out+'/following-desktop.png'});
  await p.getByRole('link',{name:'阅读近期动态',exact:true}).click();await p.locator('.reading-layout').waitFor({state:'visible'});checks++;await p.getByRole('button',{name:/我关注的 ·/}).click();
  await p.setViewportSize({width:390,height:844});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);await p.screenshot({path:out+'/following-mobile.png'});checks++;
  const other=await browser.newContext();const op=await other.newPage();await op.goto(base+'/for-you');await op.getByRole('button',{name:/我关注的 · 0/}).waitFor();checks++;
  // Actual anonymous and authenticated report boundary.
  assert.equal((await context.request.get(base+'/api/admin/analytics/summary')).status(),401);checks++;
  await p.setViewportSize({width:1440,height:1000});await p.goto(base+'/admin?section=statistics');await p.getByLabel('管理密码').fill('visits-test-only');await p.getByRole('button',{name:'进入管理',exact:true}).click();await p.getByRole('heading',{name:'访问统计',exact:true}).waitFor();await p.getByRole('heading',{name:'独立访客（估算）',exact:true}).waitFor();await p.screenshot({path:out+'/statistics-desktop.png'});checks++;
  await p.setViewportSize({width:390,height:844});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);await p.screenshot({path:out+'/statistics-mobile.png'});checks++;
  const report=await (await context.request.get(base+'/api/admin/analytics/summary',{headers})).json();assert.ok(report.totals.pv-before.totals.pv>=2);assert.equal(report.totals.uv-before.totals.uv,1);checks++;
  assert.equal(errors.length,0,errors.join('\n'));checks++;
  fs.writeFileSync(out+'/result.json',JSON.stringify({checks,errors,report,scope:'Isolated temporary SQLite; browser fixtures, not real visitors'},null,2));console.log(JSON.stringify({checks,errors,out}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
