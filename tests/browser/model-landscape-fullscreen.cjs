// Native Fullscreen API success is never mocked. Only failure branches are injected.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{
 const base='http://127.0.0.1:18059',out=process.env.READING_OUTPUT||'/tmp/fieldtofit-chart-fullscreen';
 fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:process.env.READING_CHROMIUM||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const context=await browser.newContext({viewport:{width:1440,height:1000},extraHTTPHeaders:{DNT:'1'}});
 const page=await context.newPage(),errors=[],checks=[];
 page.on('pageerror',e=>errors.push(e.message));
 const chart=page.locator('.landscape-chart'),entry=chart.getByRole('button',{name:/^(全屏查看|退出全屏|View fullscreen|Exit fullscreen)$/});
 const plot=chart.locator('.landscape-plot'),search=chart.locator('.chart-search input');
 const native=()=>page.waitForFunction(()=>document.fullscreenElement===document.querySelector('.landscape-chart'));
 const exited=()=>page.waitForFunction(()=>!document.fullscreenElement&&document.activeElement===document.querySelector('.landscape-chart-actions button[aria-busy]'));
 const geometry=()=>plot.locator('.chart-point').evaluateAll(ns=>ns.map(n=>{
  const c=n.querySelector('circle'),box=n.ownerSVGElement.viewBox.baseVal;return [n.dataset.modelId,Number(((Number(c.getAttribute('cx'))-78)/(box.width-168)).toFixed(8)),Number(((Number(c.getAttribute('cy'))-86)/(box.height-206)).toFixed(8)),c.getAttribute('fill')];
 }));
 async function enter(keyboard=false){
  if(keyboard){await entry.focus();await page.keyboard.press('Enter');}else await entry.click();
  await native();await page.waitForFunction(()=>document.querySelector('.landscape-chart-actions button[aria-busy]').getAttribute('aria-busy')==='false');
  assert.equal(await chart.evaluate(n=>n.matches(':fullscreen')),true);
  const size=await chart.evaluate(n=>({w:n.clientWidth,h:n.clientHeight,iw:innerWidth,ih:innerHeight,x:n.getBoundingClientRect().x,y:n.getBoundingClientRect().y}));
  assert.deepEqual(size,{w:size.iw,h:size.ih,iw:size.iw,ih:size.ih,x:0,y:0});
 }
 async function assertFits(){
  await page.waitForFunction(()=>{const p=document.querySelector('.landscape-plot');return p&&p.scrollWidth<=p.clientWidth+1&&p.scrollHeight<=p.clientHeight+1;});
  const bounds=await plot.boundingBox();
  for(const selector of ['.chart-model-name','.chart-axis-title','.chart-credit','.chart-tick']){
   const clipped=await plot.locator(selector).evaluateAll((nodes,b)=>nodes.filter(n=>{const r=n.getBoundingClientRect();return r.x<b.x-1||r.y<b.y-1||r.right>b.x+b.width+1||r.bottom>b.y+b.height+1;}).map(n=>n.textContent),bounds);
   assert.deepEqual(clipped,[],selector+' must fit');
  }
  assert(await chart.locator('.landscape-attribution').evaluate(n=>n.getBoundingClientRect().bottom<=innerHeight));
  assert(await chart.evaluate(n=>n.scrollHeight<=n.clientHeight+1&&n.scrollWidth<=n.clientWidth+1));
 }
 try{
  const snapshot=await (await context.request.get(base+'/api/v1/platform/model-landscape')).json();
  for(const source of snapshot.sources)for(const en of [false,true]){
   await page.goto(base+(en?'/en':'')+'/for-you?chart='+source.id+'&company=OpenAI&company=Anthropic&topic=retained#model-landscape');
   await page.waitForLoadState('networkidle');await entry.waitFor();await page.locator('html').evaluate(n=>n.dataset.theme='dark');
   assert.equal(await entry.textContent(),en?'View fullscreen':'全屏查看');
   assert.equal(await page.getByRole('button',{name:/^(放大查看|Enlarge chart)$/}).count(),0);
   await search.fill('gpt');await plot.locator('.chart-point').first().press('Enter');await chart.locator('.landscape-point-detail').waitFor();
   const selection=await chart.locator('.landscape-point-detail').textContent(),before=await geometry(),url=page.url();
   await entry.scrollIntoViewIfNeeded();const scroll=await page.evaluate(()=>scrollY);
   await enter(true);
   assert.equal(await search.inputValue(),'gpt');assert.equal(await chart.locator('.landscape-point-detail').textContent(),selection);
   await assertFits();
   assert.deepEqual(await geometry(),before);assert.equal(page.url(),url);
   assert.equal(await entry.textContent(),en?'Exit fullscreen':'退出全屏');
   await chart.getByRole('combobox').selectOption('2');
   await plot.evaluate(n=>{n.scrollLeft=180;n.scrollTop=140;});
   assert(await plot.evaluate(n=>n.scrollLeft>0&&n.scrollTop>0));
   await chart.evaluate(n=>n.scrollTop=n.scrollHeight);
   assert(await entry.evaluate(n=>{const b=n.getBoundingClientRect();return b.top>=0&&b.bottom<=innerHeight;}));
   await entry.click();await exited();
   await page.waitForFunction(y=>Math.abs(scrollY-y)<2,scroll,{timeout:5000});
   assert.equal(await search.inputValue(),'gpt');assert.equal(await chart.locator('.landscape-point-detail').textContent(),selection);
   // External/native exits use the same fullscreenchange path as browser Esc.
   await enter();await page.evaluate(()=>document.exitFullscreen());await exited();
   assert.equal(await search.inputValue(),'gpt');await page.waitForFunction(y=>Math.abs(scrollY-y)<2,scroll,{timeout:5000});
   await enter();await chart.getByRole('button',{name:en?'Filters':'筛选',exact:true}).click();await search.fill('no-matching-model-REQ-7-7');await chart.locator('.landscape-empty').waitFor();
   await chart.getByRole('button',{name:en?'Reset filters':'重置筛选',exact:true}).click();
   await page.waitForFunction(n=>document.querySelectorAll('.landscape-plot .chart-point').length===n,source.points.length);
   await chart.getByRole('button',{name:en?/^Company flagships/:/^各家旗舰模型/}).click();
   await page.waitForFunction(n=>document.querySelectorAll('.landscape-plot .chart-point').length===n,source.flagship.models.filter(m=>m.status==='plotted').length);
   await chart.getByRole('button',{name:en?'Hide filters':'收起筛选',exact:true}).click();await assertFits();
   await page.screenshot({path:out+'/'+source.id+'-'+(en?'en':'zh')+'-fullscreen-dark.png'});
   await entry.click();await exited();
   assert.deepEqual(new URL(page.url()).searchParams.getAll('company'),['flagship']);
   checks.push(source.id+' '+(en?'en':'zh')+': native enter x3, button/external exit, focus/scroll, selected model/query/URL, coordinates, zoom/pan, sticky exit, empty/reset/flagships');
  }
  for(const source of snapshot.sources)for(const [width,height] of [[1920,1080],[1366,768],[1280,720]]){
   await page.setViewportSize({width,height});await page.goto(base+'/for-you?chart='+source.id+'#model-landscape');
   await page.waitForLoadState('networkidle');await entry.waitFor();await enter();await assertFits();
   assert.equal(await plot.locator('.chart-model-name').count(),source.points.length);
   await page.screenshot({path:out+'/'+source.id+'-all-'+width+'x'+height+'.png'});
   await entry.click();await exited();checks.push(source.id+': all '+source.points.length+' names/points, axes and dates fit at '+width+'x'+height);
  }
  for(const width of [390,320]){
   await page.setViewportSize({width,height:844});await page.goto(base+'/en/for-you?chart=arena&company=OpenAI#model-landscape');
   await page.waitForLoadState('networkidle');await entry.waitFor();await enter();await assertFits();
   assert(await chart.evaluate(n=>n.scrollWidth<=n.clientWidth+1));
   await page.screenshot({path:out+'/arena-en-'+width+'-fullscreen.png'});
   await entry.click();await exited();assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
   checks.push(width+'px: native fullscreen, English controls, no outer overflow');
  }
  for(const en of [false,true])for(const failure of ['missing','disabled','rejected','sync-throw']){
   await page.goto(base+(en?'/en':'')+'/for-you?company=OpenAI#model-landscape');await page.waitForLoadState('networkidle');await entry.waitFor();
   await search.fill('gpt');const before=await geometry();
   await page.evaluate(failure=>{
    window.originalFullscreen=Element.prototype.requestFullscreen;
    if(failure==='disabled')Object.defineProperty(document,'fullscreenEnabled',{configurable:true,value:false});
    else Element.prototype.requestFullscreen=failure==='missing'?undefined:failure==='sync-throw'?function(){throw new TypeError('test denial');}:function(){return Promise.reject(new TypeError('test denial'));};
   },failure);
   await entry.click();const alert=chart.getByRole('alert');await alert.waitFor();
   assert.match(await alert.textContent(),en?/Fullscreen is unavailable|Unable to enter fullscreen/:/不支持全屏|未能进入全屏/);
   assert.equal(await page.evaluate(()=>document.fullscreenElement),null);assert.deepEqual(await geometry(),before);assert.equal(await search.inputValue(),'gpt');
   assert.equal(await page.locator('dialog[open]').count(),0);
   await page.evaluate(()=>{delete document.fullscreenEnabled;Element.prototype.requestFullscreen=window.originalFullscreen;});
   await enter();assert.equal(await alert.count(),0);
   // A failed exit must keep native fullscreen and its working exit control.
   await page.evaluate(()=>{window.originalExit=document.exitFullscreen;document.exitFullscreen=()=>Promise.reject(new TypeError('test exit denial'));});
   await entry.click();await alert.waitFor();assert.match(await alert.textContent(),en?/Unable to exit fullscreen/:/无法退出全屏/);await native();
   await page.evaluate(()=>document.exitFullscreen=window.originalExit);await entry.click();await exited();assert.equal(await alert.count(),0);
   checks.push((en?'en':'zh')+': '+failure+' entry failure, same chart/query, real retry, exit failure/recovery');
  }
  assert.deepEqual(await (await context.request.get(base+'/api/v1/platform/model-landscape')).json(),snapshot);
  assert.deepEqual(errors,[]);
  const result={passed:true,browser:browser.version(),checks,errors,scope:'Local disposable fixture; native API in headless Chrome. OS fullscreen/Esc verified separately in desktop browsers.'};
  fs.writeFileSync(out+'/results.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 }catch(error){await page.screenshot({path:out+'/failure.png'});console.error(JSON.stringify({url:page.url(),completed:checks}));throw error;}
 finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
