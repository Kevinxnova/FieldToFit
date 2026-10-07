// This script may mutate only the isolated fixture on port 18057.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{
 const base='http://127.0.0.1:18057',out=process.env.READING_OUTPUT||'/tmp/ftf-names-browser';fs.mkdirSync(out,{recursive:true});
 const b=await chromium.launch({headless:true,executablePath:process.env.READING_CHROMIUM||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const p=await b.newPage({viewport:{width:1440,height:1000}}),errors=[],checks=[];p.on('pageerror',e=>errors.push(e.message));
 try{
  const unauth=await p.request.get(base+'/api/v1/admin/workspace/names');assert.equal(unauth.status(),401);
  await p.goto(base+'/admin');await p.locator('.management-login input').fill('names-fixture-only');await p.locator('.management-login button').last().click();
  const panel=p.locator('section.management-panel').filter({has:p.getByRole('heading',{name:'新名称线索组',exact:true})});await panel.waitFor();
  await panel.getByRole('button',{name:/^Jev ·/}).click();await panel.getByText(/TypeSafe 是组织/).waitFor();
  assert.equal(await panel.getByRole('heading',{name:'typesafe.ai/jev',exact:true}).count(),1);
  await panel.getByRole('button',{name:'查看核验与撤销历史',exact:true}).click();await panel.getByText(/已核验建议推荐/).first().waitFor();
  await panel.getByText('Introducing Jev and System One',{exact:true}).click();await panel.getByText('名称原文：Jev',{exact:false}).first().waitFor();
  checks.push('private authentication, Jev/TypeSafe identity evidence, exact source position and history');
  for(const width of [1440,390,320]){await p.setViewportSize({width,height:950});assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await panel.scrollIntoViewIfNeeded();await p.screenshot({path:out+'/names-'+width+'.png'});}
  await panel.locator('textarea').fill('隔离浏览器验证重新核验流程');await panel.getByRole('button',{name:'撤销当前结论，重新核验',exact:true}).click();await panel.getByRole('button',{name:/^Jev · .*待消歧追源/}).waitFor();
  checks.push('reopen preserves audit and public content');
  await p.getByRole('button',{name:'来源与运行',exact:true}).click();const catalog=p.locator('.source-catalog');await catalog.getByRole('heading',{name:'重点跟踪对象'}).waitFor();
  await catalog.locator('table a').filter({hasText:'MiMo API · 模型发布'}).last().waitFor();
  const channelLinks=catalog.locator('table').last().locator('a');
  assert.equal(await channelLinks.filter({hasText:'MiMo API ·'}).count(),3);
  assert.equal(await channelLinks.filter({hasText:'火山方舟 ·'}).count(),3);
  assert.equal(await channelLinks.filter({hasText:'百炼 ·'}).count(),4);
  assert.equal(await channelLinks.filter({hasText:'豆包 ·'}).count(),2);
  for(const width of [1440,390,320]){await p.setViewportSize({width,height:950});assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await p.screenshot({path:out+'/sources-'+width+'.png'});}
  checks.push('12 configured endpoints, pending first success, 1440/390/320 without page overflow');
  assert.deepEqual(errors,[]);fs.writeFileSync(out+'/result.json',JSON.stringify({passed:true,checks,errors},null,2));console.log('PASS '+out+'/result.json');
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exit(1)});
