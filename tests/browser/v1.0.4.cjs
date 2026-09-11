const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{
 const b=await chromium.launch({headless:true,executablePath:process.env.READING_CHROMIUM});
 const base=process.env.READING_BASE_URL||'http://127.0.0.1:18006',out=process.env.READING_OUTPUT||'/tmp/fieldtofit-v104';fs.mkdirSync(out,{recursive:true});
 try{
 const ctx=await b.newContext({viewport:{width:1440,height:1000}}),p=await ctx.newPage(),errors=[],writes=[];
 p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(r.method()==='POST')writes.push(r.url())});
 await p.goto(base+'/community');await p.locator('.developer-projects').getByText(/暂时没有/).waitFor();
 assert.equal(await p.locator('.secondary-nav').getByText('我的账户',{exact:true}).count(),0);
 assert.deepEqual((await p.locator('.secondary-nav a').allTextContents()).slice(0,2),['关于 FieldToFit','FieldToFit 社区']);
 const fields=p.locator('.community-form input,.community-form textarea,.community-form select');assert.equal(await fields.count(),6);
 await p.getByRole('button',{name:'生成投稿内容',exact:true}).click();assert.equal(await p.locator('.community-draft').count(),0);
 const values=['测试项目 A & B','为研究者解释技术论文','https://example.com/demo?a=1&b=2','打开演示查看流程图','开源','第三方推荐'];
 for(let i=0;i<6;i++){if(i<4)await fields.nth(i).fill(values[i]);else await fields.nth(i).selectOption(values[i]);}
 await p.getByRole('button',{name:'生成投稿内容',exact:true}).click();await p.locator('.community-draft').waitFor();
 const gh=new URL(await p.getByRole('link',{name:'通过 GitHub 提交',exact:true}).getAttribute('href'));
 const mail=new URL(await p.getByRole('link',{name:'通过邮箱提交',exact:true}).getAttribute('href'));
 assert.equal(gh.pathname,'/Kevinxnova/FieldToFit/issues/new');assert.equal(mail.pathname,'fieldtofit@163.com');assert.equal(mail.searchParams.get('body'),gh.searchParams.get('body'));
 for(const v of values)assert(gh.searchParams.get('body').includes(v));assert.equal(gh.searchParams.get('title'),'项目投稿｜'+values[0]);
 await fields.nth(0).fill('更新名称');assert.equal(await p.locator('.community-draft').count(),0);
 await p.evaluate(()=>Object.defineProperty(navigator,'clipboard',{value:{writeText:()=>Promise.reject(new Error('test denied'))},configurable:true}));
 await p.getByRole('button',{name:'复制空白投稿模板',exact:true}).click();assert.match(await p.locator('.community-copy-fallback').inputValue(),/作者与提交者关系/);
 await p.screenshot({path:out+'/community-desktop.png',fullPage:true});
 await p.getByRole('link',{name:/推荐资源或纠错/}).click();await p.waitForURL('**/feedback?category=missing');assert.equal(await p.locator('select').first().inputValue(),'missing');
 await p.goto(base+'/about');assert.equal(await p.locator('h1').textContent(),'FIELD → FIT');assert.match(await p.locator('.platform-eyebrow').first().textContent(),/v1\.0\.4/);assert.match(await p.locator('.platform-page').textContent(),/同一套资料，两种使用方式/);await p.screenshot({path:out+'/about-desktop.png',fullPage:true});
 await p.goto(base+'/for-you?chart=arena&company=flagship');await p.locator('.watch-card').last().waitFor();
 const nav=p.locator('.toc-desktop nav');assert.equal(await nav.locator('.reading-toc-items').count(),0);
 assert((await nav.boundingBox()).height<850);
 await nav.getByRole('button',{name:'展开或收起发布与更新',exact:true}).click();assert.equal(await nav.locator('.reading-toc-items').count(),1);
 await nav.getByRole('button',{name:/展开或收起模型 ·/}).click();assert.equal(await nav.locator('.reading-toc-items').count(),1);assert.equal(await nav.getByRole('button',{name:'展开或收起发布与更新',exact:true}).getAttribute('aria-expanded'),'false');
 await nav.getByRole('link',{name:/^开发者投稿项目$/}).click();assert(p.url().includes('company=flagship')&&p.url().endsWith('#developer-projects'));await p.locator('.developer-projects').getByText(/暂时没有/).waitFor();
 await p.locator('.developer-projects').getByRole('link',{name:'提交个人开发项目',exact:true}).click();await p.waitForURL('**/community#submit-project');await p.waitForFunction(()=>document.activeElement?.id==='submit-project');
 await p.setViewportSize({width:390,height:844});await p.goto(base+'/community');await p.locator('.community-form').waitFor();assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await p.screenshot({path:out+'/community-mobile.png',fullPage:true});
 await p.goto(base+'/for-you?chart=arena#model-landscape');await p.locator('.watch-card').last().waitFor();const toggle=p.locator('.reading-toc-toggle'),drawer=p.locator('#reading-toc-drawer');
 await toggle.click();assert(await drawer.isVisible());assert.equal(await p.evaluate(()=>document.body.style.overflow),'hidden');await p.keyboard.press('Escape');await p.waitForFunction(()=>!document.querySelector('#reading-toc-drawer').open);assert.equal(await toggle.evaluate(n=>n===document.activeElement),true);
 await toggle.click();await p.screenshot({path:out+'/directory-mobile.png'});await drawer.getByRole('link',{name:'开发者投稿项目',exact:true}).click();await p.waitForFunction(()=>document.activeElement?.id==='developer-projects');assert(!(await drawer.isVisible()));assert.equal(await p.evaluate(()=>document.body.style.overflow),'');assert(p.url().includes('chart=arena'));
 await p.goto(base+'/for-your-ai');await p.locator('.developer-projects').getByText(/暂时没有/).waitFor();assert.match(await p.locator('.developer-projects').textContent(),/origin: developer_submission/);
 const empty=await(await ctx.request.get(base+'/api/v1/platform/watch?origin=developer_submission')).json();assert.equal(empty.total,0);assert.equal(empty.origin,'developer_submission');
 // Fixture-only published profile: verify all six public fields and filtered AI handoff.
 const collection=await(await ctx.request.get(base+'/api/v1/platform/watch')).json();
 const item={...collection.items[0],origin:'developer_submission',submission:{entry_url:'https://example.com/project',usage:'打开演示查看流程图',openness:'开源',relationship:'第三方推荐'}};
 await p.route('**/api/v1/platform/watch?origin=developer_submission',r=>r.fulfill({json:{...collection,origin:'developer_submission',total:1,items:[item]}}));
 await p.reload();await p.locator('.developer-project-card').waitFor();assert.match(await p.locator('.developer-project-card').textContent(),/第三方推荐/);
 const downloadPromise=p.waitForEvent('download');await p.locator('.developer-projects').getByRole('button',{name:'下载当前范围资料',exact:true}).click();const download=await downloadPromise;
 const pack=JSON.parse(fs.readFileSync(await download.path(),'utf8'));assert.equal(pack.reading.arguments.origin,'developer_submission');assert.equal(pack.items.length,1);assert.equal(pack.items[0].submission.usage,item.submission.usage);
 assert.deepEqual(errors,[]);assert.deepEqual(writes,[]);
 fs.writeFileSync(out+'/result.json',JSON.stringify({passed:true,base,version:'v1.0.4',checks:['community route and navigation order; account entry removed','six-field validation, encoded GitHub/email drafts, edits invalidate draft','clipboard fallback; no submission sent','about preserved opening and updated sections','compact directory, one expanded list, query-preserving links','mobile drawer focus, scroll lock, Escape and heading navigation','empty reviewed projects on all three pages; MCP filter guidance','390px no horizontal overflow'],errors},null,2));console.log('PASS '+out+'/result.json');
 }finally{await b.close()}
})().catch(e=>{console.error(e);process.exit(1)});
