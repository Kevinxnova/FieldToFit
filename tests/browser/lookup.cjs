// Use only lookup_server.py's disposable local database.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{
 const base=process.env.READING_BASE_URL||'http://127.0.0.1:18051';
 assert(['127.0.0.1','localhost'].includes(new URL(base).hostname));
 assert(process.env.READING_ADMIN_PASSWORD,'Isolated test password required');
 const out=process.env.READING_OUTPUT||'/tmp/fieldtofit-lookup';fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:process.env.READING_CHROMIUM});
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1000},permissions:['clipboard-read','clipboard-write']});
  const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  const area=page.locator('#ai-lookup');
  await page.goto(base+'/for-your-ai?lookup=UnifiedFixture');
  await area.locator('.lookup-summary').filter({hasText:'找到 12 项匹配内容'}).waitFor();
  assert.equal(await area.locator('.lookup-result').count(),10);
  await area.getByRole('button',{name:'下一页',exact:true}).click();
  await page.waitForURL(/lookup_cursor=/);await area.getByText('11–12 / 12',{exact:true}).waitFor();
  assert.equal(await area.locator('.lookup-result').count(),2);
  await area.getByLabel('内容范围',{exact:true}).selectOption('news');
  await area.locator('.lookup-summary').filter({hasText:'找到 1 项匹配内容'}).waitFor();assert(!new URL(page.url()).searchParams.has('lookup_cursor'));
  await area.getByLabel('内容范围',{exact:true}).selectOption('all');
  await area.getByLabel('统一检索关键词').fill('SearchNeedle');await area.getByRole('button',{name:'搜索资料',exact:true}).click();
  await area.locator('.lookup-snippet').filter({hasText:'原文片段'}).waitFor();
  assert(!(await area.innerText()).includes('PRIVATE-EDITOR-SECRET'));
  await area.getByRole('button',{name:'把这项交给 AI',exact:true}).click();
  const copied=await page.evaluate(()=>navigator.clipboard.readText());assert(copied.includes('curated_material')&&copied.includes('content_revision')&&copied.includes('SearchNeedle'));
  await area.getByRole('button',{name:'加入资料包',exact:true}).click();
  await area.getByRole('button',{name:'预览含原文资料包',exact:true}).click();
  await area.getByLabel('含原文资料包预览').waitFor();assert((await area.getByLabel('含原文资料包预览').inputValue()).includes('Original documented instructions'));
  await area.getByLabel('统一检索关键词').fill('Harness alias');await area.getByRole('button',{name:'搜索资料',exact:true}).click();
  await area.locator('.lookup-summary').filter({hasText:'找到 1 项匹配内容'}).waitFor();
  await area.getByRole('button',{name:'加入资料包',exact:true}).click();
  await area.getByRole('button',{name:'预览含原文资料包',exact:true}).click();
  await area.getByLabel('含原文资料包预览').waitFor();const mixed=JSON.parse(await area.getByLabel('含原文资料包预览').inputValue());assert.equal(mixed.coverage.requested_objects,2);
  assert.equal(mixed.coverage.available_objects,2);
  await area.getByRole('link',{name:'查看完整内容',exact:true}).click();await page.waitForURL(/for-you\?object=/);
  await page.getByRole('heading',{name:'Harness example',exact:true}).waitFor();
  await page.goto(base+'/for-your-ai?lookup=SearchNeedle');await area.locator('.lookup-snippet').waitFor();await area.scrollIntoViewIfNeeded();
  await page.screenshot({path:out+'/lookup-desktop.png'});
  await area.getByLabel('统一检索关键词').fill('NoMatchAtAllFixture');await area.getByRole('button',{name:'搜索资料',exact:true}).click();await area.locator('.lookup-summary').filter({hasText:'找到 0 项匹配内容'}).waitFor();
  // Reachable failure state and retry, without network dependence.
  await page.route('**/api/v1/platform/lookup?**',r=>r.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:'lookup_unavailable',detail:'Fixture temporary failure'})}));
  await area.getByLabel('统一检索关键词').fill('GPT');await area.getByRole('button',{name:'搜索资料',exact:true}).click();await area.getByRole('alert').waitFor();
  await page.unroute('**/api/v1/platform/lookup?**');await area.getByRole('button',{name:'重试',exact:true}).click();await area.locator('.lookup-result').first().waitFor();
  // Real UI alias editing: delimiter survives typing; saving never publishes.
  await page.goto(base+'/admin?section=library');await page.getByLabel('管理密码',{exact:true}).fill(process.env.READING_ADMIN_PASSWORD);await page.getByRole('button',{name:'进入管理',exact:true}).click();
  await page.getByRole('button',{name:'内容库',exact:true}).click();await page.locator('.management-library-item').filter({hasText:'CW-M01'}).click();
  const alias=page.getByLabel('已核对别名（逗号分隔，最多 20 个）');await alias.fill('');await alias.pressSequentially('BrowserAlias, SecondAlias');assert.equal(await alias.inputValue(),'BrowserAlias, SecondAlias');
  await page.getByRole('button',{name:'保存草稿',exact:true}).click();await page.getByRole('button',{name:'生成双端预览',exact:true}).waitFor({state:'visible'});
  const response=await context.request.get(base+'/api/v1/platform/lookup?q=BrowserAlias');assert.equal((await response.json()).total,0);
  await page.getByRole('button',{name:'生成双端预览',exact:true}).click();
  await page.screenshot({path:out+'/alias-editor-desktop.png'});
  // Mobile, English, dark mode and long query layout.
  await page.setViewportSize({width:390,height:844});await page.goto(base+'/for-your-ai?lookup=SearchNeedle');await area.locator('.lookup-snippet').waitFor();await area.scrollIntoViewIfNeeded();
  await page.screenshot({path:out+'/lookup-mobile.png'});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  await page.getByRole('button',{name:'EN',exact:true}).click();await area.getByRole('heading',{name:'See what your AI can discover'}).waitFor();
  await page.getByRole('button',{name:'Dark theme',exact:true}).click();await area.scrollIntoViewIfNeeded();await page.screenshot({path:out+'/lookup-mobile-dark-en.png'});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));assert.deepEqual(errors,[]);
  fs.writeFileSync(out+'/result.json',JSON.stringify({passed:true,checks:['pagination','scope reset','source excerpt','copy reading arguments','mixed source package','legacy detail link','empty and retry','private alias save','desktop','mobile','English dark','no overflow','no page errors']},null,2));
  console.log('Unified lookup browser acceptance passed');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
