// Mutations are confined to the disposable fixture on port 18058.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{
 const base='http://127.0.0.1:18058',out=process.env.MAPS_OUTPUT||'/tmp/fieldtofit-maps-browser';fs.mkdirSync(out,{recursive:true});
 const b=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});const context=await b.newContext({permissions:['clipboard-read','clipboard-write']});const p=await context.newPage(),errors=[],checks=[];
 p.on('pageerror',e=>errors.push(e.message));
 try{
  for(const width of [1440,390,320]){
   await p.setViewportSize({width,height:1000});await p.goto(base+'/for-you');await p.locator('#technical-evolution-maps').waitFor();
   const order=await p.locator('#news-overview,#technical-evolution-maps,#news-codex-28-days,#news-releases').evaluateAll(nodes=>nodes.map(n=>n.id));assert.deepEqual(order,['news-overview','technical-evolution-maps','news-codex-28-days','news-releases']);
   await p.locator('.technical-maps a[href="/maps/agent-context-cost"]').click();await p.locator('.map-node').first().waitFor();
   await p.locator('.map-graph').first().getByRole('button',{name:/CSA2/}).click();await p.locator('.map-node-detail').first().getByText(/890 bytes/).first().waitFor();
   assert.equal(await p.locator('.map-node-detail').first().getByRole('link').first().getAttribute('href'),'https://arxiv.org/html/2609.19969v1#S2.SS3');
   const node=p.locator('.map-graph').first().getByRole('button',{name:/Bounded Replay/});await node.focus();await p.keyboard.press('Enter');assert.equal(await node.getAttribute('aria-pressed'),'true');
   await p.getByRole('button',{name:'把地图交给 AI',exact:true}).click();const copied=JSON.parse(await p.evaluate(()=>navigator.clipboard.readText()));const api=await p.request.get(base+'/api/v1/platform/maps?slug=agent-context-cost');assert.deepEqual(copied.map,(await api.json()).items[0]);
   await p.getByRole('button',{name:'复制地图链接',exact:true}).click();assert.equal(await p.evaluate(()=>navigator.clipboard.readText()),base+'/maps/agent-context-cost');
   await p.getByRole('button',{name:'查看前后变化',exact:true}).click();await p.locator('.map-diff').first().waitFor();assert.ok(await p.locator('.map-diff').count()>0);
   assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`overflow ${width}`);
   await p.screenshot({path:out+'/map-'+width+'.png',fullPage:true});checks.push('graph/evidence/keyboard/AI/link/history/overflow '+width);
  }
  await p.goto(base+'/maps');await p.getByRole('link',{name:'V4 → V4.1：Agent 的成本省在哪里？',exact:true}).waitFor();await p.getByLabel('地图范围').selectOption('historical');await p.getByText('当前范围没有已审地图。',{exact:true}).waitFor();await p.getByLabel('地图范围').selectOption('recent');await p.getByRole('link',{name:'V4 → V4.1：Agent 的成本省在哪里？',exact:true}).waitFor();checks.push('recent/historical filter');
  await p.goto(base+'/watch/CW-M06');await p.getByRole('link',{name:'V4 → V4.1：Agent 的成本省在哪里？',exact:true}).waitFor();checks.push('dossier map link');
  await p.goto(base+'/for-your-ai');await p.locator('#ai-technical-maps').getByRole('link',{name:'V4 → V4.1：Agent 的成本省在哪里？',exact:true}).waitFor();checks.push('AI entry');
  await p.goto(base+'/admin');await p.locator('.management-login input').fill('maps-fixture-only');await p.locator('.management-login button').last().click();await p.getByRole('heading',{name:'技术地图维护',exact:true}).waitFor();
  await p.getByRole('button',{name:'内容库',exact:true}).click();await p.getByLabel('查找内容').fill('DeepSeek-V4.1');await p.locator('.management-library-item').filter({hasText:'D-90'}).click();await p.getByText('技术报告精选&分析（按问题长期整理）',{exact:true}).waitFor();
  await p.getByLabel('报告首次发布',{exact:true}).fill('2026-09-17');await p.getByLabel('报告数值',{exact:true}).nth(2).fill('0.125');await p.getByLabel('关系含义',{exact:true}).last().selectOption('parallel');
  const editSummary='浏览器实际保存草稿 '+Date.now();await p.getByLabel('本次公开修订说明',{exact:true}).fill(editSummary);await p.getByRole('button',{name:'保存草稿',exact:true}).click();await p.getByText('草稿已保存，网站内容未改变。',{exact:true}).waitFor();const unchanged=await (await p.request.get(base+'/api/v1/platform/maps?slug=agent-context-cost')).json();assert.equal(unchanged.items[0].change_summary,'夹具修订：补充条件对照');
  await p.getByRole('button',{name:'生成双端预览',exact:true}).click();await p.getByText(editSummary,{exact:true}).first().waitFor();checks.push('admin edit/save/private preview');
  for(const width of [1440,390,320]){await p.setViewportSize({width,height:1000});assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`admin overflow ${width}`);await p.screenshot({path:out+'/editor-'+width+'.png',fullPage:true});}
  for(const zh of [true,false])for(const dark of [true,false]){
   await p.evaluate(({zh,dark})=>{localStorage.setItem('fieldtofit-workspace-zh',JSON.stringify(zh));localStorage.setItem('fieldtofit-workspace-dark',JSON.stringify(dark));},{zh,dark});
   await p.goto(base+'/maps/agent-context-cost');await p.locator('.map-graph').first().waitFor();assert.equal(await p.locator('html').getAttribute('data-theme'),dark?'dark':'light');assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await p.screenshot({path:out+'/map-320-'+(zh?'zh':'en')+'-'+(dark?'dark':'light')+'.png',fullPage:true});
  }checks.push('bilingual/light/dark at 320');
  const health=await (await p.request.get(base+'/api/health')).json();assert.equal(health.version,'v1.8.7');checks.push('running fixture version 1.8.7');
  await p.route('**/api/v1/platform/maps?slug=*',r=>r.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Fixture map read unavailable'})}));await p.reload();await p.getByRole('alert').filter({hasText:'Fixture map read unavailable'}).waitFor();assert.equal(await p.locator('.map-node').count(),0);await p.unroute('**/api/v1/platform/maps?slug=*');await p.reload();await p.locator('.map-node').first().waitFor();checks.push('read failure clears graph; reload recovers');
  assert.deepEqual(errors,[]);fs.writeFileSync(out+'/results.json',JSON.stringify({checks,errors},null,2));console.log(JSON.stringify({checks,errors,output:out}));
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exit(1);});
