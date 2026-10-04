import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { BASE, request } from '../../api/knowledge';
const ID='fieldtofit-traffic-browser',OUT='fieldtofit-visits-opt-out',ADMIN='fieldtofit-visits-admin';
type Config={enabled:boolean;origin:string;consent_required:boolean};
let current:{config:Config;browser:string|null;path:string;consent:boolean;abort:AbortController;pageReady?:Promise<boolean>}|null=null;
export function privacyExcluded(){
  if(navigator.doNotTrack==='1'||(navigator as Navigator&{globalPrivacyControl?:boolean}).globalPrivacyControl||navigator.webdriver)return true;
  try{return localStorage.getItem(OUT)==='1'||localStorage.getItem(ADMIN)==='1'||!!sessionStorage.getItem('fieldtofit-admin-password');}catch{return false;}
}
async function browserId(){
  if(!navigator.locks)return null;
  return navigator.locks.request(ID,()=>{try{const saved=JSON.parse(localStorage.getItem(ID)||'null');if(saved&&saved.expires>Date.now())return saved.id as string;const id=crypto.randomUUID();localStorage.setItem(ID,JSON.stringify({id,expires:Date.now()+90*86400_000}));return id;}catch{return null;}});
}
async function sendEvent(kind:string,contentId?:string,eventId:string=crypto.randomUUID()){
  const state=current;if(!state||privacyExcluded()||state.abort.signal.aborted||document.visibilityState!=='visible')return false;
  if(kind!=='page_view'&&state.pageReady&&!(await state.pageReady))return false;
  if(state.abort.signal.aborted||privacyExcluded()||document.visibilityState!=='visible')return false;
  const body=JSON.stringify({event_id:eventId,browser_id:state.browser,kind,path:state.path,...(contentId?{content_id:contentId}:{}),referrer:document.referrer,campaign:new URLSearchParams(location.search).get('utm_campaign')||'',consent:state.consent});
  for(let attempt=0;attempt<3;attempt++){
    if(state.abort.signal.aborted||privacyExcluded()||document.visibilityState!=='visible')return false;
    const abort=new AbortController(),cancel=()=>abort.abort();state.abort.signal.addEventListener('abort',cancel,{once:true});const timer=setTimeout(cancel,8000);
    try{const response=await fetch(BASE+'/analytics/events',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',body,signal:abort.signal});if(response.ok){window.dispatchEvent(new Event('fieldtofit-visits-updated'));return true;}if(response.status<500)return false;}catch{if(state.abort.signal.aborted)return false;}finally{clearTimeout(timer);state.abort.signal.removeEventListener('abort',cancel);}
    await new Promise(resolve=>setTimeout(resolve,500*(attempt+1)));
  }
  return false;
}
export function trackAction(kind:'material_export'|'material_read'|'handoff_copy'|'mcp_address_copy'|'mcp_service_check',id?:string){void sendEvent(kind,id);}
export function TrafficReady({ready,config}:{ready:boolean;config:Config}){
  const location=useLocation();const [preference,setPreference]=useState(0);const last=useRef<{path:string;key:string;id:string;sent:boolean}|null>(null);
  useEffect(()=>{
    if(!ready||!config.enabled||config.origin!==window.location.origin||new URL(BASE,window.location.origin).origin!==window.location.origin)return;
    // Query/filter/hash changes do not create a new page exposure. A return from another path does.
    if(!last.current||last.current.path!==location.pathname)last.current={path:location.pathname,key:location.key,id:crypto.randomUUID(),sent:false};
    const visit=last.current,abort=new AbortController();let starting=false;
    const start=async()=>{
      if(starting||abort.signal.aborted||privacyExcluded()||document.visibilityState!=='visible')return;
      let consent=false;try{consent=localStorage.getItem('fieldtofit-analytics-consent')==='1';}catch{/* anonymous only */}
      if(config.consent_required&&!consent)return;
      starting=true;try{const browser=await browserId();if(abort.signal.aborted)return;current={config,browser,path:location.pathname,consent,abort};if(!visit.sent){current.pageReady=sendEvent('page_view',undefined,visit.id);visit.sent=await current.pageReady;}}finally{starting=false;}
    };
    const pref=()=>{if(privacyExcluded()){abort.abort();current=null;visit.sent=false;visit.id=crypto.randomUUID();try{localStorage.removeItem(ID);}catch{/* no storage */}}setPreference(v=>v+1);};
    const storage=(e:StorageEvent)=>{if(!e.key||[OUT,ADMIN,'fieldtofit-analytics-consent'].includes(e.key))pref();};
    void start();document.addEventListener('visibilitychange',start);window.addEventListener('fieldtofit-visits-preference',pref);window.addEventListener('storage',storage);
    return()=>{abort.abort();if(current?.abort===abort)current=null;document.removeEventListener('visibilitychange',start);window.removeEventListener('fieldtofit-visits-preference',pref);window.removeEventListener('storage',storage);};
  },[ready,location.pathname,config.enabled,config.origin,config.consent_required,preference]);
  return null;
}
export function ContentExposure({id,children}:{id:string;children:React.ReactNode}){
  const ref=useRef<HTMLDivElement>(null);
  useEffect(()=>{const node=ref.current;if(!node)return;let timer:ReturnType<typeof setTimeout>|undefined;
    const observer=new IntersectionObserver(entries=>{clearTimeout(timer);if(entries[0].intersectionRatio>=0.5&&document.visibilityState==='visible')timer=setTimeout(()=>{if(document.visibilityState==='visible')void sendEvent('content_view',id);},1000);},{threshold:[0,0.5]});
    const visibility=()=>{clearTimeout(timer);observer.unobserve(node);observer.observe(node);};observer.observe(node);document.addEventListener('visibilitychange',visibility);return()=>{clearTimeout(timer);observer.disconnect();document.removeEventListener('visibilitychange',visibility);};},[id]);
  return <div ref={ref} data-content-exposure={id} style={{maxHeight:'80vh',overflow:'auto'}}>{children}</div>;
}
type Report={start:string;end:string;totals:Record<string,number|null>;trend:Record<string,string|number>[];pages:Record<string,string|number>[];contents:Record<string,string|number>[];sources:Record<string,string|number>[];actions:Record<string,string|number>[];status:string;started_at:string|null;updated_at:string|null;coverage:string};
const metricNames:Record<string,string>={uv:'独立访客（估算）',pv:'页面浏览',sessions:'访问次数',returning_uv:'复访访客',return_rate:'复访占比',anonymous_pv:'无标识浏览',content_views:'内容被看见',exports:'资料导出',material_reads:'原文读取',repeat_readers:'再次取材的浏览器'};
const actionNames:Record<string,string>={page_view:'页面浏览',content_view:'内容被看见',material_export:'资料导出',material_read:'原文读取',handoff_copy:'复制AI交接说明',mcp_address_copy:'复制接入地址／说明',mcp_service_check:'网站到资料服务检查成功'};
const reportValue=(key:string,value:string|number)=>key==='kind'?(actionNames[String(value)]||value):key==='source'?({'direct_unknown':'直接／未知','external':'外部链接','search:google':'Google 搜索','search:bing':'Bing 搜索','search:baidu':'百度搜索'} as Record<string,string>)[String(value)]||String(value).replace(/^campaign:/,'已登记推广：'):String(value);
const reportTime=(v:string|null)=>v?new Date(v).toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',hour12:false}):'—';
const today=()=>new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Shanghai'});
export function TrafficReport(){
 const [start,setStart]=useState(today()),[end,setEnd]=useState(today()),[data,setData]=useState<Report|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const latest=useRef(0);
 const load=async()=>{const seq=++latest.current;setBusy(true);setError('');setData(null);try{const next=await request<Report>('/admin/analytics/summary?'+new URLSearchParams({start,end}),{},true);if(seq===latest.current)setData(next);}catch(e){if(seq===latest.current){setError((e as Error).message);setData(null);}}finally{if(seq===latest.current)setBusy(false);}};
 useEffect(()=>{void load();},[start,end]);
 return <section className="platform-panel"><h2>访问统计</h2><p>北京时间 · 仅管理员可见 · 最长 90 天区间</p><div className="platform-actions">{[0,1,7,30].map(n=><button className="button" key={n} onClick={()=>{const d=new Date(today()+'T12:00:00+08:00');d.setDate(d.getDate()-(n===1?1:Math.max(0,n-1)));setStart(d.toLocaleDateString('sv-SE',{timeZone:'Asia/Shanghai'}));setEnd(n===1?d.toLocaleDateString('sv-SE',{timeZone:'Asia/Shanghai'}):today());}}>{n===0?'今日':n===1?'昨日':`近 ${n} 日`}</button>)}<label>开始<input type="date" value={start} onChange={e=>setStart(e.target.value)}/></label><label>结束<input type="date" value={end} onChange={e=>setEnd(e.target.value)}/></label><button className="button" disabled={busy} onClick={load}>刷新</button><button className="button" disabled={!data||busy} onClick={async()=>{try{const res=await fetch(BASE+'/admin/analytics/export?'+new URLSearchParams({start:data!.start,end:data!.end}),{headers:{'X-Admin-Password':sessionStorage.getItem('fieldtofit-admin-password')||''}});if(!res.ok)throw new Error('导出失败');const url=URL.createObjectURL(await res.blob());const a=document.createElement('a');a.href=url;a.download='fieldtofit-traffic.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){setError((e as Error).message);}}}>导出汇总 CSV</button></div>
 {busy&&<p role="status">正在读取统计…</p>}{error&&<p role="alert">{error}</p>}{data&&<><p>{data.status==='not_started'?'尚无采集数据':data.status==='paused'?'统计已暂停':'采集已开启'} · 首次采集 {reportTime(data.started_at)} · 最后接收 {reportTime(data.updated_at)}</p><div className="platform-facts">{Object.keys(metricNames).map(k=>[k,data.totals[k]] as const).map(([k,v])=><article key={k}><h3>{metricNames[k]||k}</h3><strong>{data.status==='not_started'?'—':v===null?'—':k==='return_rate'?(v*100).toFixed(1)+'%':v.toLocaleString()}</strong></article>)}</div><p>{data.coverage}</p>{[['trend','每日趋势'],['pages','热门页面'],['contents','内容被看见'],['sources','入口与来源'],['actions','使用动作']].map(([key,label])=>{const rows=data[key as 'trend'];return <section key={key}><h3>{label}</h3>{rows.length?<div className="watch-table-scroll"><table className="watch-table"><thead><tr>{Object.keys(rows[0]).map(k=><th key={k}>{metricNames[k]||({day:'日期',path:'页面',content_id:'内容',views:'次数',source:'来源',entry:'入口',kind:'动作',count:'次数'} as Record<string,string>)[k]||k}</th>)}</tr></thead><tbody>{rows.map((row,i)=><tr key={i}>{Object.entries(row).map(([column,v])=><td key={column}>{reportValue(column,v)}</td>)}</tr>)}</tbody></table></div>:<p>本区间没有已接收记录；不能据此判断实际访问为零。</p>}</section>})}</>}
 </section>;
}
