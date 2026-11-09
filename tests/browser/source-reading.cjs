const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
const base='http://127.0.0.1:18070',out=process.env.SOURCE_READING_OUTPUT||'output/operations/source-reading-2026-11-09';fs.mkdirSync(out,{recursive:true});
(async()=>{const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});let checks=0;const errors=[];
try{
 const api=await browser.newContext();const data=await (await api.request.get(base+'/api/v1/platform/news')).json();
 for(const lang of ['zh','en'])for(const width of [1440,390,320]){
  const ctx=await browser.newContext({viewport:{width,height:1000},colorScheme:width===390?'dark':'light'}),page=await ctx.newPage();page.on('pageerror',e=>errors.push(e.message));
  const prefix=lang==='en'?'/en':'';
  for(const ident of ['D-321','D-324']){
   const item=data.items.find(i=>i.id===ident);
   for(const path of ['/news/'+ident,'/maps/'+item.technical_map.slug]){
    await page.goto(base+prefix+path,{waitUntil:'domcontentloaded'});await page.locator('.source-reading').first().waitFor();
    await page.locator(path.startsWith('/news')?'.news-card':'.map-history').waitFor();
    assert.equal(await page.locator('.news-editorial:visible,.map-editorial:visible,.map-overview:visible,.map-report-figure:visible').count(),0);checks++;
    assert.equal(await page.locator('.source-reading-block').count(),item.source_reading.blocks.length);checks++;
    const expected=lang==='zh'?item.source_reading.blocks[0].translation_zh:item.source_reading.blocks[0].quote;
    assert((await page.locator('.source-reading').innerText()).includes(expected));checks++;
    const details=page.locator('.source-reading-block').first().locator('details');assert.equal(await details.evaluate(e=>e.open),false);await details.locator('summary').focus();await page.keyboard.press('Enter');assert.equal(await details.evaluate(e=>e.open),true);checks++;
    assert.equal(await page.locator('.source-original-figure img').count(),0);assert.equal(await page.locator('.source-original-figure a').first().getAttribute('href'),item.source_reading.blocks[1].original_url);checks++;
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow ${path} ${lang} ${width}`);checks++;
    await page.screenshot({path:out+`/${ident}-${path.startsWith('/maps')?'report':'news'}-${lang}-${width}.png`,fullPage:true});
   }
  }
  await page.goto(base+prefix+'/for-you');await page.locator('.company-updates').first().waitFor();
  assert.equal(await page.locator('.company-updates li').count(),6);checks++;
  assert(!(await page.locator('.company-updates').allInnerTexts()).join(' ').includes('会不会'));checks++;
  await page.screenshot({path:out+`/home-${lang}-${width}.png`,fullPage:true});await ctx.close();
 }
 const admin=await browser.newContext();await admin.addInitScript(()=>sessionStorage.setItem('fieldtofit-admin-password','source-reading-fixture'));const page=await admin.newPage();page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+'/admin?section=library&kind=news&id=D-321');await page.getByLabel('查找内容').fill('D-321');await page.locator('.management-library-item').filter({hasText:'D-321'}).first().click();await page.locator('.source-editor').waitFor();assert(await page.getByLabel('使用原文摘录与对应原图').isChecked());checks++;
 const editor=page.locator('.source-editor');assert.equal(await editor.locator('fieldset').count(),2);await editor.getByRole('button',{name:'添加摘录',exact:true}).click();assert.equal(await editor.locator('fieldset').count(),3);await editor.locator('fieldset').last().getByRole('button',{name:'移除段落'}).click();assert.equal(await editor.locator('fieldset').count(),2);checks++;
 await page.screenshot({path:out+'/editor.png',fullPage:true});await admin.close();await api.close();
 assert.deepEqual(errors,[]);fs.writeFileSync(out+'/browser-result.json',JSON.stringify({passed:true,checks,errors,scope:'isolated original-source examples; both languages; 1440/390/320; original links, keyboard and editor'},null,2));console.log('PASS '+checks+' browser checks');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
