const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{
const browser=await chromium.launch({headless:true,executablePath:process.env.READING_CHROMIUM});
try{
 const base=process.env.READING_BASE_URL||'http://127.0.0.1:18003',out=process.env.READING_OUTPUT||'/tmp/fieldtofit-v101';fs.mkdirSync(out,{recursive:true});
 const context=await browser.newContext({viewport:{width:1440,height:1000},permissions:['clipboard-read','clipboard-write']});const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+'/for-you');await page.locator('.watch-card').last().waitFor();await page.locator('.chart-point').first().waitFor();
 assert.equal(await page.locator('.news-card').count(),10);assert.equal(await page.locator('.watch-card').count(),27);
 assert(await page.locator('.platform-lead').first().textContent().then(s=>s.includes('模型能力与价格图')));
 assert.equal(await page.getByText('查看旧版概览归档',{exact:true}).count(),0);assert.equal(await page.getByText('历史资料与原文库',{exact:true}).count(),0);
 assert.equal(await page.locator('.news-card').first().locator('.news-editorial > .news-points > li').count(),2);
 assert(await page.locator('.news-card').first().locator('.news-editorial > .news-points').isVisible());
 assert(await page.locator('.watch-card').first().locator(':scope > .watch-notes').isVisible());
 assert.equal(await page.locator('.chart-point[role=button]').count(),8);
 assert(await page.evaluate(()=>document.querySelector('#model-landscape').getBoundingClientRect().top<document.querySelector('#recent-news').getBoundingClientRect().top));
 await page.locator('.landscape-plot').scrollIntoViewIfNeeded();await page.screenshot({path:out+'/desktop-aa.png'});
 const aa=page.getByRole('tab',{name:'Artificial Analysis',exact:true});await aa.focus();await page.keyboard.press('ArrowRight');await page.waitForFunction(()=>document.querySelector('#chart-tab-arena')?.getAttribute('aria-selected')==='true');
 assert.equal(await page.getByRole('tab',{name:'Arena',exact:true}).getAttribute('aria-selected'),'true');assert(page.url().includes('chart=arena'));assert.equal(await page.locator('[data-source-date]').textContent(),'2026-09-02');
 await page.getByRole('button',{name:/^claude-fable-5;/}).focus();await page.keyboard.press('Enter');assert.match(await page.locator('.landscape-point-detail').textContent(),/claude-fable-5/);
 await page.screenshot({path:out+'/desktop-arena.png'});
 await page.getByRole('tab',{name:'Epoch AI',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#chart-tab-epoch')?.getAttribute('aria-selected')==='true');assert.equal(await page.locator('.chart-point[role=button]').count(),6);assert.equal(await page.locator('[data-source-date]').textContent(),'来源未标注');
 await page.reload();await page.locator('.chart-point').first().waitFor();assert.equal(await page.getByRole('tab',{name:'Epoch AI',exact:true}).getAttribute('aria-selected'),'true');
 await page.getByText('如何理解这三个来源？',{exact:true}).click();assert.equal(await page.locator('.landscape-explanation li').count(),4);
 await page.getByRole('button',{name:'放大查看',exact:true}).click();assert(await page.locator('dialog').isVisible());await page.keyboard.press('Escape');assert(!(await page.locator('dialog').isVisible()));assert.equal(await page.evaluate(()=>document.activeElement.textContent),'放大查看');
 await page.setViewportSize({width:390,height:844});await page.goto(base+'/for-you?chart=epoch#model-landscape');await page.locator('.chart-point').first().waitFor();assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:out+'/mobile-epoch.png'});
 const nav=page.getByRole('navigation',{name:'本页目录'});await page.getByRole('button',{name:'本页目录',exact:false}).click();await nav.getByRole('link',{name:'模型能力与价格',exact:true}).click();assert.equal(await page.getByRole('button',{name:'本页目录',exact:false}).getAttribute('aria-expanded'),'false');
 await page.goto(base+'/for-your-ai');await page.locator('.watch-ai').waitFor();assert.equal(await page.getByText('历史资料与原文库',{exact:true}).count(),0);await page.getByRole('button',{name:'复制 MCP 接入说明',exact:true}).click();const copied=await page.evaluate(()=>navigator.clipboard.readText());assert(copied.includes('/api/mcp/curated')&&copied.includes('curated_watch')&&copied.includes('curated_news'));assert(!copied.includes('Authorization'));
 await page.screenshot({path:out+'/mobile-ai.png'});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.getByRole('button',{name:'测试 MCP 服务',exact:true}).click();await page.getByText('网站到 MCP 服务连接成功；你的 AI 客户端仍需完成配置。',{exact:true}).waitFor();
 await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:()=>Promise.reject(new Error('denied'))}}));await page.getByRole('button',{name:'复制 MCP 接入说明',exact:true}).click();await page.getByRole('textbox',{name:'MCP 接入说明',exact:true}).waitFor();
 await page.goto(base+'/about');assert.match(await page.locator('.platform-eyebrow').first().textContent(),/v1\.0\.1/);const health=await(await context.request.get(base+'/api/health')).json();assert.equal(health.version,'v1.0.1');
 await page.route('**/api/v1/platform/model-landscape',r=>r.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:'unavailable'})}));await page.goto(base+'/for-you');await page.getByText('图表暂时无法读取，近期动态仍可继续阅读。',{exact:true}).waitFor();await page.locator('.news-card').last().waitFor();assert.equal(await page.locator('.news-card').count(),10);assert.equal(await page.locator('.chart-point').count(),0);
 assert.deepEqual(errors,[]);fs.writeFileSync(out+'/result.json',JSON.stringify({passed:true,base,version:health.version,checks:['3 sources / independent units / accurate dates','URL and keyboard tabs','point selection / enlargement / Escape focus','desktop and mobile / no page overflow','visible editorial points','removed legacy UI','MCP handoff / real service test / copy fallback','about and health version','chart failure preserves news'],screenshots:['desktop-aa.png','desktop-arena.png','mobile-epoch.png','mobile-ai.png']},null,2));console.log('v1.0.1 browser acceptance passed');
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
