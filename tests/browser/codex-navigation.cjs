// Retry only observed transient network failures before the interactive UI loads.
// Product assertions stay outside this helper and are never retried.
const transient=/ERR_NETWORK_CHANGED|ERR_CONNECTION_RESET/;
async function navigate(page,url,options={},records=[],reload=false){
 for(let attempt=0;attempt<3;attempt++){
  const failures=[];
  const failed=request=>{const error=request.failure()?.errorText||'';if(transient.test(error))failures.push({path:new URL(request.url()).pathname,error});};
  page.on('requestfailed',failed);
  try{
   const response=reload?await page.reload(options):await page.goto(url,options);
   if(new URL(url).pathname==='/for-you')await page.locator('.codex-view-toggle').waitFor({timeout:30000});
   return response;
  }catch(error){
   if(attempt===2||(!transient.test(error.message)&&!failures.length))throw error;
   records.push({url,attempt:attempt+1,error:error.message.split('\n')[0],failures});
  }finally{page.off('requestfailed',failed);}
 }
}
module.exports={navigate};
