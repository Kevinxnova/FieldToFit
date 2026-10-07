// Mutating checks require this isolated fixture server; never use a production base.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{
 const base=process.env.READING_BASE_URL||'http://127.0.0.1:18056';
 assert(['localhost','127.0.0.1'].includes(new URL(base).hostname));
 assert.equal(process.env.READING_ADMIN_PASSWORD,'maintenance-fixture-only');
 const out=process.env.READING_OUTPUT||'/tmp/fieldtofit-reviewed-maintenance';fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:process.env.READING_CHROMIUM});
 const ctx=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});const page=await ctx.newPage();page.setDefaultTimeout(15000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await ctx.grantPermissions(['clipboard-read','clipboard-write'],{origin:base});
 const admin={'X-Admin-Password':process.env.READING_ADMIN_PASSWORD};const checks=[];
 try {
  await page.goto(base+'/watch/CW-T01');const card=page.locator('#watch-cw-t01');await card.waitFor();
  const mats=card.locator('.content-materials');await mats.locator('summary').click();
  await mats.getByRole('button',{name:'读取已审核原文',exact:true}).first().click();
  const positions=mats.getByLabel('章节／文件页码',{exact:true});await positions.selectOption('section-2');
  await page.waitForFunction(()=>document.querySelector('.content-materials section > pre')?.textContent==='## Install\n\nFirst step.\n\n');
  await mats.getByRole('button',{name:'复制原文引用',exact:true}).click();const citation=JSON.parse(await page.evaluate(()=>navigator.clipboard.readText()));assert.equal(citation.location.id,'section-2');assert.equal(citation.excerpt,'## Install\n\nFirst step.\n\n');assert.equal(citation.object_id,'CW-T01');checks.push('section citation');
  await mats.getByRole('button',{name:'读取已审核原文',exact:true}).nth(1).click();await positions.selectOption('page-2');
  await mats.locator('.material-gaps').filter({hasText:'没有文字层'}).waitFor();assert((await mats.locator('.material-gaps').textContent()).includes('公式布局未验证'));checks.push('PDF physical pages and gaps');
  await page.screenshot({path:out+'/public-desktop.png'});
  const report=card.locator('.report-correction[data-field="introduction"]');
  await report.getByRole('button',{name:'报告此处有误',exact:true}).click();
  const fieldChoice=report.getByLabel('具体纠错位置',{exact:true});const cell=await fieldChoice.locator('option[value^="blocks."]').first().getAttribute('value');assert(cell);await fieldChoice.selectOption(cell);
  await report.locator('pre').filter({hasText:/./}).waitFor();await fieldChoice.selectOption('introduction');
  await report.getByLabel('问题与新证据',{exact:true}).fill('PRIVATE BROWSER REPORT: improve introduction.');
  await report.getByLabel('联系方式（选填，仅维护者可见）',{exact:true}).fill('private-browser@example.org');
  await page.route('**/api/v1/feedback',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Isolated feedback failure'})}),{times:1});
  await report.getByRole('button',{name:'提交纠错',exact:true}).click();await report.getByText('Isolated feedback failure',{exact:true}).waitFor();
  assert((await report.getByLabel('问题与新证据',{exact:true}).inputValue()).includes('PRIVATE BROWSER REPORT'));
  await report.getByRole('button',{name:'复制待提交报告',exact:true}).click();const pending=JSON.parse(await page.evaluate(()=>navigator.clipboard.readText()));assert.equal(pending.context.object_id,'CW-T01');assert.equal(pending.contact,'private-browser@example.org');checks.push('failed feedback retains copyable report');
  await report.getByRole('button',{name:'提交纠错',exact:true}).click();await report.getByRole('status').waitFor();checks.push('contextual private correction');
  await page.goto(base+'/admin?section=settings');await page.locator('.management-login input').fill(process.env.READING_ADMIN_PASSWORD);await page.locator('.management-login button').last().click();
  const board=page.locator('.object-checks');await board.waitFor();await board.getByRole('button',{name:'建立今日全对象清单',exact:true}).click();
  await board.getByText('49',{exact:true}).first().waitFor();const row=board.locator('.check-row').filter({hasText:'隔离验收档案'});await row.locator('summary').first().click();
  await row.getByRole('button',{name:'获取／重试官方入口',exact:true}).click();await row.getByLabel('核对说明',{exact:true}).waitFor();
  await row.getByLabel('核对说明',{exact:true}).fill('Actual isolated fixture comparison to approved introduction.');
  await row.getByLabel('已完成全部必要入口的档案核对',{exact:true}).check();await row.getByText('登记一项字段差异',{exact:true}).click();
  await row.getByLabel('建议新值',{exact:true}).fill('新的官方能力，等待具体文案确认。');await row.getByLabel('本次原文中的定位引文',{exact:true}).fill('New verified feature.');
  await row.getByRole('button',{name:'保存核对记录',exact:true}).click();await row.getByText('仍待处理的差异证据',{exact:true}).waitFor();
  await row.getByRole('button',{name:'准备档案更新提案',exact:true}).click();await row.getByText('已准备私密更新提案，内容确认后再创建草稿。',{exact:true}).waitFor();checks.push('daily ledger fetch review proposal and full denominator');
  await page.screenshot({path:out+'/ledger-desktop.png'});
  // A real publication in the isolated fixture provides the correction's repair evidence.
  let response=await ctx.request.get(base+'/api/v1/admin/workspace/content/watch/CW-T01',{headers:admin});let d=await response.json();d.draft.introduction='已修复介绍：来源、版本与使用条件已核实。';
  response=await ctx.request.patch(base+'/api/v1/admin/workspace/content/watch/CW-T01',{headers:admin,data:d});assert.equal(response.status(),200);
  response=await ctx.request.post(base+'/api/v1/admin/workspace/content/watch/CW-T01/preview',{headers:admin,data:{}});const preview=await response.json();assert(preview.ready);
  response=await ctx.request.post(base+'/api/v1/admin/workspace/content/watch/CW-T01/publish',{headers:admin,data:{...preview,confirmed:true,reason:'Isolated browser correction'}});assert.equal(response.status(),200);
  const fixed=(await response.json()).history[0].seq;
  await page.goto(base+'/admin?section=feedback');const correction=page.locator('.correction-review').filter({hasText:'PRIVATE BROWSER REPORT'});await correction.waitFor();
  await correction.getByLabel('纠错处理状态',{exact:true}).selectOption('resolved');await correction.getByLabel('内部处理说明',{exact:true}).fill('PRIVATE resolution note');
  await correction.getByLabel('实际发布修订编号',{exact:true}).fill(String(fixed));await correction.getByLabel('公开更正说明',{exact:true}).fill('已依据官方材料修订介绍。');await correction.getByLabel('已核对实际修复修订与公开说明',{exact:true}).check();
  await correction.getByRole('button',{name:'保存纠错处理',exact:true}).click();await page.waitForFunction(()=>document.querySelector('.correction-review')?.textContent.includes('resolved'));
  checks.push('published repair receipt');await page.screenshot({path:out+'/correction-desktop.png'});
  await page.goto(base+'/watch/CW-T01');const comparison=page.locator('.revision-compare');await comparison.locator('summary').click();await comparison.locator('.revision-field').first().waitFor();
  await comparison.getByRole('button',{name:'复制对照链接',exact:true}).click();
  const downloadPromise=page.waitForEvent('download');await comparison.getByRole('button',{name:'下载对照资料',exact:true}).click();const download=await downloadPromise;await download.saveAs(out+'/comparison.json');
  const json=JSON.parse(fs.readFileSync(out+'/comparison.json','utf8'));assert.equal(json.id,'CW-T01');assert(json.fields.some(f=>f.field==='introduction'));
  const params=new URL(base+json.share_path);await page.goto(params.href);await page.locator('.revision-field').first().waitFor();await page.reload();await page.locator('.revision-field').first().waitFor();
  assert(!JSON.stringify(json).includes('PRIVATE'));checks.push('comparison sharing reload export and privacy');
  await page.route('**/api/v1/platform/content/CW-T01/compare?**',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Isolated retry check'})}),{times:1});
  await page.locator('.revision-compare').getByLabel('同时显示未变化字段',{exact:true}).check();await page.getByText('Isolated retry check',{exact:true}).waitFor();
  await page.locator('.revision-compare').getByRole('button',{name:'重试',exact:true}).click();await page.locator('.revision-field').first().waitFor();checks.push('comparison failure and retry recovery');
  await page.locator('.correction-receipts summary').click();await page.getByText('已依据官方材料修订介绍。',{exact:true}).waitFor();
  for(const width of [1440,390,320]) {
   await page.setViewportSize({width,height:900});await page.locator('.revision-compare').getByLabel('同时显示未变化字段',{exact:true}).check();await page.locator('.revision-values table').first().waitFor();await page.locator('.revision-compare').scrollIntoViewIfNeeded();assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.screenshot({path:out+'/compare-'+width+'.png'});
   await page.goto(base+'/admin?section=settings');await board.waitFor();const target=board.locator('.check-row').filter({hasText:'隔离验收档案'});await target.locator('summary').first().click();assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:out+'/ledger-'+width+'.png'});
   await page.goto(params.href);await page.locator('.revision-field').first().waitFor();
  }
  await page.getByLabel('较早修订',{exact:true}).focus();await page.keyboard.press('Tab');assert(await page.getByLabel('较新修订',{exact:true}).evaluate(e=>e===document.activeElement));checks.push('1440/390/320 layouts and keyboard');
  assert.deepEqual(errors,[]);fs.writeFileSync(out+'/result.json',JSON.stringify({passed:true,checks,errors,widths:[1440,390,320]},null,2));console.log('PASS '+out+'/result.json');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
