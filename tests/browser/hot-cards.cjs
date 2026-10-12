// Real local build and reviewed sample cards; isolated failure variants use response fixtures.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),crypto=require('node:crypto');
const base=process.env.READING_BASE_URL||'http://127.0.0.1:18062';
const out=process.env.READING_OUTPUT||'/tmp/fieldtofit-hot-cards-browser';fs.mkdirSync(out,{recursive:true});
(async()=>{
 const b=await chromium.launch({headless:true,executablePath:process.env.READING_CHROMIUM||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 let checks=0;const screenshots=[];
 try{
  const c=await b.newContext({viewport:{width:1440,height:1000},permissions:['clipboard-read','clipboard-write']}),p=await c.newPage(),errors=[];
  p.on('pageerror',e=>errors.push(e.message));
  const snapshot=async(name,selector)=>{await p.locator(selector).screenshot({path:out+'/'+name+'.png'});screenshots.push(name+'.png');};
  for(const lang of ['zh','en']){
   const prefix=lang==='en'?'/en':'';
   for(const width of [1440,390,320])for(const theme of ['light','dark']){
    await p.setViewportSize({width,height:950});await p.goto(base+prefix+'/for-you#hot-information-cards');
    await p.locator('.hot-card-preview').last().waitFor();await p.evaluate(t=>document.documentElement.dataset.theme=t,theme);
    assert.equal(await p.locator('.hot-card-preview').count(),3);checks++;
    assert.ok(await p.locator('.news-glance').evaluate(e=>e.nextElementSibling.classList.contains('hot-card-section')));checks++;
    assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`homepage overflow ${lang}/${width}/${theme}`);checks++;
    if(width===1440)assert.equal(await p.locator('.hot-card-grid').evaluate(e=>getComputedStyle(e).gridTemplateColumns.split(' ').length),3);
    if(theme==='light'||width===390)await snapshot(`${lang}-${width}-${theme}-home`,'.hot-card-section');
    await p.locator('.hot-card-read').first().click();await p.locator('.hot-card-sheet').waitFor();
    assert.ok(p.url().includes('/news/D-83#hot-information-card'));assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`detail overflow ${lang}/${width}/${theme}`);checks++;
    assert.equal(await p.locator('.hot-card-changes li').count(),3);assert.equal(await p.locator('.hot-card-scenarios li').count(),2);checks++;
    if(lang==='en')assert.ok(!/[\u3400-\u9fff]/.test(await p.locator('.hot-card-reading').innerText()));checks++;
    if(theme==='light'||width===390)await snapshot(`${lang}-${width}-${theme}-detail`,'.hot-card-sheet');
   }
   await p.setViewportSize({width:390,height:844});
   for(const id of ['D-83','D-113','D-92']){
    await p.goto(base+prefix+'/news/'+id+'#hot-information-card');await p.locator('.hot-card-sheet').waitFor();
    const view=p.getByRole('button',{name:lang==='zh'?'查看分享图':'View share image',exact:true});await view.focus();await p.keyboard.press('Enter');await p.locator('.hot-card-dialog[open] img').waitFor();
    await p.keyboard.press('Escape');await p.waitForFunction(()=>document.activeElement?.textContent==='查看分享图'||document.activeElement?.textContent==='View share image');assert.ok(await view.evaluate(e=>document.activeElement===e));checks++;
    const [download]=await Promise.all([p.waitForEvent('download'),p.getByRole('button',{name:lang==='zh'?'保存分享图':'Save share image',exact:true}).click()]);
    const path=out+'/'+download.suggestedFilename();await download.saveAs(path);
    const item=(await(await c.request.get(base+'/api/v1/platform/news?id='+id+(lang==='en'?'&lang=en':''))).json()).items[0];
    assert.equal(crypto.createHash('sha256').update(fs.readFileSync(path)).digest('hex'),item.hot_card.share[lang].sha256);checks++;
    if(id!=='D-83')await snapshot(`${lang}-390-${id}` ,'.hot-card-sheet');
   }
   await p.getByRole('button',{name:lang==='zh'?'复制链接':'Copy link',exact:true}).click();assert.equal(await p.evaluate(()=>navigator.clipboard.readText()),base+prefix+'/news/D-92#hot-information-card');checks++;
   await p.goto(base+prefix+'/for-you#hot-information-cards');await p.locator('.hot-card-all').click();await p.waitForFunction(()=>document.querySelectorAll('.release-row').length===3);assert.ok(p.url().includes('news_cards=1'));checks++;
   await p.reload();await p.locator('.release-row').last().waitFor();assert.equal(await p.locator('.release-row').count(),3);checks++;
   await p.getByLabel(lang==='zh'?'对象／关键词':'Object / keyword',{exact:true}).fill(lang==='zh'?'合上电脑':'Close your laptop');await p.getByRole('button',{name:lang==='zh'?'查找动态':'Find developments',exact:true}).click();await p.waitForFunction(()=>document.querySelectorAll('.release-row').length===1);
   await p.locator('.release-row .hot-card-badge').click();await p.locator('.hot-card-sheet').waitFor();await p.locator('.published-detail>p>a').click();await p.waitForFunction(()=>document.activeElement?.id==='news-d-83');assert.ok(p.url().includes('news_cards=1'));assert.equal(await p.locator('.release-row').count(),1);checks++;
   await p.goto(base+prefix+'/for-you#hot-information-cards');await p.locator('.hot-card-read').first().click();await p.locator('.hot-card-sheet').waitFor();await p.locator('.published-detail>p>a').click();await p.waitForFunction(()=>document.activeElement?.id==='hot-information-cards');checks++;
  }
  const raw=await(await c.request.get(base+'/api/v1/platform/news?id=D-83')).json();
  let mode='pending';
  await p.route('**/api/v1/platform/news?id=D-83',r=>{const data=structuredClone(raw);if(mode==='pending'){data.items[0].hot_card.status='needs_update';data.items[0].hot_card.update_note='隔离更正提示';delete data.items[0].hot_card.share;}return r.fulfill({json:data});});
  await p.goto(base+'/news/D-83');await p.locator('.hot-card-maintenance').waitFor();assert.equal(await p.getByRole('button',{name:'保存分享图',exact:true}).count(),0);checks++;
  mode='current';await p.route('**/hot-cards/*.png',r=>r.fulfill({status:503,body:'Unavailable'}));await p.reload();await p.locator('.hot-card-sheet').waitFor();await p.getByRole('button',{name:'查看分享图',exact:true}).click();await p.getByText('分享图暂不可用，正文仍可阅读。',{exact:true}).waitFor();await p.keyboard.press('Escape');await p.getByRole('button',{name:'保存分享图',exact:true}).click();await p.getByText('图片暂不可用，请稍后重试；正文仍可阅读。',{exact:true}).waitFor();checks++;
  await p.unroute('**/api/v1/platform/news?id=D-83');
  const all=await(await c.request.get(base+'/api/v1/platform/news')).json();
  await p.route('**/api/v1/platform/news',r=>{const data=structuredClone(all);data.items.forEach(i=>delete i.hot_card);return r.fulfill({json:data});});await p.goto(base+'/for-you');await p.getByText('暂无已审信息卡，完成审核后会在这里展示。',{exact:true}).waitFor();assert.equal(await p.locator('.hot-card-preview').count(),0);checks++;
  await p.unroute('**/api/v1/platform/news');await p.route('**/api/v1/platform/news',r=>r.fulfill({status:503,json:{error:'unavailable'}}));await p.reload();await p.getByText('动态暂时无法读取。',{exact:true}).waitFor();assert.equal(await p.locator('.hot-card-section').count(),0);checks++;
  await p.unroute('**/api/v1/platform/news');await p.unroute('**/hot-cards/*.png');
  await p.goto(base+'/admin?section=library');await p.getByLabel('管理密码',{exact:true}).fill('hot-cards-fixture-only');await p.getByRole('button',{name:'进入管理',exact:true}).click();
  await p.getByLabel('查找内容',{exact:true}).fill('D-83');await p.locator('.management-library-item').filter({hasText:'D-83'}).click();await p.locator('.hot-card-editor>summary').click();
  const headline=p.getByLabel('一句结论',{exact:true}),original=await headline.inputValue();assert.equal(original,'合上电脑，云端任务继续跑');
  await headline.fill(original+'（验收草稿）');await p.getByRole('button',{name:'保存草稿',exact:true}).click();await p.waitForFunction(()=>[...document.querySelectorAll('button')].find(e=>e.textContent==='生成双端预览'&&!e.disabled));
  assert.equal((await(await c.request.get(base+'/api/v1/platform/news?id=D-83')).json()).items[0].hot_card.headline,original);checks++;
  await headline.fill(original);await p.getByRole('button',{name:'保存草稿',exact:true}).click();await p.waitForFunction(()=>[...document.querySelectorAll('button')].find(e=>e.textContent==='生成双端预览'&&!e.disabled));
  await p.getByRole('button',{name:'生成双端预览',exact:true}).click();await p.locator('.management-preview .hot-card-sheet').waitFor();assert.equal(await p.locator('.management-preview .hot-card-changes li').count(),3);checks++;
  await p.getByRole('button',{name:'English preview',exact:true}).click();await p.waitForFunction(()=>document.querySelector('.management-preview .hot-card-sheet')?.textContent.includes('Close your laptop.'));assert.ok(!/[\u3400-\u9fff]/.test(await p.locator('.management-preview .hot-card-reading').innerText()));checks++;
  assert.deepEqual(errors,[]);
  fs.writeFileSync(out+'/result.json',JSON.stringify({passed:true,checks,screenshots,errors},null,2));console.log('PASS '+checks+' browser checks; '+screenshots.length+' screenshots');
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exit(1)});
