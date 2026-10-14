import { useEffect, useRef, useSyncExternalStore } from 'react';
import { request, readToken } from './knowledge';
import { currentLanguage, useLanguage, restoreLanguageScroll } from '../locale/language';
import type { NewsCollection } from '../components/workspace/NewsReading';
import type { WatchCollection } from '../components/workspace/ContinuousWatch';
import type { Landscape } from '../components/workspace/ModelLandscape';

export type ReadingHome = {revision:string;safety:{items:[string,boolean,[string,string,string][],string[]?][];aliases:unknown[]};news:NewsCollection;watch:WatchCollection;projects:WatchCollection;charts:Landscape};
type Entry = {data:any;error:string;pending?:Promise<void>;used:number;bytes:number;home:boolean;terminal?:boolean};
const entries = new Map<string,Entry>();
const listeners = new Set<()=>void>();
let generation=0, identity=readToken(), version=0;
let latest: {language:string;path:string;data:ReadingHome}|null=null;
let proposed: ReadingHome|null=null, notice='', checking:Promise<void>|null=null;
let adoptedRevision='', bootstrapKey='', activeHomeKey='';
const MAX_BYTES=8*1024*1024;
const emit=()=>{version++;listeners.forEach(fn=>fn());};
const subscribe=(fn:()=>void)=>{listeners.add(fn);return()=>{listeners.delete(fn);};};
const snapshot=()=>version;
const homePath=(q='',type='')=>'/v1/platform/reading?'+new URLSearchParams({q,type});
const keyFor=(path:string,language:string)=>language+'|'+path;
function scope(){if(identity!==readToken()){identity=readToken();generation++;entries.clear();latest=null;proposed=null;notice='';adoptedRevision='';bootstrapKey='';queueMicrotask(emit);}}
function trim(protect:string){
  const ordered=()=>[...entries].filter(([k,e])=>k!==protect&&!e.pending).sort((a,b)=>a[1].used-b[1].used);
  while([...entries.values()].filter(e=>!e.home).length>10||[...entries.values()].filter(e=>e.home).length>2||[...entries.values()].reduce((n,e)=>n+e.bytes,0)>MAX_BYTES){
    const victim=ordered()[0];if(!victim)break;entries.delete(victim[0]);
  }
  const protectedEntry=entries.get(protect);
  if(protectedEntry&&protectedEntry.bytes>MAX_BYTES){protectedEntry.error='Reading data exceeds the cache budget';protectedEntry.data=null;protectedEntry.bytes=0;}
}
function put(path:string,language:string,data:any){
  const key=keyFor(path,language),entry=entries.get(key)||{data:null,error:'',used:0,bytes:0,home:path.startsWith('/v1/platform/reading?')};
  Object.assign(entry,{data,error:'',terminal:false,used:Date.now(),bytes:new TextEncoder().encode(JSON.stringify(data)).length});entries.set(key,entry);trim(key);
  if(entry.home&&data?.revision&&language===currentLanguage()&&(!activeHomeKey||activeHomeKey===key)){latest={path,language,data};proposed=null;adoptedRevision=data.revision;}
}
function clearDetails(){generation++;for(const [key,e] of entries)if(!e.home)entries.delete(key);}
export function applyReadingUpdate(){
  if(!proposed||!latest)return;
  window.dispatchEvent(new Event('fieldtofit:save-reading'));
  const data=proposed;proposed=null;clearDetails();
  for(const [key,e] of entries)if(e.home)entries.delete(key);
  put(latest.path,latest.language,data);bootstrapKey=keyFor(latest.path,latest.language);notice='';emit();
  window.dispatchEvent(new Event('fieldtofit:restore-reading'));
}
function restricted(before:ReadingHome,after:ReadingHome){
  const next=new Map(after.safety.items.map(i=>[i[0],i]));
  return JSON.stringify(before.safety.aliases)!==JSON.stringify(after.safety.aliases)||before.safety.items.some(([id,translated,materials,sections=[]])=>{
    const value=next.get(id);if(!value||translated&&!value[1]||sections.some(section=>!value[3]?.includes(section)))return true;
    return materials.some(m=>!value[2].some(n=>JSON.stringify(m)===JSON.stringify(n)));
  });
}
function invalidate(){generation++;entries.clear();latest=null;proposed=null;adoptedRevision='';notice='withdrawn';emit();}
function revoke(){if(notice!=='access')generation++;entries.clear();latest=null;proposed=null;adoptedRevision='';notice='access';emit();}
export async function checkReading(){
  scope();if(checking||!latest||document.visibilityState==='hidden')return checking;
  const context=latest, epoch=generation;
  checking=(async()=>{
    try{
      const result=await request<ReadingHome&{unchanged?:boolean}>(context.path+'&after='+encodeURIComponent(context.data.revision));
      if(epoch!==generation||currentLanguage()!==context.language||latest!==context)return;
      notice='';
      if(!result.unchanged){
        proposed=result;
        if(restricted(context.data,result)){applyReadingUpdate();notice='withdrawn';}
      }
    }catch(error){
      if(epoch!==generation)return;
      const status=(error as any).status;
      if(status===401||status===403)revoke();else if((error as any).code==='english_unavailable')invalidate();else notice='offline';
    }finally{emit();checking=null;}
  })();return checking;
}
async function fetchEntry(path:string,language:string,force=false){
  scope();if(notice==='access'&&!force)return;const key=keyFor(path,language);let entry=entries.get(key);
  if(entry?.pending)return entry.pending;
  if(!force&&entry?.data)return;
  if(!entry){entry={data:null,error:'',used:Date.now(),bytes:0,home:path.startsWith('/v1/platform/reading?')};entries.set(key,entry);}
  const epoch=generation, target=entry;
  target.error='';
  target.pending=(async()=>{
    try{
      const data=await request<any>(path);
      if(epoch!==generation||identity!==readToken())return;
      if(target.home&&latest&&language===currentLanguage()&&restricted(latest.data,data)){invalidate();}
      put(path,language,data);if(notice==='access')notice='';
    }catch(error){
      if(epoch!==generation)return;
      const status=(error as any).status;
      if(status===401||status===403){revoke();return;}
      if(status===404||status===410||(error as any).code==='english_unavailable'){target.data=null;target.bytes=0;target.terminal=true;}
      target.error=(error as Error).message;if(target.data)notice='offline';
    }finally{target.pending=undefined;emit();}
  })();emit();return target.pending;
}
// This public bootstrap is emitted by the same request that rendered the page.
if(typeof document!=='undefined'){
  const node=document.getElementById('fieldtofit-reading');
  if(node){try{const boot=JSON.parse(node.textContent||'');if(!readToken()&&boot.language===currentLanguage()&&boot.data?.revision){bootstrapKey=keyFor(homePath(boot.q,boot.type),boot.language);put(homePath(boot.q,boot.type),boot.language,boot.data);}}catch{/* Fall back to a normal public read. */}node.remove();}
}
export function useReadingRemote<T>(path:string|null){
  const language=useLanguage();scope();useSyncExternalStore(subscribe,snapshot,snapshot);
  const key=path?keyFor(path,language):'',entry=entries.get(key);
  if(path?.startsWith('/v1/platform/reading?'))activeHomeKey=key;
  const retained=useRef<{key:string;epoch:number;data:T}|null>(null);
  if(entry?.terminal)retained.current=null;
  if(entry?.data)retained.current={key,epoch:generation,data:entry.data};
  const data=entry?.data??(retained.current?.key===key&&retained.current.epoch===generation?retained.current.data:null);
  useEffect(()=>{
    if(!path)return;
    const existing=entries.get(key);if(existing)existing.used=Date.now();
    if(existing?.home&&existing.data){latest={path,language,data:existing.data};}
    if(!existing?.data)void fetchEntry(path,language);
    else if(existing.home){if(bootstrapKey===key)bootstrapKey='';else void checkReading();}
    else void fetchEntry(path,language,true);
    return()=>{if(activeHomeKey===key)activeHomeKey='';};
  },[key,generation]);
  useEffect(()=>{if(data){window.dispatchEvent(new Event('fieldtofit:reading-ready'));restoreLanguageScroll(language);}},[key,data]);
  return {data:data as T|null,error:data?'':entry?.error||(notice==='access'?'Read access changed':''),refreshError:data?entry?.error||'':'',loading:!!path&&!data&&!entry?.error&&notice!=='access',refreshing:!!entry?.pending,reload:()=>{if(path)void fetchEntry(path,language,true);}};
}
export function useHomeReading(q:string,type:string){
  const result=useReadingRemote<ReadingHome>(homePath(q,type));
  return {...result,shared:latest?.language===currentLanguage()?latest.data:null};
}
export async function readComplete<T>(path:string):Promise<T>{
  // Export/copy always revalidates public availability, even when a body is cached.
  const language=currentLanguage(),epoch=generation;
  await fetchEntry(path,language,true);
  if(language!==currentLanguage()||epoch!==generation)throw new Error('Reading context changed; retry');
  const e=entries.get(keyFor(path,language));if(!e?.data||e.error)throw new Error(e?.error||'Could not load complete materials');return e.data;
}
export function useReadingUpdates(active:boolean,home=false){
  const language=useLanguage();useSyncExternalStore(subscribe,snapshot,snapshot);
  useEffect(()=>{
    if(!active)return;
    if(!home&&(!latest||latest.language!==language))void fetchEntry(homePath(),language);
    const check=()=>{void checkReading();};
    // A bootstrap is already current; navigation/focus checks occur independently.
    const timer=setInterval(check,60000);window.addEventListener('focus',check);document.addEventListener('visibilitychange',check);window.addEventListener('fieldtofit:check-reading',check);
    return()=>{clearInterval(timer);window.removeEventListener('focus',check);document.removeEventListener('visibilitychange',check);window.removeEventListener('fieldtofit:check-reading',check);};
  },[active,language,home]);
  return {pending:!!proposed&&latest?.language===language,notice:latest?.language===language||notice==='access'?notice:'',apply:applyReadingUpdate,check:()=>notice==='access'?fetchEntry(homePath(),language,true):checkReading(),revision:adoptedRevision};
}
