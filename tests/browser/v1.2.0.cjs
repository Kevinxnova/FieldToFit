// Run only against an isolated local validation database; never publish content.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
 const base=process.env.READING_BASE_URL||'http://127.0.0.1:18012';
 assert(new URL(base).hostname==='127.0.0.1','This test requires the isolated local fixture server');
 const key=fs.readFileSync(process.env.READING_ADMIN_KEY_FILE,'utf8');
 const out=process.env.READING_OUTPUT||'/tmp/fieldtofit-v120-browser';fs.mkdirSync(out,{recursive:true});
 const b=await chromium.launch({headless:true,executablePath:process.env.READING_CHROMIUM});
 try{
 const ctx=await b.newContext({viewport:{width:1440,height:1000}}),p=await ctx.newPage(),errors=[];
 p.on('pageerror',e=>errors.push(e.message));
 const before=await(await ctx.request.get(base+'/api/v1/platform/watch')).json();
 await p.goto(base+'/sources');await p.locator('.catalog-table-scroll tbody tr').first().waitFor();
 assert.equal(await p.locator('.catalog-table-scroll').first().locator('tbody tr').count(),12);
 assert.match(await p.locator('body').textContent(),/官方公告及闭源产品变化入口待接入/);
 await p.locator('.catalog-table-scroll').first().locator('summary').first().click();
 await p.screenshot({path:out+'/sources-desktop.png',fullPage:true});await p.screenshot({path:out+'/sources-desktop-viewport.png'});
 await p.goto(base+'/admin');await p.getByLabel('管理密码',{exact:true}).fill(key);await p.getByRole('button',{name:'进入管理',exact:true}).click();
 await p.locator('.management-candidate').first().waitFor();assert.equal(await p.locator('.management-candidate').count(),30);
 assert(!await p.getByText('高关注待核实线索',{exact:true}).count());
 await p.getByRole('button',{name:'下一页',exact:true}).first().click();await p.waitForFunction(()=>document.querySelectorAll('.management-candidate').length===6);
 await p.getByRole('button',{name:'上一页',exact:true}).first().click();await p.waitForFunction(()=>document.querySelectorAll('.management-candidate').length===30);
 await p.getByRole('button',{name:'审阅此项',exact:true}).first().click();
 await p.getByText('已获取的原始材料',{exact:true}).click();await p.locator('.review-material').first().waitFor();
 assert.match(await p.locator('.review-material').first().textContent(),/pip install/);
 await p.getByText('调整审阅优先级',{exact:true}).click();await p.getByLabel('调整理由',{exact:true}).fill('验收：需要核对许可证');
 await p.locator('.management-review-side').getByRole('button',{name:'待核实',exact:true}).click();
 await p.getByText('已更新审阅优先级，网站内容未改变。',{exact:true}).waitFor();
 await p.locator('.review-tabs').getByRole('button',{name:'待核实',exact:true}).click();await p.waitForFunction(()=>document.querySelectorAll('.management-candidate').length===2);
 await p.getByRole('button',{name:'审阅此项',exact:true}).filter({visible:true}).first().click();
 await p.getByRole('button',{name:'加入待整理',exact:true}).click();await p.getByText('已加入待整理，尚未发布到网站。',{exact:true}).waitFor();
 await p.screenshot({path:out+'/daily-desktop.png',fullPage:true});
 const after=await(await ctx.request.get(base+'/api/v1/platform/watch')).json();assert.deepEqual(after,before);
 await p.setViewportSize({width:390,height:844});await p.goto(base+'/sources');await p.locator('.catalog-table-scroll').first().waitFor();
 assert(await p.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1));
 const region=p.locator('.catalog-table-scroll').first();await region.evaluate(e=>e.scrollLeft=200);assert(await region.evaluate(e=>e.scrollLeft>0));
 await p.screenshot({path:out+'/sources-mobile.png',fullPage:true});await p.screenshot({path:out+'/sources-mobile-viewport.png'});
 await p.goto(base+'/admin?section=daily');await p.locator('.management-candidate').first().waitFor();
 assert(await p.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1));await p.screenshot({path:out+'/daily-mobile.png',fullPage:true});
 await p.goto(base+'/admin?section=settings');await p.locator('.source-catalog').waitFor();await p.getByRole('button',{name:'立即检查',exact:true}).first().waitFor();
 assert.deepEqual(errors,[]);fs.writeFileSync(out+'/result.json',JSON.stringify({passed:true,checks:['12 tracked organizations','material-backed priority','pagination','manual reason','private selection','unchanged public watch','desktop and mobile tables','no page errors']},null,2));
 console.log('Source tables, priority review, private selection and mobile checks passed');
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exit(1)});
